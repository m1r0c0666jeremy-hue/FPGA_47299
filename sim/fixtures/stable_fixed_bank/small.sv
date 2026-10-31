`timescale 1ns/1ps
module selector_case #(parameter WORDS=32,V4=1)(output reg done=0);
reg clk=0;always #5 clk=~clk;
reg rst=0,start=0,we=0,result=0,snap=0,inv=0,verdict=0,good=0;
reg [1:0] bank=0;reg [31:0] id=32'hfffffff0,vid=0,stamp=32'hfffffff0;reg [15:0] epoch=0;
reg [24:0] addr=0;reg [767:0] meta=0;reg [9:0] command=0;reg timed=1;
wire os0,os1,good0,good1;wire [851:0] a,b;
reference_frame_store #(.WORDS(WORDS),.V4(V4)) refdut(clk,rst,start,bank,id,we,addr,result,meta,snap,command,os0,a,good0,stamp,epoch,timed,inv);
refined_frame_store #(.WORDS(WORDS),.V4(V4)) fastdut(clk,rst,start,bank,id,we,addr,result,meta,snap,command,os1,b,good1,stamp,epoch,timed,inv);
integer metadata_snapshots=0,checked=0,frames=0,n,j;reg [31:0] random_state=32'h3ad54b67;reg [9:0] tag;reg bad_address,bad_source;
function [24:0] base(input [1:0] bk);case(bk)0:base=0;1:base=7000000;2:base=14000000;3:base=21000000;endcase endfunction
task advance;begin @(negedge clk);random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};snap=random_state[0];command=random_state[9:0];end endtask
always @(posedge clk)begin #1;if(rst)begin
 if({os0,good0,a}!=={os1,good1,b})$fatal(1,"selector mismatch frame%0d cycle%0d snapshot%b/%b ref%h fast%h",frames,checked,os0,os1,a,b);
 if(os0 && a[255])metadata_snapshots=metadata_snapshots+1;checked=checked+1;
end end
initial begin repeat(4)advance;rst=1;
for(frames=0;frames<3000;frames=frames+1)begin
 bank=frames%4;id=id+1;stamp=stamp+33333;epoch=frames/73;tag=random_state[12:3];bad_address=frames%13==0;bad_source=frames%7==0;
 start=1;we=frames%19==0;addr=base(bank);advance;start=0;we=0;
 meta=0;for(j=0;j<24;j=j+1)meta[j*32+:32]=random_state^(frames*1337+j*17);
 meta[31:0]=id;meta[255]=1;meta[415:413]=V4?4:3;meta[720]=timed;meta[719:704]=epoch;meta[671:640]=stamp;
 {meta[243],meta[242:235],meta[244]}=tag;
 for(n=0;n<WORDS;n=n+1)begin
  we=1;addr=base(bank)+n*8+((bad_address && n==WORDS/2)?8:0);
  if(frames%17==0)meta[719:704]=epoch+1'b1;result=n==WORDS-1 || n==1;verdict=n==WORDS-1;good=!bad_source;vid=id;
  if(n==WORDS-1)begin command=tag;snap=1;end
  advance;
 end
 we=0;result=0;verdict=0;
 command=tag;snap=1;advance;command=tag;snap=1;advance;
 if(frames%11==0)begin verdict=1;good=0;vid=id;advance;verdict=0;end
 if(frames%17==0)begin verdict=1;good=1;vid=id;advance;verdict=0;end
 if(frames%31==0)begin inv=1;advance;inv=0;end
 repeat(5)advance;
end
if(metadata_snapshots<100)$fatal(1,"Insufficient valid metadata snapshots V4%0d count%0d",V4,metadata_snapshots);$display("STABLE_FIXED_BANK_CASE_PASS frames3000 cycles%0d wrap/lastwrite_snapshot/meta/invalidate/bank_reuse",checked);done=1;
end endmodule
module tb;wire [5:0] done;
selector_case #(.WORDS(4),.V4(0)) a(done[0]);selector_case #(.WORDS(8),.V4(0)) b(done[1]);selector_case #(.WORDS(32),.V4(0)) c(done[2]);
selector_case #(.WORDS(4),.V4(1)) d(done[3]);selector_case #(.WORDS(8),.V4(1)) e(done[4]);selector_case #(.WORDS(32),.V4(1)) f(done[5]);
initial begin wait(&done);$display("STAGE1_FIXED_BANK_SMALL_PASS frames18000 words4/8/32 V4both every-clock compare; SIMULATION_ONLY_NO_PHYSICAL_CLAIM");$finish;end
endmodule
