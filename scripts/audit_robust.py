"""Audit the repaired ingress + relaxed color build without rewriting old evidence."""
from pathlib import Path
import json,hashlib,re,ast,argparse
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--snapshot',action='store_true');p.add_argument('--record-build',action='store_true');a=p.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return p.read_text(encoding='utf-8-sig')
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
project=r/'td_project/target_lock_robust.al'
paths=[(project.parent/q).resolve() for q in re.findall(r'<File Path="([^"]+)"',read(project))]
assert paths and all(q.is_file() and q.is_relative_to(r) for q in paths)
gen=json.loads(read(r/'reports/target_generation_manifest.json'))
for rel,digest in gen['files'].items():assert sha(r/rel)==digest,rel
for manifest,base in [('reports/source_manifest.json','vendor_reference/lab1'),('vendor_reference/lab3_osd/manifest.json','vendor_reference/lab3_osd')]:
 for item in json.loads(read(r/manifest))['files']:assert sha(r/base/item['path'])==item['sha256'],item['path']
tree=ast.parse(read(r/'scripts/audit_project.py'))
modified=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MODIFIED' for t in n.targets))
for f in ['target_vendor_changes.json','robust_vendor_changes.json']:modified.update(json.loads(read(r/'reports'/f)))
for item in json.loads(read(r/'reports/source_manifest.json'))['files']:
 if item['path'].startswith('user_source/'):assert sha(r/item['path'])==modified.get(item['path'],item['sha256']).lower(),item['path']
for ext in ('adc','sdc'):assert (r/f'td_project/target_lock.{ext}').read_bytes()==(r/f'td_project/scaling_test.{ext}').read_bytes()
for rel in ['td_project/target_lock_robust.al','td_project/target_lock.adc','td_project/target_lock.sdc','scripts/build_target_lock_robust.tcl','scripts/generate_target.py',*gen['files']]:paths.append(r/rel)
inputs={p.relative_to(r).as_posix():sha(p) for p in sorted(set(paths))}
old=[f'build/{s}/{s}.bit' for s in ['target_lock_candidates','target_lock_dualcolor','target_lock','scaling_test','imagepreprocess_10_3']]
start=r/'reports/robust_build_inputs.json'
if a.snapshot:save(start,dict(inputs=inputs,old_bits={s:sha(r/s) for s in old}));print('ROBUST_BUILD_INPUTS_SNAPSHOTTED');raise SystemExit
before=json.loads(read(start));assert before['inputs']==inputs,'Source changed since build snapshot'
assert all(sha(r/s)==h for s,h in before['old_bits'].items()),'Old bit changed'
logs=['robust_ingress.log','robust_unit_simulation.log','robust_detection_simulation.log','robust_colors.log','robust_video_simulation.log','robust_osd_simulation.log','robust_preprocess_regression.log']
logs.append('robust_geometry.log')
texts=[read(r/'reports'/s) for s in logs]
assert texts[0].count('PASS AWB 960 packed = 960 DDR')==2 and texts[0].count('PASS ingress CP=')==6
assert 'VENDOR_FIFO_RTL:' in texts[0]
assert 'CANDIDATE_UNIT_TESTS_PASSED' in texts[1] and texts[1].count('cases=450')==4
assert 'PASS detector 1280x720 frames=2' in texts[1]
assert 'frames=101' in texts[2] and 'stale_rejected=11' in texts[2]
assert 'ROBUST_COLORS_PASSED' in texts[3]
assert texts[4].count('PASS target video:')==15 and sum(map(int,re.findall(r'pixels=\s*(\d+)',texts[4])))==15175680
assert texts[5].count('PASS OSD case')==72
assert texts[6].count('run exit 0')==3
assert 'PASS robust geometry: 24 frames' in texts[7]
assert all('FATAL' not in t and 'Traceback' not in t for t in texts)
build=r/'build/target_lock_robust';bit=build/'target_lock_robust.bit';timing=read(build/'target_lock_robust_phy.ts')
for tag in ('SWNS','HWNS'):assert float(re.search(tag+r': ([-\d.]+)ns',timing)[1])>=0,timing
tool_log=read(r/'reports/td_target_lock_robust.log')
assert 'TARGET_LOCK_ROBUST_BUILD_COMPLETED' in tool_log and 'BUILD_FAILED:' not in tool_log
assert bit.stat().st_mtime>=start.stat().st_mtime
validation=sorted(set([*r.glob('scripts/test_robust_*.py'),*r.glob('sim/tb_robust_*.sv'),*r.glob('sim/tb_candidate_*.sv'),r/'sim/fifo_model.sv',r/'scripts/robust_reference.py',r/'scripts/candidate_reference.py']))
obj=dict(status='SOFTWARE_AND_BUILD_PASS_HARDWARE_PENDING',inputs=inputs,old_bits=before['old_bits'],bit_sha256=sha(bit),timing=timing.strip(),validation_inputs={p.relative_to(r).as_posix():sha(p) for p in validation},test_logs={s:sha(r/'reports'/s) for s in logs},hardware='NOT TESTED',limitation='Frame-head 960/720 defect fixed and behaviorally verified. Physical FIFO, camera cable, HDMI and relaxed-color performance require board testing. Global color statistics can include same-color background.')
record=r/'reports/robust_build_manifest.json'
if a.record_build:(r/'reports/robust_build.log').write_text(tool_log,encoding='utf-8',newline='\n');save(record,obj)
else:assert json.loads(read(record))==obj
print(json.dumps({k:obj[k] for k in ['status','bit_sha256','timing','limitation']},ensure_ascii=False,indent=2))
