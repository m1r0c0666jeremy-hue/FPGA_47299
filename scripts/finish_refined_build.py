"""One-shot completion of the explicitly selected in-progress build attempts.

No scheduling, retries of failed builds, Git changes, board writes or uploads.
A passing summary only triggers the existing full audit and guarded packager.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,sys,time,zipfile
R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--attempt',action='append',required=True)
ap.add_argument('--timeout-hours',type=float,default=4);a=ap.parse_args()
attempts=sorted({(R/name).resolve() for name in a.attempt})
assert 0<a.timeout_hours<=12
assert all(p.is_relative_to(R/'build') and p.is_dir() for p in attempts)
key=hashlib.sha256('\n'.join(p.relative_to(R).as_posix() for p in attempts).encode()).hexdigest()[:16]
out=R/'build'/f'refined_delivery_watch_{key}';out.mkdir(exist_ok=False)
documents=[R/'README.md',R/'reports/refined/最终验证报告.md',R/'docs/颜色视频显示改进_上板一页.md']
originals={p:sha(p) for p in documents}
state=dict(status='WAITING_FOR_FULL_BUILD',started=datetime.datetime.now().isoformat(),pid=__import__('os').getpid(),attempts=[p.relative_to(R).as_posix() for p in attempts],documents={p.relative_to(R).as_posix():v for p,v in originals.items()})
def save(**changes):
 state.update(changes,updated=datetime.datetime.now().isoformat())
 (out/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
save();print('REFINED_COMPLETION_WATCH',out,flush=True)
deadline=time.monotonic()+a.timeout_hours*3600
try:
 while time.monotonic()<deadline:
  finished=[]
  for p in attempts:
   try:s=json.loads((p/'summary.json').read_text(encoding='utf-8'))
   except (FileNotFoundError,json.JSONDecodeError):continue
   finished.append(p)
   if not (s.get('stage')=='full' and s.get('exit_code')==0 and s.get('resource_pass') and s.get('timing_pass') and s.get('inputs_unchanged')):continue
   assert all(sha(p)==value for p,value in originals.items()),'Delivery documents changed while waiting; review before publication'
   save(status='AUDITING',selected=p.relative_to(R).as_posix())
   stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
   audit_record=R/'reports/refined'/f'final_audit_{stamp}.json'
   with (out/'completion.log').open('x',encoding='utf-8') as log:
    subprocess.run([sys.executable,'-X','utf8',str(R/'scripts/audit_refined.py'),'--regression','--attempt',str(p),'--record',str(audit_record)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
    save(status='PACKAGING',audit=audit_record.relative_to(R).as_posix())
    previous=set((R/'reports/refined').glob('delivery_*.json'))
    subprocess.run([sys.executable,'-X','utf8',str(R/'scripts/package_refined.py'),'--attempt',str(p)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
   created=set((R/'reports/refined').glob('delivery_*.json'))-previous
   assert len(created)==1,created
   record=created.pop();delivery=json.loads(record.read_text(encoding='utf-8'))
   dest=(R/delivery['delivery_directory']).resolve();assert dest.is_relative_to(R/'build')
   assert sha(R/delivery['bit'])==delivery['bit_sha256']
   assert sha(R/delivery['source_zip'])==delivery['source_zip_sha256']
   for line in (dest/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    expected,name=line.split('  ',1);assert sha(dest/name)==expected,name
   with zipfile.ZipFile(R/delivery['source_zip']) as z:
    manifest=json.loads(z.read('SOURCE_MANIFEST.json'))
    assert set(z.namelist())==set(manifest)|{'SOURCE_MANIFEST.json'}
    for name,value in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==value,name
   save(status='PACKAGED_FINAL_ARCHIVE_PENDING',delivery=record.relative_to(R).as_posix(),bit=delivery['bit'],bit_sha256=delivery['bit_sha256'],source_zip=delivery['source_zip'],source_zip_sha256=delivery['source_zip_sha256'],hardware='PENDING',git_commit='PENDING; no automatic Git changes')
   print('REFINED_COMPLETION_PACKAGED',record,flush=True);raise SystemExit(0)
  if len(finished)==len(attempts):
   save(status='NO_PASSING_BUILD',reason='All selected full builds ended without meeting the final resource/timing gates; no packager invoked')
   print('REFINED_COMPLETION_NO_PASSING_BUILD',out,flush=True);raise SystemExit(2)
  time.sleep(10)
 save(status='WAIT_TIMEOUT',reason='No passing selected build within the finite wait; TD processes were not stopped')
 raise SystemExit(3)
except Exception as error:
 save(status='REVIEW_REQUIRED',error=repr(error))
 raise
