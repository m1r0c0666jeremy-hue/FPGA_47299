"""Midpoint admission and a single diagnostic pair, plus existing identity cases."""
from refined_testlib import R,run,literal_fixture
import ast,json,zipfile
info=json.loads((R/'reports/refined/protected_inputs.json').read_text(encoding='utf-8'))
old=R/info['backup']/'stable_tracker_before.v'
if not old.exists():
 with zipfile.ZipFile(R/info['backup']/'sources_before.zip') as z:old.write_bytes(z.read('rtl/color_regions/stable_tracker.v'))
src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;reg [31:0] id=0;reg [1023:0] candidates=0;
wire done,valid,hv;wire [127:0] a,b;wire [10:0] tx;wire [9:0] ty;wire [3:0] reason;wire [83:0] boxes;wire [1:0] state;
stable_tracker dut(clk,rst,start,id,10'd3,16'd0,1'b1,candidates,done,a,b,valid,tx,ty,reason,hv,boxes,stateEXTRA);
function [127:0] c(input integer x,y);begin c=0;c[120]=1;c[61:42]=256;c[72:62]=x;c[82:73]=y;c[89:83]=100;end endfunction
task frame;integer n;begin @(negedge clk);id=id+1;start=1;@(negedge clk);start=0;n=0;while(!done && n<200)begin @(negedge clk);n=n+1;end if(!done)$fatal(1,"tracker timeout");end endtask
initial begin repeat(4)@(negedge clk);rst=1;candidates[127:0]=c(640,330);candidates[639:512]=c(640,550);
frame;frame;frame;MIDPOINT_CHECK
rst=0;repeat(3)@(negedge clk);rst=1;id=0;candidates=0;candidates[127:0]=c(640,300);candidates[639:512]=c(640,310);frame;
DIAGNOSTIC_CHECK
$display("REFINED_TRACKER_COMPARISON_PASS LABEL midpoint and per-pair rejection");$finish;end endmodule'''
for before in (True,False):
 code=src.replace('EXTRA','' if before else ',,,,,').replace('MIDPOINT_CHECK','if(valid)$fatal(1,"baseline guide fixture changed");' if before else 'if(!valid || tx!=640 || ty!=220)$fatal(1,"midpoint guide failed");')
 code=code.replace('DIAGNOSTIC_CHECK','if(!a[104])$fatal(1,"baseline missing-bit fixture changed");' if before else 'if(a[111:104]!=4 || !a[120] || !b[120] || valid)$fatal(1,"invalid slots contaminated rejection %h",a);')
 code=code.replace('LABEL','before' if before else 'after')
 run('tracker_comparison_before' if before else 'tracker_comparison_after',code,[old if before else R/'rtl/color_regions/stable_tracker.v'])
# Keep the prior geometric tie, direction and occlusion tests with the new ports.
quality=literal_fixture(R/'scripts/test_ring_tracker.py').replace('boxes,state);','boxes,state,,,,,);')
run('tracker_quality_and_diagnostics',quality,[R/'rtl/color_regions/stable_tracker.v'])
for node in ast.walk(ast.parse((R/'scripts/test_stable_adversarial.py').read_text(encoding='utf-8'))):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='run' and isinstance(node.args[0],ast.Constant) and node.args[0].value=='tracker':
  regression=ast.literal_eval(node.args[1]).replace('boxes,selected_state);','boxes,selected_state,,,,,);')
  run('tracker_identity_adversarial',regression,[R/'rtl/color_regions/stable_tracker.v']);break
