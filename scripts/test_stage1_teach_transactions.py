"""Exercise command/write collisions on the actual synchronous route memory."""
import argparse
from refined_testlib import R,run

BENCH=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [1:0] mode=3;reg k2=0,k3=0,k4=0,clear=0;
reg image_ok=1,live=1,sample=0;reg [3:0] fault=0;reg [10:0] x=100;reg [9:0] y=100;
reg [31:0] us=0;reg [40:0] context_id=1;wire [3:0] state,reason;wire [10:0] count;
stage1_route #(.CYCLES_PER_MS(200)) dut(.clk(clk),.rst_n(rst),.mode(mode),.current_k(8'd50),.key2(k2),.key3(k3),.key4(k4),.clear(clear),
.image_ok(image_ok),.real_live(live),.real_sample(sample),.real_reason(fault),.real_x(x),.real_y(y),.source_us(us),
.context_id(context_id),.frame_commit(1'b0),.sequence_fail(1'b0),.shown_x(11'd0),.shown_y(10'd0),.shown_ms(16'd0),
.state(state),.reason(reason),.count(count));
task clocks;input integer n;begin repeat(n)@(negedge clk);end endtask
task ms;input integer n;begin clocks(n*200);end endtask
task key2;begin k2=1;clocks(1);k2=0;clocks(3);end endtask
task point;input integer a,t;begin x=a;us=t;sample=1;clocks(1);sample=0;clocks(70);end endtask
task old_route;begin
rst=0;clocks(2);rst=1;mode=3;context_id=1;live=1;image_ok=1;fault=0;sample=0;k2=0;k3=0;k4=0;clear=0;
clocks(3);key2;point(100,0);ms(50);point(200,50000);ms(50);point(300,100000);key2;
if(count!=3 || state!=1)$fatal(1,"prime route");end endtask
integer n;reg [39:0] previous;
initial begin clocks(3);
for(n=0;n<8;n=n+1)begin
old_route;key2;point(900,200000);ms(50);point(1000,250000);previous=dut.memory[2];
ms(50);x=1100;us=300000;sample=1;clocks(1);sample=0;
while(!dut.div_done)clocks(1);
case(n)0:k3=1;1:k4=1;2:k2=1;3:clear=1;4:mode=0;5:begin live=0;fault=4;end 6:context_id=2;7:rst=0;endcase
clocks(1);k2=0;k3=0;k4=0;clear=0;clocks(5);
if(n<2)begin
if(state!=3 || count!=3 || dut.pending_record || dut.memory[2][10:0]!=1100)
$fatal(1,"rejected command stranded accepted sample case%0d state%0d count%0d pending%b",n,state,count,dut.pending_record);
end else begin
if(count!=(n==3 || n==7?0:2) || dut.memory[2]!==previous)$fatal(1,"canceled write published case%0d count%0d",n,count);end
end
old_route;previous=dut.memory[0];key2;x=700;us=200000;sample=1;k2=1;clocks(1);k2=0;sample=0;clocks(5);
if(count!=3 || dut.memory[0]!==previous)$fatal(1,"pending-start/key2 overwrote old payload");
old_route;key2;x=700;us=200000;sample=1;k3=1;clocks(1);k3=0;sample=0;clocks(5);
if(count!=1 || state!=3 || dut.memory[0][10:0]!=700)$fatal(1,"reject play while first valid point commits");
$display("STAGE1_TEACH_TRANSACTIONS_PASS collisions=10 payload/count/cancel/rejected-keys");$finish;end endmodule'''

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidate');ap.add_argument('--expected-failure',action='store_true');a=ap.parse_args()
    core=R/a.candidate if a.candidate else R/'rtl/color_regions/stage1_regions.v'
    run('stage1_teach_transactions',BENCH,[core],expected_failure=a.expected_failure,timeout=60)
