"""Actual vendor CSI16/RAW10 unpack to the FHD full-line asynchronous bridge."""
from refined_testlib import R,run
mods=[R/f'rtl/color_regions/{n}.v' for n in ('fhd_raw_bridge','fhd_isp_line_ram','refined_reset_bridge')]
mods += [R/f'user_source/hdl_source/isp/{n}.v' for n in ('csi_unpacket_2lane','raw10_unpacket_2lane')]
s=r'''`timescale 1ns/1ps
module tb;
reg rx=0,proc=0,rst=0,hs=0;reg [15:0] hsd=0;
always #4.167 rx=~rx;always #8.333 proc=~proc;
wire fs,fe,cv,ch,rs,re,rv;wire [31:0] cd;wire [39:0] rd;
csi_unpacket_2lane csi(rx,rst,hs,hsd,fs,fe,cv,ch,cd);
raw10_unpacket_2lane raw(rx,rst,fs,fe,cv,cd,10'd0,rs,re,rv,rd);
reg oldhs=0,seen=0;reg [7:0] tail=0;reg [31:0] seq=0,stamp=0;
always @(posedge rx)if(!rst)begin oldhs<=0;seen<=0;tail<=0;seq<=0;stamp<=0;end
else begin
 oldhs<=ch;tail<={tail[6:0],oldhs && !ch && seen};
 if(cv)seen<=1;if(oldhs && !ch)seen<=0;
 if(fs)begin seq<=seq+1;stamp<=1234+seq;end
end
wire [39:0] q;wire qv,qs,ql,ab;wire [31:0] qid,qus,ov,bad;
fhd_raw_bridge #(.HEIGHT(3)) dut(rx,proc,rst,rs,re,rv,tail[7],rd,seq,stamp,q,qv,qs,ql,ab,qid,qus,ov,bad);
integer count=0,heads=0,lasts=0,groups=0,raw_sofs=0,csi_ends=0,abort_count=0;
function [39:0] expected;input integer n;begin
 expected={10'((n*4+3)%1024),10'((n*4+2)%1024),10'((n*4+1)%1024),10'((n*4)%1024)};end endfunction
always @(negedge rx)if(rst)begin if(rv)groups=groups+1;if(rs)raw_sofs=raw_sofs+1;if(tail[7])csi_ends=csi_ends+1;end
always @(negedge proc)if(rst)begin
 if(ab)abort_count=abort_count+1;
 if(qv)begin
  if(q!==expected(count))$fatal(1,"CSI/RAW packing index%0d got%h expected%h",count,q,expected(count));
  if(qid!=1 || qus!=1234)$fatal(1,"CSI SOF metadata mismatch");
  count=count+1;if(qs)heads=heads+1;if(ql)lasts=lasts+1;
 end
end
task beat;input [15:0] word;begin @(negedge rx);hs=1;hsd=word;end endtask
task stop_packet;begin @(negedge rx);hs=0;hsd=0;repeat(30)@(negedge rx);end endtask
task short_packet;input [7:0] dt;begin beat({dt,8'd0});beat(16'd0);stop_packet();end endtask
reg [7:0] bytes[0:2399];integer y,x,g,p0,p1,p2,p3;
initial begin
 repeat(8)@(negedge rx);rst=1;repeat(8)@(negedge rx);short_packet(0);
 for(y=0;y<3;y=y+1)begin
  for(g=0;g<480;g=g+1)begin
   p0=((y*480+g)*4)%1024;p1=(p0+1)%1024;p2=(p0+2)%1024;p3=(p0+3)%1024;
   bytes[g*5]=p0>>2;bytes[g*5+1]=p1>>2;bytes[g*5+2]=p2>>2;bytes[g*5+3]=p3>>2;
   bytes[g*5+4]={2'(p3&3),2'(p2&3),2'(p1&3),2'(p0&3)};
  end
  beat({8'h2b,8'h60});beat({8'h09,8'h00});
  for(x=0;x<2400;x=x+2)beat({bytes[x],bytes[x+1]});
  beat(16'd0);stop_packet();repeat(2000)@(negedge rx);
 end
 short_packet(1);repeat(1000)@(negedge proc);
 if(count!=1440 || heads!=1 || lasts!=3 || groups!=1440 || csi_ends!=3 || raw_sofs!=1 || abort_count || bad || ov)
 $fatal(1,"chain counts out%0d heads%0d ends%0d raw%0d CSIends%0d rawSOFs%0d abort%0d bad%0d",count,heads,lasts,groups,csi_ends,raw_sofs,abort_count,bad);
 $display("FHD_CSI_BRIDGE_PASS real CSI headers/2400-byte lines, RAW10 bit ordering, EOL drain, contiguous480 and original SOF identity/time");$finish;
end
initial begin #1000000;$fatal(1,"watchdog");end
endmodule'''
run('fhd_actual_csi_bridge',s,mods,compile_args=['-DFHD_BEHAVIORAL_RAM'])
