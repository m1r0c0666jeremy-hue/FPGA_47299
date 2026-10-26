"""Whole-line independent teaching/motion footer contract."""
from refined_testlib import R,run

CHARS=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()'

def main():
    src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,latch=0,row=0;reg [5:0] col=0;reg [1:0] mode=3;
reg [63:0] status=0;reg [3:0] state=2,occupied=1;reg [2:0] expected=1,actual=3;reg [19:0] dwell=2500;
wire [7:0] glyph;wire enabled;
stage1_teach_text dut(clk,rst,latch,col,row,mode,status,state,occupied,expected,actual,dwell,glyph,enabled);
integer i;reg [359:0] chars="CHARS";
task capture;begin latch=1;@(negedge clk);latch=0;repeat(180)@(negedge clk);
for(i=0;i<64;i=i+1)begin col=i;@(negedge clk);if(glyph>=45)$fatal(1,"glyph range");$write("%c",chars[(44-glyph)*8+:8]);end $write("\n");end endtask
initial begin repeat(3)@(negedge clk);rst=1;
'''.replace('CHARS',CHARS)
    cases=[]
    states=['EMPTY','READY','WAIT TIP','RECORD','LOADING','REPLAY','PAUSED','DONE','FAIL']
    reasons=['','TRACKING OFF','CAMERA NOT READY','VIDEO NOT READY','NO VALID TIP','STALE 250MS','BRIGHTNESS BUSY','GESTURE CANCELED','CONTEXT CHANGED','METADATA MISMATCH','STOP FIRST','NO ROUTE','LIMIT 30S/FULL','STOPPED','CLEARED','NEED 2 TIMED POINTS']
    def add(st=5,reason=0,elapsed=12345,duration=30000,count=602,trend=1,valid=1,seq=1,use=1,draft=0,row=0,mode=3,state=2):
        bus=st|(reason<<4)|(count<<8)|(elapsed<<19)|(duration<<35)|(valid<<51)|(trend<<52)|(seq<<54)|(use<<55)|(draft<<56)
        src_line=f'status=64\'h{bus:x};row={row};mode={mode};state={state};capture;\n'
        if mode==3 and row==0:
            text=[' ']*64
            def put(n,s):text[n:n+len(s)]=s
            put(0,'TEACH');put(6,states[st].ljust(8));put(15,f'{elapsed//1000:02d}.{elapsed//100%10}/{duration//1000:02d}.{duration//100%10}s')
            put(26,f'P{count:04d}');put(32,reasons[reason].ljust(32));expected_line=''.join(text)
        elif mode==2:
            expected_line=' '*21+(['MOVE    ','APPROACH','AWAY    ','STILL   '][trend] if valid else ' '*8)+' '*35
        elif row==1 and not seq:
            text=list('K2 REC/STOP K3 PLAY/PAUSE K4 STOP K4 HOLD CLEAR'.ljust(64))
            prefix='FINISH DRAFT. SEQ OFF' if draft else 'NO SAVED AREAS. SEQ OFF'
            text[:32]=prefix.ljust(32);text[32:]='K3 PLAY K4 STOP K4 HOLD CLEAR'.ljust(32);expected_line=''.join(text)
        else:expected_line=None
        cases.append((src_line,expected_line,st,row,state))
    for st in range(9):add(st=st)
    for reason in range(16):add(reason=reason)
    for elapsed,duration,count in ((0,0,0),(99,100,1),(999,1000,2),(29999,30000,601),(30000,30000,602)):
        add(elapsed=elapsed,duration=duration,count=count)
    for trend in range(4):add(mode=2,trend=trend)
    add(seq=0,row=1);add(seq=0,row=1,draft=1);add(row=1,state=6,st=8)
    src+=''.join(c[0] for c in cases)+'$display("STAGE1_TEACH_UI_CAPTURE_PASS");$finish;end endmodule'
    out=run('stage1_teach_ui',src,[R/'rtl/color_regions/stage1_ui_formatter.v',R/'rtl/color_regions/stage1_ui_text.v'],timeout=60)
    text=(R/'reports/refined/regression'/(out.name+'.log')).read_text()
    lines=[s for s in text.splitlines() if len(s)==64]
    assert len(lines)==len(cases),(len(lines),len(cases))
    for line,(_,expected_line,st,row,state) in zip(lines,cases):
        if expected_line is not None:assert line==expected_line,(line,expected_line)
        else:assert 'EXP B GOT C' in line,line
    with (R/'reports/refined/regression'/(out.name+'.log')).open('a') as f:f.write(f'STAGE1_TEACH_UI_PASS cases={len(cases)}\n')
    print('STAGE1_TEACH_UI_PASS',len(cases))

if __name__=='__main__':main()
