module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,de=0;reg [767:0] meta=0;
reg [1:0] umode=1,trend=0;reg [3:0] state=0,nd=2,occupied=0,error=0;
reg [2:0] n=2,target=1,actual=0;reg [10:0] distance=1234;reg [19:0] dwell=12345;reg tip=1,show=1,muted=0,busy=0;
wire vs,hs,ode;wire [23:0] rgb;
stage1_osd dut(umode,672'd0,168'd0,16'd0,4'd0,n,target,actual,nd,state,4'd0,occupied,muted,trend,distance,dwell,error,4'd0,busy,tip,1'b0,1'b0,3'd5,
clk,rst,1'b0,1'b0,de,24'h123456,meta,11'd0,10'd0,3'd2,2'd1,3'd2,1'b1,show,1'b1,1'b0,1'b1,1'b1,
vs,hs,ode,rgb,1'b1,2'd0,32'h12345678,1'b0,1'b1,32'd12345,32'd2,128'd0,128'd0,39'd0,18'd0);
reg [23:0] expected[0:122879];integer c,x,y,outn;reg checking=0;
always @(posedge clk)begin #1;if(checking && ode)begin
if(rgb!==expected[outn])$fatal(1,"region footer c%0d pixel%0d got%h expected%h",c,outn,rgb,expected[outn]);outn=outn+1;end end
task frame;begin
@(negedge clk);de=0;rst=0;checking=0;repeat(3)@(negedge clk);rst=1;
@(negedge clk);dut.y=620;dut.x=0;outn=0;
for(y=620;y<720;y=y+1)for(x=0;x<1280;x=x+1)begin
@(negedge clk);de=1;if(y==624 && x==1)checking=1;
if(y==640 && x==0 && !dut.footer_ready)$fatal(1,"region formatter deadline");end
@(negedge clk);de=0;repeat(4)@(negedge clk);checking=0;
if(outn!=122880)$fatal(1,"footer length");end endtask
initial begin meta[255]=1;meta[247]=1;meta[415:413]=4;meta[559:544]=16'h00af;
c=0;umode=1;state=0;n=2;target=1;actual=0;nd=2;occupied=0;distance=1234;dwell=12345;trend=0;error=0;tip=1;show=1;muted=0;busy=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/0.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS edit");
c=1;umode=1;state=0;n=2;target=1;actual=0;nd=2;occupied=0;distance=1234;dwell=12345;trend=0;error=2;tip=1;show=1;muted=0;busy=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/1.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS edit_cross");
c=2;umode=1;state=0;n=0;target=1;actual=0;nd=2;occupied=0;distance=0;dwell=12345;trend=0;error=0;tip=1;show=1;muted=0;busy=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/2.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS edit_no_area");
c=3;umode=2;state=2;n=2;target=1;actual=0;nd=0;occupied=1;distance=86;dwell=2500;trend=0;error=0;tip=1;show=1;muted=0;busy=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/3.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS running");
c=4;umode=2;state=2;n=2;target=1;actual=0;nd=0;occupied=1;distance=86;dwell=2500;trend=0;error=0;tip=1;show=1;muted=0;busy=1;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/4.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS waiting_geometry");
c=5;umode=2;state=1;n=2;target=1;actual=0;nd=0;occupied=1;distance=86;dwell=2500;trend=0;error=0;tip=1;show=1;muted=0;busy=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/5.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS wait_out");
c=6;umode=2;state=3;n=2;target=1;actual=0;nd=0;occupied=1;distance=86;dwell=2500;trend=0;error=0;tip=1;show=1;muted=0;busy=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/6.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS paused");
c=7;umode=2;state=6;n=2;target=1;actual=3;nd=0;occupied=1;distance=86;dwell=2500;trend=0;error=0;tip=1;show=1;muted=0;busy=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/7.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS fail");
c=8;umode=2;state=6;n=2;target=1;actual=3;nd=0;occupied=1;distance=86;dwell=2500;trend=0;error=0;tip=1;show=1;muted=1;busy=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/8.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS fail_muted");
c=9;umode=2;state=6;n=2;target=1;actual=3;nd=0;occupied=1;distance=86;dwell=2500;trend=0;error=0;tip=1;show=0;muted=1;busy=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/9.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS hidden_fail");
c=10;umode=2;state=3;n=2;target=1;actual=0;nd=0;occupied=1;distance=86;dwell=2500;trend=0;error=0;tip=1;show=0;muted=0;busy=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/10.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS hidden_pause");
c=11;umode=2;state=7;n=2;target=1;actual=0;nd=0;occupied=1;distance=86;dwell=2500;trend=0;error=0;tip=0;show=0;muted=0;busy=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/11.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS hidden_lost");
c=12;umode=2;state=2;n=2;target=1;actual=0;nd=0;occupied=1;distance=86;dwell=2500;trend=0;error=0;tip=1;show=0;muted=0;busy=0;$readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_rect_region_footer_vectors_042ccc84d10b/12.hex",expected);frame;$display("REGION_FOOTER_CASE_PASS hidden_run");
$display("STAGE1_REGION_FOOTER_PASS cases=13 pixels=1597440");$finish;end endmodule