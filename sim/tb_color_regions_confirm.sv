`timescale 1ns/1ps
module tb_color_regions_confirm;
reg clk=0;always #5 clk=~clk;
reg rst_n=0,start=0;reg [31:0] frame_id=0;reg [9:0] command=1;
reg frame_good=1;reg [1:0] color_bad=0;reg [511:0] candidates=0;
wire busy,done;wire [511:0] confirmed;wire [43:0] mx;wire [39:0] my;
regions_confirm u(clk,rst_n,start,frame_id,command,frame_good,color_bad,candidates,busy,done,confirmed,mx,my);
function [127:0] item(input integer x,input integer y);
begin item=0;item[120]=1;item[72:62]=x;item[82:73]=y;end endfunction
task frame(input integer id,input [3:0] expected);
begin @(negedge clk);frame_id=id;start=1;@(negedge clk);start=0;
wait(done);#1;
if({confirmed[504],confirmed[376],confirmed[248],confirmed[120]}!==expected)
$fatal(1,"frame %d validity got %b expected %b",id,{confirmed[504],confirmed[376],confirmed[248],confirmed[120]},expected);
@(negedge clk);end endtask
initial begin
repeat(3)@(negedge clk);rst_n=1;
candidates={item(800,100),item(600,100),item(300,100),item(100,100)};
frame(1,0);frame(1,0);frame(2,0);frame(3,15);
candidates={item(600,100),item(800,100),item(100,100),item(300,100)};
frame(4,15);frame(6,0);frame(7,0);frame(8,15);
candidates[120]=0;frame(9,14);candidates[127:0]=item(300,100);frame(10,14);frame(11,14);frame(12,15);
candidates[127:0]=item(397,100);frame(13,14);frame(14,14);frame(15,15);
color_bad=1;frame(16,12);color_bad=0;frame(17,12);frame(18,12);frame(19,15);
command=3;frame(20,0);frame(21,0);frame(22,15);
frame_good=0;frame(23,0);frame_good=1;frame(24,0);frame(25,0);frame(26,15);
command=2;frame(27,0);command=3;frame(28,0);frame(29,0);frame(30,15);
$display("PASS confirmation: duplicates, identity swaps, gap, missing, jump, bad colour, session, invalid, enable");$finish;
end
endmodule
