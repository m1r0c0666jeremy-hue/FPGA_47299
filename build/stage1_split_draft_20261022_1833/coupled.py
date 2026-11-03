"""Actual private editor -> split frame snapshot -> visible 5x5 press-position mark."""
from pathlib import Path
import json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];P=R/'build/stage1_shared_vertex_20261022';sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
from audit_stage1 import sha
previous=json.loads((O/'private_validation.json').read_text())['checks']['private_split_shared_regions']
s=(R/previous['bench']).read_text()


def edit(a,b):
    global s
    assert s.count(a)==1,(a,s.count(a))
    s=s.replace(a,b)


declarations='''reg geometry_commit=0,rde=0;reg [10:0] rx=0;reg [9:0] ry=0;
wire [3:0] pmask;wire [23:0] pcolor,lcolor;wire lon,rready,under;wire [7:0] glyph;wire [2:0] gx;wire [3:0] gy;
stage1_render #(.SPLIT_DRAFT(1)) picture(clk,rst,geometry_commit,private_saved,counts,closed,mode,11'd0,10'd0,3'd0,1'b0,
state,completed,expected,actual,rx,ry,rde,pmask,pcolor,lon,glyph,gx,gy,lcolor,rready,under,private_draft,nr,nd!=0);
integer row_check,column_check;reg [3:0] expected_mask;
'''
edit('stage1_regions #',declarations+'stage1_regions #')
scan='''geometry_commit=1;@(negedge clk);geometry_commit=0;repeat(10000)@(negedge clk);
if(!rready || under)$fatal(1,"coupled draft prepare failed");
for(row_check=0;row_check<105;row_check=row_check+1)begin
for(column_check=0;column_check<1650;column_check=column_check+1)begin
@(negedge clk);rx=column_check<1280?column_check:0;ry=row_check;rde=column_check<1280;
@(posedge clk);#1;
if(rde)begin
expected_mask=(row_check>=98 && row_check<=102 && column_check>=98 && column_check<=102)?4'd1:4'd0;
if(pmask!==expected_mask || under)$fatal(1,"actual editor/draft render xy%0d/%0d got%h expected%h",column_check,row_check,pmask,expected_mask);
end end end
@(negedge clk);rde=0;
$display("PRIVATE_EDIT_RENDER_POINT_PASS pixels=134400");
'''
edit('record(300,100);record(200,250);key(3);',scan+'record(300,100);record(200,250);key(3);')
mods=[O/'stage1_regions_shared.v',O/'stage1_render.v',P/'stage1_point.v',P/'stage1_validate.v']+[R/'rtl/color_regions'/(n+'.v') for n in ('stage1_arith','stage1_segment','stage1_sequence')]
out=run('private_split_edit_render',s,mods,timeout=300)
result=dict(scope='PRIVATE ONLY; one actual editor point/105 rows plus editor/order checks, not full video integration',
            output=out.relative_to(R).as_posix(),bench_sha256=sha(out/'tb.sv'),producer_sha256=sha(Path(__file__)),
            inputs={p.relative_to(R).as_posix():sha(p) for p in mods},pixels=134400,adopted=False)
with (O/'coupled_validation.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
