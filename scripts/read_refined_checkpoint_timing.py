"""Read a TD placed checkpoint without changing its database or constraints."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--attempt', required=True)
args = parser.parse_args()
attempt = (ROOT / args.attempt).resolve()
assert attempt.parent == ROOT / 'build'
database = attempt / 'target_color_regions_placed.db'
before = hashlib.sha256(database.read_bytes()).hexdigest()
out = ROOT / 'build' / ('refined_checkpoint_timing_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
out.mkdir(exist_ok=False)
script = out / 'run.tcl'
script.write_text('''cd {%s}
if {[catch {
 import_device ph1_35p.db -package PH1P35MDG324 -speed 3
 import_db {%s}
 update_timing -mode manhattan
 report_timing_summary -file detailed.timing -ep_num 20 -path_num 1
 report_analysis manhattan -timing -max_path_num 20 -path_num_per_ep 1 -file timing_analysis.txt
 puts "READONLY_CHECKPOINT_TIMING_PASS"
} message]} {puts stderr "PROBE_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
''' % (out.as_posix(), database.as_posix()), encoding='utf-8')
with (out / 'td.log').open('w', encoding='utf-8') as log:
    result = subprocess.run(['D:/26_software/TangDynasty/bin/td_commands_prompt.exe', script.as_posix()],
                            cwd=out, stdout=log, stderr=subprocess.STDOUT)
log = (out / 'td.log').read_text(encoding='utf-8', errors='replace')
ok = result.returncode == 0 and 'READONLY_CHECKPOINT_TIMING_PASS' in log and (out / 'detailed.timing').is_file()
record = dict(probe_only=True, confidence='Placed / Manhattan; NOT final routed timing',
              source=database.relative_to(ROOT).as_posix(), sha256=before,
              checkpoint_unchanged=before == hashlib.sha256(database.read_bytes()).hexdigest(),
              exit_code=result.returncode, tool_script_executed='READONLY_CHECKPOINT_TIMING_PASS' in log)
if ok:
    report = (out / 'detailed.timing').read_text(encoding='utf-8', errors='replace')
    paths = []
    for block in report.split('Slack               : ')[1:]:
        header = block.split('Delay Type')[0]
        if 'Check Type' not in header:
            continue
        def field(key):
            match = re.search(r'^' + re.escape(key) + r'\s*:\s*(.*)$', header, re.M)
            return match.group(1) if match else None
        paths.append(dict(slack_ns=float(header.splitlines()[0].replace('ns', '')),
                          check=field('Check Type'), begin=field('Begin Point'), end=field('End Point'),
                          budget=field('Budget'), delay=field('Data Path Delay')))
    record['reported_paths'] = len(paths)
    record['worst_paths'] = {kind: sorted([p for p in paths if p['check'] == kind],
                                         key=lambda p: p['slack_ns'])[:3] for kind in ('setup', 'hold')}
record['status'] = 'PASS' if ok and record['checkpoint_unchanged'] else 'FAILED'
(out / 'summary.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(out.relative_to(ROOT).as_posix(), record['status'])
assert record['status'] == 'PASS', record
