"""Generate the small functional footer, glyph ROM, and source-isolated wrappers."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]

def assets():
    result={};chars=' '+''.join(dict.fromkeys('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ:+-/原图色彩高亮灰度二值模式倍率配红蓝黄紫候选状态待命搜索中区域多个拥挤按键冲突视频未就绪无新帧更多判取样隐藏'))
    chars=''.join(dict.fromkeys(chars));assert len(chars)<=128
    ids={s:i for i,s in enumerate(chars)}
    def g(c):return str(ids[c])
    def literal(row,start,text):return '\n'.join(f"{start+i}:footer={g(ch)};" for i,ch in enumerate(text))
    cases=[{},{}]
    def put(row,start,text):
        for i,c in enumerate(text):cases[row][start+i]=g(c)
    def field(row,start,signal,strings):
        for i in range(max(map(len,strings))):
            cases[row][start+i]=':'.join(f'{signal}=={n}?{g(s[i] if i<len(s) else " ")}' for n,s in enumerate(strings))+':0'
    put(0,0,'模式:');field(0,3,'I_mode',['原图','色彩高亮','灰度','色彩二值'])
    put(0,8,'倍率:');cases[0][11]=f'I_zoom==0?{g("1")}:I_zoom==1?{g("2")}:{g("4")}'
    put(0,14,'配色:');field(0,17,'I_pair',['红蓝','黄紫'])
    put(0,21,'候选 A:');cases[0][26]=f'{g("0")}+na';cases[0][27]=f'I_detection_valid && I_meta[319]?{g("+")}:0'
    put(0,29,'B:');cases[0][31]=f'{g("0")}+nb';cases[0][32]=f'I_detection_valid && I_meta[383]?{g("+")}:0'
    put(0,35,'R1-01')
    put(1,0,'状态:');field(1,3,'I_state',['待命','搜索中','区域','多个区域','区域拥挤','按键冲突','视频未就绪','无新帧'])
    for i,c in enumerate('更多区域待判'):cases[1][11+i]=f'I_detection_valid && (I_meta[412] || I_meta[411])?{g(c)}:0'
    put(1,19,'RGB:')
    for start,sig in [(23,'red_bcd'),(27,'green_bcd'),(31,'blue_bcd')]:
        for i in range(3):cases[1][start+i]=f'I_mode==1 && I_show && I_sample_valid?{g("0")}+{sig}[{11-4*i}-:4]:{g("-")}'
    cases[1][26]=g('/');cases[1][30]=g('/')
    code='if(!row)begin case(col)\n'+'\n'.join(f'{i}:footer={v};' for i,v in sorted(cases[0].items()))+'\nendcase end else begin case(col)\n'+'\n'.join(f'{i}:footer={v};' for i,v in sorted(cases[1].items()))+'\nendcase end'
    s=(R/'scripts/color_regions_osd.v.txt').read_text(encoding='utf-8').replace('@FOOTER@',code)
    for key,ch in [('YELLOW','黄'),('RED','红'),('BLUE','蓝'),('PURPLE','紫'),('COLOR','色'),('A','A'),('B','B'),('ONE','1'),('TWO','2')]:s=s.replace('@'+key+'@',g(ch))
    result['rtl/color_regions/regions_osd.v']=s
    font=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',16);rows=[]
    for ch in chars:
        im=Image.new('1',(16,16));draw=ImageDraw.Draw(im);draw.text((0,-1),ch,font=font,fill=1)
        rows.extend(sum(int(im.getpixel((x,y)))<<(15-x) for x in range(16)) for y in range(16))
    rows += [0]*(2048-len(rows))
    result['rtl/color_regions/regions_glyph_rom.v']='module regions_glyph_rom(input wire clk,input wire [10:0] addr,output reg [15:0] data);\n(* ram_style="block" *) reg [15:0] rom[0:2047];\ninitial begin\n'+''.join(f"rom[{i}]=16'h{v:04x};\n" for i,v in enumerate(rows))+'end\nalways @(posedge clk)data<=rom[addr];\nendmodule\n'
    return result
