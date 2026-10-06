"""Strict fault-boundary regression: every black pixel, including the first two."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import os, subprocess
r = Path(__file__).resolve().parents[1]
out = r / 'build/sim/improve_fourfold_scale'
bin = r / 'tools/iverilog/ucrt64/bin'
env = os.environ.copy()
env['PATH'] = str(bin) + os.pathsep + env.get('PATH', '')
files = ['sim/tb_fourfold_video.sv', 'rtl/05_roi_processing/scaling_line_reader.v',
         'rtl/05_roi_processing/bilinear_rgb.v', 'rtl/02_image_preprocess/image_preprocess.v',
         str(out / 'image_preprocess_main.v'),
         *[f'rtl/09_osd_ui/{n}.v' for n in ['scaling_osd', 'scaling_glyph_rom', 'scaling_logo_rom']]]
subprocess.run(list(map(str, [bin / 'iverilog.exe', '-g2012', '-s', 'tb_fourfold_video',
                            '-o', out / 'strict_fault.vvp', *files])), cwd=r, env=env, check=True)
def run(args):
    return subprocess.run(list(map(str, [bin / 'vvp.exe', out / 'strict_fault.vvp', *args])),
                          cwd=r, env=env, capture_output=True, text=True, timeout=1200)
cases = [['+ZOOM=2', '+X=0', '+Y=0', '+MODE=0', '+FAULT=1', '+FRAMES=2'],
         ['+ZOOM=2', '+X=960', '+Y=564', '+MODE=2', '+FAULT=2', '+FRAMES=3']]
with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(run, cases))
log = '\n'.join(c.stdout + c.stderr for c in results)
(r / 'reports/fourfold_fault_simulation.log').write_text(log, encoding='utf-8')
print(log)
assert all(c.returncode == 0 for c in results)
