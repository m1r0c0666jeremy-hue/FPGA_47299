"""Independent footer text/pixel oracle, official symbol and source overlays."""
from refined_testlib import R,run
O=R/"build/sim/refined_ui";O.mkdir(parents=True,exist_ok=True)
from PIL import Image,ImageDraw,ImageFont
import json,re
manifest=json.loads((R/'assets/osd/anlogic/refined_ui_manifest.json').read_text(encoding='utf-8'))
assert manifest['font_size']==24 and manifest['longest_line']*24<=1120
font=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',24)
logo=[0]*8192
for a,v in re.findall(r"mem\[(\d+)\]=2'h([0-9a-f]);",(R/'rtl/09_osd_ui/scaling_logo_rom.v').read_text()):logo[int(a)]=int(v,16)
palette=[0x101824,0x1c2c4e,0xed1b23,0xe0e8f4]
cases=[('overview',['色彩高亮 2  X 红蓝 180 状态:跟踪中      RGB:123/045/067','F:12345678 V:00AF A:000345/080 B:000678/095'],0,0),
 ('counts',['A012345>010000 N4 Q080 S1 F5','B023456>020000 N3 Q095 S2 F5 P2 R00 C3 L02'],1,0),
 ('model',['A H345/030 M032 D016 S4/16 R1024 B1024','B H195/255 M032 D016 S4/16 T173893 Z00007'],2,0)]
helptext=['','中央白纸 KEY3采样 KEY2取消','移走工具 保持背景 KEY3采样 KEY2取消','A近尖端色对准中央 KEY3采样 KEY2取消','B后方色对准中央 KEY3采样 KEY2取消']
states=['','白纸校准','空背景校准','A色校准','B色校准']
for p in range(1,5):cases.append((f'cal{p}',[f'校准:{states[p]:<9} E00 F:12345678 V:00AF',helptext[p]],2,p<<5))
cases += [('busy',['校准:采样处理中     E00 F:12345678 V:00AF','8帧采样或串行回放 请保持画面 KEY2取消'],0,0x50),
          ('inseparable',['校准:采样失败      E06 F:12345678 V:00AF','背景不可分 KEY3重采 KEY2取消'],1,0x66)]
def expected(lines):
 im=Image.new('RGB',(1280,96),(16,24,36));d=ImageDraw.Draw(im);
 for row,text in enumerate(lines):
  assert len(text)<=46,(text,len(text))
  for col,ch in enumerate(text):
   g=Image.new('1',(24,24));ImageDraw.Draw(g).text((0,-1),ch,font=font,fill=1)
   for yy in range(24):
    for xx in range(24):
     if g.getpixel((xx,yy)):im.putpixel((16+24*col+xx,12+44*row+yy),(240,244,255))
 for yy in range(64):
  for xx in range(98):
   def col(x,y):return logo[y*96+x] if 0<=x<96 and 0<=y<62 else 0
   v=col(xx-1,yy-1)
   if not v and any(col(xx-1+dx,yy-1+dy) for dx in (-1,0,1) for dy in (-1,0,1)):v=3
   rgb=palette[v];im.putpixel((1167+xx,16+yy),((rgb>>16)&255,(rgb>>8)&255,rgb&255))
 return im
for i,(_,lines,_,_) in enumerate(cases):
 im=expected(lines);data=im.tobytes();(O/f'footer_{i}.hex').write_text(''.join(data[j:j+3].hex()+'\n' for j in range(0,len(data),3)),encoding='ascii')
 if i==0:im.save(R/'reports/refined/footer_preview.png')
meta=0
def put(lo,width,v):
 global meta;meta|=v<<lo
for lo,w,v in [(32,1,1),(33,4,3),(184,20,345),(204,20,678),(245,1,1),(246,1,1),(247,1,1),(255,1,1),(256,20,12345),(276,20,23456),(296,20,10000),(316,20,20000),(336,3,4),(339,3,3),(342,4,5),(346,4,5),(350,7,80),(357,7,95),(364,2,1),(366,2,2),(368,2,2),(378,2,3),(380,4,2),(384,8,67),(392,8,45),(400,8,123),(413,3,3),(416+27,2,1),(416+29,8,16),(416+37,8,32),(416+45,9,30),(416+54,9,345),(480+27,2,1),(480+29,8,16),(480+37,8,32),(480+45,9,255),(480+54,9,195),(544,16,0xaf),(569,12,1024),(581,12,1024),(604,1,1),(607,18,173893),(625,15,7)]:put(lo,w,v)
src=f'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,vs=0,hs=0,de=0;reg [639:0] meta=640'h{meta:0160x};reg [1:0] diag=0;reg rotate=1;
wire ovs,ohs,ode;wire [23:0] rgb;
stable_osd dut(clk,rst,vs,hs,de,24'h123456,meta,11'd320,10'd204,3'd2,2'd1,3'd2,1'b1,1'b1,1'b1,1'b0,1'b1,1'b1,ovs,ohs,ode,rgb,rotate,diag,32'h12345678,1'b0);
reg [23:0] expected[0:122879];integer c,x,y,n=0,outn=0;reg [1023:0] path;
always @(posedge clk)begin #1;if(ode && y>=624)begin
if(rgb!==expected[outn])begin
for(n=0;n<46;n=n+1)$display("CHAR %0d %0d",n,dut.characters[n]);
$fatal(1,"footer c%0d pixel%0d xy%0d/%0d got%h expected%h",c,outn,outn%1280,624+outn/1280,rgb,expected[outn]);end outn=outn+1;end end
task frame(input integer d,cal);begin
@(negedge clk);de=0;rst=0;repeat(3)@(negedge clk);rst=1;diag=d;meta[567:560]=cal;rotate=1;
@(negedge clk);dut.y=620;dut.x=0;outn=0;
for(y=620;y<720;y=y+1)for(x=0;x<1280;x=x+1)begin
@(negedge clk);de=1;end
@(negedge clk);de=0;repeat(4)@(negedge clk);if(outn!=122880)$fatal(1,"footer count %d",outn);end endtask
initial begin
'''
for i,(name,lines,diag,cal) in enumerate(cases):src+=f'c={i};$readmemh("{(O/f"footer_{i}.hex").as_posix()}",expected);frame({diag},{cal});$display("RING_UI_CASE_PASS {name}");\n'
src+='''$display("RING_UI_PASS all 96 footer rows: manual pages, 4 calibration steps, busy/error text, official symbol colours/transparency, decimal/hex and 2-clock sync");$finish;end endmodule'''
# Count output rows from the renderer's one-cycle delayed input, rather than
# the producer loop variable, which advances before the last delayed pixel.
src=src.replace('if(ode && y>=624)', 'if(ode && dut.y>=624 && !(dut.y==624 && dut.x<2))')
run('transparent_ui_pixels',src,[R/f'rtl/color_regions/{n}.v' for n in ('stable_osd','stable_glyph_rom','stable_footer_glyph_rom','stable_footer_program_rom','stable_footer_text_rom')]+[R/'rtl/color_regions/refined_logo_rom.v',R/'rtl/color_regions/refined_overlay_geometry.v'])
