"""Native checkpoint and final physical review with exact source/constraint provenance."""
from pathlib import Path
import argparse,json,subprocess,re
from native_zoom_policy import R,sha,canonical_build_inputs,git
from refined_build_report import assess
from audit_stage1 import routing_audit,signature

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

def review(parent,route=None):
 parent=(R/parent).resolve();before=json.loads((parent/'inputs.json').read_text(encoding='utf-8'))
 canonical_build_inputs(before)
 summary=json.loads((parent/'summary.json').read_text(encoding='utf-8'));context=json.loads((parent/'source_context.json').read_text(encoding='utf-8'))
 assert summary['stage']=='place' and summary['exit_code']==0 and summary['inputs_unchanged'] and summary['resource_pass']
 assert before==json.loads((parent/'inputs_after.json').read_text(encoding='utf-8'))
 commit=context['compiled_source_commit']
 for n,h in before.items():
  assert sha(parent/'compiled_source'/n)==h
  data=subprocess.check_output(['git','show',commit+':'+n],cwd=R)
  import hashlib
  assert hashlib.sha256(data).hexdigest()==h,n
 for n in ('target_color_regions_gate.db','target_color_regions_placed.db'):
  assert sha(parent/n)==summary['checkpoints'][n]
 reuse=context.get('reused_gate')
 if reuse:
  origin=R/reuse['parent'];original_context=json.loads((origin/'source_context.json').read_text(encoding='utf-8'))
  assert original_context['compiled_source_commit']==commit
  assert before==json.loads((origin/'inputs.json').read_text(encoding='utf-8'))
  assert sha(origin/'target_color_regions_gate.db')==reuse['checkpoint_sha256']
  assert sha(origin/'summary.json')==reuse['parent_summary_sha256']
  assert all(sha(origin/'compiled_source'/n)==h for n,h in before.items())
  from native_gate_recovery import gate_recovery_proof
  original_summary=json.loads((origin/'summary.json').read_text(encoding='utf-8'))
  assert gate_recovery_proof(origin,original_summary['exit_code'],(origin/'td.log').read_text(encoding='utf-8'))==reuse['recovery']
 tcl=(parent/'run.tcl').read_text(encoding='utf-8');log=(parent/'td.log').read_text(encoding='utf-8')
 assert 'REFINED_PLACED_CHECKPOINT_READY' in log and 'BUILD_FAILED:' not in log
 clocks=(parent/'placed_clocks.txt').read_text(encoding='utf-8')
 for name in ('NATIVE_REF_CLK','NATIVE_PROCESS_CLK','HDMI_PIXEL_CLK','HDMI_SERIAL_CLK','MIPI_RX_BYTE_CLK'):assert name in clocks,name
 assert (parent/'placed_exceptions.timing').is_file()
 for name,period in (('NATIVE_REF_CLK',41.667),('NATIVE_PROCESS_CLK',16.667),('HDMI_PIXEL_CLK',13.333),('HDMI_SERIAL_CLK',2.667)):
  rows=[line for line in clocks.splitlines() if name in line and re.search(r'\b'+str(period)[:4],line)]
  assert rows,'Missing/incorrect effective period '+name
 ddr=[line for line in clocks.splitlines() if 'usr_clk' in line and re.search(r'\b7\.500\b',line)]
 assert ddr,'Native DDR user clock must be 133.333MHz, not inherited66.667MHz'
 result={'status':'PLACEMENT_PASSED_FINAL_ROUTE_PENDING','compiled_source_commit':commit,'compiler_input_count':len(before),
  'inputs_sha256':sha(parent/'inputs.json'),'parent':parent.relative_to(R).as_posix(),'parent_summary_sha256':sha(parent/'summary.json'),
  'resources':summary['resources'],'current_frozen_git_exact':True,'user_original_protected':True,'new_clocks_present':True}
 result['reused_gate']=reuse
 result['effective_parameters']=parameters(parent,summary,context)
 if route:
  route=(R/route).resolve();s=json.loads((route/'summary.json').read_text(encoding='utf-8'))
  assert s['stage']=='full' and s['exit_code']==0 and s['inputs_unchanged'] and s['working_tree_matches'] and s['checkpoint_unchanged']
  assert before==json.loads((route/'inputs.json').read_text(encoding='utf-8'))==json.loads((route/'inputs_after.json').read_text(encoding='utf-8'))
  for n,h in before.items():assert sha(route/'compiled_source'/n)==h
  measured=assess(route,'full');assert measured['resource_pass'] and measured['timing_pass'],measured
  result.update(measured);result['routing']=routing_audit(route/'td.log')
  for name in ('placed_clocks.txt','placed_exceptions.timing'):
   assert signature(parent/name,parent,route)==signature(route/name,parent,route),'Route changed operative constraints: '+name
  result.update(status='CANDIDATE_SOFTWARE_AND_FINAL_PHYSICAL_PASSED_HARDWARE_PENDING',route=route.relative_to(R).as_posix(),route_summary_sha256=sha(route/'summary.json'),bit_sha256=sha(route/'target_color_regions.bit'))
 return result

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--parent',required=True);ap.add_argument('--route');ap.add_argument('--output',required=True);a=ap.parse_args()
 result=review(a.parent,a.route);(R/a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result)
