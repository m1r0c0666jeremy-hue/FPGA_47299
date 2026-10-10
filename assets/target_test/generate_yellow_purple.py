"""Create a dimensioned A4 marker target; requires Pillow. No RTL changes."""
from pathlib import Path
from xml.sax.saxutils import escape
import json
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
cfg = json.loads((ROOT / 'rtl/03_tool_detection/target_config.json').read_text())
L, D = cfg['L_mm'], cfg['D_mm']
assert L > 0 and D >= 0 and L + D < 220
DPI = 300
S = DPI / 25.4
im = Image.new('RGB', (round(297*S), round(210*S)), 'white')
draw = ImageDraw.Draw(im)
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">',
       '<rect width="297" height="210" fill="white"/>']

def line(x1, y1, x2, y2, width=.25):
    draw.line((round(x1*S),round(y1*S),round(x2*S),round(y2*S)), fill='black', width=max(1,round(width*S)))
    svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="{width}"/>')

def text(x, y, value, size=4, center=True):
    font = ImageFont.truetype('C:/Windows/Fonts/simhei.ttf', round(size*S))
    draw.text((round(x*S), round(y*S)), value, font=font, fill='black', anchor='mm' if center else 'lm')
    svg.append(f'<text x="{x}" y="{y}" text-anchor="{"middle" if center else "start"}" dominant-baseline="central" font-family="SimHei,Microsoft YaHei,sans-serif" font-size="{size}" fill="black">{escape(value)}</text>')

def circle(x, y, r, color):
    draw.ellipse(tuple(round(v*S) for v in (x-r,y-r,x+r,y+r)), fill=color)
    svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')

def dimension(x1, x2, y, label):
    line(x1,y,x2,y)
    for x in (x1,x2): line(x,y-2,x,y+2)
    text((x1+x2)/2,y+5,label,3.6)

b = (297-L-D)/2
a = b+L
t = a+D
y = 97
text(148.5,24,'黄紫双色锁定测试图',7)
text(148.5,36,'紫色后标记 B  →  黄色前标记 A  →  尖端参考 T',4)
text(148.5,46,f'L = {L} mm     D = {D} mm     K = {D/L:.3f}     色块直径 10 mm',3.8)

# Solid color disks: no letters or crosshairs inside the detection regions.
circle(b,y,5,'#C020E0')
circle(a,y,5,'#FFFF00')
line(t-2.5,y,t+2.5,y,.4)
line(t,y-2.5,t,y+2.5,.4)
text(b,109,'紫色 B',3.6)
text(a,109,'黄色 A',3.6)
text(t,109,'参考 T',3.6)
for x in (b,a,t): line(x,116,x,126,.15)
dimension(b,a,124,f'L = {L} mm')
dimension(a,t,124,f'D = {D} mm')

text(148.5,149,'A4 横向，按 100%／实际大小打印；关闭“适应页面”。',3.6)
text(148.5,158,'贴在同一块硬卡片上整体移动；SW3 拨至 1（下），短按 KEY3 开始。',3.5)
text(148.5,167,'锁定后比较黄色准心与黑色 T 中心；先在无黄紫干扰的背景测试。',3.5)
dimension(123.5,173.5,183,'打印后用尺核对：50 mm')
text(148.5,199,'打印颜色会受纸张、墨水和光照影响；本图不代表实物识别已经验收。',3)

svg.append('</svg>')
(OUT/'yellow_purple_A4.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8')
im.save(OUT/'yellow_purple_A4_300dpi.png',dpi=(DPI,DPI))
preview=im.copy()
preview.thumbnail((1485,1050),Image.Resampling.LANCZOS)
preview.save(OUT/'yellow_purple_preview.png')
assert im.getpixel((round(b*S),round(y*S))) == (192,32,224)
assert im.getpixel((round(a*S),round(y*S))) == (255,255,0)
print(f'Created A4 SVG and PNG: L={L}mm D={D}mm; {im.width}x{im.height}px at {DPI} DPI')
