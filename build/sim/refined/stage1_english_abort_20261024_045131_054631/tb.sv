module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,de=0;reg [767:0] meta=0;
reg [2:0] zoom=2,control=2;reg [1:0] mode=1,diag=0;reg pair=0,rotate=1,tracking=1,video=1,lv=1;
reg [31:0] latency=12345,age=2;wire vs,hs,ode;wire [23:0] rgb;
stage1_osd dut(2'd0,672'd0,168'd0,16'd0,4'd0,3'd0,3'd0,3'd0,4'd0,4'd0,4'd0,4'd0,1'b0,2'd0,11'd0,20'd0,4'd0,4'd0,1'b0,1'b0,1'b0,1'b0,3'd5,clk,rst,1'b0,1'b0,de,24'h123456,meta,11'd0,10'd0,zoom,mode,control,tracking,1'b1,video,pair,1'b1,1'b1,vs,hs,ode,rgb,rotate,diag,32'h12345678,1'b0,lv,latency,age,128'd0,128'd0,39'd0,18'd0);
reg [23:0] expected[0:122879];integer c,x,y,n,outn=0;reg checking=0;
always @(posedge clk)begin #1;if(checking && ode)begin
if(rgb!==expected[outn])$fatal(1,"English footer case%0d pixel%0d got%h expected%h",c,outn,rgb,expected[outn]);outn=outn+1;end end
task frame;begin
@(negedge clk);de=0;rst=0;checking=0;repeat(3)@(negedge clk);rst=1;
@(negedge clk);dut.y=620;dut.x=0;outn=0;
for(y=620;y<720;y=y+1)for(x=0;x<1280;x=x+1)begin
@(negedge clk);de=1;if(y==624 && x==1)checking=1;
if((c==0 && y==622 && x==0)||(c==1 && y==624 && x==2))lv=0;
if(y==640 && x==0 && !dut.footer_ready)$fatal(1,"formatter deadline");end
@(negedge clk);de=0;repeat(4)@(negedge clk);checking=0;
if(outn!=122880)$fatal(1,"English footer count %0d",outn);end endtask
initial begin
c=0;meta=768'h000000000002000000000000000000000000000000000000000000af0000000000000000000000000000000080000000000000000000000000000000000000008080000000000000000000000000000000000000000000000000000600000000;diag=0;zoom=2;mode=1;pair=0;rotate=1;control=2;tracking=1;video=1;lv=1;latency=12345;age=2;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/sim/stage1_footer_pixels/abort_0.hex",expected);frame;$display("ENGLISH_UI_CASE_PASS late_abort");
c=1;meta=768'h000000000002000000000000000000000000000000000000000000af0000000000000000000000000000000080000000000000000000000000000000000000008080000000000000000000000000000000000000000000000000000600000000;diag=1;zoom=2;mode=1;pair=0;rotate=1;control=2;tracking=1;video=1;lv=1;latency=12345;age=2;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/sim/stage1_footer_pixels/abort_1.hex",expected);frame;$display("ENGLISH_UI_CASE_PASS last_pixel_abort");
$display("STAGE1_ENGLISH_ABORT_PASS 2 cases 245760 pixels");$finish;end endmodule