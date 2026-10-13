`timescale 1ns/1ps
module tb_color_regions_roi;
reg clk=0,rst=0,sof=0;wire [415:0] meta;wire [31:0] id,drop;wire ov;
regions_capture dut(clk,rst,sof,1'b0,1'b0,96'd0,1'b0,1'b1,8'd1,1'b1,id,ov,meta,drop);
task tick;begin #5;clk=1;#5;clk=0;end endtask
function [41:0] box(input integer x0,x1,y0,y1);begin box={10'(y1),10'(y0),11'(x1),11'(x0)};end endfunction
function [127:0] candidate(input integer x0,x1,y0,y1,input [1:0] membership);
begin candidate=0;candidate[120]=1;candidate[41:0]=box(x0,x1,y0,y1);candidate[91:90]=membership;end endfunction
reg [167:0] old_rois,expected;integer i;
initial begin
 tick;rst=1;repeat(2000)tick;
 // Exact union-boundary semantics: duplicate ROIs do not hide a cut edge.
 dut.sp=0;dut.active_rv=3;dut.active_rois={84'd0,box(100,120,40,70),box(100,120,40,70)};
 dut.cp[3]=1;dut.xp[3]=100;dut.yp[3]=60;force dut.hits=16'h1111;#1;
 if(dut.ma!==4'b1111 || dut.ca!==4'b0001)$fatal(1,"duplicate ROI exterior %b",dut.ca);
 // Adjacent ROIs jointly cover the seam; every pixel is counted once.
 dut.active_rois={84'd0,box(102,120,40,70),box(90,101,40,70)};#1;
 if(dut.ma!==4'b1111 || dut.ca!==4'b0000)$fatal(1,"adjacent ROI seam %b",dut.ca);
 dut.active_rv=1;dut.active_rois={126'd0,box(0,20,0,20)};dut.xp[3]=0;dut.yp[3]=0;#1;
 if(dut.ca!==0)$fatal(1,"real frame border must be allowed");release dut.hits;
 // Serial frame-background arithmetic must publish all four slots atomically.
 old_rois={4{box(1,10,1,10)}};dut.next_rois=old_rois;dut.next_rv=15;dut.roi_command=3;
 dut.worker_bank=0;dut.commands[0]=3;dut.complete=1;dut.failed=0;dut.clipped=0;dut.state=5;
 dut.candidates={candidate(900,919,500,519,2),candidate(600,619,300,319,1),candidate(300,319,200,219,2),candidate(100,119,100,119,1)};
 force dut.confirm_done=1;force dut.grid_boxes=168'd0;force dut.grid_valid=0;force dut.grid_failed=0;force dut.dx=0;force dut.dy=0;
 tick;release dut.confirm_done;
 for(i=0;i<4;i=i+1)begin
  if(i==1)sof=1;else sof=0;
  tick;
  if(dut.next_rois!==old_rois || dut.next_rv!==15)$fatal(1,"partially published ROI slot%0d",i);
  if(i==1 && dut.frame_rois!==old_rois)$fatal(1,"SOF captured mixed old/new ROIs");
 end
 sof=0;tick;
 expected={box(836,983,436,583),box(536,683,236,383),box(236,383,136,283),box(36,183,36,183)};
 if(dut.next_rois!==expected || dut.next_rv!==15 || dut.roi_command!==3)$fatal(1,"atomic ROI update result");
 $display("PASS ROI: duplicate/adjacent union, real frame edge, four-slot expansion and SOF collision atomicity");$finish;
end
endmodule
