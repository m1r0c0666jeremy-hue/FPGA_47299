"""Independent arithmetic/pixel/grid oracles for the production replacement."""
from pathlib import Path
import os,subprocess,random,json
from fractions import Fraction
from collections import deque
R=Path(__file__).resolve().parents[1];O=R/'build/sim/stable_units';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
logs=[]
def run(name,source,modules):
    tb=O/(name+'.sv');tb.write_text(source,encoding='utf-8')
    for cmd in ([str(iv),'-g2012','-s','tb','-o',str(O/(name+'.vvp')),str(tb),*[str(R/'rtl/color_regions'/m) for m in modules]],
                [str(iv.with_name('vvp.exe')),str(O/(name+'.vvp'))]):
        p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,text=True,timeout=900)
        logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
        (R/'reports/transparent_ring/regression/stable_units.log').write_text('\n'.join(logs),encoding='utf-8')
        if p.returncode:raise SystemExit(p.returncode)
def model(lo,hi,m,d,s):return (1<<63)|(lo<<54)|(hi<<45)|(m<<37)|(d<<29)|(s<<27)
def oracle(rgb,c):
    r,g,b=rgb;m=max(rgb);d=m-min(rgb)
    if not d:return False
    if m==r:h=Fraction(60*(g-b),d)%360
    elif m==g:h=120+Fraction(60*(b-r),d)
    else:h=240+Fraction(60*(r-g),d)
    lo,hi,mv,dc,sc=c
    return m>=mv and d>=dc and 16*d>=[3,4,6,8][sc]*m and ((h>=lo or h<hi) if lo>hi else lo<=h<hi)
rng=random.Random(4783);sets=[[(345,30,32,16,1),(195,255,32,16,1)],[(45,75,32,16,1),(255,330,32,16,1)],[(338,19,24,8,0),(211,263,28,12,2)]]
lines=[]
for k in range(9000):
    c=sets[k%3];rgb=tuple(rng.randrange(256) for _ in range(3));mask=int(oracle(rgb,c[0]))+2*int(oracle(rgb,c[1]))
    lines.append(f'{(model(*c[1])<<64)|model(*c[0]):032x}{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}{mask:x}')
