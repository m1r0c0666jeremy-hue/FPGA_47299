"""Bind the completed private replay to current sources, saved gold data and benches."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
private=json.loads((O/'validation.json').read_text())
reference=R/'reports/stage1/software_current_20261022_2123.json';old=json.loads(reference.read_text())
assert len(private['checks'])==4 and sha(O/'stage1_render.v')==private['candidate_sha256']
assert all(sha(R/n)==h for n,h in private['unchanged_formal_inputs'].items())
checks={}
for label,e in private['checks'].items():
    record=R/e['record'];log=record.with_suffix('.log');d=json.loads(record.read_text())
    assert sha(record)==e['record_sha256'] and sha(log)==e['log_sha256'] and d['exit_code']==0
    inputs={n.replace('\\','/'):h for n,h in d['inputs'].items()}
    fixtures=old['regression'][label]['fixture_inputs'];producers=old['regression'][label]['producer_inputs']
    assert all(sha(R/n)==h for group in (inputs,fixtures,producers) for n,h in group.items())
    bench=Path(d['output'])/'tb.sv'
    checks[label]=dict(**e,inputs=inputs,bench=bench.relative_to(R).as_posix(),bench_sha256=sha(bench),
                       reference_fixtures=fixtures,reference_producers=producers)
result=dict(scope='PRIVATE FOUR ROWS ONLY; no resource or final physical result; not adopted',
    time=datetime.datetime.now().isoformat(),checks=checks,reference=reference.relative_to(R).as_posix(),reference_sha256=sha(reference),
    candidate_sha256=sha(O/'stage1_render.v'),producer_sha256=sha(O/'probe.py'),seal_producer_sha256=sha(Path(__file__)),
    unchanged_formal_inputs=private['unchanged_formal_inputs'])
with (O/'sealed_validation.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print('PRIVATE_FOUR_ROW_SEALED four checks; formal source unchanged; NOT ADOPTED')
