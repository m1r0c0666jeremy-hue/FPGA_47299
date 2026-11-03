"""Independent signed-rational endpoint oracle against the production K ALU."""
from pathlib import Path
import random
from refined_testlib import R,run


def rounded(n):
    return (n+50)//100 if n>=0 else -((-n+50)//100)


def main():
    rng=random.Random(1027)
    cases=[]
    # All default-K numerator values, including both halves and outside values.
    for n in range(-1279,3838):
        for a in range(max(0,(n+2)//3),1280):
            b=3*a-n
            if 0<=b<1280:
                cases.append((50,a,360,b,360));break
    for k in range(201):
        for ax,ay,bx,by in ((0,0,1279,719),(1279,719,0,0),(10,10,11,11),
                           (11,11,10,10),(640,360,640,360),(500,400,600,500),
                           (500,400,400,300)):
            cases.append((k,ax,ay,bx,by))
    cases += [(rng.randrange(201),rng.randrange(1280),rng.randrange(720),
               rng.randrange(1280),rng.randrange(720)) for _ in range(12000)]
    out=R/'build/stage1_k_oracle_vectors';out.mkdir(exist_ok=True)
    path=out/'signed_endpoint.hex'
    words=[]
    for k,ax,ay,bx,by in cases:
        tx=rounded(100*ax+k*(ax-bx));ty=rounded(100*ay+k*(ay-by))
        # K8, Ax11, Ay10, Bx11, By10, signed Tx14, signed Ty14.
        value=k
        for n,bits in ((ax,11),(ay,10),(bx,11),(by,10),(tx&16383,14),(ty&16383,14)):
            value=(value<<bits)|n
        words.append(f'{value:020x}\n')
    path.write_text(''.join(words),encoding='ascii')
    source=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;
wire done,tv;wire [10:0] tx;wire [9:0] ty;wire [3:0] bounds;
stage1_k_tracker dut(.clk(clk),.rst_n(rst),.start(1'b0),.frame_id(32'd0),
 .command(10'd1),.revision(16'd0),.complete(1'b1),.candidates(1024'd0),
 .done(done),.tip_valid(tv),.tip_x(tx),.tip_y(ty),.tip_bounds(bounds),.k_value(8'd50));
reg [77:0] vectors[0:COUNT-1];reg [77:0] v;integer i,clocks;
reg signed [13:0] ex,ey;reg [3:0] eb;
initial begin
$readmemh("VECTORS",vectors);repeat(3)@(negedge clk);rst=1;
for(i=0;i<COUNT;i=i+1)begin
 @(negedge clk);v=vectors[i];
 // Isolate the production ALU after the unchanged marker selector/filter.
 // Full classifier/bank ownership is covered separately by the live fixture.
 dut.k_frozen=v[77:70];dut.fax=v[69:59];dut.fay=v[58:49];
 dut.fbx=v[48:38];dut.fby=v[37:28];dut.streak=3;dut.tip_valid=0;dut.state=5;
 ex=$signed(v[27:14]);ey=$signed(v[13:0]);clocks=0;
 @(negedge clk);
 while(!done && clocks<90)begin @(negedge clk);clocks=clocks+1;end
 eb={ey>=720,ey<0,ex>=1280,ex<0};
 if(!done || $signed(dut.nt_x)!==ex || $signed(dut.nt_y)!==ey || bounds!==eb)
 $fatal(1,"K arithmetic case%0d k%0d A%0d/%0d B%0d/%0d got%0d/%0d expected%0d/%0d bounds%b/%b cycles%0d",
 i,v[77:70],v[69:59],v[58:49],v[48:38],v[37:28],$signed(dut.nt_x),$signed(dut.nt_y),ex,ey,bounds,eb,clocks);
 if(tv!==(eb==0) || (tv && (tx!==ex[10:0] || ty!==ey[9:0])))$fatal(1,"K validity/clipping case%0d",i);
end
$display("STAGE1_K_TRACKER_PASS cases=COUNT signed-rational/default-equivalence/all-K/bounds/shared-ALU");$finish;
end endmodule'''.replace('COUNT',str(len(cases))).replace('VECTORS',path.as_posix())
    run('stage1_k_tracker',source,[R/'rtl/color_regions/stage1_memory_video_out.v'],timeout=240)


if __name__=='__main__':main()
