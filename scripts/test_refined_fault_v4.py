"""Final reader: every timeout drains; missing snapshots record once per frame."""
from refined_testlib import R,run,literal_fixture
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--before',action='store_true');ap.add_argument('--before-counts',action='store_true');a=ap.parse_args()
src=literal_fixture(R/'scripts/test_refined_recovery.py').replace('stable_line_reader','refined_line_reader')
src=src.replace('repeat(8)@(negedge pc);newframe;','''repeat(8)@(negedge pc);newframe;
if(mode==2)begin wait(dut.state==3);@(negedge dc);dut.failed_jobs=2;wait(dut.state==10);repeat(900)@(negedge dc);
if(recoveries!=0 || !ctrl || dut.state!=10)$fatal(1,"third failed task skipped drain interval");
$display("REFINED_THIRD_DRAIN_PASS third timeout still stops issuing and waits for outstanding returns");end''',1)
mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_line_reader','stable_model_lane','stable_filter4','refined_reset_bridge','refined_zoom_geometry','refined_ddr_recovery','refined_mc_to_user_interface')]+[R/'rtl/04_tracking/target_mailbox.v',R/'user_source/ip_source/w155_d512_fifo/w155_d512_fifo.v',R/'user_source/ip_source/w155_d512_fifo/soft_fifo_al_f58e8b3e1f3d.v']
peak_check='''
integer peak_bus,peak_return,peak_checks=0;
always @(posedge dc)if(dut.d_rst && dut.timeout_event)begin
 peak_bus=dut.bus_wait;peak_return=dut.return_wait;#1;
 if(dut.O_ddr_diag[35:18]<peak_bus || dut.O_ddr_diag[53:36]<peak_return)
 $fatal(1,"failed-job wait peak lost bus%0d/%0d return%0d/%0d",dut.O_ddr_diag[35:18],peak_bus,dut.O_ddr_diag[53:36],peak_return);
 peak_checks=peak_checks+1;
 $display("FAILED_JOB_PEAK_PASS cause%0d bus%0d return%0d",dut.O_ddr_diag[75:72],dut.O_ddr_diag[35:18],dut.O_ddr_diag[53:36]);
end
'''
src=src.replace('endmodule',peak_check+'\nendmodule')
src=src.replace('if(dd[87:76]<2 || checks<1000)', '''if(dd[75:72]!=4 || dd[62:54]!=240 || dd[71:63]!=239)$fatal(1,"fault beat snapshot overwritten after good row %h",dd);
$display("FAULT_COUNTS_STICKY_PASS cause4 accepted240 returned239 after successful fresh row");
if(dd[87:76]<2 || checks<1000)''')
if a.before:
 mods=[R/'build/refined_full_20261017_224454/compiled_source/rtl/color_regions/refined_line_reader.v' if p.name=='refined_line_reader.v' else p for p in mods]
if a.before_counts:
 mods=[R/'build/refined_full_20261017_231328/compiled_source/rtl/color_regions/refined_line_reader.v' if p.name=='refined_line_reader.v' else p for p in mods]
for mode in ((0,) if a.before else (1,) if a.before_counts else (0,1,2)):
 name=f'before_failed_peak_drain_{mode}' if a.before else f'before_fault_counts_drain_{mode}' if a.before_counts else f'final_video_drain_{mode}'
 run(name,src,mods,args=[f'+MODE={mode}'],expected_failure=a.before or a.before_counts)
if a.before or a.before_counts:raise SystemExit(0)
missing=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,vs=0,de=0,stream=1;wire rd;wire [127:0] pd;
refined_line_reader dut(.I_frame_commit(1'b0),.I_selected_good(1'b0),.I_rst_n(rst),.I_ddr_clk(clk),.I_write_busy(1'b0),.I_write_en(1'b0),.I_read_buffer(2'd0),.I_frame_id(32'd0),.I_models(128'd0),.I_ddr_ready(1'b1),.I_ddr_valid(1'b0),.I_ddr_data(128'd0),.O_read_en(rd),.I_pixel_clk(clk),.I_vs(vs),.I_hs(1'b0),.I_de(de),.I_x0(11'd0),.I_y0(10'd48),.I_zoom(3'd0),.I_rotate(1'b1),.I_stream_n(stream),.O_pixel_diag(pd),.I_accepted_reads(32'd0),.I_unexpected_return(1'b0));
integer f,n;
initial begin repeat(5)@(negedge clk);rst=1;repeat(10)@(negedge clk);
for(f=1;f<=3;f=f+1)begin vs=1;de=0;@(negedge clk);vs=0;repeat(3)@(negedge clk);de=1;repeat(32)@(negedge clk);de=0;
if(pd[3:0]!=5 || pd[108:93]!=f || rd)$fatal(1,"snapshot fault count/cause f%0d diag%h",f,pd);stream=f!=1;end
$display("REFINED_SNAPSHOT_FAULT_PASS once per actual display frame, no invalid-bank reads, diagnosis survives stream reset");$finish;end endmodule'''
run('final_missing_snapshot',missing,[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_line_reader','stable_model_lane','stable_filter4','refined_reset_bridge','refined_zoom_geometry')]+[R/'rtl/04_tracking/target_mailbox.v'])
bus_peak=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,commit=0,stream=1;wire [127:0] dd;integer n=0;
refined_line_reader #(.JOB_TIMEOUT_CYCLES(64),.DRAIN_TIMEOUT_CYCLES(64)) dut(
.I_frame_commit(commit),.I_selected_good(1'b1),.I_rst_n(rst),.I_ddr_clk(clk),.I_write_busy(1'b1),.I_write_en(1'b0),
.I_read_buffer(2'd0),.I_frame_id(32'd9),.I_models(128'd0),.I_ddr_ready(1'b1),.I_ddr_valid(1'b0),.I_ddr_data(128'd0),
.I_pixel_clk(clk),.I_vs(1'b0),.I_hs(1'b0),.I_de(1'b0),.I_x0(11'd0),.I_y0(10'd48),.I_zoom(3'd0),.I_rotate(1'b0),
.I_stream_n(stream),.O_ddr_diag(dd),.I_accepted_reads(32'd0),.I_unexpected_return(1'b0));
initial begin repeat(5)@(negedge clk);rst=1;repeat(10)@(negedge clk);commit=1;@(negedge clk);commit=0;
while(dd[75:72]!=6 && n<200)begin @(negedge clk);n=n+1;end
if(dd[75:72]!=6 || dd[35:18]<63 || dd[62:54]!=0 || dd[71:63]!=0)$fatal(1,"write-busy peak not retained %h",dd);
stream=0;repeat(10)@(negedge clk);
if(dd[75:72]!=6 || dd[35:18]<63)$fatal(1,"peak lost on stream reset");
$display("FAILED_BUS_PEAK_PASS wait%0d no accepted reads, timeout cause6 survives stream reset",dd[35:18]);$finish;end endmodule'''
run('failed_bus_wait_peak',bus_peak,[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_line_reader','stable_model_lane','stable_filter4','refined_reset_bridge','refined_zoom_geometry')]+[R/'rtl/04_tracking/target_mailbox.v'])
