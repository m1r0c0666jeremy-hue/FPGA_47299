from pathlib import Path
import datetime,json,re,sys,hashlib
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from stage1_policy import canonical_build_inputs,baseline_inputs,check_protected,sha
from audit_stage1 import audit
p=R/'build/stage1_route_20261024_064219_494771';inp=json.loads((p/'inputs.json').read_text());canonical_build_inputs(inp)
assert all(sha(p/'compiled_source'/n)==h for n,h in inp.items())
c=json.loads((p/'source_context.json').read_text());parent=c['placed_checkpoint'];bd=R/parent['parent'];assert sha(bd/parent['checkpoint_name'])==parent['checkpoint_sha256']
assert sha(p/parent['checkpoint_name'])==parent['checkpoint_sha256']
assert not (p/'summary.json').exists() and not (p/'target_color_regions.bit').exists()
s=audit();assert s['passed']==s['required']==110
log=(p/'td.log').read_text();iterations=[dict(iteration=int(m[1]),over_count=int(m[2]),over=int(m[3]),worst=int(m[4]),seconds=float(m[5])) for m in re.finditer(r'Iter (\d+):.*?over cnt = (\d+)\([^)]*\), over = (\d+), worst = (\d+),.*?time\(s\) = ([\d.]+)',log)]
assert datetime.datetime.now().astimezone()>=datetime.datetime.fromisoformat('2026-10-24T08:19:08+08:00')
assert list(re.finditer(r'Iter [0-9]+:',log))[-1].start()>list(re.finditer('Marking ',log))[-1].start()
assert len(iterations)==18 and iterations[-1]['over']==19680 and min(i['over'] for i in iterations)==13337
r=dict(status='CANCELLED_BY_AGENT_NOT_DELIVERABLE',time=datetime.datetime.now().astimezone().isoformat(),reason='F routability about128 minutes. First20percent recovery reached iteration14 minimum13337, then15/16/17 rose15257/16400/18293. Announced30-minute stopping rule was extended exactly one round for the second20percent recovery; iteration18 still19680 and1393.51seconds. About one hour without a new low. Preserve all results and quantify fully software-proven six-check G3 serial-snapshot structure. Incomplete agent cancellation is not a final native failure or pass.',attempt=p.relative_to(R).as_posix(),process_id=42440,process_started='2026-10-24T06:42:21.5596828+08:00',session_exit_code=1,route_result='CANCELLED_INCOMPLETE_NO_FINAL_ROUTING_OR_TIMING_RESULT',iterations=iterations,td_log_sha256=sha(p/'td.log'),source_context=c,input_count=len(inp),inputs_unchanged=True,frozen_inputs_unchanged=True,placed_checkpoint_unchanged=True,original_baseline_count=baseline_inputs(R),protected_files=check_protected(),final_timing_available=False,deliverable=False,software_report='reports/stage1/software_current_20261024_0708.json',software_checks=110,continuing_authorized_task=True,new_timer_created=False,producer_sha256=sha(Path(__file__)))
for dest in (p/'outcome.json',R/'reports/stage1/route_cancelled_20261024_0850.json'):
 with dest.open('x',encoding='utf-8') as f:json.dump(r,f,indent=2)
print('F_CANCELLED_INCOMPLETE;308 frozen/current, parentDB, original297/5 and current110 remain valid')
