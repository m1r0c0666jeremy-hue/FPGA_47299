"""Native checkpoint and final physical review with exact source/constraint provenance."""
from pathlib import Path
import argparse,json,subprocess,re
from native_zoom_policy import R,sha,canonical_build_inputs,git
from refined_build_report import assess
from audit_stage1 import routing_audit,signature

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
 assert not context.get('reused_gate'),'First native integration must synthesize its new source'
 tcl=(parent/'run.tcl').read_text(encoding='utf-8');log=(parent/'td.log').read_text(encoding='utf-8')
 assert 'REFINED_PLACED_CHECKPOINT_READY' in log and 'BUILD_FAILED:' not in log
 clocks=(parent/'target_color_regions_clocks.txt').read_text(encoding='utf-8')
 for name in ('NATIVE_REF_CLK','NATIVE_PROCESS_CLK','HDMI_PIXEL_CLK','HDMI_SERIAL_CLK','MIPI_RX_BYTE_CLK'):assert name in clocks,name
 assert (parent/'target_color_regions_exception.timing').is_file()
 result={'status':'PLACEMENT_PASSED_FINAL_ROUTE_PENDING','compiled_source_commit':commit,'compiler_input_count':len(before),
  'inputs_sha256':sha(parent/'inputs.json'),'parent':parent.relative_to(R).as_posix(),'parent_summary_sha256':sha(parent/'summary.json'),
  'resources':summary['resources'],'current_frozen_git_exact':True,'user_original_protected':True,'new_clocks_present':True}
 if route:
  route=(R/route).resolve();s=json.loads((route/'summary.json').read_text(encoding='utf-8'))
  assert s['stage']=='full' and s['exit_code']==0 and s['inputs_unchanged'] and s['working_tree_matches'] and s['checkpoint_unchanged']
  assert before==json.loads((route/'inputs.json').read_text(encoding='utf-8'))==json.loads((route/'inputs_after.json').read_text(encoding='utf-8'))
  for n,h in before.items():assert sha(route/'compiled_source'/n)==h
  measured=assess(route,'full');assert measured['resource_pass'] and measured['timing_pass'],measured
  result.update(measured);result['routing']=routing_audit(route/'td.log')
  for name in ('target_color_regions_clocks.txt','target_color_regions_exception.timing'):
   assert signature(parent/name,parent,route)==signature(route/name,parent,route),'Route changed operative constraints: '+name
  result.update(status='CANDIDATE_SOFTWARE_AND_FINAL_PHYSICAL_PASSED_HARDWARE_PENDING',route=route.relative_to(R).as_posix(),route_summary_sha256=sha(route/'summary.json'),bit_sha256=sha(route/'target_color_regions.bit'))
 return result

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--parent',required=True);ap.add_argument('--route');ap.add_argument('--output',required=True);a=ap.parse_args()
 result=review(a.parent,a.route);(R/a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result)
