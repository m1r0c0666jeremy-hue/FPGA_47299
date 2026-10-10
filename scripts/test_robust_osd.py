"""Compare every RTL OSD pixel against an independent raster composition.
Font atlas is a generated asset; placement, clipping, colors and geometry are
reconstructed here without reading the OSD Verilog implementation.
"""
from pathlib import Path
import os,json,subprocess,re
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageDraw
import numpy as np
r=Path(__file__).resolve().parents[1];out=r/'build/sim/robust/osd';out.mkdir(parents=True,exist_ok=True)
preview=r/'reports/robust_preview';preview.mkdir(exist_ok=True)
iv=r/'tools/iverilog/ucrt64/bin/iverilog.exe';vvp=iv.with_name('vvp.exe');env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
cmd=[iv,'-g2012','-s','tb_candidate_osd','-o',out/'osd.vvp','sim/tb_candidate_osd.sv','rtl/09_osd_ui/target_diagnostics.v','rtl/09_osd_ui/target_osd.v','rtl/09_osd_ui/target_glyph_rom.v','rtl/09_osd_ui/scaling_logo_rom.v']
c=subprocess.run(list(map(str,cmd)),cwd=r,env=env,capture_output=True,text=True);assert c.returncode==0,c.stdout+c.stderr
manifest=json.loads((r/'reports/target_generation_manifest.json').read_text(encoding='utf-8'))
atlas=Image.open(r/'reports/target_preview/glyphs.png').convert('RGB');chars=manifest['characters']
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
cases=[dict(c,pair=pair) for pair in range(2) for c in cases]
cases += [dict(cases[2],pair=p,mode=m,zoom=z,x0=0,y0=0,A=(100,65),B=(45,65),T=(128,65)) for p in range(2) for m in range(4) for z in range(3)]
cases += [dict(cases[2],pair=p,A=(px,py),B=(px,py),T=(px,py),x0=0,y0=0) for p in range(2) for px,py in [(0,0),(1279,623),(100,5),(300,600)]]
cases=[dict(c,detection=int(c['state'] in (1,2,3)),ca=int(c['state'] in (1,2,3)),cb=int(c['state'] in (1,2,3)),frameok=1,na=357,nb=357,fa=100,fb=100,reason=0) for c in cases]
for pair in (0,1):
 for patch in [dict(ca=1,cb=0,nb=0,fb=0,reason=2),dict(ca=0,cb=1,na=0,fa=0,reason=2),dict(ca=0,cb=0,na=0,nb=0,fa=0,fb=0,reason=2),dict(ca=0,na=1,reason=3),dict(ca=1,na=100,fa=0,reason=0),dict(reason=5),dict(reason=6),dict(frameok=0,ca=0,cb=0,reason=1),dict(detection=0,ca=0,cb=0),dict(na=921600,ca=1,nb=0,cb=0,fb=0,reason=2)]:
  cases.append(dict(cases[2],state=1,tip=0,pair=pair,**patch))
