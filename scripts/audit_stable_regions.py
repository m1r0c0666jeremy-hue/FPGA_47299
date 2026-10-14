"""Read-only audit of production inputs, old artifacts, real TD and log evidence."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys,zipfile
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(attempt,check_build=False):
    attempt=Path(attempt).resolve();assert attempt.is_relative_to(R/'build')
    baseline=json.loads((R/'reports/stable_regions_baseline.json').read_text(encoding='utf-8'))
    git=['git','-c',f'safe.directory={R.as_posix()}','-C',str(R)]
    head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()
    branch=subprocess.check_output(git+['branch','--show-current'],text=True).strip()
    subprocess.run(git+['merge-base','--is-ancestor',baseline['head'],head],check=True)
    assert branch=='docs/color-regions-env-issues',branch
    for n,h in baseline['protected'].items():assert sha(R/n)==h,('old artifact changed',n)
    for n,h in baseline['inputs'].items():
        if n.startswith(('rtl/','user_source/')) and Path(n).suffix.lower() in ('.v','.sv','.tcl','.adc','.sdc'):
            assert sha(R/n)==h,('original RTL/IP changed',n)
    inputs=json.loads((attempt/'inputs.json').read_text(encoding='utf-8'))
    assert inputs==json.loads((attempt/'inputs_after.json').read_text(encoding='utf-8'))
    for n,h in inputs.items():assert sha(R/n)==h,('compiled input changed',n)
    with zipfile.ZipFile(attempt/'source_snapshot.zip') as z:
        assert set(z.namelist())==set(inputs)
        for n,h in inputs.items():assert hashlib.sha256(z.read(n)).hexdigest()==h,('snapshot mismatch',n)
    subprocess.run([sys.executable,str(R/'scripts/generate_target.py'),'--color-regions','--check'],cwd=R,check=True)
    project=(R/'td_project/target_color_regions.al').read_text(encoding='utf-8')
    assert f'Path="{(R/"td_project").as_posix()}"' in project
    names=set(re.findall(r'../rtl/color_regions/([^"/]+)\.v',project))
    expected={'regions_divide'}|{'stable_'+n for n in ('model_lane','awb','packer','calibration','controls','filter4','grid','tracker','capture','frame_store','display','line_reader','preprocess','osd','glyph_rom','isp','camera_capture','memory_video_out','top')}
    assert names==expected,names^expected
    obj=dict(head=head,branch=branch,attempt=attempt.relative_to(R).as_posix(),input_count=len(inputs),
             ingress_sha256=sha(R/'user_source/hdl_source/video_in.v'),protected=baseline['protected'],hardware='PENDING')
    if check_build:
        log=(R/'reports'/(attempt.name+'.log')).read_text(encoding='utf-8')
        assert 'TARGET_COLOR_REGIONS_BUILD_COMPLETED' in log and 'BUILD_FAILED:' not in log
        bit=attempt/'target_color_regions.bit';assert bit.is_file()
        ts=(attempt/'target_color_regions_phy.ts').read_text(encoding='utf-8')
        timing={n:float(re.search(n+r':\s*([-\d.]+)ns',ts)[1]) for n in ('SWNS','HWNS')}
        assert min(timing.values())>=0,timing
        area=(attempt/'target_color_regions_phy.area').read_text(encoding='utf-8')
        resources={k:int(re.search(r'^#'+tag+r'\s+(\d+)',area,re.M)[1]) for k,tag in [('Slice','slice'),('LUT6','lut6'),('Register','reg'),('ERAM20K','eram'),('DSP','dsp')]}
        for k,limit in [('Slice',21216),('LUT6',21216),('Register',42432),('ERAM20K',108),('DSP',40)]:assert resources[k]<=limit,(k,resources[k])
        summary=(attempt/'target_color_regions_pr.timing').read_text(encoding='utf-8')
        exceptions=(attempt/'target_color_regions_exception.timing').read_text(encoding='utf-8')
        obj.update(status='PRODUCTION_SOFTWARE_AND_BUILD_PASSED_HARDWARE_PENDING',bit_sha256=sha(bit),timing_ns=timing,
                   resources=resources,sta_coverage_percent=float(re.search(r'STA coverage\s*:\s*([\d.]+)%',summary)[1]),
                   ignored_max_delay_constraints=int(re.search(r'Ignored\s*:\s*(\d+)',exceptions)[1]))
        checks={'stable_units.log':['STABLE_CLASSIFIER_PASS','STABLE_AWB_PASS','STABLE_GRID_PASS case0','STABLE_GRID_PASS case1','STABLE_GRID_PASS case2'],
                'stable_filter.log':['STABLE_FILTER_PASS'],'stable_calibration.log':['STABLE_CALIBRATION_PASS'],
                'stable_capture.log':['STABLE_CAPTURE_PASS'],'stable_controls.log':['STABLE_CONTROLS_PASS'],
                'stable_packer.log':['STABLE_PACKER_PASS'],'stable_ingress.log':['172800 words','PASS ingress CP=8 DP=7','PASS ingress CP=5 DP=11','PASS ingress CP=11 DP=5'],
                'stable_video.log':['STABLE_VIDEO_PASS'],'stable_transport.log':['PASS association','PASS stable moving display'],
                'stable_live.log':['STABLE_LIVE_PASS pair0','STABLE_LIVE_PASS pair1','four pages, three zooms, parameter switch'],
                'stable_isp.log':['STABLE_ISP_PASS'],
                'stable_faults.log':['STABLE_FAULTS_PASS'],
                'stable_adversarial.log':['STABLE_TRACKER_ADVERSARIAL_PASS','STABLE_GRID_BANKS_PASS','STABLE_CAPTURE_MODELS_PASS']}
        evidence={}
        for name,markers in checks.items():
            p=R/'reports'/name;text=p.read_text(encoding='utf-8');assert all(m in text for m in markers),name
            assert 'FATAL:' not in text and 'error:' not in text,name
            evidence[name]=sha(p)
        cases=json.loads((R/'reports/stable_video_cases.json').read_text(encoding='utf-8'))
        assert {(j[0],j[1],j[4]) for j in cases if j[5]==0} >= {(p,z,m) for p in (0,1) for z in range(3) for m in range(4)}
        obj['evidence']=evidence
    print('STABLE_AUDIT_PASS',len(inputs),'inputs;',len(baseline['protected']),'protected artifacts',flush=True)
    return obj
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);p.add_argument('--check-build',action='store_true');a=p.parse_args()
    obj=audit(R/a.attempt if not Path(a.attempt).is_absolute() else a.attempt,a.check_build)
    print(json.dumps({k:v for k,v in obj.items() if k not in ('protected','evidence')},ensure_ascii=False,indent=2))
