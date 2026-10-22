"""Private bit-width probe; no formal RTL/oracle edits or parallel TD."""
from pathlib import Path
import hashlib,json,math,random,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
from test_stage1_arith import BENCH
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
formal=json.loads((R/'build/stage1_place_20261023_032446/inputs.json').read_text());assert all(sha(R/n)==h for n,h in formal.items())
reference=R/'reports/stage1/software_current_20261023_0002.json';old=json.loads(reference.read_text());checks={}
def execute(label,source,modules,fixtures,producers):
 out=run('private_bounded_point_'+label,source,modules,timeout=300);record=R/'reports/refined/regression'/(out.name+'.json');d=json.loads(record.read_text());assert d['exit_code']==0
 checks[label]={'record':record.relative_to(R).as_posix(),'record_sha256':sha(record),'log_sha256':sha(record.with_suffix('.log')),'bench':(out/'tb.sv').relative_to(R).as_posix(),'bench_sha256':sha(out/'tb.sv'),'inputs':{n.replace('\\','/'):h for n,h in d['inputs'].items()},'fixtures':fixtures,'producers':producers}
for mw,dw,nw,sw in [(12,48,48,24),(21,23,48,24),(24,14,48,24),(21,23,40,12)]:
 if nw==48:path=R/f'build/stage1_arith_vectors/math_{mw}_{dw}.hex'
 else:
  rng=random.Random(102304);vals=[];bounds=[0,1,-1,2,-2,-(1<<(mw-1)),(1<<(mw-1))-1]
  for a in bounds:
   for b in bounds:vals.append((0,a,b,a*b))
  for _ in range(1200):
   a=rng.randrange(-(1<<(mw-1)),1<<(mw-1));b=rng.randrange(-(1<<(mw-1)),1<<(mw-1));vals.append((0,a,b,a*b))
  for i in range(400):
   a=((1<<nw)-1) if i==1 else rng.getrandbits(nw);b=0 if i==0 else rng.randrange(1,1<<dw);vals.append((1,a,b,(1<<48)-1 if b==0 else a//b))
   a=((1<<(sw*2))-1) if i==1 else rng.getrandbits(sw*2);vals.append((2,a,0,math.isqrt(a)))
  path=O/'math_21_23_40_12.hex';mask=(1<<48)-1
  with path.open('x',encoding='utf8') as f:f.write('\n'.join(f'{op:x}{a&mask:012x}{b&mask:012x}{v&mask:012x}' for op,a,b,v in vals)+'\n')
 assert len(path.read_text().splitlines())==2049
 src=BENCH.replace('WIDTH',str(mw)).replace('DIVISOR',str(dw)).replace('COUNT','2049').replace('FILE',path.as_posix())
 src=src.replace(f'.MW({mw}),.DW({dw})',f'.MW({mw}),.DW({dw}),.NW({nw}),.SW({sw})')
 src=src.replace('(b==0?1:48):24',f'(b==0?1:{nw}):{sw}')
 execute(f'math_{mw}_{dw}_{nw}_{sw}',src,[O/'stage1_arith.v'],{path.relative_to(R).as_posix():sha(path)},{'scripts/test_stage1_arith.py':sha(R/'scripts/test_stage1_arith.py')})
for label in ('stage1_point','stage1_validate','stage1_regions'):
 e=old['regression'][label];assert all(sha(R/n)==h for group in (e['inputs'],e['fixture_inputs'],e['producer_inputs']) for n,h in group.items())
 benches=[R/n for n in e['fixture_inputs'] if n.endswith('/tb.sv')];assert len(benches)==1
 modules=[O/Path(n).name if n in ('rtl/color_regions/stage1_arith.v','rtl/color_regions/stage1_point.v') else R/n for n in e['inputs']]
 execute(label,benches[0].read_text(),modules,e['fixture_inputs'],e['producer_inputs'])
 assert all(sha(R/n)==h for n,h in formal.items())
result={'status':'PRIVATE_BOUNDED_WIDTH_VALIDATED_NOT_ADOPTED','scope':'No resource or physical credit; formal source unchanged','candidate_inputs':{(O/n).relative_to(R).as_posix():sha(O/n) for n in ('stage1_arith.v','stage1_point.v')},'checks':checks,'reference':reference.relative_to(R).as_posix(),'reference_sha256':sha(reference),'producer_sha256':sha(Path(__file__)),'unchanged_formal_inputs':formal}
with (O/'validation.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
print('PRIVATE_BOUNDED_POINT_PASS checks',len(checks),'NOT ADOPTED',flush=True)
