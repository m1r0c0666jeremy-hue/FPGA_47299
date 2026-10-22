"""Private fixed-word edge transfer; formal build inputs remain unchanged."""
from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reference=R/'reports/stage1/software_current_20261023_0002.json'
proof=json.loads(reference.read_text());formal=json.loads((R/'build/stage1_place_20261023_022120/inputs.json').read_text())
assert all(sha(R/n)==h for n,h in formal.items())
source=(R/'rtl/color_regions/stage1_render.v').read_text()
def edit(a,b):
 global source
 assert source.count(a)==1,(a,source.count(a))
 source=source.replace(a,b)
edit("edge_mem[{edge_id,3'b000}+field[2:0]]<=work[field*16+:16];","edge_mem[{edge_id,3'b000}+field[2:0]]<=work[15:0];")
edit("if(field!=0)work[(field-1'b1)*16+:16]<=edge_q;","if(field!=0)work<={edge_q,work[127:16]};")
edit('WRITE_EDGE:begin\n if(field==7)',"WRITE_EDGE:begin\n work<={16'd0,work[127:16]};\n if(field==7)")
candidate=O/'stage1_render.v'
with candidate.open('x',encoding='utf8',newline='\n') as f:f.write(source)
checks={}
for label,marker in [('stage1_render_guards','STAGE1_RENDER_GUARDS_PASS'),('stage1_regions','STAGE1_EDIT_RENDER_PASS point_pixels=134400'),('stage1_render_14_624','STAGE1_RENDER_PASS cases=14 pixels=11182080'),('stage1_overlay','STAGE1_OVERLAY_PASS cases=8 pixels=6389760')]:
 entry=proof['regression'][label]
 assert all(sha(R/n)==h for g in (entry['inputs'],entry['fixture_inputs'],entry['producer_inputs']) for n,h in g.items())
 benches=[R/n for n in entry['fixture_inputs'] if n.endswith('/tb.sv')];assert len(benches)==1
 modules=[candidate if n=='rtl/color_regions/stage1_render.v' else R/n for n in entry['inputs']]
 out=run('private_work_shift_'+label,benches[0].read_text(),modules,timeout=1800)
 record=R/'reports/refined/regression'/(out.name+'.json');log=record.with_suffix('.log');assert marker in log.read_text()
 data=json.loads(record.read_text());inputs={n.replace('\\','/'):h for n,h in data['inputs'].items()}
 checks[label]={'record':record.relative_to(R).as_posix(),'record_sha256':sha(record),'log_sha256':sha(log),'bench':(out/'tb.sv').relative_to(R).as_posix(),'bench_sha256':sha(out/'tb.sv'),'inputs':inputs,'reference_fixtures':entry['fixture_inputs'],'reference_producers':entry['producer_inputs']}
 assert all(sha(R/n)==h for n,h in formal.items())
 with (O/'progress.json').open('w',encoding='utf8') as f:json.dump({'scope':'PRIVATE NOT ADOPTED','checks':checks},f,indent=2)
result={'scope':'PRIVATE NOT ADOPTED; no resource or final physical result','checks':checks,'reference':reference.relative_to(R).as_posix(),'reference_sha256':sha(reference),'candidate_sha256':sha(candidate),'producer_sha256':sha(Path(__file__)),'unchanged_formal_inputs':formal}
with (O/'validation.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
print('PRIVATE_WORK_SHIFT_ALL_PASS; NOT ADOPTED',flush=True)
