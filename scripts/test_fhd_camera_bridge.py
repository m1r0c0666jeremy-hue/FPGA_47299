"""Native-rate RAW40 bridge: full-width lines, asynchronous phase, faults/reset.

BRAM is modeled with the declared one-cycle NOREG read-before-write semantics.
The actual PH1P primitive remains a TD elaboration/implementation check.
"""
from refined_testlib import R,run
mods=[R/f'rtl/color_regions/{n}.v' for n in ('fhd_raw_bridge','fhd_isp_line_ram','refined_reset_bridge')]
source=r'''`timescale 1ns/1ps
module tb;
reg rx=0,proc=0,run_proc=1,rst=0,sof=0,eof=0,v=0,eol=0;
always #4.167 rx=~rx;
always #8.333 if(run_proc)proc=~proc;
reg [39:0] d=0;reg [31:0] id=0,us=0;
wire [39:0] q;wire qv,qs,ql,abort_frame;wire [31:0] qid,qus,overflows,bad;
fhd_raw_bridge #(.HEIGHT(3),.IDLE_LIMIT(10000)) dut(rx,proc,rst,sof,eof,v,eol,d,id,us,
 q,qv,qs,ql,abort_frame,qid,qus,overflows,bad);
integer counts[0:15];integer heads[0:15];integer linebeat=0,linegap=10000,aborts=0,j,k,oldid=-1;
reg prev=0;
always @(negedge proc)if(rst)begin
 if(abort_frame)begin aborts=aborts+1;linebeat=0;prev=0;end
 if(qv)begin
  if(qid!=q/1000000 || qus!=qid*37)$fatal(1,"source metadata/data mismatch id%0d d%0d us%0d",qid,q,qus);
  if(qid!=oldid)begin linebeat=0;oldid=qid;end
  if(!prev && linebeat!=0)$fatal(1,"interrupted admitted line");
  if(!prev && linegap<90)$fatal(1,"ISP line gap too short %0d",linegap);
  if(qs)begin if(counts[qid]!=0)$fatal(1,"duplicate SOF");heads[qid]=heads[qid]+1;end
  if(q!==qid*1000000+counts[qid])$fatal(1,"FIFO sequence id%0d word%0d got%0d",qid,counts[qid],q);
  counts[qid]=counts[qid]+1;linebeat=linebeat+1;linegap=0;
  if(ql)begin if(linebeat!=480)$fatal(1,"wrong admitted line length%0d",linebeat);linebeat=0;end
 end else linegap=linegap+1;
 prev=qv;
end
task start_frame;input integer n;begin
 @(negedge rx);id=n;us=n*37;sof=1;@(negedge rx);sof=0;
end endtask
task line;input integer row,n;integer x;begin
 for(x=0;x<n;x=x+1)begin
  @(negedge rx);v=1;d=id*1000000+row*480+x;
  @(negedge rx);v=0;
  if(x%4==3)repeat(2)@(negedge rx);
 end
 repeat(10)@(negedge rx);eol=1;@(negedge rx);eol=0;
 repeat(2500)@(negedge rx);
end endtask
task end_frame;begin @(negedge rx);eof=1;@(negedge rx);eof=0;end endtask
task good_frame;input integer n;begin start_frame(n);line(0,480);line(1,480);line(2,480);end_frame();repeat(300)@(negedge proc);
 if(counts[n]!=1440 || heads[n]!=1)$fatal(1,"good frame count n%0d count%0d heads%0d",n,counts[n],heads[n]);
end endtask
initial begin
 for(j=0;j<16;j=j+1)begin counts[j]=0;heads[j]=0;end
 repeat(6)@(negedge rx);rst=1;repeat(10)@(negedge rx);
 good_frame(1);
 start_frame(2);line(0,480);line(1,479);end_frame();repeat(300)@(negedge proc);
 if(counts[2]!=480 || bad!=1)$fatal(1,"short line reached ISP");
 start_frame(3);line(0,481);end_frame();repeat(300)@(negedge proc);
 if(counts[3]!=0 || bad!=2)$fatal(1,"overlong line reached ISP");
 // Stop the processing clock: two lines fit, a third cannot be admitted.
 @(negedge proc);run_proc=0;start_frame(4);line(0,480);line(1,480);line(2,480);end_frame();
 if(overflows!=1)$fatal(1,"full-line reservation failed to detect overflow");
 run_proc=1;repeat(1400)@(negedge proc);
 if(counts[4]!=0)$fatal(1,"aborted queued frame escaped");
 good_frame(5);
 start_frame(6);for(k=0;k<220;k=k+1)begin @(negedge rx);v=1;d=6000000+k;end
 @(negedge rx);v=0;rst=0;repeat(6)@(negedge rx);rst=1;repeat(12)@(negedge rx);
 good_frame(7);
 start_frame(8);line(0,480);repeat(18000)@(negedge proc);end_frame();repeat(100)@(negedge proc);
 good_frame(9);
 start_frame(10);for(k=0;k<200;k=k+1)begin @(negedge rx);v=1;d=10000000+k;end
 @(negedge rx);v=0;end_frame();repeat(300)@(negedge proc);
 if(counts[10]!=0)$fatal(1,"EOF published a partial line");
 good_frame(11);
 start_frame(12);line(0,480);end_frame();repeat(300)@(negedge proc);
 if(counts[12]!=480)$fatal(1,"EOF partial-frame test failed");
 good_frame(13);
 start_frame(14);for(k=0;k<30;k=k+1)begin @(negedge rx);v=1;d=14000000+k;end
 @(negedge rx);v=0;good_frame(15);
 if(counts[14]!=0)$fatal(1,"replacement SOF published partial line");
 if(aborts<4)$fatal(1,"missing abort/reset/idle recovery events %0d",aborts);
 $display("FHD_RAW_BRIDGE_PASS 7 complete frames, exact480, >=90 gap, SOF/time, short/long/overflow/reset/idle/partial EOF/replacement SOF recovery");$finish;
end
initial begin #3000000;$fatal(1,"watchdog");end
endmodule'''
run('fhd_raw_bridge',source,mods,compile_args=['-DFHD_BEHAVIORAL_RAM'])

