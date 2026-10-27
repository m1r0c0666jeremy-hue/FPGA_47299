"""Camera faults must survive startup/calibration/replay footer priorities."""
import argparse
from refined_testlib import R,run
from stage1_test_sources import EXTRA_OSD,OSD_ZERO_NAMED


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--before',action='store_true');a=ap.parse_args()
    # Named defaults deliberately use gain_failed=0: a startup ID failure has
    # no preceding brightness key press and must still name the actual fault.
    defaults=OSD_ZERO_NAMED.replace(".I_ui_mode(2'd0)",'.I_ui_mode(mode)')
    defaults=defaults.replace(".I_gain_failed(1'b0)",'.I_gain_failed(gain_failed)')
    defaults=defaults.replace(".I_tip_reason(4'd0)",".I_tip_reason(4'd2)")
    src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,de=0,gain_failed=0;
reg [1:0] mode=0;reg [17:0] camera=0;reg [767:0] meta=0;
stage1_osd dut(DEFAULTS
 .I_region_draft(168'd0),.I_clk(clk),.I_rst_n(rst),.I_vs(1'b0),.I_hs(1'b0),.I_de(de),
 .I_rgb(24'd0),.I_meta(meta),.I_x0(11'd0),.I_y0(10'd0),.I_zoom(3'd0),.I_mode(2'd0),.I_state(3'd6),
 .I_tracking(1'b0),.I_show(1'b0),.I_video_ok(1'b0),.I_pair(1'b0),.I_detection_valid(1'b0),.I_sample_valid(1'b0),
 .I_rotate(1'b0),.I_diag(2'd0),.I_image_id(32'd0),.I_geometry_commit(1'b0),.I_latency_valid(1'b0),
 .I_latency_us(32'd0),.I_frame_age(32'd0),.I_ddr_diag(128'd0),.I_pixel_diag(128'd0),.I_recovery(39'd0),.I_camera(camera));
reg [359:0] chars=" 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()";
reg [87:0] expected;reg [7:0] ascii;integer fault,m,c,j,n;
task snapshot;begin
 rst=0;de=0;repeat(3)@(negedge clk);rst=1;
 @(negedge clk);dut.y=625;dut.x=0;de=1;
 @(negedge clk);de=0;
 // Changing the live camera word must not change this frame's footer.
 camera={1'b0,4'd9,4'd1,2'd0,7'd90};
 repeat(1500)@(negedge clk);
 if(!dut.footer_ready)$fatal(1,"camera footer deadline");
 for(j=0;j<22;j=j+1)begin
  if(dut.characters[106+j]>=45)$fatal(1,"camera footer glyph");
  ascii=chars[(44-dut.characters[106+j])*8+:8];
  if(ascii!==(j<11?expected[(10-j)*8+:8]:8'd32))
   $fatal(1,"camera fault obscured mode%0d fault%0d char%0d got%c expected%h",mode,fault,j,ascii,expected);
 end
end endtask
initial begin c=0;
// Start with the reported new readback/ID faults, then all camera fault codes.
for(n=0;n<5;n=n+1)begin fault=n==0?4:n==1?5:n-1;
 case(fault)1:expected="CAM NACK   ";2:expected="CAM TIMEOUT";3:expected="VIDEO LOST ";
 4:expected="CFG RD FAIL";5:expected="CAM ID FAIL";endcase
 for(m=0;m<4;m=m+1)begin
  mode=m;meta=0;gain_failed=0;camera={1'b0,4'd9,4'(fault),2'd3,7'd90};snapshot;c=c+1;
 end
end
fault=5;expected="CAM ID FAIL";mode=0;meta[567:565]=1;
camera={1'b0,4'd9,4'd5,2'd3,7'd90};snapshot;c=c+1;
meta=0;fault=4;expected="CFG RD FAIL";gain_failed=1;
camera={1'b0,4'd9,4'd4,2'd3,7'd90};snapshot;c=c+1;
$display("STAGE1_CAMERA_OSD_PASS cases=%0d startup/readback/ID/all-modes/hidden/calibration/snapshot",c);$finish;
end endmodule'''.replace('DEFAULTS',defaults)
    mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('stage1_osd','refined_english_font_rom','refined_english_text_rom','refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry')]
    run('stage1_camera_osd_before' if a.before else 'stage1_camera_osd',src,mods+EXTRA_OSD,
        expected_failure=a.before,timeout=120)


if __name__=='__main__':main()
