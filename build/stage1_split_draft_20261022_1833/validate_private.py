"""Bind private replay evidence; this is never a formal candidate acceptance."""
from pathlib import Path
import datetime,json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];P=R/'build/stage1_shared_vertex_20261022';sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
from audit_stage1 import sha


def saved(prefix,marker):
    for p in sorted((R/'reports/refined/regression').glob(prefix+'_*.json'),reverse=True):
        d=json.loads(p.read_text())
        if d['exit_code'] or d.get('expected_failure'):continue
        if not all(sha(R/n)==h for n,h in d['inputs'].items()):continue
        log=p.with_suffix('.log')
        if marker not in log.read_text():continue
        tb=Path(d['output'])/'tb.sv'
        return dict(record=p.relative_to(R).as_posix(),record_sha256=sha(p),log_sha256=sha(log),
                    bench=tb.relative_to(R).as_posix(),bench_sha256=sha(tb),inputs=d['inputs'])
    raise AssertionError('Missing private current-source evidence: '+prefix)


previous=saved('private_split_draft_regions','STAGE1_REGIONS_PASS')
mods=[O/'stage1_regions_shared.v',P/'stage1_point.v',P/'stage1_validate.v']+[R/'rtl/color_regions'/(n+'.v') for n in ('stage1_arith','stage1_segment','stage1_sequence')]
run('private_split_shared_regions',(R/previous['bench']).read_text(),mods,timeout=300)
specs={
  'private_split_draft_regions':'STAGE1_REGIONS_PASS',
  'private_split_shared_regions':'STAGE1_REGIONS_PASS',
  'private_split_draft_render':'STAGE1_RENDER_PASS cases=14 pixels=11182080',
  'private_split_draft_overlay':'STAGE1_OVERLAY_PASS cases=8 pixels=6389760',
  'private_split_draft_guards':'STAGE1_RENDER_GUARDS_PASS',
  'private_shared_vertex_point':'STAGE1_POINT_PASS cases=516',
  'private_shared_vertex_validate':'STAGE1_VALIDATE_PASS cases=220',
}
checks={n:saved(n,marker) for n,marker in specs.items()}
proof=json.loads((R/'reports/stage1/software_current_20261022_1545.json').read_text())
fixtures={}
for name in ('stage1_regions','stage1_render_14_624','stage1_overlay','stage1_render_guards','stage1_point','stage1_validate'):
    fixtures.update(proof['regression'][name]['fixture_inputs'])
assert all(sha(R/n)==h for n,h in fixtures.items())
current=json.loads((R/'build/stage1_route_20261022_171017_601880/inputs.json').read_text())
assert all(sha(R/n)==h for n,h in current.items())
result=dict(scope='PRIVATE PROTOTYPE ONLY; NOT ADOPTED; no final resources/timing or board evidence',
  time=datetime.datetime.now().isoformat(),formal_function_commit='199a45767161d2cde66573878d17e075d1494887',
  unchanged_formal_inputs=len(current),checks=checks,reference_oracle_fixtures=fixtures,
  producers={p.relative_to(R).as_posix():sha(p) for p in (O/'probe.py',O/'replay.py',O/'guards.py',Path(__file__),R/'scripts/refined_testlib.py')},
  limitation='Editor and renderer replays plus shared-port editor test; actual maintained video wrappers/integration must be refreshed if adopted')
with (O/'private_validation.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print('PRIVATE_SPLIT_VALIDATION_PASS',len(checks),'checks; formal inputs unchanged',len(current),flush=True)
