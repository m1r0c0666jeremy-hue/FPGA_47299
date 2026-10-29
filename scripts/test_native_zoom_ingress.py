"""691200 dense writes through actual capture/command FIFOs, ID and time pairing."""
from refined_testlib import R
from test_native_zoom_core import execute

def main():
 tb=r'''`timescale 1ns/1ps
module tb;
reg cc=0,dc=0,rst=0,sof=0,v=0;always #8.333 cc=~cc;always #3.75 dc=~dc;
reg [127:0] data=0;wire wr,wb,ovf,beg;wire [1:0] bank;wire [31:0] id,stamp;wire [15:0] epoch;wire time_ok;wire [24:0] addr;wire [127:0] payload;
reg [31:0] fid=1;integer cycle=0;wire ready=cycle%13!=0;wire rb=cycle%1000>=600 && cycle%1000<840 && !wb;
refined_video_in writer(.I_rst_n(rst),.I_camera_clk(cc),.I_camera_frame_start(sof),.I_camera_frame_id(fid),
.O_frame_begin(beg),.O_frame_bank(bank),.O_frame_id(id),.O_capture_overflow(ovf),.I_camera_valid(v),.I_camera_data(data),.I_mipi_rx_error(1'b0),
.I_ddr_clk(dc),.I_display_pause(1'b0),.I_video_out_rd_busy(rb),.O_video_in_wr_busy(wb),.O_ddr_user_wr_en(wr),.O_ddr_user_addr(addr),.O_ddr_user_wr_data(payload),.I_ddr_user_ready(ready),
.I_frame_us(32'd123456),.I_epoch(16'd9),.I_time_valid(1'b1),.O_frame_us(stamp),.O_epoch(epoch),.O_time_valid(time_ok));
wire selected,ss;wire [851:0] view;reg result=0,snap=0,verdict=0;reg [767:0] meta=0;
native_frame_store #(.V4(1)) store(dc,rst,beg,bank,id,wr,addr,result,meta,snap,10'd0,ss,view,selected,stamp,epoch,time_ok,ovf,verdict,1'b1,fid);
function [127:0] pattern(input integer n);pattern={32'hbedabeda,32'(n),32'(n^32'hff00ff),32'(n+17)};endfunction
integer n,writes=0;reg [24:0] base;
always @(posedge dc)if(rst)begin cycle=cycle+1;
if(beg)begin base=bank==0?0:bank==1?7000000:bank==2?14000000:21000000;if(id!=fid || stamp!=123456 || epoch!=9 || !time_ok)$fatal(1,"writer identity/time freeze");end
if(wr)begin if(payload!==pattern(writes) || addr!==base+writes*8)$fatal(1,"dense write order %0d %0d",writes,addr);writes=writes+1;end
if(ovf)$fatal(1,"native packing rate overflow");end
initial begin repeat(6)@(negedge cc);rst=1;repeat(8)@(negedge cc);
sof=1;@(negedge cc);sof=0;
for(n=0;n<691200;n=n+1)begin
v=1;data=pattern(n);@(negedge cc);
if(n%3==2)begin v=0;@(negedge cc);end
if(n%480==479)begin v=0;repeat(400)@(negedge cc);end
end
v=0;repeat(3000)@(negedge cc);
if(writes!=691200)$fatal(1,"dense count %0d",writes);
snap=1;@(negedge dc);snap=0;@(negedge dc);if(view[802] || selected)$fatal(1,"unqualified dense image published");
meta[31:0]=fid;meta[255]=1;meta[415:413]=4;meta[671:640]=123456;meta[719:704]=9;meta[720]=1;
result=1;verdict=1;@(negedge dc);result=0;verdict=0;repeat(3)@(negedge dc);snap=1;@(negedge dc);snap=0;@(negedge dc);
if(!view[802] || !selected || view[31:0]!=fid || view[671:640]!=123456 || view[719:704]!=9)$fatal(1,"dense/meta/source association");
$display("NATIVE_INGRESS_PASS actualFIFO/dense691200/60MHz_133MHz/congestion/identity/source_qualification");$finish;end
initial begin #40000000;$fatal(1,"watchdog");end endmodule'''
 mods=['refined_video_in.v','native_frame_store.v','refined_reset_bridge.v']
 mods += [str(R/'user_source/ip_source'/n) for n in ('w128_d512_fifo/w128_d512_fifo.v','w128_d512_fifo/soft_fifo_al_4057d6b76aa6.v')]
 execute('ingress',tb,mods,timeout=1800)
if __name__=='__main__':main()
