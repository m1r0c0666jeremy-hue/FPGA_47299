"""Independent integer arithmetic checks all shared fields, restart and reset."""
from refined_testlib import R,run
src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,latch=0;
reg [31:0] latency,age;reg [19:0] dwell;reg [6:0] gain,target;reg [7:0] k;reg [79:0] teaching;
wire [175:0] numbers;wire ready;
stage1_footer_numbers dut(clk,rst,latch,latency,age,dwell,gain,target,k,teaching,numbers,ready);
reg [175:0] expected,held;integer c,cycles;reg [31:0] seed=32'hbadcaffe;
function [31:0] rand32;input unused;begin seed=seed^(seed<<13);seed=seed^(seed>>17);seed=seed^(seed<<5);rand32=seed;end endfunction
function [31:0] decimal_ref;input [31:0] value;reg [31:0] v;integer i;begin
v=value;decimal_ref=0;for(i=0;i<8;i=i+1)begin decimal_ref[i*4+:4]=v%10;v=v/10;end end endfunction
task randomize_inputs;begin latency=rand32(0);age=rand32(0);dwell=rand32(0);gain=rand32(0);target=rand32(0);k=rand32(0);teaching={rand32(0),rand32(0),rand32(0)};
case(c%6)0:begin latency=0;age=0;dwell=0;end
1:begin latency=9999999;age=999;dwell=999900;end
2:begin latency=10000000;age=1000;dwell=1048575;end
3:begin latency=32'hffffffff;age=32'hffffffff;dwell=99;end
default:begin latency=rand32(0)%11000000;age=rand32(0)%1100;end endcase end endtask
task start;begin
expected[31:0]=decimal_ref(latency>9999999?9999999:latency);expected[63:32]=decimal_ref(age>999?999:age);
expected[79:64]=decimal_ref(dwell/100);expected[91:80]=decimal_ref(gain);expected[103:92]=decimal_ref(target);
expected[115:104]=decimal_ref(k);expected[131:116]=decimal_ref(teaching[34:19]/100);
expected[147:132]=decimal_ref(teaching[50:35]/100);expected[163:148]=decimal_ref(teaching[18:8]);expected[175:164]=decimal_ref(teaching[71:64]);
latch=1;@(negedge clk);latch=0;if(ready)$fatal(1,"old ready survived latch");end endtask
initial begin randomize_inputs;repeat(3)@(negedge clk);rst=1;
for(c=0;c<512;c=c+1)begin
@(negedge clk);randomize_inputs;start;
if(c%5==0)begin repeat(50)@(negedge clk);randomize_inputs;start;end
if(c%17==0)begin repeat(17)@(negedge clk);rst=0;@(negedge clk);if(ready)$fatal(1,"reset ready");rst=1;randomize_inputs;start;end
randomize_inputs;cycles=0;
while(!ready && cycles<350)begin @(negedge clk);cycles=cycles+1;end
if(!ready || numbers!==expected)$fatal(1,"numeric c%0d cycles%0d got%h expected%h",c,cycles,numbers,expected);
held=numbers;repeat(5)begin randomize_inputs;@(negedge clk);if(numbers!==held || !ready)$fatal(1,"uncommitted value leaked");end
end
$display("STAGE1_FOOTER_NUMBERS_PASS cases=512 ten-fields/clamp/div100/restart/reset/snapshot/deadline");$finish;
end endmodule'''
run('stage1_footer_numbers',src,[R/'rtl/color_regions/stage1_ui_formatter.v',R/'rtl/color_regions/stage1_ui_text.v'],timeout=120)
