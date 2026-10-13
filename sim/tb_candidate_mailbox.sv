`timescale 1ns/1ps
module tb_candidate_mailbox;
 reg sc=0,dc=0,rst=0,send=0;always #6.667 sc=~sc;always #8.13 dc=~dc;
 reg [255:0] data=0;wire ready,valid;wire [255:0] got;
 target_mailbox dut(sc,rst,send,data,ready,dc,rst,valid,got);
 integer i,received=0;
 function [255:0] packet(input integer n);integer j;begin
  for(j=0;j<8;j=j+1)packet[j*32+:32]=n^(32'h87654321*j);
 end endfunction
 always @(negedge dc)if(rst&&valid)begin
  if(got!==packet(received))$fatal(1,"torn/missing CDC packet #%d",received);
  received=received+1;
 end
 initial begin
  repeat(5)@(negedge sc);rst=1;
  for(i=0;i<100;i=i+1)begin
   @(negedge sc);while(!ready)@(negedge sc);
   data=packet(i);send=1;@(negedge sc);send=0;data=~data;
  end
  repeat(20)@(negedge dc);if(received!=100)$fatal;
  $display("PASS bundled CDC: 100 coherent 256-bit transactions, asynchronous clocks");$finish;
 end
endmodule
