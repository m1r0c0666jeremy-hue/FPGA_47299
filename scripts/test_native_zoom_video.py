"""Real 75MHz/133MHz row scheduling and independent dense/1x pixel oracle."""
import argparse
from test_native_zoom_core import execute,PIXEL
from refined_testlib import R

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--zoom',type=int,choices=(0,1,2));ap.add_argument('--rotate',type=int,choices=(0,1));a=ap.parse_args()
    tb=r'''`timescale 1ns/1ps
module tb;
reg pc=0,dc=0;always #6.667 pc=~pc;always #3.75 dc=~dc;
reg rst=0,commit=0;reg [10:0] px=0;reg [9:0] py=0;
wire vs=py<5,hs=px>=1390 && px<1430,de=py>=25 && py<745 && px<1280;
integer z=0,rot=0,origin_x=0,origin_y=48;
wire ovs,ohs,ode,ok,rb,re,ft;wire [24:0] ra;wire [23:0] rgb;wire [1:0] mask;
wire [127:0] dd,pd;reg dr=1,dv=0,wb=0,we=0;reg [127:0] data=0;reg [31:0] accepted=0;
native_line_reader dut(.I_frame_commit(commit),.I_selected_good(1'b1),.I_rst_n(rst),
.I_ddr_clk(dc),.I_write_busy(wb),.I_write_en(we),.I_read_buffer(2'd2),.I_frame_id(32'd7),
.I_models(128'h80000000000000008000000000000000),.I_ddr_ready(dr),.I_ddr_valid(dv),.I_ddr_data(data),
.O_read_busy(rb),.O_read_en(re),.O_read_addr(ra),.I_pixel_clk(pc),.I_vs(vs),.I_hs(hs),.I_de(de),
.I_x0(11'(origin_x)),.I_y0(10'(origin_y)),.I_zoom(3'(z)),.O_vs(ovs),.O_hs(ohs),.O_de(ode),.O_rgb(rgb),
.O_mask(mask),.O_video_ok(ok),.I_rotate(1'(rot)),.I_stream_n(1'b1),.O_fault_toggle(ft),
.O_ddr_diag(dd),.O_pixel_diag(pd),.I_accepted_reads(accepted),.I_unexpected_return(1'b0));
PIXEL
reg [24:0] queue[0:4095];integer head=0,tail=0,cycles=0,k,pos,xx,yy,ch;
function [127:0] word_at(input [24:0] address);
integer i,b,x,y,c;reg [23:0] p;begin
for(i=0;i<16;i=i+1)begin b=(address-14000000)*2+i;y=b/7680;x=(b%7680)/3;c=b%3;
p=pixel(x,y);word_at[127-i*8-:8]=p[23-c*8-:8];end end endfunction
always @(posedge dc)if(rst)begin if(re && we)$fatal(1,"shared DDR read/write collision");
if(re)begin queue[tail&4095]=ra;tail=tail+1;accepted<=accepted+1'b1;end end
always @(negedge dc)if(rst)begin
cycles=cycles+1;dv=0;
if(head<tail && cycles%17!=0)begin data=word_at(queue[head&4095]);head=head+1;dv=1;end
dr=cycles%13!=0;
we=wb;
if(wb)begin if(cycles%11==0)wb=0;end else if(!rb && cycles%79==0)wb=1;
if(tail-head>=4096)$fatal(1,"DDR queue overflow");
end
always @(negedge pc)begin
if(!rst)begin px=0;py=0;commit=0;end
else begin
commit=py==0 && px==96;
if(px==1649)begin px=0;py=py==749?0:py+1'b1;end else px=px+1'b1;
end end
integer ox=0,oy=0,checked=0,sx,sy;reg oldvs=0;reg [23:0] expected;
always @(posedge pc)begin
#1;
if(rst)begin
if(ovs && !oldvs)begin ox=0;oy=0;end oldvs=ovs;
if(ode)begin
 if(oy<624)begin
  if(z==2)begin
   sx=2*origin_x+(rot?1279-ox:ox);sy=2*origin_y+(rot?623-oy:oy);expected=pixel(sx,sy);
  end else begin
   sx=origin_x+((rot?1279-ox:ox)*(z==1?2:1))/(z==1?3:1);
   sy=origin_y+((rot?623-oy:oy)*(z==1?2:1))/(z==1?3:1);
   expected=average(sx*2,sy*2);
  end
  if(rgb!==expected || !ok)$fatal(1,"native video z%0d r%0d out%0d/%0d source%0d/%0d got%h expected%h ok%b diag%h adapter_state%0d core_state%0d",
   z,rot,ox,oy,sx,sy,rgb,expected,ok,dd,dut.adapter.state,dut.core.state);
  checked=checked+1;
 end
 if(ox==1279)begin ox=0;oy=oy+1;end else ox=ox+1;
 if(checked==798720)begin
  if(ft)$fatal(1,"video recovery fault");
  $display("NATIVE_VIDEO_PASS zoom%0d rotate%0d pixels798720 actual75MHz/133MHz dense_detail_or_average DDR_bubbles/write_yield",z,rot);$finish;
 end
end end end
initial begin
if($value$plusargs("ZOOM=%d",z))begin end
if($value$plusargs("ROTATE=%d",rot))begin end
if(z==1)begin origin_x=101;origin_y=99;end
if(z==2)begin origin_x=640;origin_y=408;end
repeat(12)@(negedge pc);rst=1;
end
initial begin #20000000;$fatal(1,"video watchdog checked%0d",checked);end
endmodule'''.replace('PIXEL',PIXEL)
    modules=['native_line_reader.v','native_line_core.v','native_read_adapter.v','native_downsample2.v','stable_packer.v',
             'stable_model_lane.v','stable_filter4.v','refined_zoom_geometry.v','refined_reset_bridge.v',str(R/'rtl/04_tracking/target_mailbox.v')]
    jobs=[(z,r) for z in ((a.zoom,) if a.zoom is not None else (0,1,2))
                for r in ((a.rotate,) if a.rotate is not None else (0,1))]
    for z,r in jobs:execute(f'video_{z}_{r}',tb,modules,args=[f'+ZOOM={z}',f'+ROTATE={r}'],timeout=1800)
if __name__=='__main__':main()
