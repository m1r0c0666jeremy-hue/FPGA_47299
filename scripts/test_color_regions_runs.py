"""Independent per-pixel run oracle including three events on the last group."""
from pathlib import Path
import os,subprocess,random
R=Path(__file__).resolve().parents[1];O=R/'build/sim/color_regions/runs';O.mkdir(parents=True,exist_ok=True)
rng=random.Random(61);lines=[];W=1280
for pattern in range(16):
    a=[0]*W;a[-8:-4]=[1]*4;a[-4:]=[(pattern>>i)&1 for i in range(4)];lines.append(a)
lines += [[1]*W,[0]*W,[(i%2)==0 for i in range(W)]]
for _ in range(64):lines.append([rng.randrange(2) for i in range(W)])
for _ in range(32):
    a=[0]*W
    for j in range(rng.randrange(1,33)):
        p=rng.randrange(W-30);size=rng.randrange(1,30);a[p:p+size]=[1]*size
    lines.append(a)
with (O/'stim.txt').open('w') as f:
    total=0
    for y,line in enumerate(lines):
        op=None;count=0
        for x in range(0,W,4):
            mask=sum(bool(line[x+i])<<i for i in range(4));quals=[rng.randrange(4) for _ in range(4)]
            memberships=[rng.randrange(1,4) for _ in range(4)];clips=[int(rng.randrange(31)==0) for _ in range(4)];out=[]
            for i in range(4):
                xx=x+i
                if not line[xx]:
                    if op:out.append(op);op=None
                else:
                    if op is None:op=[xx,xx,0,0,0,0,0]
                    op[1]=xx;op[2]+=xx;op[3]+=y;op[4]+=quals[i];op[5]|=clips[i];op[6]|=memberships[i]
            if x==W-4 and op:out.append(op);op=None
            packed=0
            for i,(lo,hi,sx,sy,sq,clip,mem) in enumerate(out):
                packed|=(lo|(hi<<11)|(sx<<22)|(sy<<42)|(sq<<62)|(clip<<74)|(mem<<75))<<(77*i)
            count+=len(out);n=min(count,32);total+=len(out)
            f.write(f'{x} {y} {mask:x} {sum(q<<(2*i) for i,q in enumerate(quals)):x} {sum(m<<(2*i) for i,m in enumerate(memberships)):x} {sum(v<<i for i,v in enumerate(clips)):x} {len(out)} {packed:x} {int(x==W-4)} {n} {int(count>32)}\n')
tb=r'''`timescale 1ns/1ps
module tb;
 reg clk=0,rst=0,v=0;always #5 clk=~clk;reg [10:0] x=0;reg [9:0] y=0;
 reg [3:0] mask=0,clip=0;reg [7:0] q=0,mem=0;wire [1:0] n,lb;wire [230:0] rec;wire eol,ov,fb;wire [5:0] count;wire [9:0] oy;
 integer f,r,en,ee,ec,eo,checked=0;reg [230:0] er;
 regions_runs4 dut(clk,rst,1'b0,v,x,y,mask,clip,q,mem,2'd0,1'b0,n,rec,eol,count,ov,lb,fb,oy);
 initial begin repeat(3)@(negedge clk);rst=1;f=$fopen("@INPUT@","r");
 while(!$feof(f))begin
   @(negedge clk);r=$fscanf(f,"%d %d %h %h %h %h %d %h %d %d %d\n",x,y,mask,q,mem,clip,en,er,ee,ec,eo);v=1;
   @(posedge clk);#1;
   if(n!==en || rec!==er || eol!==ee || ov!==eo || (ee && count!==ec))
      $fatal(1,"run mismatch x%0d y%0d n%0d/%0d rec%h/%h overflow%0d/%0d",x,y,n,en,rec,er,ov,eo);
   checked=checked+1;
 end
 $display("PASS runs4: %0d groups, three-event EOL, moments, flags and overflow",checked);$finish;end
endmodule'''.replace('@INPUT@',(O/'stim.txt').as_posix())
(O/'tb.sv').write_text(tb,encoding='utf-8')
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','');logs=[]
for a in ([iv,'-g2012','-s','tb','-o',O/'runs.vvp',O/'tb.sv',R/'rtl/color_regions/regions_runs4.v'],[iv.with_name('vvp.exe'),O/'runs.vvp']):
 p=subprocess.run(list(map(str,a)),cwd=R,env=env,capture_output=True,text=True,timeout=180);logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
 (R/'reports/color_regions_runs.log').write_text('\n'.join(logs),encoding='utf-8');assert p.returncode==0
