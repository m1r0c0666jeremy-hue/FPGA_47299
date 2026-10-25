"""Compiled timed simulation for long external-behavior fixtures.

Verilator is two-state; four-state initialization/error checks stay in Icarus.
No RTL substitutions or unsupported-feature black boxes are enabled here.
"""
import datetime,hashlib,json,os,re,subprocess,threading
from pathlib import Path
from refined_testlib import R
_compiled={}
_compile_lock=threading.Lock()

def run_native(name,source,modules,top='tb',args=(),timeout=1800,compile_args=()):
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    out=R/'build/sim/native'/f'{name}_{stamp}';out.mkdir(parents=True)
    report=R/'reports/refined/regression';report.mkdir(exist_ok=True,parents=True)
    tb=out/'tb.sv';tb.write_text(source,encoding='utf-8')
    modules=list(map(Path,modules));dependencies=list(modules)
    for p in modules:
        for inc in re.findall(r'`include\s+"([^"]+)"',p.read_text(encoding='utf-8',errors='replace')):
            for candidate in (p.parent/inc,R/'rtl/color_regions'/inc):
                if candidate.is_file():dependencies.append(candidate);break
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    hashes={p.relative_to(R).as_posix():sha(p) for p in dependencies}
    runtime=R/'tools/native_sim/ucrt64';inc=runtime/'share/verilator/include'
    env=os.environ.copy();env['PATH']=str(runtime/'bin')+os.pathsep+env.get('PATH','')
    env['VERILATOR_ROOT']=str(runtime/'share/verilator')
    options=[]
    argument_iter=iter(compile_args)
    for option in argument_iter:
        if option=='-I':option='-I'+str(next(argument_iter))
        if option.startswith('-P'+top+'.'):option='-G'+option[len(top)+3:]
        options.append(option)
    obj=out/'obj';exe=out/'simulation.exe';log=report/f'{name}_{stamp}.log'
    generate=[runtime/'bin/verilator_bin.exe','--cc','--main','--exe','--timing','--assert','-Wno-fatal',
              '--top-module',top,'--Mdir',obj,'--prefix','Vtest',*options,tb,*modules]
    code=0;timed_out=False;cached=False;producer=str(out)
    tool_hash=sha(runtime.parent/'manifest.json')
    key=hashlib.sha256(json.dumps([hashes,source,top,options,tool_hash],sort_keys=True).encode()).hexdigest()
    with log.open('w',encoding='utf-8') as output:
        with _compile_lock:
            if key in _compiled:
                exe,binary_sha,producer=_compiled[key]
                assert sha(exe)==binary_sha,'compiled simulation changed during batch'
                cached=True
            else:
                for stage in ('generate','compile'):
                    if stage=='generate':command=generate
                    else:command=[runtime/'bin/g++.exe','-std=c++20','-O2','-pthread','-DVL_TIME_CONTEXT',
                         '-I'+str(obj),'-I'+str(inc),'-I'+str(inc/'vltstd'),
                         *sorted(obj.glob('*.cpp')),inc/'verilated.cpp',inc/'verilated_timing.cpp',inc/'verilated_threads.cpp','-o',exe]
                    try:code=subprocess.run(list(map(str,command)),cwd=R,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=timeout).returncode
                    except subprocess.TimeoutExpired:code=124;timed_out=True
                    if code:break
                if not code:
                    binary_sha=sha(exe);_compiled[key]=(exe,binary_sha,producer)
        if not code:
            stage='simulate'
            command=[exe,*args]
            try:code=subprocess.run(list(map(str,command)),cwd=R,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=timeout).returncode
            except subprocess.TimeoutExpired:code=124;timed_out=True
    unchanged=all(sha(R/n)==v for n,v in hashes.items())
    passed=code==0 and unchanged and not timed_out
    record=dict(inputs=hashes,exit_code=code,passed=passed,timed_out=timed_out,stage=stage,inputs_unchanged=unchanged,
                backend='Verilator 5.050 two-state/timing; GCC 16.2',output=str(out),fixture_sha256=sha(tb),
                tool_manifest_sha256=tool_hash,compiled_from=producer,reused_compilation=cached,
                binary_sha256=sha(exe) if exe.is_file() else None,arguments=list(args))
    (report/f'{name}_{stamp}.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    content=log.read_text(encoding='utf-8',errors='replace')
    print('\n'.join(line for line in content.splitlines() if '_PASS' in line or 'FRAME ' in line or 'walltime' in line) if passed else content[-7000:],flush=True)
    if not passed:raise SystemExit(f'{name}: native verification rejected at {stage}: {code}; log={log}')
    return out
