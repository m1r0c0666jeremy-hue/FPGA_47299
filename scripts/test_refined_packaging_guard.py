"""A failed TD attempt must not publish artifacts or modify delivery pointers."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
attempts=[R/'build/refined_full_20261017_224454',R/'build/refined_route_20261018_010650_797911']
docs=[R/'README.md',R/'reports/refined/最终验证报告.md',R/'docs/颜色视频显示改进_上板一页.md']
before={p.relative_to(R).as_posix():sha(p) for p in docs}
directories={p.name for p in (R/'build').glob('target_color_regions_refined_*')}
logs=[];cases=[]
for attempt in attempts:
 summary=json.loads((attempt/'summary.json').read_text(encoding='utf-8'))
 assert summary['exit_code']!=0
 p=subprocess.run([sys.executable,'-X','utf8',str(R/'scripts/package_refined.py'),'--attempt',str(attempt)],cwd=R,capture_output=True,text=True,encoding='utf-8')
 log=p.stdout+p.stderr
 assert p.returncode!=0 and f"'exit_code': {summary['exit_code']}" in log,log
 assert 'Missing current-source passing evidence' not in log,log
 assert before=={p.relative_to(R).as_posix():sha(p) for p in docs}
 assert directories=={p.name for p in (R/'build').glob('target_color_regions_refined_*')}
 logs.append(attempt.relative_to(R).as_posix()+'\n'+log)
 cases.append(dict(attempt=attempt.relative_to(R).as_posix(),build_exit_code=summary['exit_code'],guard_exit_code=p.returncode,checkpoint=bool(summary.get('checkpoint_provenance'))))
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
out=R/'reports/refined'/f'packaging_guard_{stamp}'
out.with_suffix('.log').write_text('\n'.join(logs)+'\nPACKAGING_GUARD_PASS stopped full and actual failed checkpoint TD rejected before artifact publication; docs and directories unchanged\n',encoding='utf-8')
inputs={p.relative_to(R).as_posix():sha(p) for p in [R/'scripts/package_refined.py',R/'scripts/audit_refined.py',Path(__file__),*[a/'summary.json' for a in attempts]]}
out.with_suffix('.json').write_text(json.dumps(dict(passed=True,expected_build_rejection=True,cases=cases,inputs=inputs,protected_document_hashes=before),ensure_ascii=False,indent=2),encoding='utf-8')
print('PACKAGING_GUARD_PASS no deliverable or document changes from failed build',out.relative_to(R))
