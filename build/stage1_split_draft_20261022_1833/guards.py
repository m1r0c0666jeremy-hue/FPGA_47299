"""Private late-commit/recovery and both snapshot-plane freeze checks."""
from pathlib import Path
import json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
from audit_stage1 import sha
proof=json.loads((R/'reports/stage1/software_current_20261022_1545.json').read_text())
e=proof['regression']['stage1_render_guards']
assert all(sha(R/n)==h for n,h in e['fixture_inputs'].items())
paths=[R/n for n in e['fixture_inputs'] if n.endswith('/tb.sv')];assert len(paths)==1
s=paths[0].read_text()


def edit(a,b):
    global s
    assert s.count(a)==1,(a,s.count(a))
    s=s.replace(a,b)


edit('stage1_render dut(clk,rst,commit,vertices,',
     "reg [2:0] split_region=0;reg split_visible=1;wire [671:0] split_saved={vertices[671:168],168'd0};\nstage1_render #(.SPLIT_DRAFT(1)) dut(clk,rst,commit,split_saved,")
edit('x,y,de,mask,color,label_on,glyph,gx,gy,label_color,ready,underrun);',
     'x,y,de,mask,color,label_on,glyph,gx,gy,label_color,ready,underrun,vertices[167:0],split_region,split_visible);')
edit('vertices=0;repeat(5)', 'vertices=0;split_region=3;split_visible=0;repeat(5)')
edit('if(dut.fv[20:0]!==', 'if(!dut.fd_visible || dut.fd_region!==0 || dut.fd[20:0]!==')
run('private_split_draft_guards',s,[O/'stage1_render.v',R/'rtl/color_regions/stage1_arith.v'],timeout=60)
