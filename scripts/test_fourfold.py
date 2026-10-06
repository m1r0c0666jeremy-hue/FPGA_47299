"""Full-timing independent bilinear scoreboard; old evidence is not overwritten."""
from pathlib import Path
import argparse,os,subprocess,sys,json
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--quick',action='store_true');a=p.parse_args()
out=r/'build/sim/improve_fourfold_scale';out.mkdir(parents=True,exist_ok=True)
bin=r/'tools/iverilog/ucrt64/bin';env=os.environ.copy();env['PATH']=str(bin)+os.pathsep+env.get('PATH','')
iv=bin/'iverilog.exe';vvp=bin/'vvp.exe';logs=[]
def run(args,timeout=240):
 c=subprocess.run(list(map(str,args)),cwd=r,env=env,capture_output=True,text=True,timeout=timeout)
 logs.append(c.stdout+c.stderr);print(logs[-1],flush=True)
 (r/'reports/fourfold_simulation.log').write_text('\n'.join(logs),encoding='utf-8')
 if c.returncode:sys.exit(c.returncode)
base=subprocess.run(['git','-c',f'safe.directory={r.as_posix()}','show','4c26207:rtl/02_image_preprocess/image_preprocess.v'],cwd=r,capture_output=True,check=True).stdout
(out/'image_preprocess_main.v').write_bytes(base.replace(b'module image_preprocess #',b'module image_preprocess_main #'))
run([iv,'-g2012','-s','tb_bilinear_rgb','-o',out/'arithmetic.vvp','sim/tb_bilinear_rgb.sv','rtl/05_roi_processing/bilinear_rgb.v']);run([vvp,out/'arithmetic.vvp'])
run([iv,'-g2012','-s','tb_scaling_controls','-o',out/'controls.vvp','sim/tb_scaling_controls.sv','rtl/00_top_control/scaling_controls.v','rtl/00_top_control/scaling_viewport.v','rtl/01_camera/camera_gain_control.v']);run([vvp,out/'controls.vvp'])
files=['sim/tb_fourfold_video.sv','rtl/05_roi_processing/scaling_line_reader.v','rtl/05_roi_processing/bilinear_rgb.v','rtl/02_image_preprocess/image_preprocess.v',str(out/'image_preprocess_main.v'),*[f'rtl/09_osd_ui/{n}.v' for n in ['scaling_osd','scaling_glyph_rom','scaling_logo_rom']]]
run([iv,'-g2012','-s','tb_fourfold_video','-o',out/'video.vvp',*files])
# z,x,y,mode,fault,frames,pattern,dynamic
jobs=[(2,13,37,0,0,1,0,0),(0,0,48,0,0,1,0,0)]
if not a.quick:
 jobs=[(z,13 if z else 0,37 if z else 48,m,0,1,0,0) for z in range(3) for m in range(4)]
 jobs += [(2,x,y,m,0,1,2,0) for x,y in [(0,0),(960,0),(0,564),(960,564),(959,563)] for m in [0,2]]
 jobs += [(2,480,y,0,0,1,1,0) for y in [30,200,350,480]]
 jobs += [(2,480,282,0,0,1,3,0),(2,0,0,0,1,2,0,0),(2,960,564,2,2,3,0,0),(0,0,48,0,0,4,0,1)]
def job(t):
 i,(z,x,y,m,f,n,pat,dyn)=t
 args=[vvp,out/'video.vvp',f'+ZOOM={z}',f'+X={x}',f'+Y={y}',f'+MODE={m}',f'+FAULT={f}',f'+FRAMES={n}',f'+PATTERN={pat}',f'+DYNAMIC={dyn}']
 if f==0 and not dyn:args.append(f'+CAPTURE={out.as_posix()}/preview_{i}.ppm')
 c=subprocess.run(list(map(str,args)),cwd=r,env=env,capture_output=True,text=True,timeout=1200)
 if c.returncode==0 and f==0 and not dyn:
  with Image.open(out/f'preview_{i}.ppm') as im:im.save(out/f'preview_{i}.png')
 return i,c.returncode,c.stdout+c.stderr
with ThreadPoolExecutor(max_workers=6) as pool:
 for i,code,log in pool.map(job,enumerate(jobs)):
  logs.append(f'CASE {i} {jobs[i]}\n'+log);print(logs[-1],flush=True)
  (r/'reports/fourfold_simulation.log').write_text('\n'.join(logs),encoding='utf-8')
  if code:sys.exit(code)
(r/'reports/fourfold_test_cases.json').write_text(json.dumps({'quick':a.quick,'cases':jobs},indent=2)+'\n')
print('FOURFOLD_SIMULATION_PASSED',flush=True)
