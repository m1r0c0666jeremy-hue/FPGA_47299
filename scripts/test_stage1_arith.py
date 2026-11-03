"""Independent integer oracle and exact latency checks for all used ALU widths."""
import math,random
from refined_testlib import R,run

def main():
    rng=random.Random(102121)
    out=R/'build/stage1_arith_vectors';out.mkdir(exist_ok=True)
    for mw,dw in ((12,48),(21,23),(24,14),(14,14)):
        values=[]
        bounds=[0,1,-1,2,-2,-(1<<(mw-1)),(1<<(mw-1))-1]
        for a in bounds:
            for b in bounds:values.append((0,a,b,a*b))
        for _ in range(1200):
            a=rng.randrange(-(1<<(mw-1)),1<<(mw-1));b=rng.randrange(-(1<<(mw-1)),1<<(mw-1))
            values.append((0,a,b,a*b))
        for i in range(400):
            a=rng.getrandbits(48);b=0 if i==0 else rng.randrange(1,1<<dw)
            values.append((1,a,b,((1<<48)-1) if b==0 else a//b))
            values.append((2,a,0,math.isqrt(a)))
        path=out/f'math_{mw}_{dw}.hex'
        mask=(1<<48)-1
        path.write_text('\n'.join(f'{op:x}{a&mask:012x}{b&mask:012x}{v&mask:012x}' for op,a,b,v in values)+'\n')
        source=BENCH.replace('WIDTH',str(mw)).replace('DIVISOR',str(dw)).replace('COUNT',str(len(values))).replace('FILE',path.as_posix())
        run(f'stage1_arith_{mw}_{dw}',source,[R/'rtl/color_regions/stage1_arith.v'],timeout=300)

BENCH=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;reg [1:0] op;reg [47:0] a,b;wire busy,done;wire [47:0] value,rem;
stage1_arith #(.MW(WIDTH),.DW(DIVISOR)) dut(clk,rst,start,op,a,b,busy,done,value,rem);
reg [147:0] v[0:COUNT-1];reg [47:0] expected;integer i,t,want_latency;
initial begin $readmemh("FILE",v);repeat(3)@(negedge clk);rst=1;
for(i=0;i<COUNT;i=i+1)begin
{op,a,b,expected}=v[i];start=1;@(negedge clk);start=0;t=0;
while(!done && t<60)begin @(negedge clk);t=t+1;end
if(!done || value!==expected)$fatal(1,"arith case%0d op%0d a%h b%h got%h want%h",i,op,a,b,value,expected);
if(op==1 && b!=0 && rem!==a%b)$fatal(1,"division residue");
want_latency=op==0?WIDTH:op==1?(b==0?1:48):24;
if(t!=want_latency || busy)$fatal(1,"arithmetic changed latency %0d/%0d",t,want_latency);
@(negedge clk);end
$display("STAGE1_ARITH_PASS width=%0d divisor=%0d cases=%0d",WIDTH,DIVISOR,COUNT);$finish;end endmodule'''

if __name__=='__main__':main()
