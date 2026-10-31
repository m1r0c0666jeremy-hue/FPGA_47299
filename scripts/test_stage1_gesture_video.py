from pathlib import Path
import sys,re
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
s=(R/'rtl/color_regions/stage1_memory_video_out.v').read_text(encoding='utf-8')
expr=re.search(r'wire viewport_abort=(.*);',s)[1]
event=re.search(r'wire viewport_reprepare=(.*);',s)[1]
tb=r'''`timescale 1ns/1ps
module tb;
reg pc=0,dc=0,rst=0;always #6.667 pc=~pc;always #7.5 dc=~dc;
reg vs=0,de=0,snapshot=0;reg [851:0] packet=0;
reg I_key_cancel=0,I_key4=0,I_camera_ready=1,I_gain_busy=0;reg [1:0] I_ui_mode=3,viewport_ui_last=3;
wire [1:0] abort={EVENT,EXPR};
always @(posedge pc)viewport_ui_last<=I_ui_mode;
wire [1:0] good,health;wire [3:0] why[0:1];wire [127:0] diag[0:1];genvar g;
generate for(g=0;g<2;g=g+1)begin:d
 wire commit;wire [31:0] id,us;wire [15:0] epoch;wire tv;wire [767:0] meta;
 wire [10:0] x0;wire [9:0] y0;wire [1:0] bank;wire [2:0] zoom;wire rotate,ode;
 if(g==0)begin
 stage1_viewport #(.V4(1)) view(.I_clk(pc),.I_rst_n(rst),.I_vs(vs),.I_de(de),.I_snapshot(snapshot),.I_data(packet),
 .I_tracking(1'b1),.I_show(1'b1),.I_conflict(1'b0),.I_live(good[g]),.I_session(8'd1),.I_zoom(3'd0),.I_mode(2'd0),.I_pair(1'b0),.I_rotate(1'b0),.I_point(39'd0),.I_abort(abort),
 .O_commit(commit),.O_frame_id(id),.O_image_us(us),.O_epoch(epoch),.O_time_valid(tv),.O_meta(meta),.O_x0(x0),.O_y0(y0),.O_zoom(zoom),.O_rotate(rotate),.O_bank(bank));
 end else begin
 reference_stage1_viewport #(.V4(1)) view(.I_clk(pc),.I_rst_n(rst),.I_vs(vs),.I_de(de),.I_snapshot(snapshot),.I_data(packet),
 .I_tracking(1'b1),.I_show(1'b1),.I_conflict(1'b0),.I_live(good[g]),.I_session(8'd1),.I_zoom(3'd0),.I_mode(2'd0),.I_pair(1'b0),.I_rotate(1'b0),.I_point(39'd0),
 .O_commit(commit),.O_frame_id(id),.O_image_us(us),.O_epoch(epoch),.O_time_valid(tv),.O_meta(meta),.O_x0(x0),.O_y0(y0),.O_zoom(zoom),.O_rotate(rotate),.O_bank(bank));
 end
 wire re;reg rv=0;reg [31:0] accepted=0;
 always @(posedge dc)if(rst && re)accepted<=accepted+1'b1;
 always @(negedge dc)rv<=re;
 refined_line_reader reader(.I_frame_commit(commit),.I_selected_good(1'b1),.I_rst_n(rst),.I_ddr_clk(dc),.I_write_busy(1'b0),.I_write_en(1'b0),
 .I_read_buffer(bank),.I_frame_id(id),.I_models(128'd0),.I_ddr_ready(1'b1),.I_ddr_valid(rv),.I_ddr_data({16{8'h30}}),.O_read_en(re),
 .I_pixel_clk(pc),.I_vs(vs),.I_hs(1'b0),.I_de(de),.I_x0(x0),.I_y0(y0),.I_zoom(zoom),.I_rotate(rotate),.I_stream_n(rst),.I_accepted_reads(accepted),.I_unexpected_return(1'b0),
 .O_de(ode),.O_video_ok(good[g]),.O_pixel_diag(diag[g]));
 wire associated=meta[255] && meta[247] && meta[31:0]==id && meta[719:704]==epoch && meta[671:640]==us && tv;
 stage1_teach_image_guard guard(pc,rst,rst,I_camera_ready,I_gain_busy,good[g],ode,associated,id,health[g],why[g]);
 end endgenerate
integer f;
initial begin repeat(5)@(negedge pc);rst=1;repeat(10)@(negedge pc);
for(f=1;f<=8;f=f+1)begin
 de=0;I_camera_ready=1;I_gain_busy=0;repeat(16)@(negedge pc);vs=1;@(negedge pc);vs=0;@(negedge pc);
 packet=0;packet[31:0]=f;packet[32]=1;packet[89:79]=640;packet[99:90]=360;packet[242:235]=1;packet[244]=1;packet[247]=1;packet[255]=1;
 packet[415:413]=4;packet[671:640]=f*16000;packet[719:704]=7;packet[720]=1;
 packet[799:768]=f;packet[802]=1;packet[834:803]=f*16000;packet[850:835]=7;packet[851]=1;snapshot=1;
 @(negedge pc);snapshot=0;@(negedge pc);I_key_cancel=(f==2);I_key4=(f==3);I_ui_mode=(f==4)?2:3;I_camera_ready=(f!=5);I_gain_busy=(f==7);@(negedge pc);I_key_cancel=0;I_key4=0;
 repeat(12000)@(negedge pc);de=1;repeat(32)@(negedge pc);
 $display("GESTURE_FRAME f%0d video%h health%h reason%0d/%0d diag%0d/%0d",f,good,health,why[0],why[1],diag[0][3:0],diag[1][3:0]);
 if(f==5 || f==7)begin
 if(health!==0 || why[0]!=(f==5?2:6))$fatal(1,"real fault was hidden");end
 else begin
 if(good[1]!==1'b1 || health[1]!==1'b1)$fatal(1,"reference setup failed");
 if(good[0]!==1'b1 || health[0]!==1'b1)$fatal(1,"gesture became missing image/record fault");end
 de=0;repeat(16)@(negedge pc);
end
$display("STAGE1_GESTURE_VIDEO_PASS actual-reader/guard eightframes/gesture/key4/mode/camera/gain/recovery");$finish;end endmodule'''.replace('EXPR',expr).replace('EVENT',event)
rtl=R/'rtl/color_regions'
mods=[rtl/n for n in ['stage1_regions.v','stage1_sequence.v','stage1_memory_video_out.v','refined_zoom_geometry.v','refined_line_reader.v','stable_model_lane.v','stable_filter4.v','refined_reset_bridge.v']]+[R/'rtl/04_tracking/target_mailbox.v',R/'sim/stage1_viewport_before_retime.v']
run('stage1_gesture_video',tb,mods,timeout=120)
