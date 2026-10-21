"""Complete 96-row pixel oracle for region-mode and hidden critical messages."""
from refined_testlib import R,run
from stage1_test_sources import EXTRA_OSD
import re,json

def main():
    chars=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()'
    historical=json.loads((R/'assets/osd/anlogic/refined_ui_manifest.json').read_text(encoding='utf-8'))['characters']
    old={int(i):int(v,16) for i,v in re.findall(r"rom\[(\d+)\]=16'h([0-9a-f]+);",(R/'rtl/color_regions/stable_footer_glyph_rom.v').read_text())}
    font={c:[old[historical.index(c)*16+y]>>8 for y in range(16)] for c in chars}
    logo={int(i):int(v,16) for i,v in re.findall(r"mem\[(\d+)\]=2'h([0-9a-f]+);",(R/'rtl/color_regions/refined_logo_rom.v').read_text())}
    second='LAT 0012.3ms AGE 002 FR F:12345678 V:00AF'
    cases=[]
    def add(name,line,**kw):
        d=dict(name=name,mode=2,state=2,n=2,expected=1,actual=0,nd=0,occupied=1,distance=86,dwell=2500,trend=0,error=0,tip=1,show=1,muted=0,busy=0,line=line)
        d.update(kw);assert len(line)<=64,(name,len(line));cases.append(d)
    def edit(msg='TIP READY',dist='1234',n=2):return f"EDIT {'ABCD-'[n]} PTS 3/8 SAVE {n}/4 {msg:<16} D{dist}PX IN - T012.3s ST"
    def test(state,detail,occupied='A',dist='0086',target='B'):return f'{state:<8} NEXT {target} IN {occupied}  D{dist}PX T002.5s {"STABLE":<8} {detail:<17}'
    add('edit',edit(),mode=1,nd=3,occupied=0,distance=1234,dwell=12345,state=0)
    add('edit_cross',edit('SELF CROSS/ZERO'),mode=1,nd=3,occupied=0,distance=1234,dwell=12345,state=0,error=2)
    add('edit_no_area',edit('TIP READY','----',0),mode=1,n=0,nd=3,occupied=0,distance=0,dwell=12345,state=0)
    add('running',test('RUN','TIP READY'))
    add('waiting_geometry',test('RUN','BUSY',dist='----'),busy=1)
    add('wait_out',test('WAIT OUT','LEAVE ALL AREAS'),state=1)
    add('paused',test('PAUSED','KEY3 RESUME'),state=3)
    add('fail',test('FAIL','EXP B GOT C'),state=6,actual=3)
    add('fail_muted',test('FAIL','EXP B GOT C  MUTE'),state=6,actual=3,muted=1)
    add('hidden_fail','FAIL EXP B GOT C. KEY2 RETEST'.ljust(32)+'MUTE',state=6,actual=3,muted=1,show=0)
    add('hidden_pause','PAUSED. KEY3 RESUME',state=3,show=0)
    add('hidden_lost','INPUT LOST. KEY2 RETEST',state=7,show=0,tip=0)
    add('hidden_run','',state=2,show=0)
    out=R/'build/stage1_region_footer_vectors';out.mkdir(parents=True,exist_ok=True)
    paths=[]
    for i,d in enumerate(cases):
        pixels=[0x101824]*(1280*96)
        for row,line in enumerate([d['line'],second if d['show'] else '']):
            for col,c in enumerate(line.ljust(64)):
                for yy,bits in enumerate(font[c]):
                    for xx in range(8):
                        if bits>>(7-xx)&1:pixels[((16 if row==0 else 60)+yy)*1280+16+col*8+xx]=0xf0f4ff
        palette=[0,0x1c2c4e,0xed1b23,0xe0e8f4]
        for yy in range(64):
            for xx in range(98):
                if logo[yy*98+xx]:pixels[(16+yy)*1280+1167+xx]=palette[logo[yy*98+xx]]
        path=out/f'{i}.hex';path.write_text(''.join(f'{p:06x}\n' for p in pixels));paths.append(path)
    source=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,de=0;reg [767:0] meta=0;
reg [1:0] umode=1,trend=0;reg [3:0] state=0,nd=3,occupied=0,error=0;
reg [2:0] n=2,target=1,actual=0;reg [10:0] distance=1234;reg [19:0] dwell=12345;reg tip=1,show=1,muted=0,busy=0;
wire vs,hs,ode;wire [23:0] rgb;
stage1_osd dut(umode,672'd0,16'd0,4'd0,n,target,actual,nd,state,4'd0,occupied,muted,trend,distance,dwell,error,4'd0,busy,tip,1'b0,1'b0,3'd5,
clk,rst,1'b0,1'b0,de,24'h123456,meta,11'd0,10'd0,3'd2,2'd1,3'd2,1'b1,show,1'b1,1'b0,1'b1,1'b1,
vs,hs,ode,rgb,1'b1,2'd0,32'h12345678,1'b0,1'b1,32'd12345,32'd2,128'd0,128'd0,39'd0,18'd0);
reg [23:0] expected[0:122879];integer c,x,y,outn;reg checking=0;
always @(posedge clk)begin #1;if(checking && ode)begin
if(rgb!==expected[outn])$fatal(1,"region footer c%0d pixel%0d got%h expected%h",c,outn,rgb,expected[outn]);outn=outn+1;end end
task frame;begin
@(negedge clk);de=0;rst=0;checking=0;repeat(3)@(negedge clk);rst=1;
@(negedge clk);dut.y=620;dut.x=0;outn=0;
for(y=620;y<720;y=y+1)for(x=0;x<1280;x=x+1)begin
@(negedge clk);de=1;if(y==624 && x==1)checking=1;
if(y==640 && x==0 && !dut.footer_ready)$fatal(1,"region formatter deadline");end
@(negedge clk);de=0;repeat(4)@(negedge clk);checking=0;
if(outn!=122880)$fatal(1,"footer length");end endtask
initial begin meta[255]=1;meta[247]=1;meta[415:413]=4;meta[559:544]=16'h00af;
'''
    for i,(d,path) in enumerate(zip(cases,paths)):
        names={'mode':'umode','expected':'target'}
        source+=f'c={i};'+''.join(f"{names.get(k,k)}={v};" for k,v in d.items() if k not in ('name','line'))
        source+=f'$readmemh("{path.as_posix()}",expected);frame;$display("REGION_FOOTER_CASE_PASS {d["name"]}");\n'
    source+=f'$display("STAGE1_REGION_FOOTER_PASS cases={len(cases)} pixels={len(cases)*122880}");$finish;end endmodule'
    mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('stage1_osd','refined_english_font_rom','refined_english_text_rom','refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry')]
    run('stage1_region_footer',source,mods+EXTRA_OSD,timeout=600)

if __name__=='__main__':main()
