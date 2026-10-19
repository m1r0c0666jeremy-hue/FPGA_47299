"""Freeze the approved Git baseline as standalone simulation inputs."""
from pathlib import Path
import subprocess,hashlib,json
R=Path(__file__).resolve().parents[1];base='43564ee356443ede2c03688a70f1c8a71ca6589b'
O=R/'sim/ring_baseline';O.mkdir(exist_ok=True)
manifest={}
def save(name,data):
    p=O/name
    if p.exists() and p.read_bytes()!=data:raise SystemExit('Refusing to replace '+str(p))
    if not p.exists():p.write_bytes(data)
    manifest[name]=hashlib.sha256(data).hexdigest()
for name in ('calibration','filter4','grid','tracker'):
    save('stable_'+name+'.v',subprocess.check_output(['git','show',base+':rtl/color_regions/stable_'+name+'.v'],cwd=R))
t=subprocess.check_output(['git','show',base+':scripts/test_stable_pipeline.py'],cwd=R).decode('utf-8')
save('tb_calibration.sv',('module tb;'+t.split("run('calibration','''module tb;",1)[1].split("''',['stable_calibration.v'",1)[0]).encode('utf-8'))
save('manifest.json',json.dumps(dict(commit=base,sha256=manifest),indent=2).encode('utf-8'))
print('RING_BASELINES_FROZEN',base)
