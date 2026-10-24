"""CSI packets -> actual camera + memory wrapper -> HDMI encoder input.

Only sensor/PHY, configuration ACK transport, DDR controller and encrypted HDMI
encoder/serializer are modeled. Own reset, recovery, CDC, timing and video
wrappers are included. Verify uniform RAW scenes independently at HDMI pixels,
then recover from a DDR ready loss and a short CSI frame.
"""
from refined_testlib import R
from refined_native_testlib import run_native

camera=(R/'scripts/test_fhd_camera_integration.py').read_text(encoding='utf-8')
ns={};exec(compile(camera[:camera.rindex("\nrun(")],'camera fixture definitions','exec'),ns)
mods=list(ns['mods']);cfg=ns['cfg'];phy=ns['phy']
phy=phy[:phy.index('reg valid=0;')]+'''assign O_hs_rx_clk=tb.rx;
assign O_hs_rx_valid=tb.phy_valid;assign O_hs_rx_data=tb.phy_data;
assign O_lane_error=0;assign O_lane_match_error=0;endmodule'''
rtl=R/'rtl/color_regions'
names=('stable_memory_video_out','stable_capture','stable_model_lane','stable_filter4','stable_grid','regions_divide','stable_tracker',
       'stable_display','stable_preprocess','refined_frame_store','refined_video_in','refined_line_reader','refined_mc_to_user_interface',
       'refined_ddr_recovery','refined_ph1p35_ddr_wrapper','refined_zoom_geometry','refined_overlay_geometry','refined_performance','fhd_vtc',
       'refined_osd','refined_logo_rom','refined_footer_program_rom','refined_english_font_rom','refined_english_text_rom')
mods += [rtl/(n+'.v') for n in names]+[R/'rtl/04_tracking/target_mailbox.v']
mods += [R/'user_source/ip_source'/n for n in ('w128_d512_fifo/w128_d512_fifo.v','w128_d512_fifo/soft_fifo_al_4057d6b76aa6.v',
                                               'w155_d512_fifo/w155_d512_fifo.v','w155_d512_fifo/soft_fifo_al_f58e8b3e1f3d.v')]
for n in ('hdmi_tx.v','audio_arc_calculate.v','key_remove_shakes.v','I2S_receiver.v'):
    mods.append(next((R/'user_source').rglob(n)))
mods=list(dict.fromkeys(mods))

def header(path,marker=');'):
    s=path.read_text(encoding='utf-8');return s[:s.index(marker)+len(marker)]
