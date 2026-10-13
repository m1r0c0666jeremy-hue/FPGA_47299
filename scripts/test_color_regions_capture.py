from pathlib import Path
import subprocess,os,argparse
R=Path(__file__).resolve().parents[1];O=R/'build/sim/color_regions/capture';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
ap=argparse.ArgumentParser();ap.add_argument('--pair',type=int,choices=[0,1],default=0);ap.add_argument('--move',action='store_true');opts=ap.parse_args()
tag=f'pair{opts.pair}'+('_moving' if opts.move else '')
O=O/tag;O.mkdir(parents=True,exist_ok=True)
files=['classifier','runs4','run_labeler','divide','finalize','grid','confirm','capture']
logs=[]
for command in ([iv,'-g2012','-s','tb_color_regions_capture','-o',O/'capture.vvp',R/'sim/tb_color_regions_capture.sv',*[R/f'rtl/color_regions/regions_{f}.v' for f in files]],
             [iv.with_name('vvp.exe'),O/'capture.vvp',f'+PAIR={opts.pair}',f'+MOVE={int(opts.move)}']):
 p=subprocess.run(list(map(str,command)),cwd=R,env=env,capture_output=True,text=True,timeout=900)
 logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
 (R/f'reports/color_regions_capture_{tag}.log').write_text('\n'.join(logs),encoding='utf-8')
 assert p.returncode==0
