"""Independent English text/pixel oracle and late-abort sampling checks."""
from refined_testlib import R,run
import argparse,hashlib,json,re,zipfile
from PIL import Image

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--abort',action='store_true');ap.add_argument('--wait',action='store_true');a=ap.parse_args();assert not(a.abort and a.wait)
    manifest=json.loads((R/'assets/osd/anlogic/english_ui_manifest.json').read_text())
    chars=manifest['characters'];ids={c:i for i,c in enumerate(chars)}
    assert len(chars)<=64 and manifest['font_width']==8 and manifest['font_height']==16
    base=json.loads((R/'reports/refined/osd_memory_baseline.json').read_text())
    with zipfile.ZipFile(R/base['archive']) as z:
        oldchars=json.loads(z.read('assets/osd/anlogic/refined_ui_manifest.json'))['characters']
        oldfont={int(i):int(v,16) for i,v in re.findall(r"rom\[(\d+)\]=16'h([0-9a-f]+);",z.read('rtl/color_regions/stable_footer_glyph_rom.v').decode())}
        logo={int(i):int(v,16) for i,v in re.findall(r"mem\[(\d+)\]=2'h([0-9a-f]+);",z.read('rtl/color_regions/refined_logo_rom.v').decode())}
    font={c:[oldfont[oldchars.index(c)*16+y]>>8 for y in range(16)] for c in chars}
    actual=[int(v,16) for _,v in re.findall(r"mem\[(\d+)\]=8'h([0-9a-f]+);",(R/'rtl/color_regions/refined_english_font_rom.v').read_text())]
    assert actual[:len(chars)*16]==[v for c in chars for v in font[c]],'Font differs from delivered bitmap'
    out=R/'build/sim/osd_memory_ui';out.mkdir(parents=True,exist_ok=True)
    # Expected strings are the user-facing contract, independent of ROM tokens.
    states=['IDLE','CENTER SELECT','CONFIRMING','TRACKING','MISSING COLOR','HOLD LOST','RESELECT CENTER','TIP OUT OF VIEW','INVALID FRAME','CAL WHITE','CAL BACKGROUND','CAL A','CAL B','PROCESSING','SAMPLE FAILED','RECALIBRATE','VIDEO NOT READY','KEY CONFLICT','NO NEW FRAME','WAIT RESULT']
    errors=['','INVALID FRAME','POOR WHITE PAPER','GAIN OUT OF RANGE','MIXED/FEW SAMPLES','MODELS OVERLAP','BG NOT SEPARABLE','LOW MATERIAL KEEP','TOO MANY DARK PIX','BRIGHTNESS CHANGED','WEAK COLOR CONTRAST','HUE FAMILY MISMATCH','TOO FEW VALID PIX']
    helptext=['','WHITE PAPER IN CENTER. KEY3:SAMPLE KEY2:CANCEL','REMOVE MARKERS. AIM AT INTERFERENCE. KEY3:SAMPLE KEY2:CANCEL','A NEAR TIP IN CENTER. KEY3:SAMPLE KEY2:CANCEL','B REAR COLOR IN CENTER. KEY3:SAMPLE KEY2:CANCEL']
    def overview(status='TRACKING',mode='HILITE',zoom='2X  ',pair='R/B',direction='180',model='LEARNED',valid=True,latency='0012.3',age='002'):
        return [f'{mode:<8} {zoom} {pair} {direction} STATE:{status:<16} {model:<8}',f'LAT {latency}ms AGE {age} FR F:12345678 V:'+('00AF' if valid else '----')]
    def calibration(status,second,error=0):return [f'CAL:{status:<16} E{error:02X} F:12345678 V:00AF',second]
    # name, tracker status, calibration phase, busy, error, dirty, controls state,
    # tracking, video, meta-valid, frame-valid, zoom, mode, pair, rotate, latency-valid, latency, age, lines
    cases=[]
    def case(name,lines,**kw):
        d=dict(name=name,ts=3,phase=0,busy=0,error=0,dirty=0,control=2,tracking=1,video=1,mvalid=1,fvalid=1,zoom=2,mode=1,pair=0,rotate=1,lv=1,latency=12345,age=2,lines=lines);d.update(kw);cases.append(d)
    for diag in range(4):case('overview'+str(diag),overview())
    for i,status in enumerate(states):
        if i in range(9,13):case('state'+str(i),calibration(status,helptext[i-8]),phase=i-8)
        elif i==13:case('state13',calibration(status,'SAMPLING 8 FRAMES/PROCESSING. HOLD STILL. KEY2:CANCEL'),phase=2,busy=1)
        elif i==14:case('state14',calibration(status,'BG NOT SEPARABLE KEY3:RETRY KEY2:CANCEL',6),phase=3,error=6)
        else:
            kw={}
            if i==0:kw['tracking']=0
            elif i<=8:kw['ts']=i
            elif i==15:kw['dirty']=1
            elif i==16:kw['video']=0
            elif i==17:kw['control']=5
            elif i==18:kw['control']=7
            elif i==19:kw['mvalid']=0
            if i==8:kw['fvalid']=0
            case('state'+str(i),overview(status,valid=i!=19),**kw)
    for error in range(1,13):case('error'+str(error),calibration('SAMPLE FAILED',errors[error]+' KEY3:RETRY KEY2:CANCEL',error),phase=3,error=error)
    for z,zoom in enumerate(['1X  ','1.5X','2X  ','3X  ','4X  ']):case('zoom'+str(z),overview(zoom=zoom,mode='MASK',pair='Y/P',direction='000'),zoom=z,mode=3,pair=1,rotate=0)
    case('invalid_numbers',overview(latency='----.-',age='---'),lv=0)
    case('out_of_range',overview(latency='----.-',age='---'),latency=10000000,age=1000)
    case('zero',overview(latency='0000.0',age='000'),latency=0,age=0)
    case('maximum',overview(latency='9999.9',age='999'),latency=9999999,age=999)
    if a.abort:
        cases=[]
        case('late_abort',overview(latency='----.-',age='---'))
        case('last_pixel_abort',overview(latency='----.-',age='---'))
    if a.wait:
        cases=[]
        case('wait_transition',['WAIT RESULT',''])
    palette=[0x101824,0x1c2c4e,0xed1b23,0xe0e8f4]
    expected_files=[]
    for n,d in enumerate(cases):
        pixels=[0x101824]*(1280*96)
        for row,line in enumerate(d['lines']):
            assert len(line)<=64,(d['name'],len(line))
            for col,c in enumerate(line):
                for yy,bits in enumerate(font[c]):
                    for xx in range(8):
                        if bits&(1<<(7-xx)):pixels[(16+row*44+yy)*1280+16+col*8+xx]=0xf0f4ff
        for yy in range(64):
            for xx in range(98):
                v=logo[yy*98+xx]
                if v:pixels[(16+yy)*1280+1167+xx]=palette[v]
        p=out/(('abort_' if a.abort else 'wait_' if a.wait else '')+str(n)+'.hex');p.write_text(''.join(f'{v:06x}\n' for v in pixels),encoding='ascii');expected_files.append(p)
        if n in (0,29,36):
            im=Image.new('RGB',(1280,96));im.putdata([(v>>16,(v>>8)&255,v&255) for v in pixels]);im.save(out/(d['name']+'.png'))
    src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,de=0;reg [767:0] meta=0;
