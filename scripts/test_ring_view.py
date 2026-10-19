"""Rotation changes only at an accepted blank-frame transaction; overlays match."""
from test_ring_calibration import R,run
src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,vs=0,de=0,snap=0,rotate=1;reg [674:0] data=0;
wire commit,shown,pair,det,sample,orientation;wire [1:0] bank,zoom,mode;wire [31:0] fid;wire [10:0] cx,x0;wire [9:0] cy,y0;wire [639:0] meta;wire [2:0] state;
stable_display view(clk,rst,vs,de,snap,data,1'b1,1'b1,1'b0,1'b1,8'd1,2'd1,2'd0,1'b0,commit,bank,fid,cx,x0,cy,y0,zoom,mode,meta,shown,pair,det,sample,state,rotate,orientation);
wire ovs,ohs,ode;wire [23:0] rgb;reg [639:0] om=0;
stable_osd osd(clk,rst,1'b0,1'b0,1'b0,24'h123456,om,11'd400,10'd300,2'd1,2'd0,3'd2,1'b1,1'b1,1'b1,1'b0,1'b1,1'b0,ovs,ohs,ode,rgb,rotate,2'd0,32'd7);
task blank;begin @(negedge clk);vs=1;@(negedge clk);vs=0;repeat(2)@(negedge clk);snap=1;@(negedge clk);snap=0;end endtask
task probe(input integer x,y,input [23:0] color);begin
@(negedge clk);osd.x=x;osd.y=y;#1;
if(!osd.back_on || osd.back!=color)$fatal(1,"overlay rotation%0d xy%0d/%0d got%h on%0d",rotate,x,y,osd.back,osd.back_on);end endtask
integer k;
initial begin repeat(3)@(negedge clk);rst=1;if(!orientation)$fatal(1,"default180");
data[674]=1;data[671:640]=7;data[31:0]=7;data[255]=1;data[247]=1;data[244]=1;data[242:235]=1;data[415:413]=3;
blank;if(!orientation || !commit)$fatal(1,"180 commit");
de=1;rotate=0;snap=1;@(negedge clk);snap=0;if(!orientation || commit)$fatal(1,"midframe rotation");
de=0;blank;if(orientation || !commit)$fatal(1,"0 commit");
om[245]=1;om[246]=1;om[141:100]={10'd359,10'd340,11'd449,11'd430};om[183:142]={10'd399,10'd380,11'd499,11'd480};om[32]=1;om[89:79]=470;om[99:90]=370;
rotate=0;probe(60,100,24'hff6060);probe(198,170,24'h6090ff);probe(140,140,24'h40ff90);
rotate=1;probe(1180,520,24'hff6060);probe(1080,450,24'h6090ff);probe(1138,482,24'h40ff90);
// Calibration/sampling and central guide use exactly the same source transform.
om[245]=0;om[246]=0;om[32]=0;om[567:565]=1;probe(1280-2*(647-400)-2,624-2*(352-300)-2,24'h80ff80);
om[567:565]=0;om[36:33]=1;probe(1280-2*(959-400)-2,624-2*(400-300)-2,24'h40c080);
// Body geometry never rotates upright footer coordinates.
rotate=0;probe(1152,624,24'hffffff);rotate=1;probe(1152,624,24'hffffff);
$display("RING_VIEW_PASS atomic orientation, noncentral viewport, A/B boxes, signed tip, guide/sample and upright footer");$finish;end endmodule'''
run('view_rotation',src,[R/f'rtl/color_regions/{n}.v' for n in ('stable_display','stable_osd','stable_glyph_rom','stable_footer_glyph_rom','stable_footer_program_rom','stable_footer_text_rom')]+[R/'rtl/09_osd_ui/scaling_logo_rom.v'])
