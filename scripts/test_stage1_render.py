"""Fraction-based supercover oracle, independent of incremental RTL and RAM packing."""
from refined_testlib import R,run
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
    polys=[[(80,80),(400,85),(380,170),(100,160)],
           [(500,100),(750,120),(730,300),(670,210),(620,300),(570,200),(520,280),(510,180)],
           [(1100,500),(1250,510),(1220,710),(1120,680)],
           [(5,10),(60,18),(55,710),(10,700)]]
    cases=[(z,r,2,0) for z in range(5) for r in range(2)]
    if a.quick:cases=[(1,0,2,0),(4,1,2,0)]
    else:cases +=[(0,0,1,0),(0,0,2,1),(1,0,1,2),(0,0,1,3)]
    out=R/'build/stage1_render_vectors';out.mkdir(exist_ok=True,parents=True)
    contexts=[]
    for case,(z,rot,mode,kind) in enumerate(cases):
        active=polys;closed=15
        if kind==1:
            active=[[(x,y),(x+70,y+1),(x+130,y+30),(x+150,y+110),(x+120,y+170),(x+60,y+180),(x+10,y+140),(x-10,y+60)] for x,y in [(90,80),(480,90),(800,300),(300,480)]]
        elif kind==2:active=[[(90,90)]];closed=0
        elif kind==3:active=[[(90,90),(350,95),(180,280)]];closed=0
        verts=sizes=0
        for j,poly in enumerate(active):
            sizes|=len(poly)<<(4*j)
            for k,(x,y) in enumerate(poly):verts|=(x|(y<<11))<<(21*(8*j+k))
        context=0
        for v,w in [(verts,672),(sizes,16),(closed,4),(mode,2),(40,11),(48,10),(z,3),(rot,1),(2,4),(1,4),(1,3),(0,3)]:context=(context<<w)|v
        contexts.append(f'{context:0184x}')
        rows=[0]*a.rows
        for region,poly in enumerate(active):
            points=[(mapped(x,40,z,rot,1280),mapped(y,48,z,rot,624)) for x,y in poly]
            edges=list(zip(points,points[1:]+(points[:1] if closed>>region&1 else [])))
            if len(points)==1:edges=[(points[0],points[0])]
            for (ax,ay),(bx,by) in edges:
                if by<ay:ax,bx,ay,by=bx,ax,by,ay
                for y in range(max(0,ay-(2 if len(points)==1 and mode==1 else 0)),min(a.rows-1,by+(2 if len(points)==1 and mode==1 else 0))+1):
                    if ay==by:low,high=min(ax,bx),max(ax,bx)
                    else:
                        lo_y=2*ay if y==ay else 2*y-1
                        hi_y=2*by if y==by else 2*y+1
                        u=Fraction(2*ax)+Fraction((bx-ax)*(lo_y-2*ay),by-ay)
                        v=Fraction(2*ax)+Fraction((bx-ax)*(hi_y-2*ay),by-ay)
                        low=ceil((min(u,v)-1)/2);high=(max(u,v)+1)//2
                    if mode==1 and (len(points)==1 or y==ay or y==by):low-=2;high+=2
                    low=max(0,low);high=min(1279,high)
                    if low<=high:rows[y]|=(((1<<(4*(high-low+1)))-1)//15)*(1<<region)<<(4*low)
        (out/f'expected_{case}.hex').write_text('\n'.join(f'{v:01280x}' for v in rows)+'\n')
    (out/'contexts.hex').write_text('\n'.join(contexts)+'\n')
    src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,commit=0;reg [671:0] vertices;reg [15:0] counts;reg [3:0] closed;
reg [1:0] mode;reg [10:0] x0,x=0;reg [9:0] y0,y=0;reg [2:0] zoom;reg rotate;
reg [3:0] state,completed;reg [2:0] target,actual;reg de=0;
wire [3:0] mask;wire [23:0] color,label_color;wire label_on,ready,underrun;wire [7:0] glyph;wire [2:0] gx;wire [3:0] gy;
stage1_render dut(clk,rst,commit,vertices,counts,closed,mode,x0,y0,zoom,rotate,state,completed,target,actual,
x,y,de,mask,color,label_on,glyph,gx,gy,label_color,ready,underrun);
reg [732:0] contexts[0:CASES-1];reg [5119:0] expected[0:ROWS-1];integer c,yy,h,dbg;reg [3:0] want;reg [127:0] ew;
initial begin $readmemh("DIR/contexts.hex",contexts);repeat(3)@(negedge clk);rst=1;
for(c=0;c<CASES;c=c+1)begin
@(negedge clk);
{vertices,counts,closed,mode,x0,y0,zoom,rotate,state,completed,target,actual}=contexts[c];
$readmemh($sformatf("DIR/expected_%0d.hex",c),expected);de=0;x=0;y=0;commit=1;@(negedge clk);commit=0;
repeat(10000)@(negedge clk);if(!ready || underrun)$fatal(1,"initial row deadline state%0d",dut.state);
vertices=0;counts=0;
for(yy=0;yy<ROWS;yy=yy+1)begin
for(h=0;h<1650;h=h+1)begin
@(negedge clk);de=h<1280;x=h<1280?h:0;y=yy;
@(posedge clk);#1;
if(de)begin want=expected[yy][h*4+:4];
if(mask!==want || underrun)begin
for(dbg=8;dbg<16;dbg=dbg+1)begin ew={dut.edge_mem[dbg*8+7],dut.edge_mem[dbg*8+6],dut.edge_mem[dbg*8+5],dut.edge_mem[dbg*8+4],dut.edge_mem[dbg*8+3],dut.edge_mem[dbg*8+2],dut.edge_mem[dbg*8+1],dut.edge_mem[dbg*8]};
$display("EDGE%0d span%b %0d..%0d cur%d rem%0d q%d r%0d den%0d ys%0d..%0d end%d flags%b",dbg,dut.span_valid[dbg],dut.span_lo[dbg],dut.span_hi[dbg],$signed(ew[15:0]),ew[29:16],$signed(ew[45:30]),ew[59:46],ew[73:60],ew[83:74],ew[93:84],$signed(ew[109:94]),ew[114:110]);end
$fatal(1,"render c%0d z%0d r%b xy%0d/%0d mask%h/%h state%0d row%0d ready%b bank%b tag%0d underrun%b",c,zoom,rotate,h,yy,mask,want,dut.state,dut.row,ready,dut.bank_valid,dut.bank_row[yy%2],underrun);end
end end end
de=0;$display("STAGE1_RENDER_CASE_PASS case%0d zoom%0d rotate%b rows%0d",c,zoom,rotate,ROWS);
end
$display("STAGE1_RENDER_PASS cases=%0d pixels=%0d",CASES,CASES*ROWS*1280);$finish;end
endmodule'''
    src=src.replace('DIR',out.as_posix()).replace('CASES',str(len(cases))).replace('ROWS',str(a.rows))
    run(f'stage1_render_{len(cases)}_{a.rows}',src,[R/'rtl/color_regions/stage1_arith.v',R/'rtl/color_regions/stage1_render.v'],timeout=1800)

if __name__=='__main__':main()
