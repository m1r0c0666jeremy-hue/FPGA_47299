"""Independent pixel and source-completion oracles for native zoom primitives."""
from pathlib import Path
import hashlib,json,sys,re,traceback
from refined_testlib import R,run

RTL=R/'rtl/color_regions'
def execute(name,tb,modules,**kw):
    output=run('native_zoom_'+name,tb,[RTL/n for n in modules],**kw)
    record={'test':name,'output':output.relative_to(R).as_posix(),
            'fixture_sha256':hashlib.sha256((output/'tb.sv').read_bytes()).hexdigest(),
            'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'rtl':{n:hashlib.sha256((RTL/n).read_bytes()).hexdigest() for n in modules}}
    producers={}
    for frame in traceback.extract_stack():
        p=Path(frame.filename)
        if p.is_absolute() and p.is_relative_to(R/'scripts') and p.is_file():
            producers[p.relative_to(R).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    record['producer_inputs']=producers
    (output/'native_receipt.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    return output

PIXEL=r'''
function [23:0] pixel(input integer x,y);
reg [7:0] r,g,b;begin
r=(x*17+y*31+((x^y)&1)*97)&255;
g=(x*7+y*13+3)&255;b=(255-x*11-y*19)&255;
pixel={r,g,b};end endfunction
function [23:0] average(input integer x,y);
reg [23:0] a,b,c,d;reg [9:0] s;integer k;begin
a=pixel(x,y);b=pixel(x+1,y);c=pixel(x,y+1);d=pixel(x+1,y+1);
for(k=0;k<3;k=k+1)begin s={2'd0,a[23-k*8-:8]}+{2'd0,b[23-k*8-:8]}+
{2'd0,c[23-k*8-:8]}+{2'd0,d[23-k*8-:8]}+10'd2;average[23-k*8-:8]=s>>2;end
end endfunction
'''

def pixels(full=False):
    w,h=(2560,1440) if full else (32,8)
    source=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,valid=0,abort_frame=0;
reg [95:0] rgb=0;wire os,ov;wire [95:0] out;wire [32:0] tag;
native_downsample2 #(.WIDTH(W),.HEIGHT(H)) dut(clk,rst,abort_frame,sof,valid,rgb,33'h10000005a,os,ov,out,tag);
integer received=0,starts=0,i,x,y,lane;reg [23:0] expected;
PIXEL
always @(negedge clk)if(rst)begin
 if(os)begin starts=starts+1;if(tag!=33'h10000005a)$fatal(1,"early SOF tag");end
 if(ov)begin
  for(i=0;i<4;i=i+1)begin
   expected=average(((received+i)%(W/2))*2,((received+i)/(W/2))*2);
   if(out[95-i*24-:24]!==expected)$fatal(1,"average mismatch pixel%0d got%h expected%h",received+i,out[95-i*24-:24],expected);
  end received=received+4;
 end
end
initial begin
repeat(4)@(negedge clk);rst=1;sof=1;@(negedge clk);sof=0;
for(y=0;y<H;y=y+1)for(x=0;x<W;x=x+4)begin
 @(negedge clk);valid=1;for(lane=0;lane<4;lane=lane+1)rgb[95-lane*24-:24]=pixel(x+lane,y);
 if(x%28==0)begin @(negedge clk);valid=0;repeat(2)@(negedge clk);end
end
@(negedge clk);valid=0;repeat(10)@(negedge clk);
if(received!=W*H/4 || starts!=1)$fatal(1,"count received%0d starts%0d",received,starts);
// An abort coincident with a potential reduction cannot publish another pair.
abort_frame=1;valid=1;repeat(3)@(negedge clk);valid=0;repeat(5)@(negedge clk);
if(ov || os)$fatal(1,"abort leak");
$display("NATIVE_DOWNSAMPLE_PASS source=%0dx%0d reduced_pixels=%0d",W,H,received);$finish;
end endmodule'''.replace('PIXEL',PIXEL)
    source=re.sub(r'\bW\b',str(w),source)
    source=re.sub(r'\bH\b',str(h),source)
    # Replace only uppercase whole-word constants, not letters within messages.
    execute('average_full' if full else 'average',source,['native_downsample2.v'],timeout=300)

def crop():
    source=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,v=0,abort_frame=0;reg [95:0] rgb;
wire os,ov,ol;wire [95:0] out;wire [32:0] tag;
native_rgb_crop #(.FULL_WIDTH(32),.FULL_HEIGHT(12),.CROP_X(4),.CROP_Y(2),.CROP_WIDTH(24),.CROP_HEIGHT(8))
dut(clk,rst,abort_frame,sof,v,rgb,33'h100000007,os,ov,ol,out,tag);
integer count=0,starts=0,ends=0,x,y,i;reg [23:0] expected;
PIXEL
always @(negedge clk)if(rst && ov)begin
for(i=0;i<4;i=i+1)begin expected=pixel(4+(count+i)%24,2+(count+i)/24);
if(out[95-i*24-:24]!==expected)$fatal(1,"crop wrong index%0d",count+i);end
if(os)starts=starts+1;if(ol)ends=ends+1;count=count+4;
if(tag!=33'h100000007)$fatal(1,"crop tag");end
initial begin repeat(4)@(negedge clk);rst=1;sof=1;@(negedge clk);sof=0;
for(y=0;y<12;y=y+1)for(x=0;x<32;x=x+4)begin
@(negedge clk);v=1;for(i=0;i<4;i=i+1)rgb[95-i*24-:24]=pixel(x+i,y);
@(negedge clk);v=0;end
repeat(5)@(negedge clk);if(count!=192 || starts!=1 || ends!=8)$fatal(1,"crop dimensions");
$display("NATIVE_CROP_PASS includes_full_frame_outside_ROI");$finish;end endmodule'''.replace('PIXEL',PIXEL)
    for phase in range(4):
        fixture=source.replace('.CROP_X(4)',f'.CROP_X({4+phase})').replace('pixel(4+(count+i)%24',f'pixel({4+phase}+(count+i)%24')
        execute(f'crop_phase{phase}',fixture,['native_rgb_crop.v'])

def gate():
    source=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0,verdict=0,good=0,sof=0,v=0,ready=0;
reg [31:0] id=1,vid=1;reg [32:0] tag=33'h100000001;wire out,ok,gt,bt;wire [31:0] oid;
native_source_gate #(.GROUPS(8)) dut(clk,rst,start,id,verdict,good,vid,sof,v,tag,ready,out,ok,oid,gt,bt);
integer n,events=0;
always @(posedge clk)if(rst && out && ready)events=events+1;
task begin_source(input integer number);begin id=number;tag={1'b1,id};start=1;@(negedge clk);start=0;end endtask
task pixels;begin sof=1;v=1;@(negedge clk);sof=0;repeat(7)@(negedge clk);v=0;repeat(2)@(negedge clk);end endtask
task finish_source(input integer number,input bit legal);begin vid=number;good=legal;verdict=1;@(negedge clk);verdict=0;repeat(2)@(negedge clk);end endtask
initial begin repeat(4)@(negedge clk);rst=1;
begin_source(1);finish_source(1,1);if(out)$fatal(1,"EOF alone published before RGB complete");pixels;
if(!out || !ok || oid!=1)$fatal(1,"good source gate");repeat(5)@(negedge clk);
if(!out || oid!=1)$fatal(1,"backpressure must hold verdict");ready=1;repeat(3)@(negedge clk);
if(events!=1 || out)$fatal(1,"duplicate source completion");
begin_source(2);pixels;if(out)$fatal(1,"ROI/pixels alone published before source EOF");
finish_source(2,0);if(events!=2)$fatal(1,"bad tail verdict not delivered");
ready=0;begin_source(5);finish_source(1,1);pixels;
if(out)$fatal(1,"reused low-ID bank accepted stale source verdict");finish_source(5,1);
if(!out || !ok || oid!=5)$fatal(1,"reused slot valid recovery");ready=1;repeat(3)@(negedge clk);
if(events!=3)$fatal(1,"source count");
ready=0;begin_source(6);pixels;v=1;@(negedge clk);v=0;finish_source(6,1);
if(!out || ok)$fatal(1,"late good EOF erased extra RGB failure");ready=1;repeat(3)@(negedge clk);
if(events!=4)$fatal(1,"overflow failure missing");
ready=0;begin_source(7);pixels;finish_source(7,1);ready=1;repeat(3)@(negedge clk);
if(events!=5)$fatal(1,"initial good publication");
v=1;@(negedge clk);v=0;repeat(4)@(negedge clk);
if(events!=6)$fatal(1,"published source overflow was not revoked");
$display("NATIVE_SOURCE_GATE_PASS EOF/RGB/backpressure/bad_tail/bank_reuse");$finish;end endmodule'''
    execute('source_gate',source,['native_source_gate.v'])

def main():
    crop();pixels();gate()
    if '--full' in sys.argv:pixels(True)
if __name__=='__main__':main()
