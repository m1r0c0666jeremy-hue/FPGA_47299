"""Strict stable checkpoint review; compares actual clocks with the old release."""
from pathlib import Path
import json,re,subprocess,hashlib,argparse
from stage1_policy import sha,canonical_build_inputs
from refined_build_report import assess
R=Path(__file__).resolve().parents[1]
def route_execution(base,summary,log,tcl):
 starts=list(re.finditer(r'^RUN-1002 : start command "route"\s*$',log,re.M))
 assert starts,'Missing actual route command'
 prefix=log[:starts[-1].start()];overrides={}
 for match in re.finditer(r'^RUN-1002 : start command "set_param route ([a-z_]+) ([A-Za-z0-9_.-]+)"\s*$',prefix,re.M):
  key,value=match.groups()
  # TD6.2 omits this documented preset option from report_param output.
  # Accept only the fixed TimingUltra value actually logged and in frozen Tcl.
  assert key in base or (key=='postrt_opt_extra_round' and value=='4'),'Unknown route override '+key
  assert f'set_param route {key} {value}' in tcl,'Route setting is not in frozen Tcl'
  overrides[key]=value
 actual={**base,**overrides}
 assert actual.get('fix_hold')==actual.get('timing')=='on'
 performed='ROUTE_NORMAL_FAILED_RETRY_ROUTABILITY' in prefix
 assert performed==summary['route_retry_performed']
 assert len(starts)==(2 if performed else 1),'Unexpected number of route attempts'
 expected=summary['route_effort']
 if performed:
  assert summary['retry_routability'] and expected=='normal'
  marker=prefix.index('ROUTE_NORMAL_FAILED_RETRY_ROUTABILITY')
  assert re.search(r'RUN-1003 : finish command "route"',prefix[starts[0].end():marker])
  expected='routability'
 assert expected==summary['final_route_effort']==actual.get('effort')
 assert expected in ('normal','routability')
 return {'scope':'Final route command parameters; parent checkpoint plus executed overrides',
  'initial_effort':summary['route_effort'],'final_effort':expected,'retry_performed':performed,
  'route_command_count':len(starts),'overrides':overrides,'final_parameters':actual}

def parameters(parent,summary,context):
 def settings(path):
  pairs=[line.split('|') for line in path.read_text(encoding='utf-8').splitlines()]
  return {p[0].strip():p[1].strip() for p in pairs if len(p)>=3 and re.fullmatch(r'[a-z_]+',p[0].strip())}
 place=settings(parent/'effective_place.txt');route=settings(parent/'effective_route.txt')
 expected={'pr_strategy':str(summary['placement_strategy']),'effort':summary['place_effort'],
  'macro_performance':summary['macro_performance'],'max_fanout':str(summary['max_fanout']) if summary['max_fanout'] is not None else None}
 for n,v in expected.items():
  if v is not None:assert place.get(n)==v,'Actual place parameter differs: '+n
 assert route.get('fix_hold')=='on' and route.get('timing')=='on','Route disabled hold/timing checks'
 log=(parent/'td.log').read_text(encoding='utf-8');tcl=(parent/'run.tcl').read_text(encoding='utf-8')
 official=summary.get('official_strategy')
 if official:
  assert sha(parent/'official_strategy_ph1.json')==official['sha256']
  definitions=json.loads((parent/'official_strategy_ph1.json').read_text(encoding='utf-8'))
  for name,definition in official['selected'].items():
   assert definitions[name]==definition,'Official preset differs from frozen definition'
   for item in definition['params']:
    if context.get('reused_gate') and item['step'] in ('rtl','gate'):continue
    command='set_param '+item['step']+' '+item['param']+' '+str(item['val'])
    assert command in tcl and 'start command "'+command+'"' in log,'Preset was not applied: '+command
 if not context.get('reused_gate'):
  for stage,key,value in [('gate','map_mode',summary['map_mode']),('gate','pack_effort',summary['pack_effort']),
    ('rtl','infer_fsm',summary['infer_fsm']),('rtl','min_ripple_len',summary['min_ripple_len'])]:
   if value is None or value=='project':continue
   command=f'set_param {stage} {key} {value}'
   assert command in tcl and 'start command "'+command+'"' in log,'Synthesis setting not applied: '+command
 return {'place':place,'route':route,'place_sha256':sha(parent/'effective_place.txt'),'route_sha256':sha(parent/'effective_route.txt')}

