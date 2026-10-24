"""Run targeted RTL simulations; no physical PHY/IP simulation is claimed."""
from pathlib import Path
import os
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
bin_dir=root/'tools/iverilog/ucrt64/bin'
env=os.environ.copy()
env['PATH']=str(bin_dir)+os.pathsep+env.get('PATH','')
hdl='user_source/hdl_source/'
tests={
    'status':['rtl/01_camera/camera_status.v','rtl/00_top_control/status_sync.v'],
    'pack':[hdl+'isp/data96_128/data96_128.v'],
    'axis':[hdl+'isp/uial2axis.v'],
    'video_timing':[hdl+'vtc/uivtc.v',hdl+'hdmi_mixer.v'],
    'memory':['sim/fifo_model.sv',hdl+'video_in.v'],
    'readout':['sim/fifo_model.sv',hdl+'video_out.v'],
}
out=root/'build/sim'; out.mkdir(parents=True,exist_ok=True)
logs=[]; failed=False
for name,files in tests.items():
    image=out/(name+'.vvp')
    command=[str(bin_dir/'iverilog.exe'),'-g2012','-s','tb_'+name,'-o',str(image),
             str(root/'sim'/('tb_'+name+'.sv'))]+[str(root/f) for f in files]
    compiled=subprocess.run(command,capture_output=True,text=True,env=env,cwd=root)
    logs.append(f'=== {name}: compile exit {compiled.returncode} ===\n{compiled.stdout}{compiled.stderr}')
    if compiled.returncode:
        failed=True; continue
    run=subprocess.run([str(bin_dir/'vvp.exe'),str(image)],capture_output=True,text=True,env=env,cwd=root,timeout=120)
    logs.append(f'=== {name}: run exit {run.returncode} ===\n{run.stdout}{run.stderr}')
    failed |= run.returncode != 0
text='\n'.join(logs)
(root/'reports/simulation.log').write_text(text,encoding='utf-8')
print(text)
sys.exit(1 if failed else 0)
