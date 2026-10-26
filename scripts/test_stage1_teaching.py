"""Independent arithmetic and timed route contracts; no board access."""
import math, random
from refined_testlib import R,run

MODULES=[R/'rtl/color_regions/stage1_regions.v',R/'rtl/color_regions/stage1_sequence.v']

def motion():
    rng=random.Random(0x1024)
    cases=[(0,0),(100,100),(200,200),(1279,719),(400,300)]+[(rng.randrange(1280),rng.randrange(720)) for _ in range(95)]
    src='''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,active=0,sample=0;reg [10:0] x=0;reg [9:0] y=0;
reg [18:0] identity=1;wire [1:0] trend;wire [10:0] distance;wire valid;
stage1_motion #(.CYCLES_PER_MS(200)) dut(clk,rst,active,sample,x,y,{10'd300,11'd400,10'd100,11'd200},identity,trend,distance,valid);
task point;input integer px,py;begin x=px;y=py;sample=1;@(negedge clk);sample=0;repeat(100)@(negedge clk);end endtask
task ms;input integer n;begin repeat(n*200)@(negedge clk);end endtask
initial begin repeat(3)@(negedge clk);rst=1;active=1;repeat(3)@(negedge clk);
'''
    for i,(x,y) in enumerate(cases):
        dx=max(200-x,0,x-400);dy=max(100-y,0,y-300);expected=math.isqrt(dx*dx+dy*dy)
        src+=f'identity=identity+1;repeat(2)@(negedge clk);point({x},{y});if(!valid || distance!={expected})$fatal(1,"distance case{i} got%0d expected{expected}",distance);\n'
    src+='''identity=identity+1;repeat(3)@(negedge clk);point(600,200);
ms(200);point(590,200);if(trend!=1)$fatal(1,"approach");
ms(200);point(610,200);if(trend!=2)$fatal(1,"away");
ms(200);point(610,220);if(trend!=0)$fatal(1,"lateral mistaken for still");
identity=identity+1;repeat(3)@(negedge clk);point(500,200);
repeat(12)begin ms(50);point(500,200);end
if(trend!=3)$fatal(1,"stationary window trend%0d",trend);
repeat(1312)begin ms(50);point(500,200);if(trend!=3)$fatal(1,"still lost across 16-bit millisecond rollover");end
active=0;@(negedge clk);if(valid)$fatal(1,"invalid active retained valid");
$display("STAGE1_TEACH_MOTION_PASS distance_cases=100 approach/away/lateral/still/reset/timewrap");$finish;end endmodule'''
    run('stage1_teach_motion',src,MODULES,timeout=120)

def route():
    src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [1:0] mode=3;reg k2=0,k3=0,k4=0,clear=0;
reg image_ok=1,live=1,sample=0;reg [3:0] fault=0;reg [10:0] x=0;reg [9:0] y=0;
reg [31:0] us=32'hfff00000;reg [40:0] context_id=1;reg commit=0,fail=0;
wire [3:0] state,reason;wire [10:0] count,px;wire [9:0] py;wire [15:0] elapsed,duration,pm;
wire use_point,pv,start,running;reg [10:0] sx=0;reg [9:0] sy=0;reg [15:0] sm=0;
stage1_route #(.CYCLES_PER_MS(200)) dut(clk,rst,mode,k2,k3,k4,clear,image_ok,live,sample,fault,x,y,us,context_id,commit,fail,sx,sy,sm,
state,reason,count,elapsed,duration,use_point,pv,px,py,pm,start,running);
always @(posedge clk)if(commit)begin sx<=px;sy<=py;sm<=pm;end
task clocks;input integer n;begin repeat(n)@(negedge clk);end endtask
task ms;input integer n;begin clocks(n*200);end endtask
task key;input integer n;begin case(n)2:k2=1;3:k3=1;4:k4=1;endcase clocks(1);k2=0;k3=0;k4=0;clocks(3);end endtask
task point;input integer a,b;input [31:0] t;begin x=a;y=b;us=t;sample=1;clocks(1);sample=0;clocks(70);end endtask
task view;begin commit=1;clocks(1);commit=0;clocks(3);end endtask
integer i,held;reg [15:0] frozen;reg [31:0] base;
initial begin clocks(3);rst=1;clocks(3);key(2);base=us;point(100,100,base);
if(state!=3 || count!=1)$fatal(1,"record first");
ms(50);point(200,150,base+50000);if(count!=2)$fatal(1,"record second count%0d",count);
ms(50);point(300,200,base+100000);ms(20);key(2);
if(state!=1 || duration<120 || count!=3)$fatal(1,"record duration state%0d ms%0d count%0d",state,duration,count);
live=0;fault=4;key(3);clocks(20);
if(state!=5 || !pv || px!=100 || py!=100)$fatal(1,"play without actual tool state%0d xy%0d/%0d",state,px,py);
ms(25);clocks(120);view();
if(px<148 || px>154 || py<124 || py>127)$fatal(1,"interpolation xy%0d/%0d t%0d",px,py,pm);
key(3);frozen=elapsed;ms(500);if(elapsed!=frozen || state!=6)$fatal(1,"pause clock");
key(3);ms(100);clocks(120);repeat(3)view();
if(state!=7 || px!=300 || py!=200)$fatal(1,"finish hold state%0d xy%0d/%0d",state,px,py);
key(4);if(use_point || count!=3)$fatal(1,"stop loses route");
key(2);if(count!=3 || state!=1)$fatal(1,"bad record start erased route");
live=1;fault=0;key(2);if(count!=3)$fatal(1,"pending record erased route");
clear=1;sample=1;clocks(1);clear=0;sample=0;clocks(70);if(count!=0 || state!=0)$fatal(1,"clear/write collision");
key(2);base=32'hffff0000;point(500,300,base);
for(i=1;i<1200;i=i+1)begin ms(50);point(500+(i%100),300,base+i*50000);end
// Source time wraps while the run is lengthened slightly by the fixture.
if(count>1202 || count<1100 || duration>60000)$fatal(1,"capacity count%0d duration%0d",count,duration);
if(state==3)ms(1000);
if(state!=1 || duration!=60000)$fatal(1,"full 60 seconds state%0d duration%0d",state,duration);
key(3);clocks(20);ms(50);clocks(120);view();fail=1;clocks(1);fail=0;
if(state!=8 || px!=sx || py!=sy || elapsed!=sm)$fatal(1,"failure did not hold shown point");
key(4);key(2);point(100,100,1000);ms(50);point(200,200,51000);
live=0;fault=4;clocks(1);if(state!=1 || count!=2 || reason!=4)$fatal(1,"fault prefix");
live=1;clocks(10);if(state!=1)$fatal(1,"automatic record resumed");
key(3);clocks(20);context_id=2;clocks(1);if(use_point || count!=2 || reason!=8)$fatal(1,"context stop");
$display("STAGE1_TEACH_ROUTE_PASS 60s/source-wrap/interpolation/tail/pause/clear/fault/prefix/no-tip-play/fail");$finish;end endmodule'''
    run('stage1_teach_route',src,MODULES,timeout=180)

if __name__=='__main__':
    motion();route()
