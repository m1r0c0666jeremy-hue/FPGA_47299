"""Small geometry, real async bridge: missing EOF and malformed packets."""
from test_native_zoom_core import execute

TB=r'''`timescale 1ns/1ps
module tb;
reg rx=0,proc=0,rst=0;always #4 rx=~rx;always #8 proc=~proc;
reg sof=0,eof=0,v=0,last=0,error=0;reg [31:0] id=0;wire ov,os,ol,oa,verdict,good;wire [31:0] vid,oid,stamp,overflow,bad;wire [39:0] data;
native_raw_bridge #(.GROUPS(4),.HEIGHT(2),.GAP(2),.IDLE_LIMIT(100)) dut(
.I_rx_clk(rx),.I_processing_clk(proc),.I_rst_n(rst),.I_sof(sof),.I_eof(eof),.I_valid(v),.I_line_end(last),.I_packet_error(error),
.I_data(40'h12345),.I_source_id(id),.I_source_us(32'd17),.O_data(data),.O_valid(ov),.O_sof(os),.O_last(ol),.O_abort(oa),.O_source_id(oid),.O_source_us(stamp),
.O_overflows(overflow),.O_bad_lines(bad),.O_verdict(verdict),.O_good(good),.O_verdict_id(vid));
integer good_count=0,bad_count=0,i,j;reg [31:0] last_bad;
always @(negedge proc)if(verdict)begin if(good)good_count=good_count+1;else begin bad_count=bad_count+1;last_bad=vid;end end
task start(input integer n);begin id=n;sof=1;@(negedge rx);sof=0;repeat(4)@(negedge rx);end endtask
task rows;begin for(i=0;i<2;i=i+1)begin for(j=0;j<4;j=j+1)begin v=1;@(negedge rx);end v=0;last=1;@(negedge rx);last=0;repeat(30)@(negedge rx);end end endtask
task finish;begin eof=1;@(negedge rx);eof=0;repeat(30)@(negedge rx);end endtask
initial begin repeat(5)@(negedge rx);rst=1;repeat(10)@(negedge rx);
start(1);rows;finish;if(good_count!=1 || bad_count)$fatal(1,"good source");
start(2);rows;repeat(150)@(negedge proc);if(bad_count!=1 || last_bad!=2)$fatal(1,"missing EOF stop was not rejected");
start(3);rows;start(4);repeat(20)@(negedge proc);if(bad_count<2 || last_bad!=3)$fatal(1,"next SOF did not reject unclosed old source count%0d id%0d",bad_count,last_bad);rows;finish;
if(good_count!=2)$fatal(1,"recovery after missing EOF");
start(5);rows;error=1;@(negedge rx);error=0;finish;
if(good_count!=2 || bad_count<3 || last_bad!=5)$fatal(1,"packet fault failed");
$display("NATIVE_BRIDGE_PASS good/missingEOF_stop/missingEOF_nextSOF/recovery/packet_fault");$finish;end
initial begin #100000;$fatal(1,"watchdog");end endmodule'''

if __name__=='__main__':
    execute('bridge',TB,['native_raw_bridge.v','native_line_ram.v','refined_reset_bridge.v','../04_tracking/target_mailbox.v'],compile_args=['-DNATIVE_BEHAVIORAL_RAM'])
