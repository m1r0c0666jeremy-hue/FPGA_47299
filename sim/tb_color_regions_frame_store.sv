`timescale 1ns/1ps
module tb_color_regions_frame_store;
 reg clk=0,rst=0,beginf=0,write=0,result=0,snap=0;always #5 clk=~clk;
 reg [1:0] bank=0;reg [31:0] fid=0;reg [24:0] addr=0;reg [415:0] meta=0;reg [9:0] command=1;
 wire os,good;wire [450:0] data;integer checks=0;
 regions_frame_store #(.WORDS(4)) dut(clk,rst,beginf,bank,fid,write,addr,result,meta,snap,command,os,data,good);
 function [24:0] base;input [1:0] b;begin case(b)0:base=0;1:base=7000000;2:base=14000000;3:base=21000000;endcase end endfunction
 function [415:0] packet;input [31:0] id;input [9:0] cmd;input box;
 begin packet=0;packet[31:0]=id;packet[255]=1;packet[415:413]=1;packet[244]=cmd[0];packet[243]=cmd[9];packet[242:235]=cmd[8:1];packet[247]=1;packet[245]=box;packet[110:100]=11'd77;end endfunction
 task capture;input [1:0] b;input [31:0] id;input corrupt;integer k;
 begin
  @(negedge clk);beginf=1;bank=b;fid=id;
  @(negedge clk);beginf=0;
  for(k=0;k<4;k=k+1)begin write=1;addr=base(b)+k*8+(corrupt && k==2?8:0);@(negedge clk);end
  write=0;
 end endtask
 task send;input [415:0] p;begin @(negedge clk);meta=p;result=1;@(negedge clk);result=0;end endtask
 task snapshot;input [31:0] id;input [1:0] b;input has;
 begin
  @(negedge clk);snap=1;@(posedge clk);#1;
  if(!os || !data[450] || data[449:448]!==b || data[447:416]!==id || data[255]!==has)
     $fatal(1,"snapshot %h bank%0d meta%0d expected %h bank%0d meta%0d",data[447:416],data[449:448],data[255],id,b,has);
  if(has && data[31:0]!==id)$fatal(1,"cross-frame metadata");
  if(!has && data[415:0]!==416'd0)$fatal(1,"fallback must clear all candidates and sample");
  checks=checks+1;@(negedge clk);snap=0;
 end endtask
 initial begin
  repeat(4)@(negedge clk);rst=1;
  capture(0,10,0);snapshot(10,0,0);
  capture(3,9,0);send(packet(9,1,1));snapshot(9,3,1);
  send(packet(10,1,0));snapshot(10,0,1);if(data[245])$fatal(1,"empty latest did not replace old box");
  capture(1,11,0);snapshot(10,0,1);
  capture(2,12,0);snapshot(12,2,0);
  command=3;snapshot(12,2,0);send(packet(12,3,1));snapshot(12,2,1);
  // Reuse wins over an old result and same-cycle snapshot.
  @(negedge clk);beginf=1;bank=2;fid=16;result=1;meta=packet(12,3,1);snap=1;
  #1;if(good)$fatal(1,"old selection not invalidated at bank reuse");
  @(posedge clk);#1;if(data[449:448]==2)$fatal(1,"reused image selected");
  @(negedge clk);beginf=0;result=0;snap=0;
  snapshot(11,1,0);capture(3,13,1);snapshot(11,1,0);
  // Reset and wrap-around newest ordering.
  @(negedge clk);rst=0;@(negedge clk);rst=1;command=1;
  capture(0,32'hfffffffe,0);capture(1,32'hffffffff,0);send(packet(32'hffffffff,1,1));
  capture(2,0,0);snapshot(32'hffffffff,1,1);send(packet(0,1,0));snapshot(0,2,1);
  // The last legal DDR word and result are eligible for a snapshot that cycle.
  @(negedge clk);beginf=1;bank=3;fid=1;@(negedge clk);beginf=0;
  write=1;addr=base(3);@(negedge clk);addr=base(3)+8;@(negedge clk);addr=base(3)+16;
  @(negedge clk);addr=base(3)+24;result=1;meta=packet(1,1,1);snap=1;
  @(posedge clk);#1;if(data[447:416]!==1 || !data[255] || !data[245])$fatal(1,"last-word bypass");
  checks=checks+1;
  $display("PASS functional frame store: %0d selections, actual bank, empty/latest, command, age, reuse, wrap and same-cycle finish",checks);$finish;
 end
endmodule
