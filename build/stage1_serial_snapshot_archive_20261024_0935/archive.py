"""Archive completed current G3 evidence only; never stage active route files.

Requires a sealed 112-check report. This is a local Git archive, not a board
delivery, and does not run synthesis, simulation, routing or publication.
"""
from pathlib import Path
import argparse, datetime, json, subprocess, sys

O = Path(__file__).resolve().parent
R = O.parents[1]
sys.path.insert(0, str(R / 'scripts'))
from audit_stage1 import audit, sha

ap = argparse.ArgumentParser()
ap.add_argument('--software', required=True)
ap.add_argument('--commit', action='store_true')
a = ap.parse_args()
report = (R / a.software).resolve()
assert report.is_relative_to(R / 'reports/stage1')
proof = json.loads(report.read_text(encoding='utf8'))
fresh = audit()
assert fresh['required'] == fresh['passed'] == 112 and not fresh['missing']
assert proof['regression'] == fresh['regression']
assert proof['required'] == proof['passed'] == 112 and not proof['missing']
assert fresh['generator_pass'] and fresh['original_protection_pass']
assert proof['head'] == fresh['head']
git = ['git', '-c', 'safe.directory=' + R.as_posix()]
assert not subprocess.check_output(git + ['diff', '--cached', '--name-only'], cwd=R), 'Preserve existing staged changes'

paths = {report, Path(__file__).resolve()}
for e in proof['regression'].values():
    record = R / e['record']
    assert sha(record) == e['record_sha256']
    assert sha(record.with_suffix('.log')) == e['log_sha256']
    paths.update((record, record.with_suffix('.log')))
    for group in ('inputs', 'fixture_inputs', 'producer_inputs'):
        for name, h in e[group].items():
            p = (R / name).resolve()
            assert p.is_relative_to(R) and sha(p) == h, name
            paths.add(p)

place = R / 'build/stage1_place_20261024_090145'
summary = json.loads((place / 'summary.json').read_text())
assert summary['stage'] == 'place' and summary['exit_code'] == 0 and summary['inputs_unchanged']
assert all(sha(place / n) == h for n, h in summary['checkpoints'].items())
for p in place.iterdir():
    if p.is_file() and p.suffix in ('.json', '.tcl', '.txt', '.log', '.area', '.timing', '.qor', '.zip', '.al'):
        paths.add(p)
review_dir = R / 'build/stage1_place_review_20261024_0913'
paths.update(p for p in review_dir.rglob('*') if p.is_file() and p.suffix in ('.py', '.json', '.tcl', '.txt', '.log'))
paths.update(R / n for n in (
    'reports/stage1/placement_review_20261024_092143.json',
    'README.md', 'reports/stage1/validation.md',
    'docs/区域顺序_第一阶段_执行记录.md', 'scripts/package_stage1.py',
    'build/stage1_serial_snapshot_adoption_20261024_0855/run_checks.py'))
assert report.relative_to(R).as_posix().encode() in (R / 'scripts/package_stage1.py').read_bytes()
assert all(p.is_file() and p.is_relative_to(R) for p in paths)
assert not any('stage1_route_20261024_092334_800316' in str(p) for p in paths)
manifest = {p.relative_to(R).as_posix(): sha(p) for p in sorted(paths)}
out = O / ('archive_manifest_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.json')
result = dict(status='CURRENT_SOFTWARE_AND_PLACEMENT_ARCHIVE_FINAL_ROUTE_PENDING',
              compiler_commit='555020828e32058ec6b7a3c7f61045b4c5cbbcab',
              software_report=report.relative_to(R).as_posix(),
              software_report_sha256=sha(report), current_checks=112,
              resources=summary['resources'], files=manifest,
              hardware_status='PENDING; no push, board download or Flash write')
with out.open('x', encoding='utf8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
paths.add(out)
if a.commit:
    payload = b''.join(p.relative_to(R).as_posix().encode('utf8') + b'\0' for p in sorted(paths))
    subprocess.run(git + ['add', '-f', '--pathspec-from-file=-', '--pathspec-file-nul'], input=payload, cwd=R, check=True)
    assert all(sha(R / n) == h for n, h in manifest.items())
    subprocess.run(git + ['commit', '-m', 'stage1: archive G3 current 112 checks and measured placement'], cwd=R, check=True)
print('G3_CURRENT_EVIDENCE_ARCHIVED' if a.commit else 'G3_ARCHIVE_MANIFEST_PREPARED', out, len(paths))
