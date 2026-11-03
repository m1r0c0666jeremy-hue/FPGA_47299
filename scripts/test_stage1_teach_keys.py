"""Unscaled 75MHz/20ms debounce for mode-11 short keys and hold-to-clear."""
from refined_testlib import R,run

def main():
    src=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #6.667 clk=~clk;reg rst=0;reg [2:0] keys=7;wire [1:0] mode;
wire k2,k3,k4,cancel;integer c2=0,c3=0,c4=0,clear=0;
stage1_controls controls(.I_clk(clk),.I_rst_n(rst),.I_keys_n(keys),.I_ui_switch(2'd3),
.I_gain_ack(1'b0),.I_cal_status(8'd0),.I_pause(1'b0),.I_camera({1'b1,4'd7,4'd0,2'd0,7'd90}),
.O_ui_mode(mode),.O_click2(k2),.O_click3(k3),.O_click4(k4),.O_cancel(cancel));
always @(posedge clk)begin if(k2)c2=c2+1;if(k3)c3=c3+1;if(k4 && !cancel)c4=c4+1;if(k4 && cancel)clear=clear+1;end
task ms;input integer n;begin repeat(n*75000)@(negedge clk);end endtask
task key;input [2:0] mask;input integer n;begin keys=~mask;ms(n);keys=7;ms(35);end endtask
initial begin repeat(4)@(negedge clk);rst=1;ms(40);if(mode!=3)$fatal(1,"mode11");
key(1,50);key(2,100);key(4,300);
if(c2!=1 || c3!=1 || c4!=1 || clear!=0)$fatal(1,"75M shorts %0d/%0d/%0d clear%0d",c2,c3,c4,clear);
key(4,1050);if(clear!=1 || c4!=1)$fatal(1,"long clear leaked short");
// A chord consumes both short gestures even though 11 has no chord command.
key(3,120);if(c2!=1 || c3!=1 || c4!=1 || clear!=1)$fatal(1,"chord leaked command");
$display("STAGE1_TEACH_KEYS_75M_PASS 50/100/300ms long-clear/chord actual75000-cycles-per-ms");$finish;end endmodule'''
    run('stage1_teach_keys_75m',src,[R/'rtl/color_regions/stage1_controls.v'],timeout=1200)

if __name__=='__main__':main()