logs=[]
def work(item):
 i,c=item;A,B,T=c['A'],c['B'],c['T'];fields=[(255,1,c['detection']),(245,1,c['ca']),(246,1,c['cb']),(247,1,c['frameok']),(184,20,c['na']),(204,20,c['nb']),(224,7,c['fa']),(248,7,c['fb']),(33,4,c['reason']),(243,1,c['pair']),(32,1,c['tip']),(37,11,A[0]),(48,10,A[1]),(58,11,B[0]),(69,10,B[1]),(79,11,T[0]),(90,10,T[1])]
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
 if c['show'] and c['detection'] and c['video']:
  redblue=[]
  for j,(box,P) in enumerate(zip(sb,(A,B))):
   x1,x2,y1,y2=box;cx,cy=center(P)
   edge=(xx>=x1)&(xx<=x2)&(yy>=y1)&(yy<=y2)&((xx<x1+2)|(xx>x2-2)|(yy<y1+2)|(yy>y2-2))
   redblue.append((edge|((abs(xx-cx)<=2)&(abs(yy-cy)<=2))) & bool(c['frameok'] and c['ca' if j==0 else 'cb']))
  expected[:624][redblue[1]]=[192,80,255] if c["pair"] else [48,128,255];expected[:624][redblue[0]]=[255,255,0] if c["pair"] else [255,48,48]
  tx,ty=center(T);dx,dy=abs(xx-tx),abs(yy-ty)
  outline=((dx>=2)&(dx<=13)&(dy<=2))|((dy>=2)&(dy<=13)&(dx<=2))
  cross=((dx>=3)&(dx<=12)&(dy<=1))|((dy>=3)&(dy<=12)&(dx<=1))
  if c['tip']:expected[:624][outline]=0;expected[:624][cross]=[255,255,0]
  # Independent rectangle layout oracle: first valid candidate wins.
  def clamp(v,hi):return max(0,min(hi,v))
  def intersects(a,b):
   return a[0]<b[0]+b[2] and b[0]<a[0]+a[2] and a[1]<b[1]+b[3] and b[1]<a[1]+a[3]
  vis=[bool(c['frameok'] and c['ca' if j==0 else 'cb']) and b[1]>=0 and b[0]<1280 and b[3]>=0 and b[2]<624 for j,b in enumerate(sb)]
  tv=c['tip'] and 0<=tx<1280 and 0<=ty<624
  tr=(clamp(tx+17 if tx+137<=1280 else tx-137,1160),clamp(ty-24,494),120,48)
  a,b=sb
  ac=[(clamp(a[0],1136),clamp(y,518),144,24) for y in [a[2]-26 if a[2]>=26 else a[3]+3,a[3]+3]]
  ac += [(clamp(a[1]-143,1136),clamp(y,518),144,24) for y in [a[2]-26 if a[2]>=26 else a[3]+3,a[3]+3]]
  ar=next((q for q in ac if not(vis[0] and tv and intersects(q,tr))),None)
  fallback=ar is None;ar=ar or ac[-1]
  bc=[(clamp(b[0],1136),clamp(y,518),144,24) for y in [b[2]-26 if b[2]>=26 else b[3]+3,b[3]+3]]
  bc += [(clamp(x,1136),clamp(b[2],518),144,24) for x in [b[1]+3,b[0]-147]]
  br=next((q for q in bc if not vis[1] or not((tv and intersects(q,tr)) or (vis[0] and intersects(q,ar)))),None)
  fallback |= br is None;br=br or bc[-1]
  if fallback:tr=(8,8,120,48);ar=(8,60,144,24);br=(8,88,144,24)
  if tv:labels += [('十字准心T',tr[0],tr[1],(255,255,0),120,48),('估算尖端',tr[0],tr[1]+24,(255,255,0),0,0)]
  if vis[0]:labels.append(('黄色标记点A' if c['pair'] else '红色标记点A',ar[0],ar[1],(255,255,0) if c['pair'] else (255,80,80),144,24))
  if vis[1]:labels.append(('紫色标记点B' if c['pair'] else '蓝色标记点B',br[0],br[1],(208,112,255) if c['pair'] else (64,160,255),144,24))
 im=Image.fromarray(expected)
 def text(s,x,y,color=(255,255,255),blocked=None):
  for j,ch in enumerate(s):
   mask=masks[ch].copy()
   if blocked is not None:
    ma=np.array(mask);ma[blocked[y:y+24,x+j*24:x+(j+1)*24]]=0;mask=Image.fromarray(ma)
   im.paste(color,(x+j*24,y,x+(j+1)*24,y+24),mask)
 for ch,x,y,col,w,h in labels:
  if w:im.paste((0,0,0),(x,y,x+w,y+h))
  text(ch,x,y,col)
 if c['show'] and c['video'] and c['state'] in (1,2,3):
  im.paste((0,0,0),(8,544,848,616))
  for j,(n,fill,ok) in enumerate([(c['na'],c['fa'],c['ca']),(c['nb'],c['fb'],c['cb'])]):
   status='待结果' if not c['detection'] else '帧无效' if not c['frameok'] else '无像素' if n==0 else '面积不符' if n<32 or n>921600 else '候选' if ok else '填充不足'
   text(('A' if j==0 else 'B')+'像素：',8,544+j*24)
   text(f'{n:06d}' if c['detection'] else '------',104,544+j*24)
   text('填充：',272,544+j*24);text(f'{fill:03d}' if c['detection'] else '---',344,544+j*24)
   text('%',416,544+j*24);text(status,464,544+j*24)
  reasons=['','帧无效','缺少双色','面积不符','填充不足','间距不符','尖端越界','位移或帧号异常','采集溢出','等待结果','确认中','已锁定']
  code=9 if not c['detection'] else 1 if not c['frameok'] else 11 if c['tip'] else c['reason'] or 10
  reason=reasons[code]
  if code==2:reason='缺少双色' if c['na']==c['nb']==0 else '缺少A' if c['na']==0 else '缺少B'
  text('诊断：'+reason,8,592)
 text('模式：',16,628);text(['原图','边缘','灰度','二值化'][c['mode']],88,628)
 text('倍率：',208,628);text(str(scale),280,628);text('状态：',352,628)
 text(['待命','搜索中','锁定跟踪','失锁','已停止','按键冲突','视频未就绪'][c['state']],424,628)
 text('配色：',16,658);text('黄紫' if c['pair'] else '红蓝',88,658);text('估算尖端：(',184,658)
 text(f'{T[0]:04d},{T[1]:04d})' if c['tip'] else '----,----)',352,658)
 cfgvals=manifest['config'];text(f'L={cfgvals["L_mm"]:04d}mm D={cfgvals["D_mm"]:04d}mm K={manifest["K_display"]}',16,688);text('标注：',664,688);text('开' if c['show'] else '关',736,688)
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
  logs.append(textout);print(textout,flush=True);(r/'reports/robust_osd_simulation.log').write_text('\n'.join(logs)+'\n',encoding='utf-8')
(preview/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(r/'reports/robust_osd_simulation.log').write_text('\n'.join(logs)+'\nCANDIDATE_OSD_TESTS_PASSED\n',encoding='utf-8')
print('CANDIDATE_OSD_TESTS_PASSED')
