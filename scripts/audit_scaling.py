"""ScalingTest dependency/source/build audit. No hardware claims or legacy audit overrides."""
from pathlib import Path
import argparse, ast, hashlib, json, re, shutil

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--record-build',action='store_true');args=p.parse_args()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return path.read_text(encoding='utf-8-sig')
checks=[]
# Read the old audit's explicit vendor exceptions without executing its old topology tests.
tree=ast.parse(read(root/'scripts/audit_project.py'))
modified=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MODIFIED' for t in n.targets))
manifest=json.loads(read(root/'reports/source_manifest.json'))
for item in manifest['files']:
 assert sha(root/'vendor_reference/lab1'/item['path'])==item['sha256']
 if item['path'].startswith('user_source/'):
  assert sha(root/item['path'])==modified.get(item['path'],item['sha256']).lower(),item['path']
checks.append(f'{len(manifest["files"])} Lab1 baseline files and all registered working vendor hashes preserved')
lab=json.loads(read(root/'vendor_reference/lab3_osd/manifest.json'))
for item in lab['files']:assert sha(root/'vendor_reference/lab3_osd'/item['path'])==item['sha256']
checks.append('4 contest Lab3 reference files unchanged; original archive paths/hashes recorded')
rom=json.loads(read(root/'assets/osd/anlogic/scaling_rom_manifest.json'))
for name,digest in rom['files'].items():
 path=root/('rtl/09_osd_ui' if name.endswith('.v') else 'assets/osd/anlogic')/name
 assert sha(path)==digest,name
checks.append('Generated OSD/logo/font hashes match generation manifest')
project=root/'td_project/scaling_test.al';al=read(project)
paths=[(project.parent/rel).resolve() for rel in re.findall(r'<File Path="([^"]+)"',al)]
for path in paths:
 assert path.is_relative_to(root) and path.is_file(),path
 assert '/sim/' not in path.as_posix() and '/vendor_reference/' not in path.as_posix(),path
assert '<Device>PH1P35MDG324</Device>' in al and '<Speed>-3</Speed>' in al
active={p.relative_to(root).parts[1] for p in paths if p.relative_to(root).parts[0]=='rtl'}
assert active=={'00_top_control','01_camera','02_image_preprocess','05_roi_processing','09_osd_ui','10_memory_video_out'}
pins=read(root/'td_project/scaling_test.adc')
for port,pin in [('I_switch[1]','A4'),('I_switch[0]','B4'),('I_ui_switch[1]','E11'),('I_ui_switch[0]','D11'),('I_button[0]','A9'),('I_button[1]','B9'),('I_button[2]','C7'),('I_rst_n','D5')]:
 assert re.search(re.escape(port)+r'.*LOCATION = '+pin+r'\b',pins),(port,pin)
checks.append(f'{len(paths)} dependencies resolve; 6 active RTL directories; board pins match agreed mapping')
bit=root/'build/scaling_test/scaling_test.bit'
for extra in ['scripts/build_scaling_test.tcl','td_project/scaling_test.al','td_project/scaling_test.sdc','td_project/scaling_test.adc']:
 paths.append(root/extra)
inputs={p.relative_to(root).as_posix():sha(p) for p in sorted(set(paths))}
record=root/'reports/scaling_build_manifest.json'
if args.record_build:
 assert all(p.stat().st_mtime<=bit.stat().st_mtime for p in paths),'Source changed after bit generation'
 log=read(root/'reports/td_scaling_test.log')
 assert 'SCALING_TEST_BUILD_COMPLETED' in log and 'BUILD_FAILED:' not in log
 shutil.copyfile(root/'reports/td_scaling_test.log',root/'reports/scaling_test_build.log')
 record.write_text(json.dumps({'inputs':inputs,'bit_sha256':sha(bit)},indent=2)+'\n',encoding='utf-8')
build=json.loads(read(record))
assert build['inputs']==inputs,'Build inputs changed; rebuild and re-record the manifest'
assert sha(bit)==build['bit_sha256']
assert sha(root/'build/imagepreprocess_10_3/imagepreprocess_10_3.bit')=='eddd9d7d28eb431de92d1d0f061962645b7734b027469290ae06166c9183ddf9'
ts=read(root/'build/scaling_test/scaling_test_phy.ts')
for name in ('SWNS','HWNS'):
 assert float(re.search(name+r': ([-\d.]+)ns',ts)[1])>=0,ts
checks.append('Current build inputs/bit match archived hashes; setup and hold slack non-negative; previous bit retained')
sim=read(root/'reports/scaling_simulation.log')
osd=read(root/'reports/scaling_osd_simulation.log')
regression=read(root/'reports/imagepreprocess_10_3_simulation.log')
assert sim.count('PASS scaling video:')==15 and sim.count('PASS controls:')==1
assert sum(map(int,re.findall(r'pixels=\s*(\d+)',sim)))==15175680
assert osd.count('PASS OSD case ')==6
assert regression.count('run exit 0')==3 and 'pixels=3688960' in regression
assert not any('FATAL' in log or 'Traceback' in log for log in (sim,osd,regression))
checks.append('Archived logs: 15 video cases / 15175680 pixels, controls, 6 OSD cases and 3 algorithm regression cases passed')
validation_paths=[root/p for p in ['scripts/test_scaling.py','scripts/test_scaling_osd.py','scripts/test_imagepreprocess_10_3.py','sim/tb_scaling_controls.sv','sim/tb_scaling_video.sv','sim/tb_scaling_osd.sv','reports/scaling_simulation.log','reports/scaling_osd_simulation.log','reports/imagepreprocess_10_3_simulation.log']]
result={'status':'PASS','checks':checks,'bit_sha256':sha(bit),'timing':ts.strip(),
 'validation_files':{p.relative_to(root).as_posix():sha(p) for p in validation_paths},
 'scope':'Static dependency/hash/build audit, not equivalence, CDC formal proof, DDR PHY simulation or hardware acceptance.'}
(root/'reports/scaling_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