high=r'''`timescale 1ns/1ps
module tb;
reg rx=0,proc=0,run_proc=1,rst=0,sof=0,eof=0,v=0,eol=0;always #4.167 rx=~rx;always #8.333 if(run_proc)proc=~proc;
reg [39:0] d=0;reg [31:0] id=0,us=0;wire [39:0] q;wire qv,qs,ql,ab;wire [31:0] qi,qu,ov,bad;
fhd_raw_bridge #(.HEIGHT(2)) dut(rx,proc,rst,sof,eof,v,eol,d,id,us,q,qv,qs,ql,ab,qi,qu,ov,bad);
integer count=0,heads=0,aborts=0,n=0,x,y;reg [31:0] want_id,want_us;
always @(negedge proc)if(rst)begin
 if(ab)aborts=aborts+1;
 if(qv)begin
  if(qi!==want_id || qu!==want_us)$fatal(1,"32-bit source identity/time truncated %h/%h",qi,qu);
  if(q!==40'hab00000000+count)$fatal(1,"high-ID sample ordering");
  if(qs)heads=heads+1;count=count+1;
 end
end
task start;input [31:0] f,t;begin @(negedge rx);id=f;us=t;want_id=f;want_us=t;count=0;heads=0;sof=1;@(negedge rx);sof=0;end endtask
task line;input integer row;begin
 for(x=0;x<480;x=x+1)begin @(negedge rx);v=1;d=40'hab00000000+row*480+x;@(negedge rx);v=0;end
 repeat(8)@(negedge rx);eol=1;@(negedge rx);eol=0;repeat(1500)@(negedge rx);
end endtask
task finish;begin @(negedge rx);eof=1;@(negedge rx);eof=0;repeat(300)@(negedge proc);end endtask
initial begin
 repeat(8)@(negedge rx);rst=1;repeat(10)@(negedge rx);
 start(32'hf123456f,32'hdeadbeef);line(0);line(1);finish();
 if(count!=960 || heads!=1)$fatal(1,"high-ID complete frame");
 start(32'hf1234570,32'h80000000);line(0);finish();
 if(aborts!=1 || count!=480)$fatal(1,"high-ID partial EOF abort");
 start(32'hf1234571,32'h0000000f);line(0);line(1);finish();
 if(count!=960 || heads!=1 || ov)$fatal(1,"high-ID recovery");
 @(negedge proc);run_proc=0;
 start(32'hf1234572,32'hfedcba98);line(0);line(1);
 @(negedge rx);eof=1;@(negedge rx);eof=0;
 id=32'hcafebabe;us=32'h12345678;run_proc=1;repeat(1800)@(negedge proc);
 if(count!=960 || heads!=1 || ov)$fatal(1,"two-line queued replay/metadata retention");
 // A one-bit toggle would alias here: two overflowed source frames arrive
 // while the processing clock is stopped, after a complete queued frame.
 @(negedge proc);run_proc=0;
 start(32'hf1234573,32'haaaaaaaa);line(0);line(1);
 @(negedge rx);eof=1;@(negedge rx);eof=0;
 start(32'hf1234574,32'hbbbbbbbb);line(0);
 @(negedge rx);eof=1;@(negedge rx);eof=0;
 start(32'hf1234575,32'hcccccccc);line(0);
 @(negedge rx);eof=1;@(negedge rx);eof=0;
 n=aborts;run_proc=1;repeat(1800)@(negedge proc);
 if(aborts<=n || count!=0 || ov!=2)$fatal(1,"multiple paused-clock aborts aliased away");
 start(32'hf1234576,32'hdddddddd);line(0);line(1);finish();
 if(count!=960 || heads!=1)$fatal(1,"multiple abort recovery");
 $display("FHD_RAW_BRIDGE_HIGH32_PASS identity/time wrap, queued metadata, partial EOF and multiple paused-clock abort recovery");$finish;
end
endmodule'''
run('fhd_raw_bridge_high32',high,mods,compile_args=['-DFHD_BEHAVIORAL_RAM'])
