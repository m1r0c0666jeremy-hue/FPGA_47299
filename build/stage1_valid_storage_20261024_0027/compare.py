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
extra+='wire [3:0] mask_ref;wire [23:0] pixel_ref,label_color_ref;wire label_ref,ready_ref,under_ref;wire [7:0] glyph_ref;wire [2:0] gx_ref;wire [3:0] gy_ref;\n'
extra+='stage1_render #(.SPLIT_DRAFT(1)) reference_picture(clk,rst,geometry_commit,private_saved_ref,counts_ref,closed_ref,mode,11\'d0,10\'d0,3\'d0,1\'b0,state_ref,completed_ref,expected_ref,actual_ref,rx,ry,rde,mask_ref,pixel_ref,label_ref,glyph_ref,gx_ref,gy_ref,label_color_ref,ready_ref,under_ref,private_draft_ref,nr_ref,nd_ref!=0);\n'
extra+='integer comparison_samples=0,reset_round,valid_region,valid_vertex,full_frames=0,compare_row,compare_col;\n'
extra+='task compare_full_frame;begin @(negedge clk);rde=0;rx=0;ry=624;geometry_commit=1;@(negedge clk);geometry_commit=0;repeat(10000)@(negedge clk);for(compare_row=0;compare_row<624;compare_row=compare_row+1)for(compare_col=0;compare_col<1650;compare_col=compare_col+1)begin @(negedge clk);rx=compare_col<1280?compare_col:0;ry=compare_row;rde=compare_col<1280;end @(negedge clk);rde=0;full_frames=full_frames+1;end endtask\n' 
extra+='always @(negedge clk)begin #2; if(rst)begin\n'
extra+='if({'+','.join(status)+'}!=={'+','.join(n+'_ref' for n in status)+'})$fatal(1,"controller status differs sample %0d",comparison_samples);\n'
extra+='for(valid_region=0;valid_region<nr;valid_region=valid_region+1)for(valid_vertex=0;valid_vertex<counts[valid_region*4+:4];valid_vertex=valid_vertex+1)begin\n'
extra+='if(private_saved[valid_region*168+valid_vertex*21+:21]!==private_saved_ref[valid_region*168+valid_vertex*21+:21])$fatal(1,"saved coordinate differs");end\n'
extra+='for(valid_vertex=0;valid_vertex<nd;valid_vertex=valid_vertex+1)if(private_draft[valid_vertex*21+:21]!==private_draft_ref[valid_vertex*21+:21])$fatal(1,"draft coordinate differs");\n'
extra+='if({pmask,pcolor,lon,glyph,gx,gy,lcolor,rready,under}!=={mask_ref,pixel_ref,label_ref,glyph_ref,gx_ref,gy_ref,label_color_ref,ready_ref,under_ref})$fatal(1,"coupled displayed outputs differ sample %0d",comparison_samples);\n'
extra+='comparison_samples=comparison_samples+1;end end\n'
bench=bench[:m.end()]+extra+bench[m.end():]
anchor='repeat(3)@(negedge clk);rst=1;';assert bench.count(anchor)==1
stress=anchor+'\nfor(reset_round=0;reset_round<4;reset_round=reset_round+1)begin\nrecord(100,100);record(300,100);record(200,250);\n@(negedge clk);c3=1;@(negedge clk);c3=0;repeat(reset_round+4)@(negedge clk);rst=0;repeat(2)@(negedge clk);rst=1;end\n'
stress+='for(reset_round=0;reset_round<4;reset_round=reset_round+1)begin\nframe(120,120);down=1;@(negedge clk);down=0;repeat(reset_round)@(negedge clk);rst=0;repeat(2)@(negedge clk);rst=1;end\n'
stress+='@(negedge clk);rst=0;repeat(2)@(negedge clk);rst=1;\n'
bench=bench.replace(anchor,stress,1)
bench=bench.replace('if(nr!=1 || closed!=1)$fatal(1,"delete last region");','if(nr!=1 || closed!=1)$fatal(1,"delete last region");compare_full_frame();record(850,100);compare_full_frame();record(1000,100);record(920,220);key(3);compare_full_frame();key(4);if(nr!=1 || nd!=0)$fatal(1,"reuse then delete failed");',1)
bench=bench.replace('$finish;end', '$display("PRIVATE_VALID_DATA_CONTROL_EQUIVALENCE_PASS samples=%0d reset_interruptions=9 full_frames=%0d",comparison_samples,full_frames);$finish;end',1)
mods=[O/'stage1_regions.v' if n=='rtl/color_regions/stage1_regions.v' else O/'stage1_render.v' if n=='rtl/color_regions/stage1_render.v' else R/n for n in e['inputs']]
mods.append(O/'stage1_regions_reference.v')
out=run('private_valid_storage_equivalence',bench,mods,timeout=1800)
record=R/'reports/refined/regression'/(out.name+'.json');obj=json.loads(record.read_text());assert obj['exit_code']==0
result=dict(status='PRIVATE_CONTROL_EQUIVALENCE_PASSED_NOT_ADOPTED',record=record.relative_to(R).as_posix(),record_sha256=sha(record),log_sha256=sha(record.with_suffix('.log')),bench=(out/'tb.sv').relative_to(R).as_posix(),bench_sha256=sha(out/'tb.sv'),inputs=obj['inputs'],fixtures=e['fixture_inputs'],producers=e['producer_inputs'],producer_sha256=sha(Path(__file__)),reference_sha256=sha(reference))
with (O/'equivalence_validation.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
