"""Archive passed rectangle software and final physical proof without touching inputs."""
from pathlib import Path
import json,subprocess,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from audit_stage1 import audit,sha
attempt='build/stage1_route_20261024_125519_122210';proof=audit(attempt)
assert proof['passed']==proof['required']==107 and not proof['missing']
assert proof['build']['routing']['routing_drc_pass']
paths={Path(__file__).resolve()}
git=['git','-c','safe.directory='+R.as_posix()]
assert not subprocess.check_output(git+['diff','--cached','--name-only'],cwd=R)
paths|={R/n for n in subprocess.check_output(git+['diff','--name-only','-z'],cwd=R).decode('utf8').split('\0') if n}
for n in ['routing_guards_20261024_130333.json','guards_20261024_130406.json','gate_reuse_guards_20261024_130407.json','placement_review_20261024_125507.json','final_rect_build_review_20261024_1304.json']:
 p=R/'reports/stage1'/n;paths.add(p);d=json.loads(p.read_text());paths|={R/k for k in d.get('fixtures',{})}
for directory in [R/attempt,R/'build/stage1_place_20261024_124631']:
 s=json.loads((directory/'summary.json').read_text());assert s['exit_code']==0 and s['inputs_unchanged']
 for n,h in {**s.get('checkpoints',{}),**s.get('route_checkpoints',{})}.items():assert sha(directory/n)==h
 paths|={p for p in directory.iterdir() if p.is_file() and p.suffix in ('.json','.tcl','.txt','.log','.area','.timing','.ts','.zip','.al','.qor')}
for folder in ['build/stage1_rect_place_review_20261024_1248','build/stage1_rect_audit_format_20261024_1304']:
 paths|={p for p in (R/folder).rglob('*') if p.is_file()}
manifest={p.relative_to(R).as_posix():sha(p) for p in sorted(paths)}
out=O/'manifest.json'
with out.open('x',encoding='utf8') as f:json.dump(dict(status='CURRENT_107_AND_FINAL_ZERO_DRC_NONNEGATIVE_TIMING_PASSED_HARDWARE_PENDING',compiler_commit=proof['build']['compiled_source_commit'],resources=proof['build']['summary']['resources'],slack_ns=proof['build']['summary']['slack_ns'],files=manifest),f,ensure_ascii=False,indent=2)
paths.add(out);payload=b''.join(p.relative_to(R).as_posix().encode('utf8')+b'\0' for p in sorted(paths))
subprocess.run(git+['add','-f','--pathspec-from-file=-','--pathspec-file-nul'],input=payload,cwd=R,check=True)
assert all(sha(R/n)==h for n,h in manifest.items())
subprocess.run(git+['commit','-m','stage1: archive rectangle zero-conflict final route and passing timing'],cwd=R,check=True,stdout=subprocess.DEVNULL)
print('RECT_FINAL_ARCHIVED',len(paths),proof['build']['summary']['slack_ns'])
