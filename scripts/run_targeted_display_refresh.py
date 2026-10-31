"""Bounded current-source regressions after the three targeted display repairs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,datetime,subprocess,sys,hashlib
R=Path(__file__).resolve().parents[1]

def main():
    phase=R/(R/'build/current_targeted_display_retime_path.txt').read_text().strip()
    out=phase/('software_refresh_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'));out.mkdir()
    from stage1_policy import compiler_paths
    frozen={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in compiler_paths(R)}
    short=[['test_stage1_release1030.py','--part','stats'],['test_stage1_release1030.py','--part','footer']]
    short += [[n] for n in ('test_stage1_footer_equivalence.py','test_stage1_camera_osd.py',
      'test_stage1_k_tracker.py','test_stage1_k_capture.py','test_stage1_k_controls.py',
      'test_stage1_rect_observer.py','test_stage1_scene_observer.py','test_stage1_teaching.py',
      'test_stage1_teach_pause_transactions.py','test_stage1_teach_replay30.py',
      'test_stage1_teach_transactions.py','test_stage1_teach_integration.py','test_stage1_teach_alarm.py',
      'test_stage1_teach_pixels.py','test_stage1_real_keys.py','test_stage1_transactions.py',
      'test_stage1_project.py','test_stage1_regions.py','test_stage1_rect.py','test_stage1_overlay.py',
      'test_stage1_region_footer.py','test_stage1_legacy_clock.py')]
    short += [['test_stage1_real_keys.py','--faults'],['test_stage1_rect.py','--geometry']]
    short += [['test_stage1_footer.py',*a] for a in ([],['--abort'],['--wait'])]
    baseline=[['test_stage1_timing_baseline.py',n,*a] for n,a in (
      ('test_refined_geometry.py',[]),('test_refined_fault_v4.py',[]),('test_refined_arbitration.py',[]),
      ('test_osd_memory_ui.py',[]),('test_osd_memory_ui.py',['--abort']),('test_osd_memory_ui.py',['--wait']),
      ('test_osd_memory_overlay.py',[]),('test_osd_packed_program.py',[]))]
    jobs={'short_current':short,'baseline12':baseline,
      'video84':[['test_stage1_video.py','--full','--faults','--workers','2','--reuse-current']],
      'live4':[['test_stage1_live.py','--reader','refined','--store','refined','--line-gap','160','--workers','1']]}
    record={'started':datetime.datetime.now().astimezone().isoformat(),'inputs':frozen,'jobs':{}}
    def save(): (out/'progress.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    def execute(name,commands):
        with (out/(name+'.log')).open('w',encoding='utf-8') as log:
            for args in commands:
                log.write('RUN '+repr(args)+'\n');log.flush()
                code=subprocess.run([sys.executable,'-X','utf8',str(R/'scripts'/args[0]),*args[1:]],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
                if code:return {'exit_code':code,'failed_command':args}
        return {'exit_code':0,'commands':commands}
    save();print('TARGETED_DISPLAY_REFRESH',out,flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks={pool.submit(execute,n,c):n for n,c in jobs.items()}
        for f in as_completed(tasks):
            name=tasks[f];record['jobs'][name]=f.result();save();print(name,record['jobs'][name]['exit_code'],flush=True)
    assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in frozen.items()),'Active RTL changed'
    record.update(finished=datetime.datetime.now().astimezone().isoformat(),inputs_unchanged=True);save()
    if any(v['exit_code'] for v in record['jobs'].values()):raise SystemExit(1)
    print('TARGETED_DISPLAY_REFRESH_PASS',flush=True)

if __name__=='__main__':main()
