from pathlib import Path
import datetime,json,re,sys,hashlib
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from stage1_policy import canonical_build_inputs,baseline_inputs,check_protected,sha
from audit_stage1 import audit
p=R/'build/stage1_route_20261024_051241_605588';inp=json.loads((p/'inputs.json').read_text());canonical_build_inputs(inp)
assert all(sha(p/'compiled_source'/n)==h for n,h in inp.items())
c=json.loads((p/'source_context.json').read_text());parent=c['placed_checkpoint'];bd=R/parent['parent'];assert sha(bd/parent['checkpoint_name'])==parent['checkpoint_sha256']
assert not (p/'summary.json').exists() and not (p/'target_color_regions.bit').exists()
s=audit();assert s['passed']==s['required']==110
log=(p/'td.log').read_text();iterations=[dict(iteration=int(m[1]),over_count=int(m[2]),over=int(m[3]),worst=int(m[4]),seconds=float(m[5])) for m in re.finditer(r'Iter (\d+):.*?over cnt = (\d+)\([^)]*\), over = (\d+), worst = (\d+),.*?time\(s\) = ([\d.]+)',log)]
assert len(iterations)==23 and iterations[-1]['over']==13085 and min(i['over'] for i in iterations)==10714
r=dict(status='CANCELLED_BY_AGENT_NOT_DELIVERABLE',time=datetime.datetime.now().astimezone().isoformat(),reason='E normal about67 minutes; iteration20 minimum10714 followed by11260/12274/13085. About22 minutes without new low; next-round stopping rule announced before iteration23, no new broader hotspot recovery. Quantify proven private shared-region-memory alternative instead of more blind long routing. This is incomplete cancellation, not a final native failure or pass.',attempt=p.relative_to(R).as_posix(),process_id=21588,process_started='2026-10-24T05:12:43.9004247+08:00',session_exit_code=1,route_result='CANCELLED_INCOMPLETE_NO_FINAL_ROUTING_OR_TIMING_RESULT',iterations=iterations,td_log_sha256=sha(p/'td.log'),source_context=c,input_count=len(inp),inputs_unchanged=True,frozen_inputs_unchanged=True,placed_checkpoint_unchanged=True,original_baseline_count=baseline_inputs(R),protected_files=check_protected(),final_timing_available=False,deliverable=False,software_report='reports/stage1/software_current_20261024_0532.json',software_checks=110,continuing_authorized_task=True,new_timer_created=False,producer_sha256=sha(Path(__file__)))
for dest in (p/'outcome.json',R/'reports/stage1/route_cancelled_20261024_0620.json'):
 with dest.open('x',encoding='utf-8') as f:json.dump(r,f,indent=2)
print('E_CANCELLED_INCOMPLETE;308 frozen/current, parentDB, original297/5 and current110 remain valid')
