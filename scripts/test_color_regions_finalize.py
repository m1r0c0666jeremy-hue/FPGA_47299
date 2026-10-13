"""Frame-finalizer RAM protocol, union-by-rank, fixed point metrics and ranking."""
from pathlib import Path
import os,subprocess,json
R=Path(__file__).resolve().parents[1];O=R/'build/sim/color_regions/finalize';O.mkdir(parents=True,exist_ok=True)
# The labeler test supplies real RTL RAM records; pixel components are checked
# there. Here independently reduce each label graph and calculate top candidates.
rows=[]
for line in (R/'build/sim/color_regions/labeler/actual.txt').read_text().splitlines():
 t=line.split()
 if t[0]=='CASE':rows.append(dict(bad=int(t[2]),n=int(t[3]),ne=int(t[4]),s=[],e=[]))
 elif t[0]=='S':rows[-1]['s'].append(int(t[1],16) if 'x' not in t[1] else 0)
 else:rows[-1]['e'].append(int(t[1],16))
def b(n,l,w):return (n>>l)&((1<<w)-1)
def pack(box,count,sx,sy,sq,membership=1,clip=0):
 x0,x1,y0,y1=box
 return count|(sx<<20)|(sy<<51)|(x0<<82)|(x1<<93)|(y0<<104)|(y1<<114)|(sq<<124)|(membership<<146)|(clip<<148)
# Fairness: a large component and its runner-up share ROI 0; the smaller ROI1
# component must retain a slot. Also check a clipped component never publishes.
rows += [dict(bad=0,n=3,ne=0,e=[],s=[pack((10,29,2,11),200,3900,1300,600),pack((60,74,2,11),150,10050,975,450),pack((900,907,10,13),32,28912,368,0,2)]),
         dict(bad=0,n=1,ne=0,e=[],s=[pack((10,29,2,11),200,3900,1300,600,1,1)])]
expected=[]
# Balanced union tree reaches rank seven; duplicate deep-leaf edges exercise
# all 512 equivalence slots and both root walks without relying on RTL parents.
graph=[]
for stride in (1,2,4,8,16,32,64):
 for i in range(0,128,2*stride):graph.append((i<<7)|(i+stride))
graph += [(127<<7)|126]*(512-len(graph))
rows.append(dict(bad=0,n=128,ne=512,e=graph,s=[pack((i*2,i*2+1,0,1),4,i*8+2,2,12,1+(i%2)) for i in range(128)]))
rows.append(dict(bad=0,n=128,ne=0,e=[],s=[pack((i*8,i*8+3,0,3),16,i*128+24,24,48-i%49,1+(i%2)) for i in range(128)]))
with (O/'stim.txt').open('w') as f:
 for c,row in enumerate(rows):
  f.write(f'{row["bad"]} {row["n"]} {row["ne"]}\n')
  for s in row['s']:f.write(f'{s:x}\n')
  for e in row['e']:f.write(f'{e:x}\n')
  parent=list(range(row['n']))
  def root(x):
   while parent[x]!=x:x=parent[x]
   return x
  for e in row['e']:parent[root(e>>7)]=root(e&127)
  cs={}
  for i,s in enumerate(row['s']):
   a=cs.setdefault(root(i),[0,0,0,1280,0,720,0,0,0,0]);a[0]+=b(s,0,20);a[1]+=b(s,20,31);a[2]+=b(s,51,31)
   a[3]=min(a[3],b(s,82,11));a[4]=max(a[4],b(s,93,11));a[5]=min(a[5],b(s,104,10));a[6]=max(a[6],b(s,114,10));a[7]+=b(s,124,22);a[8]|=b(s,146,2);a[9]|=b(s,148,1)
  items=[];clipped=0
  if not row['bad']:
   for v in cs.values():
    n,sx,sy,x0,x1,y0,y1,sq,mem,clip=v;w=x1-x0+1;h=y1-y0+1
    if clip:clipped|=mem;continue
    if n<16 or w<2 or h<2 or w*4>1280*3 or h*4>32*3:continue
    fill=100*n//(w*h);items.append(dict(box=[x0,x1,y0,y1],count=n,cx=sx//n,cy=sy//n,fill=fill,score=n*(64+fill)+4*sq,mem=mem))
  items.sort(key=lambda a:(-a['score'],a['box'][2],a['box'][0]))
  r0=next((a for a in items if a['mem']&1),None);r1=next((a for a in items if a['mem']&2),None)
  chosen=[r0,r1] if r0 and r1 and r0 is not r1 else items[:2]
  expected.append(dict(bad=row['bad'],more=len(items)>2,clipped=clipped,candidates=chosen))
