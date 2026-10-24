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
    ring=branch=='feature/transparent-ring-stability'
    assert ring or branch=='docs/color-regions-env-issues',branch
    if ring:
        subprocess.run(git+['merge-base','--is-ancestor','43564ee356443ede2c03688a70f1c8a71ca6589b',head],check=True)
        from ring_protection import P,digest
        for path,h in json.loads(P.read_text(encoding='utf-8')).items():assert digest(Path(path))==h,('protected user/history input',path)
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
    if ring:
        expected|={'stable_footer_glyph_rom','stable_footer_program_rom','stable_footer_text_rom'}
        assert '../rtl/09_osd_ui/scaling_logo_rom.v' in project
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
                'stable_capture.log':['STABLE_CAPTURE_PASS'],'stable_controls.log':['STABLE_CONTROLS_PASS'],
                'stable_packer.log':['STABLE_PACKER_PASS'],'stable_ingress.log':['172800 words','PASS ingress CP=8 DP=7','PASS ingress CP=5 DP=11','PASS ingress CP=11 DP=5'],
                'stable_video.log':['STABLE_VIDEO_PASS'],'stable_transport.log':['PASS association','PASS stable moving display'],
                'stable_live.log':['STABLE_LIVE_PASS pair0','STABLE_LIVE_PASS pair1','four pages, three zooms, parameter switch'],
                'stable_isp.log':['STABLE_ISP_PASS'],
                'stable_faults.log':['STABLE_FAULTS_PASS'],
                'stable_adversarial.log':['STABLE_TRACKER_ADVERSARIAL_PASS','STABLE_GRID_BANKS_PASS','STABLE_CAPTURE_MODELS_PASS']}
        evidence_root=R/'reports/transparent_ring/regression' if ring else R/'reports'
        if not ring:checks.update({'stable_filter.log':['STABLE_FILTER_PASS'],'stable_calibration.log':['STABLE_CALIBRATION_PASS']})
        if ring:checks['ring_live_final.log']=checks.pop('stable_live.log')
        evidence={}
        for name,markers in checks.items():
            p=evidence_root/name;text=p.read_text(encoding='utf-8');assert all(m in text for m in markers),name
            assert 'FATAL:' not in text and 'error:' not in text,name
            evidence[p.relative_to(R).as_posix()]=sha(p)
        cases=json.loads((evidence_root/'stable_video_cases.json').read_text(encoding='utf-8'))
        assert {(j[0],j[1],j[4]) for j in cases if j[5]==0} >= {(p,z,m) for p in (0,1) for z in range(3) for m in range(4)}
        if ring:
            assert {(j[0],j[1],j[4],j[7]) for j in cases if j[5]==0} >= {(p,z,m,r) for p in (0,1) for z in range(3) for m in range(4) for r in (0,1)}
            live=(evidence_root/'ring_live_final.log').read_text(encoding='utf-8')
            assert all(f'STABLE_LIVE_PASS pair{p} rotation{r}' in live for p in (0,1) for r in (0,1))
            final_live=json.loads((evidence_root/'ring_live_final_inputs.json').read_text(encoding='utf-8'))
            assert final_live['input_hashes_unchanged'] and final_live['frames']==20
            for n,h in final_live['inputs'].items():assert sha(R/n)==h,('final live input changed',n)
            extra={'calibration_acquisition.log':'RING_CALIBRATION_PASS','background_sampler.log':'RING_BACKGROUND_SAMPLER_PASS',
                   'after_broad_cluster.log':'success=1','before_broad_cluster.log':'success=0',
                   'after_polluted_frames.log':'success=0','before_polluted_frames.log':'success=1',
                   'after_dark_blue_background.log':'success=1','after_inseparable_background.log':'success=0',
                   'grid_phases_after.log':'retained=512/512','grid_phases_before.log':'retained=432/512',
                   'strong_filter.log':'RING_FILTER_PASS','tracker_quality.log':'RING_TRACKER_PASS',
                   'tracker_quality_before.log':'RING_TRACKER_BEFORE_PASS','diagnostics_capture.log':'RING_DIAGNOSTICS_PASS',
                   'protocol_v3.log':'RING_PROTOCOL_PASS','controls_chords.log':'RING_CONTROLS_PASS',
                   'ui_pixels.log':'RING_UI_PASS','view_rotation.log':'RING_VIEW_PASS','publication_collision.log':'RING_PUBLICATION_PASS'}
            for material in ('purple_dark_bias','yellow_dark_bias','blue_metal_reflection','purple_neutral_background','yellow_bright_neutral'):
                for version in ('before','after'):extra[f'{version}_{material}.log']='success=1'
            for fixture in ('four_edges','quality_top4','rejected_first_owner','shared_fringe','thin_shapes','weak_chain','weak_print_and_ring'):
                for strict in (0,4):extra[f'grid_{fixture}_strict{strict}.log']='RING_GRID_EDGES_PASS'
            for name,marker in extra.items():
                path=R/'reports/transparent_ring'/name;text=path.read_text(encoding='utf-8')
                assert marker in text and 'FATAL:' not in text and 'error:' not in text,name
                evidence[path.relative_to(R).as_posix()]=sha(path)
            obj.update(video_jobs=len(cases),video_frames=sum(j[6] for j in cases),video_pixels=sum(j[6] for j in cases)*1280*624)
        obj['evidence']=evidence
    print('STABLE_AUDIT_PASS',len(inputs),'inputs;',len(baseline['protected']),'protected artifacts',flush=True)
    return obj
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);p.add_argument('--check-build',action='store_true');a=p.parse_args()
    obj=audit(R/a.attempt if not Path(a.attempt).is_absolute() else a.attempt,a.check_build)
    print(json.dumps({k:v for k,v in obj.items() if k not in ('protected','evidence')},ensure_ascii=False,indent=2))
