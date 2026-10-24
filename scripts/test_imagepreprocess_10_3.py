"""Independent algorithm scoreboard and switch tests. Does not run old defect tests."""
from pathlib import Path
import os
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
bin_dir=root/'tools/iverilog/ucrt64/bin'
env=os.environ.copy();env['PATH']=str(bin_dir)+os.pathsep+env.get('PATH','')
out=root/'build/sim/imagepreprocess_10_3';out.mkdir(parents=True,exist_ok=True)
jobs=[('switch','tb_switch_mode_10_3',['sim/tb_switch_mode_10_3.sv','rtl/00_top_control/switch_mode_control.v'],[]),
      ('image_small','tb_imagepreprocess_10_3',['sim/tb_imagepreprocess_10_3.sv','rtl/02_image_preprocess/image_preprocess.v'],['-Ptb_imagepreprocess_10_3.W=17','-Ptb_imagepreprocess_10_3.H=9']),
      ('image_720p','tb_imagepreprocess_10_3',['sim/tb_imagepreprocess_10_3.sv','rtl/02_image_preprocess/image_preprocess.v'],[])]
logs=[];failed=False
for name,top,files,params in jobs:
    image=out/(name+'.vvp')
    c=subprocess.run([str(bin_dir/'iverilog.exe'),'-g2012','-s',top,*params,'-o',str(image),*[str(root/f) for f in files]],capture_output=True,text=True,env=env,cwd=root)
    logs.append(f'=== {name} compile exit {c.returncode} ===\n{c.stdout}{c.stderr}')
    if c.returncode: failed=True;continue
    r=subprocess.run([str(bin_dir/'vvp.exe'),str(image)],capture_output=True,text=True,env=env,cwd=root,timeout=180)
    entry=f'=== {name} run exit {r.returncode} ===\n{r.stdout}{r.stderr}'
    logs.append(entry);print(entry,flush=True);failed|=r.returncode!=0
    if failed: break
(root/'reports/imagepreprocess_10_3_simulation.log').write_text('\n'.join(logs),encoding='utf-8')
sys.exit(int(failed))
