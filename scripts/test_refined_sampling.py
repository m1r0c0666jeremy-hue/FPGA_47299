"""Exact eight-frame sampling and same-scene directed-negative comparison."""
from refined_testlib import R,run
import json,zipfile
info=json.loads((R/'reports/refined/protected_inputs.json').read_text(encoding='utf-8'))
old=R/info['backup']/'stable_calibration_before.v'
if not old.exists():
 with zipfile.ZipFile(R/info['backup']/'sources_before.zip') as z:old.write_bytes(z.read('rtl/color_regions/stable_calibration.v'))
src=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,v=0,sample=0;reg [95:0] rgb=0;
wire [11:0] gr,gb;wire [127:0] models;wire [15:0] rev;wire active,needs,fp;wire [7:0] status,fs;wire [23:0] fg;
stable_calibration dut(clk,rst,sof,v,rgb,1'(PAIR),1'b0,sample,1'b0,1'b0,gr,gb,models,rev,active,needs,status,fp,fg,fsEXTRA);
reg [95:0] expected[0:511];reg [20:0] coordinates[0:511];integer f,xx,yy,p,n=0,j,timeout=0;reg [127:0] saved;
function [23:0] pixel(input integer x,y);begin pixel=24'h141414;if(NEGATIVE && x>=636 && x<644 && y>=356 && y<364)pixel=TARGET;end endfunction
always @(posedge clk)if(rst && dut.sample_write)begin
if({dut.rx,dut.ry}!==coordinates[n] || rgb!==expected[n] || dut.sample_wraddr!=n)$fatal(1,"sample coordinate/data/order %0d got%0d/%0d expected%h",n,dut.rx,dut.ry,coordinates[n]);n=n+1;end
initial begin
$readmemh("EXPECTED",expected);$readmemh("COORDINATES",coordinates);
repeat(4)@(negedge clk);rst=1;@(negedge clk);saved=dut.profiles[PAIR];dut.phase=2;dut.cp=PAIR;dut.staged_r=1024;dut.staged_b=1024;
sample=1;@(negedge clk);sample=0;
for(f=0;f<8;f=f+1)for(yy=0;yy<720;yy=yy+1)for(xx=0;xx<1280;xx=xx+4)begin
@(negedge clk);sof=xx==0 && yy==0;v=1;for(p=0;p<4;p=p+1)rgb[95-p*24-:24]=pixel(xx+p,yy);end
@(negedge clk);sof=1;v=0;@(negedge clk);sof=0;
if(n!=512 || !dut.background_valid || dut.phase!=3)$fatal(1,"background incomplete %0d status%h",n,status);
for(j=0;j<512;j=j+1)if(dut.background[j]!==expected[j])$fatal(1,"sample RAM %0d",j);
for(j=0;j<512;j=j+1)dut.samples[j]={4{TARGET}};
dut.phase=4;dut.cp=PAIR;dut.staged_a=dut.profiles[PAIR][63:0];dut.state=5;dut.clear_index=0;
while((dut.state!=0 || timeout==0) && timeout<3000000)begin @(negedge clk);timeout=timeout+1;end
if(timeout>=3000000)$fatal(1,"search timeout");
CHECK
$display("REFINED_SAMPLING_PASS LABEL pairPAIR negativeNEGATIVE 512 exact groups; material/background replay cycles%0d status%h",timeout,status);$finish;end endmodule'''
out=R/'build/sim/refined_sampling';out.mkdir(parents=True,exist_ok=True)
for before,pair,negative in ((True,0,1),(False,0,1),(False,1,1),(False,0,0),(False,1,0)):
 target=0x285078 if pair==0 else 0x782864
 coords=[]
 for f in range(8):
  points=[(52+160*i+8*f,(17+90*j if before else 27+120*j)+8*((3*f)%8)) for j in range(8 if before else 6) for i in range(8)]
  if not before:points += [(x,y) for y in range(356,364) for x in (636,640)]
  coords.extend(sorted(points,key=lambda p:(p[1],p[0])))
 assert len(coords)==512 and all(len(set(coords[f*64:(f+1)*64]))==64 for f in range(8))
 label=f'{"before" if before else "after"}_{pair}_{negative}'
 cf=out/(label+'_coords.hex');cf.write_text('\n'.join(f'{x<<10|y:06x}' for x,y in coords),encoding='ascii')
 ef=out/(label+'_pixels.hex');ef.write_text('\n'.join(''.join(f'{target if negative and 636<=x+p<644 and 356<=y<364 else 0x141414:06x}' for p in range(4)) for x,y in coords),encoding='ascii')
 check='if(dut.phase!=0 || status[3:0]!=0)$fatal(1,"expected separable model");' if before or not negative else 'if(dut.phase!=4 || status[3:0]!=6 || dut.profiles[PAIR]!==saved)$fatal(1,"directed negative not rejected atomically");'
 if not before:check+='if(dut.staged_quality[32:21]!=2048 || dut.staged_quality[41:33]!=256)$fatal(1,"material quality totals");'
 code=src.replace('CHECK',check).replace('PAIR',str(pair)).replace('NEGATIVE',str(negative)).replace('TARGET',f"24'h{target:06x}").replace('EXTRA','' if before else ',,').replace('EXPECTED',ef.as_posix()).replace('COORDINATES',cf.as_posix()).replace('LABEL',label)
 run('sampling_'+label,code,[old if before else R/'rtl/color_regions/stable_calibration.v',R/'rtl/color_regions/regions_divide.v'])
