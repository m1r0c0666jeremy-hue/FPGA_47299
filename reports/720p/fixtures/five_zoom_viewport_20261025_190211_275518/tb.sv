module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,vs=0,de=0,snap=0,rotate=0;reg [2:0] zoom=0;reg [674:0] data=0;
wire commit,show,pair,dv,sv,orientation;wire [1:0] bank,mode;wire [2:0] outzoom,state;wire [31:0] id;wire [10:0] cx,x0;wire [9:0] cy,y0;wire [639:0] meta;
stable_display dut(clk,rst,vs,de,snap,data,1'b1,1'b1,1'b0,1'b1,8'd1,zoom,2'd3,1'b0,commit,bank,id,cx,x0,cy,y0,outzoom,mode,meta,show,pair,dv,sv,state,rotate,orientation);
integer z,r,i,w,h,p,q;integer fid=0;
task frame;begin @(negedge clk);vs=1;@(negedge clk);vs=0;repeat(2)@(negedge clk);fid=fid+1;data[31:0]=fid;data[671:640]=fid;snap=1;@(negedge clk);snap=0;@(negedge clk);end endtask
initial begin repeat(4)@(negedge clk);rst=1;data[674]=1;data[255]=1;data[247]=1;data[244]=1;data[242:235]=1;data[415:413]=3;data[32]=1;
for(z=0;z<5;z=z+1)for(r=0;r<2;r=r+1)begin zoom=z;rotate=r;
case(z)1:begin w=853;h=416;end 2:begin w=640;h=312;end 3:begin w=427;h=208;end 4:begin w=320;h=156;end default:begin w=1280;h=624;end endcase
data[89:79]=1279;data[99:90]=719;
for(i=0;i<60;i=i+1)begin frame;if(x0+w>1280 || y0+h>720 || cx-x0!=w/2 || cy-y0!=h/2 || outzoom!=z || orientation!=r)$fatal(1,"viewport upper bound z%0d x%0d y%0d",z,x0,y0);end
if(x0!=1280-w || y0!=720-h)$fatal(1,"upper clamp not reached");data[89:79]=0;data[99:90]=0;
for(i=0;i<60;i=i+1)begin frame;if(x0+w>1280 || y0+h>720)$fatal(1,"lower bound");end
if(x0!=0 || y0!=0)$fatal(1,"lower clamp not reached");end
data[567:565]=2;frame;if(outzoom!=0 || mode!=0 || x0!=0 || y0!=48)$fatal(1,"calibration 1x");data[567:565]=0;frame;if(outzoom!=4 || mode!=3)$fatal(1,"zoom restore");
$display("REFINED_VIEWPORT_PASS five zooms, odd-width clamps, step-limited movement, both orientations, calibration/restoration");$finish;end endmodule