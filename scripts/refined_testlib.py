"""Isolated simulation outputs and immutable per-run source hashes."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess
import ast
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
    hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in modules}
    log_path=report/f'{name}_{stamp}.log';code=0
    for cmd in ([IV,'-g2012',*compile_args,'-s',top,'-o',out/'test.vvp',tb,*modules],[IV.with_name('vvp.exe'),out/'test.vvp',*args]):
        # Persist output during long simulations as well as after completion.
        with log_path.open('a',encoding='utf-8') as output:
            p=subprocess.run(list(map(str,cmd)),cwd=R,env=ENV,stdout=output,stderr=subprocess.STDOUT,text=True,timeout=timeout)
        code=p.returncode
        if code:break
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(R))] for p in modules),'Inputs changed during simulation'
    name=f'{name}_{stamp}'
    (report/(name+'.json')).write_text(json.dumps(dict(inputs=hashes,exit_code=code,expected_failure=expected_failure,output=str(out)),indent=2),encoding='utf-8')
    print(log_path.read_text(encoding='utf-8'),flush=True)
    if bool(code)!=expected_failure:raise SystemExit(f'{name}: unexpected exit {code}')
    return out
