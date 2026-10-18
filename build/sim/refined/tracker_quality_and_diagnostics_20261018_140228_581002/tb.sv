module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;reg [31:0] id=0;reg [1023:0] candidates=0;
wire done,valid,hv;wire [127:0] a,b;wire [10:0] tx;wire [9:0] ty;wire [3:0] reason;wire [83:0] boxes;wire [1:0] state;
stable_tracker dut(clk,rst,start,id,10'd3,16'd0,1'b1,candidates,done,a,b,valid,tx,ty,reason,hv,boxes,state,,,,,);
function [127:0] candidate;input integer x,q;begin candidate=0;candidate[120]=1;candidate[61:42]=100;
candidate[72:62]=x;candidate[82:73]=360;candidate[89:83]=q;candidate[41:0]={10'd367,10'd352,11'(x+7),11'(x-8)};end endfunction
task frame;integer n;begin @(negedge clk);id=id+1;start=1;@(negedge clk);start=0;n=0;
while(!done && n<200)begin @(negedge clk);n=n+1;end if(!done)$fatal(1,"tracker timeout");end endtask
initial begin repeat(3)@(negedge clk);rst=1;
candidates[127:0]=candidate(590,0);candidates[255:128]=candidate(690,100);candidates[639:512]=candidate(640,100);
frame;if(valid || a[72:62]!=690 || a[93:92]!=1 || a[95:94]!=0 || a[97:96]!=1 || a[99:98]!=1 || a[111:104]!=0)$fatal(1,"initial quality choice/diagnostic %h",a);
frame;frame;if(!valid || tx!=715 || ty!=360 || a[97:96]!=2 || a[99:98]!=3)$fatal(1,"confirmed identity");
candidates[639:512]=0;frame;if(valid || a[103:100]!=1 || !a[104] || a[97:96]!=3)$fatal(1,"missing-colour diagnostics %h",a);
candidates[639:512]=candidate(640,100);candidates[255:128]=0;frame;
if(valid || !a[108] || a[103:100]!=2)$fatal(1,"reversal diagnostics %h",a);
candidates[255:128]=candidate(690,100);frame;frame;frame;
if(!valid || a[72:62]!=690 || a[103:100]!=0 || a[111:104]!=0)$fatal(1,"recovery identity/diagnostics");
$display("RING_TRACKER_PASS geometric tie quality, central/history selection, chosen slots, confirmation, missing/direction rejects and recovery");$finish;end endmodule