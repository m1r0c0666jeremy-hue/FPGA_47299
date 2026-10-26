"""A full 30s recording AND replay checked against independent point vectors."""
from pathlib import Path
import hashlib
from refined_testlib import R,run

def main():
    out=R/'build'/('stage1_teach_30_vectors_'+hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]);out.mkdir(exist_ok=True)
    points=[]
    for i in range(600):
        points.append((500,500) if i%200<40 else (100+(i%100)*5,100+((i//100)%4)*100))
    expected=[]
    for t in range(30001):
        i=min(t//50,599)
        x,y=points[i]
        expected.append(x|(y<<11))
    source=out/'input.hex';oracle=out/'expected.hex'
    source.write_text(''.join(f'{x|(y<<11):06x}\n' for x,y in points),encoding='ascii')
    oracle.write_text(''.join(f'{p:06x}\n' for p in expected),encoding='ascii')
    src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,k2=0,k3=0,k4=0,clear=0,sample=0,live=1;
reg [10:0] x=0;reg [9:0] y=0;reg [31:0] us=32'hffff0000;reg checking=0;integer frame_phase=0;
wire commit=checking && frame_phase==0;wire [3:0] state,reason;wire [10:0] count,px;wire [9:0] py;
wire [15:0] elapsed,duration,pm;wire pv,use_point;
reg [15:0] shown_ms=0;reg [10:0] shown_x=0;reg [9:0] shown_y=0;
stage1_route #(.CYCLES_PER_MS(200)) dut(.clk(clk),.rst_n(rst),.mode(2'd3),.key2(k2),.key3(k3),.key4(k4),.clear(clear),
.image_ok(1'b1),.real_live(live),.real_sample(sample),.real_reason(live?4'd0:4'd4),.real_x(x),.real_y(y),.source_us(us),
.context_id(41'd1),.frame_commit(commit),.sequence_fail(1'b0),.shown_x(shown_x),.shown_y(shown_y),.shown_ms(shown_ms),
.state(state),.reason(reason),.count(count),.elapsed_ms(elapsed),.duration_ms(duration),.point_valid(pv),.point_use(use_point),.point_x(px),.point_y(py),.point_ms(pm));
reg [20:0] inputs[0:599],expected[0:30000];integer i,checked=0;reg [15:0] held_time;
always @(posedge clk)begin
if(checking)begin if(frame_phase==3399)frame_phase<=0;else frame_phase<=frame_phase+1;end
if(commit)begin shown_ms<=pm;shown_x<=px;shown_y<=py;
if(pv)begin if(pm>30000 || {py,px}!==expected[pm])$fatal(1,"30s replay t%0d got%0d/%0d expected%0d/%0d",pm,px,py,expected[pm][10:0],expected[pm][20:11]);checked=checked+1;end end
end
task clocks;input integer n;begin repeat(n)@(negedge clk);end endtask
task ms;input integer n;begin clocks(n*200);end endtask
initial begin
$readmemh("INPUT",inputs);$readmemh("ORACLE",expected);
clocks(4);rst=1;clocks(3);k2=1;clocks(1);k2=0;clocks(3);
for(i=0;i<600;i=i+1)begin {y,x}=inputs[i];us=32'hffff0000+i*50000;sample=1;clocks(1);sample=0;clocks(9999);end
clocks(3);if(state!=1 || count!=600 || duration!=30000)$fatal(1,"30s record count%0d duration%0d state%0d",count,duration,state);
live=0;k3=1;clocks(1);k3=0;checking=1;ms(10000);k3=1;clocks(1);k3=0;held_time=elapsed;ms(1000);
if(state!=6 || elapsed!=held_time)$fatal(1,"full route pause");k3=1;clocks(1);k3=0;ms(20100);
if(state!=7 || elapsed!=30000 || count!=600 || checked<1700 || {py,px}!==inputs[599])$fatal(1,"30s end state%0d t%0d n%0d checks%0d",state,elapsed,count,checked);
ms(500);if(elapsed!=30000)$fatal(1,"end clocks advanced");
k4=1;clocks(1);k4=0;if(use_point || count!=600)$fatal(1,"stop loses route");
$display("STAGE1_TEACH_REPLAY30_PASS record600 replay30000ms independent30001-vectors frames=%0d pause/tail/wrap/no-tip",checked);$finish;end endmodule'''
    src=src.replace('INPUT',source.as_posix()).replace('ORACLE',oracle.as_posix())
    run('stage1_teach_replay30',src,[R/'rtl/color_regions/stage1_regions.v'],timeout=600)

if __name__=='__main__':main()
