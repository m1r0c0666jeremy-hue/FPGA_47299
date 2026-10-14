"""Full HDMI timing, supported source masks, both pairs/pages/zooms and DDR stalls."""
from pathlib import Path
import os,subprocess,argparse,json
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parents[1];O=R/'build/sim/stable_video';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
p=argparse.ArgumentParser();p.add_argument('--rotate',type=int,choices=[0,1]);p.add_argument('--quick',action='store_true');p.add_argument('--pair',type=int,choices=[0,1]);a=p.parse_args()
def classify(x,y,pair):
    if x<0 or x>=1280 or y<0 or y>=720:return 0
    r=x&255;g=y&255;b=((x>>8)*64+(y>>8)*16+((x^y)&15))&255;m=max(r,g,b);d=m-min(r,g,b)
    if m<32 or d<16 or 4*d<m:return 0
    if m==r:n=60*(g-b);n=n+360*d if n<0 else n
    elif m==g:n=120*d+60*(b-r)
    else:n=240*d+60*(r-g)
    if pair:return int(45*d<=n<75*d)+2*int(255*d<=n<330*d)
    return int(n<30*d or n>=345*d)+2*int(195*d<=n<255*d)
for pair in (0,1):
    file=O/f'masks_{pair}.hex'
    if not file.exists():
        raw=bytearray(classify(x,y,pair) for y in range(720) for x in range(1280))
        supported=bytearray(len(raw))
        for y in range(720):
            for x in range(1280):
                n=y*1280+x;v=raw[n]
                if not v:continue
                neighbors=0
                for yy in range(max(0,y-1),min(720,y+2)):
                    for xx in range(max(0,x-1),min(1280,x+2)):
                        if xx!=x or yy!=y:neighbors|=raw[yy*1280+xx]
                supported[n]=v&neighbors
        file.write_text('\n'.join(f'{v:x}' for v in supported),encoding='ascii')
        print('SOURCE_MASK_ORACLE',pair,flush=True)
s=(R/'sim/tb_scaling_video.sv').read_text(encoding='utf-8').replace('tb_scaling_video','tb_stable_video')
s=s.replace('integer zarg=0,','integer rarg=0,parg=0,zarg=0,')
s=s.replace('    scaling_line_reader dut(','''    reg commit=0,vs_prev=0;integer countdown=0;
    wire [1:0] source_mask;reg [127:0] models;
    function [63:0] model(input integer lo,hi);begin model=(64'h8000000000000000)|(64'(lo)<<54)|(64'(hi)<<45)|(64'd32<<37)|(64'd16<<29)|(64'd1<<27);end endfunction
    reg [1:0] mask_reference[0:921599];reg [1023:0] mask_path;
    always @(posedge pc)begin vs_prev<=vs;commit<=0;
      if(vs&&!vs_prev)countdown<=20;
      else if(countdown>0)begin countdown<=countdown-1;if(countdown==1)commit<=1;end end
    stable_line_reader dut(commit,1'b1,''').replace('wrbusy,wren,read_buffer,ready','wrbusy,wren,read_buffer,32\'d123,models,ready').replace('sde,rgb,ok);',"sde,rgb,source_mask,ok,1'(rarg));")
s=s.replace('image_preprocess process(pc,rst,mode,','stable_preprocess process(pc,rst,mode,1\'(parg),').replace('sde,rgb,pvs','sde,rgb,source_mask,pvs')
start=s.index('    scaling_osd osd(');end=s.index('\n',start)
s=s[:start]+'''    stable_osd osd(.I_clk(pc),.I_rst_n(rst),.I_vs(pvs),.I_hs(phs),.I_de(pde),.I_rgb(prgb),
      .I_tracking(1'b0),.I_detection_valid(1'b0),.I_sample_valid(1'b0),.I_pair(1'(parg)),.I_meta(640'd0),.I_x0(x0),.I_y0(y0),.I_zoom(zoom),.I_mode(active_mode),.I_state(3'd1),
      .I_rotate(1'(rarg)),.I_diag(2'd0),.I_image_id(32'd123),.I_show(1'b0),.I_video_ok(ok),.O_vs(ovs),.O_hs(ohs),.O_de(ode),.O_rgb(orgb));'''+s[end:]
s=s.replace('vs_delay[8],hs_delay[8],de_delay[8]','vs_delay[4],hs_delay[4],de_delay[4]').replace("orgb!==24'h102030","orgb!==24'h101824")
s=s.replace('                if(oy==312 && ox==645 && orgb!==24\'hffff00) $fatal(1,"yellow crosshair");','')
s=s.replace('PASS scaling video:','STABLE_VIDEO_PASS:')
s=s.replace('    function [127:0] word_at','''    function [23:0] page_pixel(input [23:0] rgb,input integer md,input [1:0] mask);
integer gray;begin gray=(rgb[23:16]+2*rgb[15:8]+rgb[7:0]+2)/4;
case(md)0:page_pixel=rgb;1:begin gray=gray/4;page_pixel=mask[0]?(parg?24'hffff40:24'hff6060):mask[1]?(parg?24'he080ff:24'h6090ff):{8'(gray),8'(gray),8'(gray)};end
2:page_pixel={8'(gray),8'(gray),8'(gray)};3:page_pixel=mask!=0?24'hffffff:0;endcase end endfunction
    function [127:0] word_at''')
s=s.replace('                    checked=checked+1;','''                    if(fault==0 && source_mask!==mask_reference[(expected_y+(sycount>>expected_z))*1280+expected_x+(sxcount>>expected_z)])
                      $fatal(1,"source mask mismatch xy%0d/%0d got%h",sxcount,sycount,source_mask);
                    checked=checked+1;''')
