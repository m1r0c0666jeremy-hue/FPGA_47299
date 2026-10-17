"""Verify real checkpoint clock/exception reports; reject semantic changes."""
from pathlib import Path
import datetime, hashlib, json, tempfile
from audit_refined import R, checkpoint_report_signature

parent=R/'build/refined_place_20261018_005818'
child=R/'build/refined_route_20261018_010650_797911'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert 'CHECKPOINT_CONSTRAINT_ROUNDTRIP_PASS' in (child/'td.log').read_text(encoding='utf-8')
checks=[]
with tempfile.TemporaryDirectory(prefix='checkpoint_reports_') as directory:
 for name in ('placed_clocks.txt','placed_exceptions.timing'):
  first=checkpoint_report_signature(parent/name,parent,child)
  assert first==checkpoint_report_signature(child/name,parent,child),name
  # A changed clock period or any extra exception must remain significant.
  changed=Path(directory)/name
  changed.write_text((child/name).read_text(encoding='utf-8')+'\nset_false_path -from NEW_UNAUTHORIZED_CLOCK\n',encoding='utf-8')
  assert first!=checkpoint_report_signature(changed,parent,child),name
  checks.append(dict(report=name,roundtrip_equal=True,added_exception_rejected=True,parent_sha256=sha(parent/name),restored_sha256=sha(child/name)))
 # The normalization is restricted to tool metadata rows, not arbitrary
 # occurrences of Date/Generated inside a clock name or exception.
 for value in ('clock Generated 100.0','set_clock Date: 16.668','Period: 16.668'):
  changed=Path(directory)/'semantic.txt';changed.write_text(value,encoding='utf-8')
  assert checkpoint_report_signature(changed,parent,child)==value
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
out=R/'reports/refined'/f'checkpoint_reports_{stamp}'
out.with_suffix('.json').write_text(json.dumps(dict(passed=True,parent=parent.relative_to(R).as_posix(),child=child.relative_to(R).as_posix(),checks=checks,inputs={p.relative_to(R).as_posix():sha(p) for p in (R/'scripts/audit_refined.py',R/'scripts/run_refined_route.py',Path(__file__))}),indent=2),encoding='utf-8')
out.with_suffix('.log').write_text('CHECKPOINT_REPORTS_PASS real reports equal except dates; added exception remains significant; no RTL/ADC/SDC changes\n',encoding='utf-8')
print('CHECKPOINT_REPORTS_PASS',out.relative_to(R))
