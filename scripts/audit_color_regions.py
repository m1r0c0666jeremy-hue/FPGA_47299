"""Read-only build/source/protected-bit audit. No generation or hardware acceptance."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys,zipfile
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return p.read_text(encoding='utf-8-sig',errors='replace')
def audit(attempt,check_build=False):
 attempt=Path(attempt).resolve();assert attempt.is_relative_to(R/'build') and attempt.is_dir()
 baseline=json.loads(read(R/'reports/color_regions_baseline.json'))
 for name,h in baseline['protected_bits'].items():assert sha(R/name)==h,'Historical bit changed: '+name
 assert sha(R/'user_source/hdl_source/video_in.v')==baseline['ingress_sha256']
 for name,h in baseline['source_inputs'].items():
  if name.startswith(('rtl/','user_source/')) and Path(name).suffix.lower() in ('.v','.sv','.tcl','.adc','.sdc'):
   assert sha(R/name)==h,'Existing RTL/IP changed: '+name
 with zipfile.ZipFile(R/baseline['source_archive']) as z:
  cfg=json.loads(z.read('rtl/03_tool_detection/target_config.json'))
 current=json.loads(read(R/'rtl/03_tool_detection/target_config.json'))
 assert all(current[k]==v for k,v in cfg.items()),'Inactive baseline configuration changed'
 head=subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip()
 branch=subprocess.check_output(['git','-C',str(R),'branch','--show-current'],text=True).strip()
 assert head==baseline['head'] and branch=='LockingnTracking'
 for args in [('--check',),('--color-regions','--check')]:
  subprocess.run([sys.executable,str(R/'scripts/generate_target.py'),*args],cwd=R,check=True)
 inputs=json.loads(read(attempt/'inputs.json'))
 for name,h in inputs.items():assert sha(R/name)==h,'Frozen input differs: '+name
 with zipfile.ZipFile(attempt/'source_snapshot.zip') as z:
  assert set(z.namelist())==set(inputs)
  for name,h in inputs.items():assert hashlib.sha256(z.read(name)).hexdigest()==h
 project=read(R/'td_project/target_color_regions.al')
 paths=re.findall(r'<File Path="([^"]+)"',project)
 for p in paths:
  assert 'teacher_color_diag' not in p and Path(p).name not in (
   'target_detector.v','target_tracker.v','target_osd.v','target_diagnostics.v',
   'target_capture_pipeline.v','target_display.v','target_frame_store.v','image_preprocess.v')
 expected={'classifier','runs4','run_labeler','divide','finalize','grid','confirm','capture',
           'frame_store','display','preprocess','osd','glyph_rom','line_reader','memory_video_out','top'}
 assert {Path(p).stem.removeprefix('regions_') for p in paths if '/color_regions/' in p}==expected
 obj=dict(head=head,branch=branch,inputs=inputs,protected_bits=baseline['protected_bits'],
          attempt=attempt.relative_to(R).as_posix(),hardware='NOT TESTED')
 if check_build:
  log=read(R/'reports'/(attempt.name+'.log'))
  assert 'TARGET_COLOR_REGIONS_BUILD_COMPLETED' in log and 'BUILD_FAILED:' not in log
  bit=attempt/'target_color_regions.bit';assert bit.is_file() and bit.stat().st_mtime>=(attempt/'inputs.json').stat().st_mtime
  ts=read(attempt/'target_color_regions_phy.ts');area=read(attempt/'target_color_regions_phy.area')
  timing={tag:float(re.search(tag+r':\s*([-\d.]+)ns',ts)[1]) for tag in ('SWNS','HWNS')}
  assert min(timing.values())>=0,ts
  resources={key:int(re.search(r'^#'+tag+r'\s+(\d+)',area,re.M)[1]) for key,tag in (
   ('Slice','slice'),('LUT6','lut6'),('Register','reg'),('ERAM20K','eram'),('DSP','dsp'))}
  for key,limit in [('Slice',21216),('LUT6',21216),('Register',42432),('ERAM20K',108),('DSP',40)]:assert resources[key]<=limit
  summary=read(attempt/'target_color_regions_pr.timing')
  exceptions=read(attempt/'target_color_regions_exception.timing')
  coverage=float(re.search(r'STA coverage\s*:\s*([\d.]+)%',summary)[1])
  ignored=int(re.search(r'Ignored\s*:\s*(\d+)',exceptions)[1])
  obj.update(status='FUNCTIONAL_SOFTWARE_AND_TD_PASSED_HARDWARE_PENDING',bit_sha256=sha(bit),
    resources=resources,timing_ns=timing,sta_coverage_percent=coverage,
    ignored_max_delay_constraints=ignored,clock_warning='See original TD clock report; local camera clock routing and physical CDC still require hardware validation.')
 print('COLOR_REGIONS_AUDIT_PASS',len(inputs),'frozen inputs',len(baseline['protected_bits']),'protected bits',flush=True)
 return obj
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);p.add_argument('--check-build',action='store_true');a=p.parse_args()
 audit(R/a.attempt if not Path(a.attempt).is_absolute() else a.attempt,a.check_build)
