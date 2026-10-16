"""Final reader: every timeout drains; missing snapshots record once per frame."""
from refined_testlib import R,run,literal_fixture
src=literal_fixture(R/'scripts/test_refined_recovery.py').replace('stable_line_reader','refined_line_reader')
src=src.replace('repeat(8)@(negedge pc);newframe;','''repeat(8)@(negedge pc);newframe;
if(mode==2)begin wait(dut.state==3);@(negedge dc);dut.failed_jobs=2;wait(dut.state==10);repeat(900)@(negedge dc);
if(recoveries!=0 || !ctrl || dut.state!=10)$fatal(1,"third failed task skipped drain interval");
$display("REFINED_THIRD_DRAIN_PASS third timeout still stops issuing and waits for outstanding returns");end''',1)
mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_line_reader','stable_model_lane','stable_filter4','refined_reset_bridge','refined_zoom_geometry','refined_ddr_recovery','refined_mc_to_user_interface')]+[R/'rtl/04_tracking/target_mailbox.v',R/'user_source/ip_source/w155_d512_fifo/w155_d512_fifo.v',R/'user_source/ip_source/w155_d512_fifo/soft_fifo_al_f58e8b3e1f3d.v']
for mode in (0,1,2):run(f'final_video_drain_{mode}',src,mods,args=[f'+MODE={mode}'])
missing=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,vs=0,de=0,stream=1;wire rd;wire [127:0] pd;
refined_line_reader dut(.I_frame_commit(1'b0),.I_selected_good(1'b0),.I_rst_n(rst),.I_ddr_clk(clk),.I_write_busy(1'b0),.I_write_en(1'b0),.I_read_buffer(2'd0),.I_frame_id(32'd0),.I_models(128'd0),.I_ddr_ready(1'b1),.I_ddr_valid(1'b0),.I_ddr_data(128'd0),.O_read_en(rd),.I_pixel_clk(clk),.I_vs(vs),.I_hs(1'b0),.I_de(de),.I_x0(11'd0),.I_y0(10'd48),.I_zoom(3'd0),.I_rotate(1'b1),.I_stream_n(stream),.O_pixel_diag(pd),.I_accepted_reads(32'd0),.I_unexpected_return(1'b0));
integer f,n;
initial begin repeat(5)@(negedge clk);rst=1;repeat(10)@(negedge clk);
for(f=1;f<=3;f=f+1)begin vs=1;de=0;@(negedge clk);vs=0;repeat(3)@(negedge clk);de=1;repeat(32)@(negedge clk);de=0;
if(pd[3:0]!=5 || pd[108:93]!=f || rd)$fatal(1,"snapshot fault count/cause f%0d diag%h",f,pd);stream=f!=1;end
$display("REFINED_SNAPSHOT_FAULT_PASS once per actual display frame, no invalid-bank reads, diagnosis survives stream reset");$finish;end endmodule'''
run('final_missing_snapshot',missing,[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_line_reader','stable_model_lane','stable_filter4','refined_reset_bridge','refined_zoom_geometry')]+[R/'rtl/04_tracking/target_mailbox.v'])
