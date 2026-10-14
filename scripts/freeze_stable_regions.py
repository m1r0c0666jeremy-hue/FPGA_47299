"""Freeze pre-change tracked inputs and protect every existing bit/source ZIP."""
from pathlib import Path
import hashlib,json,subprocess,datetime
R=Path(__file__).resolve().parents[1]
out=R/'reports/stable_regions_baseline.json'
if out.exists():raise SystemExit('Baseline already exists; refusing overwrite')
git=['git','-c',f'safe.directory={R.as_posix()}','-C',str(R)]
files=subprocess.check_output(git+['ls-files','-z']).decode().split('\0')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected={p.relative_to(R).as_posix():sha(p) for p in R.rglob('*') if p.is_file() and
 (p.suffix=='.bit' or p.suffix=='.zip' and 'snapshot' in p.name)}
out.write_text(json.dumps(dict(head=subprocess.check_output(git+['rev-parse','HEAD']).decode().strip(),
 branch=subprocess.check_output(git+['branch','--show-current']).decode().strip(),
 inputs={n:sha(R/n) for n in files if n and (R/n).is_file()},protected=protected),indent=2),encoding='utf-8')
print('FROZEN',len(files)-1,'tracked inputs;',len(protected),'protected artifacts')
