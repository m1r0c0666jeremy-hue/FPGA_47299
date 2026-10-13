"""Four-lane RTL against a rational HSV oracle, including valid bubbles."""
from pathlib import Path
import os,subprocess,random
from color_regions_reference import classify,configuration
R=Path(__file__).resolve().parents[1];O=R/'build/sim/color_regions/classifier';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
rng=random.Random(20261012);pixels=[(n,n,n) for n in range(256)]
pixels += [(25,30,60),(50,25,65),(110,120,114),(23,0,0),(24,0,0)]
for m in (24,25,31,32,40,64,80,128,255):
    for d in (7,8,9,max(1,3*m//16),max(1,(3*m+15)//16)):
        if d>m:continue
        for x in range(m-d,m+1):
            pixels += [(m,x,m-d),(m-d,m,x),(x,m-d,m),(m,m-d,x),(x,m,m-d),(m-d,x,m)]
pixels += [tuple(rng.randrange(256) for _ in range(3)) for _ in range(32768)]
while len(pixels)%4:pixels.append((0,0,0))
with (O/'vectors.txt').open('w') as f:
    for i in range(0,len(pixels),4):
        rgb=hits=quality=0
        for lane,p in enumerate(pixels[i:i+4]):
            rgb=(rgb<<24)|(p[0]<<16)|(p[1]<<8)|p[2]
            hit,q=classify(p,configuration());hits|=hit<<(4*lane);quality|=q<<(2*lane)
        f.write(f'{rgb:024x} {hits:04x} {quality:02x}\n')
tb=r'''`timescale 1ns/1ps
module tb;
 reg clk=0,rst=0,v=0;reg [95:0] rgb=0;always #5 clk=~clk;
 wire ov;wire [15:0] hit;wire [7:0] q;integer f,n,k=0,checked=0;
 reg [15:0] eh,ehq[0:3];reg [7:0] eq,eqq[0:3];reg [3:0] vq=0;
 regions_color4 dut(clk,rst,v,rgb,ov,hit,q);
 always @(posedge clk)begin
   vq<={vq[2:0],v&&rst};ehq[0]<=eh;eqq[0]<=eq;
   for(n=1;n<4;n=n+1)begin ehq[n]<=ehq[n-1];eqq[n]<=eqq[n-1];end
   #1;
   if(ov!==vq[3])$fatal(1,"valid alignment");
   if(ov)begin
     if(hit!==ehq[3] || q!==eqq[3])$fatal(1,"mismatch hit=%h exp=%h quality=%h exp=%h",hit,ehq[3],q,eqq[3]);
     checked=checked+1;
   end
 end
 initial begin
  repeat(4)@(negedge clk);rst=1;
  f=$fopen("@VECTORS@","r");if(!f)$fatal(1,"input");
  while(!$feof(f))begin
    @(negedge clk);v=1;n=$fscanf(f,"%h %h %h\n",rgb,eh,eq);k=k+1;
    if(k%7==0)begin @(negedge clk);v=0;rgb=96'h123456aabbccf0f0f0010203;end
  end
  @(negedge clk);v=0;repeat(8)@(negedge clk);
  if(checked!=@GROUPS@)$fatal(1,"count %d",checked);
  $display("PASS color regions classifier: %0d groups, four independent pixels, rational oracle",checked);$finish;
 end
endmodule'''.replace('@VECTORS@',(O/'vectors.txt').as_posix()).replace('@GROUPS@',str(len(pixels)//4))
(O/'tb.sv').write_text(tb,encoding='utf-8')
logs=[]
for a in ([iv,'-g2012','-s','tb','-o',O/'test.vvp',O/'tb.sv',R/'rtl/color_regions/regions_classifier.v'],[iv.with_name('vvp.exe'),O/'test.vvp']):
    p=subprocess.run(list(map(str,a)),cwd=R,env=env,capture_output=True,text=True,timeout=180)
    logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
    (R/'reports/color_regions_classifier.log').write_text('\n'.join(logs),encoding='utf-8')
    assert p.returncode==0
