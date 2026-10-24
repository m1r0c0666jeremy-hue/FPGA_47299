from pathlib import Path
"""Independent full RGB oracle: region edges, font, label avoidance and hide.

Only archived font bitmaps and rational source geometry form the expected pixels;
no candidate internal signals are used to calculate the oracle.
"""
from refined_testlib import R,run
import hashlib
from stage1_test_sources import EXTRA_OSD
from test_stage1_render import mapped,ceil
from fractions import Fraction
import json,re

def main():
    chars=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()'
    historical=json.loads((R/'assets/osd/anlogic/refined_ui_manifest.json').read_text(encoding='utf-8'))['characters']
    old={int(i):int(v,16) for i,v in re.findall(r"rom\[(\d+)\]=16'h([0-9a-f]+);",(R/'rtl/color_regions/stable_footer_glyph_rom.v').read_text())}
    font={c:[old[historical.index(c)*16+y]>>8 for y in range(16)] for c in chars}
    polys=[[(10,10),(30,40)],[(35,10),(55,40)],[(60,10),(80,40)],[(1230,600),(1250,620)]]
    packed=sum((x|(y<<11))<<(21*(8*r+k)) for r,p in enumerate(polys) for k,(x,y) in enumerate(p))
    cases=[(0,0,2,1),(0,1,2,1),(1,0,2,1),(1,1,2,1),(4,0,2,1),(4,1,2,1),(0,0,6,1),(0,1,6,0)]
    out=R/'build'/('stage1_rect_overlay_vectors_'+hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]);out.mkdir(parents=True,exist_ok=True)
    labels=[]
    for case,(zoom,rot,state,show) in enumerate(cases):
        rgb=[0x203040|(y%256)<<8|(x%256) for y in range(624) for x in range(1280)]
        mapped_polys=[[(mapped(x,0,zoom,rot,1280),mapped(y,0,zoom,rot,624)) for x,y in p] for p in polys]
        mapped_polys=[[(min(x for x,y in p),min(y for x,y in p)),(max(x for x,y in p),min(y for x,y in p)),(max(x for x,y in p),max(y for x,y in p)),(min(x for x,y in p),max(y for x,y in p))] for p in mapped_polys]
        colors=[0xff4050 if state==6 and r==0 else 0x40ff90 if r==0 else 0xffe040 if state==2 and r==1 else 0x9098a0 for r in range(4)]
        positions=[]
        for r,p in enumerate(mapped_polys):
            if show:
                for (ax,ay),(bx,by) in zip(p,p[1:]+p[:1]):
                    if by<ay:ax,bx,ay,by=bx,ax,by,ay
                    for y in range(max(0,ay),min(623,by)+1):
                        if ay==by:low,high=min(ax,bx),max(ax,bx)
                        else:
                            u=Fraction(2*ax)+Fraction((bx-ax)*((2*ay if y==ay else 2*y-1)-2*ay),by-ay)
                            v=Fraction(2*ax)+Fraction((bx-ax)*((2*by if y==by else 2*y+1)-2*ay),by-ay)
                            low=ceil((min(u,v)-1)/2);high=(max(u,v)+1)//2
                        for x in range(max(0,low),min(1279,high)+1):rgb[y*1280+x]=colors[r]
            valid=max(x for x,y in p)>=0 and min(x for x,y in p)<1280 and max(y for x,y in p)>=0 and min(y for x,y in p)<624
            x,y=p[0];x=max(0,min(1232,x));y=(608 if y>626 else y-18) if y>=18 else (0 if y< -3 else y+3)
            up=y>304
            for attempt in range(36):
                if not valid or not any(v and x<px+50 and x+50>px and y<py+18 and y+18>py for px,py,v in positions):break
                if up and y>=18:y-=18
                elif not up and y<=590:y+=18
                else:up=not up;x=x-64 if x>=64 else x+64
            else:raise AssertionError('label allocation exhausted')
            positions.append((x,y,valid))
        for r,(x,y,valid) in enumerate(positions):
            if not (valid and show):continue
            for yy in range(16):
                for dx in range(48):
                    c=('AREA '+chr(65+r))[dx//8]
                    rgb[(y+yy)*1280+x+dx]=colors[r] if font[c][yy]>>(7-dx%8)&1 else 0x101824
        (out/f'{case}.hex').write_text(''.join(f'{v:06x}\n' for v in rgb))
        labels.append(positions)
    (out/'labels.json').write_text(json.dumps(labels,indent=2))
    src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,commit=0,de=0,vs=0,show=1,rot=0;reg [2:0] zoom=0;reg [3:0] state=2;
reg [23:0] raw=0;wire ovs,ohs,ode;wire [23:0] rgb;
stage1_osd dut(2'd2,672'hVERTICES,168'd0,16'h2222,4'hf,3'd4,3'd1,3'd1,4'd0,state,4'd1,4'd0,1'b0,2'd0,11'd0,20'd0,4'd0,4'd0,1'b0,1'b1,1'b0,1'b0,3'd5,
clk,rst,vs,1'b0,de,raw,768'd0,11'd0,10'd0,zoom,2'd0,3'd0,1'b0,show,1'b1,1'b0,1'b0,1'b0,
ovs,ohs,ode,rgb,rot,2'd0,32'd0,commit,1'b0,32'd0,32'd0,128'd0,128'd0,39'd0,18'd0);
reg [23:0] expected[0:798719];reg [23:0] e0=0,e1=0;reg v0=0,v1=0,checking=0;integer c,y,h,index=0,pixels=0;
always @(posedge clk)begin
if(de)begin e0<=expected[index];index=index+1;end
e1<=e0;v0<=de;v1<=v0;#1;
if(checking && (ode!==v1 || (v1 && rgb!==e1)))$fatal(1,"overlay c%0d input%0d/%0d index%0d got%h expected%h de%b/%b",c,h,y,index,rgb,e1,ode,v1);
if(checking && v1)pixels=pixels+1;
end
task frame;begin
checking=0;de=0;rst=0;repeat(3)@(negedge clk);rst=1;vs=1;@(negedge clk);vs=0;commit=1;@(negedge clk);commit=0;
repeat(10000)@(negedge clk);if(!dut.region_ready || dut.region_underrun)$fatal(1,"overlay preparation");
index=0;checking=1;
for(y=0;y<624;y=y+1)for(h=0;h<1650;h=h+1)begin
@(negedge clk);de=h<1280;raw=24'h203040|((y%256)<<8)|(h%256);end
@(negedge clk);de=0;repeat(3)@(negedge clk);checking=0;
if(index!=798720)$fatal(1,"input pixel count");end endtask
initial begin
'''.replace('VERTICES',f'{packed:x}')
    for i,(z,r,s,sh) in enumerate(cases):
        src+=f'c={i};zoom={z};rot={r};state={s};show={sh};$readmemh("{(out/f"{i}.hex").as_posix()}",expected);frame;$display("STAGE1_OVERLAY_CASE_PASS c{i}");\n'
    src+=f'$display("STAGE1_OVERLAY_PASS cases={len(cases)} pixels=%0d",pixels);$finish;end endmodule'
    mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('stage1_osd','refined_english_font_rom','refined_english_text_rom','refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry')]
    run('stage1_overlay',src,mods+EXTRA_OSD,timeout=1800)

if __name__=='__main__':main()
