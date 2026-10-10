"""Extend the independent raster oracle with single-candidate diagnostic cases."""
from pathlib import Path
p=Path(__file__).with_name('test_candidate_osd.py')
s=p.read_text(encoding='utf-8')
s=s.replace('logs=[]', '''cases=[dict(c,detection=int(c['state'] in (1,2,3)),ca=int(c['state'] in (1,2,3)),cb=int(c['state'] in (1,2,3)),frameok=1,na=357,nb=357,fa=100,fb=100,reason=0) for c in cases]
for pair in (0,1):
 for patch in [dict(ca=1,cb=0,nb=0,fb=0,reason=2),dict(ca=0,cb=1,na=0,fa=0,reason=2),dict(ca=0,cb=0,na=0,nb=0,fa=0,fb=0,reason=2),dict(ca=0,na=1,reason=3),dict(ca=0,na=100,fa=10,reason=4),dict(reason=5),dict(reason=6),dict(frameok=0,ca=0,cb=0,reason=1),dict(detection=0,ca=0,cb=0),dict(na=921600,ca=0,reason=3)]:
  cases.append(dict(cases[2],state=1,tip=0,pair=pair,**patch))
logs=[]''')
s=s.replace("fields=[(243,1,c['pair'])", "fields=[(255,1,c['detection']),(245,1,c['ca']),(246,1,c['cb']),(247,1,c['frameok']),(184,20,c['na']),(204,20,c['nb']),(224,7,c['fa']),(248,7,c['fb']),(33,4,c['reason']),(243,1,c['pair'])")
s=s.replace("if c['show'] and c['tip'] and c['video']:","if c['show'] and c['detection'] and c['video']:")
s=s.replace("for box,P in zip(sb,(A,B)):","for j,(box,P) in enumerate(zip(sb,(A,B))):")
s=s.replace('redblue.append(edge|((abs(xx-cx)<=2)&(abs(yy-cy)<=2)))',"redblue.append((edge|((abs(xx-cx)<=2)&(abs(yy-cy)<=2))) & bool(c['frameok'] and c['ca' if j==0 else 'cb']))")
s=s.replace('expected[:624][outline]=0;expected[:624][cross]=[255,255,0]',"if c['tip']:expected[:624][outline]=0;expected[:624][cross]=[255,255,0]")
s=s.replace('vis=[b[1]>=0 and b[0]<1280 and b[3]>=0 and b[2]<624 for b in sb]',"vis=[bool(c['frameok'] and c['ca' if j==0 else 'cb']) and b[1]>=0 and b[0]<1280 and b[3]>=0 and b[2]<624 for j,b in enumerate(sb)]")
s=s.replace('tv=0<=tx<1280 and 0<=ty<624',"tv=c['tip'] and 0<=tx<1280 and 0<=ty<624").replace('clamp(ty-24,576)','clamp(ty-24,494)').replace('clamp(y,600)','clamp(y,518)').replace('clamp(b[2],600)','clamp(b[2],518)')
s=s.replace(" text('模式：',16,628)",''' if c['show'] and c['video'] and c['state'] in (1,2,3):
  im.paste((0,0,0),(8,544,848,616))
  for j,(n,fill,ok) in enumerate([(c['na'],c['fa'],c['ca']),(c['nb'],c['fb'],c['cb'])]):
   status='待结果' if not c['detection'] else '帧无效' if not c['frameok'] else '无像素' if n==0 else '面积不符' if n<64 or n>20000 else '候选' if ok else '填充不足'
   text(('A' if j==0 else 'B')+'像素：',8,544+j*24)
   text(f'{n:06d}' if c['detection'] else '------',104,544+j*24)
   text('填充：',272,544+j*24);text(f'{fill:03d}' if c['detection'] else '---',344,544+j*24)
   text('%',416,544+j*24);text(status,464,544+j*24)
  reasons=['','帧无效','缺少双色','面积不符','填充不足','间距不符','尖端越界','位移或帧号异常','采集溢出','等待结果','确认中','已锁定']
  code=9 if not c['detection'] else 1 if not c['frameok'] else 11 if c['tip'] else c['reason'] or 10
  reason=reasons[code]
  if code==2:reason='缺少双色' if c['na']==c['nb']==0 else '缺少A' if c['na']==0 else '缺少B'
  text('诊断：'+reason,8,592)
 text('模式：',16,628)''')
p.write_text(s,encoding='utf-8')
