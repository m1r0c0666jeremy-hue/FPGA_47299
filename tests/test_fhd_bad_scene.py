"""A visibly different short CSI frame must never leak into HDMI video."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from refined_testlib import R
from refined_native_testlib import run_native

text=(R/'scripts/test_fhd_camera_hdmi.py').read_text(encoding='utf-8')
ns={};exec(compile(text[:text.rindex('\nrun_native(')],'full CSI to HDMI fixture','exec'),ns)
source=ns['source']
old="level=f>=7?8'h70:8'h50;"
assert old in source
source=source.replace(old,"level=f==10?8'ha0:(f>=7?8'h70:8'h50);")
# The encoder-side oracle accepts only the two valid complete scenes (0x50
# and 0x70). Any 0xa0 pixel from the truncated source frame is observable failure.
source=source.replace('FHD_CAMERA_HDMI_PASS','FHD_BAD_SCENE_HDMI_PASS')
run_native('fhd_camera_hdmi_bad_scene',source+'\n'+ns['phy']+'\n'+ns['cfg']+'\n'+ns['ddr']+'\n'+ns['core']+'\n'+ns['hdmiphy'],ns['mods'],
           compile_args=['-I'+str(R/'rtl/color_regions'),'-DFHD_BEHAVIORAL_RAM'],timeout=1800)
