from candidate_reference import candidate_meta
"""Independent RGB thresholds/statistics plus actual CDC/detector/tracker RTL."""
from pathlib import Path
import random,subprocess,os,json
r=Path(__file__).resolve().parents[1];out=r/'build/sim/candidate';out.mkdir(parents=True,exist_ok=True)
iv=r/'tools/iverilog/ucrt64/bin/iverilog.exe';vv=iv.with_name('vvp.exe');env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
W,H=128,64
def hit(c,pair,j):
 R,G,B=c
 if not pair:
  m,o1,o2=(R,G,B) if j==0 else (B,R,G)
  return m>=80 and m-o1>=32 and m-o2>=32 and 2*m>=3*o1 and 2*m>=3*o2
 v1,v2,other=(R,G,B) if j==0 else (R,B,G)
 return min(v1,v2)>=80 and min(v1,v2)-other>=24 and 4*min(v1,v2)>=5*other and max(v1,v2)<=2*min(v1,v2)
def pack(n,low,width,val):return n|((val&((1<<width)-1))<<low)
cases=[]
for pair in (0,1):
 for _ in range(5):cases.append(dict(pair=pair,color=None,style='normal'))
# Independent boundary values for both component minima, difference, ratio,
# balance, white/black/green, other pair colors and near-overflow channels.
colors=[(80,80,56),(79,80,20),(80,79,20),(80,80,57),(120,120,96),(119,119,96),(160,80,20),(161,80,20),(255,255,231),(255,255,232),(0,0,0),(255,255,255),(0,255,0),(255,0,0),(0,0,255),(160,100,160)]
for color in colors:
 for j in (0,1):cases.append(dict(pair=1,color=color,j=j,style='normal'))
for style in ('empty','missing','noise','tiny','sparse','oversize','short','long','fault','fault_empty','short_empty'):
 cases.append(dict(pair=1,color=None,style=style))
