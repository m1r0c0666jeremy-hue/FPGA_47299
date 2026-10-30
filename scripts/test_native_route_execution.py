"""Execution-metadata parser checks only; not a physical or delivery pass."""
import copy,datetime,hashlib,json,re
from pathlib import Path
from native_zoom_policy import R,sha
from review_native_zoom_physical import route_execution
from verify_native_zoom_delivery import verify_route_execution

def main():
 folder=R/'build'/('native_route_execution_parser_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));folder.mkdir(exist_ok=False)
 route=R/'build/native_zoom_route_20261030_101718_706304'
 source=(route/'td.log').read_text(encoding='utf-8');tcl=(route/'run.tcl').read_text(encoding='utf-8')
 starts=list(re.finditer(r'^RUN-1002 : start command "route"\s*$',source,re.M));assert len(starts)==2
 retry=source[:starts[-1].end()]+'\n'
 normal=(R/'build/native_fixed_arithmetic_20261030_093754/normal_route_failure.log').read_text(encoding='utf-8')
 # Both are real execution traces; neither is a completed, passing candidate.
 (folder/'normal_failure_snapshot.log').write_text(normal,encoding='utf-8')
 (folder/'retry_start_snapshot.log').write_text(retry,encoding='utf-8')
 base={'effort':'normal','fix_hold':'on','hold_fix_iteration':'5','post_route_opt':'high','timing':'on'}
 normal_s={'route_effort':'normal','retry_routability':True,'route_retry_performed':False,'final_route_effort':'normal'}
 retry_s={**normal_s,'route_retry_performed':True,'final_route_effort':'routability'}
 cases=[]
 def positive(name,log,summary):
  record=route_execution(base,summary,log,tcl);verify_route_execution(log,tcl,base,summary,record)
  cases.append({'name':name,'expected':'ACCEPT_METADATA_ONLY','passed':True});return record
 positive('real_normal_failure_trace',normal,normal_s)
 record=positive('real_routability_start_trace',retry,retry_s)
 def reject(name,log,script,summary):
  for checker in (lambda:route_execution(base,summary,log,script),lambda:verify_route_execution(log,script,base,summary,record)):
   try:checker()
   except AssertionError:pass
   else:raise AssertionError('Parser accepted '+name)
  cases.append({'name':name,'expected':'REJECT','passed':True})
 reject('summary_wrong_final_effort',retry,tcl,{**retry_s,'final_route_effort':'normal'})
 reject('retry_not_authorized',retry,tcl,{**retry_s,'retry_routability':False})
 reject('retry_marker_missing',retry.replace('ROUTE_NORMAL_FAILED_RETRY_ROUTABILITY','REMOVED'),tcl,retry_s)
 index=retry.rfind('RUN-1002 : start command "route"')
 injected='RUN-1002 : start command "set_param route fix_hold off"\n'
 reject('actual_hold_disabled',retry[:index]+injected+retry[index:],tcl+'\nset_param route fix_hold off\n',retry_s)
 reject('setting_absent_from_frozen_tcl',retry,tcl.replace('set_param route effort routability','set_param route effort normal'),retry_s)
 receipt={'status':'EXECUTION_METADATA_PARSER_PASS','case_count':len(cases),'cases':cases,
  'scope':'Two real incomplete/failed traces plus five corruptions; no new hardware/software/delivery qualification',
  'producer_sha256':sha(Path(__file__)),'reviewer_sha256':sha(R/'scripts/review_native_zoom_physical.py'),
  'verifier_sha256':sha(R/'scripts/verify_native_zoom_delivery.py'),
  'normal_snapshot_sha256':sha(folder/'normal_failure_snapshot.log'),'retry_snapshot_sha256':sha(folder/'retry_start_snapshot.log')}
 (folder/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(folder,receipt)

if __name__=='__main__':main()
