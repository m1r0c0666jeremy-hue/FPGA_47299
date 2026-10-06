"""Reset the whole digital video model during active video, then verify a fresh frame."""
from pathlib import Path
import os,subprocess
r=Path(__file__).resolve().parents[1];out=r/'build/sim/improve_fourfold_scale'
bin=r/'tools/iverilog/ucrt64/bin';env=os.environ.copy();env['PATH']=str(bin)+os.pathsep+env.get('PATH','')
files=['sim/tb_fourfold_reset.sv','rtl/05_roi_processing/scaling_line_reader.v','rtl/05_roi_processing/bilinear_rgb.v','rtl/02_image_preprocess/image_preprocess.v',str(out/'image_preprocess_main.v'),*[f'rtl/09_osd_ui/{n}.v' for n in ['scaling_osd','scaling_glyph_rom','scaling_logo_rom']]]
subprocess.run(list(map(str,[bin/'iverilog.exe','-g2012','-s','tb_fourfold_reset','-o',out/'reset.vvp',*files])),cwd=r,env=env,check=True)
c=subprocess.run(list(map(str,[bin/'vvp.exe',out/'reset.vvp','+RESET=1','+ZOOM=2','+X=960','+Y=564','+MODE=2','+PATTERN=2'])),cwd=r,env=env,capture_output=True,text=True,timeout=600)
(r/'reports/fourfold_reset_simulation.log').write_text(c.stdout+c.stderr,encoding='utf-8');print(c.stdout+c.stderr)
assert c.returncode==0
