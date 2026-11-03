"""Read-only verification of the fresh full-source placement; no CAD calls."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,sys
O=Path(__file__).resolve().parent;R=O.parents[1]
sys.path.insert(0,str(R/'scripts'))
from stage1_policy import canonical_build_inputs,baseline_inputs,check_protected,sha
from refined_build_report import assess
p=R/'build/stage1_place_20261024_090145'
s=json.loads((p/'summary.json').read_text());c=json.loads((p/'source_context.json').read_text())
assert s['stage']=='place' and s['exit_code']==0 and s['resource_pass'] and s['inputs_unchanged']
assert assess(p,'place')['resources']==s['resources']
before=json.loads((p/'inputs.json').read_text());canonical_build_inputs(before)
assert before==json.loads((p/'inputs_after.json').read_text())
assert all(sha(p/'compiled_source'/n)==h for n,h in before.items())
commit=c['compiled_source_commit'];assert c['input_count']==len(before) and c['inputs_sha256']==sha(p/'inputs.json')
names=list(before)
raw=subprocess.run(['git','-c','safe.directory='+R.as_posix(),'cat-file','--batch'],cwd=R,input=('\n'.join(commit+':'+n for n in names)+'\n').encode(),capture_output=True,check=True).stdout
offset=0
for n in names:
    end=raw.index(b'\n',offset);header=raw[offset:end];offset=end+1
    assert not header.endswith(b' missing'),n
    size=int(header.split()[-1]);assert hashlib.sha256(raw[offset:offset+size]).hexdigest()==before[n],n;offset+=size+1
assert all(sha(p/n)==h for n,h in s['checkpoints'].items())
assert 'REFINED_PLACED_CHECKPOINT_READY' in (p/'td.log').read_text()
params={}
for filename in ('effective_place.txt','effective_route.txt'):
    params[filename]={}
    for line in (p/filename).read_text().splitlines():
        parts=[x.strip() for x in line.split('|')]
        if len(parts)>=3 and re.fullmatch('[a-z_]+',parts[0]) and parts[0]!='Parameters':params[filename][parts[0]]=parts[1]
assert params['effective_place.txt']['pr_strategy']=='2'
assert params['effective_place.txt']['max_fanout']=='999999'
assert params['effective_route.txt']['fix_hold']=='on' and params['effective_route.txt']['timing']=='on'
old=json.loads((R/'build/stage1_place_20261024_004652/summary.json').read_text())['resources']
result=dict(status='PLACEMENT_PASSED_FINAL_ROUTE_PENDING',attempt=p.relative_to(R).as_posix(),compiled_source_commit=commit,input_count=len(before),git_blob_inputs_verified=len(before),resources=s['resources'],previous_C_004652=old,delta={n:s['resources'][n]-old[n] for n in old},checkpoints=s['checkpoints'],reused_gate=c['reused_gate'],actual_parameters=params,parameter_reports={n:sha(p/n) for n in params},original_baseline_count=baseline_inputs(R),protected_files=check_protected(),hardware_status='PENDING')
pre_C=json.loads((R/'build/stage1_place_20261023_223056/summary.json').read_text())['resources']
result['previous_pre_C_223056']=pre_C
result['delta_vs_pre_C_223056']={n:s['resources'][n]-pre_C[n] for n in pre_C}
previous_D=json.loads((R/'build/stage1_place_20261024_032009/summary.json').read_text())['resources']
result['previous_D_032009']=previous_D
result['delta_vs_D_032009']={n:s['resources'][n]-previous_D[n] for n in previous_D}
previous_E=json.loads((R/'build/stage1_place_20261024_044722/summary.json').read_text())['resources']
result['previous_E_044722']=previous_E
result['delta_vs_E_044722']={n:s['resources'][n]-previous_E[n] for n in previous_E}
previous_F=json.loads((R/'build/stage1_place_20261024_062426/summary.json').read_text())['resources']
result['previous_F_062426']=previous_F
result['delta_vs_F_062426']={n:s['resources'][n]-previous_F[n] for n in previous_F}
output=R/'reports/stage1'/('placement_review_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.json')
with output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps(result),flush=True)
