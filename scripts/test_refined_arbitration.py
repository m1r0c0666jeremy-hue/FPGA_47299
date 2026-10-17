"""Peak camera write traffic against real FIFOs/reader, separate from detection."""
from refined_testlib import R,run
O=R/'build/sim/refined_arbitration';O.mkdir(parents=True,exist_ok=True)
writer=(R/'rtl/color_regions/refined_video_in.v').read_text(encoding='utf-8').replace('module refined_video_in (','module arbitration_video_in #(parameter BW=240)(').replace('burst_count==239','burst_count==BW-1').replace('fifo_count>=240','fifo_count>=BW')
p=O/'writer.v';p.write_bytes(writer.encode('utf-8'))
s=r'''`timescale 1ns/1ps
module tb;
reg cc=0,dc=0,pc=0,rst=0;always #8.334 cc=~cc;always #7.5 dc=~dc;always #6.667 pc=~pc;
reg cs=0,cv=0;wire wr,wb,rb,re,ready,ovf;wire [24:0] wa,ra;wire [127:0] wd;
arbitration_video_in #(.BW(BW)) writer(.I_rst_n(rst),.I_camera_clk(cc),.I_camera_frame_start(cs),.I_camera_frame_id(32'd1),.I_camera_valid(cv),.I_camera_data({16{8'h30}}),.I_mipi_rx_error(1'b0),.I_ddr_clk(dc),.I_display_pause(1'b0),.I_video_out_rd_busy(rb),.O_video_in_wr_busy(wb),.O_capture_overflow(ovf),.O_ddr_user_wr_en(wr),.O_ddr_user_addr(wa),.O_ddr_user_wr_data(wd),.I_ddr_user_ready(ready),.I_frame_us(32'd0),.I_epoch(16'd0),.I_time_valid(1'b1));
wire app,wren,unexpected;wire [2:0] cmd;wire [24:0] addr;wire [31:0] accepted;wire [9:0] outstanding;integer tick=0;reg ret=0;
wire ardy=cmd[0]?(tick%19!=0 && tick%23!=0):tick%13!=0;
refined_mc_to_user_interface adapter(.I_clk(dc),.I_rst_n(rst),.I_ddr_user_wr_en(wr),.I_ddr_user_rd_en(re),.I_ddr_user_addr(wr?wa:ra),.I_ddr_user_wr_data(wd),.O_ddr_user_ready(ready),.O_mc_app_en(app),.O_mc_app_addr(addr),.O_mc_app_cmd(cmd),.I_mc_app_rdy(ardy),.O_mc_app_wdf_wren(wren),.I_mc_app_wdf_rdy(tick%7!=0),.I_mc_app_rd_data({16{8'h30}}),.I_mc_app_rd_data_end(ret),.I_mc_app_rd_data_valid(ret),.O_unexpected_return(unexpected),.O_outstanding_reads(outstanding),.O_accepted_reads(accepted));
integer due[0:2047],head=0,tail=0;
always @(posedge dc)if(rst && app && cmd[0] && ardy)begin due[tail]=tick+37;tail=(tail+1)%2048;end
always @(negedge dc)begin tick=tick+1;ret=0;if(head!=tail && due[head]<=tick)begin ret=1;head=(head+1)%2048;end end
integer h=0,v=725,count=0;reg vs_old=0,commit=0;integer countdown=0;
reg overloaded=0,verify_recovered=0,stop_capture=0;
wire vs=v>=725 && v<730,hs=h>=1390 && h<1430,de=v<720 && h<1280;
wire os,oh,od,ok;wire [23:0] rgb;wire [127:0] pd,dd;
refined_line_reader reader(commit,1'b1,rst,dc,wb,wr,2'd2,32'd1,128'd0,ready,ret,{16{8'h30}},rb,re,ra,pc,vs,hs,de,11'd0,10'd48,3'd0,os,oh,od,rgb,,ok,1'b0,1'b1,,dd,pd,accepted,unexpected);
integer ox=0,oy=0;reg old_os=0;
always @(negedge pc)if(rst)begin
if(os && !old_os)begin ox=0;oy=0;if(overloaded)begin verify_recovered=1;count=0;end end old_os=os;
if(od)begin if(oy<624)begin
if(!ok)begin
if(!RECOVER || verify_recovered)$fatal(1,"ARBITRATION_UNDERRUN BW%0d xy%0d/%0d ready%b sy%0d joby%0d state%0d wrbusy%b DD%h PD%h",BW,ox,oy,reader.ready,reader.sy,reader.job_y,reader.state,wb,dd,pd);
if(!overloaded)begin $display("ARBITRATION_OVERLOAD_DETECTED xy%0d/%0d cause%0d",ox,oy,pd[3:0]);$fflush();overloaded=1;stop_capture=1;end
end
if(!overloaded || verify_recovered)begin if(rgb!==24'h303030)$fatal(1,"RGB changed");count=count+1;end end
if(ox==1279)begin ox=0;oy=oy+1;end else ox=ox+1;
if(oy==624 && (!RECOVER || verify_recovered))begin if(count!=798720 || ovf || unexpected || (RECOVER && !overloaded))$fatal(1,"traffic coverage/overflow");$display("ARBITRATION_PASS BW%0d full recovered image798720, overload%0d, real FIFO independent PAXI ready",BW,overloaded);$finish;end end
commit=0;if(vs && !vs_old)countdown=20;else if(countdown>0)begin countdown=countdown-1;if(countdown==1)commit=1;end vs_old=vs;
if(h==1649)begin h=0;v=v==749?0:v+1;end else h=h+1;
end
integer f,n;
initial begin repeat(12)@(negedge cc);rst=1;for(f=0;f<3;f=f+1)begin for(n=0;n<230400;n=n+1)begin @(negedge cc);cs=n==0 && !stop_capture;cv=n%4!=3 && !stop_capture;end @(negedge cc);cs=0;cv=0;repeat(260000)@(negedge cc);end end
initial begin #50000000;$fatal(1,"arbitration timeout");end
endmodule'''
mods=[p,*[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_line_reader','stable_model_lane','stable_filter4','refined_reset_bridge','refined_zoom_geometry','refined_mc_to_user_interface')],R/'rtl/04_tracking/target_mailbox.v']
mods += [R/'user_source/ip_source'/n for n in ('w128_d512_fifo/w128_d512_fifo.v','w128_d512_fifo/soft_fifo_al_4057d6b76aa6.v','w155_d512_fifo/w155_d512_fifo.v','w155_d512_fifo/soft_fifo_al_f58e8b3e1f3d.v')]
import sys
bw=int(sys.argv[1]) if len(sys.argv)>1 else 240
recover='--recover' in sys.argv
run(f'arbitration_bw{bw}'+('_recover' if recover else ''),s.replace('module tb;',f'module tb;localparam BW={bw},RECOVER={int(recover)};'),mods,timeout=1200)
