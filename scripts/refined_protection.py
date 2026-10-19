"""Freeze/check pre-existing deliveries and user files without rewriting them."""
from pathlib import Path
import argparse, datetime, hashlib, json, subprocess, zipfile
R = Path(__file__).resolve().parents[1]
P = R / 'reports/refined/protected_inputs.json'
def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def record():
    if P.exists():
        raise SystemExit('Refusing to replace protection record')
    branch = subprocess.check_output(['git','branch','--show-current'], cwd=R, text=True).strip()
    head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=R, text=True).strip()
    assert branch == 'release/transparent-ring-stability-20261015'
    assert head == '2f79847f8443fb18f3896a6b88ae9b75c06c9ff8'
    status = subprocess.check_output(['git','status','--porcelain','-z','--untracked-files=all'], cwd=R).split(b'\0')
    user = [R / item[3:].decode('utf-8') for item in status if item]
    paths = set(user + list(R.rglob('*.bit')) + list(R.rglob('*.zip')))
    paths.update(R/'td_project'/n for n in ('target_lock.adc','target_lock.sdc','target_color_regions.al'))
    paths.update(Path(p) for p in (
        'D:/aaa_FPGA/color-regions-env-issues/td_project/target_color_regions.al',
        'D:/aaa_FPGA/criticalwork/td_project/target_color_regions.al'))
    P.parent.mkdir(parents=True, exist_ok=True)
    backup = R / 'build' / ('refined_baseline_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(exist_ok=False)
    tracked = subprocess.check_output(['git','ls-files','-z'], cwd=R).split(b'\0')
    with zipfile.ZipFile(backup/'sources_before.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in tracked:
            if not name: continue
            p = R/name.decode('utf-8')
            if p.is_file() and p.suffix.lower() in ('.v','.sv','.py','.tcl','.al','.adc','.sdc','.json','.txt','.mem','.hex','.svg') and 'build' not in p.relative_to(R).parts:
                z.write(p,p.relative_to(R))
    paths.add(backup/'sources_before.zip')
    data = dict(branch=branch, baseline=head, backup=backup.relative_to(R).as_posix(),
                user_files=[str(p) for p in user],
                files={str(p.resolve()):digest(p) for p in sorted(paths) if p.is_file()})
    P.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('REFINED_PROTECTION_RECORDED',len(data['files']),backup)
def check():
    data=json.loads(P.read_text(encoding='utf-8'))
    changed=[p for p,h in data['files'].items() if not Path(p).is_file() or digest(Path(p))!=h]
    if changed: raise SystemExit('Protected inputs changed: '+str(changed))
    print('REFINED_PROTECTION_PASS',len(data['files']))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--record',action='store_true');a=ap.parse_args()
    record() if a.record else check()
