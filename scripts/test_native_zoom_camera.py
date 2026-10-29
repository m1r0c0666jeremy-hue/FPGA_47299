"""Real CSI/RAW packets -> native bridge -> full ISP -> dual 720p and dense DDR.

Physical DPHY/configuration transport are modeled here; config readback has a
separate pin-level suite. The actual source rate is 960Mbps/lane, not a slow
sequence of already-decoded ISP groups.
"""
from pathlib import Path
import sys
from test_native_zoom_core import execute
from native_zoom_codegen import template
from refined_testlib import R

def main():
    s=template('camera_integration_tb.sv')
    s=s.replace('stable_camera_capture #','native_camera_capture #')
    s=s.replace('wire rv,rs,dv,ds,pv,ps,cap,known;',
      'wire verdict,legal;wire [31:0] verdict_id;integer verdicts=0,valid_verdicts=0,fault_case=0;wire rv,rs,dv,ds,pv,ps,cap,known;')
    s=s.replace(' .I_gain_r(', " .I_verdict_ready(1'b1),.O_source_verdict(verdict),.O_source_good(legal),.O_verdict_id(verdict_id),\n .I_gain_r(",1)
    s=s.replace(' if(cap!==proc)', ' if(verdict)begin verdicts=verdicts+1;if(legal)valid_verdicts=valid_verdicts+1;if(verdict_id!=1)$fatal(1,"source verdict ID");end\n if(cap!==proc)')
    s=s.replace('2399','3239').replace('y<1080','y<1944').replace('g<480','g<648').replace('x<2400','x<(fault_case && y==1900?3238:3240)')
    s=s.replace("beat({8'h2b,8'h60});beat({8'h09,8'h00});", "beat({8'h2b,8'ha8});beat({8'h0c,8'h00});")
    s=s.replace('repeat(2000)@(negedge rx);','repeat(350)@(negedge rx);')
    s=s.replace('initial begin\n repeat(10)', 'initial begin\n if($value$plusargs("FAULT=%d",fault_case))begin end\n repeat(10)')
    s=s.replace('rawgroups!=518400 || detectgroups!=518400 || words!=388800',
      'rawgroups!=230400 || detectgroups!=230400 || words!=691200')
    a=s.index(' if(dut.u_raw_bridge.O_overflows')
    b=s.index('$finish;',a)+len('$finish;')
    s=s[:a]+''' if(dut.u_raw_bridge.O_overflows || latest!=1 || verdicts!=1 || valid_verdicts!=(fault_case?0:1))
 $fatal(1,"native source qualification overflows%0d bad%0d verdicts%0d good%0d",dut.u_raw_bridge.O_overflows,dut.u_raw_bridge.O_bad_lines,verdicts,valid_verdicts);
 if(!fault_case && (dut.u_raw_bridge.O_bad_lines || dut.full_frame_gate.count!=1259712))$fatal(1,"native full source count");
 if(fault_case && dut.u_raw_bridge.O_bad_lines==0)$fatal(1,"bad row outside ROI was not rejected");
 $display("NATIVE_CAMERA_PASS fault%0d CSI1944/3240-byte-lines/pre921600/post921600/dense691200/tail-source-verdict",fault_case);$finish;'''+s[b:]
    epoch=0xdda24aef
    s=s.replace("32'hb36b2798",f"32'h{epoch^(epoch>>1):08x}")
    phy=(R/'user_source/hdl_source/mipi_dphy_rx/mipi_dphy_rx_ph1p_mipiio_wrapper.sv').read_text(encoding='utf-8')
    phy=phy[:phy.index(');')+2]+'''reg valid=0;reg [15:0] data=0;
assign O_hs_rx_clk=I_lp_clk;assign O_hs_rx_valid=valid;assign O_hs_rx_data=data;
assign O_lane_error=0;assign O_lane_match_error=0;endmodule'''
    cfg=(R/'rtl/color_regions/native_camera_config.v').read_text(encoding='utf-8')
    cfg=cfg[cfg.index('module native_camera_config'):cfg.index(' localparam BOOT')]
    cfg=cfg.replace('output reg','output wire')+'''assign ready=1;assign receiver_enable=1;
assign gain_ack=gain_req;assign parameter_event=0;assign fault=0;assign retries=0;
assign phase=7;assign requested_gain=90;assign applied_gain=90;assign scl=1;assign sda=1'bz;endmodule'''
    names=['native_camera_capture.v','native_csi_guard.v','native_isp.v','native_source_gate.v','native_raw_bridge.v',
      'native_line_ram.v','native_rgb_crop.v','native_downsample2.v','native_demosaic.v','native_raw_matrix.v',
      'native_zhenghe.v','native_line_buffer.v','stable_awb.v','stable_packer.v','refined_reset_bridge.v','refined_timebase.v']
    names += [str(R/'rtl/04_tracking/target_mailbox.v'),str(R/'rtl/01_camera/camera_status.v')]
    names += [str(R/f'user_source/hdl_source/isp/{n}.v') for n in ('csi_unpacket_2lane','raw10_unpacket_2lane')]
    names += [str(R/f'user_source/hdl_source/isp/demosaic_4x_2_0/{n}.v') for n in ('mipi_to_raw_converter','bilinear_interpolation')]
    names += [str(next((R/'user_source').rglob('data128_96.v')))]
    execute('camera_tail_fault' if '--fault' in sys.argv else 'camera_full',s+'\n'+phy+'\n'+cfg,names,
       compile_args=['-DNATIVE_BEHAVIORAL_RAM'],args=['+FAULT=1'] if '--fault' in sys.argv else [],timeout=1800)
if __name__=='__main__':main()
