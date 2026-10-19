"""Preserve the baseline plus the independently observed later .al save."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 baseline=json.loads((R/'reports/refined/protected_inputs.json').read_text(encoding='utf-8'))
 observed=json.loads((R/'reports/refined/user_project_change_20261017.json').read_text(encoding='utf-8'))
 for name,expected in baseline['files'].items():
  p=Path(name)
  if name==observed['path']:
   assert expected==observed['baseline_sha256']
   with zipfile.ZipFile(R/observed['baseline_archive']) as z:
    assert hashlib.sha256(z.read(observed['baseline_member'])).hexdigest()==expected
   assert sha(p)==observed['observed_sha256'],'Original project changed again; preserve and review before proceeding'
   assert sha(R/observed['preserved_copy'])==observed['observed_sha256']
  else:assert sha(p)==expected,'Protected input changed: '+name
 print('REFINED_PROTECTION_PASS',len(baseline['files']),'baseline files plus preserved later project save')
if __name__=='__main__':check()
