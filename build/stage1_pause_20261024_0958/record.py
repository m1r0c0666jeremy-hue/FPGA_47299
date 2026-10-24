"""Read-only integrity checks and a user-requested pause record; no build/tests."""
from pathlib import Path
import datetime,json,re,subprocess,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from stage1_policy import canonical_build_inputs,baseline_inputs,check_protected,sha
count=subprocess.check_output(['powershell','-NoProfile','-Command',
    '@(Get-Process -Name td_commands_prompt,vvp -ErrorAction SilentlyContinue).Count'],text=True).strip()
assert count=='0'
count=subprocess.check_output(['powershell','-NoProfile','-Command',
    '@(Get-Process -Id 2512,38760,39712 -ErrorAction SilentlyContinue).Count'],text=True).strip()
assert count=='0'
p=R/'build/stage1_route_20261024_092334_800316'
inputs=json.loads((p/'inputs.json').read_text());canonical_build_inputs(inputs)
assert all(sha(p/'compiled_source'/n)==h for n,h in inputs.items())
context=json.loads((p/'source_context.json').read_text());checkpoint=context['placed_checkpoint']
assert sha(p/checkpoint['checkpoint_name'])==sha(R/checkpoint['parent']/checkpoint['checkpoint_name'])==checkpoint['checkpoint_sha256']
assert not (p/'summary.json').exists() and not (p/'target_color_regions.bit').exists()
report=R/'reports/stage1/software_current_20261024_0944.json'
software=json.loads(report.read_text(encoding='utf8'));assert software['passed']==software['required']==112 and not software['missing']
for e in software['regression'].values():
    assert sha(R/e['record'])==e['record_sha256']
    assert sha((R/e['record']).with_suffix('.log'))==e['log_sha256']
    for group in ('inputs','fixture_inputs','producer_inputs'):
        assert all(sha(R/n)==h for n,h in e[group].items())
log=(p/'td.log').read_text()
iterations=[dict(iteration=int(m[1]),over_count=int(m[2]),over=int(m[3]),worst=int(m[4]),seconds=float(m[5]))
    for m in re.finditer(r'Iter (\d+):.*?over cnt = (\d+)\([^)]*\), over = (\d+), worst = (\d+),.*?time\(s\) = ([\d.]+)',log)]
assert iterations[-1]['iteration']==19 and iterations[-1]['over']==10056
assert min(i['over'] for i in iterations)==9804
result=dict(status='PAUSED_BY_USER_NOT_DELIVERABLE',time=datetime.datetime.now().astimezone().isoformat(),
    reason='Jeremy requested pause and read-only assessment of replacing arbitrary polygons with axis-aligned rectangles. Stop completion Python first, then route wrapper; both sessions exited1 by explicit Ctrl-C. This is an incomplete user cancellation, not a native final routing failure or pass.',
    attempt=p.relative_to(R).as_posix(),native_pid=38760,route_session=11752,
    completion_pid=2512,completion_session=63685,processes_stopped=True,session_exit_code=1,
    td_log_sha256=sha(p/'td.log'),source_context=context,iterations=iterations,
    input_count=len(inputs),current_and_frozen_inputs_unchanged=True,placed_checkpoint_unchanged=True,
    baseline_input_count=baseline_inputs(R),protected_files=check_protected(),
    software_report=report.relative_to(R).as_posix(),software_report_sha256=sha(report),current_checks=112,
    final_timing_available=False,deliverable=False,no_new_build_simulation_or_package=True,
    noon_heartbeat_must_honor_this_later_pause=True,producer_sha256=sha(Path(__file__)))
for dest in (p/'outcome.json',R/'reports/stage1/pause_20261024_0958.json'):
    with dest.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
dest=R/'build/stage1_completion_20261024_0949/outcome.json'
assert not dest.exists()
with dest.open('x',encoding='utf8') as f:json.dump(dict(status='CANCELLED_BY_USER_PAUSE_NO_PACKAGING',
    time=result['time'],pid=2512,session_exit_code=1,pause_record='reports/stage1/pause_20261024_0958.json'),f,indent=2)
print('USER_PAUSE_RECORDED latest_over=10056 minimum_over=9804; no CAD/VVP/completion; current112 and308/297/5 protected')
