"""Independent rational coordinate oracle for boxes, points and odd view extents."""
from refined_testlib import R,run
import random
out=R/'build/sim/refined_geometry';out.mkdir(parents=True,exist_ok=True)
rows=[];rng=random.Random(47299)
for zoom,(p,q) in enumerate(((1,1),(3,2),(2,1),(3,1),(4,1))):
 w=(1279*q)//p+1;h=(623*q)//p+1
 for rot in (0,1):
  for origin in ((0,0),(1280-w,720-h),((1280-w)//3,(720-h)//3)):
   for k in range(12):
    ax=rng.randrange(1264);ay=rng.randrange(704);bx=rng.randrange(1264);by=rng.randrange(704)
    a=(ax,ax+15,ay,ay+15);b=(bx,bx+15,by,by+15);tip=(rng.randrange(1280),rng.randrange(720));phase=k%5
    def box(v):return v[0]|v[1]<<11|v[2]<<22|v[3]<<32
    meta=box(a)<<100|box(b)<<142|tip[0]<<79|tip[1]<<90|phase<<565
    small=phase in (0,2);sample=(636,643,356,363) if small else (632,647,352,367)
    points=[]
    for rect in (a,b,(320,959,180,539),sample):
     for axis,N in ((0,1280),(1,624)):
      lo=(rect[axis*2]-origin[axis])*p;hi=(rect[axis*2+1]+1-origin[axis])*p
      l=-((-lo)//q);r=-((-hi)//q)-1
      points.extend((N-1-r,N-1-l) if rot else (l,r))
    for axis,N in ((0,1280),(1,624)):
     d=tip[axis]-origin[axis];l=-((-d*p)//q);r=-((-(d+1)*p)//q)-1;c=(l+r)//2
     points.append(N-1-c if rot else c)
    expected=sum((v&0x3fff)<<(14*i) for i,v in enumerate(points))
    rows.append(expected|origin[0]<<252|origin[1]<<263|zoom<<273|rot<<276|meta<<277)
file=out/'vectors.hex';file.write_text('\n'.join(f'{v:0230x}' for v in rows),encoding='ascii')
src=f'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,commit=0;reg [639:0] meta=0;reg [10:0] x0=0;reg [9:0] y0=0;reg [2:0] zoom=0;reg rotate=0;
wire ready;wire [251:0] points;reg [916:0] vectors[0:{len(rows)-1}];integer i,n;
refined_overlay_geometry dut(clk,rst,commit,meta,x0,y0,zoom,rotate,ready,points);
initial begin $readmemh("{file.as_posix()}",vectors);repeat(4)@(negedge clk);rst=1;
for(i=0;i<{len(rows)};i=i+1)begin @(negedge clk);meta=vectors[i][916:277];rotate=vectors[i][276];zoom=vectors[i][275:273];y0=vectors[i][272:263];x0=vectors[i][262:252];commit=1;
@(negedge clk);commit=0;n=0;while(!ready && n<20)begin @(negedge clk);n=n+1;end
if(!ready || points!==vectors[i][251:0])$fatal(1,"geometry vector%0d zoom%0d rot%0d got%h expected%h",i,zoom,rotate,points,vectors[i][251:0]);end
$display("REFINED_GEOMETRY_PASS {len(rows)} rational-reference cases, all zooms/directions, odd extents, clipped boxes, sample/guide and mirrored point centres");$finish;end endmodule'''
run('rational_overlay_geometry',src,[R/'rtl/color_regions/refined_overlay_geometry.v'])
view=r'''module tb;
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
$display("REFINED_VIEWPORT_PASS five zooms, odd-width clamps, step-limited movement, both orientations, calibration/restoration");$finish;end endmodule'''
run('five_zoom_viewport',view,[R/'rtl/color_regions/stable_display.v',R/'rtl/color_regions/refined_zoom_geometry.v'])
