"""Exercise actual editor, validation, geometry and sequence as one connected circuit."""
from refined_testlib import R,run

def main():
    src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [1:0] mode=1;reg down=0,c2=0,c3=0,c4=0,cancel=0;
reg tracking=1,video_ok=1,camera_ready=1,gain_busy=0;reg [7:0] session=1;reg pair=0,commit=0,detection=1;
reg [31:0] image=0;reg [767:0] meta=0;
wire [2:0] nr,expected,actual;wire [3:0] nd,state,completed,occupied,closed,ee,se;wire [15:0] revision,counts;
wire [671:0] vertices;wire muted,alarm,busy,live;wire [1:0] trend;wire [10:0] distance;wire [19:0] dwell;
stage1_regions #(.CYCLES_PER_MS(1000)) dut(clk,rst,mode,down,c2,c3,c4,cancel,tracking,video_ok,camera_ready,gain_busy,
session,pair,commit,detection,image,meta,nr,nd,revision,vertices,counts,closed,state,completed,occupied,expected,actual,
muted,alarm,trend,distance,dwell,ee,se,busy,live);
task frame;input integer x,y;begin
@(negedge clk);image=image+1;meta[31:0]=image;meta[89:79]=x;meta[99:90]=y;commit=1;
@(negedge clk);commit=0;repeat(10000)@(negedge clk);end endtask
task key;input integer k;begin
@(negedge clk);case(k)2:c2=1;3:c3=1;4:c4=1;endcase
@(negedge clk);c2=0;c3=0;c4=0;repeat(5000)@(negedge clk);end endtask
task record;input integer x,y;begin
frame(x,y);down=1;@(negedge clk);down=0;
frame(x+5,y+5);key(2);end endtask
task three;input integer x,y;begin frame(x,y);frame(x,y);frame(x,y);end endtask
initial begin
meta[255]=1;meta[247]=1;meta[32]=1;meta[415:413]=4;meta[242:235]=1;meta[244]=1;meta[559:544]=16'h1234;
repeat(3)@(negedge clk);rst=1;
record(100,100);if(nd!=1 || vertices[20:0]!={10'd100,11'd100})$fatal(1,"press-down capture changed on release nd%0d v%h error%0d",nd,vertices[20:0],ee);
record(300,100);record(200,250);key(3);
if(nr!=1 || nd!=0 || counts[3:0]!=3 || closed!=1)$fatal(1,"A save failed nr%0d nd%0d error%0d",nr,nd,ee);
record(500,100);record(700,100);record(600,250);key(3);
if(nr!=2 || nd!=0 || closed!=3)$fatal(1,"B save failed nr%0d nd%0d err%0d",nr,nd,ee);
record(140,140);record(160,140);record(150,160);key(3);repeat(10000)@(negedge clk);
if(nr!=2 || nd!=3 || ee!=3)$fatal(1,"contained region accepted nr%0d nd%0d err%0d",nr,nd,ee);
key(4);key(4);key(4);if(nd!=0 || nr!=2)$fatal(1,"draft undo");
mode=0;repeat(3)@(negedge clk);if(nr!=2)$fatal(1,"switch erased regions");mode=2;frame(900,400);key(2);three(900,400);
if(state!=2)$fatal(1,"editor connected to sequence state%0d err%0d",state,se);
three(200,150);if(expected!=1 || completed!=1)$fatal(1,"actual geometry did not confirm A state%0d in%h d%0d",state,occupied,distance);
repeat(260000)@(negedge clk);if(state!=7 || alarm)$fatal(1,"repeated old source did not interrupt");
frame(900,400);key(2);three(900,400);three(200,150);three(900,400);three(600,150);
if(state!=5 || completed!=3)$fatal(1,"A B integration did not pass state%0d completed%h",state,completed);
mode=1;repeat(3)@(negedge clk);key(4);if(nr!=1 || closed!=1)$fatal(1,"delete last region");
down=1;@(negedge clk);down=0;cancel=1;@(negedge clk);cancel=0;key(2);if(nd!=0)$fatal(1,"cancelled gesture recorded point");
rst=0;@(negedge clk);if(nr!=0 || nd!=0 || alarm)$fatal(1,"reset did not clear");
$display("STAGE1_REGIONS_PASS press-position/edit/concavity-validation/undo/modes/actual-geometry/order/stale/reset");$finish;end
endmodule'''
    names=['stage1_arith.v','stage1_point.v','stage1_segment.v','stage1_validate.v','stage1_sequence.v','stage1_regions.v']
    run('stage1_regions',src,[R/'rtl/color_regions'/n for n in names],timeout=180)
    buzzer=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,enable=0;wire buzzer;
stage1_buzzer #(.CLOCK_HZ(40000)) dut(clk,rst,enable,buzzer);
integer n,toggles=0;reg previous=1;
initial begin repeat(3)@(negedge clk);if(buzzer!==1)$fatal(1,"reset beep");rst=1;enable=1;
for(n=0;n<40005;n=n+1)begin @(negedge clk);if(buzzer!=previous)toggles=toggles+1;previous=buzzer;
if(n>8010 && n<39990 && buzzer!==1)$fatal(1,"quiet interval not high");end
if(toggles<790 || toggles>810)$fatal(1,"tone frequency/cadence wrong %0d",toggles);
enable=0;repeat(5)@(negedge clk);if(buzzer!==1)$fatal(1,"mute failed");
$display("STAGE1_BUZZER_PASS high-silent/reset/2kHz/cadence/mute");$finish;end
endmodule'''
    run('stage1_buzzer',buzzer,[R/'rtl/color_regions/stage1_buzzer.v'],timeout=60)

if __name__=='__main__':main()
