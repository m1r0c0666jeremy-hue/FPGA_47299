"""Corrupt private copies of an actual verified delivery; never mutate its files."""
import argparse,copy,datetime,hashlib,json,re,zipfile
from pathlib import Path
from verify_native_zoom_delivery import verify
R=Path(__file__).resolve().parents[1]
H=lambda b:hashlib.sha256(b).hexdigest()
J=lambda d:json.dumps(d,ensure_ascii=False,indent=2).encode('utf-8')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--folder',required=True);a=ap.parse_args()
 source=Path(a.folder).resolve();verify(source)
 before={p.name:H(p.read_bytes()) for p in source.iterdir() if p.is_file()}
 delivery=json.loads((source/'delivery.json').read_text(encoding='utf-8'))
 with zipfile.ZipFile(source/'native_zoom_same_source.zip') as z:base={n:z.read(n) for n in z.namelist() if n!='SOURCE_MANIFEST.json'}
 bit=(source/'target_color_regions.bit').read_bytes()
 root=R/'build'/('native_zoom_delivery_guards_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));root.mkdir(exist_ok=False)
 def read(payload,name):return json.loads(payload[name])
 def soft(payload,change):
  d=read(payload,'qualification/software.json');change(d,payload);payload['qualification/software.json']=J(d)
 def phys(payload,change):
  d=read(payload,'qualification/physical.json');change(d,payload);payload['qualification/physical.json']=J(d)
 cases={}
 cases['missing_native']=lambda p:soft(p,lambda d,p:d['native'].pop(next(iter(d['native']))))
 cases['missing_legacy']=lambda p:soft(p,lambda d,p:d['legacy_unchanged'].pop(next(iter(d['legacy_unchanged']))))
 cases['native_count_55']=lambda p:soft(p,lambda d,p:d.update(native_required=55,native_passed=55))
 cases['rtl_payload_changed']=lambda p:p.update({'rtl/color_regions/native_read_adapter.v':p['rtl/color_regions/native_read_adapter.v']+b'\n// wrong source\n'})
 def dependency(p,group):
  d=read(p,'qualification/software.json');e=next(iter(d['native'].values()))
  name=next(iter(e[group]));p[name.replace('\\','/')]+=b'\n// changed dependency\n'
 cases['producer_changed']=lambda p:dependency(p,'producer_inputs')
 def fixture(p):
  d=read(p,'qualification/software.json');e=next(iter(d['native'].values()));name=str(Path(e['receipt']).parent/'tb.sv').replace('\\','/');p[name]+=b'\n// changed fixture\n'
 cases['fixture_changed']=fixture
 def failed_sim(d,p):
  e=next(iter(d['native'].values()));record=read(p,e['record']);record['exit_code']=1;p[e['record']]=J(record);e['record_sha256']=H(p[e['record']])
 cases['failed_sim_rehashed']=lambda p:soft(p,failed_sim)
 def bad_guard(d,p):
  g=d['negative_guards'];record=read(p,g['record']);record['status']='FAILED';p[g['record']]=J(record);g['sha256']=H(p[g['record']])
 cases['failed_guard_rehashed']=lambda p:soft(p,bad_guard)
 cases['negative_setup']=lambda p:phys(p,lambda d,p:d['slack_ns'].update(SWNS=-0.001))
 cases['negative_hold']=lambda p:phys(p,lambda d,p:d['slack_ns'].update(HWNS=-0.001))
 cases['over_capacity']=lambda p:phys(p,lambda d,p:d['resources'].update(slice=21217))
 def wrong_area(p):
  name='qualification/route/target_color_regions_phy.area';p[name]=re.sub(rb'(?m)^(\s*#slice\s+)\d+',rb'\g<1>1',p[name],count=1)
 cases['actual_area_mismatch']=wrong_area
 def abnormal(d,p):
  name='qualification/route/td.log';assert b'No abnormal timing path.' in p[name]
  p[name]=p[name].replace(b'No abnormal timing path.',b'Abnormal timing path.')
  d['routing']['log_sha256']=H(p[name])
 cases['actual_abnormal_path']=lambda p:phys(p,abnormal)
 cases['archive_traversal']=lambda p:p.update({'../unexpected.txt':b'unsafe member'})
 rejected=[]
 for label,mutate in cases.items():
  out=root/label;out.mkdir();payload=base.copy();mutate(payload);d=copy.deepcopy(delivery)
  manifest={n:H(b) for n,b in sorted(payload.items())}
  with zipfile.ZipFile(out/'native_zoom_same_source.zip','w',zipfile.ZIP_DEFLATED) as z:
   for n,b in sorted(payload.items()):z.writestr(n,b)
   z.writestr('SOURCE_MANIFEST.json',J(manifest))
  (out/'target_color_regions.bit').write_bytes(bit)
  d['artifacts']['native_zoom_same_source.zip']=H((out/'native_zoom_same_source.zip').read_bytes())
  d['software_sha256']=H(payload['qualification/software.json']);d['physical_sha256']=H(payload['qualification/physical.json'])
  (out/'delivery.json').write_bytes(J(d))
  try:verify(out)
  except AssertionError:rejected.append(label)
  else:raise AssertionError('Delivery guard accepted '+label)
  print('NATIVE_DELIVERY_GUARD_REJECTED',label,flush=True)
 assert before=={p.name:H(p.read_bytes()) for p in source.iterdir() if p.is_file()}
 receipt={'status':'NATIVE_DELIVERY_GUARDS_PASS','candidate':str(source),'candidate_hashes':before,'rejected':rejected,'case_count':len(rejected),
  'producer_sha256':H(Path(__file__).read_bytes()),'verifier_sha256':H((R/'scripts/verify_native_zoom_delivery.py').read_bytes()),'original_unchanged':True}
 (root/'receipt.json').write_bytes(J(receipt));print(root,receipt)
if __name__=='__main__':main()