(O/'classifier.hex').write_text('\n'.join(lines),encoding='ascii')
run('classifier',f'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [23:0] rgb=0;reg [127:0] models=0;wire [1:0] hit;
reg [155:0] vectors[0:8999];reg [1:0] expected[0:3];integer i,j;
stable_model_lane dut(clk,rst,rgb,models,hit);
initial begin $readmemh("{(O/'classifier.hex').as_posix()}",vectors);for(j=0;j<4;j=j+1)expected[j]=0;
repeat(3)@(negedge clk);rst=1;
for(i=0;i<9004;i=i+1)begin @(negedge clk);if(i<9000)begin models=vectors[i][155:28];rgb=vectors[i][27:4];end else begin rgb=0;models=0;end
for(j=3;j>0;j=j-1)expected[j]=expected[j-1];expected[0]=i<9000?vectors[i][1:0]:0;
@(posedge clk);#1;if(i>=3 && hit!==expected[3])$fatal(1,"class mismatch %0d got%0d expected%0d",i,hit,expected[3]);end
$display("STABLE_CLASSIFIER_PASS 9000 independent Fraction inputs");$finish;end endmodule''',['stable_model_lane.v'])
run('awb','''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,v=0,s=0,l=0;reg [95:0] rgb=0;reg [11:0] gr=1024,gb=1024;wire ov,os,ol;wire [95:0] out;
stable_awb dut(clk,rst,l,s,v,rgb,gr,gb,ol,os,ov,out);
initial begin repeat(3)@(negedge clk);rst=1;
@(negedge clk);rgb={4{24'h648050}};v=1;s=1;gr=1536;gb=2048;
@(negedge clk);s=0;gr=512;gb=512;
@(posedge clk);#1;if(!ov||!os||out!=={4{24'h9680a0}})$fatal(1,"first SOF/gain alignment %h",out);
@(posedge clk);#1;if(os||out!=={4{24'h9680a0}})$fatal(1,"gain changed mid frame");
@(negedge clk);s=1;rgb={4{24'hffffff}};gr=2048;gb=2048;
@(negedge clk);s=0;v=0;@(posedge clk);#1;if(!os||out!=={4{24'hffffff}})$fatal(1,"saturation");
$display("STABLE_AWB_PASS SOF, freeze, rounding, saturation");$finish;end endmodule''',['stable_awb.v'])
def pixel(x,y,c,case):
    if case==0:
        return (120<=x<180 and 220<=y<270) if c==0 else (340<=x<420 and 230<=y<290)
    if case==1:return True
    return x%32<16 and y%32<16
for case in range(3):
    counts=[[[0,0,0] for _ in range(3600)] for c in range(2)]
    for y in range(720):
        for x in range(1280):
            for c in range(2):
                if pixel(x,y,c,case):
                    v=counts[c][y//16*80+x//16];v[0]+=1;v[1]+=x;v[2]+=y
    expected=[]
    for c in range(2):
        active=set()
        for n,(count,_,__) in enumerate(counts[c]):
            x=n%80;y=n//80
            support=sum(counts[c][yy*80+xx][0] for yy in range(max(0,y-1),min(45,y+2)) for xx in range(max(0,x-1),min(80,x+2)))
            if count>=4 and support>=16:active.add(n)
        comps=[]
        while active:
            root=min(active);active.remove(root);q=deque([root]);nodes=[]
            while q:
                n=q.popleft();nodes.append(n);x=n%80;y=n//80
                for yy in range(max(0,y-1),min(45,y+2)):
                    for xx in range(max(0,x-1),min(80,x+2)):
                        z=yy*80+xx
                        if z in active:active.remove(z);q.append(z)
            count=sum(counts[c][n][0] for n in nodes);sx=sum(counts[c][n][1] for n in nodes);sy=sum(counts[c][n][2] for n in nodes)
            box=(min(n%80 for n in nodes)*16,max(n%80 for n in nodes)*16+15,min(n//80 for n in nodes)*16,max(n//80 for n in nodes)*16+15)
            if count>=48 and box[1]-box[0]<960 and box[3]-box[2]<540:comps.append((count,sx//count,sy//count,box))
        expected.append(comps)
    checks=''
    if case==0:
        for c,comps in enumerate(expected):
            assert len(comps)==1
            count,cx,cy,(x0,x1,y0,y1)=comps[0];n=c*512
            checks+=f'if(!cand[{n+120}] || cand[{n+61}:{n+42}]!={count} || cand[{n+72}:{n+62}]!={cx} || cand[{n+82}:{n+73}]!={cy})$fatal(1,"moments colour{c}: %h",cand[{n+127}:{n}]);\n'
    elif case==1:checks='if(cand[120] || cand[632])$fatal(1,"oversized background accepted");'
    else:checks='if(!cand[120] || !cand[632])$fatal(1,"fragment pressure lost candidates");'
    func=f'''function px;input integer xx,yy,cc;begin
px={('(cc==0?(xx>=120 && xx<180 && yy>=220 && yy<270):(xx>=340 && xx<420 && yy>=230 && yy<290))' if case==0 else '1' if case==1 else '(xx%32<16 && yy%32<16)')};end endfunction'''
    run('grid'+str(case),f'''module tb;reg clk=0;always #5 clk=~clk;reg rst=0,v=0,bank=0,start=0;reg [10:0] x=0;reg [9:0] y=0;reg [3:0] ha=0,hb=0;wire busy,done,failed;wire [1023:0] cand;wire [17:0] cycles;integer xx,yy,p,n;
stable_grid dut(clk,rst,v,bank,x,y,ha,hb,start,1'b0,1'b0,84'd0,1'b0,busy,done,failed,cand,cycles);
{func}
initial begin repeat(3)@(negedge clk);rst=1;
for(yy=0;yy<720;yy=yy+1)for(xx=0;xx<1280;xx=xx+4)begin @(negedge clk);v=1;x=xx;y=yy;for(p=0;p<4;p=p+1)begin ha[p]=px(xx+p,yy,0);hb[p]=px(xx+p,yy,1);end end
@(negedge clk);v=0;repeat(4)@(negedge clk);start=1;@(negedge clk);start=0;n=0;
while(!done && n<215000)begin @(negedge clk);n=n+1;end
if(!done||failed||cycles>=212000)$fatal(1,"grid deadline/failed %0d %0d",cycles,failed);
{checks}
$display("STABLE_GRID_PASS case{case} cycles=%0d",cycles);$finish;end endmodule''',['stable_grid.v','regions_divide.v'])
print('STABLE_UNIT_ORACLES_PASS',flush=True)
