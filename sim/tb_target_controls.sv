`timescale 1ns/1ps
module tb_target_controls;
 reg clk=0,rst=0;always #5 clk=~clk;
 reg [2:0] keys=7;reg [1:0] sw=0;reg ack=0;
 wire req,up,tracking,show,conflict;wire [1:0] zoom;wire [7:0] session;
 target_controls #(.CYCLES_PER_MS(3)) dut(clk,rst,keys,sw,ack,req,up,zoom,tracking,show,session,conflict);
 task wait_ms(input integer n);repeat(n*3) @(negedge clk);endtask
 task release_all;begin keys=7;wait_ms(30);end endtask
 initial begin
  repeat(4)@(negedge clk);rst=1;release_all;
  keys=5;wait_ms(5);keys=7;wait_ms(30);if(tracking)$fatal(1,"bounce toggled");
  keys=5;wait_ms(30);if(!tracking||session!=1)$fatal(1,"first start");
  wait_ms(1600);if(!tracking||session!=1)$fatal(1,"held KEY3 repeated");
  release_all;keys=5;wait_ms(30);if(tracking||session!=2)$fatal(1,"stop");
  release_all;keys=4;wait_ms(30);if(!conflict)$fatal;
  keys=5;wait_ms(30);if(tracking||session!=2)$fatal(1,"conflict release triggered KEY3");
  release_all;keys=5;wait_ms(30);if(!tracking||session!=3)$fatal;
  release_all;sw=2;wait_ms(30);if(!show)$fatal;
  keys=6;wait_ms(30);if(!up||!req)$fatal(1,"gain up");ack=req;
  sw=0;wait_ms(170);if(!up)$fatal(1,"gain direction must remain latched");ack=req;
  release_all;keys=6;wait_ms(30);if(up||show)$fatal(1,"gain down / show off");ack=req;
  release_all;sw=1;wait_ms(30);keys=3;wait_ms(30);if(zoom!=1)$fatal(1,"zoom in");
  wait_ms(610);if(zoom!=2)$fatal;release_all;
  sw=0;wait_ms(30);keys=3;wait_ms(30);if(zoom!=1)$fatal(1,"zoom out");
  rst=0;wait_ms(2);rst=1;wait_ms(50);if(tracking||zoom!=0||session!=0)$fatal(1,"reset while held");
  release_all;
  $display("PASS target controls: debounce, toggle, hold, conflict, gain latch, zoom, reset");$finish;
 end
 initial begin #1000000;$fatal(1,"controls timeout");end
endmodule
