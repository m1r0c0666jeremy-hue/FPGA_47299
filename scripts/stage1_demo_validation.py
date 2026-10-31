"""Preserve the original155 checks, adding only colour and FPS checks."""
from pathlib import Path
import json


def demo_specs():
    data = json.loads((Path(__file__).parent/'demo1101_baseline_specs.json').read_text())
    assert data['source_commit'] == '4081ad0a067c7f1cca31fed15fc1bed8b210d704'
    assert len(data['checks']) == 155
    checks = {n: (value[0], tuple(value[1])) for n, value in data['checks'].items()}
    checks.update({
        'stage1_demo_fps': ('STAGE1_DEMO_FPS_PASS vectors5000',
                           ('stage1_memory_video_out',)),
        'stage1_demo_fps_footer': ('STAGE1_DEMO_FPS_FOOTER_PASS cases144',
                                  ('stage1_osd', 'stage1_ui_formatter')),
        'stage1_ry_bp_colours': ('STAGE1_RY_BP_COLOURS_PASS',
                               ('stable_calibration',)),
    })
    assert len(checks) == 158
    return checks
