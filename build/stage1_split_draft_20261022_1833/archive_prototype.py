"""Archive only explicit prototype sources and their bound evidence; no binaries."""
from pathlib import Path
import json,subprocess
O=Path(__file__).resolve().parent;R=O.parents[1];P=R/'build/stage1_shared_vertex_20261022'
git=['git','-c','safe.directory='+R.as_posix()]
staged=set(subprocess.check_output(git+['diff','--cached','--name-only','-z'],cwd=R).decode().split('\0'))-{''}
files=set()
for folder in (O,P):
    files|={p for p in folder.iterdir() if p.is_file() and p.suffix in ('.py','.v','.md','.json')}
files.add(R/'build/stage1_span_probe_20261021_1110/probe.py')
for name in ('private_validation.json','stamp_validation.json'):
    d=json.loads((O/name).read_text())
    for e in d['checks'].values():
        record=R/e['record'];files|={record,record.with_suffix('.log'),R/e['bench']}
    files|={R/n for n in d.get('reference_oracle_fixtures',{})}
for name in ('gate_comparison.json','gate_stamp_comparison.json'):
    d=json.loads((O/name).read_text())
    for e in d['outputs'].values():
        folder=R/e['directory']
        files|={p for p in folder.iterdir() if p.is_file() and p.suffix in ('.v','.al','.tcl','.area','.log','.json')}
files|={R/'docs/区域顺序_第一阶段_执行记录.md',R/'reports/stage1/route_cancelled_20261022_1913.json'}
folder=R/'build/stage1_route_20261022_171017_601880'
files|={folder/n for n in ('outcome.json','td.log','inputs.json','source_context.json','checkpoint_provenance.json')}
assert all(p.is_file() and p.is_relative_to(R) for p in files)
names={p.relative_to(R).as_posix() for p in files}
assert staged<=names,'Preserve unrelated staging'
subprocess.run(git+['add','-f','--']+sorted(names),cwd=R,check=True)
subprocess.run(git+['diff','--cached','--stat'],cwd=R,check=True)
print('EXPLICIT_PROTOTYPE_ARCHIVE_STAGED',len(files))
