"""Deterministic two-row UI; overlay visibility never hides operating text."""
from refined_english_ui import STATES
CHARS=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()'
# All 20 state meanings are retained in eleven readable columns next to K.
SHORT_STATES=['IDLE','CENTER SEL','CONFIRMING','TRACKING','MISS COLOR','HOLD LOST',
              'RESELECT','TIP OUT','BAD FRAME','CAL WHITE','CAL BG','CAL A','CAL B',
              'PROCESSING','SAMPLE FAIL','RECALIBRATE','VIDEO WAIT','KEY CONFL','NO NEW FR','WAIT RESULT']
MESSAGES=['TIP READY','SET TWO CORNERS','RECT TOO SMALL','AREA TOUCH/OVER','MAX 4 AREAS','TIP NOT READY',
          'MAX 2 CORNERS','NO SAVED AREAS','BUSY','GESTURE CANCELED','FINISH DRAFT','LEAVE ALL AREAS',
          'KEY2 START','KEY2 RETEST','KEY3 RESUME','INPUT LOST']
REASONS=['','TRACKING OFF','CAMERA NOT READY','VIDEO NOT READY','FRAME HAS NO VALID TIP',
         'STALE 250MS','BRIGHTNESS BUSY','GESTURE CANCELED','CONTEXT CHANGED','METADATA MISMATCH']
RUN_NAMES=['IDLE','WAIT OUT','RUN','PAUSED','MOVE OUT','PASS','FAIL','STOPPED']
CAMERA_FAULTS=['CAM NACK','CAM TIMEOUT','VIDEO LOST','CFG RD FAIL','CAM ID FAIL']

