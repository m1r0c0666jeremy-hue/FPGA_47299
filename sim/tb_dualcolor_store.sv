`timescale 1ns/1ps
module tb_dualcolor_store;
 reg clk=0,rst=0,start=0,wr=0,result=0,snap=0;always #7.5 clk=~clk;
 reg [1:0] bank=0,read_bank=0;reg [31:0] id=0;reg [24:0] addr=0;reg [255:0] meta=0;
 wire valid,good;wire [290:0] data;
 target_frame_store #(.WORDS(16)) dut(clk,rst,start,bank,id,wr,addr,result,meta,snap,read_bank,valid,data,good);
 task begin_frame(input integer b,f);begin
  @(negedge clk);bank=b;id=f;start=1;
  @(negedge clk);start=0;
 end endtask
 task write_words(input integer b,n);integer i;begin
  for(i=0;i<n;i=i+1)begin @(negedge clk);wr=1;addr=b*7000000+i*8;end
  @(negedge clk);wr=0;
 end endtask
 task result_for(input integer f);begin
  @(negedge clk);meta=0;meta[31:0]=f;meta[32]=1;meta[89:79]=731;result=1;
  @(negedge clk);result=0;
 end endtask
 task snapshot(input integer b);begin
  @(negedge clk);read_bank=b;snap=1;
  @(negedge clk);snap=0;if(!valid)$fatal;
 end endtask
 initial begin
  repeat(4)@(negedge clk);rst=1;
  snapshot(0);if(data[290]||good)$fatal(1,"uninitialized bank valid");
  begin_frame(0,100);write_words(0,16);result_for(100);snapshot(0);
  if(!good||!data[290]||!data[32]||data[31:0]!=100||data[287:256]!=100)$fatal(1,"matched snapshot");
  begin_frame(1,101);write_words(1,15);result_for(101);snapshot(1);
  if(good||data[290]||data[32])$fatal(1,"short write bank valid");
  snapshot(0);if(!good)$fatal;
  begin_frame(0,104);if(good)$fatal(1,"overwritten selected generation still good");
  result_for(100);write_words(0,16);snapshot(0);
  if(!good||!data[290]||data[32]||data[287:256]!=104)$fatal(1,"stale metadata accepted");
  result_for(104);snapshot(0);if(!data[32]||data[31:0]!=104)$fatal;
  @(negedge clk);wr=1;addr=128;@(negedge clk);wr=0;
  if(good)$fatal(1,"overlong frame valid");
  begin_frame(2,106);@(negedge clk);wr=1;addr=14000008;@(negedge clk);wr=0;
  write_words(2,16);result_for(106);snapshot(2);if(data[290]||data[32])$fatal(1,"out of order write valid");
  $display("PASS frame store: matching, missing, overwritten, stale, short, long, nonsequential");$finish;
 end
endmodule
