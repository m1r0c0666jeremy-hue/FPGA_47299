"""Actual editor/reference equivalence, including all four eight-vertex areas."""
from pathlib import Path
import ast, hashlib, json, re
from refined_testlib import R, run

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    producer=R/'scripts/test_stage1_regions.py'
    tree=ast.parse(producer.read_text(encoding='utf-8'))
    main_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    assignment=next(n for n in main_node.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='src' for t in n.targets))
    bench=ast.literal_eval(assignment.value)
    reference=R/'build/stage1_valid_storage_20261024_0027/stage1_regions_reference.v'
    reference_hash=sha(reference)
    producer_hash=sha(producer)
    ports=[('nr',3),('nd',4),('revision',16),('vertices',672),('counts',16),('closed',4),('state',4),('completed',4),('occupied',4),('expected',3),('actual',3),('muted',1),('alarm',1),('trend',2),('distance',11),('dwell',20),('ee',4),('se',4),('busy',1),('live',1),('metrics_valid',1),('private_saved',672),('private_draft',168)]
    m=re.search(r'stage1_regions #\(\.CYCLES_PER_MS\(1000\)\) dut\((.*?)\);',bench,re.S)
    assert m
    args=[x.strip() for x in m[1].split(',')]
    assert args[-len(ports):]==[n for n,w in ports]
    args[-len(ports):]=[n+'_ref' for n,w in ports]
    extra='\n'.join('wire '+('' if w==1 else f'[{w-1}:0] ')+n+'_ref;' for n,w in ports)+'\n'
    extra+='stage1_regions_reference #(.CYCLES_PER_MS(1000)) reference_controller('+','.join(args)+');\n'
    status=[n for n,w in ports if n not in ('vertices','private_saved','private_draft')]
    extra+='wire [3:0] mask_ref;wire [23:0] pixel_ref,label_color_ref;wire label_ref,ready_ref,under_ref;wire [7:0] glyph_ref;wire [2:0] gx_ref;wire [3:0] gy_ref;\n'
    extra+="stage1_render #(.SPLIT_DRAFT(1)) reference_picture(clk,rst,geometry_commit,private_saved_ref,counts_ref,closed_ref,mode,11'd0,10'd0,3'd0,1'b0,state_ref,completed_ref,expected_ref,actual_ref,rx,ry,rde,mask_ref,pixel_ref,label_ref,glyph_ref,gx_ref,gy_ref,label_color_ref,ready_ref,under_ref,private_draft_ref,nr_ref,nd_ref!=0);\n"
    extra+='integer comparison_samples=0,valid_region,valid_vertex,full_frames=0,compare_row,compare_col;\n'
    extra+='task compare_full_frame;begin @(negedge clk);rde=0;rx=0;ry=624;geometry_commit=1;@(negedge clk);geometry_commit=0;repeat(10000)@(negedge clk);for(compare_row=0;compare_row<624;compare_row=compare_row+1)for(compare_col=0;compare_col<1650;compare_col=compare_col+1)begin @(negedge clk);rx=compare_col<1280?compare_col:0;ry=compare_row;rde=compare_col<1280;end @(negedge clk);rde=0;full_frames=full_frames+1;end endtask\n'
    extra+='always @(negedge clk)begin #2; if(rst)begin\n'
    extra+='if({'+','.join(status)+'}!=={'+','.join(n+'_ref' for n in status)+'})$fatal(1,"controller status differs sample %0d",comparison_samples);\n'
    extra+='for(valid_region=0;valid_region<nr;valid_region=valid_region+1)for(valid_vertex=0;valid_vertex<counts[valid_region*4+:4];valid_vertex=valid_vertex+1)begin\n'
    extra+='if(private_saved[valid_region*168+valid_vertex*21+:21]!==private_saved_ref[valid_region*168+valid_vertex*21+:21])$fatal(1,"saved coordinate differs");end\n'
    extra+='for(valid_vertex=0;valid_vertex<nd;valid_vertex=valid_vertex+1)if(private_draft[valid_vertex*21+:21]!==private_draft_ref[valid_vertex*21+:21])$fatal(1,"draft coordinate differs");\n'
    extra+='if({pmask,pcolor,lon,glyph,gx,gy,lcolor,rready,under}!=={mask_ref,pixel_ref,label_ref,glyph_ref,gx_ref,gy_ref,label_color_ref,ready_ref,under_ref})$fatal(1,"coupled displayed outputs differ sample %0d",comparison_samples);\n'
    extra+='comparison_samples=comparison_samples+1;end end\n'
    bench=bench[:m.end()]+extra+bench[m.end():]
    phase='@(negedge clk);rst=0;repeat(2)@(negedge clk);rst=1;mode=1;\n'
    octagon=[(100,100),(140,90),(180,100),(190,140),(180,180),(140,190),(100,180),(90,140)]
    for area in range(4):
        for x,y in octagon:
            phase+=f'record({x+300*area},{y});\n'
        phase+=f'if(nd!=8 || nr!={area})$fatal(1,"eight-point draft failed area {area}");\n'
        if area==0:
            phase+='record(140,140);if(nd!=8 || ee!=6)$fatal(1,"ninth vertex not rejected");\n'
        phase+=f'key(3);repeat(100000)@(negedge clk);if(nr!={area+1} || nd!=0 || counts[{4*area}+:4]!=8 || busy)$fatal(1,"full polygon save failed area {area} nr%0d nd%0d error%0d",nr,nd,ee);\n'
    phase+='record(1180,200);if(nr!=4 || nd!=0 || ee!=4)$fatal(1,"fifth area not rejected");\n'
    phase+='compare_full_frame();\n'
    phase+='@(negedge clk);rst=0;repeat(2)@(negedge clk);rst=1;\n'
    phase+='compare_full_frame();if(nr!=0 || nd!=0 || alarm || pmask!=0 || under)$fatal(1,"full storage reset left valid region");\n'
    phase+='$display("STAGE1_REGIONS_CAPACITY_PASS areas=4 points=32 ninth_vertex_rejected fifth_area_rejected reset_empty_frame samples=%0d full_frames=%0d",comparison_samples,full_frames);\n'
    needle='rst=0;@(negedge clk);if(nr!=0 || nd!=0 || alarm)$fatal(1,"reset did not clear");'
    assert bench.count(needle)==1
    bench=bench.replace(needle,phase+needle,1)
    names=['stage1_arith.v','stage1_point.v','stage1_segment.v','stage1_validate.v','stage1_sequence.v','stage1_regions.v','stage1_render.v']
    out=run('stage1_regions_capacity',bench,[R/'rtl/color_regions'/n for n in names]+[reference],timeout=1800)
    assert sha(reference)==reference_hash and sha(producer)==producer_hash
    record=R/'reports/refined/regression'/(out.name+'.json')
    obj=json.loads(record.read_text(encoding='utf-8'))
    obj['producer_inputs'][producer.relative_to(R).as_posix()]=producer_hash
    record.write_text(json.dumps(obj,indent=2),encoding='utf-8')

if __name__=='__main__':
    main()
