from pathlib import Path
import sys,json,hashlib
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
clone=O/'stage1_render_clean_reference.v'
assert not clone.exists();s=(O/'stage1_render.v').read_text();clone.write_bytes(s.replace('module stage1_render #','module stage1_render_clean_reference #',1).encode())
bench=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,rrst=0,c=0,rc=0;reg[671:0] v=0;
wire[3:0]m,rm;wire[23:0]color,rcolor,lc,rlc;wire lon,rlon,ready,rready,u,ru;wire[7:0]g,rg;wire[2:0]gx,rgx;wire[3:0]gy,rgy;
stage1_render dut(clk,rst,c,v,16'h0003,4'h1,2'd2,11'd0,10'd0,3'd0,1'b0,4'd0,4'd0,3'd0,3'd0,11'd0,10'd0,1'b0,m,color,lon,g,gx,gy,lc,ready,u,168'd0,3'd0,1'b0);
stage1_render_clean_reference refdut(clk,rrst,rc,v,16'h0003,4'h1,2'd2,11'd0,10'd0,3'd0,1'b0,4'd0,4'd0,3'd0,3'd0,11'd0,10'd0,1'b0,rm,rcolor,rlon,rg,rgx,rgy,rlc,rready,ru,168'd0,3'd0,1'b0);
integer k;
initial begin
v[20:0]={10'd100,11'd100};v[41:21]={10'd200,11'd600};v[62:42]={10'd500,11'd200};
repeat(3)@(negedge clk);rst=1;c=1;@(negedge clk);c=0;
wait(dut.mstart && dut.mop==1 && !dut.mbusy);@(negedge clk);
v=0;v[20:0]={10'd100,11'd200};v[41:21]={10'd500,11'd300};v[62:42]={10'd300,11'd600};rrst=1;c=1;rc=1;
@(negedge clk);c=0;rc=0;repeat(12000)@(negedge clk);
if(!ready || !rready || u || ru)$fatal(1,"mid-divider-launch recommit readiness differs ready%0d/%0d under%0d/%0d state%0d/%0d busy%0d/%0d",ready,rready,u,ru,dut.state,refdut.state,dut.mbusy,refdut.mbusy);
for(k=0;k<640;k=k+1)if(dut.state_line_mem[k]!==refdut.state_line_mem[k])$fatal(1,"mid-launch recommit row word differs %0d",k);
for(k=768;k<1024;k=k+1)if(dut.state_line_mem[k]!==refdut.state_line_mem[k])$fatal(1,"mid-launch recommit edge word differs %0d",k);
$display("SERIAL_SNAPSHOT_MID_LAUNCH_RECOMMIT_PASS words=896");$finish;end endmodule'''
run('private_serial_snapshot_mid_launch',bench,[R/'rtl/color_regions/stage1_arith.v',O/'stage1_render.v',clone],timeout=60)
