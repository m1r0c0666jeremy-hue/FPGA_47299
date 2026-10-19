"""Real RGB capture with per-frame counts, mailbox blockage and bank reuse."""
from test_ring_calibration import R,run
src='''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,v=0,ready=1;reg [95:0] rgb=0;reg [15:0] rev=1;
wire [31:0] id,drop;wire ov;wire [639:0] meta;reg [127:0] models;integer f,x,y,i,n,received=0;reg [23:0] px;reg [639:0] saved;
function [63:0] model;input integer lo,hi;begin model=64'h8000000000000000|(64'(lo)<<54)|(64'(hi)<<45)|(64'd32<<37)|(64'd16<<29)|(64'd1<<27);end endfunction
stable_capture dut(clk,rst,sof,v,1'b0,rgb,1'b0,1'b1,8'd7,models,rev,24'h400400,8'd0,1'b0,1'b0,ready,id,ov,meta,drop);
always @(negedge clk)if(ov && meta[31:0]<=8)begin
received=received+1;n=meta[31:0];
if(meta[415:413]!=3 || !meta[604] || !meta[247] || meta[543:416]!==models || meta[559:544]!=(n>=6?2:1))$fatal(1,"frame/protocol provenance %0d",n);
if(meta[275:256]!=(n==5?n:48+n) || meta[315:296]!=(n==5?0:48) || meta[295:276]!=((n==4 || n==5)?0:256) || meta[335:316]!=((n==4 || n==5)?0:256))$fatal(1,"raw/filtered counts frame%0d %0d/%0d %0d/%0d",n,meta[275:256],meta[315:296],meta[295:276],meta[335:316]);
if(n!=5 && (meta[338:336]!=1 || meta[356:350]!=100 || meta[203:184]!=48))$fatal(1,"candidate/support frame%0d",n);
if(n==5 && (meta[338:336]!=0 || meta[345:342]!=2 || meta[349:346]!=1))$fatal(1,"failure stages");
if(n==3 && (!meta[32] || meta[379:378]!=3 || meta[369:368]!=2))$fatal(1,"confirmation diagnostics");
if(n==8 && (!meta[32] || meta[379:378]!=3 || meta[377:370]!=0))$fatal(1,"recovery/latest diagnostics");
end
initial begin models={model(195,255),model(345,30)};repeat(3)@(negedge clk);rst=1;
for(f=1;f<=8;f=f+1)begin
if(f==5)ready=0;rev=f>=6?2:1;
for(y=0;y<720;y=y+1)for(x=0;x<1280;x=x+4)begin @(negedge clk);v=1;sof=x==0 && y==0;
for(i=0;i<4;i=i+1)begin px=24'h282828;
if(f!=5 && x+i>=640 && x+i<643 && y>=320 && y<336)px=24'hb41414;
if(f!=4 && f!=5 && x+i>=520 && x+i<536 && y>=320 && y<336)px=24'h1428b4;
if(y==16 && x+i>=16 && x+i<16+32*f && (x+i-16)%32==0)px=24'hb41414;
rgb[95-i*24-:24]=px;end end end
@(negedge clk);sof=1;v=0;@(negedge clk);sof=0;repeat(213000)@(negedge clk);
if(!dut.waiting_result || dut.waiting_packet[31:0]!=8 || dut.owned[1])$fatal(1,"mailbox retained acquisition bank");saved=dut.waiting_packet;
// Frame10 reuses frame8's bank while the independently copied frame8 result is
// still pending. Check before the subsequent invalid-frame packet can replace it.
sof=1;v=1;rgb={4{24'hb41414}};@(negedge clk);sof=0;repeat(6)@(negedge clk);v=0;
if(dut.waiting_packet!==saved || dut.raw_a[1]==56)$fatal(1,"pending diagnostics changed on bank reuse");
ready=1;repeat(100)@(negedge clk);
if(received!=4 || drop<3)$fatal(1,"blocked mailbox/latest packet %0d %0d",received,drop);
$display("RING_DIAGNOSTICS_PASS eight full RGB frames, raw/filter/candidate/support/decision counts, frozen model versions, mailbox blockage and bank reuse");$finish;end endmodule'''
run('diagnostics_capture',src,[R/f'rtl/color_regions/{n}.v' for n in ('stable_capture','stable_model_lane','stable_filter4','stable_grid','regions_divide','stable_tracker')])
