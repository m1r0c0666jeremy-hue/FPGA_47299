"""Eight complete background frames with independent position/data checks."""
from test_ring_calibration import R,run
src='''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,v=0,sample=0;reg [95:0] rgb=0;
wire [11:0] gr,gb;wire [127:0] models;wire [15:0] rev;wire active,needs,fp;wire [7:0] status,fs;wire [23:0] fg;
stable_calibration dut(clk,rst,sof,v,rgb,1'b0,1'b0,sample,1'b0,1'b0,gr,gb,models,rev,active,needs,status,fp,fg,fs);
integer f,xx,yy,p,n=0,j,ex,ey;reg [95:0] expected[0:511];reg [23:0] color;
function [23:0] pixel;input integer x,y,f;begin pixel={8'(x),8'(y),8'(f*31)};end endfunction
always @(posedge clk)if(rst && dut.sample_write)begin
ex=52+160*(dut.groups%8)+8*dut.frames;ey=17+90*(dut.groups/8)+8*((3*dut.frames)%8);
if(dut.rx!=ex || dut.ry!=ey)$fatal(1,"background coordinates frame%0d group%0d",dut.frames,dut.groups);
if(dut.sample_wraddr!=n)$fatal(1,"sample address sequence");n=n+1;
end
initial begin
for(f=0;f<8;f=f+1)for(j=0;j<64;j=j+1)for(p=0;p<4;p=p+1)
expected[f*64+j][95-p*24-:24]=pixel(52+160*(j%8)+8*f+p,17+90*(j/8)+8*((3*f)%8),f);
repeat(3)@(negedge clk);rst=1;@(negedge clk);dut.phase=2;dut.cp=0;dut.staged_r=1024;dut.staged_b=1024;
sample=1;@(negedge clk);sample=0;
for(f=0;f<8;f=f+1)for(yy=0;yy<720;yy=yy+1)for(xx=0;xx<1280;xx=xx+4)begin
@(negedge clk);sof=xx==0 && yy==0;v=1;for(p=0;p<4;p=p+1)rgb[95-p*24-:24]=pixel(xx+p,yy,f);end
@(negedge clk);sof=1;v=0;@(negedge clk);sof=0;
if(n!=512 || !dut.background_valid || dut.phase!=3)$fatal(1,"background incomplete %0d %h",n,status);
for(j=0;j<512;j=j+1)if(dut.background[j]!==expected[j])$fatal(1,"background pixel/address %0d",j);
$display("RING_BACKGROUND_SAMPLER_PASS eight full frames, 512 exact four-pixel words, stratified coordinates and jitter");$finish;end endmodule'''
run('background_sampler',src,[R/'rtl/color_regions/stable_calibration.v',R/'rtl/color_regions/regions_divide.v'])
