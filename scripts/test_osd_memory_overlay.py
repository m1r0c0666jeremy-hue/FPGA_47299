"""Unchanged non-text image plus independent English labels at clipped edges."""
from refined_testlib import R,run
import json,zipfile,re
b=json.loads((R/'reports/refined/osd_memory_baseline.json').read_text())
out=R/'build/sim/osd_memory_overlay';out.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(R/b['archive']) as z:
    original=z.read('rtl/color_regions/refined_osd.v').decode().replace('module refined_osd(', 'module chinese_original(').replace('refined_footer_program_rom','chinese_program_rom')
    original_path=out/'chinese_original.v';original_path.write_text(original,encoding='utf-8')
    program=out/'chinese_program_rom.v';program.write_bytes(z.read('rtl/color_regions/refined_footer_program_rom.v').replace(b'refined_footer_program_rom',b'chinese_program_rom'))
    chars=json.loads(z.read('assets/osd/anlogic/refined_ui_manifest.json'))['characters']
    font={int(i):int(v,16) for i,v in re.findall(r"rom\[(\d+)\]=16'h([0-9a-f]+);",z.read('rtl/color_regions/stable_footer_glyph_rom.v').decode())}
labels=['RED A1','BLUE B1','YELLOW A1','PURPLE B1']
rows=[]
for label in labels:
    for i in range(9):rows.extend([(font[chars.index(label[i])*16+y]>>8) if i<len(label) else 0 for y in range(16)])
glyph=out/'label_bitmap.hex';glyph.write_text(''.join(f'{v:02x}\n' for v in rows),encoding='ascii')
src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,de=0,pair=0,rotate=0,commit=0;reg [767:0] meta=0;
wire [23:0] a,b;wire va,ha,da,vb,hb,db;
chinese_original original(clk,rst,1'b0,1'b0,de,24'h123456,meta,11'd0,10'd0,3'd0,2'd0,3'd2,1'b1,1'b1,1'b1,pair,1'b1,1'b1,va,ha,da,a,rotate,2'd0,32'h12345678,commit,1'b1,32'd12345,32'd2,128'd0,128'd0,39'd0,18'd0);
refined_osd candidate(clk,rst,1'b0,1'b0,de,24'h123456,meta,11'd0,10'd0,3'd0,2'd0,3'd2,1'b1,1'b1,1'b1,pair,1'b1,1'b1,vb,hb,db,b,rotate,2'd0,32'h12345678,commit,1'b1,32'd12345,32'd2,128'd0,128'd0,39'd0,18'd0);
reg [7:0] font[0:575];integer f,x,y,dx=0,dy=0,lastx,lasty,n=0,labels_checked=0,stable_checked=0;
integer sx0[0:1],sx1[0:1],sy0[0:1],sy1[0:1],bx0[0:1],bx1[0:1],by0[0:1],by1[0:1];
integer lx[0:1],oldlx[0:1],ly[0:1],width[0:1],kind[0:1];
integer j,px,py,charno;reg checking=0,prev=0,in_new,in_any;reg [23:0] expected;
always @(posedge clk)begin #1;
if(checking && prev && lasty<624)begin
if({va,ha,da}!=={vb,hb,db})$fatal(1,"overlay sync changed");
in_any=0;in_new=0;expected=24'h123456;
for(j=0;j<2;j=j+1)begin
if(lastx>=oldlx[j] && lastx<oldlx[j]+64 && lasty>=ly[j] && lasty<ly[j]+16)in_any=1;
if(lastx>=lx[j] && lastx<lx[j]+width[j] && lasty>=ly[j] && lasty<ly[j]+16)begin
in_any=1;in_new=1;px=lastx-lx[j];py=lasty-ly[j];charno=px/8;
expected=font[kind[j]*144+charno*16+py][7-px%8]?(j==0?(pair?24'hffff40:24'hff6060):(pair?24'he080ff:24'h6090ff)):24'h101824;end end
if(!in_any)begin if(a!==b)$fatal(1,"non-text image changed f%0d xy%0d/%0d got%h expected%h",f,lastx,lasty,b,a);stable_checked=stable_checked+1;end
if(in_new)begin if(b!==expected)$fatal(1,"English label f%0d xy%0d/%0d got%h expected%h",f,lastx,lasty,b,expected);labels_checked=labels_checked+1;end
n=n+1;end
lastx=dx;lasty=dy;prev=de;
end
initial begin $readmemh("GLYPH_FILE",font);
meta[255]=1;meta[247]=1;meta[245]=1;meta[246]=1;meta[36:33]=3;meta[415:413]=4;
repeat(3)@(negedge clk);rst=1;
for(f=0;f<8;f=f+1)begin
pair=f[0];rotate=f[1];
if(f<4)begin sx0[0]=1210;sx1[0]=1278;sy0[0]=602;sy1[0]=620;sx0[1]=0;sx1[1]=65;sy0[1]=0;sy1[1]=20;end
else begin sx0[0]=600;sx1[0]=640;sy0[0]=200;sy1[0]=240;sx0[1]=620;sx1[1]=660;sy0[1]=200;sy1[1]=240;end
meta[141:100]={10'(sy1[0]),10'(sy0[0]),11'(sx1[0]),11'(sx0[0])};
meta[183:142]={10'(sy1[1]),10'(sy0[1]),11'(sx1[1]),11'(sx0[1])};
for(j=0;j<2;j=j+1)begin
bx0[j]=rotate?1279-sx1[j]:sx0[j];bx1[j]=rotate?1279-sx0[j]:sx1[j];
by0[j]=rotate?623-sy1[j]:sy0[j];by1[j]=rotate?623-sy0[j]:sy1[j];
kind[j]=pair*2+j;width[j]=kind[j]==0?48:kind[j]==1?56:72;
lx[j]=bx0[j]<0?0:bx0[j]>1280-width[j]?1280-width[j]:bx0[j];
oldlx[j]=bx0[j]<0?0:bx0[j]>1216?1216:bx0[j];
ly[j]=by0[j]>=18?by0[j]-18:by1[j]+3;if(ly[j]>608)ly[j]=608;if(ly[j]<0)ly[j]=0;end
commit=1;repeat(40)@(negedge clk);commit=0;prev=0;checking=1;
for(y=0;y<624;y=y+1)for(x=0;x<1280;x=x+1)begin
@(negedge clk);de=1;dx=x;dy=y;original.x=x;original.y=y;candidate.x=x;candidate.y=y;end
@(negedge clk);de=0;repeat(3)@(negedge clk);checking=0;
end
$display("OSD_ENGLISH_OVERLAY_PASS %0d image pixels, %0d non-text equal, %0d independent label pixels; corners, overlap, pairs and orientations",n,stable_checked,labels_checked);$finish;
end endmodule'''.replace('GLYPH_FILE',glyph.as_posix())
mods=[original_path,program]+[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_osd','stable_glyph_rom','stable_footer_glyph_rom','stable_footer_text_rom','refined_english_font_rom','refined_english_text_rom','refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry')]
run('osd_english_overlay',src,mods,timeout=1800)
