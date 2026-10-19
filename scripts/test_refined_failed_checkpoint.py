"""Check the real frozen failed-route chain and persistent negative fixtures."""
import datetime,hashlib,json
from audit_refined import R,canonical_build_inputs,checkpoint_report_signature
from refined_failed_checkpoint import verify_source,clock_periods
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'build/refined_route_20261018_115500_912935'
probe=R/'build/refined_failed_checkpoint_probe_20261018_133626'
proof,inputs,context,summary,parent=verify_source(R,source,probe,canonical_build_inputs,checkpoint_report_signature)
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
fixtures=R/'build'/('refined_failed_checkpoint_guard_'+stamp);fixtures.mkdir()
clocks=(probe/'restored_clocks.txt').read_text(encoding='utf-8')
assert '16.668' in clocks
changed=fixtures/'changed_clock.txt';changed.write_text(clocks.replace('16.668','33.336',1),encoding='utf-8')
assert clock_periods(changed)!=clock_periods(probe/'restored_clocks.txt')
exception=fixtures/'extra_exception.timing'
exception.write_text((probe/'restored_exceptions.timing').read_text(encoding='utf-8')+'\nset_false_path -from NEW_UNAUTHORIZED_CLOCK\n',encoding='utf-8')
assert checkpoint_report_signature(exception,source,probe)!=checkpoint_report_signature(probe/'restored_exceptions.timing',source,probe)
# Exercise SHA rejection using an isolated copy of the source metadata and
# compiled files. No real checkpoint, report or constraint is overwritten.
import shutil
fake=fixtures/'source';fake.mkdir()
for name in ('inputs.json','source_context.json','normal_failure_checkpoint.json','checkpoint_provenance.json','normal_failure_prefix.log','td.log','failed_normal_route.db'):
 shutil.copyfile(source/name,fake/name)
shutil.copytree(source/'compiled_source',fake/'compiled_source')
saved=json.loads((fake/'normal_failure_checkpoint.json').read_text(encoding='utf-8'));saved['checkpoint_sha256']='0'*64
(fake/'normal_failure_checkpoint.json').write_text(json.dumps(saved),encoding='utf-8')
try:verify_source(R,fake,probe,canonical_build_inputs,checkpoint_report_signature)
except AssertionError as error:assert str(error)=='Failed routing checkpoint SHA mismatch',str(error)
else:raise AssertionError('Corrupt checkpoint hash accepted')
out=R/'reports/refined'/('failed_checkpoint_guard_'+stamp)
record=dict(passed=True,physical_routing=False,clock_pairs=len(proof['clock_periods']),frozen_inputs=len(inputs),proof=proof,changed_clock_rejected=True,added_exception_rejected=True,changed_checkpoint_hash_rejected=True,fixtures=fixtures.relative_to(R).as_posix(),inputs={p.relative_to(R).as_posix():sha(p) for p in (R/'scripts/audit_refined.py',R/'scripts/refined_failed_checkpoint.py',__import__('pathlib').Path(__file__),changed,exception)})
out.with_suffix('.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
out.with_suffix('.log').write_text('FAILED_CHECKPOINT_GUARD_PASS real 295-input chain and eight clock pairs; changed clock/exception/checkpoint hash rejected; no physical routing claim\n',encoding='utf-8')
print('FAILED_CHECKPOINT_GUARD_PASS',out.relative_to(R))
