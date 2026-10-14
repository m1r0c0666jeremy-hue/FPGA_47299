from pathlib import Path
import os,subprocess
R=Path(__file__).resolve().parents[1];O=R/'build/sim/stable_faults';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','');logs=[]
files=[R/'sim/tb_stable_faults.sv',*[R/f'rtl/color_regions/{n}.v' for n in ('stable_capture','stable_model_lane','stable_filter4','stable_grid','regions_divide','stable_tracker')]]
for cmd in ([iv,'-g2012','-s','tb_stable_faults','-o',O/'faults.vvp',*files],[iv.with_name('vvp.exe'),O/'faults.vvp']):
    q=subprocess.run(list(map(str,cmd)),cwd=R,env=env,capture_output=True,text=True,timeout=900);logs.append(q.stdout+q.stderr);print(logs[-1],flush=True)
    (R/'reports/stable_faults.log').write_text('\n'.join(logs),encoding='utf-8')
    if q.returncode:raise SystemExit(q.returncode)
