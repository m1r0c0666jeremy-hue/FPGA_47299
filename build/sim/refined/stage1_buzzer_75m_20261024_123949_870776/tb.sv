`timescale 1ns/1ps
module tb #(parameter HZ=40000);
reg clk=0;always #6.667 clk=~clk;reg rst=0,enable=0;wire buzzer;
stage1_buzzer #(.CLOCK_HZ(HZ)) dut(clk,rst,enable,buzzer);
integer k,toggles=0;reg previous=1;
initial begin
repeat(3)@(negedge clk);if(buzzer!==1)$fatal(1,"reset not silent");rst=1;enable=1;
for(k=0;k<HZ+HZ/4000+4;k=k+1)begin
@(negedge clk);if(buzzer!=previous)toggles=toggles+1;previous=buzzer;
if(k>HZ/5+10 && k<HZ-10 && buzzer!==1)$fatal(1,"quiet interval or counter width wrong cycle%0d",k);
end
if(toggles<790 || toggles>810)$fatal(1,"2kHz/200ms cadence changed edges%0d",toggles);
if(buzzer!==0)$fatal(1,"one-second counter did not wrap and start next tone");
enable=0;repeat(5)@(negedge clk);if(buzzer!==1)$fatal(1,"mute not silent");
rst=0;#1;if(buzzer!==1)$fatal(1,"async reset not silent");
if(HZ==40000)$display("STAGE1_BUZZER_PASS high-silent/reset/2kHz/cadence/mute");
else $display("STAGE1_BUZZER_75M_PASS full75000000-cycle-wrap/2kHz/200ms/quiet/mute/reset/same-domain-top");
$finish;end endmodule