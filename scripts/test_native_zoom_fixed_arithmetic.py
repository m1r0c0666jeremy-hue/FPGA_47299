"""Exhaustive row arithmetic and clock-exact address comparison to frozen RTL."""
import datetime,hashlib,json
from refined_testlib import R
from test_native_zoom_core import execute

REFERENCE_SHA='68c28cec9b2fc4ea0c2f9500abf5f247ee6f78636fee919062fdea2db864dfc5'

def main():
 reference=R/'vendor_reference/native_line_core_f7d.v'
 raw=reference.read_bytes();assert hashlib.sha256(raw).hexdigest()==REFERENCE_SHA
 folder=R/'build'/('native_fixed_arithmetic_reference_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
 folder.mkdir(exist_ok=False)
 old=folder/'frozen_line_core.v'
 old.write_text(raw.decode('utf-8').replace('module native_line_core #','module frozen_line_core #'),encoding='utf-8')
 ports='''.I_ddr_clk(clk),.I_pixel_clk(clk),.I_rst_n(rst),.I_stream_n(1'b1),
 .I_frame_commit(1'b0),.I_selected_good(1'b0),.I_write_busy(1'b0),.I_write_en(1'b0),
 .I_read_buffer(2'd0),.I_frame_id(32'd0),.I_models(128'd0),.I_ddr_ready(1'b0),
 .I_ddr_valid(1'b0),.I_ddr_data(128'd0),.I_vs(1'b0),.I_hs(1'b0),.I_de(1'b0),
 .I_x0(11'd0),.I_y0(10'd0),.I_zoom(3'd0),.I_rotate(1'b0),
 .I_accepted_reads(32'd0),.I_unexpected_return(1'b0),.I_native_zoom(3'd0),
 .I_native_x0(11'd0),.I_native_y0(10'd0)'''
 tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;
native_line_core dut(PORTS);frozen_line_core refdut(PORTS);
reg [9:0] row=0;reg first=0,request_rotate=0,saved_rotate=0;
reg [1:0] bank=0;reg [24:0] saved_base=0;
integer n,f,r,s,b,checks=0;reg [24:0] expected_y,expected_offset;
initial begin
 repeat(4)@(negedge clk);rst=1;repeat(4)@(negedge clk);
 force dut.fy=row;force refdut.fy=row;
 force dut.sy=row;force refdut.sy=row;
 force dut.prefetch=row;force refdut.prefetch=row;
 for(n=0;n<1024;n=n+1)begin
  row=n;#1;
  if(dut.row_mod3(row)!==n%3 || dut.mask_slot!==refdut.mask_slot ||
     dut.pb!==refdut.pb || dut.next_slot!==refdut.next_slot)
    $fatal(1,"modulo mismatch row%0d new%0d expected%0d",n,dut.row_mod3(row),n%3);
 end
 release dut.fy;release refdut.fy;release dut.sy;release refdut.sy;
 release dut.prefetch;release refdut.prefetch;
 force dut.req_y=row;force refdut.req_y=row;
 force dut.req_first=first;force refdut.req_first=first;
 force dut.req_rotate=request_rotate;force refdut.req_rotate=request_rotate;
 force dut.frame_rotate=saved_rotate;force refdut.frame_rotate=saved_rotate;
 force dut.req_image=bank;force refdut.req_image=bank;
 force dut.frame_base=saved_base;force refdut.frame_base=saved_base;
 force dut.state=0;force refdut.state=0;
 force dut.req2=1;force refdut.req2=1;force dut.ack=0;force refdut.ack=0;
 for(f=0;f<2;f=f+1)for(r=0;r<2;r=r+1)for(s=0;s<2;s=s+1)
 for(b=0;b<4;b=b+1)for(n=0;n<1024;n=n+1)begin
  @(negedge clk);row=n;first=f;request_rotate=r;saved_rotate=s;bank=b;
  // Non-bank-aligned base also exercises full-width addition and wrap.
  saved_base=25'h1f00001+b*7000000;
  expected_y=(f?r:s)?25'd719-n:n;
  expected_offset=expected_y*1920;
  @(posedge clk);#1;
  if(dut.row_offset!==expected_offset || dut.line_base!==refdut.line_base ||
     dut.O_read_addr!==refdut.O_read_addr)
    $fatal(1,"row address mismatch row%0d first%0d r%0d/%0d bank%0d new%h old%h",
           n,f,r,s,b,dut.line_base,refdut.line_base);
  checks=checks+1;
 end
 $display("NATIVE_FIXED_ARITHMETIC_PASS modulo1024 three_paths addresses%0d all10bit_rows banks4 both_directions first_and_saved 25bit_wrap clock_exact",checks);
 $finish;
end
initial begin #1000000;$fatal(1,"fixed arithmetic watchdog");end
endmodule'''.replace('PORTS',ports)
 modules=['native_line_core.v',str(old),'stable_model_lane.v','stable_filter4.v',
          'refined_reset_bridge.v','refined_zoom_geometry.v',str(R/'rtl/04_tracking/target_mailbox.v')]
 out=execute('fixed_arithmetic',tb,modules,timeout=120)
 receipt=out/'native_receipt.json';d=json.loads(receipt.read_text(encoding='utf-8'))
 d['producer_inputs'][reference.relative_to(R).as_posix()]=REFERENCE_SHA
 receipt.write_text(json.dumps(d,indent=2),encoding='utf-8')

if __name__=='__main__':main()
