"""DDR bytes and old-coordinate expectations independent of adapter arithmetic."""
from test_native_zoom_core import execute,PIXEL

def main():
    tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,ven=0;
reg [24:0] va=0;wire vr,vv;wire [127:0] vd;wire [31:0] accepted;
reg [9:0] sy=0,y0=0;reg [10:0] x0=0;reg [1:0] bank=0;reg [2:0] zoom=0;
reg wb=0,we=0,dr=1,dv=0;reg [127:0] data=0;wire rb,re;wire [24:0] ra;wire fault;
native_read_adapter dut(clk,rst,ven,va,vr,vv,vd,accepted,sy,bank,zoom,x0,y0,wb,we,dr,dv,data,rb,re,ra,1'b0,fault);
PIXEL
reg [24:0] queue[0:4095];integer head=0,tail=0,cycles=0,requests=0,returned=0,scenarios=0;
integer lane,byte_index,x,y,channel,offset,j,n;reg [127:0] expected;reg [23:0] p;
function integer base(input integer b);begin case(b)0:base=0;1:base=7000000;2:base=14000000;3:base=21000000;endcase end endfunction
function [127:0] dense_word(input [24:0] address);
integer k,pos,xx,yy,ch;reg [23:0] rgb;begin
for(k=0;k<16;k=k+1)begin
pos=(address-base(bank))*2+k;yy=pos/7680;xx=(pos%7680)/3;ch=pos%3;
rgb=pixel(xx,yy);dense_word[127-k*8-:8]=rgb[23-ch*8-:8];end end endfunction
function [127:0] logical_word(input integer word_index);
integer k,pos,xx,yy,ch;reg [23:0] rgb;begin
for(k=0;k<16;k=k+1)begin pos=word_index*16+k;xx=pos/3;ch=pos%3;
if(zoom==2)begin yy=2*y0+sy;if(yy>1439)yy=1439;rgb=pixel(2*x0+xx,yy);end
else rgb=average(2*xx,2*sy);
logical_word[127-k*8-:8]=rgb[23-ch*8-:8];end end endfunction
always @(posedge clk)if(rst)begin
if(re && we)$fatal(1,"read collided with registered final writer beat");
if(re)begin queue[tail]=ra;tail=tail+1;if(tail>=4096)$fatal(1,"DDR queue full");end end
always @(negedge clk)if(rst)begin
cycles=cycles+1;
if(vv)begin expected=logical_word(returned);if(vd!==expected)
$fatal(1,"DDR pixels scenario%0d zoom%0d row%0d x0%0d word%0d got%h expected%h state%0d",scenarios,zoom,sy,x0,returned,vd,expected,dut.state);
returned=returned+1;end
if(fault)$fatal(1,"adapter fault scenario%0d state%0d accepted%0d returned%0d",scenarios,dut.state,accepted,returned);
// In-order DDR with bubbles and independent write bursts between read batches.
dv=0;if(head<tail && cycles%7!=0 && cycles>5)begin data=dense_word(queue[head]);head=head+1;dv=1;end
dr=cycles%11!=0;
we=wb;
if(wb)begin if(cycles%13==0)wb=0;end
else if(!rb && cycles%19==0)wb=1;
end
task scenario(input integer z,b,yy,xx,oy);begin
rst=0;ven=0;dv=0;wb=0;we=0;repeat(4)@(negedge clk);
head=0;tail=0;cycles=0;requests=0;returned=0;zoom=z;bank=b;sy=yy;x0=xx;y0=oy;rst=1;
while(requests<240)begin
@(negedge clk);ven=vr;va=base(bank)+sy*1920+requests*8;
if(vr)requests=requests+1;
end
@(negedge clk);ven=0;n=0;
while(returned<240 && n<20000)begin @(negedge clk);n=n+1;end
repeat(20)@(negedge clk);
if(returned!=240 || accepted!=240 || head!=tail)$fatal(1,"adapter completion zoom%0d returned%0d accepted%0d head%0d tail%0d",zoom,returned,accepted,head,tail);
scenarios=scenarios+1;
end endtask
initial begin
for(j=0;j<8;j=j+1)scenario(2,j%4,17,j,40);
scenario(2,3,623,639,408);scenario(2,0,624,640,408);
for(j=0;j<4;j=j+1)begin scenario(0,j,0,0,0);scenario(1,j,719,300,200);end
$display("NATIVE_READ_ADAPTER_PASS scenarios=%0d words=%0d dense_offsets/all_banks/2x2_average/bubbles/write_yield",scenarios,scenarios*240);$finish;
end endmodule'''.replace('PIXEL',PIXEL)
    execute('read_adapter',tb,['native_read_adapter.v','native_downsample2.v','stable_packer.v'],timeout=180)
if __name__=='__main__':main()
