"""Audit ImproveFourfoldScale without changing the baseline audit or evidence."""
from pathlib import Path
import argparse,ast,hashlib,json,re,subprocess,shutil
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--record-build',action='store_true');a=p.parse_args()
def read(p):return p.read_text(encoding='utf-8-sig')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def base(p):return subprocess.run(['git','-c',f'safe.directory={r.as_posix()}','show',f'4c26207:{p}'],cwd=r,capture_output=True,check=True).stdout
checks=[]
tree=ast.parse(read(r/'scripts/audit_project.py'))
mods=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MODIFIED' for t in n.targets))
for item in json.loads(read(r/'reports/source_manifest.json'))['files']:
 assert sha(r/'vendor_reference/lab1'/item['path'])==item['sha256']
 if item['path'].startswith('user_source/'):assert sha(r/item['path'])==mods.get(item['path'],item['sha256']).lower()
for item in json.loads(read(r/'vendor_reference/lab3_osd/manifest.json'))['files']:
 assert sha(r/'vendor_reference/lab3_osd'/item['path'])==item['sha256']
for name,h in json.loads(read(r/'assets/osd/anlogic/scaling_rom_manifest.json'))['files'].items():
 assert sha(r/('rtl/09_osd_ui' if name.endswith('.v') else 'assets/osd/anlogic')/name)==h
checks.append('193 Lab1 baseline files, registered vendor edits, 4 Lab3 references and OSD assets preserved')
for path in ['rtl/02_image_preprocess/image_preprocess.v','rtl/09_osd_ui/scaling_osd.v','rtl/00_top_control/scaling_controls.v','scripts/audit_scaling.py','reports/scaling_build_manifest.json','reports/scaling_simulation.log','reports/scaling_osd_simulation.log','reports/imagepreprocess_10_3_simulation.log','build/scaling_test/scaling_test.bit']:
 assert (r/path).read_bytes()==base(path),path
assert read(r/'td_project/improve_fourfold_scale.sdc')==read(r/'td_project/scaling_test.sdc'),'Timing constraints differ'
assert read(r/'td_project/improve_fourfold_scale.adc')==read(r/'td_project/scaling_test.adc'),'Pins differ'
checks.append('Main algorithms/controls/OSD/old bit/evidence retained byte-for-byte; no constraint exceptions added')
project=r/'td_project/improve_fourfold_scale.al';text=read(project)
paths=[(project.parent/p).resolve() for p in re.findall(r'<File Path="([^"]+)"',text)]
for f in paths:assert f.is_file() and f.is_relative_to(r) and '/sim/' not in f.as_posix() and '/vendor_reference/' not in f.as_posix(),f
assert '<Device>PH1P35MDG324</Device>' in text and '<Speed>-3</Speed>' in text
assert r/'rtl/05_roi_processing/bilinear_rgb.v' in paths
checks.append(f'{len(paths)} TD dependencies resolve with PH1P35MDG324 -3')
for f in ['scripts/build_improve_fourfold_scale.tcl','td_project/improve_fourfold_scale.al','td_project/improve_fourfold_scale.sdc','td_project/improve_fourfold_scale.adc']:paths.append(r/f)
inputs={f.relative_to(r).as_posix():sha(f) for f in sorted(set(paths))}
bit=r/'build/improve_fourfold_scale/improve_fourfold_scale.bit';manifest=r/'reports/fourfold_build_manifest.json'
if a.record_build:
 assert all(f.stat().st_mtime<=bit.stat().st_mtime for f in paths),'Inputs newer than bit'
 log=read(r/'reports/td_improve_fourfold_scale.log')
 assert 'IMPROVE_FOURFOLD_SCALE_BUILD_COMPLETED' in log and 'BUILD_FAILED:' not in log
 shutil.copyfile(r/'reports/td_improve_fourfold_scale.log',r/'reports/fourfold_build.log')
 manifest.write_text(json.dumps({'inputs':inputs,'bit_sha256':sha(bit)},indent=2)+'\n')
b=json.loads(read(manifest));assert b['inputs']==inputs and b['bit_sha256']==sha(bit)
ts=read(r/'build/improve_fourfold_scale/improve_fourfold_scale_phy.ts')
for n in ['SWNS','HWNS']:assert float(re.search(n+r': ([-\d.]+)ns',ts)[1])>=0,ts
checks.append('Bit matches complete build manifest; nonnegative setup/hold slack')
sim=read(r/'reports/fourfold_simulation.log');cases=json.loads(read(r/'reports/fourfold_test_cases.json'))
assert not cases['quick'] and len(cases['cases'])==30
assert sim.count('PASS fourfold video:')==30 and 'PASS bilinear arithmetic:' in sim and 'PASS controls:' in sim
assert sum(map(int,re.findall(r'pixels=\s*(\d+)',sim)))==36*1280*624
osd=read(r/'reports/fourfold_osd_simulation.log');pre=read(r/'reports/fourfold_preprocess_simulation.log')
assert osd.count('PASS OSD case ')==6 and pre.count('run exit 0')==3
assert not any('FATAL' in t or 'Traceback' in t for t in [sim,osd,pre])
reset=read(r/'reports/fourfold_reset_simulation.log');assert 'PASS fourfold video:' in reset and 'FATAL' not in reset
fault=read(r/'reports/fourfold_fault_simulation.log')
assert fault.count('PASS fourfold video:')==2 and 'FATAL' not in fault
assert 'black_count<=2' not in read(r/'sim/tb_fourfold_video.sv')
checks.append('Strict fault-boundary rerun: both latency faults, 5 frames, no first-pixel waiver')
checks.append('30 full-timing cases/36 frames, independent arithmetic, controls, 6 OSD cases and 3 preprocessing regressions passed')
validation=[*r.glob('scripts/*fourfold*.py'),r/'sim/tb_fourfold_video.sv',r/'sim/tb_fourfold_reset.sv',r/'sim/tb_bilinear_rgb.sv',r/'sim/tb_scaling_controls.sv',*r.glob('reports/fourfold_*simulation.log'),r/'reports/fourfold_test_cases.json']
result={'status':'PASS','baseline':'4c2620782e7f29367620975b51e850a34f846ef1','checks':checks,'bit_sha256':sha(bit),'timing':ts.strip(),'validation_files':{f.relative_to(r).as_posix():sha(f) for f in validation},'scope':'Software and static/build evidence only; not board acceptance, DDR PHY simulation or full CDC proof.'}
(r/'reports/fourfold_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