def clocks(path):
 result={}
 for line in path.read_text(encoding='utf-8').splitlines():
  cols=[s.strip() for s in line.split('|')]
  if len(cols)>7 and cols[2]=='PH1P_PHY_GCLK':
   try:result[cols[5]]=float(cols[6])
   except ValueError:pass
 return result

def review(parent,route=None):
 parent=(R/parent).resolve();inputs=json.loads((parent/'inputs.json').read_text(encoding='utf-8'))
 canonical_build_inputs(inputs);assert len(inputs)==304
 s=json.loads((parent/'summary.json').read_text(encoding='utf-8'));ctx=json.loads((parent/'source_context.json').read_text(encoding='utf-8'))
 assert s['stage']=='place' and s['exit_code']==0 and s['inputs_unchanged'] and s['resource_pass']
 assert inputs==json.loads((parent/'inputs_after.json').read_text(encoding='utf-8'))
 assert not ctx.get('reused_gate'),'Stable release requires fresh synthesis'
 commit=ctx['compiled_source_commit'];assert re.fullmatch('[0-9a-f]{40}',commit)
 names=list(inputs);raw=subprocess.run(['git','cat-file','--batch'],cwd=R,input=('\n'.join(commit+':'+n for n in names)+'\n').encode(),capture_output=True,check=True).stdout
 offset=0
 for n in names:
  assert sha(parent/'compiled_source'/n)==inputs[n]
  end=raw.index(b'\n',offset);h=raw[offset:end];offset=end+1
  assert not h.endswith(b' missing'),n
  size=int(h.split()[-1]);assert hashlib.sha256(raw[offset:offset+size]).hexdigest()==inputs[n],n;offset+=size+1
 for n,h in s['checkpoints'].items():assert sha(parent/n)==h
 assert sha(R/'td_project/target_color_regions_stage1.al')=='6b9d309fdd45fedead3a1419d7ed0862d385f34d286f6bf74df517f3cbe55ad0'
 manifest=json.loads((R/'build/target_region_sequence_stage1_20261028_170103/source_files.json').read_text(encoding='utf-8'))
 baseline='build/stage1_place_20261028_160918/placed_clocks.txt'
 assert sha(R/baseline)==manifest[baseline]
 from stage1_ddr_contract import contract
 corrected=contract(R)
 expected=clocks(R/baseline)
 # Only the two clocks downstream of the approved DDR reference correction
 # change. Camera/HDMI/control/board clocks and all constraint files stay exact.
 if corrected['reference_mhz']==100:
  expected['u_video/u_ph1p35_324_ddr_wrapper/u_ddr2/usr_clk']=7.5
  expected['u_video/u_ph1p35_324_ddr_wrapper/u_ddr2/mcu_clk']=19.687
 else:
  assert corrected['profile']=='LEGACY_50MHZ_REFERENCE_CORRECTION_DEFERRED'
 actual=clocks(parent/'placed_clocks.txt')
 assert actual==expected,('Unexpected clock periods after DDR correction',actual,expected)
 measured=assess(parent,'place');assert measured['resource_pass'] and measured['resources']==s['resources']
 result=dict(status='PLACE_VERIFIED_FINAL_ROUTE_PENDING',parent=parent.relative_to(R).as_posix(),compiled_source_commit=commit,
  compiler_input_count=len(inputs),current_frozen_git_exact=True,resources=measured['resources'],clocks_ns=actual,
  effective_parameters=parameters(parent,s,ctx),parent_summary_sha256=sha(parent/'summary.json'),ddr_reference_contract=corrected)
 if route:
  from audit_stage1 import build_audit
  result['build']=build_audit(route,review_place=False)
  rp=(R/route).resolve();rs=json.loads((rp/'summary.json').read_text(encoding='utf-8'))
  result['route_execution']=route_execution(result['effective_parameters']['route'],rs,(rp/'td.log').read_text(encoding='utf-8'),(rp/'run.tcl').read_text(encoding='utf-8'))
  result['status']='CANDIDATE_PHYSICAL_PASS_HARDWARE_PENDING'
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--route');p.add_argument('--output',required=True);a=p.parse_args()
 d=review(a.parent,a.route);q=R/a.output
 with q.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
 print(json.dumps(d,ensure_ascii=False))
