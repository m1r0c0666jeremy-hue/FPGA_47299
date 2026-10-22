"""Private default-parameter cycle equivalence with asynchronous reset interruptions."""
from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
oldproof=R/'build/stage1_resetfree_arith_ungated_20261023_0101/validation.json';old=json.loads(oldproof.read_text());checks={}
baseline=R/'build/stage1_resetfree_arith_ungated_20261023_0101/baseline_arith.v'
assert baseline.read_text().replace('module baseline_arith #','module stage1_arith #',1)==(R/'rtl/color_regions/stage1_arith.v').read_text()
formal=json.loads((R/'build/stage1_place_20261023_032446/inputs.json').read_text());assert all(sha(R/n)==h for n,h in formal.items())
for mw,dw in ((12,48),(21,23),(24,14)):
 e=old['checks'][f'equivalence_{mw}_{dw}'];assert sha(R/e['bench'])==e['bench_sha256']
 bench=(R/e['bench']).read_text().replace('PRIVATE_RESETFREE_EQ_PASS','PRIVATE_BOUNDED_DEFAULT_EQ_PASS')
 out=run(f'private_bounded_default_{mw}_{dw}',bench,[baseline,O/'stage1_arith.v'],timeout=300)
 record=R/'reports/refined/regression'/(out.name+'.json');d=json.loads(record.read_text());assert d['exit_code']==0
 checks[f'{mw}_{dw}']={'record':record.relative_to(R).as_posix(),'record_sha256':sha(record),'log_sha256':sha(record.with_suffix('.log')),'bench':(out/'tb.sv').relative_to(R).as_posix(),'bench_sha256':sha(out/'tb.sv'),'inputs':{n.replace('\\','/'):h for n,h in d['inputs'].items()},'reference_bench':e['bench'],'reference_bench_sha256':e['bench_sha256']}
assert all(sha(R/n)==h for n,h in formal.items())
result={'status':'PRIVATE_DEFAULT_CYCLES_EQUIVALENT_NOT_ADOPTED','checks':checks,'candidate_sha256':sha(O/'stage1_arith.v'),'producer_sha256':sha(Path(__file__)),'unchanged_formal_inputs':formal}
with (O/'equivalence_validation.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
print('PRIVATE_BOUNDED_DEFAULT_EQ_ALL_PASS; 3 widths; NOT ADOPTED',flush=True)
