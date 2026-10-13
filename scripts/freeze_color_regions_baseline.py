"""One-time, non-destructive source/bit freeze before the functional experiment."""
from pathlib import Path
import hashlib,json,subprocess,zipfile,datetime
R=Path(__file__).resolve().parents[1]
P=R/'reports/color_regions_baseline.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(R),*a],encoding='utf-8').strip()
if P.exists():
    old=json.loads(P.read_text(encoding='utf-8'))
    for f,h in old['protected_bits'].items():assert sha(R/f)==h,f
    assert sha(R/'user_source/hdl_source/video_in.v')==old['ingress_sha256']
    print('REGIONS_BASELINE_PROTECTION_PASS');raise SystemExit
assert git('branch','--show-current')=='LockingnTracking'
assert git('rev-parse','HEAD')=='e82a62fca10dc6e8e6807b426666866ef4217054'
sources=[]
for folder in ('rtl','scripts','sim','td_project','user_source'):
    sources += [p for p in (R/folder).rglob('*') if p.is_file() and p.suffix.lower() in
                ('.v','.sv','.json','.py','.txt','.al','.tcl','.adc','.sdc','.mem','.hex')
                and '__pycache__' not in p.parts and 'log' not in p.parts]
sources += [R/'README.md']
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
archive=R/'reports'/f'color_regions_before_{stamp}.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(set(sources)):z.write(p,p.relative_to(R).as_posix())
with zipfile.ZipFile(archive) as z:
    for p in sorted(set(sources)):assert z.read(p.relative_to(R).as_posix())==p.read_bytes()
obj={'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),
     'status':git('status','--short'),'source_archive':archive.relative_to(R).as_posix(),
     'source_archive_sha256':sha(archive),'source_inputs':{p.relative_to(R).as_posix():sha(p) for p in sorted(set(sources))},
     'protected_bits':{p.relative_to(R).as_posix():sha(p) for p in R.rglob('*.bit')},
     'ingress_sha256':sha(R/'user_source/hdl_source/video_in.v')}
assert obj['ingress_sha256']=='6c02b617ef32c478ab39bf17e0fe5e48a3f6e38eca1796bf628cb19052c7838b'
P.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('REGIONS_BASELINE_FROZEN',len(sources),len(obj['protected_bits']),archive)
