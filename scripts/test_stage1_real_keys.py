"""Real debounce and production display/reader across normal frame blanking."""
from refined_testlib import R, run
import argparse

BASE = r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [2:0] keys=7;
reg frames=1;integer phase=0,n=0;reg vs=0,snapshot=0;reg [851:0] packet=0;
reg [10:0] px=100;reg [9:0] py=100;reg [31:0] stamp;
wire tracking,show,pair,rotate,down,c2,c3,c4,cancel,gb;wire [7:0] session;wire [1:0] mode;
wire [2:0] zoom,az;wire commit,video_ok,detection,reader_de,ar,time_ok;wire [1:0] bank;
wire [31:0] image,image_us;wire [15:0] epoch;wire [767:0] meta;wire [10:0] x0;wire [9:0] y0;
wire [3:0] nd,ee;wire live;integer downs=0,clicks=0,cancels=0,blankings=0;reg was_pending=0;
stage1_controls #(.CYCLES_PER_MS(4)) controls(.I_clk(clk),.I_rst_n(rst),.I_keys_n(keys),
.I_ui_switch(2'd1),.I_gain_ack(1'b0),.I_cal_status(8'd0),.I_pause(1'b0),.I_camera({1'b1,4'd7,4'd0,2'd0,7'd90}),
.O_tracking(tracking),.O_show(show),.O_session(session),.O_pair(pair),.O_rotate(rotate),.O_zoom(zoom),
.O_ui_mode(mode),.O_down2(down),.O_click2(c2),.O_click3(c3),.O_click4(c4),.O_cancel(cancel),.O_gain_busy(gb));
always @(negedge clk)if(rst && frames)begin
 phase=(phase+1)%64;vs=phase<4;snapshot=phase==2;
 if(snapshot)begin n=n+1;stamp=n*16000;packet=0;packet[31:0]=n;packet[32]=1;
 packet[89:79]=px;packet[99:90]=py;packet[242:235]=session;packet[243]=pair;packet[244]=tracking;
 packet[247]=1;packet[255]=1;packet[415:413]=4;packet[559:544]=16'h1234;
 packet[671:640]=stamp;packet[703:672]=stamp;packet[719:704]=7;packet[720]=1;
 packet[799:768]=n;packet[802]=1;packet[834:803]=stamp;packet[850:835]=7;packet[851]=1;end
end else begin vs=0;snapshot=0;end
stable_display #(.V4(1)) view(.I_clk(clk),.I_rst_n(rst),.I_vs(vs),.I_de(1'b0),.I_snapshot(snapshot),.I_data(packet),
.I_tracking(tracking),.I_show(show),.I_conflict(1'b0),.I_live(video_ok),.I_session(session),.I_zoom(zoom),.I_mode(2'd0),
.I_pair(pair),.I_rotate(rotate),.O_commit(commit),.O_bank(bank),.O_frame_id(image),.O_x0(x0),.O_y0(y0),
.O_zoom(az),.O_rotate(ar),.O_meta(meta),.O_detection_valid(detection),.O_image_us(image_us),.O_epoch(epoch),.O_time_valid(time_ok));
refined_line_reader reader(.I_frame_commit(commit&&time_ok),.I_selected_good(1'b1),.I_rst_n(rst),.I_ddr_clk(clk),
.I_write_busy(1'b1),.I_write_en(1'b0),.I_read_buffer(bank),.I_frame_id(image),.I_models(meta[543:416]),
.I_ddr_ready(1'b0),.I_ddr_valid(1'b0),.I_ddr_data(128'd0),.I_pixel_clk(clk),.I_vs(vs),.I_hs(1'b0),.I_de(1'b0),
.I_x0(x0),.I_y0(y0),.I_zoom(az),.I_rotate(ar),.I_stream_n(rst),.I_accepted_reads(32'd0),.I_unexpected_return(1'b0),
.O_video_ok(video_ok),.O_de(reader_de));
GUARD
stage1_regions #(.CYCLES_PER_MS(4)) regions(.clk(clk),.rst_n(rst),.mode(mode),.down2(down),.click2(c2),.click3(c3),
.click4(c4),.cancel(cancel),.tracking(tracking),.video_ok(REGION_VIDEO),.camera_ready(1'b1),.gain_busy(gb),.session(session),
.pair(pair),.frame_commit(commit),.detection_valid(REGION_ASSOC),.image_id(image),.meta(meta),.draft_count(nd),.edit_error(ee),.tip_live(live));
always @(posedge clk)if(rst)begin
 if(down)begin downs=downs+1;px<=105;py<=105;end
 if(c2)clicks=clicks+1;if(cancel)cancels=cancels+1;
 if(regions.point_pending)was_pending=1;if(vs&&!video_ok)blankings=blankings+1;
end
task ms;input integer k;begin repeat(4*k)@(negedge clk);end endtask
initial begin repeat(4)@(negedge clk);rst=1;ms(50);keys=5;ms(1100);keys=7;ms(50);
if(!tracking || !live)$fatal(1,"setup not ready");cancels=0;
FREEZE
keys=6;ms(100);keys=7;ms(50);
if(downs!=1 || clicks!=1 || cancels!=0 || !was_pending || blankings==0)$fatal(1,"gesture coverage down%0d click%0d cancel%0d pending%b blanks%0d live%b age%0d",downs,clicks,cancels,was_pending,blankings,live,regions.tip_age);
if(nd!=1 || regions.draft[20:0]!={10'd100,11'd100})$fatal(1,"crossframe lost point pts%0d error%0d",nd,ee);
$display("STAGE1_REAL_KEYS_PASS down%0d click%0d blankings%0d",downs,clicks,blankings);$finish;end
endmodule'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--legacy',action='store_true');ap.add_argument('--freeze',action='store_true');ap.add_argument('--faults',action='store_true');a=ap.parse_args()
    src=BASE.replace('FREEZE','while(!video_ok || vs)@(negedge clk);frames=0;' if a.freeze else '')
    if not a.legacy:
        src=src[:src.index('initial begin repeat(4)')]+(FAULTS if a.faults else HAPPY)+'\nendmodule'
        src=src.replace('reg frames=1;', "reg camera_ready=1,stream_n=1,tip_exists=1,same_id=0,bad_packet=0,reader_active=0,inject_busy=0;reg [1:0] switches=1;reg [15:0] source_epoch=7,source_model=16'h1234;reg frames=1;")
        src=src.replace(".I_ui_switch(2'd1)",'.I_ui_switch(switches)').replace(".I_camera({1'b1,4'd7",".I_camera({camera_ready,4'd7")
        src=src.replace('n=n+1;', 'if(!same_id)n=n+1;').replace('packet[32]=1;', 'packet[32]=tip_exists;').replace('packet[255]=1;', 'packet[255]=!bad_packet;')
        src=src.replace("packet[559:544]=16'h1234;",'packet[559:544]=source_model;').replace('packet[719:704]=7;', 'packet[719:704]=source_epoch;').replace('packet[850:835]=7;', 'packet[850:835]=source_epoch;')
        src=src.replace('.I_stream_n(rst)', '.I_stream_n(stream_n)').replace('.I_hs(1\'b0),.I_de(1\'b0)', '.I_hs(1\'b0),.I_de(reader_active)')
        src=src.replace(".camera_ready(1'b1),.gain_busy(gb)",'.camera_ready(camera_ready),.gain_busy(gb||inject_busy)')
        src=src.replace('wire [3:0] nd,ee;', 'wire [2:0] nr,expected;wire [3:0] state,completed,nd,ee,reason;wire alarm;wire [671:0] saved;')
        src=src.replace('.draft_count(nd),.edit_error(ee),.tip_live(live)', '.draft_count(nd),.edit_error(ee),.tip_live(live),.tip_reason(reason),.region_count(nr),.saved_vertices(saved),.run_state(state),.expected_area(expected),.completed(completed),.alarm(alarm)')
    guard="""wire associated,area_video;
stage1_input_guard guard(clk,rst,stream_n,tracking,camera_ready,gb||inject_busy,video_ok,reader_de,commit,session,pair,image,epoch,image_us,time_ok,meta,associated,area_video);"""
    src=src.replace('GUARD','' if a.legacy else guard).replace('REGION_VIDEO','video_ok' if a.legacy else 'area_video').replace('REGION_ASSOC','detection' if a.legacy else 'associated')
    mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('stage1_controls','stable_display','refined_line_reader','stage1_regions','stage1_sequence','refined_zoom_geometry','refined_reset_bridge','stable_model_lane','stable_filter4')]+[R/'rtl/04_tracking/target_mailbox.v']
    run('stage1_real_keys'+('_faults' if a.faults else '')+('_legacy' if a.legacy else '')+('_freeze' if a.freeze else ''),src,mods,expected_failure=a.legacy and not a.freeze,timeout=120)

