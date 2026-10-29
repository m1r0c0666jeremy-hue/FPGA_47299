"""Independent, read-only verification of a native source ZIP and physical receipts."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,zipfile,re
H=lambda b:hashlib.sha256(b).hexdigest()

def verify(folder):
 folder=Path(folder);delivery=json.loads((folder/'delivery.json').read_text(encoding='utf-8'))
 assert delivery['status']=='CANDIDATE_SOFTWARE_AND_FINAL_PHYSICAL_PASSED_HARDWARE_PENDING'
 assert delivery['archive_name']=='原生2倍细节与三档倍率候选'
 for n,h in delivery['artifacts'].items():assert H((folder/n).read_bytes())==h,n
 with zipfile.ZipFile(folder/'native_zoom_same_source.zip') as z:
  names=z.namelist();assert len(names)==len(set(names))
  assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts for n in names)
  manifest=json.loads(z.read('SOURCE_MANIFEST.json'))
  assert set(names)==set(manifest)|{'SOURCE_MANIFEST.json'}
  for n,h in manifest.items():assert H(z.read(n))==h,n
  def read(n):return json.loads(z.read(n))
  soft=read('qualification/software.json');physical=read('qualification/physical.json');inputs=read('qualification/inputs.json')
  assert H(z.read('qualification/software.json'))==delivery['software_sha256']
  assert H(z.read('qualification/physical.json'))==delivery['physical_sha256']
  assert soft['status']=='PASS' and soft['native_required']==soft['native_passed']==44
  assert soft['legacy_required']==soft['legacy_passed']==155 and not soft['missing_native'] and not soft['missing_legacy']
  assert inputs==soft['compiler_inputs']
  assert inputs==read('qualification/place/inputs.json')==read('qualification/route/inputs.json')==read('qualification/route/inputs_after.json')
  assert len(inputs)==physical['compiler_input_count']==327
  assert physical['compiled_source_commit']==delivery['compiled_source_commit']
  for stage in ('place','route'):
   summary=read('qualification/'+stage+'/summary.json')
   assert summary['exit_code']==0 and summary['inputs_unchanged'] and summary['working_tree_matches']
  guard=soft['negative_guards'];assert guard['cases']==11 and H(z.read(guard['record']))==guard['sha256']
  assert read(guard['record'])['inputs']==inputs
  for n,h in inputs.items():assert H(z.read(n))==h,n
  for e in soft['native'].values():
   assert H(z.read(e['receipt']))==e['receipt_sha256'];r=read(e['receipt'])
   assert H(z.read(e['record']))==e['record_sha256'];record=read(e['record'])
   assert record['exit_code']==0 and not record['expected_failure']
   log=str(PurePosixPath(e['record']).with_suffix('.log'));assert H(z.read(log))==e['log_sha256']
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
  routing=physical['routing'];assert routing['routing_drc_pass'] and routing['final_over_count']==routing['final_over']==routing['final_worst']==0
  assert H(z.read('qualification/route/td.log'))==routing['log_sha256']
  log=z.read('qualification/route/td.log').decode('utf-8');start=log.rfind('RUN-1002 : start command "route"');assert start>=0
  log=log[start:];m=re.search(r'Stage (\d+) \| Routing DRC\s*\n',log);assert m
  end=re.search(r'End Stage '+m[1]+r' \| Routing DRC;',log);assert end and end.start()>m.end()
  values=re.findall(r'over cnt = (\d+)\([^)]*\), over = (\d+), worst = (\d+)',log[:m.start()]);assert tuple(map(int,values[-1]))==(0,0,0)
  body=log[m.end():end.start()];assert all(s in body for s in ('No multi-drive.','No abnormal timing path.','Check Pass.'))
  assert 'REFINED_CHECKPOINT_FULL_COMPLETED' in log and 'BUILD_FAILED:' not in log
  timing=z.read('qualification/route/target_color_regions_phy.ts').decode('utf-8')
  for k,v in physical['slack_ns'].items():assert float(re.search(k+r':\s*([-\d.]+)ns',timing)[1])==v
 return {'status':'INDEPENDENT_SAME_SOURCE_PASS','archive_name':delivery['archive_name'],'file_count':len(manifest),
         'native_checks':soft['native_passed'],'legacy_unchanged_checks':soft['legacy_passed'],'bit_sha256':delivery['artifacts']['target_color_regions.bit'],
         'source_zip_sha256':delivery['artifacts']['native_zoom_same_source.zip'],'hardware':'PENDING_JEREMY'}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--folder',required=True);ap.add_argument('--receipt',required=True);a=ap.parse_args()
 result=verify(a.folder);Path(a.receipt).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result)
