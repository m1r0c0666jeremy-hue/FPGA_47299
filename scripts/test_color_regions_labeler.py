"""Check RAM-backed run labels/equivalences against independent pixel BFS."""
from pathlib import Path
import os,subprocess,json
from color_regions_reference import components
R=Path(__file__).resolve().parents[1];O=R/'build/sim/color_regions/labeler';O.mkdir(parents=True,exist_ok=True)
W=1280;H=32;cases=[]
def case(name):
    a=[[0]*W for _ in range(H)];cases.append((name,a));return a
def box(a,x,y,w,h):
    for yy in range(y,y+h):
        for xx in range(x,x+w):a[yy][xx]=1
case('empty');a=case('solid');box(a,120,3,400,24)
a=case('ring');box(a,150,2,30,28)
for yy in range(5,27):
    for xx in range(154,176):a[yy][xx]=0
box(a,900,10,15,12)
a=case('diagonal_equality');box(a,10,2,3,1);box(a,14,2,3,1);box(a,12,3,3,1)
# One previous run must remain available for the next diagonal current run.
box(a,40,6,3,1);box(a,39,7,3,1);box(a,43,7,3,1)
a=case('32_runs');
for n in range(32):box(a,n*40,0,3,H)
a=case('33_runs');
for n in range(33):box(a,n*38,0,3,H)
for count in (128,129):
    a=case(str(count)+'_labels')
    for n in range(count):box(a,(n%32)*40,(n//32)*4,2,2)
a=case('full_width');box(a,0,0,W,H)
a=case('three_eol_events');box(a,1270,0,6,H);box(a,1277,0,1,H);box(a,1279,0,1,H)
with (O/'stim.txt').open('w') as f:
 for ci,(name,a) in enumerate(cases):
    for y in range(H):
      for x in range(0,W,4):f.write(f'{sum(a[y][x+i]<<i for i in range(4)):x}\n')
expected=[]
for name,a in cases:expected.append((name,components(a,[[1]*W for _ in range(H)])))
tb=r'''`timescale 1ns/1ps
module tb;
 reg clk=0,rst=0,v=0,sof=0,beginf=0,bank=0;always #5 clk=~clk;
 reg [10:0] x=0;reg [9:0] y=0;reg [1:0] lb=0;reg [3:0] mask=0;
 wire [1:0] rn,rl;wire [230:0] rr;wire re,rov,rf;wire [5:0] rt;wire [9:0] ry;
 regions_runs4 front(clk,rst,sof,v,x,y,mask,4'd0,8'h55,8'h55,lb,bank,rn,rr,re,rt,rov,rl,rf,ry);
 wire [1:0] bad;wire closed,cb;wire [7:0] n0,n1;wire [9:0] e0,e1;wire [8:0] maxcy;
 reg [7:0] sa=0;reg [9:0] ea=0;wire [148:0] sq;wire [13:0] eq;
 regions_run_labeler #(.HEIGHT(@H@)) dut(clk,rst,beginf,bank,rn,rr,re,rov,rt,rl,rf,ry,
       bad,closed,cb,n0,n1,e0,e1,sa,1'b0,149'd0,sq,ea,eq,maxcy);
 integer f,o,i,j,c,k,r,waits,nn,ne;reg seen;
 always @(posedge clk)if(closed)seen<=1;
 initial begin
  f=$fopen("@INPUT@","r");o=$fopen("@OUTPUT@","w");
  repeat(4)@(negedge clk);rst=1;
  for(c=0;c<@CASES@;c=c+1)begin
    @(negedge clk);bank=c%2;beginf=1;seen=0;
    @(negedge clk);beginf=0;
    for(j=0;j<@H@;j=j+1)for(i=0;i<1280;i=i+4)begin
       v=1;x=i;y=j;lb=j%3;sof=(i==0 && j==0);r=$fscanf(f,"%h\n",mask);@(negedge clk);
    end
    v=0;sof=0;waits=0;
    while(!seen && waits<600)begin @(negedge clk);waits=waits+1;end
    if(!seen)$fatal(1,"no closure case %0d state%0d pending%0d",c,dut.state,dut.pending);
    nn=bank?n1:n0;ne=bank?e1:e0;
    $fdisplay(o,"CASE %0d %0d %0d %0d %0d",c,bad[bank],nn,ne,maxcy);
    for(k=0;k<nn;k=k+1)begin sa={bank,k[6:0]};@(posedge clk);#1;$fdisplay(o,"S %h",sq);@(negedge clk);end
    for(k=0;k<ne;k=k+1)begin ea={bank,k[8:0]};@(posedge clk);#1;$fdisplay(o,"E %h",eq);@(negedge clk);end
    repeat(10)@(negedge clk);
  end
  $display("PASS labeler RTL stream completed");$finish;
 end
endmodule'''.replace('@H@',str(H)).replace('@CASES@',str(len(cases))).replace('@INPUT@',(O/'stim.txt').as_posix()).replace('@OUTPUT@',(O/'actual.txt').as_posix())
(O/'tb.sv').write_text(tb,encoding='utf-8');iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe'
env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','');logs=[]
for a in ([iv,'-g2012','-s','tb','-o',O/'labeler.vvp',O/'tb.sv',R/'rtl/color_regions/regions_runs4.v',R/'rtl/color_regions/regions_run_labeler.v'],[iv.with_name('vvp.exe'),O/'labeler.vvp']):
 p=subprocess.run(list(map(str,a)),cwd=R,env=env,capture_output=True,text=True,timeout=240);logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
 (R/'reports/color_regions_labeler.log').write_text('\n'.join(logs),encoding='utf-8');assert p.returncode==0
actual=[]
for line in (O/'actual.txt').read_text().splitlines():
 t=line.split()
 if t[0]=='CASE':actual.append(dict(case=int(t[1]),bad=int(t[2]),n=int(t[3]),edges=int(t[4]),cycles=int(t[5]),s=[],e=[]))
 elif t[0]=='S':
    if 'x' in t[1]:assert actual[-1]['bad'],'Unknown valid statistics';actual[-1]['s'].append(None)
    else:actual[-1]['s'].append(int(t[1],16))
 else:actual[-1]['e'].append(int(t[1],16))
def bits(n,lo,w):return (n>>lo)&((1<<w)-1)
for row,(name,truth) in zip(actual,expected):
 if name in ('33_runs','129_labels'):
    assert row['bad'],(name,row);continue
 assert not row['bad'],(name,row)
 assert row['cycles']<288,(name,row['cycles'])
 parent=list(range(row['n']))
 def root(x):
    while parent[x]!=x:x=parent[x]
    return x
 for edge in row['e']:parent[root(edge>>7)]=root(edge&127)
 groups={}
 for label,s in enumerate(row['s']):
    key=root(label);a=groups.setdefault(key,dict(count=0,sx=0,sy=0,sumq=0,box=[1280,-1,720,-1]))
    a['count']+=bits(s,0,20);a['sx']+=bits(s,20,31);a['sy']+=bits(s,51,31);a['sumq']+=bits(s,124,22)
    a['box']=[min(a['box'][0],bits(s,82,11)),max(a['box'][1],bits(s,93,11)),min(a['box'][2],bits(s,104,10)),max(a['box'][3],bits(s,114,10))]
 got=sorted((tuple(a['box']),a['count'],a['sx'],a['sy'],a['sumq']) for a in groups.values())
 want=sorted((a['box'],a['count'],a['sx'],a['sy'],a['sumq']) for a in truth)
 assert got==want,(name,got[:8],want[:8])
 logs.append(f'PASS {name}: {len(got)} independent pixel components, max row {row["cycles"]} cycles')
print('\n'.join(logs[2:]));(R/'reports/color_regions_labeler.log').write_text('\n'.join(logs),encoding='utf-8')
