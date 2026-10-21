"""Independent rational geometry oracle for the actual iterative RTL."""
from refined_testlib import R,run
from fractions import Fraction
from math import isqrt
import random,re

def relation(poly,p):
    x,y=p;inside=False;dist=None
    for (ax,ay),(bx,by) in zip(poly,poly[1:]+poly[:1]):
        dx,dy=bx-ax,by-ay;wx,wy=x-ax,y-ay
        cross=dx*wy-dy*wx;dot=wx*dx+wy*dy;length=dx*dx+dy*dy
        if (ay>y)!=(by>y) and ((cross>0 and dy>0) or (cross<0 and dy<0)):inside=not inside
        if dot<=0:d=Fraction(wx*wx+wy*wy)
        elif dot>=length:d=Fraction((x-bx)**2+(y-by)**2)
        else:d=Fraction(cross*cross,length)
        dist=d if dist is None else min(dist,d)
    return int(inside),int(dist<=4),isqrt(dist.numerator//dist.denominator)

def main():
    rng=random.Random(1021)
    polys=[[(20,20),(190,20),(190,150),(20,150)],
           [(250,30),(450,40),(430,200),(390,120),(350,200),(320,110),(270,200),(260,120)],
           [(800,10),(1000,15),(850,300)],
           [(10,550),(200,500),(180,700),(30,690)]]
    queries=[(x,y) for x,y in [(0,0),(1279,719),(20,20),(21,21),(22,22),(23,23),(80,80),(350,170),(350,60),(900,90)]]
    queries +=[(rng.randrange(1280),rng.randrange(720)) for _ in range(110)]
    queries +=[(20+i,100) for i in range(-4,5)]
    vectors=[]
    for count in (1,2,3,4):
        for p in queries:
            verts=0;sizes=0;im=nm=ds=0
            for j,poly in enumerate(polys[:count]):
                sizes|=len(poly)<<(4*j)
                for k,(x,y) in enumerate(poly):verts|=(x|(y<<11))<<(21*(8*j+k))
                a,b,c=relation(poly,p);im|=a<<j;nm|=b<<j;ds|=c<<(11*j)
            vals=[(verts,672),(sizes,16),(count,3),(p[0],11),(p[1],10),(im,4),(nm,4),(ds,44)]
            word=0
            for v,w in vals:word=(word<<w)|v
            vectors.append(f'{word:0191x}')
    out=R/'build/stage1_geometry_vectors';out.mkdir(exist_ok=True,parents=True)
    path=out/'point.hex';path.write_text('\n'.join(vectors)+'\n')
    src='''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;reg [2:0] nr;reg [15:0] counts;
reg [671:0] vertices;reg [10:0] px;reg [9:0] py;wire busy,done;wire [3:0] im,nm;wire [43:0] ds;
stage1_point dut(clk,rst,start,nr,counts,vertices,px,py,busy,done,im,nm,ds);
reg [763:0] vectors[0:N-1];reg [3:0] ei,en;reg [43:0] ed;integer i,t,max_cycles=0;
initial begin $readmemh("FILE",vectors);repeat(3)@(negedge clk);rst=1;
for(i=0;i<N;i=i+1)begin
{vertices,counts,nr,px,py,ei,en,ed}=vectors[i];start=1;@(negedge clk);start=0;t=0;
while(!done && t<20000)begin @(negedge clk);t=t+1;end
if(!done || im!==ei || nm!==en || ds!==ed)$fatal(1,"point case%0d p%0d/%0d inside%h/%h near%h/%h dist%h/%h state%0d",i,px,py,im,ei,nm,en,ds,ed,dut.state);
if(t>max_cycles)max_cycles=t;@(negedge clk);
end
$display("STAGE1_POINT_PASS cases=%0d max_cycles=%0d",N,max_cycles);$finish;end
endmodule'''
    src=re.sub(r'\bN\b',str(len(vectors)),src).replace('FILE',path.as_posix())
    run('stage1_point',src,[R/'rtl/color_regions/stage1_arith.v',R/'rtl/color_regions/stage1_point.v'],timeout=300)

    def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def hit(a,b,c,d):
        return (max(min(a[0],b[0]),min(c[0],d[0]))<=min(max(a[0],b[0]),max(c[0],d[0])) and
                max(min(a[1],b[1]),min(c[1],d[1]))<=min(max(a[1],b[1]),max(c[1],d[1])) and
                orient(a,b,c)*orient(a,b,d)<=0 and orient(c,d,a)*orient(c,d,b)<=0)
    def valid(saved,poly):
        n=len(poly)
        if not 3<=n<=8 or len(saved)>=4:return False
        edges=list(zip(poly,poly[1:]+poly[:1]))
        if any(a==b for a,b in edges):return False
        if sum(a[0]*b[1]-b[0]*a[1] for a,b in edges)==0:return False
        for i,(a,b) in enumerate(edges):
            for j,(c,d) in enumerate(edges[i+1:],i+1):
                if j==i+1 or (i==0 and j==n-1):
                    if orient(a,b,c)==orient(a,b,d)==0:
                        axis=0 if a[0]!=b[0] else 1
                        if max(min(a[axis],b[axis]),min(c[axis],d[axis]))<min(max(a[axis],b[axis]),max(c[axis],d[axis])):return False
                elif hit(a,b,c,d):return False
        for old in saved:
            if any(hit(a,b,c,d) for a,b in edges for c,d in zip(old,old[1:]+old[:1])):return False
            if relation(old,poly[0])[0] or relation(poly,old[0])[0]:return False
        return True
    drafts=[[],[(1,1)],[(1,1),(2,2)],[(500,300),(600,300),(600,400),(500,400)],
            [(20,20),(190,150),(190,20),(20,150)],[(500,500),(600,500),(550,500)],
            [(500,500),(600,500),(550,500),(550,600)],[(500,300),(600,300),(600,300),(500,400)],
            [(30,30),(40,30),(40,40),(30,40)],[(0,0),(210,0),(210,210),(0,210)],
            [(190,50),(220,50),(220,100),(190,100)],
            [(500,300),(700,300),(700,500),(650,450),(600,500),(580,400),(520,480),(510,400)]]
    drafts += [[(x,200),(x+90,220),(x+80,320),(x+20,350)] for x in range(0,1100,35)]
    vv=[]
    for count in range(5):
        for poly in drafts:
            verts=sizes=draft=0
            for j,old in enumerate(polys[:count]):
                sizes|=len(old)<<(4*j)
                for k,(x,y) in enumerate(old):verts|=(x|(y<<11))<<(21*(8*j+k))
            for k,(x,y) in enumerate(poly):draft|=(x|(y<<11))<<(21*k)
            word=0
            for v,w in [(verts,672),(sizes,16),(count,3),(draft,168),(len(poly),4),(int(valid(polys[:count],poly)),1)]:word=(word<<w)|v
            vv.append(f'{word:0216x}')
    path=out/'validate.hex';path.write_text('\n'.join(vv)+'\n')
    src='''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;reg [2:0] nr;reg [15:0] counts;reg [671:0] vertices;
reg [3:0] nd;reg [167:0] draft;wire busy,done,passed;wire [3:0] error_code;
stage1_validate dut(clk,rst,start,nr,counts,vertices,nd,draft,busy,done,passed,error_code);
reg [863:0] vectors[0:N-1];reg ep;integer i,t,max_cycles=0;
initial begin $readmemh("FILE",vectors);repeat(3)@(negedge clk);rst=1;
for(i=0;i<N;i=i+1)begin
{vertices,counts,nr,draft,nd,ep}=vectors[i];start=1;@(negedge clk);start=0;t=0;
while(!done && t<100000)begin @(negedge clk);t=t+1;end
if(!done || passed!==ep)$fatal(1,"validation case%0d nr%0d nd%0d pass%b/%b error%0d state%0d i%0d j%0d",i,nr,nd,passed,ep,error_code,dut.state,dut.i,dut.j);
if(t>max_cycles)max_cycles=t;@(negedge clk);end
$display("STAGE1_VALIDATE_PASS cases=%0d max_cycles=%0d",N,max_cycles);$finish;end
endmodule'''
    src=re.sub(r'\bN\b',str(len(vv)),src).replace('FILE',path.as_posix())
    run('stage1_validate',src,[R/'rtl/color_regions'/n for n in ['stage1_arith.v','stage1_point.v','stage1_segment.v','stage1_validate.v']],timeout=300)

if __name__=='__main__':main()
