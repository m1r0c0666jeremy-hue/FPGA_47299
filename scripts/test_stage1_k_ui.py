"""Independent 64-column expectations for shared K and recorded-route identity."""
import contextlib
import io
from refined_testlib import R,run

CHARS=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()'
SHORT_STATES=('IDLE','CENTER SEL','CONFIRMING','TRACKING','MISS COLOR','HOLD LOST',
              'RESELECT','TIP OUT','BAD FRAME','CAL WHITE','CAL BG','CAL A','CAL B',
              'PROCESSING','SAMPLE FAIL','RECALIBRATE','VIDEO WAIT','KEY CONFL','NO NEW FR','WAIT RESULT')
REASONS=('','TRACKING OFF','CAMERA NOT READY','VIDEO NOT READY','NO VALID TIP','STALE 250MS',
         'BRIGHTNESS BUSY','GESTURE CANCELED','CONTEXT CHANGED','METADATA MISMATCH','STOP FIRST',
         'NO ROUTE','LIMIT 30S/FULL','STOPPED','CLEARED','NEED 2 TIMED POINTS')
STATES=('EMPTY','READY','WAIT TIP','RECORD','LOADING','REPLAY','UNUSED','DONE','FAIL')
RUN_STATES=('IDLE','WAIT OUT','RUN','PAUSED','MOVE OUT','PASS','FAIL','STOPPED')

def put(line,at,text):
    assert at+len(text)<=64
    line[at:at+len(text)]=text

def check_capture(name,source,expected):
    quiet=io.StringIO()
    try:
        with contextlib.redirect_stdout(quiet):
            out=run(name,source,[R/'rtl/color_regions/stage1_ui_formatter.v',R/'rtl/color_regions/stage1_ui_text.v'],timeout=120)
        log=R/'reports/refined/regression'/(out.name+'.log')
        lines=[line for line in log.read_text(encoding='utf-8').splitlines() if len(line)==64]
        assert len(lines)==len(expected),(len(lines),len(expected))
        for i,(actual,wanted) in enumerate(zip(lines,expected)):
            assert actual==wanted,(i,actual,wanted)
        with log.open('a',encoding='utf-8') as handle:handle.write(f'{name.upper()}_PASS cases={len(expected)}\n')
        print(f'{name.upper()}_PASS cases={len(expected)} log={log.relative_to(R)}')
    except BaseException:
        print(quiet.getvalue())
        raise

def normal_ui():
    source=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,latch=0,row=0;reg [5:0] col=0;
