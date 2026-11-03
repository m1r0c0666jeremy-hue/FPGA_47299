"""PLAY/STOP/restart at each synchronous lookahead boundary."""
from refined_testlib import R,run

BENCH=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,k2=0,k3=0,k4=0,clear=0,sample=0,image_ok=1;
reg [1:0] mode=3;reg [10:0] x=100;reg [31:0] us=0;
wire [3:0] state;wire [10:0] px;wire [9:0] py;wire [15:0] pm,elapsed;wire use_point;
integer phase_edge,i,t,command;reg [15:0] held;
stage1_route #(.CYCLES_PER_MS(200)) dut(.clk(clk),.rst_n(rst),.mode(mode),.current_k(8'd50),.key2(k2),.key3(k3),.key4(k4),.clear(clear),
.image_ok(image_ok),.real_live(1'b1),.real_sample(sample),.real_reason(4'd0),.real_x(x),.real_y(10'd100),.source_us(us),
.context_id(41'd1),.frame_commit(1'b0),.sequence_fail(1'b0),.shown_x(11'd0),.shown_y(10'd0),.shown_ms(16'd0),
.state(state),.point_x(px),.point_y(py),.point_ms(pm),.elapsed_ms(elapsed),.point_use(use_point));
task clocks;input integer n;begin repeat(n)@(negedge clk);end endtask
task ms;input integer n;begin clocks(n*200);end endtask
task point;input integer i;begin x=100+i*100;us=i*50000;sample=1;clocks(1);sample=0;clocks(70);end endtask
task prime;begin
rst=0;clocks(2);rst=1;mode=3;image_ok=1;k2=0;k3=0;k4=0;clear=0;clocks(3);k2=1;clocks(1);k2=0;
for(i=0;i<5;i=i+1)begin point(i);ms(50);end
k2=1;clocks(1);k2=0;clocks(2);k3=1;clocks(1);k3=0;
end endtask
initial begin
for(phase_edge=5;phase_edge<=7;phase_edge=phase_edge+1)begin
prime;while(dut.phase!=phase_edge)clocks(1);
k3=1;clocks(1);k3=0;held=elapsed;ms(10);
if(state!=5 || elapsed<=held)$fatal(1,"PLAY paused/restarted at phase%0d",phase_edge);
for(t=50;t<=200;t=t+50)begin
while(pm<t)clocks(1);
if(px!=100+t*2 || py!=100)$fatal(1,"lookahead skipped phase%0d t%0d got%0d",phase_edge,t,px);
end
for(command=0;command<4;command=command+1)begin
prime;while(dut.phase!=phase_edge)clocks(1);
case(command)0:k4=1;1:clear=1;2:mode=0;3:image_ok=0;endcase
clocks(1);k4=0;clear=0;held=pm;clocks(40);
if(use_point || pm!=held || state==5)$fatal(1,"canceled read published phase%0d command%0d",phase_edge,command);
if(command==0)begin k3=1;clocks(1);k3=0;clocks(20);
if(state!=5 || px!=100 || pm!=0)$fatal(1,"STOP/restart did not reset route");end
end end
$display("STAGE1_TEACH_COMMANDS_PASS phases5/6/7 play/stop/restart/cancel");$finish;
end endmodule
'''

if __name__=="__main__":
    run("stage1_teach_pause_transactions",BENCH,[R/"rtl/color_regions/stage1_regions.v"],timeout=60)
