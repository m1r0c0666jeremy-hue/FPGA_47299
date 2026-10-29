"""Create a fresh candidate only after current software and final physical review."""
import argparse,json,datetime,subprocess,zipfile,hashlib
from pathlib import Path
from native_zoom_policy import R,sha,canonical_build_inputs,check_protected
from audit_native_zoom import audit
from review_native_zoom_physical import review

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--parent',required=True);ap.add_argument('--route',required=True);a=ap.parse_args()
 soft=audit();assert soft['status']=='PASS',soft['missing_native']
 physical=review(a.parent,a.route);assert physical['status']=='CANDIDATE_SOFTWARE_AND_FINAL_PHYSICAL_PASSED_HARDWARE_PENDING'
 stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');out=R/'build'/('target_native_zoom_'+stamp);out.mkdir(exist_ok=False)
 payload={}
 def add(n):
  n=n.replace('\\','/');p=(R/n).resolve();assert p.is_relative_to(R) and p.is_file(),n
  payload[p.relative_to(R).as_posix()]=p.read_bytes()
 def add_bytes(n,b):payload[n]=b
 # Include editable sources, generators and instructions as tracked at packaging,
 # plus the exact dependency closure of every reused/current validation record.
 for n in subprocess.check_output(['git','ls-files','-z'],cwd=R).decode('utf-8').split('\0'):
  if n and not n.startswith(('build/','reports/','tools/','release/','releases/')) and not n.endswith(('.bit','.zip','.vvp')):add(n)
 for n in soft['compiler_inputs']:add(n)
 add(soft['negative_guards']['record'])
 for e in soft['native'].values():
  for n in (e['receipt'],e['record'],str(Path(e['record']).with_suffix('.log')),str(Path(e['receipt']).parent/'tb.sv')):add(n)
  for group in ('inputs','producer_inputs'):
   for n in e[group]:add(n)
 for e in soft['legacy_unchanged'].values():
  add(e['record']);add(str(Path(e['record']).with_suffix('.log')))
  for group in ('inputs','fixture_inputs','producer_inputs'):
   for n in e[group]:add(n)
 for name,d in [('software.json',soft),('physical.json',physical),('inputs.json',soft['compiler_inputs'])]:
  add_bytes('qualification/'+name,json.dumps(d,ensure_ascii=False,indent=2).encode('utf-8'))
 for label,path in [('place',a.parent),('route',a.route)]:
  folder=R/path
  for p in folder.iterdir():
   if p.is_file() and p.suffix in ('.json','.log','.tcl','.sdc','.adc','.area','.ts','.timing','.txt'):
    add_bytes('qualification/'+label+'/'+p.name,p.read_bytes())
 reference=R/'build/stage1_native_zoom_20261029_152351/sc500cs_official_reference.c'
 add_bytes('vendor_reference/sc500cs_official_fixed.c',reference.read_bytes())
 manifest={n:hashlib.sha256(b).hexdigest() for n,b in sorted(payload.items())}
 with zipfile.ZipFile(out/'native_zoom_same_source.zip','w',zipfile.ZIP_DEFLATED) as z:
  for n,b in sorted(payload.items()):z.writestr(n,b)
  z.writestr('SOURCE_MANIFEST.json',json.dumps(manifest,indent=2))
 bit=R/a.route/'target_color_regions.bit';(out/bit.name).write_bytes(bit.read_bytes())
 delivery={'archive_name':'原生2倍细节与三档倍率候选','status':physical['status'],'branch':'Final_Mode_1028',
  'compiled_source_commit':physical['compiled_source_commit'],'packaging_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),
  'artifacts':{n:sha(out/n) for n in ('target_color_regions.bit','native_zoom_same_source.zip')},
  'software_sha256':hashlib.sha256(payload['qualification/software.json']).hexdigest(),
  'physical_sha256':hashlib.sha256(payload['qualification/physical.json']).hexdigest(),
  'project':'td_project/target_color_regions_native_zoom.al','hardware':'PENDING_JEREMY','not_pushed_or_programmed':True}
 (out/'delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2),encoding='utf-8')
 (out/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in delivery['artifacts'].items()),encoding='utf-8')
 print('NATIVE_CANDIDATE_CREATED',out,delivery)
if __name__=='__main__':main()
