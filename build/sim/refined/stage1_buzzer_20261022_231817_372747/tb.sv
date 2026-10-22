module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,enable=0;wire buzzer;
stage1_buzzer #(.CLOCK_HZ(40000)) dut(clk,rst,enable,buzzer);
integer n,toggles=0;reg previous=1;
initial begin repeat(3)@(negedge clk);if(buzzer!==1)$fatal(1,"reset beep");rst=1;enable=1;
for(n=0;n<40005;n=n+1)begin @(negedge clk);if(buzzer!=previous)toggles=toggles+1;previous=buzzer;
if(n>8010 && n<39990 && buzzer!==1)$fatal(1,"quiet interval not high");end
if(toggles<790 || toggles>810)$fatal(1,"tone frequency/cadence wrong %0d",toggles);
enable=0;repeat(5)@(negedge clk);if(buzzer!==1)$fatal(1,"mute failed");
$display("STAGE1_BUZZER_PASS high-silent/reset/2kHz/cadence/mute");$finish;end
endmodule