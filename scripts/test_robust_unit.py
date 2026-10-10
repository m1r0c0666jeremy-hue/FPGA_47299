from candidate_reference import candidate_meta
"""Independent integer oracles + RTL tests. Does not overwrite historic logs."""
from pathlib import Path
import argparse,os,subprocess,json,random
r=Path(__file__).resolve().parents[1]
out=r/'build/sim/robust';out.mkdir(parents=True,exist_ok=True)
iv=r/'tools/iverilog/ucrt64/bin/iverilog.exe';vvp=iv.with_name('vvp.exe')
env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
p=argparse.ArgumentParser();p.add_argument('--full',action='store_true');a=p.parse_args()
logs=[]
def run(args,timeout=300):
 c=subprocess.run([str(x) for x in args],cwd=r,env=env,capture_output=True,text=True,timeout=timeout)
 text=c.stdout+c.stderr;logs.append(text);print(text,flush=True)
 (r/'reports/robust_unit_simulation.log').write_text('\n'.join(logs),encoding='utf-8')
 if c.returncode:raise RuntimeError(f'Command failed: {args}')
def test(name,files,args=(),params=(),timeout=300):
 top='tb_candidate_'+name;exe=out/(name+'.vvp')
 run([iv,'-g2012','-s',top,*params,'-o',exe,'sim/'+top+'.sv',*files]);run([vvp,exe,*args],timeout)
