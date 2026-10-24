from pathlib import Path
import subprocess,os
R=Path(__file__).resolve().parents[1];O=R/'build/sim/color_regions/backpressure';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','');logs=[]
files=['classifier','runs4','run_labeler','divide','finalize','grid','confirm','capture']
for command in ([iv,'-g2012','-s','tb_color_regions_backpressure','-o',O/'busy.vvp',R/'sim/tb_color_regions_backpressure.sv',*[R/f'rtl/color_regions/regions_{f}.v' for f in files]],[iv.with_name('vvp.exe'),O/'busy.vvp']):
 p=subprocess.run(list(map(str,command)),cwd=R,env=env,capture_output=True,text=True,timeout=90)
 logs.append(p.stdout+p.stderr);print(logs[-1],flush=True);(R/'reports/color_regions_backpressure.log').write_text('\n'.join(logs),encoding='utf-8');assert p.returncode==0
