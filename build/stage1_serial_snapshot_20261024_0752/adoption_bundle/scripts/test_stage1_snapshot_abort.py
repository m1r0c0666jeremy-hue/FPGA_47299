"""A recommitted job must equal a fresh instance of the same current renderer."""
from refined_testlib import R,run
import hashlib
original=R/'rtl/color_regions/stage1_render.v';body=original.read_bytes()
needle=b'module stage1_render #';assert body.count(needle)==1
renamed=body.replace(needle,b'module stage1_render_clean_reference #',1)
folder=R/'build'/('stage1_snapshot_abort_reference_'+hashlib.sha256(body).hexdigest());folder.mkdir(exist_ok=True)
reference=folder/'stage1_render_clean_reference.v'
if reference.exists():assert reference.read_bytes()==renamed
else:
    with reference.open('xb') as f:f.write(renamed)
source=(R/'sim/stage1_snapshot_abort_tb.sv').read_text(encoding='utf-8')
run('stage1_snapshot_abort',source,[R/'rtl/color_regions/stage1_arith.v',original,reference],timeout=120)
