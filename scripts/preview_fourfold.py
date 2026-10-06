"""Comparison from actual RTL captures and the independent MAIN nearest mapping."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
r=Path(__file__).resolve().parents[1];captures=r/'build/sim/improve_fourfold_scale';out=r/'reports/fourfold_preview';out.mkdir(exist_ok=True)
yy,xx=np.indices((720,1280));src=np.zeros((720,1280,3),dtype=np.uint8)
white=((yy<200)&(((xx%32)==8)|((xx%32)==10)))|((yy>=200)&(yy<350)&((xx%160)==(yy%160)))|((yy>=350)&(yy<500)&((((xx//3)^(yy//3))&1)!=0))|((yy>=500)&(yy<600)&(xx==641)&(yy==550))
src[white]=255
src[600:,:,0]=(xx[600:]%256).astype(np.uint8);src[600:,:,1]=(yy[600:]%256).astype(np.uint8);src[600:,:,2]=((xx[600:]+yy[600:])%256).astype(np.uint8)
Image.fromarray(src).save(out/'source_chart.png')
font=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',22)
small=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',18)
canvas=Image.new('RGB',(1340,1010),'#eef2f5');d=ImageDraw.Draw(canvas)
d.text((24,16),'4倍放大对照：左为同源最近邻参考，右为实际 RTL 双线性输出',font=font,fill='#142332')
d.text((24,48),'合成测试图，不是相机实拍。局部截图再等比例放大以便检查；不增加真实采样细节。',font=small,fill='#364959')
rows=[(22,30,'细线与窄间隙',(0,0,320,80)),(23,200,'斜线',(80,0,400,80)),(24,350,'棋盘格',(0,0,320,80)),(25,480,'单像素点',(616,254,680,298))]
manifest=[]
for row,(i,y0,title,box) in enumerate(rows):
 im=Image.open(captures/f'preview_{i}.png').convert('RGB');arr=np.array(im)
 sy=y0+np.arange(624)//4;sx=480+np.arange(1280)//4
 nearest=src[sy[:,None],sx[None,:]].copy()
 # Preserve the identical OSD/crosshair only for the full-screen reference.
 near_full=arr.copy();near_full[:624]=nearest
 y,x=np.indices((624,1280));dx=abs(x-640);dy=abs(y-312)
 mask=((dx>=2)&(dx<=13)&(dy<=2))|((dy>=2)&(dy<=13)&(dx<=2))
 near_full[:624][mask]=arr[:624][mask]
 Image.fromarray(near_full).save(out/f'{i}_nearest_reference.png');im.save(out/f'{i}_bilinear_rtl.png')
 top=90+row*228;d.text((24,top),title,font=font,fill='#142332')
 a=Image.fromarray(near_full).crop(box);b=im.crop(box)
 size=(640,160) if row<3 else (256,176)
 a=a.resize(size,Image.Resampling.NEAREST);b=b.resize(size,Image.Resampling.NEAREST)
 canvas.paste(a,(24,top+34));canvas.paste(b,(690,top+34))
 manifest.append({'case':i,'source_y':y0,'crop':box,'rtl_capture_sha256':hashlib.sha256((captures/f'preview_{i}.png').read_bytes()).hexdigest()})
canvas.save(out/'comparison.png');(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(out/'comparison.png')