reg [7:0] k=50;reg page=0,busy=0,failed=0,show=1;reg [4:0] status=15;
reg [6:0] actual=90,target=105;wire [7:0] glyph;wire enabled,footer;
stage1_ui_formatter dut(.clk(clk),.rst_n(rst),.latch(latch),.col(col),.mode(2'd0),.run_state(4'd0),
.area_count(3'd0),.draft_area(3'd0),.expected_area(3'd0),.actual_area(3'd0),.draft_count(4'd0),.occupied(4'd0),
.distance(11'd0),.dwell_ms(20'd0),.trend(2'd0),.edit_error(4'd0),.start_error(4'd0),.busy(1'b0),.tip_live(1'b1),
.muted(1'b0),.gain_busy(busy),.gain_failed(failed),.gain_slot(3'd5),.show(show),.glyph(glyph),
.override_enable(enabled),.force_footer(footer),.row(row),.gain_actual(actual),.gain_target(target),.zoom(3'd1),
.process_mode(2'd1),.pair(1'b0),.rotate(1'b1),.status(status),.tip_reason(4'd0),.I_k_value(k),.I_k_adjust(page));
integer i;reg [359:0] chars="CHARS";
task snapshot;begin latch=1;@(negedge clk);latch=0;repeat(60)@(negedge clk);end endtask
task capture;begin for(i=0;i<64;i=i+1)begin col=i;repeat(3)@(negedge clk);
if(glyph>=45 || !enabled || !footer)$fatal(1,"glyph/override/footer contract");
$write("%c",chars[(44-glyph)*8+:8]);end $write("\n");end endtask
initial begin repeat(4)@(negedge clk);rst=1;
'''.replace('CHARS',CHARS)
    commands=[];expected=[]
    def line_for(k,page=0,status=15,busy=0,failed=0,show=1,actual=90,target=105):
        line=[' ']*64
        put(line,0,'HILITE');put(line,8,' ZOOM ');put(line,14,'1.5X');put(line,19,'R/Y');put(line,23,'180')
        gains=(16,32,48,64,80,90,105)
        put(line,27,f'BRT{actual:03d}');put(line,34,f'{gains.index(actual)+1 if actual in gains else "-"}/7');put(line,38,'MARK');put(line,43,'ON' if show else 'OFF')
        put(line,47,f'K{k//100}.{k%100:02d}');put(line,53,SHORT_STATES[status])
        if failed:put(line,0,'BRT FAILED. CHECK CAM')
        elif busy:put(line,0,f'BRT{actual:03d} TO{target:03d} BUSY ')
        elif page:
            line=[' ']*64;put(line,0,'K ADJUST');put(line,9,f'K{k//100}.{k%100:02d}');put(line,16,'K3 INC K4 DEC K2 EXIT')
        return ''.join(line)
    def add(k=50,page=0,status=15,busy=0,failed=0,show=1,actual=90,target=105):
        commands.append(f'k={k};page={page};status={status};busy={busy};failed={failed};show={show};actual={actual};target={target};snapshot;capture;\n')
        expected.append(line_for(k,page,status,busy,failed,show,actual,target))
    for k in range(201):add(k=k)
    for status in range(20):add(status=status)
    for k in (0,50,200):add(k=k,page=1)
    add(k=51,page=1,busy=1,actual=97);add(k=52,page=1,failed=1)
    add(k=75,show=0)
    # Every character comes from the previous frame's snapshot, even if the
    # asynchronous UI controls change before the footer is scanned.
    commands.append('k=50;page=1;busy=0;failed=0;show=0;snapshot;k=199;page=0;capture;\n')
    expected.append(line_for(50,page=1,show=0))
    source+=''.join(commands)+'$display("STAGE1_K_UI_CAPTURE_DONE");$finish;end endmodule'
    check_capture('stage1_k_ui',source,expected)

def teaching_ui():
    source=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,latch=0,row=0;reg [5:0] col=0;reg [1:0] mode=3;
reg [79:0] status=0;reg [7:0] current=50;reg [3:0] state=2;wire [7:0] glyph;wire enabled;
stage1_teach_text dut(clk,rst,latch,col,row,mode,status,state,4'd1,3'd1,3'd3,20'd2500,glyph,enabled,current,176'd0);
integer i;reg [359:0] chars="CHARS";
task snapshot;begin latch=1;@(negedge clk);latch=0;repeat(180)@(negedge clk);end endtask
task capture;begin for(i=0;i<64;i=i+1)begin col=i;@(negedge clk);
if(glyph>=45 || !enabled)$fatal(1,"teaching glyph/override contract");
$write("%c",chars[(44-glyph)*8+:8]);end $write("\n");end endtask
initial begin repeat(4)@(negedge clk);rst=1;
'''.replace('CHARS',CHARS)
    commands=[];expected=[]
    def add(st=5,reason=0,recorded=50,current=50,valid=1,row=0,seq=1,use=1,draft=0,state=2):
        bus=st|(reason<<4)|(602<<8)|(12345<<19)|(30000<<35)|(seq<<54)|(use<<55)|(draft<<56)|(recorded<<64)|(valid<<72)
        commands.append(f'status=80\'h{bus:x};current={current};row={row};state={state};snapshot;capture;\n')
        line=[' ']*64
        if row==0:
            put(line,0,'TEACH');put(line,6,STATES[st].ljust(8));put(line,15,'12.3/30.0s');put(line,26,'P0602')
            put(line,32,f'RK{recorded//100}.{recorded%100:02d}' if valid else 'RK----')
            if valid and recorded!=current:put(line,39,'DIFF')
            put(line,44,REASONS[reason])
        else:
            if st in (2,3):keys='K2 STOP K4 HOLD CLEAR';short='K2 STOP'
            elif st in (4,5):keys='K4 STOP K4 HOLD CLEAR';short='K4 STOP'
            elif st in (7,8):keys='K3 REPLAY K4 STOP K4 HOLD CLEAR';short='K3 REPLAY K4 STOP'
            else:keys='K3 PLAY K4 STOP K4 HOLD CLEAR';short='K3 PLAY K4 STOP'
            if seq and use:
                put(line,0,RUN_STATES[state].ljust(8));put(line,9,'NEXT');put(line,14,'-' if state==5 else 'B')
                put(line,16,'IN');put(line,19,'A');put(line,30,'T002.5s');put(line,47,short.ljust(17))
                if state==6:put(line,47,'EXP B GOT C'.ljust(17))
                if st==7 and state!=5:put(line,0,'INCOMP  ')
            elif use:
                put(line,0,('FINISH DRAFT. SEQ OFF' if draft else 'NO SAVED AREAS. SEQ OFF').ljust(32))
                put(line,32,keys.ljust(32))
            else:
                hint=keys if st in (2,3,4,5,7,8) else 'K2 REC/STOP K3 PLAY K4 STOP K4 HOLD CLEAR'
                put(line,0,hint.ljust(64))
        expected.append(''.join(line))
    for k in (0,1,49,50,99,100,199,200):
        add(recorded=k,current=k);add(recorded=k,current=50 if k!=50 else 51)
    add(recorded=255,current=200,valid=0)
    for reason in range(16):add(reason=reason)
    for st in range(9):add(st=st)
    for st in (2,3,4,5,7,8):
        add(st=st,row=1);add(st=st,row=1,seq=0);add(st=st,row=1,use=0)
    add(st=5,row=1,seq=0,draft=1);add(st=8,row=1,state=6)
    add(st=7,row=1,state=5);add(st=7,row=1,state=2)
    source+=''.join(commands)+'$display("STAGE1_K_TEACH_UI_CAPTURE_DONE");$finish;end endmodule'
    check_capture('stage1_k_teach_ui',source,expected)

def main():
    normal_ui()
    teaching_ui()

if __name__=='__main__':main()
