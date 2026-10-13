"""Coarse RAM accumulation, 8-neighbour search, border and worst-case deadlines."""
from pathlib import Path
import os,subprocess
from color_regions_reference import grid_regions
R=Path(__file__).resolve().parents[1];O=R/'build/sim/color_regions/grid';O.mkdir(parents=True,exist_ok=True)
W,H=1280,720;cases=[]
for name in ('empty','two_regions','many_and_bottom','all_active'):
 a=[[0]*W for _ in range(H)];b=[[0]*W for _ in range(H)]
 def rect(mask,x,y,w,h):
  for yy in range(y,y+h):mask[yy][x:x+w]=[1]*w
 if name=='two_regions':rect(a,20,20,20,20);rect(a,1000,650,15,30);rect(b,420,210,60,55)
 if name=='many_and_bottom':
  for x,y in ((3,3),(500,250),(900,500)):rect(a,x,y,6,6)
  rect(b,1272,712,8,8)
 if name=='all_active':
  a=[[int(x%2==0) for x in range(W)] for _ in range(H)];b=[[1-v for v in row] for row in a]
 cases.append((name,a,b))
with (O/'stim.txt').open('w') as f:
 for _,a,b in cases:
  for y in range(H):
   for x in range(0,W,4):f.write(f'{sum(a[y][x+i]<<i for i in range(4)):x}{sum(b[y][x+i]<<i for i in range(4)):x}\n')
tb=r'''`timescale 1ns/1ps
module tb;
 reg clk=0,rst=0,beginf=0,bank=0,v=0,start=0,wb=0;always #5 clk=~clk;
 reg [10:0] x=0;reg [9:0] y=0;reg [7:0] masks=0;
 wire busy,done,failed;wire [1:0] ready,bad,more;wire [167:0] boxes;wire [3:0] bv;
 regions_grid dut(clk,rst,beginf,bank,v,x,y,masks[7:4],masks[3:0],start,wb,busy,done,failed,ready,bad,boxes,bv,more);
 integer f,o,c,i,j,r,t;
 initial begin
   f=$fopen("@IN@","r");o=$fopen("@OUT@","w");repeat(4)@(negedge clk);rst=1;
   wait(ready==3);@(negedge clk);
   for(c=0;c<@CASES@;c=c+1)begin
    bank=c%2;beginf=1;@(negedge clk);beginf=0;
    for(j=0;j<720;j=j+1)for(i=0;i<1280;i=i+4)begin
      x=i;y=j;v=1;r=$fscanf(f,"%h\n",masks);@(negedge clk);
    end
    v=0;repeat(3)@(negedge clk);
    $fdisplay(o,"CASE %0d",c);
    for(i=0;i<920;i=i+1)$fdisplay(o,"C %h",dut.counts[{bank,i[9:0]}]);
    wb=bank;start=1;@(negedge clk);start=0;t=0;
    while(!done && t<66000)begin @(negedge clk);t=t+1;end
    if(!done)$fatal(1,"grid timeout");
    $fdisplay(o,"R %0d %0d %h %h %h",failed,t,bv,more,boxes);
    repeat(4)@(negedge clk);
   end
   $display("PASS grid RTL streams");$finish;
 end
endmodule'''.replace('@IN@',(O/'stim.txt').as_posix()).replace('@OUT@',(O/'actual.txt').as_posix()).replace('@CASES@',str(len(cases)))
(O/'tb.sv').write_text(tb,encoding='utf-8');iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','');logs=[]
for a in ([iv,'-g2012','-s','tb','-o',O/'grid.vvp',O/'tb.sv',R/'rtl/color_regions/regions_grid.v'],[iv.with_name('vvp.exe'),O/'grid.vvp']):
 p=subprocess.run(list(map(str,a)),cwd=R,env=env,capture_output=True,text=True,timeout=240);logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
 (R/'reports/color_regions_grid.log').write_text('\n'.join(logs),encoding='utf-8');assert p.returncode==0
actual=[]
for line in (O/'actual.txt').read_text().splitlines():
 t=line.split()
 if t[0]=='CASE':actual.append(dict(counts=[]))
 elif t[0]=='C':actual[-1]['counts'].append(int(t[1],16))
 else:actual[-1].update(failed=int(t[1]),cycles=int(t[2]),valid=int(t[3],16),more=int(t[4],16),boxes=int(t[5],16))
for row,(name,a,b) in zip(actual,cases):
 assert not row['failed'],(name,row['cycles'])
 assert row['cycles']<=65536,(name,row['cycles'])
 counts=[0]*920
 for y in range(H):
  for x in range(W):counts[(y//32)*40+x//32]+=a[y][x]+(b[y][x]<<11)
 assert row['counts']==counts,(name,next((i,row['counts'][i],counts[i]) for i in range(920) if row['counts'][i]!=counts[i]))
 for color,m in enumerate((a,b)):
  want,more=grid_regions(m)
  assert ((row['more']>>color)&1)==more,(name,color,'more')
  got=[]
  for k in range(2):
   idx=color*2+k;v=(row['boxes']>>(42*idx))&((1<<42)-1)
   if (row['valid']>>idx)&1:got.append((v&2047,(v>>11)&2047,(v>>22)&1023,(v>>32)&1023))
  assert got==[t['box'] for t in want],(name,color,got,want)
 logs.append(f'PASS {name}: all 920 two-colour counts, distinct ROIs, {row["cycles"]} cycles')
print('\n'.join(logs[2:]));(R/'reports/color_regions_grid.log').write_text('\n'.join(logs),encoding='utf-8')
