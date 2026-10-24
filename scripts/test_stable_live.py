from pathlib import Path
import os,subprocess
R=Path(__file__).resolve().parents[1];O=R/'build/sim/stable_live';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
names=['stable_awb','stable_packer','stable_capture','stable_model_lane','stable_filter4','stable_grid','regions_divide','stable_tracker','stable_frame_store','stable_display','stable_line_reader','stable_preprocess','stable_osd','stable_glyph_rom','stable_footer_glyph_rom','stable_footer_program_rom','stable_footer_text_rom']
files=[R/'sim/tb_stable_live.sv',*[R/f'rtl/color_regions/{n}.v' for n in names],R/'rtl/04_tracking/target_mailbox.v',R/'rtl/09_osd_ui/scaling_logo_rom.v',R/'user_source/hdl_source/video_in.v',R/'user_source/ip_source/w128_d512_fifo/w128_d512_fifo.v',R/'user_source/ip_source/w128_d512_fifo/soft_fifo_al_4057d6b76aa6.v'];logs=[]
commands=[]
for pair,rot in ((0,0),(1,0),(0,1),(1,1)):
    exe=O/f'live_{pair}_{rot}.vvp'
    commands.extend(([iv,'-g2012','-s','tb_stable_live',f'-Ptb_stable_live.PAIR_MODE={pair}',f'-Ptb_stable_live.ROTATE={rot}','-o',exe,*files],[iv.with_name('vvp.exe'),exe]))
for cmd in commands:
    q=subprocess.run(list(map(str,cmd)),cwd=R,env=env,capture_output=True,text=True,timeout=1800);logs.append(q.stdout+q.stderr);print(logs[-1],flush=True)
    (R/'reports/transparent_ring/regression/stable_live.log').write_text('\n'.join(logs),encoding='utf-8')
    if q.returncode:raise SystemExit(q.returncode)
