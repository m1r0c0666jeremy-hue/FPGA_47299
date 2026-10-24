"""Real-key rectangle capacity and independent coordinate/border-band oracles."""
from refined_testlib import R,run
import argparse,random

BASE=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [1:0] mode=1;
reg down=0,c2=0,c3=0,c4=0,cancel=0,tracking=1,video_ok=1,camera_ready=1,gain_busy=0;
reg [7:0] session=1;reg pair=0,commit=0,detection=1;reg [31:0] image=0;reg [767:0] meta=0;
wire [2:0] nr,expected,actual;wire [3:0] nd,state,completed,occupied,closed,ee,se;
wire [15:0] revision,counts;wire [671:0] vertices,saved;wire [167:0] draft;
wire muted,alarm,busy,live,metrics;wire [1:0] trend;wire [10:0] distance;wire [19:0] dwell;
stage1_regions #(.CYCLES_PER_MS(10000)) dut(clk,rst,mode,down,c2,c3,c4,cancel,tracking,video_ok,camera_ready,gain_busy,
session,pair,commit,detection,image,meta,nr,nd,revision,vertices,counts,closed,state,completed,occupied,expected,actual,
muted,alarm,trend,distance,dwell,ee,se,busy,live,metrics,saved,draft);
wire [3:0] mask;wire [23:0] color,lc;wire lon,ready,under;wire [7:0] glyph;wire [2:0] gx;wire [3:0] gy;
stage1_render #(.SPLIT_DRAFT(1)) picture(clk,rst,commit,saved,counts,closed,mode,11'd0,10'd0,3'd0,1'b0,
state,completed,expected,actual,11'd0,10'd0,1'b0,mask,color,lon,glyph,gx,gy,lc,ready,under,draft,nr,nd!=0);
integer snapshot_checks=0,si;reg [41:0] snapshot_want[0:3];reg [1:0] size_want[0:3];
always @(posedge clk)if(rst && commit)begin
for(si=0;si<4;si=si+1)begin snapshot_want[si]=(nr==si && nd!=0)?draft[41:0]:saved[si*168+:42];size_want[si]=counts[si*4+:2];end
#1;for(si=0;si<4;si=si+1)if(size_want[si]!=0 && (picture.points[si]!==snapshot_want[si] || picture.sizes[si]!==size_want[si]))$fatal(1,"atomic snapshot mismatch");
snapshot_checks=snapshot_checks+1;end
task frame;input integer px,py;begin
@(negedge clk);image=image+1;meta[31:0]=image;meta[89:79]=px;meta[99:90]=py;commit=1;
@(negedge clk);commit=0;repeat(8)@(negedge clk);end endtask
task key;input integer k;begin @(negedge clk);case(k)2:c2=1;3:c3=1;4:c4=1;endcase
@(negedge clk);c2=0;c3=0;c4=0;repeat(8)@(negedge clk);end endtask
task record;input integer px,py;begin frame(px,py);down=1;@(negedge clk);down=0;frame(px+1,py);key(2);end endtask
task rect;input integer x0,y0,x1,y1;begin record(x0,y0);record(x1,y1);key(3);end endtask
initial begin
meta[255]=1;meta[247]=1;meta[32]=1;meta[415:413]=4;meta[242:235]=1;meta[244]=1;meta[559:544]=16'h1234;
repeat(3)@(negedge clk);rst=1;
'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--geometry',action='store_true');a=ap.parse_args()
    source=BASE
    if a.geometry:
        rects=[(0,0,60,60),(100,80,200,160),(350,200,430,290),(1220,650,1279,719)]
        # record() intentionally moves on release. At max x use reverse corners,
        # and move within the image so the release remains valid.
        source=source.replace('frame(px+1,py);key(2);','frame(px==1279?px-1:px+1,py);key(2);')
        for l,t,r,b in rects:source+=f'rect({r},{b},{l},{t});\n'
        source+='if(nr!=4 || nd!=0 || closed!=15)$fatal(1,"geometry setup");mode=0;repeat(4)@(negedge clk);\n'
        rng=random.Random(47299)
        for case in range(1024):
            if case<512:
                l,t,r,b=rects[case%4]
                x=max(0,min(1279,rng.choice([l,r])+rng.randrange(-4,5)))
                y=max(0,min(719,rng.choice([t,b])+rng.randrange(-4,5)))
            else:x,y=rng.randrange(1280),rng.randrange(720)
            inside=near=0
            for j,(l,t,r,b) in enumerate(rects):
                if l<=x<=r and t<=y<=b:inside|=1<<j
                if l-2<=x<=r+2 and t-2<=y<=b+2 and not(l+2<x<r-2 and t+2<y<b-2):near|=1<<j
            source+=f'frame({x},{y});if(dut.observed_in!==4\'d{inside} || dut.observed_near!==4\'d{near} || !metrics)$fatal(1,"rect geometry case{case}");\n'
        source+='$display("RECT_GEOMETRY_PASS cases=1024");'
        name='stage1_rect_geometry'
    else:
        source+=r'''
key(3);if(ee!=1 || nr!=0)$fatal(1,"missing corners accepted");
record(100,100);key(3);if(ee!=1 || nd!=1)$fatal(1,"one corner saved");
record(180,180);record(220,220);if(ee!=6 || nd!=2)$fatal(1,"third corner accepted");
key(3);if(nr!=1 || nd!=0 || counts[3:0]!=2)$fatal(1,"A save");
rect(104,104,120,120);if(ee!=3 || nr!=1 || nd!=2)$fatal(1,"nested rectangle accepted");key(4);key(4);
rect(180,130,240,200);if(ee!=3 || nr!=1)$fatal(1,"touch accepted");key(4);key(4);
rect(250,250,254,254);if(ee!=2 || nr!=1)$fatal(1,"rectangle without guard-band interior accepted");key(4);key(4);
rect(400,300,300,200);if(nr!=2 || saved[168+:42]!=={10'd300,11'd400,10'd200,11'd300})$fatal(1,"reverse corners not normalized");
rect(500,350,580,430);rect(700,500,800,600);
if(nr!=4 || nd!=0 || counts!=16'h2222 || closed!=15)$fatal(1,"4 rectangles capacity");
record(900,500);if(nr!=4 || nd!=0 || ee!=4)$fatal(1,"fifth rectangle accepted");
// Remove D on the same edge as a display commit: the old display snapshot must be atomic.
@(negedge clk);commit=1;c4=1;@(negedge clk);commit=0;c4=0;repeat(40)@(negedge clk);
if(nr!=3 || closed!=7 || under)$fatal(1,"delete/commit race");
rect(900,500,1000,600);if(nr!=4 || saved[504+:42]!=={10'd600,11'd1000,10'd500,11'd900})$fatal(1,"deleted slot did not rebuild");
key(4);key(4);key(4);key(4);if(nr!=0 || counts!=0 || alarm)$fatal(1,"delete all");
record(600,400);mode=0;repeat(4)@(negedge clk);mode=1;repeat(4)@(negedge clk);if(nd!=1)$fatal(1,"mode lost draft");
mode=2;repeat(4)@(negedge clk);key(2);if(se!=1)$fatal(1,"empty configuration start error");
mode=1;repeat(4)@(negedge clk);rst=0;@(negedge clk);rst=1;repeat(4)@(negedge clk);
if(nr!=0 || nd!=0 || alarm || trend!=0 || distance!=0)$fatal(1,"reset or deferred metrics");
if(snapshot_checks<20)$fatal(1,"snapshot coverage");
$display("RECT_CAPACITY_PASS four-areas/two-corners/overlap-touch-small-reject/delete-rebuild/atomic-commit/reset");
'''
        name='stage1_rect_capacity'
    source+='$finish;end endmodule'
    run(name,source,[R/'rtl/color_regions'/n for n in ('stage1_regions.v','stage1_sequence.v','stage1_render.v')],timeout=180)

if __name__=='__main__':main()