s=s.replace('                if(oy>=624) osd_count=osd_count+1;','''                if(oy<624 && fault==0 && orgb!==page_pixel(pixel(expected_x+(ox>>expected_z),expected_y+(oy>>expected_z)),marg,
                  mask_reference[(expected_y+(oy>>expected_z))*1280+expected_x+(ox>>expected_z)]))$fatal(1,"page mismatch mode%0d xy%0d/%0d got%h",marg,ox,oy,orgb);
                if(oy>=624) osd_count=osd_count+1;''')
s=s.replace('        zoom=zarg;','''        if($value$plusargs("PAIR=%d",parg))begin end
        if($value$plusargs("MASK=%s",mask_path))begin end
        $readmemh(mask_path,mask_reference);
        models=parg?{model(255,330),model(45,75)}:{model(195,255),model(345,30)};
        zoom=zarg;''')
s=s.replace('integer expected_x=','integer expected_rotate=0,expected_x=')
s=s.replace('expected_x=x0;', 'expected_rotate=rarg;expected_x=x0;')
s=s.replace('pixel(expected_x+(sxcount>>expected_z),expected_y+(sycount>>expected_z))','pixel(expected_rotate?expected_x+(1280>>expected_z)-1-(sxcount>>expected_z):expected_x+(sxcount>>expected_z),expected_rotate?expected_y+(624>>expected_z)-1-(sycount>>expected_z):expected_y+(sycount>>expected_z))')
s=s.replace('pixel(expected_x+(ox>>expected_z),expected_y+(oy>>expected_z))','pixel(expected_rotate?expected_x+(1280>>expected_z)-1-(ox>>expected_z):expected_x+(ox>>expected_z),expected_rotate?expected_y+(624>>expected_z)-1-(oy>>expected_z):expected_y+(oy>>expected_z))')
for xx,yy in [('sxcount','sycount'),('ox','oy')]:
    s=s.replace(f'(expected_y+({yy}>>expected_z))*1280+expected_x+({xx}>>expected_z)',f'(expected_rotate?expected_y+(624>>expected_z)-1-({yy}>>expected_z):expected_y+({yy}>>expected_z))*1280+(expected_rotate?expected_x+(1280>>expected_z)-1-({xx}>>expected_z):expected_x+({xx}>>expected_z))')
s=s.replace('.I_rotate(1\'(rarg)),.I_diag', '.I_rotate(1\'(expected_rotate)),.I_diag')
s=s.replace('x0=959;y0=563;zoom=2;read_buffer=3;', 'x0=959;y0=563;zoom=2;read_buffer=3;rarg=1-rarg;')
s=s.replace('zoom=zarg;','if($value$plusargs("ROTATE=%d",rarg))begin end\n        zoom=zarg;')
# The rightmost footer is the white logo panel.
s=s.replace('if(oy==640 && orgb!==24\'h101824)', 'if(oy==640 && ox<1152 && orgb!==24\'h101824)')
tb=O/'tb_stable_video.sv' ;tb.write_text(s,encoding='utf-8')
modules=['stable_line_reader','stable_model_lane','stable_filter4','stable_preprocess','stable_osd','stable_glyph_rom','stable_footer_glyph_rom','stable_footer_program_rom','stable_footer_text_rom']
q=subprocess.run([str(iv),'-g2012','-s','tb_stable_video','-o',str(O/'video.vvp'),str(tb),*[str(R/f'rtl/color_regions/{m}.v') for m in modules],str(R/'rtl/04_tracking/target_mailbox.v'),str(R/'rtl/09_osd_ui/scaling_logo_rom.v')],cwd=R,env=env,capture_output=True,text=True)
if q.returncode:raise SystemExit(q.stdout+q.stderr)
pairs=[a.pair] if a.pair is not None else [0,1]
jobs=[(pairs[0],0,0,48,0,0,1)] if a.quick else [(pair,z,0 if z==0 else 320 if z==1 else 480,48 if z==0 else 204 if z==1 else 282,m,0,1) for pair in pairs for z in range(3) for m in range(4)]+[(0,0,0,48,0,1,2),(0,0,0,48,0,2,3),(0,0,0,48,0,0,2),(1,2,960,564,1,0,1)]
jobs=[j+(rot,) for j in jobs for rot in ([a.rotate] if a.rotate is not None else [0,1])]
def run(job):
    pair,z,x,y,m,f,n,rot=job
    cmd=[str(iv.with_name('vvp.exe')),str(O/'video.vvp'),f'+ROTATE={rot}',f'+PAIR={pair}',f'+MASK={(O/f"masks_{pair}.hex").as_posix()}',f'+ZOOM={z}',f'+X={x}',f'+Y={y}',f'+MODE={m}',f'+FAULT={f}',f'+FRAMES={n}']
    if f==0 and n==2:cmd+=['+DYNAMIC=1']
    result=subprocess.run(cmd,cwd=R,env=env,capture_output=True,text=True,timeout=1200)
    return job,result.returncode,result.stdout+result.stderr
logs=[]
with ThreadPoolExecutor(max_workers=3) as pool:
    for job,code,log in pool.map(run,jobs):
        logs.append(str(job)+'\n'+log);print(log,flush=True)
        (R/'reports/transparent_ring/regression/stable_video.log').write_text('\n'.join(logs),encoding='utf-8')
        if code:raise SystemExit(code)
(R/'reports/transparent_ring/regression/stable_video_cases.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
print('STABLE_VIDEO_ALL_PASS',flush=True)
