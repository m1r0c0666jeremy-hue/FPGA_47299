"""Run the independent FHD suite once against a hashed, unchanged source tree."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse,datetime,hashlib,json,subprocess,sys,time
from refined_testlib import R

def sources():
    paths=[R/'profile_1080p30.json']
    for folder in ('rtl','ip','user_source','assets','scripts','sim','td_project'):
        paths.extend(p for p in (R/folder).rglob('*') if p.is_file() and p.suffix.lower() not in ('.pyc','.log','.logw'))
    return {p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=3);a=ap.parse_args()
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    out=R/'reports/fhd/regression'/stamp;out.mkdir(parents=True)
    before=sources();(out/'inputs.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    jobs=[('sim_cli',['test_fhd_sim_cli.py']),('timebase',['test_fhd_timebase.py']),
          ('camera_bridge',['test_fhd_camera_bridge.py']),('csi_bridge',['test_fhd_csi_bridge.py']),
          ('isp',['test_fhd_isp.py']),('sensor_config',['test_fhd_camera_config.py']),
          ('camera',['test_fhd_camera_integration.py']),('processing',['test_fhd_processing.py']),
          ('calibration_replay',['test_fhd_calibration_replay.py']),('controls',['test_refined_controls.py']),
          ('transport',['test_fhd_transport.py','--full','--video-backend','native','--workers','3']),
          ('four_state_video',['test_fhd_transport.py','--suite','video','--zoom','0','--rotate','0','--mode','0']),
          ('four_state_highlight',['test_fhd_transport.py','--suite','video','--zoom','1','--rotate','0','--mode','1','--color','--pair','1']),
          ('four_state_binary',['test_fhd_transport.py','--suite','video','--zoom','4','--rotate','1','--mode','3','--color']),
          ('joint_video',['test_fhd_live.py','--backend','native','--workers','2']),
          ('camera_hdmi_recovery',['test_fhd_camera_hdmi.py'])]
    def execute(job):
        name,args=job;start=time.monotonic();log=out/(name+'.log')
        command=[sys.executable,str(R/'scripts'/args[0]),*args[1:]]
        with log.open('w',encoding='utf-8') as f:
            code=subprocess.run(command,cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
        record=dict(name=name,arguments=args,exit_code=code,seconds=round(time.monotonic()-start,3),log=str(log),log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
        print('FHD_REGRESSION_JOB',name,'PASS' if code==0 else 'FAIL',record['seconds'],flush=True)
        return record
    results=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for future in as_completed([pool.submit(execute,j) for j in jobs]):results.append(future.result())
    unchanged=before==sources()
    summary=dict(created_local=datetime.datetime.now().isoformat(),passed=unchanged and all(r['exit_code']==0 for r in results),
                 inputs_unchanged=unchanged,inputs_sha256=hashlib.sha256((out/'inputs.json').read_bytes()).hexdigest(),jobs=results)
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('FHD_REGRESSION_RESULT',out,summary['passed'],flush=True)
    return 0 if summary['passed'] else 1
if __name__=='__main__':sys.exit(main())
