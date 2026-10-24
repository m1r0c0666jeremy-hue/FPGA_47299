from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'scripts/test_target_osd.py').read_text(encoding='utf-8')
s=s.replace('build/sim/target_lock/osd','build/sim/dualcolor/osd').replace("r/'reports/target_preview'","r/'reports/dualcolor_preview'").replace('tb_target_osd','tb_dualcolor_osd').replace("atlas=Image.open(preview/'glyphs.png')","atlas=Image.open(r/'reports/target_preview/glyphs.png')").replace('target_osd_simulation.log','dualcolor_osd_simulation.log').replace('TARGET_OSD_TESTS_PASSED','DUALCOLOR_OSD_TESTS_PASSED')
s=s.replace('logs=[]', '''cases=[dict(c,pair=pair) for pair in range(2) for c in cases]
cases += [dict(cases[2],pair=p,mode=m,zoom=z,x0=0,y0=0,A=(100,65),B=(45,65),T=(128,65)) for p in range(2) for m in range(4) for z in range(3)]
cases += [dict(cases[2],pair=p,A=(px,py),B=(px,py),T=(px,py),x0=0,y0=0) for p in range(2) for px,py in [(0,0),(1279,623),(100,5),(300,600)]]
logs=[]''')
s=s.replace("fields=[(32,1,c['tip'])", "fields=[(243,1,c['pair']),(32,1,c['tip'])")
s=s.replace('expected[:624][redblue[1]]=[48,128,255];expected[:624][redblue[0]]=[255,48,48]', 'expected[:624][redblue[1]]=[192,80,255] if c["pair"] else [48,128,255];expected[:624][redblue[0]]=[255,255,0] if c["pair"] else [255,48,48]')
start=s.index("  for ch,b,col in [('A'");end=s.index(' im=Image.fromarray(expected)',start)
s=s[:start]+'''  # Independent rectangle layout oracle: first valid candidate wins.
  def clamp(v,hi):return max(0,min(hi,v))
  def intersects(a,b):
   return a[0]<b[0]+b[2] and b[0]<a[0]+a[2] and a[1]<b[1]+b[3] and b[1]<a[1]+a[3]
  vis=[b[1]>=0 and b[0]<1280 and b[3]>=0 and b[2]<624 for b in sb]
  tv=0<=tx<1280 and 0<=ty<624
  tr=(clamp(tx+17 if tx+137<=1280 else tx-137,1160),clamp(ty-24,576),120,48)
  a,b=sb
  ac=[(clamp(a[0],1136),clamp(y,600),144,24) for y in [a[2]-26 if a[2]>=26 else a[3]+3,a[3]+3]]
  ac += [(clamp(a[1]-143,1136),clamp(y,600),144,24) for y in [a[2]-26 if a[2]>=26 else a[3]+3,a[3]+3]]
  ar=next((q for q in ac if not(vis[0] and tv and intersects(q,tr))),None)
  fallback=ar is None;ar=ar or ac[-1]
  bc=[(clamp(b[0],1136),clamp(y,600),144,24) for y in [b[2]-26 if b[2]>=26 else b[3]+3,b[3]+3]]
  bc += [(clamp(x,1136),clamp(b[2],600),144,24) for x in [b[1]+3,b[0]-147]]
  br=next((q for q in bc if not vis[1] or not((tv and intersects(q,tr)) or (vis[0] and intersects(q,ar)))),None)
  fallback |= br is None;br=br or bc[-1]
  if fallback:tr=(8,8,120,48);ar=(8,60,144,24);br=(8,88,144,24)
  if tv:labels += [('十字准心T',tr[0],tr[1],(255,255,0),120,48),('估算尖端',tr[0],tr[1]+24,(255,255,0),0,0)]
  if vis[0]:labels.append(('黄色标记点A' if c['pair'] else '红色标记点A',ar[0],ar[1],(255,255,0) if c['pair'] else (255,80,80),144,24))
  if vis[1]:labels.append(('紫色标记点B' if c['pair'] else '蓝色标记点B',br[0],br[1],(208,112,255) if c['pair'] else (64,160,255),144,24))
''' + s[end:]
start=s.index(' blocked=np.zeros');end=s.index(" text('模式：'",start)
s=s[:start]+''' for ch,x,y,col,w,h in labels:
  if w:im.paste((0,0,0),(x,y,x+w,y+h))
  text(ch,x,y,col)
'''+s[end:]
s=s.replace("text('红A前',16,658,(255,80,80));text('蓝B后',112,658,(64,160,255));text('估算尖端：(',208,658)", "text('配色：',16,658);text('黄紫' if c['pair'] else '红蓝',88,658);text('估算尖端：(',184,658)")
s=s.replace(' KEY3启停\',16,688)', "',16,688);text('标注：',664,688);text('开' if c['show'] else '关',736,688)")
s=s.replace("print('DUALCOLOR_OSD_TESTS_PASSED')", "(r/'reports/dualcolor_osd_simulation.log').write_text('\\n'.join(logs)+'\\nDUALCOLOR_OSD_TESTS_PASSED\\n',encoding='utf-8')\nprint('DUALCOLOR_OSD_TESTS_PASSED')")
(r/'scripts/test_dualcolor_osd.py').write_text(s,encoding='utf-8',newline='\n')
print('Prepared independent dualcolor OSD pixel oracle')
