module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [1:0] mode=2;reg [2:0] nr=3;reg [3:0] draft=0;
reg sk=0,pk=0,mk=0,can=1,live=1,changed=0,sample=0;reg [3:0] im=0,nm=0;reg [43:0] ds=44'd100;
wire [3:0] state,completed,occupied,se;wire [2:0] expected,actual;wire muted,alarm;wire [1:0] trend;
wire [10:0] distance;wire [19:0] dwell;reg [19:0] held_dwell;
stage1_sequence #(.CYCLES_PER_MS(1)) dut(clk,rst,mode,nr,draft,sk,pk,mk,can,live,changed,sample,im,nm,ds,
state,expected,actual,completed,occupied,muted,alarm,trend,distance,dwell,se);
task frame;input [3:0] a,b;begin im=a;nm=b;sample=1;@(negedge clk);sample=0;repeat(9)@(negedge clk);end endtask
task frames;input [3:0] a;begin frame(a,0);frame(a,0);frame(a,0);end endtask
task start;begin sk=1;@(negedge clk);sk=0;frames(0);if(state!=2)$fatal(1,"not RUN %0d error%0d",state,se);end endtask
initial begin repeat(3)@(negedge clk);rst=1;@(negedge clk);
start;frame(1,0);frame(1,0);if(expected!=0)$fatal(1,"less than three frames counted");
frame(1,1);if(expected!=0)$fatal(1,"boundary counted");frames(1);if(expected!=1 || completed!=1)$fatal(1,"A not counted");
frames(1);if(state!=2 || expected!=1)$fatal(1,"staying in A retriggered");frames(0);
held_dwell=dwell;if(held_dwell==0)$fatal(1,"leaving A lost duration when target became B");
frame(0,0);if(dwell!=held_dwell)$fatal(1,"last duration changed while outside");frames(1);
if(state!=6 || !alarm || actual!=1)$fatal(1,"return to A did not fail");
mk=1;@(negedge clk);mk=0;@(negedge clk);if(alarm || state!=6)$fatal(1,"mute erased fail");
start;if(muted)$fatal(1,"new round remained muted");frames(4);if(state!=6 || actual!=3)$fatal(1,"skip C not failed");
start;frames(1);frames(0);frames(2);frames(0);frame(4,0);frame(4,0);pk=1;frame(4,0);pk=0;
if(state!=5 || completed!=7)$fatal(1,"PASS must outrank simultaneous pause");
live=0;repeat(5)@(negedge clk);if(state!=5)$fatal(1,"PASS not latched");live=1;
start;frames(1);pk=1;@(negedge clk);pk=0;frames(0);if(state!=3 || expected!=1)$fatal(1,"pause lost progress");
pk=1;@(negedge clk);pk=0;frames(0);if(state!=2 || expected!=1)$fatal(1,"resume did not require outside");
live=0;@(negedge clk);if(state!=7 || alarm)$fatal(1,"tracking loss must interrupt without alarm");live=1;
start;frames(1);frames(0);frame(4,0);frame(4,0);pk=1;frame(4,0);pk=0;
if(state!=6)$fatal(1,"FAIL must outrank simultaneous pause");
start;repeat(260)@(negedge clk);if(state!=7)$fatal(1,"stale frame watchdog");
mode=1;@(negedge clk);frames(1);frames(1);if(occupied!=1 || dwell==0)$fatal(1,"dwell unavailable");
frames(0);if(occupied!=0)$fatal(1,"leave failed");mode=2;@(negedge clk);start;
ds=100;frame(0,0);repeat(200)@(negedge clk);ds=96;frame(0,0);if(trend!=1)$fatal(1,"approach threshold");
draft=1;pk=1;@(negedge clk);pk=0;sk=1;@(negedge clk);sk=0;@(negedge clk);if(se!=2)$fatal(1,"unfinished draft allowed start");
$display("STAGE1_SEQUENCE_PASS boundary/order/revisit/mute/pause/loss/stale/dwell/trend");$finish;end
endmodule