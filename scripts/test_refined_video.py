"""Full source-pixel/mask/page reference with rational zoom and true reflection."""
from refined_testlib import R,run
import argparse,sys,json,hashlib
from concurrent.futures import ThreadPoolExecutor
ap=argparse.ArgumentParser();ap.add_argument('--full',action='store_true');ap.add_argument('--faults',action='store_true');ap.add_argument('--debug',type=int,choices=[0,1]);ap.add_argument('--reader',choices=['stable','refined'],default='refined');ap.add_argument('--workers',type=int,default=3);ap.add_argument('--reuse-current',action='store_true');ap.add_argument('--case-range',nargs=2,type=int);a=ap.parse_args()
# Reuse the independent colour/support oracle and timing fixture, with new output
# paths. Its power-of-two coordinate oracle below is replaced by rational maths.
legacy=R/'scripts/test_stable_video.py'
prefix=legacy.read_text(encoding='utf-8').split("tb=O/'tb_stable_video.sv'")[0]
prefix=prefix.replace("O=R/'build/sim/stable_video'",f"O=R/'build/sim/refined_video_{a.reader}'")
saved=sys.argv;sys.argv=[str(legacy)];scope={'__file__':str(legacy),'__name__':'refined_video_fixture'}
exec(compile(prefix,str(legacy),'exec'),scope);sys.argv=saved
s=scope['s'];oracle_dir=scope['O']
s=s.replace('stable_osd osd','refined_osd osd')
s=s.replace('stable_line_reader dut',a.reader+'_line_reader dut').replace(".I_meta(640'd0)",".I_meta(768'd0)")
s=s.replace("ok,1'(rarg));","ok,1'(rarg),1'b1,,,,32'd0,1'b0);")
s=s.replace('reg [1:0] zoom=0, mode=0;','reg [2:0] zoom=0;reg [1:0] mode=0;')
s=s.replace('.I_tracking(1\'b0),','.I_geometry_commit(commit),.I_tracking(1\'b0),')
for xx,yy in [('sxcount','sycount'),('ox','oy')]:
 oldx=f'expected_rotate?expected_x+(1280>>expected_z)-1-({xx}>>expected_z):expected_x+({xx}>>expected_z)'
 oldy=f'expected_rotate?expected_y+(624>>expected_z)-1-({yy}>>expected_z):expected_y+({yy}>>expected_z)'
 assert oldx in s and oldy in s,(xx,yy)
 s=s.replace(oldx,f'sample_x({xx})').replace(oldy,f'sample_y({yy})')
s=s.replace('    function [127:0] word_at',r'''    function integer ratio_p(input integer z);case(z)1,3:ratio_p=3;2:ratio_p=2;4:ratio_p=4;default:ratio_p=1;endcase endfunction
    function integer ratio_q(input integer z);ratio_q=z==1?2:1;endfunction
    function integer sample_x(input integer x);sample_x=expected_x+((expected_rotate?1279-x:x)*ratio_q(expected_z))/ratio_p(expected_z);endfunction
    function integer sample_y(input integer y);sample_y=expected_y+((expected_rotate?623-y:y)*ratio_q(expected_z))/ratio_p(expected_z);endfunction
    function [127:0] word_at''')
s=s.replace('x0=959;y0=563;zoom=2;','x0=959;y0=563;zoom=4;')
mods=[R/'rtl/color_regions'/f'{m}.v' for m in ('stable_line_reader','stable_model_lane','stable_filter4','stable_preprocess','stable_osd','stable_glyph_rom','stable_footer_glyph_rom','stable_footer_program_rom','stable_footer_text_rom','refined_overlay_geometry','refined_zoom_geometry','refined_reset_bridge','refined_logo_rom')]
mods += [R/'rtl/04_tracking/target_mailbox.v',R/'rtl/09_osd_ui/scaling_logo_rom.v']
mods=[R/'rtl/color_regions/refined_osd.v' if p.name=='stable_osd.v' else R/'rtl/color_regions/refined_footer_program_rom.v' if p.name=='stable_footer_program_rom.v' else p for p in mods]
mods += [R/'rtl/color_regions'/f'{n}.v' for n in ('refined_english_font_rom','refined_english_text_rom')]
mods=[R/f'rtl/color_regions/{a.reader}_line_reader.v' if p.name=='stable_line_reader.v' else p for p in mods]
origins=[(0,48),(101,99),(320,204),(787,400),(959,563)]
jobs=[(0,z,0,rot,0,1) for z in (0,1,3) for rot in (0,1)]
if a.full:jobs=[(pair,z,page,rot,0,1) for pair in (0,1) for z in range(5) for page in range(4) for rot in (0,1)]
if a.faults:
 fault_jobs=[(0,0,0,rot,1,2) for rot in (0,1)]+[(0,1,0,rot,0,2) for rot in (0,1)]
 jobs=jobs+fault_jobs if a.full else fault_jobs
if a.case_range is not None:
 first,last=a.case_range;assert 0<=first<last<=len(jobs);jobs=jobs[first:last]
if a.debug is not None:
 jobs=[(0,0,0,a.debug,0,1)]
 s=s.replace('            if(sde) begin', '''            if(sde && sycount==0 && sxcount<8)$display("VIDEO_DEBUG x%0d sx%0d sy%0d rgb%h q%h addr%0d good%0d ok%0d ready%b tag%0d mem0%h",sxcount,dut.sx,dut.sy,rgb,dut.pixel_q,dut.rgb_read_addr,dut.good,ok,dut.ready,dut.tags[0],dut.lines[0]);
            if(sde) begin''')
def execute(job):
 pair,z,page,rot,fault,frames=job;x,y=origins[z]
 name=f'{a.reader}_video_{pair}_{z}_{page}_{rot}_f{fault}_n{frames}'
 if a.reuse_current and a.debug is None:
  hashes={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in mods}
  for record in sorted((R/'reports/refined/regression').glob(name+'_*.json'),reverse=True):
   d=json.loads(record.read_text(encoding='utf-8'))
   recorded={n.replace('\\','/'):v for n,v in d.get('inputs',{}).items()}
   bench=__import__('pathlib').Path(d.get('output',''))/'tb.sv'
   if d.get('exit_code')==0 and not d.get('expected_failure') and hashes==recorded and bench.is_file() and bench.read_text(encoding='utf-8')==s and 'STABLE_VIDEO_PASS:' in record.with_suffix('.log').read_text(encoding='utf-8'):
    print('REFINED_VIDEO_REUSE_CURRENT',name,record.name,flush=True);return
 args=[f'+PAIR={pair}',f'+ZOOM={z}',f'+MODE={page}',f'+ROTATE={rot}',f'+X={x}',f'+Y={y}',f'+FAULT={fault}',f'+FRAMES={frames}',f'+MASK={(oracle_dir/f"masks_{pair}.hex").as_posix()}']
 if fault==0 and frames==2:args.append('+DYNAMIC=1')
 return run(name,s,mods,top='tb_stable_video',args=args,timeout=1800)
with ThreadPoolExecutor(max_workers=a.workers) as pool:list(pool.map(execute,jobs))
print('REFINED_VIDEO_ALL_PASS',len(jobs),'jobs',sum(j[-1] for j in jobs)*1280*624,'image pixels')
