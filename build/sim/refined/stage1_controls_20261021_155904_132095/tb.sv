module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [2:0] keys=7;reg [1:0] sw=0;
reg ack=0,pause=0;reg [7:0] cal=0;reg [17:0] camera={1'b1,4'd7,4'd0,2'd0,7'd90};
wire req,up,tracking,show,conflict,pair,ce,cs,cc,rotate,down,c2,c3,c4,cancel,gb,gf;
wire [2:0] zoom,slot;wire [7:0] session;wire [1:0] diag,mode;
reg [1:0] last_mode=0;
stage1_controls #(.CYCLES_PER_MS(2),.DEBOUNCE_MS(3),.LONG_PRESS_MS(20),.CHORD_WINDOW_MS(8)) dut(
clk,rst,keys,sw,ack,cal,pause,camera,req,up,zoom,tracking,show,session,conflict,pair,ce,cs,cc,rotate,diag,mode,
down,c2,c3,c4,cancel,gb,gf,slot);
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
endmodule