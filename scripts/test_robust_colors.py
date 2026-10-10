"""Independent RGB/range oracle against RTL with production config overrides."""
from pathlib import Path
import subprocess,os,json
from robust_reference import candidate_meta
r=Path(__file__).resolve().parents[1];out=r/'build/sim/robust';out.mkdir(parents=True,exist_ok=True)
iv=r/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
cfg=json.loads((r/'rtl/03_tool_detection/target_config.json').read_text())
assert (cfg['color_min'],cfg['color_diff'],cfg['ratio_num'],cfg['ratio_den'],cfg['area_min'],cfg['area_max'],cfg['fill_percent_min'])==(40,12,9,8,32,921600,0)
assert (cfg['yp_min'],cfg['yp_diff'],cfg['yp_ratio_num'],cfg['yp_ratio_den'],cfg['yp_balance'])==(40,12,9,8,4)
params='.COLOR_MIN(40),.COLOR_DIFF(12),.RATIO_NUM(9),.RATIO_DEN(8),.AREA_MIN(32),.AREA_MAX(921600),.FILL_PERCENT_MIN(0),.YP_MIN(40),.YP_DIFF(12),.YP_RATIO_NUM(9),.YP_RATIO_DEN(8),.YP_BALANCE(4),'
base=(r/'sim/tb_candidate_detector.sv').read_text().replace('target_detector #(','target_detector #('+params)
def hit(rgb,p,j):
 R,G,B=rgb
 if not p:
  strong,other1,other2=(R,G,B) if not j else (B,R,G)
  return strong>=40 and strong-max(other1,other2)>=12 and 8*strong>=9*max(other1,other2)
 a,b,o=(R,G,B) if not j else (R,B,G)
 return min(a,b)>=40 and min(a,b)-o>=12 and 8*min(a,b)>=9*o and max(a,b)<=4*min(a,b)
logs=[]
def run(cmd):
 p=subprocess.run(list(map(str,cmd)),cwd=r,env=env,capture_output=True,text=True,timeout=900)
 logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
 (r/'reports/robust_colors.log').write_text('\n'.join(logs),encoding='utf-8');assert p.returncode==0
coverage=[]
for pair in (0,1):
 for full in (False,True):
  w,h=(1280,720) if full else (128,64)
  bench=out/f'colors_{pair}_{w}.sv';bench.write_text(base.replace("1'b0,1'b1,8'd1",f"1'b{pair},1'b1,8'd1"))
  aa,bb=((210,185,170),(170,185,210)) if not pair else ((200,190,160),(180,150,200))
  # Dark/light, >= boundaries, neutral colors, chromatic noise. Expected colors
  # are derived from arithmetic independently of the RTL implementation.
  colors=[(40,28,28),(39,0,0),(40,29,28),(108,96,96),(107,95,96),(200,170,170),(255,243,243),(255,244,244),(12,12,40),(170,170,200),(40,40,28),(39,40,0),(40,40,29),(108,108,96),(107,108,96),(160,40,0),(161,40,0),(200,200,170),(40,28,40),(200,170,200),(255,255,255),(0,0,0),(128,128,128),(0,255,0)]
  jobs=list(range(7)) if full else list(range(len(colors)))
  stim=out/f'colors_{pair}_{w}.txt';expected=out/f'colors_{pair}_{w}_expected.txt'
  with stim.open('w') as f,expected.open('w') as e:
   for seq,case in enumerate(jobs,1):
    image=[(128,128,128)]*(w*h)
    if full:
     aw,ah,bw,bh=[(31,1,8,4),(8,4,8,4),(200,100,8,4),(400,300,80,50),(700,400,150,100),(1280,720,0,0),(8,4,8,4)][case]
     ax,ay,bx,by=(0,0,1000,400)
     for x0,y0,ww,hh,c in [(ax,ay,aw,ah,aa),(bx,by,bw,bh,bb)]:
      for y in range(y0,min(y0+hh,h)):
       for x in range(x0,min(x0+ww,w)):image[y*w+x]=c
     if case==6:image[-1]=aa # <1% fill is reported; no hard rejection.
    else:
     for x0,col in [(80,colors[case]),(30,bb)]:
      for y in range(20,28):
       for x in range(x0,x0+8):image[y*w+x]=col
    groups=[[],[]]
    for i,col in enumerate(image):
     for j in (0,1):
      if hit(col,pair,j):groups[j].append((i%w,i//w))
    n=candidate_meta(groups,w,h,seq,1,pair,1,w*h,0)
    # Explicit acceptance examples, not merely matching a generated oracle.
    if full and case in (1,2,3,4,6):assert (n>>32)&1
    if full and case==0:assert (n>>33)&15==3
    if full and case==5:assert (n>>245)&1 and not ((n>>246)&1)
    coverage.append(dict(pair=pair,size=[w,h],case=case,areas=list(map(len,groups)),valid=bool((n>>32)&1),fillA=(n>>224)&127))
    e.write(f'{n:064x} {(1<<256)-1:064x}\n')
    f.write('1 0 0 0\n0 0 0 0\n')
    for i in range(0,w*h,4):
     word=0
     for R,G,B in image[i:i+4]:word=(word<<24)|(R<<16)|(G<<8)|B
     f.write(f'0 1 0 {word:024x}\n')
    f.write('0 0 0 0\n'*220)
   f.write('1 0 0 0\n0 0 0 0\n')
  exe=out/f'colors_{pair}_{w}.vvp'
  run([iv,'-g2012','-s','tb_candidate_detector',f'-Ptb_candidate_detector.W={w}',f'-Ptb_candidate_detector.H={h}','-o',exe,bench,'rtl/03_tool_detection/target_detector.v'])
  run([iv.with_name('vvp.exe'),exe,f'+STIM={stim}',f'+EXPECT={expected}',f'+COUNT={len(jobs)}'])
(r/'reports/robust_color_cases.json').write_text(json.dumps(coverage,indent=2),encoding='utf-8')
logs.append('ROBUST_COLORS_PASSED: 48 small + 14 full frames, independent unequal areas and centroid/fill calculations')
(r/'reports/robust_colors.log').write_text('\n'.join(logs),encoding='utf-8');print(logs[-1])