reg [2:0] zoom=2,control=2;reg [1:0] mode=1,diag=0;reg pair=0,rotate=1,tracking=1,video=1,lv=1;
reg [31:0] latency=12345,age=2;wire vs,hs,ode;wire [23:0] rgb;
refined_osd dut(clk,rst,1'b0,1'b0,de,24'h123456,meta,11'd0,10'd0,zoom,mode,control,tracking,1'b1,video,pair,1'b1,1'b1,vs,hs,ode,rgb,rotate,diag,32'h12345678,1'b0,lv,latency,age,128'd0,128'd0,39'd0,18'd0);
reg [23:0] expected[0:122879];integer c,x,y,n,outn=0;reg checking=0;
always @(posedge clk)begin #1;if(checking && ode)begin
if(rgb!==expected[outn])$fatal(1,"English footer case%0d pixel%0d got%h expected%h",c,outn,rgb,expected[outn]);outn=outn+1;end end
task frame;begin
@(negedge clk);de=0;rst=0;checking=0;repeat(3)@(negedge clk);rst=1;
@(negedge clk);dut.y=620;dut.x=0;outn=0;
for(y=620;y<720;y=y+1)for(x=0;x<1280;x=x+1)begin
@(negedge clk);de=1;if(y==624 && x==1)checking=1;
ABORT_EVENT
if(y==640 && x==0 && !dut.footer_ready)$fatal(1,"formatter deadline");end
@(negedge clk);de=0;repeat(4)@(negedge clk);checking=0;
if(outn!=122880)$fatal(1,"English footer count %0d",outn);end endtask
initial begin
'''
    src=src.replace('ABORT_EVENT', 'if((c==0 && y==622 && x==0)||(c==1 && y==624 && x==2))lv=0;' if a.abort else 'if(y==630 && x==0)tracking=0;' if a.wait else '')
    for n,(d,p) in enumerate(zip(cases,expected_files)):
        values={'ts':(33,4),'phase':(565,3),'busy':(564,1),'error':(560,4),'dirty':(568,1),'mvalid':(255,1),'fvalid':(247,1)}
        meta=(4<<413)|(1<<721)|(0xaf<<544)
        for k,(lo,w) in values.items():meta|=d[k]<<lo
        src+=f"c={n};meta=768'h{meta:0192x};diag={n%4};"+''.join(f'{k}={d[k]};' for k in ('zoom','mode','pair','rotate','control','tracking','video','lv','latency','age'))
        src+=f'$readmemh("{p.as_posix()}",expected);frame;$display("ENGLISH_UI_CASE_PASS {d["name"]}");\n'
    prefix='osd_english_abort' if a.abort else 'osd_english_wait' if a.wait else 'osd_english_ui'
    src+=f'$display("{prefix.upper()}_PASS {len(cases)} cases {len(cases)*122880} pixels");$finish;end endmodule'
    mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_osd','refined_english_font_rom','refined_english_text_rom','refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry')]
    run(prefix,src,mods,timeout=1800)

if __name__=='__main__':main()
