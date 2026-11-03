"""Additional private renderer multiplier bound; current RTL/TD remain unchanged."""
from pathlib import Path
import hashlib,json,math,random,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
from test_stage1_arith import BENCH
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=(R/'rtl/color_regions/stage1_render.v').read_text();needle='stage1_arith #(.DW(14)) line_alu';assert source.count(needle)==1
candidate=O/'stage1_render_mw14.v'
with candidate.open('x',encoding='utf8') as f:f.write(source.replace(needle,'stage1_arith #(.MW(14),.DW(14)) line_alu'))
reference=R/'reports/stage1/software_current_20261023_0002.json';old=json.loads(reference.read_text());checks={}
base=json.loads((O/'validation.json').read_text());formal=base['unchanged_formal_inputs'];assert all(sha(R/n)==h for n,h in formal.items())
assert all(sha(R/n)==h for n,h in base['candidate_inputs'].items())
def execute(label,bench,modules,fixtures,producers):
 out=run('private_bounded_render_'+label,bench,modules,timeout=1800);record=R/'reports/refined/regression'/(out.name+'.json');data=json.loads(record.read_text());assert data['exit_code']==0
 checks[label]={'record':record.relative_to(R).as_posix(),'record_sha256':sha(record),'log_sha256':sha(record.with_suffix('.log')),'bench':(out/'tb.sv').relative_to(R).as_posix(),'bench_sha256':sha(out/'tb.sv'),'inputs':{n.replace('\\','/'):h for n,h in data['inputs'].items()},'fixtures':fixtures,'producers':producers}
 with (O/'render_progress.json').open('w',encoding='utf8') as f:json.dump({'scope':'PRIVATE NOT ADOPTED','checks':checks},f,indent=2)
rng=random.Random(102314);vals=[];mw=14;dw=14;bounds=[0,1,-1,2,-2,-8192,8191]
for a in bounds:
 for b in bounds:vals.append((0,a,b,a*b))
for _ in range(1200):
 a=rng.randrange(-8192,8192);b=rng.randrange(-8192,8192);vals.append((0,a,b,a*b))
for i in range(400):
 a=rng.getrandbits(48);b=0 if i==0 else rng.randrange(1,1<<dw);vals.append((1,a,b,(1<<48)-1 if b==0 else a//b));vals.append((2,a,0,math.isqrt(a)))
path=O/'math_14_14.hex';mask=(1<<48)-1
with path.open('x',encoding='utf8') as f:f.write('\n'.join(f'{op:x}{a&mask:012x}{b&mask:012x}{v&mask:012x}' for op,a,b,v in vals)+'\n')
bench=BENCH.replace('WIDTH','14').replace('DIVISOR','14').replace('COUNT','2049').replace('FILE',path.as_posix())
execute('math_14_14',bench,[O/'stage1_arith.v'],{path.relative_to(R).as_posix():sha(path)},{'scripts/test_stage1_arith.py':sha(R/'scripts/test_stage1_arith.py')})
for label in ('stage1_render_guards','stage1_regions','stage1_render_14_624','stage1_overlay'):
 e=old['regression'][label];assert all(sha(R/n)==h for group in (e['inputs'],e['fixture_inputs'],e['producer_inputs']) for n,h in group.items())
 benches=[R/n for n in e['fixture_inputs'] if n.endswith('/tb.sv')];assert len(benches)==1
 modules=[candidate if n=='rtl/color_regions/stage1_render.v' else O/Path(n).name if n in ('rtl/color_regions/stage1_arith.v','rtl/color_regions/stage1_point.v') else R/n for n in e['inputs']]
 execute(label,benches[0].read_text(),modules,e['fixture_inputs'],e['producer_inputs'])
 assert all(sha(R/n)==h for n,h in formal.items())
result={'status':'PRIVATE_RENDER_MW14_VALIDATED_NOT_ADOPTED','scope':'No resource or final physical credit','checks':checks,'candidate_sha256':sha(candidate),'other_candidates':base['candidate_inputs'],'reference':reference.relative_to(R).as_posix(),'reference_sha256':sha(reference),'producer_sha256':sha(Path(__file__)),'unchanged_formal_inputs':formal}
with (O/'render_validation.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
print('PRIVATE_BOUNDED_RENDER_PASS five extra checks; NOT ADOPTED',flush=True)
