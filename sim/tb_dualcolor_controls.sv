`timescale 1ns/1ps
module tb_dualcolor_controls;
 reg clk=0,rst=0;always #5 clk=~clk;
 reg [2:0] keys=7;reg [1:0] sw=0;reg ack=0;
 wire req,up,tracking,show,conflict,pair;wire [1:0] zoom;wire [7:0] session;
 target_controls #(.CYCLES_PER_MS(10)) dut(clk,rst,keys,sw,ack,req,up,zoom,tracking,show,session,conflict,pair);
 task wait_ms(input integer n);repeat(n*10) @(negedge clk);endtask
 task release_all;begin keys=7;wait_ms(30);end endtask
 task gesture(input integer duration);begin keys=5;wait_ms(duration);keys=7;wait_ms(30);end endtask
 initial begin
  repeat(4)@(negedge clk);rst=1;release_all;
  if(!show||pair||tracking)$fatal(1,"defaults");
  gesture(5);if(tracking||!show)$fatal(1,"bounce");
  keys=5;wait_ms(100);if(tracking)$fatal(1,"short must wait release");
  release_all;if(!tracking||session!=1||!show)$fatal(1,"short");
  gesture(999);if(tracking||!show||session!=2)$fatal(1,"999ms must short");
  gesture(1000);if(tracking||show||session!=2)$fatal(1,"1000ms must long");
  gesture(1001);if(tracking||!show||session!=2)$fatal(1,"1001ms must long");
  keys=5;wait_ms(3500);if(show||tracking||session!=2)$fatal(1,"long repeated");
  release_all;if(show||tracking)$fatal(1,"long release short");
  gesture(80);if(!tracking||show)$fatal(1,"hidden start");
  sw=2;wait_ms(30);if(!pair||session!=4||!tracking||show)$fatal(1,"pair/session");
  keys=5;wait_ms(500);keys=4;wait_ms(30);if(!conflict)$fatal;
  keys=5;wait_ms(1200);release_all;
  if(!tracking||show||session!=4)$fatal(1,"conflict gesture not cancelled");
  gesture(80);if(tracking||session!=5)$fatal;
  sw=1;wait_ms(30);if(pair||session!=6)$fatal;
  keys=6;wait_ms(30);if(!up||!req)$fatal(1,"SW4 gain up");ack=req;
  sw=2;wait_ms(160);if(!up)$fatal(1,"latched gain");ack=req;
  release_all;keys=6;wait_ms(30);if(up)$fatal(1,"SW4 gain down");ack=req;
  release_all;sw=1;wait_ms(30);keys=3;wait_ms(30);if(zoom!=1)$fatal;
  wait_ms(610);if(zoom!=2)$fatal;release_all;
  keys=5;wait_ms(100);rst=0;wait_ms(3);rst=1;wait_ms(1200);
  if(tracking||!show||zoom!=0)$fatal(1,"reset held key");release_all;
  gesture(80);if(!tracking)$fatal(1,"rearm after reset");
  $display("PASS dualcolor controls: 999/1000/1001ms, held, conflict, reset, SW4 gain, pair session");$finish;
 end
 initial begin #3000000;$fatal(1,"timeout");end
endmodule
