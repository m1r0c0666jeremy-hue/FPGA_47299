"""Exercise actual snapshot/edit/validation/reset overlap against frozen F."""
from refined_testlib import R,run
source=(R/'sim/stage1_snapshot_protocol_tb.sv').read_text(encoding='utf-8')
mods=[R/'rtl/color_regions'/(n+'.v') for n in ('stage1_arith','stage1_point','stage1_segment','stage1_validate','stage1_sequence','stage1_regions','stage1_render')]
mods += [R/'sim/stage1_snapshot_frozen_regions.v',R/'sim/stage1_snapshot_frozen_render.v']
run('stage1_snapshot_protocol',source,mods,timeout=1800)
