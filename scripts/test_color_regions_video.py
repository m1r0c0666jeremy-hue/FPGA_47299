"""Actual functional reader/pages/footer under complete HDMI timing and DDR stalls."""
from pathlib import Path
import os,subprocess,json,argparse
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parents[1];O=R/'build/sim/color_regions/video';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
p=argparse.ArgumentParser();p.add_argument('--quick',action='store_true');a=p.parse_args()
s=(R/'sim/tb_scaling_video.sv').read_text(encoding='utf-8').replace('tb_scaling_video','tb_color_regions_video')
s=s.replace('    scaling_line_reader dut(','''    reg commit=0,vs_prev=0;integer countdown=0;
    always @(posedge pc)begin
      vs_prev<=vs;commit<=0;
      if(vs&&!vs_prev)countdown<=20;
      else if(countdown>0)begin countdown<=countdown-1;if(countdown==1)commit<=1;end
    end
    regions_line_reader dut(commit,1'b1,''').replace('wrbusy,wren,read_buffer,ready','wrbusy,wren,read_buffer,32\'d123,ready')
s=s.replace('image_preprocess process(pc,rst,mode,','regions_preprocess process(pc,rst,mode,1\'b0,')
start=s.index('    scaling_osd osd(');end=s.index('\n',start)
s=s[:start]+'''    regions_osd osd(.I_clk(pc),.I_rst_n(rst),.I_vs(pvs),.I_hs(phs),.I_de(pde),.I_rgb(prgb),
      .I_detection_valid(1'b0),.I_sample_valid(1'b0),.I_pair(1'b0),.I_meta(416'd0),.I_x0(x0),.I_y0(y0),.I_zoom(zoom),.I_mode(active_mode),.I_state(3'd1),
      .I_show(1'b0),.I_video_ok(ok),.O_vs(ovs),.O_hs(ohs),.O_de(ode),.O_rgb(orgb));'''+s[end:]
s=s.replace("orgb!==24'h102030","orgb!==24'h101824")
s=s.replace('                if(oy==312 && ox==645 && orgb!==24\'hffff00) $fatal(1,"yellow crosshair");','')
# Independent hue formula (real arithmetic is testbench only), covers display-only RGB.
func='''
    function [23:0] page_pixel(input [23:0] rgb,input integer md);
    integer r,g,b,m,n,d,gray;real hue;reg red,blue;
    begin
      r=rgb[23:16];g=rgb[15:8];b=rgb[7:0];m=r>g?r:g;if(b>m)m=b;
      n=r<g?r:g;if(b<n)n=b;d=m-n;hue=0;red=0;blue=0;
      if(d!=0)begin
        if(m==r)hue=60.0*(g-b)/d;else if(m==g)hue=120.0+60.0*(b-r)/d;else hue=240.0+60.0*(r-g)/d;
        if(hue<0)hue=hue+360.0;
        if(m>=24 && d>=8 && 16*d>=3*m)begin red=hue<30.0 || hue>=345.0;blue=hue>=195.0 && hue<255.0;end
      end
      gray=(r+2*g+b+2)/4;
      case(md)
       0:page_pixel=rgb;
       1:begin gray=gray/4;page_pixel=red?24'hFF6060:blue?24'h6090FF:{8'(gray),8'(gray),8'(gray)};end
       2:page_pixel={8'(gray),8'(gray),8'(gray)};
       3:page_pixel=red||blue?24'hFFFFFF:0;
      endcase
    end endfunction
'''
s=s.replace('    function [127:0] word_at',func+'    function [127:0] word_at')
s=s.replace('                if(oy>=624) osd_count=osd_count+1;', '''                if(oy<624 && fault==0 && orgb!==page_pixel(pixel(expected_x+(ox>>expected_z),expected_y+(oy>>expected_z)),marg))
                   $fatal(1,"functional page mismatch mode=%d x=%d y=%d got=%h",marg,ox,oy,orgb);
                if(oy>=624) osd_count=osd_count+1;''')
s=s.replace('PASS scaling video:','PASS functional video:');bench=O/'tb_color_regions_video.sv';bench.write_text(s,encoding='utf-8')
files=[bench,*[R/f'rtl/color_regions/regions_{n}.v' for n in ['line_reader','classifier','preprocess','osd','glyph_rom']]]
c=subprocess.run([str(iv),'-g2012','-s','tb_color_regions_video','-o',str(O/'video.vvp'),*map(str,files)],cwd=R,env=env,capture_output=True,text=True)
assert c.returncode==0,c.stdout+c.stderr
jobs=[(0,0,48,0,0,1)] if a.quick else [(z,0 if z==0 else 320 if z==1 else 480,48 if z==0 else 204 if z==1 else 282,m,0,1) for z in range(3) for m in range(4)]+[(0,0,48,0,1,2),(0,0,48,0,2,3),(0,0,48,0,0,2)]
def run(job):
 z,x,y,m,f,n=job;args=[iv.with_name('vvp.exe'),O/'video.vvp',f'+ZOOM={z}',f'+X={x}',f'+Y={y}',f'+MODE={m}',f'+FAULT={f}',f'+FRAMES={n}']
 if f==0 and n==2:args+=['+DYNAMIC=1']
 p=subprocess.run(list(map(str,args)),cwd=R,env=env,capture_output=True,text=True,timeout=1200);return p.returncode,p.stdout+p.stderr
logs=[]
with ThreadPoolExecutor(max_workers=3) as pool:
 for code,text in pool.map(run,jobs):
  logs.append(text);print(text,flush=True);(R/'reports/color_regions_video.log').write_text('\n'.join(logs),encoding='utf-8');assert code==0,text
(R/'reports/color_regions_video_cases.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
print('COLOR_REGIONS_VIDEO_PASSED')
