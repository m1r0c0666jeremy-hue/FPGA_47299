"""Independent rectangle oracle and atomic serialized observation collisions."""
import random
from refined_testlib import R,run

def main():
    rng=random.Random(0x472991024)
    rectangles=[(0,0,6,6),(100,100,300,200),(500,100,700,200),(1200,650,1279,719)]
    vertices=sum((l|(t<<11)|(h<<21)|(b<<32))<<(168*i) for i,(l,t,h,b) in enumerate(rectangles))
    src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,cancel=0,request=0;
reg [10:0] x=0;reg [9:0] y=0;reg [671:0] vertices=0;reg [2:0] nr=4;
wire sample,busy;wire [3:0] im,nm;
stage1_rect_observer dut(clk,rst,cancel,request,x,y,vertices,nr,sample,im,nm,busy);
task clocks;input integer n;begin repeat(n)@(negedge clk);end endtask
task check;input integer px,py,count,inside_expected,near_expected;begin
x=px;y=py;nr=count;request=1;clocks(1);request=0;x=1279-px;y=719-py;
clocks(4);
if(!sample || busy || im!==inside_expected[3:0] || nm!==near_expected[3:0])
$fatal(1,"rectangle xy%0d/%0d nr%0d got%h/%h expected%h/%h",px,py,count,im,nm,inside_expected,near_expected);
clocks(1);if(sample)$fatal(1,"duplicate observation");end endtask
integer phase,i;
initial begin clocks(3);rst=1;clocks(2);
'''+f"vertices=672'h{vertices:x};\n"
    boundary=[]
    for l,t,h,b in rectangles:
        boundary.extend((x,y) for x in (max(0,l-3),max(0,l-2),l,l+2,l+3,h-3,h-2,h,min(1279,h+2),min(1279,h+3))
                        for y in (max(0,t-2),t,t+3,b-3,b,min(719,b+2)))
    for i in range(1200):
        x,y=boundary[i] if i<len(boundary) else (rng.randrange(1280),rng.randrange(720))
        count=4 if i<len(boundary) else rng.randrange(5)
        im=nm=0
        for j,(l,t,h,b) in enumerate(rectangles[:count]):
            if l<=x<=h and t<=y<=b:im|=1<<j
            if l-2<=x<=h+2 and t-2<=y<=b+2 and not(l+2<x<h-2 and t+2<y<b-2):nm|=1<<j
        src+=f'check({x},{y},{count},{im},{nm});\n'
    src+=r'''
for(phase=1;phase<=4;phase=phase+1)begin
x=200;y=150;nr=4;request=1;clocks(1);request=0;clocks(phase-1);
cancel=1;clocks(1);cancel=0;
for(i=0;i<6;i=i+1)begin clocks(1);if(sample || busy)$fatal(1,"canceled observation phase%0d",phase);end
x=200;y=150;request=1;clocks(1);request=0;clocks(phase-1);
x=600;y=150;request=1;clocks(1);request=0;
for(i=0;i<3;i=i+1)begin clocks(1);if(sample)$fatal(1,"old request leaked phase%0d",phase);end
clocks(1);if(!sample || im!=4 || nm!=0)$fatal(1,"request replacement phase%0d",phase);
clocks(1);x=200;y=150;request=1;clocks(1);request=0;clocks(phase-1);
rst=0;clocks(1);rst=1;clocks(6);if(sample || busy)$fatal(1,"reset observation phase%0d",phase);
end
$display("STAGE1_RECT_OBSERVER_PASS cases=1200 cancel/replace/reset/phases1-4 coordinates-locked");$finish;
end endmodule'''
    run('stage1_rect_observer',src,[R/'rtl/color_regions/stage1_regions.v'],timeout=60)

if __name__=='__main__':main()
