from pathlib import Path
"""Fraction-based supercover oracle, independent of incremental RTL and RAM packing."""
from refined_testlib import R,run
import hashlib
from fractions import Fraction
import argparse,re

def ceil(v):return -((-v.numerator)//v.denominator)
def mapped(v,o,z,flip,limit):
    p,q=[(1,1),(3,2),(2,1),(3,1),(4,1)][z]
    left=ceil(Fraction((v-o)*p,q));right=ceil(Fraction((v-o+1)*p,q))-1
    result=(left+right)//2
    return limit-1-result if flip else result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--quick',action='store_true');ap.add_argument('--rows',type=int,default=624);a=ap.parse_args()
    assert 1<=a.rows<=624
    cases=[(z,r,2,0) for z in range(5) for r in range(2)]
    if a.quick:cases=[(1,0,2,0),(4,1,2,0)]
    else:cases +=[(0,0,1,0),(0,0,2,1),(1,0,1,2),(0,0,1,3)]
    out=R/'build'/('stage1_rect_render_vectors_'+hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]);out.mkdir(exist_ok=True,parents=True)
    contexts=[]
    for case,(z,rot,mode,kind) in enumerate(cases):
        active=[[(80,80),(400,170)],[(500,100),(750,300)],[(1100,500),(1250,710)],[(5,10),(60,710)]];closed=15
        if kind==1:active=[[(0,0),(1279,719)],[(40,48),(80,80)],[(1200,0),(1279,40)],[(0,680),(100,719)]]
        elif kind==2:active=[[(90,90)]];closed=0
        elif kind==3:active=[[(350,280),(90,90)]];closed=0
        verts=sizes=0
        for j,rect in enumerate(active):
            sizes|=len(rect)<<(4*j)
            for k,(x,y) in enumerate(rect):verts|=(x|(y<<11))<<(21*(8*j+k))
        context=0
        for v,w in [(verts,672),(sizes,16),(closed,4),(mode,2),(40,11),(48,10),(z,3),(rot,1),(2,4),(1,4),(1,3),(0,3)]:context=(context<<w)|v
        contexts.append(f'{context:0184x}');rows=[0]*a.rows
        def span(region,y,lo,hi):
            if not 0<=y<a.rows:return
            lo=max(0,lo);hi=min(1279,hi)
            if lo<=hi:rows[y]|=(((1<<(4*(hi-lo+1)))-1)//15)*(1<<region)<<(4*lo)
        for region,rect in enumerate(active):
            points=[(mapped(x,40,z,rot,1280),mapped(y,48,z,rot,624)) for x,y in rect]
            l=min(x for x,y in points);r=max(x for x,y in points);t=min(y for x,y in points);b=max(y for x,y in points)
            if len(points)==2:
                span(region,t,l,r);span(region,b,l,r)
                for y in range(max(0,t),min(a.rows-1,b)+1):span(region,y,l,l);span(region,y,r,r)
            if mode==1:
                for cx,cy in ([(l,t)] if len(points)==1 else [(l,t),(r,b)]):
                    for yy in range(cy-2,cy+3):span(region,yy,cx-2,cx+2)
        (out/f'expected_{case}.hex').write_text('\n'.join(f'{v:01280x}' for v in rows)+'\n')
    (out/'contexts.hex').write_text('\n'.join(contexts)+'\n')
    src=r"""module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,commit=0;reg [671:0] vertices;reg [15:0] counts;reg [3:0] closed;
reg [1:0] mode;reg [10:0] x0,x=0;reg [9:0] y0,y=0;reg [2:0] zoom;reg rotate;
reg [3:0] state,completed;reg [2:0] target,actual;reg de=0;
wire [3:0] mask;wire [23:0] color,label_color;wire label_on,ready,underrun;wire [7:0] glyph;wire [2:0] gx;wire [3:0] gy;
reg [732:0] contexts[0:CASES-1];reg [5119:0] expected[0:ROWS-1];integer c,yy,h;reg [3:0] want;
wire [1:0] split_region=c[1:0];wire [167:0] split_draft=vertices>>(split_region*168);
wire [671:0] split_mask={{504{1'b0}},{168{1'b1}}}<<(split_region*168);wire [671:0] split_saved=vertices & ~split_mask;
stage1_render #(.SPLIT_DRAFT(1)) dut(clk,rst,commit,split_saved,counts,closed,mode,x0,y0,zoom,rotate,state,completed,target,actual,
x,y,de,mask,color,label_on,glyph,gx,gy,label_color,ready,underrun,split_draft,{1'b0,split_region},1'b1);
initial begin $readmemh("DIR/contexts.hex",contexts);repeat(3)@(negedge clk);rst=1;
for(c=0;c<CASES;c=c+1)begin
@(negedge clk);{vertices,counts,closed,mode,x0,y0,zoom,rotate,state,completed,target,actual}=contexts[c];
$readmemh($sformatf("DIR/expected_%0d.hex",c),expected);de=0;x=0;y=0;commit=1;@(negedge clk);commit=0;
repeat(10000)@(negedge clk);if(!ready || underrun)$fatal(1,"rectangle preparation deadline");vertices=0;counts=0;
for(yy=0;yy<ROWS;yy=yy+1)for(h=0;h<1650;h=h+1)begin
@(negedge clk);de=h<1280;x=h<1280?h:0;y=yy;@(posedge clk);#1;
if(de)begin want=expected[yy][h*4+:4];if(mask!==want || underrun)$fatal(1,"rectangle c%0d z%0d r%b xy%0d/%0d got%h want%h",c,zoom,rotate,h,yy,mask,want);end
end
de=0;$display("STAGE1_RENDER_CASE_PASS case%0d zoom%0d rotate%b rows%0d",c,zoom,rotate,ROWS);
end
$display("STAGE1_RENDER_PASS cases=%0d pixels=%0d",CASES,CASES*ROWS*1280);$finish;end
endmodule"""
    src=src.replace('DIR',out.as_posix()).replace('CASES',str(len(cases))).replace('ROWS',str(a.rows))
    run(f'stage1_render_{len(cases)}_{a.rows}',src,[R/'rtl/color_regions/stage1_render.v'],timeout=1800)

if __name__=='__main__':main()
