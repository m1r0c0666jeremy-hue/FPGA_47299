"""Actual vendor demosaic to fixed AWB/packer, including upstream ready."""
from pathlib import Path
import os,subprocess
R=Path(__file__).resolve().parents[1];O=R/'build/sim/stable_isp';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
s=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,v=0,sof=0,last=0;reg [39:0] raw=0;reg [11:0] gr=1536,gb=512;
wire ready,rv,rs,dv,ds,ov,os,ol;wire [95:0] rr,dr;wire [127:0] packed_rgb;
stable_isp dut(gr,gb,rr,rs,rv,clk,rst,last,sof,raw,v,10'd0,1'b0,dr,ds,dv,packed_rgb,ol,os,ov,ready);
reg [95:0] expected[0:1];reg [1:0] ev=0,es=0;integer f,x,y,j,rawgroups=0,detectgroups=0,words=0,heads=0,p;
reg [11:0] frozen_r=1536,frozen_b=512;reg [15359:0] unused;
function [7:0] gain;input integer c,g;integer n;begin n=(c*g+512)/1024;gain=n>255?255:n;end endfunction
always @(posedge clk)begin
if(rst)begin
if(ready!==1'b1)$fatal(1,"demosaic upstream ready undriven/backpressured");
if(rs)begin frozen_r=gr;frozen_b=gb;end
if(rv)begin rawgroups=rawgroups+1;if(^rr===1'bx)$fatal(1,"unknown valid demosaic RGB group%0d",rawgroups);end
if(dv)detectgroups=detectgroups+1;
if(ov)words=words+1;if(os)heads=heads+1;
// Compare after the nonblocking AWB pipeline settles; the two-cycle data and
// all sidebands must have identical latency even when gain inputs change.
expected[1]=expected[0];ev={ev[0],rv};es={es[0],rs};
for(j=0;j<4;j=j+1)expected[0][95-24*j-:24]={gain(rr[95-24*j-:8],frozen_r),rr[87-24*j-:8],gain(rr[79-24*j-:8],frozen_b)};
#1;if(dv!==ev[1] || ds!==es[1] || (dv && dr!==expected[1]))$fatal(1,"actual ISP AWB/sideband alignment");
end end
initial begin expected[0]=0;expected[1]=0;repeat(5)@(negedge clk);rst=1;
for(f=0;f<2;f=f+1)begin
gr=f==0?1536:512;gb=f==0?512:2048;
for(y=0;y<720;y=y+1)begin
for(x=0;x<320;x=x+1)begin @(negedge clk);sof=x==0 && y==0;last=x==319;v=1;
raw={10'(((y*3+x)%160+40)*4),10'(((y*5+x)%160+40)*4),10'(((y*7+x)%160+40)*4),10'(((y*9+x)%160+40)*4)};end
@(negedge clk);v=0;sof=0;last=0;repeat(90)@(negedge clk);if(y==350)begin gr=1024;gb=1024;end end
repeat(1000)@(negedge clk);end
repeat(2000)@(negedge clk);
if(rawgroups!=460800 || detectgroups!=460800 || words!=345600 || heads!=2)$fatal(1,"actual ISP full counts raw%0d detect%0d words%0d sof%0d",rawgroups,detectgroups,words,heads);
$display("STABLE_ISP_PASS two complete RAW/demosaic frames, ready, frame-frozen gain, 460800 groups and 345600 packed words");$finish;end endmodule'''
tb=O/'isp.sv';tb.write_text(s,encoding='utf-8')
files=[tb,*[R/f'rtl/color_regions/{m}.v' for m in ('stable_isp','stable_awb','stable_packer')]]
for source in (R/'user_source/hdl_source/isp/demosaic_4x_2_0').rglob('*.v'):
    if source.name=='define.v':continue
    if 'blk_mem_gen_' in source.as_posix():continue
    if source.name=='demosaic.v':
        # Vendor's dangling /*//input and /*//output comments are accepted by
        # TD, rejected by Icarus. Remove only those comment-only lines locally.
        p=O/'demosaic.v';p.write_bytes(source.read_bytes().replace(b'/*//input',b'//input').replace(b'/*//output',b'//output'));files.append(p)
    else:files.append(source)
# TD's ERAM primitive is encrypted for commercial simulators. Use declared
# synchronous NOREG read-before-write port semantics, not a vendor-model claim.
ram=O/'line_ram_models.sv';ram.write_text('''module blk_mem_gen_demosaic(input [32:0] dia,input [10:0] addra,input wea,clka,input [10:0] addrb,input clkb,input [32:0] dib,input web,output reg [32:0] doa,dob);
reg [32:0] mem[0:2047];always @(posedge clka)begin doa<=mem[addra];if(wea)mem[addra]<=dia;end
always @(posedge clkb)begin dob<=mem[addrb];if(web===1'b1)mem[addrb]<=dib;end endmodule
module blk_mem_gen_zhenghe(input [31:0] dia,input [10:0] addra,input wea,clka,input [10:0] addrb,input clkb,input [31:0] dib,input web,output reg [31:0] doa,dob);
reg [31:0] mem[0:2047];always @(posedge clka)begin doa<=mem[addra];if(wea)mem[addra]<=dia;end
always @(posedge clkb)begin dob<=mem[addrb];if(web===1'b1)mem[addrb]<=dib;end endmodule
''',encoding='utf-8')
files.extend([next((R/'user_source').rglob('data128_96.v')),ram])
logs=[]
for cmd in ([iv,'-g2012','-s','tb','-o',O/'isp.vvp',*files],[iv.with_name('vvp.exe'),O/'isp.vvp']):
    p=subprocess.run(list(map(str,cmd)),cwd=R,env=env,capture_output=True,text=True,timeout=900);logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
    (R/'reports/stable_isp.log').write_text('\n'.join(logs),encoding='utf-8')
    if p.returncode:raise SystemExit(p.returncode)