def ui_assets():
    ids={c:i for i,c in enumerate(CHARS)};rom=[0]*1024
    assert len(SHORT_STATES)==len(STATES) and max(map(len,SHORT_STATES))<=11
    for base,stride,values in [(0,16,MESSAGES),(256,8,RUN_NAMES),(384,16,SHORT_STATES),(704,32,REASONS)]:
        for i,s in enumerate(values):
            assert len(s)<=stride
            for j,c in enumerate(s):rom[base+i*stride+j]=ids[c]
    # Five 12-byte messages fit the unused 320..383 ROM region. Neither the
    # existing reason bank nor the memory/address widths need to grow.
    for i,s in enumerate(CAMERA_FAULTS):
        assert len(s)<=11
        for j,c in enumerate(s):rom[320+i*12+j]=ids[c]
    text='module stage1_ui_text(input wire clk,input wire [9:0] addr,output reg [7:0] q);\n(* rom_style="bram" *)reg [7:0] mem[0:1023];\ninitial begin\n'
    text+=''.join(f"mem[{i}]=8'd{v};\n" for i,v in enumerate(rom))+'end\nalways @(posedge clk)q<=mem[addr];\nendmodule\n'
    def layout():return ["8'd0"]*64
    def put(a,k,s):
        for j,c in enumerate(s):a[k+j]=f"8'd{ids[c]}"
    edit=layout();put(edit,0,'EDIT ');edit[5]="fn<4?8'd11+fn:8'd41"
    put(edit,7,'PTS ');edit[11]="8'd1+fdraft";put(edit,12,'/2 SAVE ');edit[20]="8'd1+fn";put(edit,21,'/4')
    for i in range(24,40):edit[i]='rom_glyph'
    put(edit,41,'AUTO SAVE');put(edit,54,'T')
    for i in range(3):edit[55+i]=f"8'd1+dwell_bcd[{12-4*i}+:4]"
    put(edit,58,'.');edit[59]="8'd1+dwell_bcd[3:0]";put(edit,60,'s')
    test=layout()
    for i in range(8):test[i]='rom_glyph'
    put(test,9,'NEXT ');test[14]="fexpected<fn && fstate!=5?8'd11+fexpected:8'd41"
    put(test,16,'IN ');test[19]="foccupied[0]?8'd11:foccupied[1]?8'd12:foccupied[2]?8'd13:foccupied[3]?8'd14:8'd41"
    put(test,30,'T')
    for i in range(3):test[31+i]=f"8'd1+dwell_bcd[{12-4*i}+:4]"
    put(test,34,'.');test[35]="8'd1+dwell_bcd[3:0]";put(test,36,'s')
    for i in range(47,63):test[i]='rom_glyph'
    fail=layout();put(fail,47,'EXP ');fail[51]="8'd11+fexpected";put(fail,52,' GOT ');fail[57]="factual!=0?8'd10+factual:8'd41"
    for i in range(47,64):test[i]=f"fstate==6?({fail[i]}):({test[i]})"
    for i,c in enumerate('MUTE'):test[60+i]=f"fmuted?8'd{ids[c]}:({test[60+i]})"
    normal=layout()
    modes=['RAW     ','HILITE  ','GRAY    ','MASK    ']
    for i in range(8):normal[i]=':'.join(f"fprocess=={j}?8'd{ids[s[i]]}" for j,s in enumerate(modes[:-1]))+f":8'd{ids[modes[-1][i]]}"
    put(normal,8,' ZOOM ')
    for i in range(4):normal[14+i]=':'.join(f"fzoom=={j}?8'd{ids[s[i]]}" for j,s in enumerate(['1X  ','1.5X','2X  ','3X  ']))+f":8'd{ids['4X  '[i]]}"
    for i in range(3):normal[19+i]=f"fpair?8'd{ids['B/P'[i]]}:8'd{ids['R/Y'[i]]}"
    for i in range(3):normal[23+i]=f"frotate?8'd{ids['180'[i]]}:8'd{ids['000'[i]]}"
    put(normal,27,'BRT')
    for i in range(3):normal[30+i]=f"8'd1+gain_bcd[{8-4*i}+:4]"
    normal[34]="actual_slot<7?8'd2+actual_slot:8'd41";put(normal,35,'/7 MARK ')
    for i in range(3):normal[43+i]=f"fshow?8'd{ids['ON '[i]]}:8'd{ids['OFF'[i]]}"
    put(normal,47,'K');normal[48]="8'd1+k_bcd[8+:4]";put(normal,49,'.')
    normal[50]="8'd1+k_bcd[4+:4]";normal[51]="8'd1+k_bcd[0+:4]"
    for i in range(53,64):normal[i]='rom_glyph'
    busy=normal.copy();put(busy,0,'BRT')
    for i in range(3):busy[3+i]=f"8'd1+gain_bcd[{8-4*i}+:4]"
    put(busy,6,' TO')
    for i in range(3):busy[9+i]=f"8'd1+target_bcd[{8-4*i}+:4]"
    put(busy,12,' BUSY ')
    failed=normal.copy();put(failed,0,'BRT FAILED. CHECK CAM')
    kpage=layout();put(kpage,0,'K ADJUST ');put(kpage,9,'K')
    kpage[10]="8'd1+k_bcd[8+:4]";put(kpage,11,'.')
    kpage[12]="8'd1+k_bcd[4+:4]";kpage[13]="8'd1+k_bcd[0+:4]"
    put(kpage,16,'K3 INC K4 DEC K2 EXIT')
    reserved=layout();put(reserved,0,'TEACH EMPTY')
    ui='''`default_nettype none
module stage1_ui_formatter(input wire clk,rst_n,latch,input wire [5:0] col,
 input wire [1:0] mode,input wire [3:0] run_state,input wire [2:0] area_count,draft_area,expected_area,actual_area,
 input wire [3:0] draft_count,occupied,input wire [10:0] distance,input wire [19:0] dwell_ms,
 input wire [1:0] trend,input wire [3:0] edit_error,start_error,input wire busy,tip_live,muted,gain_busy,gain_failed,
 input wire [2:0] gain_slot,input wire show,output reg [7:0] glyph,output wire override_enable,force_footer,
 output wire [3:0] snapshot_state,output wire [1:0] snapshot_mode,
 input wire row,input wire [6:0] gain_actual,gain_target,input wire [2:0] zoom,
 input wire [1:0] process_mode,input wire pair,rotate,input wire [4:0] status,input wire [3:0] tip_reason,
 input wire [7:0] I_k_value,input wire I_k_adjust);
 reg [1:0] fmode,fprocess;reg [3:0] fstate,fn,fdraft,foccupied,fedit,fstart,freason;
 reg [2:0] fexpected,factual,fslot,fzoom;reg [4:0] fstatus;
 reg status_pending;reg fbusy,ftip,fmuted,fgain,fgain_failed,fshow,fpair,frotate,fk_adjust;
 reg [6:0] fgain_actual;reg [11:0] gain_bcd,target_bcd,k_bcd;
 reg [19:0] divider,binary;reg [6:0] remainder;reg [13:0] quotient;
 reg [15:0] bcd,dwell_bcd,adjusted;reg [1:0] conversion;reg [4:0] bit_index;
 reg [3:0] message_id;reg [9:0] rom_addr;wire [7:0] rom_glyph;reg [2:0] actual_slot;
 stage1_ui_text text_rom(clk,rom_addr,rom_glyph);
 wire [7:0] shifted={remainder,divider[19]};wire qbit=shifted>=100;
 assign snapshot_state=fstate;assign snapshot_mode=fmode;
 assign force_footer=1'b1;assign override_enable=!row || col>=42;
 function [11:0] decimal7;input [6:0] value;reg [11:0] d;integer j,k;begin d=0;
 for(j=6;j>=0;j=j-1)begin for(k=0;k<3;k=k+1)if(d[k*4+:4]>=5)d[k*4+:4]=d[k*4+:4]+3;d={d[10:0],value[j]};end
 decimal7=d;end endfunction
 function [11:0] decimal8;input [7:0] value;reg [11:0] d;integer j,k;begin d=0;
 for(j=7;j>=0;j=j-1)begin for(k=0;k<3;k=k+1)if(d[k*4+:4]>=5)d[k*4+:4]=d[k*4+:4]+3;d={d[10:0],value[j]};end
 decimal8=d;end endfunction
 integer i;
 always @*begin adjusted=bcd;for(i=0;i<4;i=i+1)if(bcd[i*4+:4]>=5)adjusted[i*4+:4]=bcd[i*4+:4]+3;
 case(fgain_actual)16:actual_slot=0;32:actual_slot=1;48:actual_slot=2;64:actual_slot=3;80:actual_slot=4;90:actual_slot=5;105:actual_slot=6;default:actual_slot=7;endcase end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin fmode<=0;fstate<=0;fn<=0;fdraft<=0;foccupied<=0;fedit<=0;fstart<=0;freason<=0;
 status_pending<=0;fexpected<=0;factual<=0;fslot<=5;fzoom<=0;fprocess<=0;fstatus<=0;fpair<=0;frotate<=1;
 fbusy<=0;ftip<=0;fmuted<=0;fgain<=0;fgain_failed<=0;fshow<=1;fgain_actual<=90;fk_adjust<=0;
 gain_bcd<=12'h090;target_bcd<=12'h090;k_bcd<=12'h050;divider<=0;binary<=0;remainder<=0;quotient<=0;
 bcd<=0;dwell_bcd<=0;conversion<=0;bit_index<=0;end
 else begin
 status_pending<=latch;if(status_pending)fstatus<=status;
 if(conversion==1)begin divider<=divider<<1;remainder<=qbit?shifted-100:shifted;quotient<={quotient[12:0],qbit};
 if(bit_index==19)begin binary<={6'd0,quotient[12:0],qbit};bcd<=0;bit_index<=0;conversion<=2;end else bit_index<=bit_index+1'b1;
 end else if(conversion==2)begin binary<=binary<<1;bcd<={adjusted[14:0],binary[19]};
 if(bit_index==19)begin dwell_bcd<={adjusted[14:0],binary[19]};conversion<=0;end else bit_index<=bit_index+1'b1;end
 if(latch)begin fmode<=mode;fstate<=run_state;fn<={1'b0,area_count};fdraft<=draft_count;foccupied<=occupied;
 fexpected<=expected_area;factual<=actual_area;fedit<=edit_error;fstart<=start_error;freason<=tip_reason;
 fbusy<=busy;ftip<=tip_live;fmuted<=muted;fgain<=gain_busy;fgain_failed<=gain_failed;fslot<=gain_slot;fshow<=show;
 fzoom<=zoom;fprocess<=process_mode;fpair<=pair;frotate<=rotate;
 k_bcd<=decimal8(I_k_value);fk_adjust<=I_k_adjust;
 fgain_actual<=gain_actual;gain_bcd<=decimal7(gain_actual);target_bcd<=decimal7(gain_target);
 divider<=dwell_ms;remainder<=0;quotient<=0;bit_index<=0;conversion<=1;end end end
 always @*begin
 message_id=fbusy?8:fedit!=0?fedit:!ftip?5:0;
 if(fmode==2)begin
 if(fbusy)message_id=8;else if(fstart!=0)case(fstart)1:message_id=7;2:message_id=10;3:message_id=5;default:message_id=8;endcase
 else case(fstate)0:message_id=12;1,4:message_id=11;3:message_id=14;5:message_id=13;7:message_id=15;default:message_id=0;endcase end
 rom_addr=0;
 if(row && col>=42)begin
 if(fstatus>=20 && fstatus<=24)rom_addr=col<53?10'd320+(fstatus-20)*12+col-42:10'd383;
 else rom_addr=10'd704+{1'b0,freason,5'd0}+col-42;end
 else if(fmode==1 && col>=24 && col<40)rom_addr={2'd0,message_id,4'd0}+col-24;
 else if(fmode==2)begin if(col<8)rom_addr=10'd256+{3'd0,fstate,3'd0}+col;
 else if(col>=47 && col<63)rom_addr={2'd0,message_id,4'd0}+col-47;end
 else if(fmode==0 && col>=53)begin
 if(fstatus>=20 && fstatus<=24)rom_addr=10'd320+(fstatus-20)*12+col-53;
 else rom_addr=10'd384+{1'b0,fstatus,4'd0}+col-53;end
 end
'''
    for name,line in [('edit',edit),('test',test),('normal',normal),('busy',busy),('failed',failed),('kpage',kpage),('reserved',reserved)]:
        ui+=f'function [7:0] {name}_char;input [5:0] column;begin {name}_char=0;case(column)\n'
        ui+=''.join(f"6'd{i}:{name}_char={expr};\n" for i,expr in enumerate(line) if expr!="8'd0")+'endcase end endfunction\n'
    ui+='''always @(row or col or fmode or fgain_failed or fgain or fshow or fn or fdraft or fstate or fexpected or factual or foccupied or fmuted or fprocess or fzoom or fpair or frotate or gain_bcd or target_bcd or actual_slot or dwell_bcd or rom_glyph or k_bcd or fk_adjust)begin
 if(row)glyph=col>=42?rom_glyph:8'd0;
 else if(fmode==2)glyph=test_char(col);else if(fmode==1)glyph=edit_char(col);
 else if(fgain_failed)glyph=failed_char(col);else if(fgain)glyph=busy_char(col);
 else if(fmode==0 && fk_adjust)glyph=kpage_char(col);
 else if(fmode==3)glyph=reserved_char(col);else glyph=normal_char(col);
 end
endmodule
`default_nettype wire
'''
    return text,ui
