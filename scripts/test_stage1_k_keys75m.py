"""Unscaled 75MHz K-page gestures; no accelerated debounce or hold thresholds."""
from refined_testlib import R,run


def main():
    src=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #6.667 clk=~clk;reg rst=0;reg [2:0] keys=7;reg [1:0] mode=0;
wire [7:0] k,session;wire page,tracking;wire [2:0] zoom;wire down,c2,c3,c4;
stage1_controls dut(.I_clk(clk),.I_rst_n(rst),.I_keys_n(keys),.I_ui_switch(mode),
 .I_gain_ack(1'b0),.I_cal_status(8'd0),.I_pause(1'b0),.I_camera({1'b1,4'd7,4'd0,2'd0,7'd90}),
 .O_k_value(k),.O_k_adjust(page),.O_session(session),.O_tracking(tracking),.O_zoom(zoom),
 .O_down2(down),.O_click2(c2),.O_click3(c3),.O_click4(c4));
integer events=0;reg [7:0] old_session;
always @(posedge clk)if(down || c2 || c3 || c4)events=events+1;
task ms(input integer n);begin repeat(n*75000)@(negedge clk);end endtask
task key(input [2:0] mask,input integer n);begin keys=~mask;ms(n);keys=7;ms(35);end endtask
initial begin repeat(4)@(negedge clk);rst=1;ms(40);
key(2,1050);if(!tracking || k!=50 || page)$fatal(1,"75M tracking setup");
old_session=session;key(3,1050);
if(!page || !tracking || zoom!=0 || session!=old_session)$fatal(1,"75M K chord leaked tracking/zoom");
key(2,50);if(k!=51 || session!=old_session+1)$fatal(1,"75M 50ms increment");
key(4,100);if(k!=50 || session!=old_session+2)$fatal(1,"75M 100ms decrement");
key(2,300);if(k!=51 || session!=old_session+3)$fatal(1,"75M 300ms increment repeated");
key(1,50);if(page || k!=51 || zoom!=0)$fatal(1,"75M exit leaked brightness/zoom");
if(events!=0)$fatal(1,"75M page leaked edit/record events");
$display("STAGE1_K_KEYS_75M_PASS actual75000-cycles-per-ms debounce20 hold1000 short50/100/300 chord/release/no-repeat");$finish;
end endmodule'''
    run('stage1_k_keys_75m',src,[R/'rtl/color_regions/stage1_controls.v'],timeout=1800)


if __name__=='__main__':main()
