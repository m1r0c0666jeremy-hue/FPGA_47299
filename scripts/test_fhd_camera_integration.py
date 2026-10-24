"""Full native FHD camera wrapper, CSI packets through real ISP and packer.

Only the physical DPHY and configuration transport are stubbed. Configuration
ACK/recovery is separately exercised by test_fhd_camera_config.py. The input
contains 1080 real CSI RAW10 packets of 2400 bytes, not predecoded ISP groups.
"""
from refined_testlib import R,run
names=('stable_camera_capture','stable_isp','stable_awb','stable_packer','refined_demosaic','refined_raw_matrix_3x3_buffer','refined_zhenghe','fhd_line_buffer_demosaic','fhd_isp_line_ram','fhd_raw_bridge','refined_reset_bridge','refined_timebase')
mods=[R/f'rtl/color_regions/{n}.v' for n in names]
mods += [R/f'user_source/hdl_source/isp/{n}.v' for n in ('csi_unpacket_2lane','raw10_unpacket_2lane')]
mods += [R/'user_source/hdl_source/isp/demosaic_4x_2_0'/f'{n}.v' for n in ('mipi_to_raw_converter','bilinear_interpolation')]
mods += [next((R/'user_source').rglob('data128_96.v')),R/'rtl/01_camera/camera_status.v']
phy=(R/'user_source/hdl_source/mipi_dphy_rx/mipi_dphy_rx_ph1p_mipiio_wrapper.sv').read_text(encoding='utf-8')
phy=phy[:phy.index(');')+2]+'''reg valid=0;reg [15:0] data=0;
assign O_hs_rx_clk=I_lp_clk;assign O_hs_rx_valid=valid;assign O_hs_rx_data=data;
assign O_lane_error=0;assign O_lane_match_error=0;endmodule'''
cfg=(R/'rtl/color_regions/refined_camera_config.v').read_text(encoding='utf-8')
cfg=cfg[cfg.index('module refined_camera_config'):cfg.index(' localparam BOOT')]
cfg=cfg.replace('output reg','output wire')+'''assign ready=1;assign receiver_enable=1;
assign gain_ack=gain_req;assign parameter_event=0;assign fault=0;assign retries=0;
assign phase=7;assign requested_gain=90;assign applied_gain=90;assign scl=1;assign sda=1'bz;endmodule'''
s=r'''`timescale 1ns/1ps
module tb;
reg rx=0,proc=0,cfgclk=0,rst=0;always #4.167 rx=~rx;always #8.333 proc=~proc;always #20.833 cfgclk=~cfgclk;
wire rv,rs,dv,ds,pv,ps,cap,known;wire [95:0] rawrgb,detectrgb;wire [127:0] packedrgb;
wire [31:0] id,us,now_us,latest;wire [3:0] fault;wire [1:0] retries;
tri sda,cp,cn;tri [3:0] dp,dn;
stable_camera_capture #(.TIMING(1)) dut(
 .I_gain_r(12'd1024),.I_gain_b(12'd1024),.O_raw_rgb(rawrgb),.O_raw_sof(rs),.O_raw_valid(rv),
 .I_control_clk(rx),.I_camera_ref_clk(cfgclk),.I_processing_clk(proc),.I_rst_n(rst),
 .I_gain_req(1'b0),.I_gain_up(1'b0),.O_gain_ack(),.O_cam_scl(),.IO_cam_sda(sda),.O_cam_24m(),.O_cam_rst(),
 .IO_rx_clk_pad_n(cn),.IO_rx_clk_pad_p(cp),.IO_rx_data_pad_n(dn),.IO_rx_data_pad_p(dp),
 .O_detect_rgb(detectrgb),.O_detect_sof(ds),.O_detect_valid(dv),.O_capture_clk(cap),
 .O_rgb128(packedrgb),.O_data_valid(pv),.O_frame_start(ps),.O_status_async(),
 .O_parameter_event(),.O_camera_ready(),.O_camera_fault(fault),.O_camera_retries(retries),.O_camera_phase(),.O_camera_gain(),
 .I_time_gray(32'hb36b2798),.O_source_id(id),.O_source_us(us),.O_now_us(now_us),.O_latest_gray(latest),.O_time_valid(known));
integer rawgroups=0,detectgroups=0,words=0,rawheads=0,detectheads=0,packheads=0;
always @(negedge proc)if(rst)begin
 if(cap!==proc)$fatal(1,"capture output clock remains in PHY domain");
 if(rv)begin rawgroups=rawgroups+1;if(^rawrgb===1'bx)$fatal(1,"unknown RAW RGB");end
 if(dv)begin
  detectgroups=detectgroups+1;
  if(!known || id!=1 || us!=32'hdda24aef)$fatal(1,"wrapper source ID/time %h %h %b",id,us,known);
  if(^detectrgb===1'bx)$fatal(1,"unknown detect RGB");
 end
 if(pv)begin words=words+1;if(^packedrgb===1'bx)$fatal(1,"unknown packed RGB");end
 if(rs)rawheads=rawheads+1;if(ds)detectheads=detectheads+1;if(ps)packheads=packheads+1;
end
task beat;input [15:0] word;begin @(negedge rx);dut.u_mipi_dphy_rx_ph1p_mipiio_wrapper.valid=1;dut.u_mipi_dphy_rx_ph1p_mipiio_wrapper.data=word;end endtask
task stop_packet;begin @(negedge rx);dut.u_mipi_dphy_rx_ph1p_mipiio_wrapper.valid=0;repeat(30)@(negedge rx);end endtask
task short_packet;input [7:0] dt;begin beat({dt,8'd0});beat(16'd0);stop_packet();end endtask
reg [7:0] bytes[0:2399];integer y,x,g,p0,p1,p2,p3;
initial begin
 repeat(10)@(negedge rx);rst=1;repeat(100)@(negedge rx);short_packet(0);
 for(y=0;y<1080;y=y+1)begin
  for(g=0;g<480;g=g+1)begin
   p0=(((y*3+g)%160)+40)*4;p1=(((y*5+g)%160)+40)*4;
   p2=(((y*7+g)%160)+40)*4;p3=(((y*9+g)%160)+40)*4;
   bytes[g*5]=p0>>2;bytes[g*5+1]=p1>>2;bytes[g*5+2]=p2>>2;bytes[g*5+3]=p3>>2;
   bytes[g*5+4]={2'(p3&3),2'(p2&3),2'(p1&3),2'(p0&3)};
  end
  beat({8'h2b,8'h60});beat({8'h09,8'h00});
  for(x=0;x<2400;x=x+2)beat({bytes[x],bytes[x+1]});
  beat(16'd0);stop_packet();repeat(2000)@(negedge rx);
 end
 short_packet(1);repeat(1500)@(negedge proc);
 if(rawgroups!=518400 || detectgroups!=518400 || words!=388800 || rawheads!=1 || detectheads!=1 || packheads!=1)
 $fatal(1,"wrapper full frame counts raw%0d detect%0d words%0d heads%0d/%0d/%0d",rawgroups,detectgroups,words,rawheads,detectheads,packheads);
 if(dut.u_raw_bridge.O_overflows || dut.u_raw_bridge.O_bad_lines || latest!=1 || dut.raw_count!=2073600)
 $fatal(1,"camera frame admission/identity/count diagnostic");
 $display("FHD_CAMERA_INTEGRATION_PASS 1080 actual CSI2400-byte packets -> async line FIFO -> actual RAW/ISP/AWB/packing: 2073600 pixels,388800 words, full32bit original timestamp");$finish;
end
initial begin #50000000;$fatal(1,"watchdog");end
endmodule'''
# The test epoch is deliberately above 2^31 so time metadata cannot accidentally
# pass with a narrowed field. It is independent of the PHY and ISP clocks.
epoch=0xdda24aef
s=s.replace("32'hb36b2798",f"32'h{epoch^(epoch>>1):08x}")
run('fhd_camera_actual_full_frame',s+'\n'+phy+'\n'+cfg,mods,compile_args=['-DFHD_BEHAVIORAL_RAM'])
