from pathlib import Path
import os,subprocess
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'build/sim/color_regions/osd';O.mkdir(parents=True,exist_ok=True)
preview=R/'reports/color_regions_preview';preview.mkdir(exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','');logs=[]
cmd=[iv,'-g2012','-s','tb_color_regions_osd','-o',O/'osd.vvp',R/'sim/tb_color_regions_osd.sv',R/'rtl/color_regions/regions_osd.v',R/'rtl/color_regions/regions_glyph_rom.v']
p=subprocess.run(list(map(str,cmd)),env=env,cwd=R,capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
for mode,hide,zoom,pair in [(0,0,0,0),(1,0,0,0),(2,0,0,0),(3,0,0,0),(1,1,0,0),(0,0,1,0),(1,0,2,0),(0,0,2,1)]:
 ppm=O/f'{mode}_{hide}_{zoom}_{pair}.ppm';p=subprocess.run([str(iv.with_name('vvp.exe')),str(O/'osd.vvp'),f'+MODE={mode}',f'+HIDE={hide}',f'+ZOOM={zoom}',f'+PAIR={pair}',f'+CAPTURE={ppm.as_posix()}'],env=env,cwd=R,capture_output=True,text=True,timeout=120)
 logs.append(p.stdout+p.stderr);print(logs[-1],flush=True);(R/'reports/color_regions_osd.log').write_text('\n'.join(logs),encoding='utf-8');assert p.returncode==0
 with Image.open(ppm) as im:im.save(preview/f'page_{mode}_hidden_{hide}_zoom_{zoom}_pair_{pair}.png')
