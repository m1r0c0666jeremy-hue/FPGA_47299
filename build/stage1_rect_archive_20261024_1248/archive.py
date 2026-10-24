"""Seal the current 107-check rectangle proof; do not touch active CAD outputs."""
from pathlib import Path
import datetime,json,subprocess,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from audit_stage1 import audit,sha
report=R/'reports/stage1/software_current_20261024_1246.json'
proof=json.loads(report.read_text(encoding='utf8'));fresh=audit()
assert proof['required']==proof['passed']==fresh['passed']==fresh['required']==107
assert not proof['missing'] and proof['regression']==fresh['regression']
assert fresh['original_protection_pass'] and fresh['generator_pass']
paths={report,Path(__file__).resolve(),R/'scripts/package_stage1.py'}
for e in proof['regression'].values():
    record=R/e['record'];assert sha(record)==e['record_sha256'] and sha(record.with_suffix('.log'))==e['log_sha256']
    paths.update((record,record.with_suffix('.log')))
    for group in ('inputs','fixture_inputs','producer_inputs'):
        for n,h in e[group].items():
            p=(R/n).resolve();assert p.is_relative_to(R) and sha(p)==h,n;paths.add(p)
assert report.relative_to(R).as_posix().encode() in (R/'scripts/package_stage1.py').read_bytes()
manifest={p.relative_to(R).as_posix():sha(p) for p in sorted(paths)}
out=O/'manifest.json'
with out.open('x',encoding='utf8') as f:json.dump(dict(status='RECTANGLE_CURRENT_107_SOFTWARE_ARCHIVE_FINAL_PHYSICAL_PENDING',compiler_commit=proof['head'],software=report.relative_to(R).as_posix(),files=manifest,hardware_status='PENDING'),f,ensure_ascii=False,indent=2)
paths.add(out)
git=['git','-c','safe.directory='+R.as_posix()]
assert not subprocess.check_output(git+['diff','--cached','--name-only'],cwd=R)
payload=b''.join(p.relative_to(R).as_posix().encode('utf8')+b'\0' for p in sorted(paths))
subprocess.run(git+['add','-f','--pathspec-from-file=-','--pathspec-file-nul'],input=payload,cwd=R,check=True)
assert all(sha(R/n)==h for n,h in manifest.items())
subprocess.run(git+['commit','-m','stage1: archive current rectangle 107 software checks'],cwd=R,check=True)
print('RECTANGLE_107_ARCHIVED',len(paths),sum(p.stat().st_size for p in paths))
