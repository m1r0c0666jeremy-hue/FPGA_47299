"""Full independent geometry oracle plus pixel/label equivalence to pre-change RTL."""
from pathlib import Path
from refined_testlib import R
task=R/(R/'build/current_display_shared_path.txt').read_text(encoding='utf-8')
ref=task/'reference/stage1_render.v'
assert ref.is_file()
s=(R/'scripts/test_stage1_render.py').read_text(encoding='utf-8')
s=s.replace('module tb;', '''module tb;
wire [3:0] ref_mask;wire [23:0] ref_color,ref_label_color;wire ref_label_on,ref_ready,ref_underrun;
wire [7:0] ref_glyph;wire [2:0] ref_gx;wire [3:0] ref_gy;''')
s=s.replace('stage1_render #(.SPLIT_DRAFT(1)) dut(', 'stage1_render #(.SPLIT_DRAFT(1),.LINE_CACHE(1)) dut(')
marker="split_draft,{1'b0,split_region},1'b1);"
assert marker in s
s=s.replace(marker,marker+'''
reference_stage1_render #(.SPLIT_DRAFT(1)) original(clk,rst,commit,split_saved,counts,closed,mode,x0,y0,zoom,rotate,state,completed,target,actual,
x,y,de,ref_mask,ref_color,ref_label_on,ref_glyph,ref_gx,ref_gy,ref_label_color,ref_ready,ref_underrun,split_draft,{1'b0,split_region},1'b1);''')
marker='if(de)begin want='
assert marker in s
s=s.replace(marker,'''if(de && (mask!==ref_mask || color!==ref_color || label_on!==ref_label_on ||
 (label_on && {glyph,gx,gy,label_color}!=={ref_glyph,ref_gx,ref_gy,ref_label_color})))
 $fatal(1,"render equivalence c%0d xy%0d/%0d",c,h,yy);
if(de)begin want=''')
s=s.replace("[R/'rtl/color_regions/stage1_render.v']", "[R/'rtl/color_regions/stage1_render.v',R/"+repr(ref.relative_to(R).as_posix())+"]")
s=s.replace("f'stage1_render_{len(cases)}_{a.rows}'", "'stage1_render_equivalence'")
s=s.replace('STAGE1_RENDER_PASS cases=', 'STAGE1_RENDER_EQUIVALENCE_PASS cases=')
exec(compile(s,str(R/'scripts/test_stage1_render.py'),'exec'),{'__name__':'__main__','__file__':__file__})
