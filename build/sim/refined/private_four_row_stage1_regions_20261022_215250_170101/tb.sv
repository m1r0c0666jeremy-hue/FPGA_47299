module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [1:0] mode=1;reg down=0,c2=0,c3=0,c4=0,cancel=0;
reg tracking=1,video_ok=1,camera_ready=1,gain_busy=0;reg [7:0] session=1;reg pair=0,commit=0,detection=1;
reg [31:0] image=0;reg [767:0] meta=0;
wire [2:0] nr,expected,actual;wire [3:0] nd,state,completed,occupied,closed,ee,se;wire [15:0] revision,counts;
wire [671:0] vertices;wire muted,alarm,busy,live,metrics_valid;wire [1:0] trend;wire [10:0] distance;wire [19:0] dwell;
wire [671:0] private_saved;wire [167:0] private_draft;
reg geometry_commit=0,rde=0;reg [10:0] rx=0;reg [9:0] ry=0;
wire [3:0] pmask;wire [23:0] pcolor,lcolor;wire lon,rready,under;wire [7:0] glyph;wire [2:0] gx;wire [3:0] gy;
stage1_render #(.SPLIT_DRAFT(1)) picture(clk,rst,geometry_commit,private_saved,counts,closed,mode,11'd0,10'd0,3'd0,1'b0,
state,completed,expected,actual,rx,ry,rde,pmask,pcolor,lon,glyph,gx,gy,lcolor,rready,under,private_draft,nr,nd!=0);
integer row_check,column_check;reg [3:0] expected_mask;
stage1_regions #(.CYCLES_PER_MS(1000)) dut(clk,rst,mode,down,c2,c3,c4,cancel,tracking,video_ok,camera_ready,gain_busy,
session,pair,commit,detection,image,meta,nr,nd,revision,vertices,counts,closed,state,completed,occupied,expected,actual,
muted,alarm,trend,distance,dwell,ee,se,busy,live,metrics_valid,private_saved,private_draft);
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
meta[255]=0;frame(100,100);if(live)$fatal(1,"invalid metadata accepted");
video_ok=0;meta[255]=1;commit=1;@(negedge clk);commit=0;repeat(10000)@(negedge clk);
if(live || dut.seen)$fatal(1,"metadata admitted before video prefetch ready");
video_ok=1;repeat(10000)@(negedge clk);
if(!live || !dut.seen)$fatal(1,"same image did not recover after video became ready without another commit");
record(100,100);if(nd!=1 || vertices[20:0]!={10'd100,11'd100})$fatal(1,"press-down capture changed on release nd%0d v%h error%0d",nd,vertices[20:0],ee);
geometry_commit=1;@(negedge clk);geometry_commit=0;repeat(10000)@(negedge clk);
if(!rready || under)$fatal(1,"coupled draft prepare failed");
for(row_check=0;row_check<105;row_check=row_check+1)begin
for(column_check=0;column_check<1650;column_check=column_check+1)begin
@(negedge clk);rx=column_check<1280?column_check:0;ry=row_check;rde=column_check<1280;
@(posedge clk);#1;
if(rde)begin
expected_mask=(row_check>=98 && row_check<=102 && column_check>=98 && column_check<=102)?4'd1:4'd0;
if(pmask!==expected_mask || under)$fatal(1,"actual editor/draft render xy%0d/%0d got%h expected%h",column_check,row_check,pmask,expected_mask);
end end end
@(negedge clk);rde=0;
$display("STAGE1_EDIT_RENDER_PASS point_pixels=134400");
record(300,100);record(200,250);key(3);
if(nr!=1 || nd!=0 || counts[3:0]!=3 || closed!=1)$fatal(1,"A save failed nr%0d nd%0d error%0d",nr,nd,ee);
if(metrics_valid)$fatal(1,"new geometry exposed old distance as valid");
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
down=1;cancel=1;@(negedge clk);down=0;cancel=0;key(2);if(nd!=0)$fatal(1,"simultaneous cancel/down recorded point");
rst=0;@(negedge clk);if(nr!=0 || nd!=0 || alarm)$fatal(1,"reset did not clear");
$display("STAGE1_REGIONS_PASS press-position/edit/concavity-validation/undo/modes/actual-geometry/order/stale/reset");$finish;end
endmodule