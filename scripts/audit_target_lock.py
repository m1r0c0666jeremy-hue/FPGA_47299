"""Separate target audit; archived legacy audits and input hashes stay intact.
--static allows source/unit inspection while integration is unfinished.
Default/--record-build require actual integrated acceptance and matching bit.
"""
from pathlib import Path
import argparse,ast,hashlib,json,re
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--static',action='store_true');p.add_argument('--record-build',action='store_true');a=p.parse_args()
def read(path):return path.read_text(encoding='utf-8-sig')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
checks=[]
tree=ast.parse(read(r/'scripts/audit_project.py'))
modified=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MODIFIED' for t in n.targets))
newmods=json.loads(read(r/'reports/target_vendor_changes.json'))
assert set(newmods)=={'user_source/hdl_source/isp/isp_top.v','user_source/hdl_source/video_in.v'}
modified.update(newmods)
manifest=json.loads(read(r/'reports/source_manifest.json'))
for item in manifest['files']:
 assert sha(r/'vendor_reference/lab1'/item['path'])==item['sha256']
 if item['path'].startswith('user_source/'):
  assert sha(r/item['path'])==modified.get(item['path'],item['sha256']).lower(),item['path']
for item in json.loads(read(r/'vendor_reference/lab3_osd/manifest.json'))['files']:
 assert sha(r/'vendor_reference/lab3_osd'/item['path'])==item['sha256']
checks.append('Original contest Lab1/Lab3 references unchanged; working vendor modifications explicitly registered')
gen=json.loads(read(r/'reports/target_generation_manifest.json'))
for path,digest in gen['files'].items():assert sha(r/path)==digest,path
checks.append('Calibration config, generated pipeline, OSD template and ROM hashes match')
project=r/'td_project/target_lock.al';al=read(project)
paths=[(project.parent/rel).resolve() for rel in re.findall(r'<File Path="([^"]+)"',al)]
for path in paths:
 assert path.is_relative_to(r) and path.is_file(),path
 assert '/sim/' not in path.as_posix() and '/vendor_reference/' not in path.as_posix(),path
active={x.relative_to(r).parts[1] for x in paths if x.relative_to(r).parts[0]=='rtl'}
assert active=={'00_top_control','01_camera','02_image_preprocess','03_tool_detection','04_tracking','05_roi_processing','09_osd_ui','10_memory_video_out'}
assert '<Device>PH1P35MDG324</Device>' in al and '<Speed>-3</Speed>' in al
assert (r/'td_project/target_lock.adc').read_bytes()==(r/'td_project/scaling_test.adc').read_bytes()
assert (r/'td_project/target_lock.sdc').read_bytes()==(r/'td_project/scaling_test.sdc').read_bytes()
checks.append(f'{len(paths)} project dependencies, 8 active RTL directories; original pins and timing constraint content retained')
assert sha(r/'build/scaling_test/scaling_test.bit')=='a598cff3ea804c0fbc9e54d1693e03cfc32fa4b9aef2d7133f234879dc6edf8c'
assert sha(r/'build/imagepreprocess_10_3/imagepreprocess_10_3.bit')=='eddd9d7d28eb431de92d1d0f061962645b7734b027469290ae06166c9183ddf9'
checks.append('Both archived main bitstreams retain original SHA256')
lognames=['target_unit_simulation.log','target_video_simulation.log','target_osd_simulation.log','target_preprocess_regression.log']
logs=[read(r/'reports'/x) for x in lognames]
assert 'TARGET_UNIT_TESTS_PASSED' in logs[0] and 'PASS detector 1280x720 frames=2' in logs[0]
assert logs[0].count('cases=450')==4 and 'PASS display:' in logs[0]
assert logs[1].count('PASS target video:')==15
assert sum(map(int,re.findall(r'pixels=\s*(\d+)',logs[1])))==15175680
assert logs[2].count('PASS OSD case')==10
assert logs[3].count('run exit 0')==3 and 'pixels=3688960' in logs[3]
assert all('FATAL' not in s and 'Traceback' not in s for s in logs)
checks.append('Independent unit, full-video, OSD pixel and four-mode regression logs passed')
for rel in ['scripts/build_target_lock.tcl','td_project/target_lock.al','td_project/target_lock.sdc','td_project/target_lock.adc',*gen['files'].keys(),'scripts/generate_target.py']:
 paths.append(r/rel)
inputs={p.relative_to(r).as_posix():sha(p) for p in sorted(set(paths))}
if a.static:
 result={'status':'STATIC_PASS_INTEGRATION_PENDING','checks':checks,'inputs':inputs,
  'limitation':'AWB/packing/video_in FIFO start reset loss reproduced. Jeremy assigned further testing and issue handling to teammate; archive current state without repair. No final-bit/hardware acceptance.',
  'test_logs':{x:sha(r/'reports'/x) for x in lognames}}
 save(r/'reports/target_static_audit.json',result);print(json.dumps({'status':result['status'],'checks':checks},ensure_ascii=False,indent=2));raise SystemExit(0)
integration=r/'reports/target_ingress_simulation.log'
assert integration.exists() and 'TARGET_INGRESS_TESTS_PASSED' in read(integration),'Integrated input verification incomplete; do not record a delivery bit'
bit=r/'build/target_lock/target_lock.bit';record=r/'reports/target_build_manifest.json'
if a.record_build:
 assert all(x.stat().st_mtime<=bit.stat().st_mtime for x in paths),'Source changed after bit generation'
 log=read(r/'reports/td_target_lock.log');assert 'TARGET_LOCK_BUILD_COMPLETED' in log and 'BUILD_FAILED:' not in log
 (r/'reports/target_lock_build.log').write_text(log,encoding='utf-8',newline='\n')
 save(record,{'inputs':inputs,'bit_sha256':sha(bit)})
build=json.loads(read(record));assert build['inputs']==inputs and build['bit_sha256']==sha(bit)
ts=read(r/'build/target_lock/target_lock_phy.ts')
for name in ('SWNS','HWNS'):assert float(re.search(name+r': ([-\d.]+)ns',ts)[1])>=0
checks.append('Integrated input acceptance and bit/input hashes match; setup and hold nonnegative')
save(r/'reports/target_audit.json',{'status':'PASS','checks':checks,'bit_sha256':sha(bit),'timing':ts.strip(),'hardware':'NOT TESTED'})
print('\n'.join(checks))
