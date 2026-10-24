`timescale 1ns/1ps
module tb_candidate_diagnostics;
 reg clk=0,rst=0;always #5 clk=~clk;
 reg [19:0] a,b;reg [6:0] fa,fb;
 wire [23:0] da,db;wire [11:0] dfa,dfb;
 target_diagnostics dut(clk,rst,a,b,fa,fb,da,db,dfa,dfb);
 function [23:0] decimal(input integer v);
  integer j;begin decimal=0;for(j=0;j<6;j=j+1)begin decimal[j*4+:4]=v%10;v=v/10;end end
 endfunction
 integer i;
 initial begin
  a=0;b=0;fa=0;fb=0;repeat(4)@(negedge clk);rst=1;
  for(i=0;i<202;i=i+1)begin
   @(negedge clk);a=i==0?0:i==1?921600:$urandom_range(0,921600);
   b=i==0?64:i==1?20000:$urandom_range(0,921600);fa=i%101;fb=100-(i%101);
   repeat(46)@(negedge clk);
   if(da!==decimal(a)||db!==decimal(b)||dfa!==decimal(fa)||dfb!==decimal(fb))$fatal(1,"decimal conversion %0d",i);
  end
  $display("PASS diagnostics decimal: 202 cases, count 0..921600, fill 0..100");$finish;
 end
endmodule
