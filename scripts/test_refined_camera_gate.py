"""Camera wrapper admits only whole frames after ready; checks monitor counts.

ISP/MIPI IP are omitted; their stream boundaries are driven explicitly. Their
numerical datapaths and vendor FIFO are checked by separate regression fixtures.
"""
from refined_testlib import R,run
src=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,ready=0,sof=0,v=0;
reg [3:0] sp=0,vp=0;always @(posedge clk)begin sp<={sp[2:0],sof};vp<={vp[2:0],v};end
wire detect_sof=sp[1],detect_valid=vp[1],packed_sof=sp[3],packed_valid=vp[3];
wire rawsof,rawvalid,ds,dv,ps,pv;wire [95:0] rgb,detect;wire [127:0] packedrgb;wire [3:0] status;
stable_camera_capture dut(.I_gain_r(12'd1024),.I_gain_b(12'd1024),.O_raw_rgb(rgb),.O_raw_sof(rawsof),.O_raw_valid(rawvalid),
.I_control_clk(clk),.I_camera_ref_clk(clk),.I_rst_n(rst),.I_gain_req(1'b0),.I_gain_up(1'b0),.O_detect_rgb(detect),.O_detect_sof(ds),.O_detect_valid(dv),
.O_rgb128(packedrgb),.O_data_valid(pv),.O_frame_start(ps),.O_status_async(status));
task group(input integer first);begin @(negedge clk);sof=first;v=1;end endtask
task no_forward;begin if(rawvalid || rawsof || dv || ds || pv || ps)$fatal(1,"unready or partial frame escaped");end endtask
integer j;reg old_complete;
initial begin
force dut.S_csi_rx_clk=clk;force dut.receiver_enable=1'b1;force dut.O_camera_ready=ready;
force dut.raw_rgb_internal=96'h804020804020804020804020;force dut.raw_sof_internal=sof;force dut.raw_valid_internal=v;
force dut.detect_sof_internal=detect_sof;force dut.detect_valid_internal=detect_valid;force dut.S_ISP_O_tuser=packed_sof;force dut.S_ISP_O_tvalid=packed_valid;
repeat(8)@(negedge clk);rst=1;repeat(8)@(negedge clk);old_complete=dut.complete_toggle;
group(1);for(j=1;j<230400;j=j+1)begin group(0);no_forward;end
group(1);group(0);if(dut.complete_toggle==old_complete)$fatal(1,"complete-frame monitor missing");
ready=1;repeat(8)@(negedge clk);no_forward;
group(1);#1;if(!rawsof || !rawvalid)$fatal(1,"ready whole frame not admitted");group(0);repeat(8)@(negedge clk);if(!pv || !dv)$fatal(1,"downstream gates not admitted");
ready=0;repeat(8)@(negedge clk);no_forward;ready=1;repeat(8)@(negedge clk);no_forward;
group(1);group(0);repeat(8)@(negedge clk);if(!pv || !dv)$fatal(1,"next complete boundary not restored");
$display("REFINED_CAMERA_GATE_PASS full-source monitor, no pre-ready output, gain/restart truncates frame, re-ready waits for fresh SOF");$finish;end endmodule'''
run('camera_frame_admission',src,[R/'rtl/color_regions'/f'{n}.v' for n in ('stable_camera_capture','refined_camera_config','refined_reset_bridge')],compile_args=['-i'])
