"""Isolate existing material model acceptance from native raster acquisition."""
from test_fhd_processing import R,V,O,run
src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;
wire [7:0] status;wire [127:0] models;integer i,n;
stable_calibration dut(.clk(clk),.rst_n(rst),.sof(1'b0),.valid(1'b0),.rgb(96'd0),.pair(1'b0),.enter(1'b0),.sample(1'b0),.cancel(1'b0),.gain_changed(1'b0),.status(status),.models(models));
initial begin repeat(4)@(negedge clk);rst=1;@(negedge clk);
for(i=0;i<512;i=i+1)begin dut.samples[i]={4{24'hc02020}};dut.background[i]={4{24'h808080}};end
dut.phase=3;dut.cp=0;dut.staged_r=1024;dut.staged_b=1024;dut.background_valid=1;dut.state=5;dut.clear_index=0;
n=0;while((dut.state!=0 || n==0) && n<3000000)begin @(negedge clk);n=n+1;end
if(dut.phase!==3'd4 || status!==8'h80 || dut.positive_sum!==12'd2048 || dut.negative_sum!==12'd0)$fatal(1,"material replay outcome");
$display("FHD_CALIBRATION_REPLAY_PASS cycles%0d peak%0d cluster%0d frameSamples%0d positive%0d negative%0d",n,dut.peak,dut.cluster,dut.frame_samples[0],dut.positive_sum,dut.negative_sum);
$finish;end endmodule'''
run('calibration_replay',src,['stable_calibration','regions_divide'])
