from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[2]
groups={
 'units':[['scripts/test_stage1_regions.py'],['scripts/test_stage1_ui.py'],['scripts/test_stage1_render_guards.py'],['scripts/test_stage1_rect.py'],['scripts/test_stage1_rect.py','--geometry']],
 'footer':[['scripts/test_stage1_footer.py'],['scripts/test_stage1_footer.py','--abort'],['scripts/test_stage1_footer.py','--wait']],
 'video':[['scripts/test_stage1_video.py','--full','--faults','--workers','8']],
 'live':[['scripts/test_stage1_live.py','--workers','4']],
 'guards':[['scripts/test_stage1_routing_guards.py'],['scripts/test_stage1_release_guards.py'],['scripts/test_stage1_gate_reuse_guards.py','--parent','build/stage1_place_20261023_032446']],
}
for args in groups[sys.argv[1]]:
 p=subprocess.run([sys.executable,'-X','utf8']+args,cwd=R)
 if p.returncode:raise SystemExit(p.returncode)
print('RECT_FORMAL_GROUP_PASS',sys.argv[1],flush=True)