# Switch during pixels, during centroid division, repeated toggles, stopped
# captures, then long stable runs proving reacquisition of each pair.
cases += [dict(pair=p,color=None,style='normal',mid=mid,enabled=en) for p,mid,en in [(0,True,1),(1,False,1),(1,False,1),(1,False,1),(1,False,1),(1,True,1),(0,False,1),(1,False,1),(0,False,0),(1,False,0),(1,False,1),(1,False,1),(1,False,1),(1,False,1),(0,False,1),(0,False,1),(0,False,1),(0,False,1)]]
stim=out/'dual_pipeline.txt';oracle=out/'dual_pipeline_expected.txt';session=0;last_cmd=None;records=[]
with stim.open('w') as f,oracle.open('w') as e:
 def emit(sof=0,valid=0,fault=0,word=0,cmd=None):f.write(f'{sof} {valid} {fault} {command if cmd is None else cmd} {word:024x}\n')
 for seq,c in enumerate(cases,1):
  pair=c['pair'];enabled=c.get('enabled',1)
  if (pair,enabled)!=last_cmd:session+=1;last_cmd=(pair,enabled)
  command=(pair<<9)|(session<<1)|enabled;stamp=session
  # Set next-frame config early enough for mailbox to settle. Previous result
  # was already emitted except for the explicit changes during division below.
  for _ in range(30):emit()
  image=[(40,40,40)]*(W*H)
  a,b=((220,180,30),(170,30,220)) if pair else ((220,30,20),(20,30,220))
  if c['color'] is not None:
   color=c['color'];color=(color[0],color[2],color[1]) if c['j'] else color
   if c['j']:b=color
   else:a=color
  for x0,y0,color in ((80,20,a),(30,20,b)):
   for y in range(y0,y0+12):
    for x in range(x0,x0+12):image[y*W+x]=color
  style=c['style']
  if style in ('empty','fault_empty','short_empty'):image=[(40,40,40)]*(W*H)
  if style=='missing':image=[v if v!=b else (40,40,40) for v in image]
  if style=='tiny':image=[(40,40,40)]*(W*H);image[0]=a;image[-1]=b
  if style in ('noise','sparse'):
   rng=random.Random(912);image=[tuple(rng.randrange(256) for _ in range(3)) if style=='noise' or i%40==0 else (40,40,40) for i in range(W*H)]
  if style=='oversize':image=[a if i%W<W//2 else b for i in range(W*H)]
  pixels=W*H-4 if style.startswith('short') else W*H+4 if style=='long' else W*H
  image=(image+[(40,40,40)]*4)[:pixels]
  fault=int(style.startswith('fault'))
  # Fault input at SOF describes the previous frame, as in production.
  if seq%2:emit(1,0,records[-1]['fault'] if records else 0);emit()
  for k in range(0,pixels,4):
   if c.get('mid') and k==64:
    session+=1;command=(((1-pair)<<9)|(session<<1)|enabled);last_cmd=(1-pair,enabled)
   word=0
   for R,G,B in image[k:k+4]:word=(word<<24)|(R<<16)|(G<<8)|B
   first=seq%2==0 and k==0
   emit(int(first),1,records[-1]['fault'] if first and records else 0,word)
  for _ in range(180):emit()
  n=seq|(stamp<<235)|(pair<<243)|(enabled<<244);groups=[[],[]]
  for i,color in enumerate(image[:W*H]):
   for j in (0,1):
    if hit(color,pair,j):groups[j].append((i%W,i//W))
  valid=pixels==W*H and not fault;reason=8 if fault else 0 if valid else 1
  areas=[];fills=[];centers=[]
  for j,pts in enumerate(groups):
   area=len(pts);areas.append(area)
   xs=[p[0] for p in pts];ys=[p[1] for p in pts]
   box=(min(xs,default=W-1),max(xs,default=0),min(ys,default=H-1),max(ys,default=0))
   fills.append(area*100 >= (box[1]-box[0]+1)*(box[3]-box[2]+1)*30)
   centers.append((sum(xs)//area,sum(ys)//area) if area else (0,0))
   for low,width,v in zip([100,111,122,132] if j==0 else [142,153,164,174],[11,11,10,10],box):n=pack(n,low,width,v)
   n=pack(n,184+j*20,20,area)
  calculate=True
  if not min(areas):valid=False;reason=2;calculate=False
  elif min(areas)<64 or max(areas)>20000:valid=False;reason=3;calculate=False
  elif not all(fills):valid=False;reason=4;calculate=False
  if calculate:
   for j,(x,y) in enumerate(centers):n=pack(n,37+j*21,11,x);n=pack(n,48+j*21,10,y)
  n=candidate_meta(groups,W,H,seq,stamp,pair,enabled,pixels,fault);valid=bool((n>>32)&1);reason=(n>>33)&15
  n=pack(n,32,1,valid);n=pack(n,33,4,reason);e.write(f'{n:064x}\n')
  records.append(dict(c,frame=seq,session=stamp,fault=fault,areas=areas,valid=valid,reason=reason))
 emit(1,0,records[-1]['fault']);emit()
 # Change command while last valid frame is still calculating its centroids.
 for _ in range(10):emit()
 command=((1-pair)<<9)|((session+1)<<1)|1
 for _ in range(220):emit()
(out/'dual_pipeline_cases.json').write_text(json.dumps(records,indent=2))
logs=[]
for cmd in ([iv,'-g2012','-s','tb_candidate_pipeline','-o',out/'pipeline.vvp','sim/tb_candidate_pipeline.sv','rtl/03_tool_detection/target_detector.v','rtl/04_tracking/target_tracker.v','rtl/04_tracking/target_mailbox.v'],[vv,out/'pipeline.vvp',f'+STIM={stim}',f'+EXPECT={oracle}',f'+COUNT={len(cases)}']):
 p=subprocess.run(list(map(str,cmd)),cwd=r,env=env,capture_output=True,text=True,timeout=500);logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
 (r/'reports/candidate_detection_simulation.log').write_text('\n'.join(logs),encoding='utf-8');assert p.returncode==0
print('CANDIDATE_DETECTION_TESTS_PASSED')
