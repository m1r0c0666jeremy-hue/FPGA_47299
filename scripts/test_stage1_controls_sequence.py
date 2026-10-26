"""Behavioral UI/sequence contract; accelerated millisecond clocks."""
from refined_testlib import R,run

def main():
    controls=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [2:0] keys=7;reg [1:0] sw=0;
reg ack=0,pause=0;reg [7:0] cal=0;reg [17:0] camera={1'b1,4'd7,4'd0,2'd0,7'd90};
wire req,up,tracking,show,conflict,pair,ce,cs,cc,rotate,down,c2,c3,c4,cancel,gb,gf;
wire [2:0] zoom,slot;wire [7:0] session;wire [1:0] diag,mode;
reg [1:0] last_mode=0;
stage1_controls #(.CYCLES_PER_MS(2),.DEBOUNCE_MS(3),.LONG_PRESS_MS(20),.CHORD_WINDOW_MS(8)) dut(
clk,rst,keys,sw,ack,cal,pause,camera,req,up,zoom,tracking,show,session,conflict,pair,ce,cs,cc,rotate,diag,mode,
down,c2,c3,c4,cancel,gb,gf,slot,);
integer clicks2=0,clicks3=0,clicks4=0,downs=0,steps=0;reg [6:0] next_gain;integer delay_ack=0,delay_feedback=0;
always @(posedge clk)begin #1;if(rst && mode!=last_mode && (down || c2 || c3 || c4))$fatal(1,"switch acceptance leaked a gesture");last_mode=mode;end
always @(posedge clk)begin
if(c2)clicks2=clicks2+1;if(c3)clicks3=clicks3+1;if(c4)clicks4=clicks4+1;if(down)downs=downs+1;
if(rst)begin
if(req!=ack && delay_ack==0)begin delay_ack=4;next_gain=up?camera[6:0]+1'b1:camera[6:0]-1'b1;end
if(delay_ack>0)begin delay_ack=delay_ack-1;if(delay_ack==0)begin ack<=req;delay_feedback=5;steps=steps+1;end end
else if(delay_feedback>0)begin delay_feedback=delay_feedback-1;if(delay_feedback==0)camera[6:0]<=next_gain;end
end end
task ms;input integer n;begin repeat(2*n)@(negedge clk);end endtask
task key;input [2:0] mask;input integer n;begin keys=~mask;ms(n);keys=7;ms(7);end endtask
initial begin repeat(3)@(negedge clk);rst=1;ms(8);
key(2,7);if(zoom!=1 || tracking)$fatal(1,"00 short KEY3 must only zoom");
key(2,28);if(!tracking || zoom!=1)$fatal(1,"long KEY3 must only track");
key(1,28);if(show || gb)$fatal(1,"long KEY2 must only hide");
key(2,28);if(tracking)$fatal(1,"tracking did not stop");
key(1,7);ms(300);if(gb || gf || slot!=6 || camera[6:0]!=105 || steps!=15)$fatal(1,"preset105 or stale feedback: slot%0d gain%0d steps%0d",slot,camera[6:0],steps);
key(1,7);ms(1000);if(gb || gf || slot!=0 || camera[6:0]!=16 || steps!=104)$fatal(1,"preset wrap steps wrong");
sw=1;ms(8);if(mode!=1)$fatal(1,"edit switch");key(1,7);key(2,7);key(4,7);
if(clicks2!=1 || clicks3!=1 || clicks4!=1 || downs!=1)$fatal(1,"edit routing");
key(1,28);if(clicks2!=1 || downs!=2)$fatal(1,"long key accidentally recorded point");
keys=6;ms(7);sw=2;ms(8);keys=7;ms(8);if(clicks2!=1 || mode!=2)$fatal(1,"mode switch leaked short key");
key(1,7);key(2,7);key(4,7);if(clicks2!=2 || clicks3!=2 || clicks4!=2)$fatal(1,"test routing");
sw=0;ms(8);key(5,28);if(!ce || clicks2!=2)$fatal(1,"calibration chord");
cal=8'h20;key(2,7);if(!cs || tracking)$fatal(1,"cal sample exclusive");key(1,7);if(!cc || gb)$fatal(1,"cal cancel exclusive");
cal=0;ms(5);key(6,28);if(rotate)$fatal(1,"rotate chord");
pause=1;@(negedge clk);pause=0;ms(5);if(tracking)$fatal(1,"camera pause");
$display("STAGE1_CONTROLS_PASS preset_steps=%0d short/long/chords/modes/calibration",steps);$finish;end
endmodule'''
    run('stage1_controls',controls,[R/'rtl/color_regions/stage1_controls.v'],timeout=120)
    sequence=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [1:0] mode=2;reg [2:0] nr=3;reg [3:0] draft=0;
reg sk=0,pk=0,mk=0,can=1,live=1,changed=0,sample=0;reg [3:0] im=0,nm=0;reg [43:0] ds=44'd100;
wire [3:0] state,completed,occupied,se;wire [2:0] expected,actual;wire muted,alarm;wire [1:0] trend;
wire [10:0] distance;wire [19:0] dwell;reg [19:0] held_dwell;
stage1_sequence #(.CYCLES_PER_MS(1)) dut(clk,rst,mode,nr,draft,sk,pk,mk,can,live,changed,sample,im,nm,ds,
state,expected,actual,completed,occupied,muted,alarm,trend,distance,dwell,se,1'b0);
task frame;input [3:0] a,b;begin im=a;nm=b;sample=1;@(negedge clk);sample=0;repeat(9)@(negedge clk);end endtask
task frames;input [3:0] a;begin frame(a,0);frame(a,0);frame(a,0);end endtask
task start;begin sk=1;@(negedge clk);sk=0;frames(0);if(state!=2)$fatal(1,"not RUN %0d error%0d",state,se);end endtask
initial begin repeat(3)@(negedge clk);rst=1;@(negedge clk);
start;frame(1,0);frame(1,0);if(expected!=0)$fatal(1,"less than three frames counted");
frame(1,1);if(expected!=0)$fatal(1,"boundary counted");frames(1);if(expected!=1 || completed!=1)$fatal(1,"A not counted");
frames(1);if(state!=2 || expected!=1)$fatal(1,"staying in A retriggered");frames(0);
held_dwell=dwell;if(held_dwell==0)$fatal(1,"leaving A lost duration when target became B");
frame(0,0);if(dwell!=held_dwell)$fatal(1,"last duration changed while outside");frames(1);
if(state!=6 || !alarm || actual!=1)$fatal(1,"return to A did not fail");
mk=1;@(negedge clk);mk=0;@(negedge clk);if(alarm || state!=6)$fatal(1,"mute erased fail");
start;if(muted)$fatal(1,"new round remained muted");frames(4);if(state!=6 || actual!=3)$fatal(1,"skip C not failed");
start;frames(1);frames(0);frames(2);frames(0);frame(4,0);frame(4,0);pk=1;frame(4,0);pk=0;
if(state!=5 || completed!=7)$fatal(1,"PASS must outrank simultaneous pause");
live=0;repeat(5)@(negedge clk);if(state!=5)$fatal(1,"PASS not latched");live=1;
start;frames(1);pk=1;@(negedge clk);pk=0;frames(0);if(state!=3 || expected!=1)$fatal(1,"pause lost progress");
pk=1;@(negedge clk);pk=0;frames(0);if(state!=2 || expected!=1)$fatal(1,"resume did not require outside");
live=0;@(negedge clk);if(state!=7 || alarm)$fatal(1,"tracking loss must interrupt without alarm");live=1;
start;frames(1);frames(0);frame(4,0);frame(4,0);pk=1;frame(4,0);pk=0;
if(state!=6)$fatal(1,"FAIL must outrank simultaneous pause");
start;repeat(260)@(negedge clk);if(state!=7)$fatal(1,"stale frame watchdog");
mode=1;@(negedge clk);frames(1);frames(1);if(occupied!=1 || dwell==0)$fatal(1,"dwell unavailable");
frames(0);if(occupied!=0)$fatal(1,"leave failed");mode=2;@(negedge clk);start;
ds=100;frame(0,0);repeat(200)@(negedge clk);ds=96;frame(0,0);if(trend!=1)$fatal(1,"approach threshold");
draft=1;pk=1;@(negedge clk);pk=0;sk=1;@(negedge clk);sk=0;@(negedge clk);if(se!=2)$fatal(1,"unfinished draft allowed start");
$display("STAGE1_SEQUENCE_PASS boundary/order/revisit/mute/pause/loss/stale/dwell/trend");$finish;end
endmodule'''
    run('stage1_sequence',sequence,[R/'rtl/color_regions/stage1_sequence.v'],timeout=120)

if __name__=='__main__':main()