ddr=header(R/'ip/refined_ddr2/ddr2.v').replace('`timescale 1ps/1ps','`timescale 1ns/1ps')+r'''
reg clk=0;always #7.5 clk=~clk;assign dhi_clk=clk;
assign ddrphy_rdy=sys_rst_n && !tb.ddr_unavailable;
integer cycle=0,awh=0,awt=0,wh=0,wt=0,rh=0,rt=0;
integer awq[0:4095],rq[0:4095],due[0:4095];reg [127:0] wq[0:4095];
reg [127:0] memory[0:1555199];reg [127:0] rdata=0;reg rv=0;
assign paxi_awready=ddrphy_rdy && cycle%13!=0;
assign paxi_wready=ddrphy_rdy && cycle%7!=0;
assign paxi_arready=ddrphy_rdy && cycle%19!=0;
assign paxi_rdata=rdata;assign paxi_rvalid=rv;assign paxi_rlast=rv;
function integer index(input integer address);
index=(address/7000000)*388800+(address%7000000)/8;endfunction
always @(posedge clk)begin
 cycle=cycle+1;rv<=0;
 if(!sys_rst_n)begin awh=0;awt=0;wh=0;wt=0;rh=0;rt=0;end
 else begin
 if(paxi_awvalid && paxi_awready)begin awq[awt]=index(paxi_awaddr);awt=(awt+1)%4096;end
 if(paxi_wvalid && paxi_wready)begin wq[wt]=paxi_wdata;wt=(wt+1)%4096;end
 if(awh!=awt && wh!=wt)begin memory[awq[awh]]=wq[wh];awh=(awh+1)%4096;wh=(wh+1)%4096;end
 if(paxi_arvalid && paxi_arready)begin rq[rt]=index(paxi_araddr);due[rt]=cycle+37;rt=(rt+1)%4096;end
 if(rh!=rt && due[rh]<=cycle && ddrphy_rdy)begin rv<=1;rdata<=memory[rq[rh]];rh=(rh+1)%4096;end
 end
end
endmodule
'''
core=header(R/'user_source/hdl_source/hdmi_1_4b_transmitter_core_wrapper.enc.v')+r'''
assign O_axis_s_ready=1;
initial if(HTOTAL!=2200 || HACTIVE!=1920 || VTOTAL!=1125 || VACTIVE!=1080 || VIDEO_VIC!=34)
 $fatal(1,"HDMI encoder profile must be VIC34/1080p30");
always @(negedge I_pixel_clk)if(!I_rst)tb.observe(I_axis_s_user,I_axis_s_valid,I_axis_s_last,I_axis_s_data);
endmodule
'''
hdmiphy=header(R/'user_source/hdl_source/hdmi_phy_warpper.v')+'\nendmodule\n'
source=r'''`timescale 1ns/1ps
module tb;
reg rx=0,proc=0,pc=0,sys=0,cfgclk=0,rst=0;
always #4.167 rx=~rx;always #8.333 proc=~proc;always #6.734006734 pc=~pc;
always #10 sys=~sys;always #20.833 cfgclk=~cfgclk;
reg phy_valid=0;reg [15:0] phy_data=0;reg ddr_unavailable=0;
wire [95:0] drgb;wire ds,dv,pv,ps,cap,known;wire [127:0] packedrgb;
wire [31:0] id,stamp,capnow,latest,nowus,timegray;wire ready,event_toggle;
tri sda,cp,cn;tri [3:0] dp,dn;
refined_timebase timebase(pc,rst,nowus,timegray);
stable_camera_capture #(.TIMING(1)) cam(
 .I_gain_r(12'd1024),.I_gain_b(12'd1024),.I_control_clk(sys),.I_camera_ref_clk(cfgclk),.I_processing_clk(proc),.I_rst_n(rst),
 .I_gain_req(1'b0),.I_gain_up(1'b0),.IO_cam_sda(sda),.IO_rx_clk_pad_n(cn),.IO_rx_clk_pad_p(cp),.IO_rx_data_pad_n(dn),.IO_rx_data_pad_p(dp),
 .O_detect_rgb(drgb),.O_detect_sof(ds),.O_detect_valid(dv),.O_capture_clk(cap),.O_rgb128(packedrgb),.O_data_valid(pv),.O_frame_start(ps),
 .O_parameter_event(event_toggle),.O_camera_ready(ready),.I_time_gray(timegray),.O_source_id(id),.O_source_us(stamp),.O_now_us(capnow),.O_latest_gray(latest),.O_time_valid(known));
stable_memory_video_out video(
 .I_source_id(id),.I_source_us(stamp),.I_capture_us(capnow),.I_board_us(nowus),.I_latest_gray(latest),.I_source_time_valid(known),.I_model_state(2'd0),.I_quality(42'd0),
 .I_camera_event(event_toggle),.I_camera_ready(ready),.I_camera_status(18'd0),.I_sys_clk(sys),.I_rst_n(rst),.I_process_rst_n(rst),
 .I_process_mode(2'd0),.I_zoom(3'd0),.I_rotate(1'b0),.I_diag(2'd0),.I_pair(1'b0),.I_tracking(1'b0),.I_show(1'b0),.I_conflict(1'b0),.I_session(8'd1),
 .I_detect_rgb(drgb),.I_detect_sof(ds),.I_detect_valid(dv),.I_models(128'd0),.I_revision(16'd0),.I_gains(24'h400400),.I_cal_status(8'd0),
 .I_cal_active(1'b0),.I_needs_cal(1'b0),.I_frame_pair(1'b0),.I_pixel_clk(pc),.I_serial_clk(pc),.I_capture_clk(cap),.I_rgb128(packedrgb),.I_data_valid(pv),.I_frame_start(ps),.I_debug_status(4'd0));
integer ox=0,oy=0,frames=0,pixels=0,complete=0,after_recovery=0,footers=0;
integer nonzero=0,black=0;reg started=0;reg [23:0] frame_color=0;
task observe(input user,valid,last,input [23:0] rgb);begin
 if(user)begin
  if(started)begin
   if(pixels!=2073600 || ox!=0 || oy!=1080)$fatal(1,"HDMI incomplete frame %0d pixels%0d xy%0d/%0d",frames,pixels,ox,oy);
   if(nonzero==1889280 && black==0)begin complete=complete+1;if(frame_color==24'h707070 && frames>=12)after_recovery=after_recovery+1;end
   $display("CAMERA_HDMI_FRAME %0d live%0d black%0d color%h",frames,nonzero,black,frame_color);$fflush();
  end
  started=1;ox=0;oy=0;pixels=0;nonzero=0;black=0;frame_color=0;frames=frames+1;
  if(frames==18)begin
   if(complete<8 || after_recovery<3 || footers<1000)$fatal(1,"missing recovered full image/OSD coverage %0d %0d %0d",complete,after_recovery,footers);
   $display("FHD_CAMERA_HDMI_PASS actualCSI/camera/ISP/wrappers/DDR/HDMI stream, %0d complete images, %0d recovered images, footer present",complete,after_recovery);$finish;
  end
 end
 if(started && valid)begin
  if(oy<984)begin
   if(rgb==0)black=black+1;
   else begin
    if(rgb!=24'h505050 && rgb!=24'h707070)$fatal(1,"CSI to HDMI pixel mismatch frame%0d xy%0d/%0d got%h",frames,ox,oy,rgb);
    if(frame_color==0)frame_color=rgb;
    if(rgb!=frame_color)$fatal(1,"mixed source scenes within displayed frame");
    nonzero=nonzero+1;
   end
  end else if(rgb!=0)footers=footers+1;
  pixels=pixels+1;if(ox==1919)begin ox=0;oy=oy+1;end else ox=ox+1;
 end
end endtask
task beat(input [15:0] word);begin @(negedge rx);phy_valid=1;phy_data=word;end endtask
task stop_packet;begin @(negedge rx);phy_valid=0;repeat(30)@(negedge rx);end endtask
task short_packet(input [7:0] dt);begin beat({dt,8'd0});beat(16'd0);stop_packet;end endtask
integer f,y,x;reg [7:0] level;
initial begin
 repeat(10)@(negedge rx);rst=1;repeat(100)@(negedge rx);
 for(f=1;f<=22;f=f+1)begin
  if(f==7)ddr_unavailable=1;
  level=f>=7?8'h70:8'h50;
  short_packet(0);
  for(y=0;y<(f==10?500:1080);y=y+1)begin
   beat({8'h2b,8'h60});beat(16'h0900);
   for(x=0;x<480;x=x+1)begin
    // RAW10 groups: four equal 8-bit MSBs and four zero 2-bit LSBs.
    if(x%2==0)begin beat({level,level});beat({level,level});end
    else begin beat({8'd0,level});beat({level,level});beat({level,8'd0});end
   end
   beat(0);stop_packet;repeat(2000)@(negedge rx);
   if(f==7 && y==100)ddr_unavailable=0;
  end
  short_packet(1);repeat(f==10?2380000:510000)@(negedge rx);
 end
end
initial begin #800000000;$fatal(1,"CSI to HDMI watchdog");end
endmodule
'''
run_native('fhd_camera_hdmi_recovery',source+'\n'+phy+'\n'+cfg+'\n'+ddr+'\n'+core+'\n'+hdmiphy,mods,
           compile_args=['-I'+str(rtl),'-DFHD_BEHAVIORAL_RAM'],timeout=1800)
