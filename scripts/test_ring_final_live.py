"""Final frozen-input real capture/video regression in four independent jobs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import os,subprocess,hashlib,json
R=Path(__file__).resolve().parents[1];O=R/'build/sim/ring_final_live';O.mkdir(parents=True,exist_ok=True)
P=R/'reports/transparent_ring/regression'
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
names=['stable_awb','stable_packer','stable_capture','stable_model_lane','stable_filter4','stable_grid','regions_divide','stable_tracker','stable_frame_store','stable_display','stable_line_reader','stable_preprocess','stable_osd','stable_glyph_rom','stable_footer_glyph_rom','stable_footer_program_rom','stable_footer_text_rom']
files=[R/'sim/tb_stable_live.sv',*[R/f'rtl/color_regions/{n}.v' for n in names],R/'rtl/04_tracking/target_mailbox.v',R/'rtl/09_osd_ui/scaling_logo_rom.v',R/'user_source/hdl_source/video_in.v',R/'user_source/ip_source/w128_d512_fifo/w128_d512_fifo.v',R/'user_source/ip_source/w128_d512_fifo/soft_fifo_al_4057d6b76aa6.v']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={p.relative_to(R).as_posix():sha(p) for p in files};logs=[];jobs=[]
for pair in (0,1):
 for rot in (0,1):
  exe=O/f'live_{pair}_{rot}.vvp';q=subprocess.run(list(map(str,[iv,'-g2012','-s','tb_stable_live',f'-Ptb_stable_live.PAIR_MODE={pair}',f'-Ptb_stable_live.ROTATE={rot}','-o',exe,*files])),cwd=R,env=env,capture_output=True,text=True)
  logs.append(q.stdout+q.stderr);assert q.returncode==0,logs[-1];jobs.append((pair,rot,exe))
def run(job):
 pair,rot,exe=job;q=subprocess.run([str(iv.with_name('vvp.exe')),str(exe)],cwd=R,env=env,capture_output=True,text=True,timeout=3600)
 return pair,rot,q.returncode,q.stdout+q.stderr
with ThreadPoolExecutor(max_workers=2) as pool:
 for pair,rot,code,log in pool.map(run,jobs):
  logs.append(log);print(log,flush=True);(P/'ring_live_final.log').write_text('\n'.join(logs),encoding='utf-8')
  assert code==0,(pair,rot,log)
after={p.relative_to(R).as_posix():sha(p) for p in files};assert before==after,'Final live inputs changed during execution'
(P/'ring_live_final_inputs.json').write_text(json.dumps(dict(inputs=before,input_hashes_unchanged=True,pairs=[0,1],rotations=[0,1],frames=20,pixels=15974400),indent=2),encoding='utf-8')
print('RING_FINAL_LIVE_ALL_PASS four frozen-input jobs',flush=True)
