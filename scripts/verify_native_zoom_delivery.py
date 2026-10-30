"""Independent, read-only verification of a native source ZIP and physical receipts."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,zipfile,re
H=lambda b:hashlib.sha256(b).hexdigest()

def verify_final_route_log(log):
 start=log.rfind('RUN-1002 : start command "route"');assert start>=0
 final=log[start:]
 drcs=list(re.finditer(r'^PHY-1001 : Stage (\d+) \| Routing DRC\s*$',final,re.M))
 assert len(drcs)==1,'Missing or ambiguous final Routing DRC'
 drc=drcs[0];stage=drc[1]
 end=re.search(r'^PHY-1001 : End Stage '+stage+r' \| Routing DRC;',final,re.M)
 assert end and end.start()>drc.end(),'Incomplete Routing DRC'
 values=re.findall(r'over cnt = (\d+)\([^)]*\), over = (\d+), worst = (\d+)',final[:drc.start()])
 assert values and tuple(map(int,values[-1]))==(0,0,0),'Final routing conflicts remain'
 body=final[drc.end():end.start()]
 assert 'No multi-drive.' in body and 'No abnormal timing path.' in body
 bound=re.search(r'^PHY-1001 : Stage '+stage+r'\.6 \| Bound Check\s*$(.*?)^PHY-1001 : End Stage '+stage+r'\.6 \| Bound Check;',body,re.M|re.S)
 assert bound and 'Check Pass.' in bound[1],'Final Bound Check did not pass'
 finish=final.find('RUN-1003 : finish command "route"',end.end())
 assert finish>=0 and final.find('REFINED_CHECKPOINT_FULL_COMPLETED',finish)>finish,'Final completion is missing or out of order'
 assert 'BUILD_FAILED:' not in final

def verify(folder):
 folder=Path(folder);delivery=json.loads((folder/'delivery.json').read_text(encoding='utf-8'))
 assert delivery['status']=='CANDIDATE_SOFTWARE_AND_FINAL_PHYSICAL_PASSED_HARDWARE_PENDING'
 assert delivery['archive_name']=='原生2倍细节与三档倍率候选'
 for n,h in delivery['artifacts'].items():assert H((folder/n).read_bytes())==h,n
 with zipfile.ZipFile(folder/'native_zoom_same_source.zip') as z:
  names=z.namelist();assert len(names)==len(set(names))
  assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n and ':' not in n for n in names)
  manifest=json.loads(z.read('SOURCE_MANIFEST.json'))
  assert set(names)==set(manifest)|{'SOURCE_MANIFEST.json'}
  for n,h in manifest.items():assert H(z.read(n))==h,n
  def read(n):return json.loads(z.read(n))
  soft=read('qualification/software.json');physical=read('qualification/physical.json');inputs=read('qualification/inputs.json')
  assert H(z.read('qualification/software.json'))==delivery['software_sha256']
  assert H(z.read('qualification/physical.json'))==delivery['physical_sha256']
  assert soft['status']=='PASS' and soft['native_required']==soft['native_passed']==63
  assert soft['legacy_required']==soft['legacy_passed']==155 and not soft['missing_native'] and not soft['missing_legacy']
  assert len(soft['native'])==63 and {'fixed_arithmetic','transitions','capture_shared_masks','capture_shared_full','capture_shared_fault','capture_shared_reducer'}<=set(soft['native']) and len(soft['legacy_unchanged'])==155
  assert inputs==soft['compiler_inputs']
  assert inputs==read('qualification/place/inputs.json')==read('qualification/route/inputs.json')==read('qualification/route/inputs_after.json')
  assert len(inputs)==physical['compiler_input_count']==327
  assert physical['compiled_source_commit']==delivery['compiled_source_commit']
  for stage in ('place','route'):
   summary=read('qualification/'+stage+'/summary.json')
   assert summary['exit_code']==0 and summary['inputs_unchanged'] and summary['working_tree_matches']
  params=physical['effective_parameters']
  assert H(z.read('qualification/place/effective_place.txt'))==params['place_sha256']
  assert H(z.read('qualification/place/effective_route.txt'))==params['route_sha256']
  assert params['route']['fix_hold']==params['route']['timing']=='on'
  options=read('qualification/place/flow_options.json')['options']
  assert params['place']['pr_strategy']==str(options['strategy']) and params['place']['max_fanout']==str(options['max_fanout'])
  assert params['place']['effort']==options['place_effort'] and params['place']['macro_performance']==options['macro_performance']
  guard=soft['negative_guards'];assert guard['cases']==11 and H(z.read(guard['record']))==guard['sha256']
  guard_record=read(guard['record']);assert guard_record['inputs']==inputs
  assert guard_record['status']=='NATIVE_GUARDS_PASS' and guard_record['case_count']==11 and len(set(guard_record['rejected']))==11
  assert H(z.read('scripts/test_native_zoom_guards.py'))==guard_record['producer_sha256']
  assert H(z.read('scripts/native_zoom_policy.py'))==guard_record['policy_sha256']
  assert H(z.read('scripts/native_zoom_codegen.py'))==guard_record['codegen_sha256']
  for n,h in inputs.items():assert H(z.read(n))==h,n
  for name,e in soft['native'].items():
   assert H(z.read(e['receipt']))==e['receipt_sha256'];r=read(e['receipt'])
   assert r['test']==name
   assert H(z.read(e['record']))==e['record_sha256'];record=read(e['record'])
   assert record['exit_code']==0 and not record['expected_failure']
   log=str(PurePosixPath(e['record']).with_suffix('.log'));assert H(z.read(log))==e['log_sha256']
   if name=='transitions':assert b'NATIVE_TRANSITIONS_PASS six_frames pixels4792320' in z.read(log)
   if name=='fixed_arithmetic':assert b'NATIVE_FIXED_ARITHMETIC_PASS modulo1024 three_paths addresses32768' in z.read(log)
   if name.startswith('capture_shared_'):
    markers={'capture_shared_masks':b'NATIVE_SHARED_MASKS_PASS','capture_shared_full':b'NATIVE_SHARED_CAPTURE_PASS frames10 pixels9216000','capture_shared_fault':b'NATIVE_SHARED_FAULT_PASS frames6','capture_shared_reducer':b'NATIVE_SHARED_REDUCER_PASS frames200 quads3200'}
    assert markers[name] in z.read(log)
   fixture=str(PurePosixPath(e['receipt']).parent/'tb.sv');assert H(z.read(fixture))==e['fixture_sha256']==r['fixture_sha256']
   for n,h in e['inputs'].items():assert H(z.read(n.replace('\\','/')))==h,n
   for n,h in e['producer_inputs'].items():assert H(z.read(n))==h,n
   assert r['producer_inputs']==e['producer_inputs']
   assert {n.replace('\\','/'):h for n,h in record['inputs'].items()}=={n.replace('\\','/'):h for n,h in e['inputs'].items()}
  for e in soft['legacy_unchanged'].values():
   assert H(z.read(e['record']))==e['record_sha256'];r=read(e['record'])
   assert r['exit_code']==0 and not r['expected_failure']
   assert H(z.read(str(PurePosixPath(e['record']).with_suffix('.log'))))==e['log_sha256']
   for group in ('inputs','fixture_inputs','producer_inputs'):
    for n,h in e[group].items():assert H(z.read(n.replace('\\','/')))==h,n
  assert physical['status']==delivery['status'] and physical['bit_sha256']==delivery['artifacts']['target_color_regions.bit']
  assert physical['current_frozen_git_exact'] and physical['new_clocks_present'] and physical['user_original_protected']
  assert physical['resource_pass'] and physical['timing_pass'] and min(physical['slack_ns'].values())>=0
  limits={'slice':21216,'lut6':21216,'reg':42432,'eram':108,'dsp':40}
  assert all(physical['resources'][k]<=v for k,v in limits.items())
  area=z.read('qualification/route/target_color_regions_phy.area').decode('utf-8')
  assert all(int(re.search(r'^\s*#'+k+r'\s+(\d+)',area,re.M)[1])==v for k,v in physical['resources'].items())
  routing=physical['routing'];assert routing['routing_drc_pass'] and routing['final_over_count']==routing['final_over']==routing['final_worst']==0
  assert H(z.read('qualification/route/td.log'))==routing['log_sha256']
  verify_final_route_log(z.read('qualification/route/td.log').decode('utf-8'))
  timing=z.read('qualification/route/target_color_regions_phy.ts').decode('utf-8')
  for k,v in physical['slack_ns'].items():assert float(re.search(k+r':\s*([-\d.]+)ns',timing)[1])==v
 return {'status':'INDEPENDENT_SAME_SOURCE_PASS','archive_name':delivery['archive_name'],'file_count':len(manifest),
         'native_checks':soft['native_passed'],'legacy_unchanged_checks':soft['legacy_passed'],'bit_sha256':delivery['artifacts']['target_color_regions.bit'],
         'source_zip_sha256':delivery['artifacts']['native_zoom_same_source.zip'],'hardware':'PENDING_JEREMY'}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--folder',required=True);ap.add_argument('--receipt',required=True);a=ap.parse_args()
 result=verify(a.folder);Path(a.receipt).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result)
