"""Read-only audit of the f395 Git return, extracted frame writer and reused bit."""
from pathlib import Path
import argparse, subprocess, json, hashlib, re
R=Path(__file__).resolve().parents[1]
BASE='f395cc011ef4c21f15863192ce148938834bd639'
FIX='cf8b7c463a415bd8741fed4ec68ff3eeac252455'
FIXPATH='user_source/hdl_source/video_in.v'
def git(*args):
 return subprocess.check_output(['git','-c','safe.directory='+R.as_posix(),*args],cwd=R)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
p=argparse.ArgumentParser();p.add_argument('--archive',action='store_true');args=p.parse_args()
m=json.loads((R/'reports/git_return_restore_manifest.json').read_text(encoding='utf-8'))
assert git('rev-parse','HEAD').decode().strip()==BASE
assert git('branch','--show-current').decode().strip()=='LockingnTracking'
assert git('diff','--name-only').decode().splitlines()==[FIXPATH]
assert not git('diff','--cached','--name-only')
entries=[]
for item in git('ls-tree','-r','-z',BASE).split(b'\0'):
 if not item:continue
 info,path=item.split(b'\t',1);mode,kind,oid=info.split();assert kind==b'blob'
 entries.append((path.decode('utf-8'),oid))
batch=subprocess.run(['git','-c','safe.directory='+R.as_posix(),'cat-file','--batch'],cwd=R,
 input=b''.join(oid+b'\n' for _,oid in entries),capture_output=True)
assert batch.returncode==0,batch.stderr
offset=0
for path,oid in entries:
 end=batch.stdout.index(b'\n',offset);header=batch.stdout[offset:end].split();assert header[0]==oid
 size=int(header[2]);start=end+1;expected=batch.stdout[start:start+size];offset=start+size+1
 if path==FIXPATH:expected=git('show',FIX+':'+path)
 assert (R/path).read_bytes()==expected,path
frozen=json.loads((R/'reports/candidate_ingress_build_inputs.json').read_text(encoding='utf-8'))['inputs']
assert len(frozen)==78
for path,h in frozen.items():assert sha(R/path)==h,path
assert sha(R/m['bit'])==m['bit_sha256']
refs={}
for line in git('for-each-ref','--format=%(refname) %(objectname) %(symref)').decode().splitlines():
 fields=line.split();refs[fields[0]]={'object':fields[1],'symref':fields[2] if len(fields)>2 else None}
assert refs==m['expected_refs']
assert git('remote','get-url','origin').decode().strip()==m['remote_url']
generated=json.loads((R/'reports/target_generation_manifest.json').read_text(encoding='utf-8'))
for path,h in generated['files'].items():assert sha(R/path)==h,path
for name,h in m['evidence_sha256'].items():assert sha(R/name)==h,name
logs={name:(R/name).read_text(encoding='utf-8') for name in ['reports/git_return_ingress.log','reports/git_return_video_simulation.log']}
ingress,video=logs.values()
assert ingress.count('PASS AWB 960 packed = 960 DDR')==2
assert ingress.count('PASS ingress CP=')==6
assert 'VENDOR_FIFO_RTL' in ingress
assert video.count('PASS target video:')==15
assert sum(map(int,re.findall(r'pixels=\s*(\d+)',video)))==15175680
assert all(term not in ingress+video for term in ['FATAL:','Traceback','ERROR:'])
if args.archive:
 before=json.loads(Path(m['complete_backup_record']).read_text(encoding='utf-8'))
 a=Path(m['archive'])
 files={path.relative_to(a).as_posix() for path in a.rglob('*') if path.is_file()}
 assert files==set(before['files_archived'])
 for path,data in before['files_archived'].items():
  assert (a/path).stat().st_size==data['size'] and sha(a/path)==data['sha256'],path
 late=Path(str(a)+'_td_saved')
 for path,data in before['td_saved_updates'].items():assert sha(late/path)==data['sha256'],path
print('GIT_RETURN_AUDIT_PASSED',len(entries),'tracked files;',len(frozen),'build inputs; 960/960; 15 video cases;', 'archive checked' if args.archive else 'source checked')
