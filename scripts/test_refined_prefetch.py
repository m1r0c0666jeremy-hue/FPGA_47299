"""Identical source RGB/mask checks for frozen old and new row loaders."""
from refined_testlib import R,run
import json,zipfile
data=json.loads((R/'reports/refined/protected_inputs.json').read_text(encoding='utf-8'))
baseline=R/data['backup']/'stable_line_reader_before.v'
if not baseline.exists():
    with zipfile.ZipFile(R/data['backup']/'sources_before.zip') as z:
        baseline.write_bytes(z.read('rtl/color_regions/stable_line_reader.v'))
src=r'''`timescale 1ns/1ps
module tb;
reg pc=0,dc=0,rst=0,commit=0;always #6.667 pc=~pc;always #7.5 dc=~dc;
wire rd,busy;wire [24:0] addr;reg valid=0,ready=1;reg [127:0] data=0;
integer rotate=0,cycles=0,head=0,tail=0,rowcycles=0,rows=0,pixels=0,masks=0;
integer queue[0:2047],due[0:2047];wire [23:0] rgb;wire [1:0] mask;wire vs,hs,de,ok;
function [63:0] model(input integer lo,hi);model=64'h8000000000000000|(64'(lo)<<54)|(64'(hi)<<45)|(64'd32<<37)|(64'd16<<29)|(64'd1<<27);endfunction
wire [127:0] models={model(195,255),model(345,30)};
stable_line_reader dut(commit,1'b1,rst,dc,1'b0,1'b0,2'd2,32'd55,models,ready,valid,data,busy,rd,addr,pc,1'b0,1'b0,1'b0,11'd0,10'd48,2'd0,vs,hs,de,rgb,mask,ok,1'(rotate)EXTRA_PORTS);
function [23:0] pixel(input integer xx,yy);pixel={8'(xx),8'(yy),8'(((xx>>8)*64)+((yy>>8)*16)+((xx^yy)&15))};endfunction
function [1:0] classify(input integer xx,yy);
 integer r,g,b,m,d,n;reg [23:0] p;begin
 classify=0;if(xx>=0 && xx<1280 && yy>=0 && yy<720)begin
 p=pixel(xx,yy);r=p[23:16];g=p[15:8];b=p[7:0];m=r>g?(r>b?r:b):(g>b?g:b);d=m-(r<g?(r<b?r:b):(g<b?g:b));
 if(m>=32 && d>=16 && d*4>=m)begin
 if(m==r)begin n=60*(g-b);if(n<0)n=n+360*d;end
 else if(m==g)n=120*d+60*(b-r);else n=240*d+60*(r-g);
 classify={(n>=195*d && n<255*d),(n<30*d || n>=345*d)};end end end endfunction
function [1:0] supported(input integer xx,yy);
 integer dx,dy;reg [1:0] neighbors;begin neighbors=0;
 for(dy=-1;dy<=1;dy=dy+1)for(dx=-1;dx<=1;dx=dx+1)if(dx!=0 || dy!=0)neighbors=neighbors|classify(xx+dx,yy+dy);
 supported=classify(xx,yy)&neighbors;end endfunction
function [127:0] word_at(input integer aa);integer j,bp,xx,yy,ch;reg [23:0] p;begin
 for(j=0;j<16;j=j+1)begin bp=((aa%7000000)/8)*16+j;xx=(bp/3)%1280;yy=bp/3840;ch=bp%3;p=pixel(xx,yy);word_at[127-8*j-:8]=p>>(16-8*ch);end end endfunction
integer xx,yy,j;reg [23:0] want;reg [1:0] wantmask;integer expected_cycles;
always @(negedge dc)begin
 cycles=cycles+1;ready=cycles%7!=0 && cycles%19!=0;valid=0;
 if(head<tail && due[head]<=cycles)begin valid=1;data=word_at(queue[head]);head=head+1;end
end
always @(posedge dc)if(rst)begin
 if(rd)begin queue[tail]=addr;due[tail]=cycles+31;tail=tail+1;end
 if(dut.state==6 || dut.state==7 || dut.state==8 || dut.state==9 || dut.state==4)rowcycles=rowcycles+1;
 if(dut.state==4 && !dut.pair_index[0])begin
  for(j=0;j<4;j=j+1)begin xx=dut.pair_index*2+j;yy=dut.job_y;
   want=pixel(rotate?1279-xx:xx,rotate?719-yy:yy);
   if(dut.pixel_quad[95-24*j-:24]!==want)$fatal(1,"RGB row%0d x%0d got%h expected%h",yy,xx,dut.pixel_quad[95-24*j-:24],want);
   pixels=pixels+1;end end
 if(dut.state==4 && dut.pair_index==639)begin
  if(rowcycles!=expected_cycles)$fatal(1,"row cycles got%0d expected%0d",rowcycles,expected_cycles);
  rowcycles=0;rows=rows+1;end
 if(dut.fv && dut.fy>=48 && dut.fy<=671)begin
  for(j=0;j<4;j=j+1)begin xx=dut.fx+j;yy=dut.fy;wantmask=supported(rotate?1279-xx:xx,rotate?719-yy:yy);
   if(dut.mask_word[2*j+:2]!==wantmask)$fatal(1,"mask row%0d x%0d got%b expected%b",yy,xx,dut.mask_word[2*j+:2],wantmask);masks=masks+1;end
 end
end
initial begin if(!$value$plusargs("ROTATE=%d",rotate))rotate=0;if(!$value$plusargs("CYCLES=%d",expected_cycles))expected_cycles=644;
 repeat(8)@(negedge pc);rst=1;repeat(8)@(negedge pc);commit=1;@(negedge pc);commit=0;
 repeat(8000)@(negedge dc);
 if(rows<3 || pixels<3840 || masks<1280)$fatal(1,"coverage rows%0d pixels%0d masks%0d",rows,pixels,masks);
 $display("REFINED_PREFETCH_PASS rotation%0d rows%0d RGB%0d masks%0d class/load cycles%0d",rotate,rows,pixels,masks,expected_cycles);$finish;end
endmodule'''
other=[R/'rtl/color_regions'/f'{n}.v' for n in ('stable_model_lane','stable_filter4','refined_reset_bridge','refined_zoom_geometry')]+[R/'rtl/04_tracking/target_mailbox.v']
for before in (True,False):
 for rot in (0,1):run(f'prefetch_{"before" if before else "after"}_{rot}',src.replace('EXTRA_PORTS','' if before else ",1'b1,,,,32'd0,1'b0"),[baseline if before else R/'rtl/color_regions/stable_line_reader.v',*other],args=[f'+ROTATE={rot}',f'+CYCLES={960 if before else 644}'])
