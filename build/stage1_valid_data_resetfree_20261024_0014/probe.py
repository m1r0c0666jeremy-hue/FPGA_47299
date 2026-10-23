"""Private data-reset proof; no formal edits or gate builds while TD is active."""
from pathlib import Path
import json,hashlib,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reference=R/'reports/stage1/software_current_20261023_203938.json';old=json.loads(reference.read_text(encoding='utf8'));assert old['passed']==old['required']==110
formal=json.loads((R/'build/stage1_place_20261023_200045/inputs.json').read_text());assert all(sha(R/n)==h for n,h in formal.items())
checks={};candidate=O/'stage1_render.v'
for label in ('stage1_render_guards','stage1_regions','stage1_render_14_624','stage1_overlay'):
 e=old['regression'][label]
 assert all(sha(R/n)==h for g in ('inputs','fixture_inputs','producer_inputs') for n,h in e[g].items())
 benches=[R/n for n in e['fixture_inputs'] if n.endswith('/tb.sv')];assert len(benches)==1
 modules=[O/'stage1_regions.v' if n=='rtl/color_regions/stage1_regions.v' else candidate if n=='rtl/color_regions/stage1_render.v' else R/n for n in e['inputs']]
 out=run('private_valid_data_resetfree_'+label,benches[0].read_text(encoding='utf8'),modules,timeout=1800)
 record=R/'reports/refined/regression'/(out.name+'.json');d=json.loads(record.read_text());assert d['exit_code']==0
 checks[label]=dict(record=record.relative_to(R).as_posix(),record_sha256=sha(record),log_sha256=sha(record.with_suffix('.log')),inputs={n.replace('\\','/'):h for n,h in d['inputs'].items()},bench=(out/'tb.sv').relative_to(R).as_posix(),bench_sha256=sha(out/'tb.sv'),fixtures=e['fixture_inputs'],producers=e['producer_inputs'])
 (O/'progress.json').write_text(json.dumps(dict(scope='PRIVATE NOT ADOPTED; no resource credit',checks=checks),indent=2),encoding='utf8')
 assert all(sha(R/n)==h for n,h in formal.items())
result=dict(status='PRIVATE_VALID_DATA_RESETFREE_VALIDATED_NOT_ADOPTED',scope='No resource/physical credit; original control reset unchanged',candidate_sha256=sha(candidate),regions_candidate_sha256=sha(O/'stage1_regions.v'),reference=reference.relative_to(R).as_posix(),reference_sha256=sha(reference),producer_sha256=sha(Path(__file__)),unchanged_formal_inputs=formal,checks=checks)
with (O/'validation.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
print('PRIVATE_VALID_DATA_RESETFREE_FOUR_REAL_BENCH_PASS',flush=True)
