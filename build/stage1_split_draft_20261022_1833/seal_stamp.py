"""Freeze private current-source evidence before any formal adoption."""
from pathlib import Path
import datetime,json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from audit_stage1 import sha
checks={}
for prefix,marker in {
 'private_split_stamp_guards':'STAGE1_RENDER_GUARDS_PASS',
 'private_split_stamp_edit_render':'PRIVATE_EDIT_RENDER_POINT_PASS pixels=134400',
 'private_split_stamp_render':'STAGE1_RENDER_PASS cases=14 pixels=11182080',
 'private_split_stamp_overlay':'STAGE1_OVERLAY_PASS cases=8 pixels=6389760',
}.items():
    for p in sorted((R/'reports/refined/regression').glob(prefix+'_*.json'),reverse=True):
        d=json.loads(p.read_text());log=p.with_suffix('.log')
        if d['exit_code'] or not all(sha(R/n)==h for n,h in d['inputs'].items()):continue
        if marker not in log.read_text():continue
        tb=Path(d['output'])/'tb.sv'
        checks[prefix]=dict(record=p.relative_to(R).as_posix(),record_sha256=sha(p),log_sha256=sha(log),
            bench=tb.relative_to(R).as_posix(),bench_sha256=sha(tb),inputs=d['inputs'])
        break
    else:raise AssertionError(prefix)
formal=json.loads((R/'build/stage1_route_20261022_171017_601880/inputs.json').read_text())
assert all(sha(R/n)==h for n,h in formal.items())
old=json.loads((R/'reports/stage1/software_current_20261022_1545.json').read_text());fixtures={}
for n in ('stage1_render_14_624','stage1_overlay','stage1_render_guards','stage1_regions'):
    fixtures.update(old['regression'][n]['fixture_inputs'])
assert all(sha(R/n)==h for n,h in fixtures.items())
baseline=json.loads((O/'gate_comparison.json').read_text())['outputs']['baseline']['resources']
candidate=json.loads((O/'gate_stamp_comparison.json').read_text())['outputs']['split_shared_stamp']['resources']
result=dict(scope='PRIVATE ONLY; NOT ADOPTED; isolated area is not whole-device fit/timing',time=datetime.datetime.now().isoformat(),
 checks=checks,reference_oracle_fixtures=fixtures,unchanged_formal_inputs=formal,
 baseline=baseline,candidate=candidate,slice_estimate_saved=baseline['slice']-candidate['slice'],
 producer_hashes={p.relative_to(R).as_posix():sha(p) for p in O.glob('*.py')},hardware_status='NOT TESTED')
with (O/'stamp_validation.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print('PRIVATE_STAMP_SEALED 4 fresh tests, 308 unchanged formal inputs, estimated slices saved',result['slice_estimate_saved'])
