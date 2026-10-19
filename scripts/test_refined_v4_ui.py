"""Independent full-footer oracle for v4 states, numbers and transparent symbol."""
from refined_testlib import R,run
from PIL import Image,ImageDraw,ImageFont
import json,re
O=R/'build/sim/refined_v4_ui';O.mkdir(parents=True,exist_ok=True)
m=json.loads((R/'assets/osd/anlogic/refined_ui_manifest.json').read_text(encoding='utf-8'));size=m['font_size'];assert size==16 and m['footer_columns']==64
font=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',size)
original=[0]*8192
for a,v in re.findall(r"mem\[(\d+)\]=2'h([0-9a-f]);",(R/'rtl/09_osd_ui/scaling_logo_rom.v').read_text()):original[int(a)]=int(v,16)
meta=0
for lo,w,v in [(32,1,1),(33,4,3),(184,20,345),(204,20,678),(245,1,1),(246,1,1),(247,1,1),(255,1,1),(256,20,12345),(276,20,23456),(296,20,10000),(316,20,20000),(336,3,4),(339,3,3),(342,4,5),(346,4,5),(350,7,80),(357,7,95),(364,2,1),(366,2,2),(368,2,2),(378,2,3),(380,4,2),(384,8,67),(392,8,45),(400,8,123),(413,3,4),(443,2,1),(445,8,16),(453,8,32),(461,9,30),(470,9,345),(507,2,1),(509,8,16),(517,8,32),(525,9,255),(534,9,195),(544,16,0xaf),(569,12,1024),(581,12,1024),(604,1,1),(607,18,173893),(625,15,7),(721,2,1),(723,12,2048),(735,9,256),(744,12,1800),(756,9,216)]:meta|=v<<lo
cases=[('overview',0,0,['色彩高亮 2X   红蓝 180 状态:跟踪中      材料已学习','板内延迟 0012.3ms 落后 002帧 F:12345678 V:00AF']),
('overview_diag1_ignored',1,0,['色彩高亮 2X   红蓝 180 状态:跟踪中      材料已学习','板内延迟 0012.3ms 落后 002帧 F:12345678 V:00AF']),
('overview_diag2_ignored',2,0,['色彩高亮 2X   红蓝 180 状态:跟踪中      材料已学习','板内延迟 0012.3ms 落后 002帧 F:12345678 V:00AF']),
('overview_diag3_ignored',3,0,['色彩高亮 2X   红蓝 180 状态:跟踪中      材料已学习','板内延迟 0012.3ms 落后 002帧 F:12345678 V:00AF'])]
helptext=['','中央白纸 KEY3采样 KEY2取消','移走双色标记 绿框对准误检物 KEY3采样 KEY2取消','A近尖端色对准中央 KEY3采样 KEY2取消','B后方色对准中央 KEY3采样 KEY2取消']
for p,label in enumerate(['','白纸校准','空背景校准','A色校准','B色校准']):
 if p:cases.append((f'cal{p}',2,p<<5,[f'校准:{label:<9} E00 F:12345678 V:00AF',helptext[p]]))
cases += [('busy',0,0x50,['校准:采样处理中     E00 F:12345678 V:00AF','8帧采样或串行回放 请保持画面 KEY2取消']),('fail',1,0x66,['校准:采样失败      E06 F:12345678 V:00AF','背景不可分 KEY3重采 KEY2取消']),('insufficient',3,0x6c,['校准:采样失败      E0C F:12345678 V:00AF','有效样本不足 KEY3重采 KEY2取消'])]
palette=[0x101824,0x1c2c4e,0xed1b23,0xe0e8f4]
for n,(name,diag,cal,lines) in enumerate(cases):
 im=Image.new('RGB',(1280,96),(16,24,36))
 for row,line in enumerate(lines):
  assert len(line)<=64
  for column,ch in enumerate(line):
   g=Image.new('1',(size,size));ImageDraw.Draw(g).text((0,-max(1,size//16)),ch,font=font,fill=1)
   for y in range(size):
    for x in range(size):
     if g.getpixel((x,y)):im.putpixel((16+size*column+x,8+(32-size)//2+44*row+y),(240,244,255))
 for yy in range(64):
  for xx in range(98):
   def colour(x,y):return original[y*96+x] if 0<=x<96 and 0<=y<62 else 0
   value=colour(xx-1,yy-1)
   if not value and any(colour(xx-1+dx,yy-1+dy) for dx in (-1,0,1) for dy in (-1,0,1)):value=3
   rgb=palette[value];im.putpixel((1167+xx,16+yy),(rgb>>16,(rgb>>8)&255,rgb&255))
 data=im.tobytes();(O/f'{n}.hex').write_text(''.join(data[i:i+3].hex()+'\n' for i in range(0,len(data),3)),encoding='ascii')
 if n<4:im.save(R/f'reports/refined/footer_v4_{name}.png')
ddr=644|32<<18|45<<36|240<<54|240<<63|4<<72
pixel=2|1279<<20|623<<31|719<<41|0x89abcdef<<61
src=f'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,de=0;reg [767:0] meta=768'h{meta:0192x};reg [1:0] diag=0;
wire ovs,ohs,ode;wire [23:0] rgb;
refined_osd dut(clk,rst,1'b0,1'b0,de,24'h123456,meta,11'd320,10'd204,3'd2,2'd1,3'd2,1'b1,1'b1,1'b1,1'b0,1'b1,1'b1,ovs,ohs,ode,rgb,1'b1,diag,32'h12345678,1'b0,
1'b1,32'd12345,32'd2,128'h{ddr:032x},128'h{pixel:032x},39'h{(4<<34|3<<16):010x},18'h{(2<<9|1<<7|90):05x});
reg [23:0] expected[0:122879];integer c,x,y,n,outn;
always @(posedge clk)begin #1;if(ode && dut.y>=624 && !(dut.y==624 && dut.x<2))begin
if(rgb!==expected[outn])begin $display("FORMAT state%0d ready%b",dut.format_state,dut.footer_ready);
$fatal(1,"footer case%0d xy%0d/%0d got%h expected%h",c,outn%1280,624+outn/1280,rgb,expected[outn]);end outn=outn+1;end end
task frame(input integer d,cal);begin
@(negedge clk);de=0;rst=0;repeat(3)@(negedge clk);rst=1;diag=d;meta[567:560]=cal;
@(negedge clk);dut.y=620;dut.x=0;outn=0;
for(y=620;y<720;y=y+1)for(x=0;x<1280;x=x+1)begin @(negedge clk);de=1;end
@(negedge clk);de=0;repeat(4)@(negedge clk);if(outn!=122880)$fatal(1,"footer count %0d",outn);end endtask
initial begin
'''
for n,(name,diag,cal,lines) in enumerate(cases):src+=f'c={n};$readmemh("{(O/f"{n}.hex").as_posix()}",expected);frame({diag},{cal});$display("V4_UI_CASE_PASS {name}");\n'
src+='$display("REFINED_V4_UI_PASS 11 states complete footer rows, sole overview ignores diagnostic selector, latency/model/calibration, transparent original colours and outline");$finish;end endmodule'
run('refined_v4_ui_pixels',src,[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_osd','stable_glyph_rom','stable_footer_glyph_rom','refined_footer_program_rom','stable_footer_text_rom','refined_logo_rom','refined_overlay_geometry')])
