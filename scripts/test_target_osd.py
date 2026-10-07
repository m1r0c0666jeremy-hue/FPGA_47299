"""Compare every RTL OSD pixel against an independent raster composition.
Font atlas is a generated asset; placement, clipping, colors and geometry are
reconstructed here without reading the OSD Verilog implementation.
"""
from pathlib import Path
import os,json,subprocess,re
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageDraw
import numpy as np
r=Path(__file__).resolve().parents[1];out=r/'build/sim/target_lock/osd';out.mkdir(parents=True,exist_ok=True)
preview=r/'reports/target_preview';preview.mkdir(exist_ok=True)
iv=r/'tools/iverilog/ucrt64/bin/iverilog.exe';vvp=iv.with_name('vvp.exe');env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
cmd=[iv,'-g2012','-s','tb_target_osd','-o',out/'osd.vvp','sim/tb_target_osd.sv','rtl/09_osd_ui/target_osd.v','rtl/09_osd_ui/target_glyph_rom.v','rtl/09_osd_ui/scaling_logo_rom.v']
c=subprocess.run(list(map(str,cmd)),cwd=r,env=env,capture_output=True,text=True);assert c.returncode==0,c.stdout+c.stderr
manifest=json.loads((r/'reports/target_generation_manifest.json').read_text(encoding='utf-8'))
atlas=Image.open(preview/'glyphs.png').convert('RGB');chars=manifest['characters']
masks={ch:atlas.crop(((i%16)*24,(i//16)*24,(i%16+1)*24,(i//16+1)*24)).convert('L').point(lambda x:255 if x>100 else 0) for i,ch in enumerate(chars)}
logo=np.zeros(8192,np.uint8)
for i,val in re.findall(r"mem\[(\d+)\]=2'h([0-9a-f]+)",(r/'rtl/09_osd_ui/scaling_logo_rom.v').read_text()):logo[int(i)]=int(val,16)
def pack(fields):
 n=0
 for low,width,val in fields:n|=(val&((1<<width)-1))<<low
 return n
cases=[]
for st in range(7):cases.append(dict(state=st,show=1,tip=int(st==2),video=int(st!=6),zoom=0,x0=0,y0=48,mode=st%4,A=(700,360),B=(600,360),T=(750,360)))
cases += [dict(cases[2],show=0),dict(cases[2],zoom=2,x0=0,y0=0,A=(3,3),B=(60,30),T=(15,15)),dict(cases[2],zoom=1,x0=640,y0=408,A=(1274,715),B=(1220,670),T=(1279,719))]
logs=[]
def work(item):
 i,c=item;A,B,T=c['A'],c['B'],c['T'];fields=[(32,1,c['tip']),(37,11,A[0]),(48,10,A[1]),(58,11,B[0]),(69,10,B[1]),(79,11,T[0]),(90,10,T[1])]
 boxes=[]
 for j,P in enumerate((A,B)):
  box=(max(0,P[0]-10),min(1279,P[0]+10),max(0,P[1]-8),min(719,P[1]+8));boxes.append(box)
  for low,width,val in zip(([100,111,122,132] if j==0 else [142,153,164,174]),[11,11,10,10],box):fields.append((low,width,val))
 cfg=out/f'{i}.txt';cfg.write_text(' '.join(str(c[key]) for key in ['show','tip','state','video','x0','y0','zoom','mode'])+f' {pack(fields):064x}\n')
 ppm=out/f'{i}.ppm';p=subprocess.run([str(vvp),str(out/'osd.vvp'),f'+CONFIG={cfg}',f'+OUT={ppm}'],cwd=r,env=env,capture_output=True,text=True,timeout=500)
 assert p.returncode==0,p.stdout+p.stderr
 actual=np.array(Image.open(ppm).convert('RGB'));expected=np.empty((720,1280,3),np.uint8);expected[:]=[32,48,64] if c['video'] else [0,0,0]
 expected[624:]=[16,32,48];expected[632:712,1024:1264]=255
 yy,xx=np.indices((624,1280));scale=1<<c['zoom'];origin=(c['x0'],c['y0'])
 def center(P):return ((P[0]-origin[0])*scale+scale//2,(P[1]-origin[1])*scale+scale//2)
 def screen_box(b):return ((b[0]-origin[0])*scale,(b[1]+1-origin[0])*scale-1,(b[2]-origin[1])*scale,(b[3]+1-origin[1])*scale-1)
 sb=list(map(screen_box,boxes));labels=[]
 if c['show'] and c['tip'] and c['video']:
  redblue=[]
  for box,P in zip(sb,(A,B)):
   x1,x2,y1,y2=box;cx,cy=center(P)
   edge=(xx>=x1)&(xx<=x2)&(yy>=y1)&(yy<=y2)&((xx<x1+2)|(xx>x2-2)|(yy<y1+2)|(yy>y2-2))
   redblue.append(edge|((abs(xx-cx)<=2)&(abs(yy-cy)<=2)))
  expected[:624][redblue[1]]=[48,128,255];expected[:624][redblue[0]]=[255,48,48]
  tx,ty=center(T);dx,dy=abs(xx-tx),abs(yy-ty)
  outline=((dx>=2)&(dx<=13)&(dy<=2))|((dy>=2)&(dy<=13)&(dx<=2))
  cross=((dx>=3)&(dx<=12)&(dy<=1))|((dy>=3)&(dy<=12)&(dx<=1))
  expected[:624][outline]=0;expected[:624][cross]=[255,255,0]
  for ch,b,col in [('A',sb[0],(255,80,80)),('B',sb[1],(64,160,255))]:
   x1,x2,y1,y2=b
   if x2>=0 and x1<1280 and y2>=0 and y1<624:labels.append((ch,max(0,min(1255,x1)),max(0,min(598,y1-26)),col))
  if 0<=tx<1280 and 0<=ty<624:labels.append(('T',0 if tx<0 else 1255 if tx>1238 else tx+17,max(0,min(598,ty-12)),(255,255,0)))
 im=Image.fromarray(expected)
 def text(s,x,y,color=(255,255,255),blocked=None):
  for j,ch in enumerate(s):
   mask=masks[ch].copy()
   if blocked is not None:
    ma=np.array(mask);ma[blocked[y:y+24,x+j*24:x+(j+1)*24]]=0;mask=Image.fromarray(ma)
   im.paste(color,(x+j*24,y,x+(j+1)*24,y+24),mask)
 blocked=np.zeros((720,1280),bool)
 for ch,x,y,col in labels:
  text(ch,x,y,col,blocked);blocked[y:y+24,x:x+24]=True
 text('模式：',16,628);text(['原图','边缘','灰度','二值化'][c['mode']],88,628)
 text('倍率：',208,628);text(str(scale),280,628);text('状态：',352,628)
 text(['待命','搜索中','锁定跟踪','失锁','已停止','按键冲突','视频未就绪'][c['state']],424,628)
 text('红A前',16,658,(255,80,80));text('蓝B后',112,658,(64,160,255));text('估算尖端：(',208,658)
 text(f'{T[0]:04d},{T[1]:04d})' if c['tip'] else '----,----)',352,658)
 cfgvals=manifest['config'];text(f'L={cfgvals["L_mm"]:04d}mm D={cfgvals["D_mm"]:04d}mm K={manifest["K_display"]} KEY3启停',16,688)
 text('安路科技',1144,660,(28,44,78))
 expected=np.array(im)
 for n,v in enumerate(logo[:96*62]):
  if v:expected[641+n//96,1032+n%96]=[237,27,35] if v==2 else [28,44,78]
 diff=np.any(actual!=expected,axis=2)
 if diff.any():
  y,x=np.argwhere(diff)[0];Image.fromarray(diff.astype(np.uint8)*255).save(out/f'{i}_diff.png')
  raise AssertionError(f'OSD case {i}, {diff.sum()} pixels differ; first ({x},{y}) actual {actual[y,x]} expected {expected[y,x]}')
 Image.fromarray(actual).save(preview/f'osd_{i:02d}.png')
 return f'PASS OSD case {i}: state={c["state"]} show={c["show"]} zoom={scale} pixels=921600'
with ThreadPoolExecutor(max_workers=3) as pool:
 for textout in pool.map(work,enumerate(cases)):
  logs.append(textout);print(textout,flush=True);(r/'reports/target_osd_simulation.log').write_text('\n'.join(logs)+'\n',encoding='utf-8')
(preview/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('TARGET_OSD_TESTS_PASSED')
