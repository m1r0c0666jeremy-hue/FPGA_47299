"""Late commits must suppress stale row data; the next frame recovers cleanly."""
from refined_testlib import R,run
src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,commit=0,de=0;reg [10:0] x=0;reg [9:0] y=0;
reg [671:0] vertices=0;wire [3:0] mask;wire [23:0] color,label_color;wire label_on,ready,underrun;
wire [7:0] glyph;wire [2:0] gx;wire [3:0] gy;
reg [2:0] split_region=0;reg split_visible=1;wire [671:0] split_saved={vertices[671:168],168'd0};
// B vertex inspected below is valid; unused snapshot payload is unspecified.
stage1_render #(.SPLIT_DRAFT(1)) dut(clk,rst,commit,split_saved,16'h0022,4'h1,2'd2,11'd0,10'd0,3'd0,1'b0,4'd2,4'd0,3'd0,3'd0,
x,y,de,mask,color,label_on,glyph,gx,gy,label_color,ready,underrun,vertices[167:0],split_region,split_visible);
integer k;
initial begin vertices[189:168]={10'd77,11'd88};vertices[20:0]={10'd10,11'd10};vertices[41:21]={10'd200,11'd200};vertices[210:189]={10'd120,11'd140};
repeat(3)@(negedge clk);rst=1;commit=1;@(negedge clk);commit=0;repeat(10000)@(negedge clk);
if(!ready || underrun)$fatal(1,"normal blanking prepare failed");
commit=1;de=1;@(negedge clk);commit=0;repeat(3)@(negedge clk);
if(!underrun || mask!==0 || label_on)$fatal(1,"late commit exposed stale overlay");
repeat(10000)@(negedge clk);if(mask!==0 || !underrun)$fatal(1,"fault did not remain suppressed for frame");
de=0;commit=1;@(negedge clk);commit=0;repeat(10000)@(negedge clk);
if(!ready || underrun)$fatal(1,"clean next frame did not recover");
// The working input may change while the current displayed snapshot is frozen.
vertices=0;split_region=3;split_visible=0;repeat(5)@(negedge clk);if(dut.points[1][20:0]!=={10'd77,11'd88} || dut.points[0][20:0]!=={10'd10,11'd10})$fatal(1,"frame geometry not frozen");
$display("STAGE1_RENDER_GUARDS_PASS late-commit/no-stale-overlay/recovery/frozen-vertices");$finish;end
endmodule'''
run('stage1_render_guards',src,[R/'rtl/color_regions/stage1_render.v'],timeout=60)
