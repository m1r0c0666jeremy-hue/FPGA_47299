"""Full 5MP native ISP, crop, independent pre/post averages, tags and packing."""
from test_native_zoom_core import execute,RTL
from refined_testlib import R

def main():
    tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #8.333 clk=~clk;reg rst=0,sof=0,last=0,v=0;
reg [39:0] data={4{10'd720}};reg [11:0] gr=1536,gb=512;
wire rs,rv,ds,dv,ps,pv,fs,fv;wire [95:0] raw,det;wire [127:0] packed_rgb;
wire [32:0] rt,dt,ft;
native_isp dut(clk,rst,1'b0,sof,last,v,data,33'h100000031,gr,gb,
rs,rv,raw,ds,dv,det,rt,dt,ps,pv,packed_rgb,fs,fv,ft);
integer raw_count=0,det_count=0,packed_count=0,full_count=0;
integer raw_starts=0,det_starts=0,pack_starts=0,x,y,i;reg [7:0] expected;
always @(negedge clk)if(rst)begin
if(fs && ft!==33'h100000031)$fatal(1,"native full tag");
if(fv)full_count=full_count+4;
if(rs)begin raw_starts=raw_starts+1;if(rt!==33'h100000031)$fatal(1,"crop/pre tag");end
if(ds)begin det_starts=det_starts+1;if(dt!==33'h100000031)$fatal(1,"post tag");end
if(ps)pack_starts=pack_starts+1;
if(rv)begin
if(raw!=={4{24'hb4b4b4}})$fatal(1,"pre average pixel%0d got%h",raw_count,raw);
raw_count=raw_count+4;end
if(dv)begin
if(det!=={4{24'hffb45a}})$fatal(1,"post average/clipping/frozen gain pixel%0d got%h",det_count,det);
det_count=det_count+4;end
if(pv)begin
for(i=0;i<16;i=i+1)begin
case((packed_count*16+i)%3)0:expected=255;1:expected=180;2:expected=90;endcase
if(packed_rgb[127-i*8-:8]!==expected)$fatal(1,"dense packed byte%0d got%h",packed_count*16+i,packed_rgb);
end packed_count=packed_count+1;end
end
initial begin repeat(5)@(negedge clk);rst=1;
for(y=0;y<1944;y=y+1)begin
for(x=0;x<648;x=x+1)begin
@(negedge clk);v=1;sof=y==0 && x==0;last=x==647;
end
@(negedge clk);v=0;sof=0;last=0;
if(y==1000)begin gr=512;gb=1536;end
repeat(96)@(negedge clk);
end
repeat(2000)@(negedge clk);
if(full_count!=5038848 || raw_count!=921600 || det_count!=921600 || packed_count!=691200 ||
raw_starts!=1 || det_starts!=1 || pack_starts!=1)
$fatal(1,"native dimensions full%0d raw%0d det%0d words%0d SOF %0d/%0d/%0d",full_count,raw_count,det_count,packed_count,raw_starts,det_starts,pack_starts);
$display("NATIVE_ISP_PASS full5038848/crop3686400/pre921600/post921600/words691200/tags/gain_freeze/saturation");$finish;
end endmodule'''
    names=['native_isp.v','native_rgb_crop.v','native_downsample2.v','native_demosaic.v',
           'native_raw_matrix.v','native_zhenghe.v','native_line_buffer.v','native_line_ram.v',
           'stable_awb.v','stable_packer.v']
    names += [str(R/'user_source/hdl_source/isp/demosaic_4x_2_0'/f'{n}.v')
              for n in ('mipi_to_raw_converter','bilinear_interpolation')]
    names += [str(next((R/'user_source').rglob('data128_96.v')))]
    execute('isp_full',tb,names,compile_args=['-DNATIVE_BEHAVIORAL_RAM'],timeout=1800)
if __name__=='__main__':main()
