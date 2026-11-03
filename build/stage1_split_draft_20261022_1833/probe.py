"""Private draft selection after frame snapshot; do not touch formal sources or TD."""
from pathlib import Path
import json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
from audit_stage1 import sha


def edit(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)


def write(name,s):
    with (O/name).open('x',encoding='utf-8') as f:f.write(s)


def manager(s):
    s=edit(s,'output wire busy,tip_live,metrics_valid);',
           'output wire busy,tip_live,metrics_valid,output wire [671:0] saved_vertices,output wire [167:0] draft_vertices);')
    return edit(s,'reg [671:0] vertices;reg [15:0] counts;reg [167:0] draft;',
                'reg [671:0] vertices;reg [15:0] counts;reg [167:0] draft;\n assign saved_vertices=vertices;assign draft_vertices=draft;')


write('stage1_regions.v',manager((R/'rtl/color_regions/stage1_regions.v').read_text()))
write('stage1_regions_shared.v',manager((R/'build/stage1_shared_vertex_20261022/stage1_regions.v').read_text()))
s=(R/'rtl/color_regions/stage1_render.v').read_text()
s=edit(s,'module stage1_render(', 'module stage1_render #(parameter SPLIT_DRAFT=0)(')
s=edit(s,'output reg ready,output reg underrun);',
       'output reg ready,output reg underrun,input wire [167:0] draft_vertices,input wire [2:0] draft_region,input wire draft_visible);')
s=edit(s,'reg [671:0] fv;','reg [167:0] fd;reg [1:0] fd_region;reg fd_visible;\n reg [671:0] fv;')
reader='''function [20:0] draft_at;input [167:0] data;input [3:0] index;begin case(index[2:0])
'''+''.join(f"3'd{i}:draft_at=data[{i*21}+:21];\n" for i in range(8))+'''endcase
if(index[3])draft_at=0;end endfunction
'''
s=edit(s,'wire [20:0] map_point=vertex_at(fv,region_id,field[1]?ni:vi);',
       reader+' wire [20:0] map_point=SPLIT_DRAFT && fd_visible && region_id==fd_region?draft_at(fd,field[1]?ni:vi):vertex_at(fv,region_id,field[1]?ni:vi);')
s=edit(s,'field<=0;fv<=0;',"field<=0;fd<=0;fd_region<=0;fd_visible<=0;fv<=0;")
s=edit(s,'fv<=vertices;fc<=counts;',
       'fv<=vertices;fd<=draft_vertices;fd_region<=draft_region[1:0];fd_visible<=draft_visible && draft_region<4;fc<=counts;')
write('stage1_render.v',s)

# This OSD adapter exists only for replaying the saved RGB oracle. Real adoption
# would connect the editor's saved/draft outputs through the maintained generator.
s=(R/'rtl/color_regions/stage1_osd.v').read_text()
decl='''wire [1:0] private_split=I_rotate?2'd3:2'd1;
 wire [167:0] private_draft=I_region_vertices>>(private_split*168);
 wire [671:0] private_mask={{504{1'b0}},{168{1'b1}}}<<(private_split*168);
 wire [671:0] private_saved=I_region_vertices & ~private_mask;
 '''
s=edit(s,'stage1_render region_render(I_clk,I_rst_n,I_geometry_commit,I_region_vertices,',
       decl+'stage1_render #(.SPLIT_DRAFT(1)) region_render(I_clk,I_rst_n,I_geometry_commit,private_saved,')
s=edit(s,'region_label_color,region_ready,region_underrun);',
       "region_label_color,region_ready,region_underrun,private_draft,{1'b0,private_split},1'b1);")
write('stage1_osd.v',s)

proof=json.loads((R/'reports/stage1/software_current_20261022_1545.json').read_text())


def bench(name):
    e=proof['regression'][name]
    assert all(sha(R/n)==h for n,h in e['fixture_inputs'].items())
    paths=[R/n for n in e['fixture_inputs'] if n.endswith('/tb.sv')]
    assert len(paths)==1
    return paths[0].read_text()


source=bench('stage1_regions')
source=edit(source,'stage1_regions #', 'wire [671:0] private_saved;wire [167:0] private_draft;\nstage1_regions #')
source=edit(source,'muted,alarm,trend,distance,dwell,ee,se,busy,live,metrics_valid);',
            'muted,alarm,trend,distance,dwell,ee,se,busy,live,metrics_valid,private_saved,private_draft);')
mods=[O/'stage1_regions.v']+[R/'rtl/color_regions'/(n+'.v') for n in ('stage1_arith','stage1_point','stage1_segment','stage1_validate','stage1_sequence')]
run('private_split_draft_regions',source,mods,timeout=300)

source=bench('stage1_render_14_624')
context_line=next(line for line in source.splitlines() if line.startswith('reg [732:0] contexts'))
source=edit(source,context_line+'\n','')
declarations=context_line+'''\nwire [1:0] private_split=c[1:0];
wire [167:0] private_draft=vertices>>(private_split*168);
wire [671:0] private_mask={{504{1'b0}},{168{1'b1}}}<<(private_split*168);
wire [671:0] private_saved=vertices & ~private_mask;
'''
source=edit(source,'stage1_render dut(clk,rst,commit,vertices,',
            declarations+'stage1_render #(.SPLIT_DRAFT(1)) dut(clk,rst,commit,private_saved,')
source=edit(source,'x,y,de,mask,color,label_on,glyph,gx,gy,label_color,ready,underrun);',
            "x,y,de,mask,color,label_on,glyph,gx,gy,label_color,ready,underrun,private_draft,{1'b0,private_split},1'b1);")
run('private_split_draft_render',source,[O/'stage1_render.v',R/'rtl/color_regions/stage1_arith.v'],timeout=1800)

names=('stage1_ui_formatter','stage1_ui_text','refined_english_font_rom','refined_english_text_rom',
       'refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry','stage1_arith')
mods=[O/'stage1_osd.v',O/'stage1_render.v']+[R/'rtl/color_regions'/(n+'.v') for n in names]
run('private_split_draft_overlay',bench('stage1_overlay'),mods,timeout=1800)
print('PRIVATE_SPLIT_DRAFT_REPLAY_PASS; not adopted; no resource or physical result',flush=True)
