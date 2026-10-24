"""Isolated simulation outputs and immutable per-run source hashes."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess
import ast,sys,re
R=Path(__file__).resolve().parents[1]
IV=R/'tools/iverilog/ucrt64/bin/iverilog.exe'
ENV=os.environ.copy();ENV['PATH']=str(IV.parent)+os.pathsep+ENV.get('PATH','')
def literal_fixture(path,name='src'):
    for node in ast.parse(Path(path).read_text(encoding='utf-8')).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):return ast.literal_eval(node.value)
    raise ValueError(f'No literal fixture {name} in {path}')
def run(name,source,modules,top='tb',args=(),expected_failure=False,timeout=1800,compile_args=()):
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    out=R/'build/sim/refined'/f'{name}_{stamp}';out.mkdir(parents=True,exist_ok=False)
    report=R/'reports/refined/regression';report.mkdir(parents=True,exist_ok=True)
    tb=out/'tb.sv';tb.write_text(source,encoding='utf-8')
    modules=list(map(Path,modules))
    dependencies=list(modules)
    for p in modules:
        for inc in re.findall(r'`include\s+"([^"]+)"',p.read_text(encoding='utf-8',errors='replace')):
            for candidate in (p.parent/inc,R/'rtl/color_regions'/inc):
                if candidate.is_file():
                    dependencies.append(candidate);break
    hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies}
    log_path=report/f'{name}_{stamp}.log';code=0;timed_out=False
    commands=([IV,'-g2012',*compile_args,'-s',top,'-o',out/'test.vvp',tb,*modules],[IV.with_name('vvp.exe'),out/'test.vvp',*args])
    for stage,cmd in zip(('compile','simulate'),commands):
        # Persist output during long simulations as well as after completion.
        with log_path.open('a',encoding='utf-8') as output:
            try:
                p=subprocess.run(list(map(str,cmd)),cwd=R,env=ENV,stdout=output,stderr=subprocess.STDOUT,text=True,timeout=timeout)
                code=p.returncode
            except subprocess.TimeoutExpired:
                timed_out=True;code=124
                output.write(f'\nVERIFICATION_TIMEOUT stage={stage} limit={timeout}s\n')
        if code:break
    unchanged=all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(R))] for p in dependencies)
    passed=unchanged and not timed_out and (not code or (stage=='simulate' and expected_failure)) and bool(code)==expected_failure
    name=f'{name}_{stamp}'
    (report/(name+'.json')).write_text(json.dumps(dict(inputs=hashes,exit_code=code,expected_failure=expected_failure,output=str(out),fixture_sha256=hashlib.sha256(tb.read_bytes()).hexdigest(),stage=stage,timed_out=timed_out,inputs_unchanged=unchanged,passed=passed),indent=2),encoding='utf-8')
    print(log_path.read_text(encoding='utf-8'),flush=True)
    if not passed:raise SystemExit(f'{name}: verification rejected (stage={stage}, exit={code}, timeout={timed_out}, inputs_unchanged={unchanged})')
    return out
