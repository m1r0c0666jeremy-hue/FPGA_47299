"""Refresh only the twelve invalidated short cases and video/live evidence."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime, hashlib, json, subprocess, sys
from stage1_policy import compiler_paths
R = Path(__file__).resolve().parents[1]


def main():
    phase = R/(R/'build/current_demo_1101_path.txt').read_text().strip()
    out = phase/('software_refresh_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    out.mkdir()
    frozen = {p.relative_to(R).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in compiler_paths(R)}
    jobs = {
        'short': [[n] for n in (
            'test_refined_camera_gate.py', 'test_stage1_footer_equivalence.py',
            'test_stage1_camera_osd.py', 'test_stage1_k_tracker.py',
            'test_stage1_k_capture.py', 'test_stage1_teach_alarm.py',
            'test_stage1_teach_pixels.py', 'test_stage1_project.py',
            'test_stage1_overlay.py', 'test_stage1_region_footer.py')]
            + [['test_stage1_footer.py', *a] for a in ([], ['--abort'], ['--wait'])],
        'video84': [['test_stage1_video.py', '--full', '--faults',
                     '--workers', '2', '--reuse-current']],
        'live4': [['test_stage1_live.py', '--reader', 'refined', '--store', 'refined',
                   '--line-gap', '160', '--workers', '2']],
    }
    record = {'started': datetime.datetime.now().astimezone().isoformat(),
              'inputs': frozen, 'jobs': {}}

    def save():
        (out/'progress.json').write_bytes((json.dumps(record, indent=2)+'\n').encode())

    def execute(name, commands):
        with (out/(name+'.log')).open('w', encoding='utf-8') as log:
            for args in commands:
                log.write('RUN '+repr(args)+'\n'); log.flush()
                code = subprocess.run(
                    [sys.executable, '-X', 'utf8', str(R/'scripts'/args[0]), *args[1:]],
                    cwd=R, stdout=log, stderr=subprocess.STDOUT).returncode
                if code:
                    return {'exit_code': code, 'failed_command': args}
        return {'exit_code': 0, 'commands': commands}

    save()
    print('DEMO1101_SOFTWARE_REFRESH', out, flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks = {pool.submit(execute, name, commands): name
                 for name, commands in jobs.items()}
        for future in as_completed(tasks):
            name = tasks[future]
            record['jobs'][name] = future.result()
            save()
            print(name, record['jobs'][name]['exit_code'], flush=True)
    assert all(hashlib.sha256((R/n).read_bytes()).hexdigest() == h
               for n, h in frozen.items()), 'Active source changed'
    record.update(finished=datetime.datetime.now().astimezone().isoformat(),
                  inputs_unchanged=True)
    save()
    if any(v['exit_code'] for v in record['jobs'].values()):
        raise SystemExit(1)
    print('DEMO1101_SOFTWARE_REFRESH_PASS', flush=True)


if __name__ == '__main__':
    main()
