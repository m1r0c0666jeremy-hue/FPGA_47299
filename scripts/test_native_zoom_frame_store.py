"""Dense-write count and full-source qualification in the real frame store."""
from test_native_zoom_core import execute

def main():
    source=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0,write_en=0,result=0,snap=0,inv=0,verdict=0,good=0;
reg [1:0] bank=0;reg [31:0] id=0,vid=0;reg [24:0] addr=0;reg [767:0] meta=0;
wire os,selected;wire [851:0] out;integer i;
native_frame_store #(.WORDS(691200),.V4(1)) dut(clk,rst,start,bank,id,write_en,addr,result,meta,
snap,10'd0,os,out,selected,32'd500,16'd3,1'b1,inv,verdict,good,vid);
task begin_source(input [1:0] b,input [31:0] number);begin
bank=b;id=number;start=1;@(negedge clk);start=0;repeat(3)@(negedge clk);
end endtask
task snapshot;begin snap=1;@(negedge clk);snap=0;@(negedge clk);end endtask
task finish_source(input bit pass);begin vid=id;good=pass;verdict=1;@(negedge clk);verdict=0;repeat(2)@(negedge clk);end endtask
initial begin repeat(4)@(negedge clk);rst=1;
begin_source(3,7);meta[31:0]=7;meta[255]=1;meta[415:413]=4;meta[720]=1;meta[719:704]=3;meta[671:640]=500;
result=1;@(negedge clk);result=0;
for(i=0;i<691200;i=i+1)begin write_en=1;addr=21000000+i*8;@(negedge clk);end
write_en=0;snapshot;
if(out[802] || selected)$fatal(1,"ROI writes alone must not publish");
finish_source(0);snapshot;if(out[802] || selected)$fatal(1,"bad tail source published");
finish_source(1);snapshot;if(out[802] || selected)$fatal(1,"bad source revived by later good verdict");
begin_source(3,11);meta[31:0]=11;result=1;@(negedge clk);result=0;
for(i=0;i<691200;i=i+1)begin write_en=1;addr=21000000+i*8;@(negedge clk);end
write_en=0;finish_source(1);snapshot;
if(!out[802] || !selected || out[801:800]!=3 || out[31:0]!=11)$fatal(1,"dense counter/source gate failed count%0d snapshot%h",dut.count[3],out);
if(dut.count[3]!=691200)$fatal(1,"dense counter truncated above 19 bits");
// New bank identity revokes old source qualifications and metadata.
begin_source(3,15);snapshot;if(out[802] || selected)$fatal(1,"bank reuse qualification leaked");
vid=7;good=1;verdict=1;@(negedge clk);verdict=0;snapshot;
if(out[802] || selected)$fatal(1,"old source verdict qualified reused bank");
inv=1;@(negedge clk);inv=0;snapshot;if(out[802] || selected)$fatal(1,"invalidate leaked source");
$display("NATIVE_FRAME_STORE_PASS writes691200/20bit_count/full_source_gate/bank_reuse/invalidate");$finish;
end endmodule'''
    execute('frame_store',source,['native_frame_store.v'],timeout=180)
if __name__=='__main__':main()
