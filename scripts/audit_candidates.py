"""Verify this build's actual inputs; never equate build success with ingress/hardware acceptance."""
from pathlib import Path
import argparse,hashlib,json,re,ast
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--record-build',action='store_true');p.add_argument('--snapshot',action='store_true');args=p.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return p.read_text(encoding='utf-8-sig')
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
project=r/'td_project/target_lock_candidates.al'
paths=[(project.parent/q).resolve() for q in re.findall(r'<File Path="([^"]+)"',read(project))]
assert paths and all(q.is_file() and q.is_relative_to(r) for q in paths)
cfg=json.loads(read(r/'rtl/03_tool_detection/target_config.json'))
assert f"LONG_PRESS_MS({cfg['long_press_ms']})" in read(r/'rtl/00_top_control/criticalwork_top.v')
gen=json.loads(read(r/'reports/target_generation_manifest.json'))
for path,digest in gen['files'].items():assert sha(r/path)==digest,path
for manifest,base in [('reports/source_manifest.json','vendor_reference/lab1'),('vendor_reference/lab3_osd/manifest.json','vendor_reference/lab3_osd')]:
 for item in json.loads(read(r/manifest))['files']:assert sha(r/base/item['path'])==item['sha256'],item['path']
tree=ast.parse(read(r/'scripts/audit_project.py'))
modified=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MODIFIED' for t in n.targets))
modified.update(json.loads(read(r/'reports/target_vendor_changes.json')))
for item in json.loads(read(r/'reports/source_manifest.json'))['files']:
 if item['path'].startswith('user_source/'):
  assert sha(r/item['path'])==modified.get(item['path'],item['sha256']).lower(),item['path']
assert (r/'td_project/target_lock.adc').read_bytes()==(r/'td_project/scaling_test.adc').read_bytes()
assert (r/'td_project/target_lock.sdc').read_bytes()==(r/'td_project/scaling_test.sdc').read_bytes()
for rel in ['td_project/target_lock_candidates.al','td_project/target_lock.adc','td_project/target_lock.sdc','scripts/build_target_lock_candidates.tcl','scripts/generate_target.py',*gen['files']]:paths.append(r/rel)
inputs={p.relative_to(r).as_posix():sha(p) for p in sorted(set(paths))}
start=r/'reports/candidate_build_inputs.json'
old_bits=['build/target_lock_dualcolor/target_lock_dualcolor.bit','build/target_lock/target_lock.bit','build/scaling_test/scaling_test.bit','build/imagepreprocess_10_3/imagepreprocess_10_3.bit']
if args.snapshot:
 save(start,{'inputs':inputs,'old_bits':{s:sha(r/s) for s in old_bits}});print('BUILD_INPUTS_SNAPSHOTTED');raise SystemExit
before=json.loads(read(start));assert before['inputs']==inputs,'Inputs changed since build start'
assert all(sha(r/s)==h for s,h in before['old_bits'].items()),'Archived bit changed'
logs=['candidate_unit_simulation.log','candidate_detection_simulation.log','candidate_video_simulation.log','candidate_osd_simulation.log','candidate_preprocess_regression.log','candidate_full_simulation.log']
texts=[read(r/'reports'/s) for s in logs]
assert 'CANDIDATE_UNIT_TESTS_PASSED' in texts[0] and 'PASS detector 1280x720 frames=2' in texts[0]
assert texts[0].count('cases=450')==4 and '999/1000/1001ms' in texts[0]
assert 'PASS dualcolor pipeline: frames=71' in texts[1]
assert 'PASS diagnostics decimal: 202 cases' in texts[0]
assert texts[2].count('PASS target video:')==15
assert sum(map(int,re.findall(r'pixels=\s*(\d+)',texts[2])))==15175680
assert texts[3].count('PASS OSD case')==72 and 'CANDIDATE_OSD_TESTS_PASSED' in texts[3]
assert texts[4].count('run exit 0')==3
assert 'PASS detector 1280x720 frames=5' in texts[5]
assert all('FATAL' not in t and 'Traceback' not in t for t in texts)
build=r/'build/target_lock_candidates';bit=build/'target_lock_candidates.bit'
timing=read(build/'target_lock_candidates_phy.ts')
for tag in ('SWNS','HWNS'):assert float(re.search(tag+r': ([-\d.]+)ns',timing)[1])>=0,timing
tool_log=read(r/'reports/td_target_lock_candidates.log')
assert 'TARGET_LOCK_CANDIDATES_BUILD_COMPLETED' in tool_log and 'BUILD_FAILED:' not in tool_log
assert bit.is_file() and bit.stat().st_mtime>=start.stat().st_mtime
record=r/'reports/candidate_build_manifest.json'
validation_paths=sorted([*r.glob('scripts/test_candidate_*.py'),*r.glob('sim/tb_candidate_*.sv'),r/'scripts/candidate_reference.py'])
obj={'status':'SOFTWARE_AND_BUILD_PASS_INTEGRATION_PENDING','inputs':inputs,'old_bits':before['old_bits'],'bit_sha256':sha(bit),'timing':timing.strip(),
 'validation_inputs':{p.relative_to(r).as_posix():sha(p) for p in validation_paths},
 'test_logs':{s:sha(r/'reports'/s) for s in logs},'hardware':'NOT TESTED',
 'limitation':'Existing AWB/packer/video_in frame-start loss remains unresolved. This source-matched bit is a debug build, not integrated or hardware acceptance.'}
if args.record_build:
 (r/'reports/candidate_build.log').write_text(tool_log,encoding='utf-8',newline='\n');save(record,obj)
else:assert json.loads(read(record))==obj,'Build manifest differs'
print(json.dumps({k:obj[k] for k in ['status','bit_sha256','timing','limitation']},ensure_ascii=False,indent=2))
