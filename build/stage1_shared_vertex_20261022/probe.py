"""Private shared vertex read port; leave the active physical build untouched."""
from pathlib import Path
import sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run

def edit(s,a,b):
    assert a in s,a
    return s.replace(a,b)

s=(R/'rtl/color_regions/stage1_point.v').read_text()
s=edit(s,'module stage1_point(', 'module stage1_point #(parameter SHARED_VERTEX=0)(')
s=edit(s,'output reg orientation_done,output reg signed [23:0] orientation_cross);',
       'output reg orientation_done,output reg signed [23:0] orientation_cross,output wire [4:0] vertex_address,input wire [20:0] vertex_data);')
s=edit(s,'wire [20:0] vertex_q=point(vertices,region_id,read_index);',
       "assign vertex_address={region_id,read_index[2:0]};\n wire [20:0] vertex_q=SHARED_VERTEX?(read_index[3]?21'd0:vertex_data):point(vertices,region_id,read_index);")
(O/'stage1_point.v').write_text(s)

s=(R/'rtl/color_regions/stage1_validate.v').read_text()
s=edit(s,'#(parameter SHARED=0)', '#(parameter SHARED=0,SHARED_VERTEX=0)')
s=edit(s,'input wire orientation_done,input wire signed [23:0] orientation_cross);',
       'input wire orientation_done,input wire signed [23:0] orientation_cross,output wire [4:0] vertex_address,input wire [20:0] vertex_data);')
s=edit(s,'wire [20:0] vertex_q=read_draft?dp(draft,read_index):vp(vertices,old_region,read_index);',
       "assign vertex_address={old_region,read_index[2:0]};\n wire [20:0] vertex_q=read_draft?dp(draft,read_index):SHARED_VERTEX?(read_index[3]?21'd0:vertex_data):vp(vertices,old_region,read_index);")
(O/'stage1_validate.v').write_text(s)

s=(R/'rtl/color_regions/stage1_regions.v').read_text()
reader='''wire [4:0] point_address,validate_address;
 wire [4:0] vertex_address=validating || validate_start?validate_address:point_address;
 function [20:0] read_vertex;input [671:0] data;input [4:0] index;begin case(index)
'''+''.join(f"5'd{i}:read_vertex=data[{i*21}+:21];\n" for i in range(32))+'''endcase end endfunction
 wire [20:0] shared_vertex=read_vertex(vertices,vertex_address);
 '''
s=edit(s,'stage1_validate #(.SHARED(1)) validator(',reader+'stage1_validate #(.SHARED(1),.SHARED_VERTEX(1)) validator(')
s=edit(s,'validation_error,os,oa,ob,oc,od,cross_q);','validation_error,os,oa,ob,oc,od,cross_q,validate_address,shared_vertex);')
s=edit(s,'stage1_point geometry(', 'stage1_point #(.SHARED_VERTEX(1)) geometry(')
s=edit(s,'point_distances,os,oa,ob,oc,od,cross_q);','point_distances,os,oa,ob,oc,od,cross_q,point_address,shared_vertex);')
(O/'stage1_regions.v').write_text(s)

mods=[O/'stage1_point.v',O/'stage1_validate.v',O/'stage1_regions.v']+[R/'rtl/color_regions'/(n+'.v') for n in ('stage1_arith','stage1_segment','stage1_sequence')]
point=(R/'build/sim/refined/stage1_point_20261022_150917_200752/tb.sv').read_text()
point=edit(point,"stage1_point dut(clk,rst,start,nr,counts,vertices,px,py,busy,done,im,nm,ds,1'b0,21'd0,21'd0,21'd0,,);",'''wire [4:0] address;wire [20:0] value=vertices>>(address*21);
stage1_point #(.SHARED_VERTEX(1)) dut(.clk(clk),.rst_n(rst),.start(start),.region_count(nr),.counts(counts),.vertices(vertices),
.px(px),.py(py),.busy(busy),.done(done),.inside_mask(im),.near_mask(nm),.distances(ds),.orientation_start(1'b0),.oa(21'd0),.ob(21'd0),.oc(21'd0),.vertex_address(address),.vertex_data(value));''')
validate=(R/'build/sim/refined/stage1_validate_20261022_150923_955433/tb.sv').read_text()
validate=edit(validate,'stage1_validate #(.SHARED(1)) dut(clk,rst,start,nr,counts,vertices,nd,draft,busy,done,passed,error_code,os,oa,ob,oc,od,oq);',
'''wire [4:0] address;wire [20:0] value=vertices>>(address*21);
stage1_validate #(.SHARED(1),.SHARED_VERTEX(1)) dut(clk,rst,start,nr,counts,vertices,nd,draft,busy,done,passed,error_code,os,oa,ob,oc,od,oq,address,value);''')
regions=(R/'build/sim/refined/stage1_regions_20261022_150934_778423/tb.sv').read_text()
for label,source in (('point',point),('validate',validate),('regions',regions)):
    run('private_shared_vertex_'+label,source,mods,timeout=300)
