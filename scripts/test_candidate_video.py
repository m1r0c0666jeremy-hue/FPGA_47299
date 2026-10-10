"""Exercise the new reader + actual target OSD with full HDMI timing.
Reuses the independent DDR/pixel oracle from the archived ScalingTest bench.
"""
from pathlib import Path
import os,subprocess,json,argparse
from concurrent.futures import ThreadPoolExecutor
r=Path(__file__).resolve().parents[1];out=r/'build/sim/candidate';out.mkdir(parents=True,exist_ok=True)
iv=r/'tools/iverilog/ucrt64/bin/iverilog.exe';vvp=iv.with_name('vvp.exe')
env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
p=argparse.ArgumentParser();p.add_argument('--quick',action='store_true');a=p.parse_args()
s=(r/'sim/tb_scaling_video.sv').read_text(encoding='utf-8').replace('tb_scaling_video','tb_target_video')
s=s.replace('    scaling_line_reader dut(','''    reg commit=0,vs_prev=0;integer countdown=0;
    always @(posedge pc)begin
      vs_prev<=vs;commit<=0;
      if(vs&&!vs_prev)countdown<=20;
      else if(countdown>0)begin countdown<=countdown-1;if(countdown==1)commit<=1;end
    end
    target_line_reader dut(commit,1'b1,''')
start=s.index('    scaling_osd osd(');end=s.index('\n',start)
s=s[:start]+'''    target_osd osd(.I_clk(pc),.I_rst_n(rst),.I_vs(pvs),.I_hs(phs),.I_de(pde),.I_rgb(prgb),
      .I_detection_valid(1'b0),.I_pair(1'b0),.I_meta(256'd0),.I_x0(x0),.I_y0(y0),.I_zoom(zoom),.I_mode(active_mode),.I_state(3'd1),
      .I_show(1'b0),.I_tip_valid(1'b0),.I_video_ok(ok),.O_vs(ovs),.O_hs(ohs),.O_de(ode),.O_rgb(orgb));'''+s[end:]
s=s.replace('                if(oy==312 && ox==645 && orgb!==24\'hffff00) $fatal(1,"yellow crosshair");','')
s=s.replace('PASS scaling video:', 'PASS target video:')
bench=out/'tb_target_video.sv';bench.write_text(s,encoding='utf-8')
files=[bench,'rtl/05_roi_processing/target_line_reader.v','rtl/02_image_preprocess/image_preprocess.v','rtl/09_osd_ui/target_diagnostics.v','rtl/09_osd_ui/target_osd.v','rtl/09_osd_ui/target_glyph_rom.v','rtl/09_osd_ui/scaling_logo_rom.v']
c=subprocess.run([str(iv),'-g2012','-s','tb_target_video','-o',str(out/'video.vvp'),*[str(f) for f in files]],cwd=r,env=env,capture_output=True,text=True)
assert c.returncode==0,c.stdout+c.stderr
jobs=[(0,0,48,0,0,1),(1,13,37,0,0,1),(2,959,563,0,0,1)]
if not a.quick:jobs += [(z,0,0,m,0,1) for z in range(3) for m in (1,2,3)]+[(0,0,48,0,1,2),(0,0,48,0,2,3),(0,0,48,0,0,2)]
logs=[]
def work(job):
 z,x,y,m,f,n=job
 args=[vvp,out/'video.vvp',f'+ZOOM={z}',f'+X={x}',f'+Y={y}',f'+MODE={m}',f'+FAULT={f}',f'+FRAMES={n}']
 if f==0 and n==2:args+=['+DYNAMIC=1']
 p=subprocess.run([str(a) for a in args],cwd=r,env=env,capture_output=True,text=True,timeout=1200)
 return p.returncode,p.stdout+p.stderr
with ThreadPoolExecutor(max_workers=3) as pool:
 for code,text in pool.map(work,jobs):
  logs.append(text);print(text,flush=True);(r/'reports/candidate_video_simulation.log').write_text('\n'.join(logs),encoding='utf-8')
  assert code==0,text
(r/'reports/candidate_video_cases.json').write_text(json.dumps(jobs,indent=2)+'\n')
print('TARGET_VIDEO_TESTS_PASSED')
