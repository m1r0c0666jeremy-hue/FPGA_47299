"""Cycle-exact bank selector comparison, actual tail writes and v4 provenance."""
from refined_testlib import R,run,literal_fixture

src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,beg=0,wr=0,result=0,snap=0,inv=0;
reg [1:0] bank=0;reg [31:0] fid=0,stamp=0;reg [24:0] addr=0;reg [767:0] meta=0;
wire a,b,ag,bg;wire [851:0] ad,bd;
stable_frame_store #(.WORDS(4),.V4(1)) before_store(clk,rst,beg,bank,fid,wr,addr,result,meta,snap,10'd15,a,ad,ag,stamp,16'd7,1'b1,inv);
refined_frame_store #(.WORDS(4),.V4(1)) after_store(clk,rst,beg,bank,fid,wr,addr,result,meta,snap,10'd15,b,bd,bg,stamp,16'd7,1'b1,inv);
reg [31:0] rng=32'h47299,seq=32'hfffffff0;integer k,j,wb,mb,checks=0,valids=0,empty=0,matched=0,notip=0;
initial begin repeat(5)@(negedge clk);rst=1;
for(k=0;k<16000;k=k+1)begin
@(negedge clk);
if(a!==b || ad!==bd || ag!==bg || before_store.complete!==after_store.complete)$fatal(1,"store selector changed cycle%0d a%b b%b ag%b bg%b",k,a,b,ag,bg);
if(a)begin checks=checks+1;if(ad[802])valids=valids+1;if(ad[802] && ad[767:0]==0)empty=empty+1;
if(ad[802] && ad[255])begin matched=matched+1;if(!ad[32])notip=notip+1;end end
rng=rng*32'd1664525+32'd1013904223;
beg=rng[3:0]==1;bank=rng[7:6];if(beg)begin seq=seq+1;fid=seq;stamp=k*16;end
wr=rng[1:0]!=3;wb=rng[11:10];addr=before_store.expected[wb];
if(!before_store.known[wb])addr=wb*7000000;
if(rng[8:4]==3)addr=addr+8;
result=rng[2:0]==2;mb=rng[13:12];meta=0;
meta[31:0]=before_store.ids[mb];meta[255]=1;meta[247]=1;meta[244]=1;meta[242:235]=7;meta[415:413]=4;
meta[671:640]=before_store.stamps[mb];meta[719:704]=before_store.epochs[mb];meta[720]=1;
meta[32]=rng[14];meta[734:723]=k%2048;
snap=rng[5:4]==0;inv=k%997==996;
end
if(checks<1000 || valids<50 || empty<10 || matched<50 || notip<20)$fatal(1,"insufficient selector stress %0d %0d %0d %0d %0d",checks,valids,empty,matched,notip);
$display("REFINED_STORE_EQUIVALENT_PASS 16000 clocks, %0d snapshots/%0d valid/%0d empty/%0d matching/%0d no-tip; wrap, exact tail/extra writes, reuse, metadata and invalidation",checks,valids,empty,matched,notip);$finish;
end endmodule'''
run('store_cached_id_comparison',src,[R/'rtl/color_regions'/f'{n}.v' for n in ('stable_frame_store','refined_frame_store')])
s=literal_fixture(R/'scripts/test_refined_timing.py','store').replace('stable_frame_store #','refined_frame_store #')
run('refined_v4_frame_store_and_display',s,[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_frame_store','stable_display','refined_zoom_geometry')])
