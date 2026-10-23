from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[2]
groups={'render':[['scripts/test_stage1_render_guards.py'],['scripts/test_stage1_render.py'],['scripts/test_stage1_overlay.py']],'footer':[['scripts/test_stage1_footer.py'],['scripts/test_stage1_footer.py','--abort'],['scripts/test_stage1_footer.py','--wait'],['scripts/test_stage1_region_footer.py']],'capacity':[['scripts/test_stage1_regions_capacity.py']],'video':[['scripts/test_stage1_video.py','--full','--faults','--workers','8']],'live':[['scripts/test_stage1_live.py','--workers','4']]}
for args in groups[sys.argv[1]]:
 p=subprocess.run([sys.executable,'-X','utf8']+args,cwd=R)
 if p.returncode:raise SystemExit(p.returncode)
print('F_FORMAL_GROUP_PASS',sys.argv[1],flush=True)
