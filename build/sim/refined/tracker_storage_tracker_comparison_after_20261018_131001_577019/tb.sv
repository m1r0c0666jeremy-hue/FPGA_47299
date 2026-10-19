module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;reg [31:0] id=0;reg [1023:0] candidates=0;
wire done,valid,hv;wire [127:0] a,b;wire [10:0] tx;wire [9:0] ty;wire [3:0] reason;wire [83:0] boxes;wire [1:0] state;
stable_tracker dut(clk,rst,start,id,10'd3,16'd0,1'b1,candidates,done,a,b,valid,tx,ty,reason,hv,boxes,state,,,,,);
function [127:0] c(input integer x,y);begin c=0;c[120]=1;c[61:42]=256;c[72:62]=x;c[82:73]=y;c[89:83]=100;end endfunction
task frame;integer n;begin @(negedge clk);id=id+1;start=1;@(negedge clk);start=0;n=0;while(!done && n<200)begin @(negedge clk);n=n+1;end if(!done)$fatal(1,"tracker timeout");end endtask
initial begin repeat(4)@(negedge clk);rst=1;candidates[127:0]=c(640,330);candidates[639:512]=c(640,550);
frame;frame;frame;if(!valid || tx!=640 || ty!=220)$fatal(1,"midpoint guide failed");
rst=0;repeat(3)@(negedge clk);rst=1;id=0;candidates=0;candidates[127:0]=c(640,300);candidates[639:512]=c(640,310);frame;
if(a[111:104]!=4 || !a[120] || !b[120] || valid)$fatal(1,"invalid slots contaminated rejection %h",a);
$display("REFINED_TRACKER_COMPARISON_PASS after midpoint and per-pair rejection");$finish;end endmodule