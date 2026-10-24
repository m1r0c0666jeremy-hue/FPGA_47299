from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[2]
for name in ('test_stage1_controls_sequence.py','test_stage1_age_equivalence.py','test_stage1_camera.py'):
 p=subprocess.run([sys.executable,'-X','utf8',str(R/'scripts'/name)],cwd=R)
 if p.returncode:raise SystemExit(p.returncode)
print('RECT_LEGACY_GROUP_PASS',flush=True)