tb=r'''`timescale 1ns/1ps
module tb;
 reg clk=0,rst=0,start=0,bad=0;reg [7:0] n;reg [9:0] ne;always #5 clk=~clk;
 reg [148:0] s[0:255],sq;reg [13:0] e[0:1023],eq;
 wire [7:0] sa;wire sw;wire [148:0] sd;wire [9:0] ea;
 wire busy,done,failed,more;wire [1:0] clipped;wire [127:0] c0,c1;
 regions_finalize #(.HEIGHT(32)) dut(clk,rst,start,1'b0,n,ne,bad,busy,done,failed,c0,c1,more,clipped,sa,sw,sd,sq,ea,eq);
 always @(posedge clk)begin sq<=s[sa];if(sw)s[sa]<=sd;eq<=e[ea];end
 integer f,o,r,i,j,t;
 initial begin f=$fopen("@IN@","r");o=$fopen("@OUT@","w");repeat(4)@(negedge clk);rst=1;
  for(i=0;i<@N@;i=i+1)begin
   r=$fscanf(f,"%d %d %d\n",bad,n,ne);
   for(j=0;j<n;j=j+1)r=$fscanf(f,"%h\n",s[j]);
   for(j=0;j<ne;j=j+1)r=$fscanf(f,"%h\n",e[j]);
   @(negedge clk);start=1;@(negedge clk);start=0;t=0;
   while(!done && t<66000)begin @(negedge clk);t=t+1;end
   if(!done)$fatal(1,"finalizer timeout");
   $fdisplay(o,"%0d %0d %0d %0d %0d %h %h",i,failed,more,clipped,t,c0,c1);
   repeat(4)@(negedge clk);
  end
  $display("PASS finalizer RTL");$finish;
 end
endmodule'''.replace('@IN@',(O/'stim.txt').as_posix()).replace('@OUT@',(O/'actual.txt').as_posix()).replace('@N@',str(len(rows)))
(O/'tb.sv').write_text(tb,encoding='utf-8');iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','');logs=[]
for a in ([iv,'-g2012','-s','tb','-o',O/'fin.vvp',O/'tb.sv',R/'rtl/color_regions/regions_divide.v',R/'rtl/color_regions/regions_finalize.v'],[iv.with_name('vvp.exe'),O/'fin.vvp']):
 p=subprocess.run(list(map(str,a)),cwd=R,env=env,capture_output=True,text=True,timeout=180);logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
 (R/'reports/color_regions_finalize.log').write_text('\n'.join(logs),encoding='utf-8');assert p.returncode==0
for line,want in zip((O/'actual.txt').read_text().splitlines(),expected):
 t=line.split();i,failed,more,clip,cycles=map(int,t[:5]);got=[]
 for value in t[5:]:
  v=int(value,16)
  if b(v,120,1):got.append(dict(box=[b(v,0,11),b(v,11,11),b(v,22,10),b(v,32,10)],count=b(v,42,20),cx=b(v,62,11),cy=b(v,73,10),fill=b(v,83,7),score=b(v,92,28),mem=b(v,90,2)))
 assert (failed,more,clip,got)==(want['bad'],want['more'],want['clipped'],want['candidates']),(i,failed,more,clip,got,want)
 logs.append(f'PASS frame-finalizer case {i}, {cycles} cycles, candidates={len(got)}')
print('\n'.join(logs[2:]));(R/'reports/color_regions_finalize.log').write_text('\n'.join(logs),encoding='utf-8')
