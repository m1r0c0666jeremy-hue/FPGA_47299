"""Refresh changed stable-release evidence with bounded simulation concurrency."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import datetime,json,subprocess,sys,hashlib
R=Path(__file__).resolve().parents[1]

def main():
    root=R/(R/'build/current_ry_bp_path.txt').read_text(encoding='utf-8').strip()
    out=root/('software_refresh_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'));out.mkdir()
    from stage1_policy import compiler_paths
    frozen={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in compiler_paths(R)}
    jobs={
      'video84':[['test_stage1_video.py','--full','--faults','--workers','2','--reuse-current']],
      'live4':[['test_stage1_live.py','--reader','refined','--store','refined','--line-gap','160','--workers','1']],
      'k_capture':[['test_stage1_k_tracker.py'],['test_stage1_k_capture.py']],
      # DDR correction changes only the top and memory wrapper. Keep completed
      # unchanged footer/geometry/colour results; refresh their actual consumers.
      'changed_wiring':[[p] for p in ('test_stage1_release1030.py','test_stage1_teach_alarm.py',
        'test_stage1_buzzer_clock.py','test_stage1_camera.py')],
    }
    record={'started':datetime.datetime.now().astimezone().isoformat(),'inputs':frozen,'jobs':{}}
    def save():
        (out/'progress.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    def execute(name,commands):
        with (out/(name+'.log')).open('w',encoding='utf-8') as log:
            for args in commands:
                log.write('RUN '+repr(args)+'\n');log.flush()
                code=subprocess.run([sys.executable,'-X','utf8',str(R/'scripts'/args[0]),*args[1:]],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
                if code:return {'exit_code':code,'failed_command':args}
        return {'exit_code':0,'commands':commands}
    save();print('STABLE_RELEASE_SOFTWARE_REFRESH',out,flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks={pool.submit(execute,n,v):n for n,v in jobs.items()}
        for future in as_completed(tasks):
            name=tasks[future];record['jobs'][name]=future.result();save();print(name,record['jobs'][name]['exit_code'],flush=True)
    assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in frozen.items()),'Active compiler input changed'
    record['finished']=datetime.datetime.now().astimezone().isoformat();record['inputs_unchanged']=True;save()
    if any(v['exit_code'] for v in record['jobs'].values()):raise SystemExit(1)
    print('STABLE_RELEASE_SOFTWARE_REFRESH_PASS',flush=True)

if __name__=='__main__':main()
