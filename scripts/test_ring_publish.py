"""Same-edge pending copy / ready / CDC sampling, without duplicate buffers."""
from test_ring_calibration import R,run
src=r'''module tb;
reg clk=0,dc=0;always #5 clk=~clk;always #7 dc=~dc;reg rst=0;
wire ready,ov,dv;wire [639:0] meta,received;wire [31:0] id,drop;integer count=0;
stable_capture dut(clk,rst,1'b0,1'b0,1'b0,96'd0,1'b0,1'b0,8'd0,128'd0,16'd0,24'd0,8'd0,1'b0,1'b0,ready,id,ov,meta,drop);
target_mailbox #(.WIDTH(640)) mailbox(clk,rst,ov,meta,ready,dc,rst,dv,received);
always @(negedge dc)if(dv)begin
case(count)0:if(received[31:0]!=22)$fatal(1,"copy/ready wrong payload");1:if(received[31:0]!=33)$fatal(1,"pulse/new copy corrupt prior send");2:if(received[31:0]!=44)$fatal(1,"pending bank lost while mailbox busy");default:$fatal(1,"duplicate send");endcase count=count+1;end
initial begin repeat(4)@(negedge clk);rst=1;repeat(2)@(negedge clk);
dut.waiting_packet=640'd11;dut.waiting_result=1;dut.ids[0]=22;dut.wb=0;dut.state=5;
@(negedge clk);if(ov || meta[31:0]!=22 || drop!=1)$fatal(1,"copy-cycle send/drop");
repeat(40)@(negedge clk);if(count!=1 || !ready)$fatal(1,"first CDC");
dut.waiting_packet=640'd33;dut.waiting_result=1;@(negedge clk);if(!ov)$fatal(1,"send not issued");
dut.ids[0]=44;dut.state=5;@(negedge clk);if(ov || meta[31:0]!=44 || drop!=1)$fatal(1,"prior send/new copy guard");
repeat(60)@(negedge clk);if(count!=3 || dut.waiting_result)$fatal(1,"CDC did not drain latest pending");
$display("RING_PUBLICATION_PASS same-cycle ready/copy, previous-pulse mailbox sampling, latest independent cache and no duplicates");$finish;end endmodule'''
run('publication_collision',src,[R/f'rtl/color_regions/{n}.v' for n in ('stable_capture','stable_model_lane','stable_filter4','stable_grid','regions_divide','stable_tracker')]+[R/'rtl/04_tracking/target_mailbox.v'])
