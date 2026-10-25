module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,commit=0;reg [639:0] meta=0;reg [10:0] x0=0;reg [9:0] y0=0;reg [2:0] zoom=0;reg rotate=0;
wire ready;wire [251:0] points;reg [916:0] vectors[0:359];integer i,n;
refined_overlay_geometry dut(clk,rst,commit,meta,x0,y0,zoom,rotate,ready,points);
initial begin $readmemh("E:/codex/FPGAco/720p-zoom/build/sim/refined_geometry/vectors.hex",vectors);repeat(4)@(negedge clk);rst=1;
for(i=0;i<360;i=i+1)begin @(negedge clk);meta=vectors[i][916:277];rotate=vectors[i][276];zoom=vectors[i][275:273];y0=vectors[i][272:263];x0=vectors[i][262:252];commit=1;
@(negedge clk);commit=0;n=0;while(!ready && n<20)begin @(negedge clk);n=n+1;end
if(!ready || points!==vectors[i][251:0])$fatal(1,"geometry vector%0d zoom%0d rot%0d got%h expected%h",i,zoom,rotate,points,vectors[i][251:0]);end
$display("REFINED_GEOMETRY_PASS 360 rational-reference cases, all zooms/directions, odd extents, clipped boxes, sample/guide and mirrored point centres");$finish;end endmodule