"""Private equivalence probe; never changes a compiled native source."""
from pathlib import Path
import datetime,hashlib,json,subprocess
from refined_testlib import R,IV,ENV

def main():
 out=R/'build'/('native_selector_probe_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir(exist_ok=False)
 original=R/'rtl/color_regions/native_frame_store.v';before=original.read_bytes();s=before.decode('utf-8').replace('module native_frame_store #','module private_frame_store #')
 s=s.replace('reg [3:0] id_settled,newer', 'reg [3:0] settled_first;reg [3:0] id_settled,newer')
 s=s.replace('id_settled<=0;for(ai=', 'id_settled<=0;settled_first<=0;for(ai=')
 s=s.replace('id_settled<=known;if(I_begin)id_settled[I_bank]<=0;', 'settled_first<=known;id_settled<=settled_first;if(I_begin)begin settled_first[I_bank]<=0;id_settled[I_bank]<=0;end')
 s=s.replace('if(V4 && I_invalidate)id_settled<=0;', 'if(V4 && I_invalidate)begin settled_first<=0;id_settled<=0;end')
 anchor='reg [9:0] tags[0:3];'
 cache='''reg [1:0] newest_table[0:15];integer mi;reg [1:0] ml,mh;
 always @(posedge I_clk)for(mi=0;mi<16;mi=mi+1)begin
 ml=(mi&2) && (!(mi&1) || newer[1][0])?1:0;
 mh=(mi&8) && (!(mi&4) || newer[3][2])?3:2;
 newest_table[mi]<=((mi>>mh)&1) && (!((mi>>ml)&1) || newer[mh][ml])?mh:ml;
 end
 '''
 assert anchor in s;s=s.replace(anchor,cache+anchor)
 old='newest=select_co[hi] && (!select_co[lo] || newer[hi][lo])?hi:lo;'
 assert old in s;s=s.replace(old,'newest=newest_table[select_co];')
 candidate=out/'private_frame_store.v';candidate.write_text(s,encoding='utf-8')
 tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;
reg rst=0,start=0,we=0,result=0,snap=0,inv=0,verdict=0,good=0;
reg [1:0] bank=0;reg [31:0] id=32'hfffffff0,vid=0,stamp=0;reg [15:0] epoch=0;
reg [24:0] addr=0;reg [767:0] meta=0;reg [9:0] command=0;reg timed=1;
wire os0,os1,good0,good1;wire [851:0] a,b;
native_frame_store #(.WORDS(32),.V4(1)) refdut(clk,rst,start,bank,id,we,addr,result,meta,snap,command,os0,a,good0,stamp,epoch,timed,inv,verdict,good,vid);
private_frame_store #(.WORDS(32),.V4(1)) fastdut(clk,rst,start,bank,id,we,addr,result,meta,snap,command,os1,b,good1,stamp,epoch,timed,inv,verdict,good,vid);
integer checked=0,frames=0,n,j;reg [31:0] random_state=32'h3ad54b67;reg [9:0] tag;reg bad_address,bad_source;
function [24:0] base(input [1:0] bk);case(bk)0:base=0;1:base=7000000;2:base=14000000;3:base=21000000;endcase endfunction
task advance;begin @(negedge clk);random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};snap=random_state[0];command=random_state[9:0];end endtask
always @(posedge clk)begin #1;if(rst)begin
 if({os0,good0,a}!=={os1,good1,b})$fatal(1,"selector mismatch frame%0d cycle%0d snapshot%b/%b ref%h fast%h",frames,checked,os0,os1,a,b);
 checked=checked+1;
end end
initial begin repeat(4)advance;rst=1;
for(frames=0;frames<3000;frames=frames+1)begin
 bank=frames%4;id=id+1;stamp=stamp+33333;epoch=frames/73;tag=random_state[12:3];bad_address=frames%13==0;bad_source=frames%7==0;
 start=1;advance;start=0;
 meta=0;for(j=0;j<24;j=j+1)meta[j*32+:32]=random_state^(frames*1337+j*17);
 meta[31:0]=id;meta[255]=1;meta[415:413]=4;meta[720]=timed;meta[719:704]=epoch;meta[671:640]=stamp;
 {meta[243],meta[242:235],meta[244]}=tag;
 for(n=0;n<32;n=n+1)begin
  we=1;addr=base(bank)+n*8+((bad_address && n==16)?8:0);
  result=n==31 || n==1;verdict=n==31;good=!bad_source;vid=id;
  if(n==31)begin command=tag;snap=1;end
  advance;
 end
 we=0;result=0;verdict=0;
 command=tag;snap=1;advance;command=tag;snap=1;advance;
 if(frames%11==0)begin verdict=1;good=0;vid=id;advance;verdict=0;end
 if(frames%17==0)begin verdict=1;good=1;vid=id;advance;verdict=0;end
 if(frames%31==0)begin inv=1;advance;inv=0;end
 repeat(5)advance;
end
$display("PRIVATE_SELECTOR_EQUIVALENCE_PASS frames3000 cycles%0d wrap/lastwrite_snapshot/meta/source/invalidate/bank_reuse; NOT_ADOPTED_NO_RESOURCE_MEASUREMENT",checked);$finish;
end endmodule'''
 (out/'tb.sv').write_text(tb,encoding='utf-8')
 with (out/'test.log').open('w',encoding='utf-8') as log:
  code=subprocess.run([str(IV),'-g2012','-s','tb','-o',str(out/'test.vvp'),str(out/'tb.sv'),str(original),str(candidate)],cwd=R,env=ENV,stdout=log,stderr=subprocess.STDOUT).returncode
  if code==0:code=subprocess.run([str(IV.with_name('vvp.exe')),str(out/'test.vvp')],cwd=R,env=ENV,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
 assert original.read_bytes()==before
 receipt={'exit_code':code,'original_sha256':hashlib.sha256(before).hexdigest(),'private_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
 'scope':'Private equivalence only; WORDS32 >= pipeline settling; production RTL and active build untouched','adopted':False,'resource_measured':False}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(out);print((out/'test.log').read_text(encoding='utf-8'));raise SystemExit(code)
if __name__=='__main__':main()