def put(n,low,width,val):return (n&~(((1<<width)-1)<<low))|((val&((1<<width)-1))<<low)
def detect_cases(w,h,full=False):
 stim=out/f'detector_{w}.txt';exp=out/f'detector_{w}_expected.txt'
 samples=[]
 cases=list(range(22)) if not full else [0,10]
 with stim.open('w') as f,exp.open('w') as e:
  for seq,case in enumerate(cases,1):
   image=[(40,40,40)]*(w*h)
   ax,ay,bx,by=(80,20,30,20) if not full else (800,360,400,360)
   if case==1:ax,bx=4,70
   if case==2:ay,by=0,h-12
   # Marginal colors test strict >= and cross-products, not floating HSV.
   color=[(220,30,20),(80,48,10),(79,10,10),(120,80,20),(119,80,20),(255,224,0),(255,223,0)]
   cr=color[(case-3)%len(color)] if 3<=case<=9 else color[0]
   for x0,y0,c in [(ax,ay,cr),(bx,by,(20,30,220))]:
    for yy in range(y0,min(y0+12,h)):
     for xx in range(x0,min(x0+12,w)):image[yy*w+xx]=c
   if case==11:image=[(50,50,50)]*(w*h)
   if case==12:
    image=[(r0,g,b) if b<100 else (40,40,40) for r0,g,b in image]
   if case==13:
    image=[(220,30,20) if i%47==0 else (20,30,220) if i%53==0 else (40,40,40) for i in range(w*h)]
   if case==14:
    image=[(255,255,255)]*(w*h);image[1]=(255,0,0);image[-2]=(0,0,255)
   if case==15:image=[(255,0,0) if i%w<w//2 else (0,0,255) for i in range(w*h)]
   if case>=19:
    rng=random.Random(case)
    for _ in range(case*3):image[rng.randrange(w*h)]=tuple(rng.randrange(256) for _ in range(3))
   count=w*h-4 if case==16 else w*h+4 if case==17 else w*h
   fault=int(case==18)
   image=(image+[(40,40,40)]*4)[:count]
   # SOF alternates: separate pulse OR coincident with first valid word.
   if seq%2:f.write(f'1 0 {samples[-1]["fault"] if samples else 0} 0\n0 0 0 0\n')
   for base in range(0,count,4):
    word=0
    for rr,gg,bb in image[base:base+4]:word=(word<<24)|(rr<<16)|(gg<<8)|bb
    sf=int(seq%2==0 and base==0)
    ff=samples[-1]['fault'] if sf and samples else 0
    f.write(f'{sf} 1 {ff} {word:024x}\n')
    if base%w==w-4:f.write('0 0 0 0\n')
   f.write('0 0 0 0\n'*160)
   groups=[[],[]]
   for i,(rr,gg,bb) in enumerate(image[:w*h]):
    if rr>=80 and rr-gg>=32 and rr-bb>=32 and 2*rr>=3*gg and 2*rr>=3*bb:groups[0].append((i%w,i//w))
    if bb>=80 and bb-gg>=32 and bb-rr>=32 and 2*bb>=3*gg and 2*bb>=3*rr:groups[1].append((i%w,i//w))
   meta=seq | (1<<235) | (1<<244);reason=8 if fault else 1 if count!=w*h else 0;valid=reason==0
   centers=[];areas=[];fills=[]
   for ci,pts in enumerate(groups):
    area=len(pts);areas.append(area)
    xmin=min((q[0] for q in pts),default=w-1);xmax=max((q[0] for q in pts),default=0)
    ymin=min((q[1] for q in pts),default=h-1);ymax=max((q[1] for q in pts),default=0)
    centers.append((sum(q[0] for q in pts)//area,sum(q[1] for q in pts)//area) if area else (0,0))
    fills.append(area*100>=(xmax-xmin+1)*(ymax-ymin+1)*30)
    for low,width,val in zip(([100,111,122,132] if ci==0 else [142,153,164,174]),[11,11,10,10],[xmin,xmax,ymin,ymax]):meta=put(meta,low,width,val)
    meta=put(meta,184+20*ci,20,area)
   calculate=True
   if min(areas)==0:valid=False;reason=2;calculate=False
   elif min(areas)<64 or max(areas)>20000:valid=False;reason=3;calculate=False
   elif not all(fills):valid=False;reason=4;calculate=False
   if calculate:
    for ci,(xx,yy) in enumerate(centers):meta=put(meta,37+21*ci,11,xx);meta=put(meta,48+21*ci,10,yy)
   meta=put(meta,32,1,valid);meta=put(meta,33,4,reason)
   meta=candidate_meta(groups,w,h,seq,1,0,1,count,fault)
   e.write(f'{meta:064x} {(1<<256)-1:064x}\n')
   samples.append({'case':case,'frame':seq,'fault':fault,'pixels':count,'valid':valid,'reason':reason})
  f.write(f'1 0 {samples[-1]["fault"]} 0\n0 0 0 0\n')
 (out/f'detector_{w}_cases.json').write_text(json.dumps(samples,indent=2))
 return [f'+STIM={stim}',f'+EXPECT={exp}',f'+COUNT={len(cases)}']
def tracker_cases(L,D):
 path=out/f'tracker_{L}_{D}.txt';rng=random.Random(727);seq=0;last=0;streak=0;prev=None;ever=False;session=1
 with path.open('w') as f:
  for i in range(450):
   enable=not (15<=i<20)
   if i in (15,20,100,250):session+=1;streak=0;prev=None;ever=False
   seq+=int(i not in (8,9,44))
   if i<30:ax,ay,bx,by=700,350,600,350
   elif i<100:ax,ay,bx,by=100+(i%10),60,50,60
   else:ax,ay,bx,by=[rng.randrange(1280),rng.randrange(720),rng.randrange(1280),rng.randrange(720)]
   source_valid=i not in (4,12,13,26,40)
   im=seq | (session<<235) | (1<<244)
   for low,width,val in [(32,1,source_valid),(33,4,0 if source_valid else 2),(37,11,ax),(48,10,ay),(58,11,bx),(69,10,by)]:im=put(im,low,width,val)
   k=(D*65536+L//2)//L
   def rounded(q):return (q+32768)//65536 if q>=0 else -((-q+32768)//65536)
   tx=rounded(ax*65536+(ax-bx)*k);ty=rounded(ay*65536+(ay-by)*k)
   dd=(ax-bx)**2+(ay-by)**2
   geo=source_valid and 16**2<=dd<=600**2 and 0<=tx<1280 and 0<=ty<720
   valid=False;reason=0 if source_valid else 2
   if not enable:streak=0;prev=None;ever=False
   state=(3 if ever else 1) if enable else 0
   if enable and seq!=last:
    jump=prev is not None and max(abs(a-b) for a,b in zip((ax,ay,bx,by),prev))>96
    good=geo and (prev is None or (not jump and seq==last+1))
    last=seq;prev=(ax,ay,bx,by) if geo else None
    if good:
     streak=min(3,streak+1)
     if streak>=3:valid=True;state=2;ever=True
    else:
     streak=0
     if source_valid:reason=5 if not 16**2<=dd<=600**2 else 6 if not (0<=tx<1280 and 0<=ty<720) else 7
   expected=im
   for low,width,val in [(32,1,valid),(33,4,reason),(79,11,tx),(90,10,ty),(232,3,state),(235,8,session)]:expected=put(expected,low,width,val)
   f.write(f'{int(enable)} {session} {im:064x} {expected:064x}\n')
 return [f'+CASES={path}']
test('diagnostics',['rtl/09_osd_ui/target_diagnostics.v'])
test('controls',['rtl/00_top_control/target_controls.v'])
test('display',['rtl/04_tracking/target_display.v'])
test('store',['rtl/04_tracking/target_frame_store.v'])
test('mailbox',['rtl/04_tracking/target_mailbox.v'])
test('detector',['rtl/03_tool_detection/target_detector.v'],detect_cases(128,64))
for L,D in [(40,20),(40,0),(30,20),(20,30)]:
 test('tracker',['rtl/04_tracking/target_tracker.v'],tracker_cases(L,D),[f'-Ptb_candidate_tracker.L={L}',f'-Ptb_candidate_tracker.D={D}'])
if a.full:test('detector',['rtl/03_tool_detection/target_detector.v'],detect_cases(1280,720,True),['-Ptb_candidate_detector.W=1280','-Ptb_candidate_detector.H=720'],900)
logs.append('CANDIDATE_UNIT_TESTS_PASSED');(r/'reports/robust_unit_simulation.log').write_text('\n'.join(logs),encoding='utf-8')
print(logs[-1])
