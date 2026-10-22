"""Verify the real gate lineage and reject forged metadata/checkpoint copies."""
from pathlib import Path
import argparse,datetime,json,shutil
from audit_stage1 import R,sha,gate_reuse_audit

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--parent',required=True);a=ap.parse_args()
 parent=(R/a.parent).resolve();assert parent.is_relative_to(R/'build')
 before=json.loads((parent/'inputs.json').read_text());context=json.loads((parent/'source_context.json').read_text());commit=context['compiled_source_commit']
 accepted=gate_reuse_audit(parent,before,commit);assert accepted and accepted['inputs_verified']==308
 stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');root=R/'build'/('stage1_gate_reuse_guards_'+stamp);root.mkdir(exist_ok=False)
 fixtures={};checks={}
 for label in ('corrupt_gate_copy','stale_origin_context','false_compiler_identity','dishonest_unchanged_flag'):
  p=root/label;p.mkdir();s=json.loads((parent/'summary.json').read_text());c=json.loads((parent/'source_context.json').read_text())
  if label=='stale_origin_context':
   c['reused_gate']['parent_context_sha256']='0'*64;s['reused_gate']=c['reused_gate']
  if label=='dishonest_unchanged_flag':s['gate_input_unchanged']=False
  (p/'summary.json').write_text(json.dumps(s));(p/'source_context.json').write_text(json.dumps(c))
  shutil.copy2(parent/'inputs.json',p/'inputs.json')
  # A deliberately truncated copy; never modify a real TD checkpoint.
  (p/'input_gate.db').write_bytes((parent/'input_gate.db').read_bytes()[:128])
  try:gate_reuse_audit(p,before,'0'*40 if label=='false_compiler_identity' else commit)
  except AssertionError:checks[label]='REJECTED'
  else:raise AssertionError('Forged gate lineage accepted: '+label)
  fixtures.update({f.relative_to(R).as_posix():sha(f) for f in p.iterdir()})
 result={'status':'GATE_REUSE_GUARDS_PASS','checks':checks,'accepted':accepted,'actual_parent':parent.relative_to(R).as_posix(),'actual_parent_summary_sha256':sha(parent/'summary.json'),'auditor_sha256':sha(R/'scripts/audit_stage1.py'),'producer_sha256':sha(Path(__file__)),'fixtures':fixtures,'scope':'Artificial forged copies only; not functional or board evidence'}
 report=R/'reports/stage1'/('gate_reuse_guards_'+stamp+'.json');report.write_text(json.dumps(result,indent=2)+'\n');print('STAGE1_GATE_REUSE_GUARDS_PASS',report.relative_to(R),checks)
if __name__=='__main__':main()
