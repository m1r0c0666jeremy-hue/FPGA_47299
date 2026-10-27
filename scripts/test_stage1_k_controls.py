"""K page, route identity, and reduced editing using real control state machines.

Milliseconds are accelerated (4 or 1 cycles/ms); production 20ms debounce and
1000ms hold thresholds are preserved. The separate live suite uses 75MHz.
"""
from refined_testlib import R,run

CONTROLS=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [2:0] keys=7;reg [1:0] sw=0;
reg ack=0,pause=0;reg [7:0] cal=0;reg [17:0] camera={1'b1,4'd7,4'd0,2'd0,7'd90};
wire req,up,tracking,show,conflict,pair,ce,cs,cc,rotate,down,c2,c3,c4,cancel,gb,gf,kpage;
wire [2:0] zoom,slot;wire [7:0] session,kvalue;wire [1:0] diag,mode;
stage1_controls #(.CYCLES_PER_MS(4)) dut(.I_clk(clk),.I_rst_n(rst),.I_keys_n(keys),.I_ui_switch(sw),
.I_gain_ack(ack),.I_cal_status(cal),.I_pause(pause),.I_camera(camera),.O_gain_req(req),.O_gain_up(up),
.O_zoom(zoom),.O_tracking(tracking),.O_show(show),.O_session(session),.O_conflict(conflict),.O_pair(pair),
.O_cal_enter(ce),.O_cal_sample(cs),.O_cal_cancel(cc),.O_rotate(rotate),.O_diag(diag),.O_ui_mode(mode),
.O_down2(down),.O_click2(c2),.O_click3(c3),.O_click4(c4),.O_cancel(cancel),.O_gain_busy(gb),
.O_gain_failed(gf),.O_gain_slot(slot),.O_k_value(kvalue),.O_k_adjust(kpage));
integer clicks2=0,clicks3=0,clicks4=0,downs=0,i;reg [7:0] before_session,before_k;
reg old_show,old_ce,old_cs,old_rotate;integer old_clicks;
always @(posedge clk)begin
if(c2)clicks2=clicks2+1;if(c3)clicks3=clicks3+1;if(c4)clicks4=clicks4+1;if(down)downs=downs+1;
end
task ms;input integer n;begin repeat(4*n)@(negedge clk);end endtask
task key;input [2:0] mask;input integer n;begin keys=~mask;ms(n);keys=7;ms(50);end endtask
task change_k;input [2:0] mask;input integer expected;begin
before_session=session;before_k=kvalue;key(mask,50);
if(kvalue!=expected || !kpage || !tracking || zoom!=1 || pair!=1 || gb || ce || cs || cc)
$fatal(1,"K key changed unrelated behavior value%0d expected%0d page%b",kvalue,expected,kpage);
if(before_k!=expected)before_session=before_session+1'b1;
if(session!=before_session)$fatal(1,"K identity increment/saturation mismatch");
end endtask
initial begin repeat(4)@(negedge clk);rst=1;ms(50);
if(kvalue!=50 || kpage)$fatal(1,"K reset");
key(2,50);key(4,50);key(2,1100);
if(zoom!=1 || !pair || !tracking)$fatal(1,"legacy 00 setup");
key(3,1100);if(!kpage || kvalue!=50 || !tracking || zoom!=1 || !pair || gb)$fatal(1,"enter page consumed chord");
change_k(2,51);change_k(4,50);
keys=5;ms(300);if(kvalue!=50)$fatal(1,"press must wait for release");keys=7;ms(50);
if(kvalue!=51 || !tracking)$fatal(1,"300ms short must change exactly once");
for(i=52;i<=200;i=i+1)change_k(2,i);
change_k(2,200);change_k(2,200);
for(i=199;i>=0;i=i-1)change_k(4,i);
change_k(4,0);change_k(4,0);
before_session=session;key(2,2500);
if(tracking || kvalue!=0 || !kpage || session!=before_session+1'b1)$fatal(1,"long K3 tracking only, no repeat");
key(2,1100);if(!tracking || kvalue!=0 || !kpage)$fatal(1,"tracking on in page");
old_show=show;key(1,1100);if(show==old_show || kvalue!=0 || !kpage)$fatal(1,"long K2 mark only");
old_ce=ce;old_rotate=rotate;key(5,1100);key(6,1100);key(7,1100);
if(ce!=old_ce || rotate!=old_rotate || kvalue!=0 || !kpage || gb)$fatal(1,"page cannot calibrate/rotate/chord leak");
before_session=session;key(1,50);
if(kpage || gb || kvalue!=0 || session!=before_session)$fatal(1,"K2 exits without brightness");
key(3,1100);key(3,1100);if(kpage || zoom!=1 || gb)$fatal(1,"toggle exits without short leak");
// Only a completed new release changes K, including a camera event in a hold.
key(3,1100);keys=5;ms(50);pause=1;@(negedge clk);pause=0;keys=7;ms(50);
if(kpage || kvalue!=0 || tracking || zoom!=1)$fatal(1,"camera event exits and consumes held gesture");
key(3,1100);keys=3;ms(50);camera[17]=0;ms(5);camera[17]=1;keys=7;ms(50);
if(kpage || kvalue!=0 || pair!=1)$fatal(1,"camera loss exits without leaked pair/K");
key(3,1100);keys=5;ms(50);sw=2;ms(50);keys=7;ms(50);
if(kpage || kvalue!=0 || mode!=2 || clicks3!=0)$fatal(1,"mode exit consumed release");
sw=1;ms(50);key(2,50);key(4,50);key(1,50);
if(clicks3!=0 || clicks4!=1 || clicks2!=1 || downs!=1)$fatal(1,"01 only K2/K4 short routing");
sw=0;ms(50);key(5,1100);if(ce==old_ce)$fatal(1,"legacy calibration chord outside page");
cal=8'h20;key(3,1100);if(kpage)$fatal(1,"K page forbidden during calibration");
old_cs=cs;key(2,50);if(cs==old_cs || kpage || zoom!=1)$fatal(1,"calibration sample remains exclusive");
key(1,50);cal=0;ms(50);key(6,1100);if(rotate==old_rotate)$fatal(1,"legacy rotate chord outside page");
// A held unacknowledged brightness request also prevents K page entry.
key(1,50);if(!gb)$fatal(1,"brightness setup");key(3,1100);
if(kpage || kvalue!=0)$fatal(1,"K page forbidden during brightness busy");
$display("STAGE1_K_CONTROLS_PASS saturation=0..200 debounce20ms holds1000ms camera/mode/cal/brightness/legacy");$finish;
end endmodule'''

ROUTE=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [1:0] mode=3;
reg k2=0,k3=0,k4=0,clear=0,healthy=1,live=1,sample=0,commit=0,seqfail=0;
reg [3:0] realreason=0;reg [10:0] x=100;reg [9:0] y=100;reg [31:0] us=0;reg [40:0] ctx=0;
reg [7:0] currentk=50;wire [7:0] routek;wire routevalid;wire [3:0] state,reason;wire [10:0] count,px;
wire [9:0] py;wire [15:0] elapsed,duration,pms;wire usepoint,valid,start,running;
stage1_route #(.CYCLES_PER_MS(1)) dut(clk,rst,mode,k2,k3,k4,clear,healthy,live,sample,realreason,x,y,us,
ctx,commit,seqfail,px,py,pms,state,reason,count,elapsed,duration,usepoint,valid,px,py,pms,start,running,currentk,routek,routevalid);
task pulse2;begin k2=1;@(negedge clk);k2=0;repeat(3)@(negedge clk);end endtask
task point;input integer stamp,xx;begin us=stamp;x=xx;sample=1;@(negedge clk);sample=0;repeat(40)@(negedge clk);end endtask
task startnew;begin live=1;realreason=0;pulse2;if(state!=2)$fatal(1,"not WAIT_POINT");end endtask
reg [39:0] oldentry;integer deadline;
initial begin repeat(4)@(negedge clk);rst=1;repeat(3)@(negedge clk);
if(routevalid || routek!=50)$fatal(1,"route K reset");
startnew;point(1000000,100);point(1050000,200);pulse2;
if(count!=2 || state!=1 || !routevalid || routek!=50)$fatal(1,"first route identity/count");
oldentry=dut.memory[0];currentk=75;live=0;realreason=4;pulse2;
if(state!=1 || count!=2 || routek!=50 || !routevalid || dut.memory[0]!=oldentry)$fatal(1,"failed start overwrote old route");
startnew;if(routek!=50 || count!=2)$fatal(1,"arming must retain old route K");
live=0;realreason=4;repeat(3)@(negedge clk);
if(state!=1 || routek!=50 || count!=2 || !routevalid)$fatal(1,"loss before first point destroyed old identity");
startnew;sample=1;us=2000000;x=300;k2=1;@(negedge clk);sample=0;k2=0;repeat(3)@(negedge clk);
if(routek!=50 || count!=2 || dut.memory[0]!=oldentry)$fatal(1,"same-cycle denied key wrote route K/data");
live=0;repeat(3)@(negedge clk);startnew;
us=3000000;x=400;sample=1;@(negedge clk);sample=0;
if(count!=1 || !routevalid || routek!=75 || dut.memory[0][20:0]!={10'd100,11'd400})$fatal(1,"first committed sample and K not atomic");
currentk=80;point(3050000,500);pulse2;
if(count!=2 || routek!=75)$fatal(1,"recorded K followed live setting");
k3=1;@(negedge clk);k3=0;commit=1;deadline=0;
while(state!=5 && deadline<30)begin @(negedge clk);deadline=deadline+1;end
if(state!=5 || reason!=0)$fatal(1,"play setup");
k3=1;@(negedge clk);k3=0;repeat(3)@(negedge clk);
if(state!=5 || reason!=0 || !running || routek!=75)$fatal(1,"PLAY K3 must be ignored without STOP FIRST");
deadline=0;while(state!=7 && deadline<150)begin @(negedge clk);deadline=deadline+1;end
if(state!=7 || reason!=0)$fatal(1,"replay must finish without stale STOP FIRST");
k4=1;@(negedge clk);k4=0;repeat(3)@(negedge clk);
startnew;k3=1;@(negedge clk);k3=0;@(negedge clk);
if(reason!=10 || routek!=75 || !routevalid)$fatal(1,"recording conflict must retain STOP FIRST");
clear=1;sample=1;@(negedge clk);clear=0;sample=0;@(negedge clk);
if(routevalid || count!=0 || state!=0)$fatal(1,"clear outranks first route sample/K write");
$display("STAGE1_K_ROUTE_PASS first_write/failed_start/clear_collision/record_conflict/replay_K3");$finish;
end endmodule'''

EDITOR=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,down=0,c2=0,c3=0,c4=0;reg [767:0] meta=0;reg [31:0] image=0;
wire [2:0] regions;wire [3:0] points,error;wire live;wire [15:0] revision;
stage1_regions #(.CYCLES_PER_MS(1)) dut(.clk(clk),.rst_n(rst),.mode(2'd1),.down2(down),.click2(c2),.click3(c3),
.click4(c4),.cancel(1'b0),.tracking(1'b1),.video_ok(1'b1),.camera_ready(1'b1),.gain_busy(1'b0),.session(8'd0),
.pair(1'b0),.frame_commit(1'b1),.detection_valid(1'b1),.image_id(image),.meta(meta),.region_count(regions),.draft_count(points),
.edit_error(error),.tip_live(live),.revision(revision));
task locate;input integer x,y;begin image=image+1;meta[31:0]=image;meta[89:79]=x;meta[99:90]=y;repeat(3)@(negedge clk);end endtask
task add;input integer x,y;begin locate(x,y);down=1;@(negedge clk);down=0;@(negedge clk);c2=1;@(negedge clk);c2=0;repeat(5)@(negedge clk);end endtask
task key3;begin c3=1;@(negedge clk);c3=0;repeat(4)@(negedge clk);end endtask
task key4;begin c4=1;@(negedge clk);c4=0;repeat(4)@(negedge clk);end endtask
reg [15:0] before_revision;
initial begin meta[32]=1;meta[244]=1;meta[247]=1;meta[255]=1;meta[415:413]=4;
repeat(4)@(negedge clk);rst=1;locate(10,10);
add(100,100);add(200,200);if(regions!=1 || points!=0)$fatal(1,"initial rectangle");
add(500,500);before_revision=revision;key3;
if(points!=1 || regions!=1 || revision!=before_revision)$fatal(1,"01 K3 must leave single draft untouched");
add(502,502);before_revision=revision;key3;
if(points!=2 || regions!=1 || revision!=before_revision || error!=2)$fatal(1,"01 K3 must leave invalid two-point draft untouched");
key4;if(points!=1)$fatal(1,"K4 must undo one point");add(800,600);
if(points!=0 || regions!=2)$fatal(1,"K4-corrected second corner must auto-save");
key3;if(regions!=2)$fatal(1,"K3 deleted saved area");key4;if(regions!=1)$fatal(1,"K4 reverse deletion");
$display("STAGE1_K_EDITOR_PASS single/two-point/saved-K3-ignored K4-correct/delete");$finish;
end endmodule'''

def main():
    rtl=R/'rtl/color_regions'
    run('stage1_k_controls',CONTROLS,[rtl/'stage1_controls.v'],timeout=120)
    modules=[rtl/'stage1_regions.v',rtl/'stage1_sequence.v']
    run('stage1_k_route_identity',ROUTE,modules,timeout=120)
    run('stage1_k_editor',EDITOR,modules,timeout=120)

if __name__=='__main__':main()
