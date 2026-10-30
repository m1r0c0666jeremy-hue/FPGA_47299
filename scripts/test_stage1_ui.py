from pathlib import Path
"""Check complete user-visible messages and numeric boundaries against actual RTL."""
from refined_testlib import R,run
import hashlib
import re,json,hashlib
CHARS=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()'

def main():
    cases=[]
    def case(**kw):
        d=dict(mode=1,state=0,n=2,expected=1,actual=0,nd=2,occupied=0,distance=1234,dwell=12345,trend=0,error=0,start_error=0,busy=0,tip=1,muted=0,gb=0,gf=0,slot=5,show=1,row=0,gain=90,tgt=105,zm=1,proc=0,reason=0)
        d.update(kw);cases.append(d)
    for error in range(10):case(error=error)
    case(busy=1);case(tip=0)
    for state in range(8):case(mode=2,state=state,actual=3 if state==6 else 0)
    case(mode=2,state=6,actual=3,muted=1)
    for n in (0,1,4):
        for distance,dwell in ((0,0),(1,99),(2047,999900)):
            case(mode=2,n=n,distance=distance,dwell=dwell,occupied=1,trend=2)
    for trend in (0,1,2):case(mode=2,state=2,trend=trend)
    case(mode=2,state=2,busy=1)
    for mode in (0,3):case(mode=mode)
    case(mode=0,gb=1);case(mode=0,gf=1);case(mode=2,state=6,actual=3,show=0)
    for state in (1,3,4,7):case(mode=2,state=state,show=0)
    case(mode=0,show=0);case(mode=0,gb=1,gain=97)
    for reason in range(10):case(row=1,reason=reason)
    for gain in (16,32,48,64,80,90,105,97):case(mode=0,gain=gain)
    source='''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,latch=0;reg [5:0] col=0;
reg [1:0] mode=0,trend=0;reg [3:0] state=0,nd=0,occupied=0,error=0,start_error=0;
reg [2:0] n=0,expected=0,actual=0,slot=5;reg [10:0] distance=0;reg [19:0] dwell=0;
reg busy=0,tip=0,muted=0,gb=0,gf=0,show=1;wire [7:0] glyph;wire override_line,force_footer;wire [3:0] ss;wire [1:0] sm;
reg row=0;reg [6:0] gain=90,tgt=105;reg [2:0] zm=1;reg [1:0] proc=0;reg [3:0] reason=0;
stage1_ui_formatter dut(clk,rst,latch,col,mode,state,n,3'd0,expected,actual,nd,occupied,distance,dwell,trend,error,start_error,
busy,tip,muted,gb,gf,slot,show,glyph,override_line,force_footer,ss,sm,row,gain,tgt,zm,proc,1'b0,1'b1,5'd3,reason,8'd50,1'b0,176'd0);
integer fd,c;reg [359:0] chars="CHARS";
initial begin fd=$fopen("OUTPUT","w");repeat(3)@(negedge clk);rst=1;
'''.replace('CHARS',CHARS)
    out=R/'build'/('stage1_rect_ui_vectors_'+hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]);out.mkdir(parents=True,exist_ok=True);capture=out/'captured.txt'
    for c,d in enumerate(cases):
        source+='@(negedge clk);'+''.join(f'{k}={v};' for k,v in d.items())
        source+='latch=1;@(negedge clk);latch=0;repeat(50)@(negedge clk);\n'
        source+='for(c=0;c<64;c=c+1)begin col=c;repeat(5)@(negedge clk);if(glyph>=45)$fatal(1,"invalid glyph");$fwrite(fd,"%c",chars[(44-glyph)*8+:8]);end $fwrite(fd,"\\n");\n'
    source+='$fclose(fd);$display("STAGE1_UI_RTL_CAPTURE_PASS");$finish;end endmodule'
    source=source.replace('OUTPUT',capture.as_posix())
    attempt=run('stage1_ui',source,[R/'rtl/color_regions'/n for n in ('stage1_ui_text.v','stage1_ui_formatter.v')],timeout=120)
    lines=capture.read_text().splitlines();assert len(lines)==len(cases)
    errors=['TIP READY','SET TWO CORNERS','RECT TOO SMALL','AREA TOUCH/OVER','MAX 4 AREAS','TIP NOT READY','MAX 2 CORNERS','NO SAVED AREAS','BUSY','GESTURE CANCELED']
    states=['IDLE','WAIT OUT','RUN','PAUSED','MOVE OUT','PASS','FAIL','STOPPED']
    def expected_line(d):
        chars=[' ']*64
        def put(at,text):chars[at:at+len(text)]=text
        if d['row']:
            reasons=['','TRACKING OFF','CAMERA NOT READY','VIDEO NOT READY','FRAME HAS NO VALID TIP','STALE 250MS','BRIGHTNESS BUSY','GESTURE CANCELED','CONTEXT CHANGED','METADATA MISMATCH']
            put(42,reasons[d['reason']]);return ''.join(chars)
        deci=d['dwell']//100;duration=f'T{deci//10:03d}.{deci%10}s'
        if d['mode']==1:
            put(0,'EDIT');put(5,chr(65+d['n']) if d['n']<4 else '-');put(7,'PTS');put(11,str(d['nd']))
            put(12,'/2 SAVE');put(20,str(d['n']));put(21,'/4');put(41,'AUTO SAVE');put(54,duration)
            put(24,'BUSY' if d['busy'] else errors[d['error']] if d['error'] else 'TIP NOT READY' if not d['tip'] else 'TIP READY')
        elif d['mode']==2:
            put(0,states[d['state']].ljust(8));put(9,'NEXT');put(14,chr(65+d['expected']) if d['expected']<d['n'] and d['state']!=5 else '-')
            put(16,'IN');put(19,next((chr(65+i) for i in range(4) if d['occupied']&(1<<i)),'-'));put(30,duration)
            detail='BUSY' if d['busy'] else {0:'KEY2 START',1:'LEAVE ALL AREAS',3:'KEY3 RESUME',4:'LEAVE ALL AREAS',5:'KEY2 RETEST',7:'INPUT LOST'}.get(d['state'],'TIP READY')
            put(47,detail.ljust(16))
            if d['state']==6:put(47,f"EXP {chr(65+d['expected'])} GOT {chr(64+d['actual']) if d['actual'] else '-'}".ljust(16))
            if d['muted']:put(60,'MUTE')
        else:
            put(0,('RAW','HILITE','GRAY','MASK')[d['proc']].ljust(8));put(8,' ZOOM ');put(14,('1X  ','1.5X','2X  ','3X  ','4X  ')[d['zm']])
            put(19,'R/Y');put(23,'180');put(27,f"BRT{d['gain']:03d}")
            gains=(16,32,48,64,80,90,105);put(34,f"{gains.index(d['gain'])+1 if d['gain'] in gains else '-'}/7")
            put(38,'MARK');put(43,'ON' if d['show'] else 'OFF');put(47,'K0.50');put(53,'TRACKING')
            if d['gf']:put(0,'BRT FAILED. CHECK CAM')
            elif d['gb']:put(0,f"BRT{d['gain']:03d} TO{d['tgt']:03d} BUSY ")
            elif d['mode']==3:chars=list('TEACH EMPTY'.ljust(64))
        return ''.join(chars)
    for d,line in zip(cases,lines):
        assert len(line)==64,(d,line)
        assert line==expected_line(d),(d,line,expected_line(d))
        if d['row']:
            reasons=['','TRACKING OFF','CAMERA NOT READY','VIDEO NOT READY','FRAME HAS NO VALID TIP','STALE 250MS','BRIGHTNESS BUSY','GESTURE CANCELED','CONTEXT CHANGED','METADATA MISMATCH']
            assert line==(' '*42+reasons[d['reason']]).ljust(64),(d,line)
        elif d['mode']==1:
            message='BUSY' if d['busy'] else errors[d['error']] if d['error'] else 'TIP NOT READY' if not d['tip'] else 'TIP READY'
            assert message in line,(d,line)
            assert 'PX' not in line and 'APPROACH' not in line and 'AWAY' not in line,(d,line)
        elif d['mode']==2:
            assert line.startswith(states[d['state']]),(d,line)
            assert 'PX' not in line and 'APPROACH' not in line and 'AWAY' not in line,(d,line)
            deci=d['dwell']//100
            assert f'T{deci//10:03d}.{deci%10}s' in line,(d,line)
            if d['state']==6:assert 'EXP B GOT C' in line,(d,line)
            if d['muted']:assert 'MUTE' in line,(d,line)
            if d['busy']:assert 'BUSY' in line,(d,line)
        elif d['gb']:assert f"BRT{d['gain']:03d} TO105 BUSY" in line,line
        elif d['gf']:assert 'BRT FAILED. CHECK CAM' in line,line
        elif d['mode']==3:assert 'TEACH EMPTY' in line,line
        else:
            assert f"BRT{d['gain']:03d}" in line and 'ZOOM 1.5X' in line and ('MARK ON' if d['show'] else 'MARK OFF') in line,(d,line)
            assert line[47:52]=='K0.50' and line[53:].rstrip()=='TRACKING',(d,line)
            assert ('-/7' if d['gain']==97 else str((16,32,48,64,80,90,105).index(d['gain'])+1)+'/7') in line,(d,line)
    record=R/'reports/refined/regression'/(attempt.name+'.json');log=record.with_suffix('.log')
    message=f'STAGE1_UI_CONTRACT_PASS {len(cases)} complete lines including all messages and numeric boundaries'
    with log.open('a',encoding='utf-8') as f:f.write(message+'\n')
    data=json.loads(record.read_text());data['oracle_passed']=True;data['inputs']['scripts/test_stage1_ui.py']=hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest()
    record.write_text(json.dumps(data,indent=2),encoding='utf-8');print(message)

if __name__=='__main__':main()
