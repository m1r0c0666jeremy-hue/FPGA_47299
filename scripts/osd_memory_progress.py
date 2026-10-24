"""Read-only current-source progress using the audit's exact requirement list."""
import json,textwrap
import audit_refined as a
source=(a.R/'scripts/audit_refined.py').read_text(encoding='utf-8')
start=source.index("  prefixes=['source_time")
end=source.index("  result['regression']",start)
scope={'english':True}
exec(compile(textwrap.dedent(source[start:end]),'audit requirement list','exec'),scope)
valid={};missing=[]
for prefix in scope['prefixes']:
    try:valid[prefix]=a.evidence(prefix,a.required_inputs(prefix))
    except AssertionError:missing.append(prefix)
print(json.dumps(dict(valid=len(valid),required=len(scope['prefixes']),missing=missing),indent=2))
