from pathlib import Path
import os,subprocess
R=Path(__file__).resolve().parents[1];O=R/'build/sim/color_regions/transport';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','');logs=[]
for name,files in [('frame_store',['regions_frame_store.v']),('confirm',['regions_confirm.v']),('display',['regions_display.v'])]:
 for a in ([iv,'-g2012','-s','tb_color_regions_'+name,'-o',O/(name+'.vvp'),R/('sim/tb_color_regions_'+name+'.sv'),*[R/'rtl/color_regions'/f for f in files]],
           [iv.with_name('vvp.exe'),O/(name+'.vvp')]):
  p=subprocess.run(list(map(str,a)),cwd=R,env=env,capture_output=True,text=True,timeout=180);logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
  (R/'reports/color_regions_transport.log').write_text('\n'.join(logs),encoding='utf-8');assert p.returncode==0
