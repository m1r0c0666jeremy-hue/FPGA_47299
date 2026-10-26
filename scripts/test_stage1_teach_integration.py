"""Production keys -> committed view -> scene -> route -> replay sequence."""
from refined_testlib import R,run

BENCH=r'''module tb;
localparam CPM=200;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [2:0] keys=7;reg [1:0] switches=1;
reg camera=1,frames=1,exists=1,same_frame=0;reg [10:0] px=900;reg [9:0] py=400;
reg [851:0] packet=0;integer phase=0,frame_id=0;reg vs=0,snapshot=0;
wire tracking,show,pair,rotate,down,k2,k3,k4,cancel,gb;wire [7:0] session;wire [1:0] mode;wire [2:0] zoom;
wire [38:0] desired,shown;wire [63:0] teaching;wire commit,det,time_valid;
wire [31:0] image,image_us;wire [15:0] epoch;wire [767:0] meta;
wire [10:0] x0;wire [9:0] y0;wire [2:0] nr,expected,actual;wire [3:0] nd,state,complete,occupied;
wire [3:0] reason;wire [19:0] dwell;wire tip,alarm;wire image_ok,associated,area_video;wire [3:0] image_reason;
wire raw_video=phase>=20;wire reader_de=phase>=100 && phase<3900;
stage1_controls #(.CYCLES_PER_MS(CPM)) controls(.I_clk(clk),.I_rst_n(rst),.I_keys_n(keys),.I_ui_switch(switches),
.I_gain_ack(1'b0),.I_cal_status(8'd0),.I_pause(1'b0),.I_camera({camera,4'd7,4'd0,2'd0,7'd90}),
.O_tracking(tracking),.O_show(show),.O_session(session),.O_pair(pair),.O_rotate(rotate),.O_zoom(zoom),
.O_ui_mode(mode),.O_down2(down),.O_click2(k2),.O_click3(k3),.O_click4(k4),.O_cancel(cancel),.O_gain_busy(gb));
always @(negedge clk)if(rst && frames)begin
phase=(phase+1)%4000;vs=phase<4;snapshot=phase==2;
if(snapshot)begin
if(!same_frame)frame_id=frame_id+1;
packet=0;packet[31:0]=frame_id;packet[32]=exists;packet[89:79]=px;packet[99:90]=py;
packet[242:235]=session;packet[243]=pair;packet[244]=tracking && camera;packet[247]=1;packet[255]=1;
packet[415:413]=4;packet[559:544]=16'h1234;packet[671:640]=frame_id*20000;packet[719:704]=7;packet[720]=1;
packet[799:768]=frame_id;packet[802]=1;packet[834:803]=frame_id*20000;packet[850:835]=7;packet[851]=1;end
end else begin vs=0;snapshot=0;end
stage1_viewport #(.V4(1)) view(.I_clk(clk),.I_rst_n(rst),.I_vs(vs),.I_de(reader_de),.I_snapshot(snapshot),.I_data(packet),
.I_tracking(tracking && camera),.I_show(show),.I_conflict(1'b0),.I_live(camera),.I_session(session),.I_zoom(zoom),.I_mode(2'd0),
.I_pair(pair),.I_rotate(rotate),.O_commit(commit),.O_frame_id(image),.O_x0(x0),.O_y0(y0),.O_meta(meta),
.O_detection_valid(det),.O_image_us(image_us),.O_epoch(epoch),.O_time_valid(time_valid),.I_point(desired),.O_point(shown));
stage1_input_guard real_guard(clk,rst,rst,tracking && camera,camera,gb,raw_video,reader_de,commit,session,pair,image,epoch,image_us,time_valid,meta,associated,area_video);
wire image_associated=meta[255] && meta[247] && meta[31:0]==image && meta[671:640]==image_us && meta[719:704]==epoch &&
 meta[242:235]==session && meta[243]==pair && meta[244]==(tracking && camera) && time_valid;
stage1_teach_image_guard #(.CYCLES_PER_MS(CPM)) guard(clk,rst,rst,camera,gb,raw_video,reader_de,image_associated,image,image_ok,image_reason);
stage1_scene #(.CYCLES_PER_MS(CPM)) scene(.clk(clk),.rst_n(rst),.mode(mode),.down2(down),.click2(k2),.click3(k3),.click4(k4),.cancel(cancel),
.tracking(tracking && camera),.video_ok(area_video),.camera_ready(camera),.gain_busy(gb),.session(session),.pair(pair),
.frame_commit(commit),.detection_valid(associated),.image_id(image),.meta(meta),.region_count(nr),.draft_count(nd),
.run_state(state),.completed(complete),.occupied(occupied),.expected_area(expected),.actual_area(actual),.alarm(alarm),
.dwell_ms(dwell),.tip_live(tip),.tip_reason(reason),.image_healthy(image_ok),.image_reason(image_reason),
.shown_point(shown),.desired_point(desired),.teaching(teaching));
integer samples=0,clears=0;reg [15:0] held_time;reg [19:0] held_dwell;reg held_show;
always @(posedge clk)if(rst)begin if(scene.virtual_sample)samples=samples+1;if(k4 && cancel)clears=clears+1;end
task ms;input integer n;begin repeat(n*CPM)@(negedge clk);end endtask
task key;input [2:0] mask;input integer n;begin keys=~mask;ms(n);keys=7;ms(35);end endtask
task corner;input integer x,y;begin px=x;py=y;ms(60);key(1,50);end endtask
task move;input integer x,y,n;begin px=x;py=y;ms(n);end endtask
initial begin repeat(4)@(negedge clk);rst=1;ms(50);key(2,1100);ms(40);
if(!tracking || !tip)$fatal(1,"enable tracking setup mode%0d tip%b assoc%b",mode,tip,associated);
corner(100,100);corner(300,200);corner(500,100);corner(700,200);
if(nr!=2 || nd!=0)$fatal(1,"actual editor setup nr%0d nd%0d",nr,nd);
move(900,400,60);switches=3;ms(60);key(1,50);ms(200);
move(200,150,260);move(900,400,220);move(600,150,260);move(900,400,220);key(1,50);
if(teaching[3:0]!=1 || teaching[18:8]<15)$fatal(1,"real-key recording state%0d n%0d reason%0d",teaching[3:0],teaching[18:8],reason);
exists=0;ms(60);key(2,50);ms(250);key(2,50);
held_time=teaching[34:19];held_dwell=dwell;ms(500);
if(teaching[3:0]!=6 || teaching[34:19]!=held_time || dwell!=held_dwell)$fatal(1,"connected pause time/dwell");
key(2,50);ms(1500);
if(teaching[3:0]!=7 || state!=5 || complete!=3 || !shown[22])$fatal(1,"replay no-tip PASS state%0d seq%0d complete%h expected%0d samples%0d",teaching[3:0],state,complete,expected,samples);
held_time=teaching[34:19];held_dwell=dwell;ms(400);
if(teaching[34:19]!=held_time || dwell!=held_dwell)$fatal(1,"DONE still clocks");
key(4,50);ms(40);if(shown[22] || alarm || nr!=2)$fatal(1,"return to real");
key(1,50);if(teaching[3:0]!=1 || teaching[18:8]<15)$fatal(1,"invalid recording overwrote old route");
exists=1;ms(60);key(1,50);ms(100);held_show=show;key(1,1100);
if(teaching[3:0]!=3 || show==held_show)$fatal(1,"long hide interrupted recording");
camera=0;ms(2);if(teaching[3:0]!=1 || reason!=2 || teaching[18:8]<2)$fatal(1,"camera fault prefix reason%0d",reason);
camera=1;ms(60);if(teaching[3:0]!=1)$fatal(1,"record resumed automatically");
key(4,1100);if(teaching[18:8]!=0 || teaching[3:0]!=0 || clears!=1)$fatal(1,"long clear leaked gesture clear%0d",clears);
// Wrong first region must freeze the same point that caused FAIL.
move(900,400,60);key(1,50);ms(220);move(600,150,300);move(200,150,300);key(1,50);exists=0;ms(40);key(2,50);ms(800);
if(teaching[3:0]!=8 || state!=6 || !alarm || actual!=2 || shown[10:0]<500 || shown[10:0]>700)$fatal(1,"replay wrong order state%0d seq%0d actual%0d x%0d",teaching[3:0],state,actual,shown[10:0]);
held_time=teaching[34:19];ms(300);if(teaching[34:19]!=held_time)$fatal(1,"FAIL kept moving");
key(4,50);if(alarm)$fatal(1,"stop did not silence");
key(2,50);ms(100);same_frame=1;ms(300);if(desired[22] || image_ok || reason!=5)$fatal(1,"virtual source masked stale video reason%0d",reason);
$display("STAGE1_TEACH_INTEGRATION_PASS keys/editor/viewport/guards/no-tip/pause/PASS/FAIL/stale/clear");$finish;end
initial begin #100000000;$fatal(1,"integration timeout");end
endmodule'''

if __name__=='__main__':
    run('stage1_teach_integration',BENCH,[R/'rtl/color_regions'/n for n in ('stage1_regions.v','stage1_sequence.v','stage1_controls.v','refined_zoom_geometry.v')],timeout=180)
