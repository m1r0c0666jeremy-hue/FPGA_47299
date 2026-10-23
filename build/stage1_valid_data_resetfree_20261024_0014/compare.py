"""Compare control, valid coordinates, edits, and reset interruptions against the formal controller."""
from pathlib import Path
import hashlib,json,re,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reference=R/'reports/stage1/software_current_20261023_203938.json';e=json.loads(reference.read_text(encoding='utf-8'))['regression']['stage1_regions']
assert all(sha(R/n)==v for g in ('inputs','fixture_inputs','producer_inputs') for n,v in e[g].items())
bench_path=next(R/n for n in e['fixture_inputs'] if n.endswith('/tb.sv'));bench=bench_path.read_text(encoding='utf-8')
ports=[('nr',3),('nd',4),('revision',16),('vertices',672),('counts',16),('closed',4),('state',4),('completed',4),('occupied',4),('expected',3),('actual',3),('muted',1),('alarm',1),('trend',2),('distance',11),('dwell',20),('ee',4),('se',4),('busy',1),('live',1),('metrics_valid',1),('private_saved',672),('private_draft',168)]
m=re.search(r'stage1_regions #\(\.CYCLES_PER_MS\(1000\)\) dut\((.*?)\);',bench,re.S);assert m
args=[x.strip() for x in m[1].split(',')];assert args[-len(ports):]==[n for n,w in ports]
args[-len(ports):]=[n+'_ref' for n,w in ports]
extra='\n'.join('wire '+('' if w==1 else f'[{w-1}:0] ')+n+'_ref;' for n,w in ports)+'\n'
extra+='stage1_regions_reference #(.CYCLES_PER_MS(1000)) reference_controller('+','.join(args)+');\n'
status=[n for n,w in ports if n not in ('vertices','private_saved','private_draft')]
extra+='integer comparison_samples=0,reset_round,valid_region,valid_vertex;\n'
extra+='always @(negedge clk)begin #2; if(rst)begin\n'
extra+='if({'+','.join(status)+'}!=={'+','.join(n+'_ref' for n in status)+'})$fatal(1,"controller status differs sample %0d",comparison_samples);\n'
extra+='for(valid_region=0;valid_region<nr;valid_region=valid_region+1)for(valid_vertex=0;valid_vertex<counts[valid_region*4+:4];valid_vertex=valid_vertex+1)begin\n'
extra+='if(private_saved[valid_region*168+valid_vertex*21+:21]!==private_saved_ref[valid_region*168+valid_vertex*21+:21])$fatal(1,"saved coordinate differs");end\n'
extra+='for(valid_vertex=0;valid_vertex<nd;valid_vertex=valid_vertex+1)if(private_draft[valid_vertex*21+:21]!==private_draft_ref[valid_vertex*21+:21])$fatal(1,"draft coordinate differs");\n'
extra+='comparison_samples=comparison_samples+1;end end\n'
bench=bench[:m.end()]+extra+bench[m.end():]
anchor='repeat(3)@(negedge clk);rst=1;';assert bench.count(anchor)==1
stress=anchor+'\nfor(reset_round=0;reset_round<4;reset_round=reset_round+1)begin\nrecord(100,100);record(300,100);record(200,250);\n@(negedge clk);c3=1;@(negedge clk);c3=0;repeat(reset_round+4)@(negedge clk);rst=0;repeat(2)@(negedge clk);rst=1;end\n'
stress+='for(reset_round=0;reset_round<4;reset_round=reset_round+1)begin\nframe(120,120);down=1;@(negedge clk);down=0;repeat(reset_round)@(negedge clk);rst=0;repeat(2)@(negedge clk);rst=1;end\n'
stress+='@(negedge clk);rst=0;repeat(2)@(negedge clk);rst=1;\n'
bench=bench.replace(anchor,stress,1)
bench=bench.replace('$finish;end', '$display("PRIVATE_VALID_DATA_CONTROL_EQUIVALENCE_PASS samples=%0d reset_interruptions=9",comparison_samples);$finish;end',1)
mods=[O/'stage1_regions.v' if n=='rtl/color_regions/stage1_regions.v' else O/'stage1_render.v' if n=='rtl/color_regions/stage1_render.v' else R/n for n in e['inputs']]
mods.append(O/'stage1_regions_reference.v')
out=run('private_valid_data_control_equivalence',bench,mods,timeout=1800)
record=R/'reports/refined/regression'/(out.name+'.json');obj=json.loads(record.read_text());assert obj['exit_code']==0
result=dict(status='PRIVATE_CONTROL_EQUIVALENCE_PASSED_NOT_ADOPTED',record=record.relative_to(R).as_posix(),record_sha256=sha(record),log_sha256=sha(record.with_suffix('.log')),bench=(out/'tb.sv').relative_to(R).as_posix(),bench_sha256=sha(out/'tb.sv'),inputs=obj['inputs'],fixtures=e['fixture_inputs'],producers=e['producer_inputs'],producer_sha256=sha(Path(__file__)),reference_sha256=sha(reference))
with (O/'equivalence_validation.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
