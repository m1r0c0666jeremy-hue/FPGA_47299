"""Check fractional microseconds and Gray-code CDC at the actual pixel rate."""
from refined_testlib import R,run
src=r'''`timescale 1ns/1ps
module tb;
reg clk=0,rst=0;always #6.734006734 clk=~clk;
wire [31:0] us,gray;refined_timebase dut(clk,rst,us,gray);
integer i,prev_us=0,age=0;reg [31:0] prev_gray=0;reg [31:0] changed;
initial begin
repeat(3)@(negedge clk);rst=1;
for(i=1;i<=297000;i=i+1)begin
 @(posedge clk);#1;
 if(us!==((i*4)/297))$fatal(1,"cumulative microsecond drift cycle=%0d us=%0d",i,us);
 if(gray!==((us>>1)^us))$fatal(1,"Gray encoding mismatch");
 changed=gray^prev_gray;
 if(changed && (changed&(changed-1)))$fatal(1,"multiple Gray bits change");
 age=age+1;
 if(us!=prev_us)begin
 if(age!=74 && age!=75)$fatal(1,"tick interval %0d",age);
 age=0;prev_us=us;end
 prev_gray=gray;
end
if(us!=4000)$fatal(1,"4ms epoch wrong");
$display("FHD_TIMEBASE_PASS 297000 cycles=4000us, one-bit Gray transitions, 74/75-cycle ticks");$finish;
end endmodule'''
run('fhd_timebase',src,[R/'rtl/color_regions/refined_timebase.v'])
