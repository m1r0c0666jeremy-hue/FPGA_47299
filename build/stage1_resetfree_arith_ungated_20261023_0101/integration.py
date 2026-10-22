"""Replay sealed actual candidate benches without regenerating shared gold files."""
from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sealed=json.loads((O/'validation.json').read_text());assert sha(O/'stage1_arith.v')==sealed['candidate_sha256']
assert all(sha(R/n)==h for n,h in sealed['unchanged_formal_inputs'].items())
original=R/'reports/stage1/software_current_20261023_0002.json';proof=json.loads(original.read_text());checks={}
for name in ('stage1_point','stage1_validate','stage1_regions'):
 e=proof['regression'][name];record=R/e['record'];d=json.loads(record.read_text())
 assert d['exit_code']==0
 assert all(sha(R/n)==h for group in (e['inputs'],e['fixture_inputs'],e['producer_inputs']) for n,h in group.items())
 bench=Path(d['output'])/'tb.sv';assert str(bench.relative_to(R)).replace('\\','/') in {n.replace('\\','/') for n in e['fixture_inputs']}
 mods=[O/'stage1_arith.v' if Path(n).name=='stage1_arith.v' else R/n for n in d['inputs']]
 out=run('stage1_private_resetfree_replay_'+name,bench.read_text(),mods,timeout=300)
 saved=R/'reports/refined/regression'/(out.name+'.json');v=json.loads(saved.read_text());assert v['exit_code']==0
 checks[name]=dict(record=saved.relative_to(R).as_posix(),record_sha256=sha(saved),log_sha256=sha(saved.with_suffix('.log')),
   inputs=v['inputs'],fixtures=v['fixture_inputs'],producers=v['producer_inputs'],
   reference_record=e['record'],reference_record_sha256=sha(record),reference_inputs=e['inputs'],reference_fixtures=e['fixture_inputs'],reference_producers=e['producer_inputs'])
assert all(sha(R/n)==h for n,h in sealed['unchanged_formal_inputs'].items())
result=dict(status='PRIVATE_RESETFREE_INTEGRATION_PASS_NOT_ADOPTED',candidate_sha256=sha(O/'stage1_arith.v'),
 producer_sha256=sha(Path(__file__)),baseline_proof=original.relative_to(R).as_posix(),baseline_proof_sha256=sha(original),checks=checks)
with (O/'integration_validation.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print('PRIVATE_RESETFREE_INTEGRATION_PASS',len(checks))
