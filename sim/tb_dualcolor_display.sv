`timescale 1ns/1ps
module tb_dualcolor_display;
 reg clk=0,rst=0,vs=0,de=0,snapshot=0,tracking=0,show=1,conflict=0,live=1;
 always #6.667 clk=~clk;
 reg [290:0] data=0;reg [7:0] session=1;reg [1:0] zoom=2,mode=0;
 reg pair=0;wire displayed_pair;wire commit,shown,tip;wire [1:0] bank,z,m;wire [31:0] fid;
 wire [10:0] cx,x0;wire [9:0] cy,y0;wire [255:0] meta;wire [2:0] state;
 target_display dut(clk,rst,vs,de,snapshot,data,tracking,show,conflict,live,session,zoom,mode,
 commit,bank,fid,cx,x0,cy,y0,z,m,meta,shown,tip,state,pair,displayed_pair);
 task frame(input integer id,ss,x,y,valid_tip,source_id);begin
  @(negedge clk);vs=1;de=0;
  repeat(4)@(negedge clk);vs=0;
  data=0;data[290]=1;data[289:288]=2;data[287:256]=id;data[31:0]=source_id;
  data[244]=1;data[243]=pair;data[32]=valid_tip;data[242:235]=ss;data[89:79]=x;data[99:90]=y;
  snapshot=1;@(negedge clk);snapshot=0;
  if(!commit)$fatal(1,"no commit");
 end endtask
 initial begin
  repeat(4)@(negedge clk);rst=1;repeat(2)@(negedge clk);
  if(state!=0||cx!=640||cy!=360)$fatal(1,"defaults");
  tracking=1;frame(5,1,900,450,1,5);
  if(!tip||state!=2||x0!=740||y0!=372||cx!=900)$fatal(1,"valid follow");
  frame(6,1,100,100,1,5);if(tip||cx!=900||state!=3)$fatal(1,"mismatched frame moved ROI");
  frame(7,0,100,100,1,7);if(tip||cx!=900)$fatal(1,"stale session");
  frame(8,1,1270,715,1,8);if(!tip||x0!=960||y0!=564)$fatal(1,"edge clamp");
  show=0;frame(9,1,800,400,1,9);if(shown||!tip||cx!=800)$fatal(1,"hidden tracking stopped");
  tracking=0;#1;if(tip)$fatal(1,"stopped tip stale");
  frame(10,1,600,300,1,10);if(cx!=800||state!=4)$fatal(1,"stopped viewport moved");
  tracking=1;session=2;frame(11,1,100,100,1,11);if(tip||cx!=800)$fatal;
  // Late response is discarded once active video starts.
  @(negedge clk);vs=1;repeat(3)@(negedge clk);vs=0;de=1;
  @(negedge clk);data[242:235]=2;snapshot=1;
  @(negedge clk);snapshot=0;if(commit||cx!=800)$fatal(1,"late snapshot accepted");
  de=0;frame(12,2,800,400,1,12);if(!tip)$fatal;
  repeat(16)frame(12,2,800,400,1,12);
  if(tip||state!=3)$fatal(1,"stopped camera retained live tip");
  frame(13,2,810,410,1,13);if(!tip)$fatal(1,"fresh frame did not recover");
  pair=1;session=3;#1;if(tip)$fatal(1,"pair stale tip");
  frame(14,2,100,100,1,14);if(tip||cx!=810)$fatal(1,"old session after pair");
  frame(15,3,820,420,1,15);if(!tip||!displayed_pair)$fatal(1,"new pair");
  // A forged matching-session but wrong-pair result must be rejected.
  @(negedge clk);vs=1;de=0;repeat(4)@(negedge clk);vs=0;
  data[243]=0;data[287:256]=16;data[31:0]=16;snapshot=1;
  @(negedge clk);snapshot=0;if(tip||cx!=820)$fatal(1,"wrong pair accepted");
  // Visibility commits at VS even without a DDR snapshot.
  show=1;@(negedge clk);vs=1;repeat(3)@(negedge clk);vs=0;
  if(!shown)$fatal(1,"visibility depends on snapshot");
  live=0;#1;if(state!=6||tip)$fatal;
  $display("PASS display: frame/session match, follow, bounds, hide, stop, late response, video fault");$finish;
 end
endmodule
