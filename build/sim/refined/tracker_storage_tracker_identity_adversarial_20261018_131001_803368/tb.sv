module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0,complete=1;reg [31:0] id=0;reg [9:0] cmd=3;reg [15:0] rev=0;
reg [1023:0] candidates=0;wire done,valid,hv;wire [127:0] a,b;wire [10:0] tx;wire [9:0] ty;wire [3:0] reason;wire [83:0] boxes;wire [1:0] selected_state;
stable_tracker dut(clk,rst,start,id,cmd,rev,complete,candidates,done,a,b,valid,tx,ty,reason,hv,boxes,selected_state,,,,,);
function [127:0] c;input integer x,y,n;begin c=0;c[120]=1;c[61:42]=n;c[72:62]=x;c[82:73]=y;c[41:0]={10'(y+8),10'(y-8),11'(x+8),11'(x-8)};end endfunction
task frame;integer cycles;begin @(negedge clk);id=id+1;start=1;@(negedge clk);start=0;cycles=0;while(!done && cycles<200)begin @(negedge clk);cycles=cycles+1;end if(!done)$fatal(1,"tracker deadline");@(negedge clk);end endtask
task reset;begin @(negedge clk);rst=0;repeat(3)@(negedge clk);rst=1;id=0;candidates=0;cmd=3;rev=0;end endtask
task tipcase;input integer ax,ay,bx,by,ex,ey;begin reset;candidates[127:0]=c(ax,ay,48);candidates[639:512]=c(bx,by,2048);
frame;if(valid)$fatal(1,"early lock1");frame;if(valid)$fatal(1,"early lock2");frame;
if(!valid || tx!=ex || ty!=ey)$fatal(1,"signed tip %0d/%0d expected%0d/%0d",tx,ty,ex,ey);end endtask
integer k;
initial begin
tipcase(640,360,541,281,690,400);tipcase(640,360,739,281,591,400);
tipcase(640,360,541,439,690,321);tipcase(640,360,739,439,591,321);
// The second, unequal-size pair is nearer the guide centre than slot zero.
reset;candidates[127:0]=c(360,200,5000);candidates[639:512]=c(390,200,5000);
candidates[255:128]=c(690,360,48);candidates[767:640]=c(590,360,4096);frame;frame;frame;
if(!valid || a[72:62]!=690 || b[72:62]!=590)$fatal(1,"central pair selection");
// A larger different pair remains a distractor after confirmation.
candidates[127:0]=c(510,380,10000);candidates[639:512]=c(410,380,10000);frame;
if(!valid || a[72:62]!=690)$fatal(1,"identity switched to larger pair");
// Direction and area discontinuities cannot recover the stored identity.
candidates=0;candidates[127:0]=c(590,360,48);candidates[639:512]=c(690,360,4096);frame;if(valid)$fatal(1,"reversed tool accepted");
candidates[127:0]=c(690,360,10000);candidates[639:512]=c(590,360,4096);frame;if(valid)$fatal(1,"area discontinuity accepted");
candidates[127:0]=c(690,360,48);frame;if(valid)$fatal(1,"early recovery1");frame;if(valid)$fatal(1,"early recovery2");frame;if(!valid)$fatal(1,"nearby recovery");
// Invalid observations must not release identity and select a central impostor.
complete=0;frame;if(valid || !hv || reason!=8 || selected_state!=2)$fatal(1,"bad frame released identity");complete=1;
candidates=0;candidates[127:0]=c(510,380,48);candidates[639:512]=c(410,380,4096);frame;frame;frame;
if(valid || !hv)$fatal(1,"bad frame auto-switched tool");
candidates[127:0]=c(690,360,48);candidates[639:512]=c(590,360,4096);frame;frame;frame;if(!valid)$fatal(1,"bad-frame nearby recovery");
// A short forward gap restarts confirmation against the existing identity.
id=id+2;frame;if(valid || !hv)$fatal(1,"short gap released identity/confirmation");frame;frame;if(!valid)$fatal(1,"gap recovery");
id=id-1;frame;if(valid || !hv)$fatal(1,"duplicate consumed/released identity");frame;frame;frame;if(!valid)$fatal(1,"duplicate recovery");
candidates[639:512]=0;for(k=0;k<15;k=k+1)begin frame;if(valid)$fatal(1,"occluded tip");end
if(reason!=6 || hv || selected_state!=3)$fatal(1,"identity expiry");candidates[639:512]=c(590,360,4096);frame;frame;frame;if(valid)$fatal(1,"expired auto reacquire");
cmd=cmd+2;frame;frame;frame;if(!valid)$fatal(1,"manual new session");
rev=rev+1;frame;if(valid)$fatal(1,"parameter version reused confirmation");frame;frame;if(!valid)$fatal(1,"version reconfirm");
id=id+15;frame;if(valid || hv || reason!=6)$fatal(1,"long raw-frame gap did not expire");frame;frame;if(valid)$fatal(1,"long gap auto reselected");
// Too-close projected marks and out-of-frame extrapolation.
reset;candidates[127:0]=c(640,360,48);candidates[639:512]=c(650,360,48);frame;frame;frame;if(valid)$fatal(1,"short projection");
reset;candidates[127:0]=c(500,360,48);candidates[639:512]=c(800,360,48);frame;frame;frame;
for(k=0;k<7;k=k+1)begin candidates[127:0]=c(500-k*70,360,48);candidates[639:512]=c(800-k*70,360,48);frame;end
if(valid || reason!=7)$fatal(1,"outside tip visible %0d reason%0d",tx,reason);
complete=0;frame;if(valid || reason!=8)$fatal(1,"invalid frame tip");
$display("STABLE_TRACKER_ADVERSARIAL_PASS four quadrants, signed odd rounding, central multi-pair, area/direction identity, recovery/expiry, version, projection and outside");$finish;end endmodule