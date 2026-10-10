from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parents[1];out=r/'build/sim/robust';out.mkdir(parents=True,exist_ok=True)
cfg=json.loads((r/'rtl/03_tool_detection/target_config.json').read_text());assert cfg['separation_max_px']==1468 and cfg['L_mm']==40 and cfg['D_mm']==20
iv=r/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
logs=[]
for cmd in [[iv,'-g2012','-s','tb_robust_geometry','-o',out/'geometry.vvp','sim/tb_robust_geometry.sv','rtl/04_tracking/target_tracker.v'],[iv.with_name('vvp.exe'),out/'geometry.vvp']]:
 p=subprocess.run(list(map(str,cmd)),cwd=r,env=env,capture_output=True,text=True,timeout=60);logs.append(p.stdout+p.stderr);print(logs[-1]);assert p.returncode==0
(r/'reports/robust_geometry.log').write_text('\n'.join(logs),encoding='utf-8')
