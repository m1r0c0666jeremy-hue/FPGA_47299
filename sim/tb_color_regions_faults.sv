`timescale 1ns/1ps
module tb_color_regions_faults;
reg clk=0;always #5 clk=~clk;
reg rst=0,sof=0,valid=0,fault=0,pair=0,en=1,ready=1;
reg [7:0] session=1;reg [95:0] rgb=0;
wire [31:0] id,dropped;wire ov;wire [415:0] meta;
regions_capture dut(clk,rst,sof,valid,fault,rgb,pair,en,session,ready,id,ov,meta,dropped);
integer f,g,lane,x,y,outputs=0,confirmed=0;reg [7:0] gray;reg [23:0] pixel;
function [23:0] scene(input integer xx,yy,ff);
reg [7:0] v;
begin
 scene=24'h686868;
 if(ff>=6 && xx>=300 && xx<320 && yy>=200 && yy<220)scene=24'h505028;
 if(ff>=6 && xx>=600 && xx<640 && yy>=300 && yy<320)scene=24'h302030;
 if(xx>=636 && xx<644 && yy>=356 && yy<364)begin
   v=64+(yy-356)*8+xx-636;scene={v,v,v};
 end
end endfunction
always @(negedge clk)if(ov)begin
 outputs=outputs+1;
 if(meta[31:0]!=outputs || !meta[255] || meta[415:413]!=1)$fatal(1,"frame header/order %d/%d",meta[31:0],outputs);
 if(meta[247] !== !(outputs==1 || outputs==3 || outputs==4))$fatal(1,"full flag id%0d",outputs);
 if(!meta[247] && (meta[245] || meta[246] || meta[318] || meta[382] || meta[408]))$fatal(1,"invalid frame published result");
 if(meta[247] && (!meta[408] || meta[407:384]!==24'h5f5f5f))$fatal(1,"same64 sample id%0d %h",outputs,meta[407:384]);
 if(meta[244] !== (outputs!=5) || meta[243] !== (outputs>=6) || meta[242:235] !== (outputs>=6?8'd2:8'd1))$fatal(1,"SOF command identity id%0d",outputs);
 if(outputs<10 && (meta[245] || meta[246] || meta[318] || meta[382]))$fatal(1,"premature/stale confirmation id%0d",outputs);
 if(outputs>=10)begin
  if(!meta[245] || !meta[246] || meta[318] || meta[382])$fatal(1,"recovery failed id%0d",outputs);
  if(meta[141:100]!=={10'd219,10'd200,11'd319,11'd300} || meta[183:142]!=={10'd319,10'd300,11'd639,11'd600})$fatal(1,"recovery box");
  confirmed=confirmed+1;
 end
 $display("PASS fault result id=%0d complete=%0d enable=%0d pair=%0d sample=%h boxes=%b%b",outputs,meta[247],meta[244],meta[243],meta[407:384],meta[245],meta[246]);
end
initial begin
 repeat(4)@(negedge clk);rst=1;repeat(2000)@(negedge clk);
 for(f=1;f<=11;f=f+1)begin
  @(negedge clk);sof=1;valid=0;fault=0;en=f!=5;pair=f>=6;session=f>=6?2:1;
  if(f!=2)begin @(negedge clk);sof=0;end
  for(g=0;g<(f==1?657:f==3?230401:230400);g=g+1)begin
   valid=1;x=(g%320)*4;y=g/320;
   for(lane=0;lane<4;lane=lane+1)rgb[95-lane*24-:24]=scene(x+lane,y,f);
   fault=f==4 && g==100;
   if(f==6 && g==1000)begin pair=0;session=44;end // Mid-frame controls cannot retag data.
   @(negedge clk);sof=0;
   if(g%113==0 && f==2)begin valid=0;@(negedge clk);end
  end
  valid=0;fault=0;repeat(450)@(negedge clk);
 end
 sof=1;@(negedge clk);sof=0;repeat(200000)@(negedge clk);
 if(outputs!=11 || confirmed!=2 || dropped!=0)$fatal(1,"outputs%0d confirmed%0d drops%0d",outputs,confirmed,dropped);
 $display("PASS capture faults: short/long/fault, simultaneous SOF+pixel, valid bubbles, stop/restart, colour/session change, exact centre RGB, recovery");$finish;
end
initial begin #50000000;$fatal(1,"timeout");end
endmodule
