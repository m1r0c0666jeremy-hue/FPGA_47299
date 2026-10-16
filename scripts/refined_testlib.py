"""Isolated simulation outputs and immutable per-run source hashes."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess
R=Path(__file__).resolve().parents[1]
IV=R/'tools/iverilog/ucrt64/bin/iverilog.exe'
ENV=os.environ.copy();ENV['PATH']=str(IV.parent)+os.pathsep+ENV.get('PATH','')
def run(name,source,modules,top='tb',args=(),expected_failure=False,timeout=1800):
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    out=R/'build/sim/refined'/f'{name}_{stamp}';out.mkdir(parents=True,exist_ok=False)
    report=R/'reports/refined/regression';report.mkdir(parents=True,exist_ok=True)
    tb=out/'tb.sv';tb.write_text(source,encoding='utf-8')
    modules=list(map(Path,modules))
    hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in modules}
    logs=[];code=0
    for cmd in ([IV,'-g2012','-s',top,'-o',out/'test.vvp',tb,*modules],[IV.with_name('vvp.exe'),out/'test.vvp',*args]):
        p=subprocess.run(list(map(str,cmd)),cwd=R,env=ENV,capture_output=True,text=True,timeout=timeout)
        logs.append(p.stdout+p.stderr);code=p.returncode
        if code:break
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(R))] for p in modules),'Inputs changed during simulation'
    name=f'{name}_{stamp}';(report/(name+'.log')).write_text('\n'.join(logs),encoding='utf-8')
    (report/(name+'.json')).write_text(json.dumps(dict(inputs=hashes,exit_code=code,expected_failure=expected_failure,output=str(out)),indent=2),encoding='utf-8')
    print(''.join(logs),flush=True)
    if bool(code)!=expected_failure:raise SystemExit(f'{name}: unexpected exit {code}')
    return out
