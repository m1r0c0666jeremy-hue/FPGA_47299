from pathlib import Path
import subprocess,os
R=Path(__file__).resolve().parents[1];O=R/'build/sim/color_regions/association';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','');logs=[]
files=[R/'sim/tb_color_regions_association.sv',R/'rtl/04_tracking/target_mailbox.v',*[R/f'rtl/color_regions/regions_{s}.v' for s in ('frame_store','display','line_reader')]]
for command in ([iv,'-g2012','-s','tb_color_regions_association','-o',O/'association.vvp',*files],[iv.with_name('vvp.exe'),O/'association.vvp']):
 p=subprocess.run(list(map(str,command)),cwd=R,env=env,capture_output=True,text=True,timeout=90)
 logs.append(p.stdout+p.stderr);print(logs[-1],flush=True);(R/'reports/color_regions_association.log').write_text('\n'.join(logs),encoding='utf-8');assert p.returncode==0
