"""Reject old layouts and preserve every diagnostic bit in actual frame store."""
from test_ring_calibration import R,run
src='''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,beginf=0,write=0,result=0,snapshot=0;
reg [639:0] meta=0;wire os,good;wire [674:0] data;
stable_frame_store #(.WORDS(1)) dut(clk,rst,beginf,2'd0,32'd1,write,25'd0,result,meta,snapshot,10'd15,os,data,good);
task snap;begin @(negedge clk);snapshot=1;@(negedge clk);snapshot=0;@(negedge clk);end endtask
initial begin repeat(3)@(negedge clk);rst=1;@(negedge clk);beginf=1;@(negedge clk);beginf=0;write=1;@(negedge clk);write=0;
meta[31:0]=1;meta[255]=1;meta[247]=1;meta[244]=1;meta[242:235]=7;meta[415:413]=2;meta[383:256]=128'hfedcba98765432100123456789abcdef;meta[639:604]=36'ha12345678;
result=1;@(negedge clk);result=0;snap;if(data[639:0]!=0 || dut.has_meta!=0)$fatal(1,"v2 layout accepted");
meta[415:413]=3;result=1;@(negedge clk);result=0;snap;
if(!data[674] || data[671:640]!=1 || data[639:0]!==meta || !good)$fatal(1,"v3 diagnostics not preserved");
$display("RING_PROTOCOL_PASS v2 rejected, v3 all 640 bits preserved with actual bank and image ID");$finish;end endmodule'''
run('protocol_v3',src,[R/'rtl/color_regions/stable_frame_store.v'])
