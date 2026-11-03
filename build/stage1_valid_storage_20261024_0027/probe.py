"""Seal current display proofs and the new actual controller/delete/reuse proof."""
from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent;R=O.parents[1];A=R/'build/stage1_valid_data_resetfree_20261024_0014'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=json.loads((A/'validation.json').read_text());eq=json.loads((O/'equivalence_validation.json').read_text());reference=R/original['reference']
assert sha(reference)==original['reference_sha256'];assert sha(O/'compare.py')==eq['producer_sha256']
assert (O/'stage1_regions_reference.v').read_text()==(R/'rtl/color_regions/stage1_regions.v').read_text().replace('module stage1_regions #','module stage1_regions_reference #',1)
assert sha(O/'stage1_render.v')==original['candidate_sha256']
checks={}
for k in ('stage1_render_guards','stage1_render_14_624','stage1_overlay'):
 e=original['checks'][k]
 assert not any(n.endswith('stage1_regions.v') for n in e['inputs'])
 assert sha(R/e['record'])==e['record_sha256'] and sha((R/e['record']).with_suffix('.log'))==e['log_sha256']
 assert all(sha(R/n)==v for g in ('inputs','fixtures','producers') for n,v in e[g].items())
 assert sha(R/e['bench'])==e['bench_sha256'];checks[k]=e
assert all(sha(R/n)==v for n,v in eq['inputs'].items())
assert sha(R/eq['record'])==eq['record_sha256'] and sha((R/eq['record']).with_suffix('.log'))==eq['log_sha256']
log=(R/eq['record']).with_suffix('.log').read_text();assert 'PRIVATE_VALID_DATA_CONTROL_EQUIVALENCE_PASS' in log and 'reset_interruptions=9 full_frames=3' in log
checks['stage1_regions']={k:eq[k] for k in ('record','record_sha256','log_sha256','bench','bench_sha256','fixtures','producers')}
checks['stage1_regions']['inputs']={n.replace('\\','/'):v for n,v in eq['inputs'].items()}
assert all(sha(R/n)==v for n,v in original['unchanged_formal_inputs'].items())
obj=dict(status='PRIVATE_VALID_STORAGE_VALIDATED_NOT_ADOPTED',scope='Reset count/control preserved; never clear invalid coordinate payload; no formal resource or route credit',candidate_sha256=sha(O/'stage1_render.v'),regions_candidate_sha256=sha(O/'stage1_regions.v'),reference=original['reference'],reference_sha256=sha(reference),producer_sha256=sha(Path(__file__)),unchanged_formal_inputs=original['unchanged_formal_inputs'],checks=checks,reused_display_proof_sha256=sha(A/'validation.json'),equivalence_sha256=sha(O/'equivalence_validation.json'))
with (O/'validation.json').open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2)
print('PRIVATE_VALID_STORAGE_SEALED_PASS')
