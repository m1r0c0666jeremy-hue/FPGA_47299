"""Private experiments must never be mistaken for the formal compiler entry."""
import datetime,json,hashlib
from audit_refined import R,canonical_build_inputs
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
formal=R/'build/refined_route_20261018_115500_912935/inputs.json'
private=R/'build/refined_tracker_storage_place_20261018_131012/inputs.json'
normal=json.loads(formal.read_text());prototype=json.loads(private.read_text())
canonical_build_inputs(normal)
for label,inputs in [('private_entry',prototype),('private_plus_formal_label',{**prototype,'td_project/target_color_regions_refined.al':normal['td_project/target_color_regions_refined.al']}),('formal_plus_private_input',{**normal,'build/fake_private.v':'0'*64}),('drive_relative_escape',{**normal,'C:fake_private.v':'0'*64})]:
 try:canonical_build_inputs(inputs)
 except AssertionError:pass
 else:raise AssertionError('Private compiler inputs accepted: '+label)
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
p=R/'reports/refined'/f'canonical_entry_guard_{stamp}'
p.with_suffix('.log').write_text('CANONICAL_ENTRY_GUARD_PASS actual formal295 accepted; private, mixed and drive-relative manifests rejected; no physical result claimed\n',encoding='utf-8')
p.with_suffix('.json').write_text(json.dumps(dict(passed=True,formal_inputs=len(normal),private_rejections=4,inputs={x.relative_to(R).as_posix():sha(x) for x in (formal,private,R/'scripts/audit_refined.py',R/'scripts/test_refined_canonical_entry.py')}),indent=2),encoding='utf-8')
print('CANONICAL_ENTRY_GUARD_PASS',p.relative_to(R))
