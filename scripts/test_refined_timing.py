"""Source provenance, bank epochs and actual display endpoint timing."""
from refined_testlib import R,run
src=r'''module tb;
reg pc=0,cc=0,rst=0;always #6.667 pc=~pc;always #8.334 cc=~cc;
wire [31:0] us,gray,now_us,latest_gray;wire [32:0] atag;
reg csi=0,raw10=0,axis=0;reg [32:0] rawtag=0,detecttag=0;wire rk,dk;wire [31:0] stamp;
refined_timebase tm(pc,rst,us,gray);
refined_stamp_source source(cc,rst,gray,csi,raw10,axis,rawtag,detecttag,atag,latest_gray,rk,dk,stamp,now_us);
reg vs=0,de=0,live=1,tvalid=1;reg [31:0] now=0,image_us=0,image_id=0,latest=0;wire pv;wire [31:0] elapsed,age;
refined_performance perf(pc,rst,vs,de,live,now,image_us,image_id,latest,tvalid,pv,elapsed,age);
task header;begin @(negedge cc);csi=1;@(negedge cc);csi=0;raw10=1;@(negedge cc);raw10=0;axis=1;rawtag=atag;detecttag=atag;@(negedge cc);axis=0;end endtask
task display;begin @(negedge pc);de=0;vs=1;@(negedge pc);vs=0;@(negedge pc);de=1;@(negedge pc);de=0;end endtask
integer i;reg [31:0] expected_stamp;reg [32:0] oldtag;
initial begin repeat(5)@(negedge pc);rst=1;repeat(7500)@(negedge pc);
if(us<99 || us>101 || now_us>us || us-now_us>1)$fatal(1,"microsecond clock/CDC");
header;oldtag=rawtag;expected_stamp=stamp;if(!rk || !dk || rawtag!=33'h100000001)$fatal(1,"first source ID");
repeat(20)@(negedge cc);axis=1;#1;if(atag[32])$fatal(1,"uial2axis wrap fabricated new source SOF");@(negedge cc);axis=0;
for(i=0;i<4;i=i+1)header;
rawtag=oldtag;detecttag=oldtag;#1;if(rk || dk)$fatal(1,"overwritten timestamp silently reassigned");
rawtag=0;detecttag=0;#1;if(rk || dk)$fatal(1,"reset token mistaken for frame zero");
// The full identity must reject two source IDs with the same short token.
detecttag=33'h100000105;#1;if(dk)$fatal(1,"low-byte token alias");
now=32'h00000020;image_us=32'hfffffff0;image_id=32'hffffffff;latest=1;display;
if(!pv || elapsed!=48 || age!=2)$fatal(1,"time/frame counter wrap");
now=100;display;if(!pv || elapsed!=116)$fatal(1,"repeated old image failed to age");
live=0;@(negedge pc);if(pv)$fatal(1,"aborted image reports valid latency");live=1;@(negedge pc);if(pv)$fatal(1,"abort became valid without next frame");
tvalid=0;display;if(pv)$fatal(1,"unknown stamp reports valid time");tvalid=1;image_us=1000;now=500;display;if(pv)$fatal(1,"future timestamp accepted");
$display("REFINED_TIMING_PASS 75-cycle us, asynchronous Gray time, actual source IDs, overwritten/aliased/reset tokens rejected, endpoint/repeat/abort/wrap");$finish;end endmodule'''
run('source_time_and_endpoint',src,[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_timebase','refined_stamp_source','refined_performance')])
store=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,beg=0,wr=0,result=0,snap=0,invalidate=0;reg [767:0] meta=0;reg [15:0] epoch=7;reg [31:0] fid=32'hffffffff,stamp=32'hfffffff0;
wire os,good;wire [851:0] data;wire commit;wire [31:0] shown_id,shown_us;wire [15:0] shown_epoch;wire timed;wire [767:0] active;
stable_frame_store #(.WORDS(1),.V4(1)) dut(clk,rst,beg,2'd0,fid,wr,25'd0,result,meta,snap,10'd15,os,data,good,stamp,epoch,1'b1,invalidate);
reg vs=0;
stable_display #(.V4(1)) view(.I_clk(clk),.I_rst_n(rst),.I_vs(vs),.I_de(1'b0),.I_snapshot(os),.I_data(data),.I_tracking(1'b1),.I_show(1'b1),.I_conflict(1'b0),.I_live(1'b1),.I_session(8'd7),.I_zoom(3'd1),.I_mode(2'd0),.I_pair(1'b0),.O_commit(commit),.O_frame_id(shown_id),.O_meta(active),.I_rotate(1'b1),.O_image_us(shown_us),.O_epoch(shown_epoch),.O_time_valid(timed));
task snapshot;begin @(negedge clk);vs=1;@(negedge clk);vs=0;snap=1;@(negedge clk);snap=0;repeat(4)@(negedge clk);end endtask
task publish;begin result=1;@(negedge clk);result=0;snapshot;end endtask
initial begin repeat(4)@(negedge clk);rst=1;@(negedge clk);beg=1;@(negedge clk);beg=0;wr=1;@(negedge clk);wr=0;snapshot;
if(!good || !timed || shown_id!=fid || shown_us!=stamp || shown_epoch!=7 || active!=0)$fatal(1,"standby image needs independent timestamp");
meta[31:0]=fid;meta[255]=1;meta[247]=1;meta[244]=1;meta[242:235]=7;meta[415:413]=3;meta[719:704]=7;publish;if(active!=0)$fatal(1,"v3 accepted by v4 store");
meta[415:413]=4;meta[719:704]=6;publish;if(active!=0)$fatal(1,"wrong generation accepted");
meta[719:704]=7;meta[671:640]=stamp;meta[720]=1;meta[722:721]=2;meta[764:723]=42'h123456789ab;publish;
if(active!==meta || !timed || shown_us!=stamp || data[767:0]!==meta)$fatal(1,"v4 fields or image provenance lost");
invalidate=1;#1;if(good)$fatal(1,"camera event did not abort selected bank immediately");@(negedge clk);invalidate=0;snapshot;
if(good || timed || data[802] || active!=0)$fatal(1,"camera restart retained image/metadata");
$display("REFINED_V4_STORE_PASS 768/852 bits, epoch mismatch/v3 rejection, standby independent timestamp, camera event invalidation");$finish;end endmodule'''
run('v4_frame_store_and_display',store,[R/'rtl/color_regions'/f'{n}.v' for n in ('stable_frame_store','stable_display','refined_zoom_geometry')])
