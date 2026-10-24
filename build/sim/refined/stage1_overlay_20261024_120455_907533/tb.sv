module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,commit=0,de=0,vs=0,show=1,rot=0;reg [2:0] zoom=0;reg [3:0] state=2;
reg [23:0] raw=0;wire ovs,ohs,ode;wire [23:0] rgb;
stage1_osd dut(2'd2,672'h26c9c52c4ce00000000000000000000000000000000280a00503c000000000000000000000000000000002806e05023000000000000000000000000000000002803c0500a,168'd0,16'h2222,4'hf,3'd4,3'd1,3'd1,4'd0,state,4'd1,4'd0,1'b0,2'd0,11'd0,20'd0,4'd0,4'd0,1'b0,1'b1,1'b0,1'b0,3'd5,
clk,rst,vs,1'b0,de,raw,768'd0,11'd0,10'd0,zoom,2'd0,3'd0,1'b0,show,1'b1,1'b0,1'b0,1'b0,
ovs,ohs,ode,rgb,rot,2'd0,32'd0,commit,1'b0,32'd0,32'd0,128'd0,128'd0,39'd0,18'd0);
reg [23:0] expected[0:798719];reg [23:0] e0=0,e1=0;reg v0=0,v1=0,checking=0;integer c,y,h,index=0,pixels=0;
always @(posedge clk)begin
if(de)begin e0<=expected[index];index=index+1;end
e1<=e0;v0<=de;v1<=v0;#1;
if(checking && (ode!==v1 || (v1 && rgb!==e1)))$fatal(1,"overlay c%0d input%0d/%0d index%0d got%h expected%h de%b/%b",c,h,y,index,rgb,e1,ode,v1);
if(checking && v1)pixels=pixels+1;
end
task frame;begin
checking=0;de=0;rst=0;repeat(3)@(negedge clk);rst=1;vs=1;@(negedge clk);vs=0;commit=1;@(negedge clk);commit=0;
repeat(10000)@(negedge clk);if(!dut.region_ready || dut.region_underrun)$fatal(1,"overlay preparation");
index=0;checking=1;
for(y=0;y<624;y=y+1)for(h=0;h<1650;h=h+1)begin
@(negedge clk);de=h<1280;raw=24'h203040|((y%256)<<8)|(h%256);end
@(negedge clk);de=0;repeat(3)@(negedge clk);checking=0;
if(index!=798720)$fatal(1,"input pixel count");end endtask
initial begin
c=0;zoom=0;rot=0;state=2;show=1;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_overlay_vectors_8531590602f0/0.hex",expected);frame;$display("STAGE1_OVERLAY_CASE_PASS c0");
c=1;zoom=0;rot=1;state=2;show=1;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_overlay_vectors_8531590602f0/1.hex",expected);frame;$display("STAGE1_OVERLAY_CASE_PASS c1");
c=2;zoom=1;rot=0;state=2;show=1;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_overlay_vectors_8531590602f0/2.hex",expected);frame;$display("STAGE1_OVERLAY_CASE_PASS c2");
c=3;zoom=1;rot=1;state=2;show=1;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_overlay_vectors_8531590602f0/3.hex",expected);frame;$display("STAGE1_OVERLAY_CASE_PASS c3");
c=4;zoom=4;rot=0;state=2;show=1;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_overlay_vectors_8531590602f0/4.hex",expected);frame;$display("STAGE1_OVERLAY_CASE_PASS c4");
c=5;zoom=4;rot=1;state=2;show=1;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_overlay_vectors_8531590602f0/5.hex",expected);frame;$display("STAGE1_OVERLAY_CASE_PASS c5");
c=6;zoom=0;rot=0;state=6;show=1;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_overlay_vectors_8531590602f0/6.hex",expected);frame;$display("STAGE1_OVERLAY_CASE_PASS c6");
c=7;zoom=0;rot=1;state=6;show=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_overlay_vectors_8531590602f0/7.hex",expected);frame;$display("STAGE1_OVERLAY_CASE_PASS c7");
$display("STAGE1_OVERLAY_PASS cases=8 pixels=%0d",pixels);$finish;end endmodule