SETUP = r"""
task setup;begin
 rst=0;keys=7;frames=1;camera_ready=1;stream_n=1;tip_exists=1;same_id=0;bad_packet=0;reader_active=0;inject_busy=0;switches=1;
 source_epoch=7;source_model=16'h1234;px=100;py=100;phase=0;n=0;repeat(5)@(negedge clk);
 rst=1;ms(50);keys=5;ms(1100);keys=7;ms(50);
 while(!live)@(negedge clk);downs=0;clicks=0;cancels=0;was_pending=0;
end endtask
task short_key;input [2:0] mask;input integer duration;begin keys=~mask;ms(duration);keys=7;ms(50);end endtask
task location;input integer x,y;begin px=x;py=y;ms(40);end endtask
task record;input integer x,y;begin location(x,y);short_key(1,50);end endtask
"""
HAPPY=SETUP+r"""
integer i,duration;
initial begin
 for(i=0;i<3;i=i+1)begin setup;ms(i*3);duration=i==0?50:i==1?100:300;
 short_key(1,duration);
 if(downs!=1 || clicks!=1 || nd!=1 || regions.draft[20:0]!={10'd100,11'd100})$fatal(1,"crossframe duration%0d nd%0d err%0d",duration,nd,ee);
 record(300,250);if(nr!=1 || nd!=0 || saved[41:0]!={10'd250,11'd300,10'd100,11'd100})$fatal(1,"automatic second point");
 record(500,300);short_key(2,50);if(nd!=0 || nr!=1)$fatal(1,"KEY3 must clear only draft");
 record(500,300);record(700,450);if(nr!=2 || nd!=0)$fatal(1,"B automatic save");
 end
 switches=2;location(900,600);short_key(1,50);ms(70);if(state!=2)$fatal(1,"normal VS interrupted WAIT OUT state%0d",state);
 location(200,150);ms(70);if(state!=2 || expected!=1)$fatal(1,"A across VS");
 location(900,600);ms(70);location(600,350);ms(70);if(state!=5 || completed!=3)$fatal(1,"A B PASS across VS");
 location(900,600);short_key(1,50);ms(70);location(600,350);ms(70);if(state!=6 || !alarm)$fatal(1,"wrong-order alarm");
 short_key(4,50);if(alarm || state!=6)$fatal(1,"mute erased FAIL");
 location(900,600);short_key(1,50);ms(70);short_key(2,50);if(state!=3)$fatal(1,"pause");
 short_key(2,50);ms(70);if(state!=2)$fatal(1,"resume across VS");
 tip_exists=0;ms(30);if(state!=7 || alarm)$fatal(1,"real loss must interrupt quietly");
 $display("STAGE1_REAL_KEYS_PASS durations50/100/300 auto-save/clear/order/PASS/FAIL/mute/pause/loss");$finish;end
"""
FAULTS=SETUP+r"""
integer f;reg [3:0] saved_reason;
initial begin
 for(f=0;f<10;f=f+1)begin setup;keys=6;ms(50);if(!regions.point_pending)$fatal(1,"no pending before fault%0d",f);
 case(f)
 0:camera_ready=0;1:tip_exists=0;2:frames=0;3:same_id=1;4:stream_n=0;
 5:reader_active=1;6:source_epoch=8;7:source_model=16'h5678;8:bad_packet=1;9:inject_busy=1;
 endcase
 ms(f==2 || f==3?300:40);keys=7;ms(50);
 if(nd!=0 || regions.point_pending || reason==0)$fatal(1,"fault accepted point%0d nd%0d reason%0d",f,nd,reason);
 case(f)0:if(reason!=2)$fatal(1,"camera reason");1:if(reason!=4)$fatal(1,"no tip reason");
 2,3:if(reason!=5)$fatal(1,"stale reason");4,5:if(reason!=3)$fatal(1,"reader/stream reason");
 6,7:if(reason!=8)$fatal(1,"context reason");8:if(reason!=9)$fatal(1,"metadata reason");9:if(reason!=6)$fatal(1,"gain reason");endcase
 saved_reason=reason;camera_ready=1;tip_exists=1;frames=1;same_id=0;stream_n=1;reader_active=0;bad_packet=0;inject_busy=0;ms(50);
 if(reason!=saved_reason)$fatal(1,"cancel reason disappeared after recovery%0d",f);
 location(100,100);short_key(1,50);if(nd!=1 || reason!=0)$fatal(1,"recovery did not require a fresh press%0d nd%0d reason%0d",f,nd,reason);
 end
 setup;keys=6;ms(1100);keys=7;ms(50);if(nd!=0 || show)$fatal(1,"long KEY2 recorded or failed to hide");
 setup;keys=6;ms(40);keys=2;ms(40);keys=7;ms(50);if(nd!=0)$fatal(1,"chord recorded");
 setup;keys=6;ms(50);switches=0;ms(50);keys=7;ms(50);if(nd!=0)$fatal(1,"mode switch recorded");
 $display("STAGE1_REAL_KEYS_FAULTS_PASS camera/no-tip/stale/repeat/stream/reader/epoch/model/meta/gain/long/chord/mode/recovery");$finish;end
"""

if __name__=='__main__':main()
