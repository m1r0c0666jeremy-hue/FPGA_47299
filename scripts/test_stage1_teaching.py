"""Independent arithmetic and timed route contracts; no board access."""
from refined_testlib import R,run

MODULES=[R/'rtl/color_regions/stage1_regions.v',R/'rtl/color_regions/stage1_sequence.v']

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
if(px!=100 || py!=100 || pm!=0)$fatal(1,"hold before 50ms xy%0d/%0d t%0d",px,py,pm);
ms(25);clocks(20);view();if(px!=200 || py!=150 || pm!=50)$fatal(1,"50ms step xy%0d/%0d t%0d",px,py,pm);
key(3);frozen=elapsed;ms(20);if(elapsed<=frozen || state!=5 || reason!=10)$fatal(1,"play key paused/restarted running route");
ms(80);clocks(120);repeat(3)view();
if(state!=7 || px!=300 || py!=200)$fatal(1,"finish hold state%0d xy%0d/%0d",state,px,py);
key(4);if(use_point || count!=3)$fatal(1,"stop loses route");
key(2);if(count!=3 || state!=1)$fatal(1,"bad record start erased route");
live=1;fault=0;key(2);if(count!=3)$fatal(1,"pending record erased route");
clear=1;sample=1;clocks(1);clear=0;sample=0;clocks(70);if(count!=0 || state!=0)$fatal(1,"clear/write collision");
key(2);base=32'hffff0000;point(500,300,base);
for(i=1;i<600;i=i+1)begin ms(50);point(500+(i%100),300,base+i*50000);end
// Source time wraps while the run is lengthened slightly by the fixture.
if(count>602 || count<550 || duration>30000)$fatal(1,"capacity count%0d duration%0d",count,duration);
if(state==3)ms(1000);
if(state!=1 || duration!=30000)$fatal(1,"full 30 seconds state%0d duration%0d",state,duration);
key(3);clocks(20);ms(50);clocks(120);view();fail=1;clocks(1);fail=0;
if(state!=8 || px!=sx || py!=sy || elapsed!=sm)$fatal(1,"failure did not hold shown point");
key(4);key(2);point(100,100,1000);ms(50);point(200,200,51000);
live=0;fault=4;clocks(1);if(state!=1 || count!=2 || reason!=4)$fatal(1,"fault prefix");
live=1;clocks(10);if(state!=1)$fatal(1,"automatic record resumed");
key(3);clocks(20);context_id=2;clocks(1);if(use_point || count!=2 || reason!=8)$fatal(1,"context stop");
$display("STAGE1_TEACH_ROUTE_PASS 30s/source-wrap/20Hz-hold/tail/play-only/clear/fault/prefix/no-tip-play/fail");$finish;end endmodule'''
    run('stage1_teach_route',src,MODULES,timeout=180)

if __name__=='__main__':
    route()
