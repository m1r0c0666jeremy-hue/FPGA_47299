"""ScalingTest simulations; full HDMI timing, ideal ordered DDR (not a PHY model)."""
from pathlib import Path
import os,sys,subprocess,argparse
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--quick',action='store_true');a=p.parse_args()
out=r/'build/sim/scaling_test';out.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env['PATH']=str(r/'tools/iverilog/ucrt64/bin')+os.pathsep+env.get('PATH','')
iv=r/'tools/iverilog/ucrt64/bin/iverilog.exe';vvp=iv.with_name('vvp.exe')
logs=[]
def run(args,timeout=240):
 c=subprocess.run([str(x) for x in args],cwd=r,env=env,capture_output=True,text=True,timeout=timeout)
 logs.append(c.stdout+c.stderr);print(c.stdout+c.stderr,flush=True)
 (r/'reports/scaling_simulation.log').write_text('\n'.join(logs),encoding='utf-8')
 if c.returncode:sys.exit(c.returncode)
control=['sim/tb_scaling_controls.sv','rtl/00_top_control/scaling_controls.v','rtl/00_top_control/scaling_viewport.v','rtl/01_camera/camera_gain_control.v']
run([iv,'-g2012','-s','tb_scaling_controls','-o',out/'controls.vvp',*control]);run([vvp,out/'controls.vvp'])
video=['sim/tb_scaling_video.sv','rtl/05_roi_processing/scaling_line_reader.v','rtl/02_image_preprocess/image_preprocess.v','rtl/09_osd_ui/scaling_osd.v','rtl/09_osd_ui/scaling_glyph_rom.v','rtl/09_osd_ui/scaling_logo_rom.v']
run([iv,'-g2012','-s','tb_scaling_video','-o',out/'video.vvp',*video])
jobs=[(0,0,48,0,0,1),(1,13,37,0,0,1),(2,959,563,0,0,1)]
if not a.quick:jobs += [(z,0,0,m,0,1) for z in range(3) for m in (1,2,3)]+[(0,0,48,0,1,2),(0,0,48,0,2,3),(0,0,48,0,0,2)]
def video_job(job):
 i,(z,x,y,m,f,n)=job
 args=[vvp,out/'video.vvp',f'+ZOOM={z}',f'+X={x}',f'+Y={y}',f'+MODE={m}',f'+FAULT={f}',f'+FRAMES={n}']
 if f==0 and n==2:args.append('+DYNAMIC=1')
 if f==0:args.append(f'+CAPTURE={out.as_posix()}/preview_{i}.ppm')
 c=subprocess.run([str(x) for x in args],cwd=r,env=env,capture_output=True,text=True,timeout=900)
 if f==0 and c.returncode==0:
  with Image.open(out/f'preview_{i}.ppm') as im:im.save(out/f'preview_{i}.png')
 return c.returncode,c.stdout+c.stderr
with ThreadPoolExecutor(max_workers=3) as pool:
 for returncode,output in pool.map(video_job,enumerate(jobs)):
  logs.append(output);print(output,flush=True)
  (r/'reports/scaling_simulation.log').write_text('\n'.join(logs),encoding='utf-8')
  if returncode:sys.exit(returncode)
print('SCALING_TEST_SIMULATION_PASSED',flush=True)
