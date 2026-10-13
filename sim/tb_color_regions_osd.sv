`timescale 1ns/1ps
module tb_color_regions_osd;
reg clk=0;always #5 clk=~clk;
reg rst=0,vs=0,hs=0,de=0,show=1,pair=0;reg [23:0] rgb=24'h405060;
reg [415:0] meta=0;reg [10:0] x0=0;reg [9:0] y0=48;reg [1:0] zoom=0,mode=0;reg [2:0] state=3;
wire ovs,ohs,ode;wire [23:0] out;
regions_osd u(clk,rst,vs,hs,de,rgb,meta,x0,y0,zoom,mode,state,show,1'b1,pair,1'b1,1'b1,ovs,ohs,ode,out);
integer x,y,n,fd=0,ox=0,oy=0,checked=0;reg oldvs=0;reg [1023:0] path;
always @(negedge clk)begin
 if(ovs && !oldvs)begin ox=0;oy=0;end oldvs=ovs;
 if(ode)begin
   if(fd)$fwrite(fd,"%c%c%c",out[23:16],out[15:8],out[7:0]);
   if(oy==0 && zoom==0 && out!==24'h405060)$fatal(1,"unexpected top diagnostic overlay");
   if(ox==((300-x0)<<zoom) && oy==((200-y0)<<zoom) && show && out!==(pair?24'hFFFF40:24'hFF6060))$fatal(1,"A box source mapping");
   if(ox==((600-x0)<<zoom) && oy==((300-y0)<<zoom) && show && out!==(pair?24'hE080FF:24'h6090FF))$fatal(1,"B box source mapping");
   if(!show && oy<624 && out!==24'h405060)$fatal(1,"hidden annotation changed image");
   if(ox==0 && oy==624 && out!==24'h101824)$fatal(1,"footer position");
   checked=checked+1;if(ox==1279)begin ox=0;oy=oy+1;end else ox=ox+1;
 end
end
initial begin
if($value$plusargs("MODE=%d",n))mode=n;
if($value$plusargs("HIDE=%d",n))show=!n;
if($value$plusargs("PAIR=%d",n))pair=n;
if($value$plusargs("ZOOM=%d",n))zoom=n;
case(zoom)0:begin x0=0;y0=48;end 1:begin x0=320;y0=204;end default:begin x0=480;y0=282;end endcase
if($value$plusargs("CAPTURE=%s",path))begin fd=$fopen(path,"wb");$fwrite(fd,"P6\n1280 720\n255\n");end
meta[245]=1;meta[246]=1;meta[318]=1;meta[408]=1;meta[407:384]={8'd71,8'd120,8'd88};
meta[141:100]={10'd219,10'd200,11'd319,11'd300};meta[183:142]={10'd319,10'd300,11'd639,11'd600};
meta[297:256]={10'd529,10'd500,11'd929,11'd900};
repeat(3)@(negedge clk);rst=1;vs=1;repeat(3)@(negedge clk);vs=0;repeat(3)@(negedge clk);
for(y=0;y<720;y=y+1)begin
 for(x=0;x<1280;x=x+1)begin de=1;@(negedge clk);end
 de=0;repeat(8)@(negedge clk);
end
repeat(5)@(negedge clk);if(checked!=921600)$fatal(1,"pixel count");if(fd)$fclose(fd);
$display("PASS compact OSD full frame mode=%0d show=%b zoom=%0d pair=%0d",mode,show,zoom,pair);$finish;
end
endmodule
