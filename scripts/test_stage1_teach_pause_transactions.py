"""Pause at synchronous lookahead boundaries, then check every replay step."""
from refined_testlib import R,run

BENCH=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,k2=0,k3=0,sample=0;
reg [10:0] x=100;reg [31:0] us=0;
wire [3:0] state;wire [10:0] px;wire [9:0] py;wire [15:0] pm,elapsed;
stage1_route #(.CYCLES_PER_MS(200)) dut(.clk(clk),.rst_n(rst),.mode(2'd3),.key2(k2),.key3(k3),.key4(1'b0),.clear(1'b0),
.image_ok(1'b1),.real_live(1'b1),.real_sample(sample),.real_reason(4'd0),.real_x(x),.real_y(10'd100),.source_us(us),
.context_id(41'd1),.frame_commit(1'b0),.sequence_fail(1'b0),.shown_x(11'd0),.shown_y(10'd0),.shown_ms(16'd0),
.state(state),.point_x(px),.point_y(py),.point_ms(pm),.elapsed_ms(elapsed));
task clocks;input integer n;begin repeat(n)@(negedge clk);end endtask
task ms;input integer n;begin clocks(n*200);end endtask
task point;input integer i;begin x=100+i*100;us=i*50000;sample=1;clocks(1);sample=0;clocks(70);end endtask
integer phase_to_pause,i,t;reg [15:0] held;
initial begin
for(phase_to_pause=5;phase_to_pause<=7;phase_to_pause=phase_to_pause+1)begin
rst=0;clocks(2);rst=1;clocks(3);k2=1;clocks(1);k2=0;
for(i=0;i<5;i=i+1)begin point(i);ms(50);end
k2=1;clocks(1);k2=0;clocks(2);k3=1;clocks(1);k3=0;
while(dut.phase!=phase_to_pause)clocks(1);
k3=1;clocks(1);k3=0;held=elapsed;ms(150);
if(state!=6 || elapsed!=held)$fatal(1,"pause boundary clock phase%0d",phase_to_pause);
k3=1;clocks(1);k3=0;
for(t=50;t<=200;t=t+50)begin
while(pm<t)clocks(1);
if(px!=100+t*2 || py!=100)$fatal(1,"lookahead skipped at pause phase%0d t%0d got%0d expected%0d",phase_to_pause,t,px,100+t*2);
end
end
$display("STAGE1_TEACH_PAUSE_TRANSACTIONS_PASS phases5/6/7 no-skipped-samples");$finish;
end endmodule'''

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--expected-failure',action='store_true');a=ap.parse_args()
    run('stage1_teach_pause_transactions',BENCH,[R/'rtl/color_regions/stage1_regions.v'],timeout=60,expected_failure=a.expected_failure)
