from candidate_reference import candidate_meta
"""Full 720p yellow/purple frames, including exact 64/63 and 20000 boundaries."""
from pathlib import Path
import subprocess,os
r=Path(__file__).resolve().parents[1];out=r/'build/sim/candidate';out.mkdir(parents=True,exist_ok=True)
iv=r/'tools/iverilog/ucrt64/bin/iverilog.exe';vvp=iv.with_name('vvp.exe');env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
bench=(r/'sim/tb_candidate_detector.sv').read_text().replace("1'b0,1'b1,8'd1", "1'b1,1'b1,8'd1")
(out/'tb_full_yp.sv').write_text(bench)
stim=out/'full_yp.txt';exp=out/'full_yp_expected.txt'
def put(n,l,w,v):return n|((v&((1<<w)-1))<<l)
jobs=[(8,8,False),(200,100,False),(200,101,False),(9,7,False),(8,8,True)]
with stim.open('w') as f,exp.open('w') as e:
 for seq,(aw,ah,stray) in enumerate(jobs,1):
  a={(x,y) for y in range(300,300+ah) for x in range(800,800+aw)}
  if stray:a.add((100,100))
  b={(x,y) for y in range(300,308) for x in range(400,408)}
  f.write('1 0 0 0\n0 0 0 0\n')
  for y in range(720):
   for x in range(0,1280,4):
    word=0
    for lane in range(4):word=(word<<24)|(0xdcb41e if (x+lane,y) in a else 0xaa1edc if (x+lane,y) in b else 0x282828)
    f.write(f'0 1 0 {word:024x}\n')
  f.write('0 0 0 0\n'*160)
  reason=3 if len(a)<64 or len(a)>20000 else 4 if stray else 0
  n=seq|(1<<235)|(1<<243)|(1<<244)|(int(reason==0)<<32)|(reason<<33)
  for j,pts in enumerate((a,b)):
   xs=[p[0] for p in pts];ys=[p[1] for p in pts]
   for l,w,v in zip([100,111,122,132] if j==0 else [142,153,164,174],[11,11,10,10],[min(xs),max(xs),min(ys),max(ys)]):n=put(n,l,w,v)
   n=put(n,184+j*20,20,len(pts))
   if not reason:n=put(n,37+j*21,11,sum(xs)//len(pts));n=put(n,48+j*21,10,sum(ys)//len(pts))
  n=candidate_meta([a,b],1280,720,seq,1,1,1,1280*720,0)
  e.write(f'{n:064x} {(1<<256)-1:064x}\n')
 f.write('1 0 0 0\n0 0 0 0\n')
logs=[]
for command in ([iv,'-g2012','-s','tb_candidate_detector','-Ptb_candidate_detector.W=1280','-Ptb_candidate_detector.H=720','-o',out/'ypfull.vvp',out/'tb_full_yp.sv','rtl/03_tool_detection/target_detector.v'],[vvp,out/'ypfull.vvp',f'+STIM={stim}',f'+EXPECT={exp}',f'+COUNT={len(jobs)}']):
 p=subprocess.run(list(map(str,command)),cwd=r,env=env,capture_output=True,text=True,timeout=900);logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
 (r/'reports/candidate_full_simulation.log').write_text('\n'.join(logs),encoding='utf-8');assert p.returncode==0
print('CANDIDATE_FULL_TESTS_PASSED')
