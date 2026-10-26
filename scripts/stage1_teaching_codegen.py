"""Teaching hooks are confined to candidate wrappers; vendor/live RTL is frozen."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]

def viewport_source():
    s=(R/'rtl/color_regions/stable_display.v').read_text(encoding='utf-8')
    s=s.replace('module stable_display #','module stage1_viewport #')
    s=s.replace('output reg O_time_valid);','output reg O_time_valid,input wire [38:0] I_point,output reg [38:0] O_point);')
    s=s.replace('I_data[89:79]','(I_point[22]?I_point[10:0]:I_data[89:79])')
    s=s.replace('I_data[99:90]','(I_point[22]?I_point[20:11]:I_data[99:90])')
    s=s.replace('!I_data[32] || I_data[MW+:32]==O_frame_id','(I_point[22]?!I_point[21]:(!I_data[32] || I_data[MW+:32]==O_frame_id))')
    s=s.replace('O_time_valid<=0;end','O_time_valid<=0;O_point<=0;end')
    s=s.replace('O_commit<=1;','O_commit<=1;O_point<=I_point[22]?I_point:{16\'d0,1\'b0,I_data[32],I_data[99:79]};')
    return s

def decorate(out):
    v=out['rtl/color_regions/stage1_memory_video_out.v']
    v=v.replace('wire [767:0] active_meta;', 'wire [767:0] active_meta;wire [38:0] teach_desired_point,teach_active_point;wire [63:0] teaching_status;wire stage1_raw_area_alarm;')
    v=v.replace('stable_display #(.V4(1))','stage1_viewport #(.V4(1))')
    v=v.replace('.O_state(active_status));','.O_state(active_status),.I_point(teach_desired_point),.O_point(teach_active_point));')
    marker='wire area_associated,area_video;wire [3:0] area_tip_reason;'
    image='''wire area_associated,area_video;wire [3:0] area_tip_reason;
    wire teaching_image_ok;wire [3:0] teaching_image_reason;
    wire teaching_image_associated=active_meta[255] && active_meta[247] && active_meta[415:413]==4 &&
     active_meta[31:0]==selected_frame_id && active_meta[719:704]==image_epoch && active_meta[671:640]==image_us &&
     active_meta[720] && image_time_valid && active_meta[242:235]==I_session && active_meta[243]==I_pair && active_meta[244]==I_tracking;
    stage1_teach_image_guard teaching_video_guard(I_pixel_clk,I_process_rst_n,stream_pixel_n,I_camera_ready,I_gain_busy,
     video_ok,S_hdmi_out_de,teaching_image_associated,selected_frame_id,teaching_image_ok,teaching_image_reason);'''
    assert marker in v;v=v.replace(marker,image)
    v=v.replace('stage1_regions area_controller','stage1_scene area_controller')
    v=v.replace('.tip_reason(area_tip_reason));','.tip_reason(area_tip_reason),.image_healthy(teaching_image_ok),.image_reason(teaching_image_reason),\n     .shown_point(teach_active_point),.desired_point(teach_desired_point),.teaching(teaching_status));')
    v=v.replace('stage1_osd u_osd (','stage1_osd u_osd (.I_teaching(teaching_status),.I_point(teach_active_point[22:0]),')
    assert '.alarm(O_area_alarm)' in v
    v=v.replace('.alarm(O_area_alarm)', '.alarm(stage1_raw_area_alarm)')
    v=v.replace('stage1_scene area_controller(', 'stage1_teach_alarm replay_alarm_gate(I_ui_mode,teaching_status[3:0],stage1_raw_area_alarm,O_area_alarm);\n    stage1_scene area_controller(')
    v+='''\n// Suppress a latched previous sequence result during replay preload/restart.
`default_nettype none
module stage1_teach_alarm(input wire [1:0] mode,input wire [3:0] route_state,input wire raw_alarm,output wire alarm);
assign alarm=raw_alarm && (mode!=2'd3 || route_state==4'd8);
endmodule
`default_nettype wire
'''
    out['rtl/color_regions/stage1_memory_video_out.v']=v
    s=out['rtl/color_regions/stage1_osd.v']
    s=s.replace('input wire [3:0] I_tip_reason\n','input wire [3:0] I_tip_reason,input wire [63:0] I_teaching,input wire [22:0] I_point\n')
    s=s.replace('wire [7:0] region_label_glyph,stage_glyph;', 'wire [7:0] region_label_glyph,stage_glyph,teaching_glyph;wire teaching_override;')
    marker=' stage1_ui_formatter region_text('
    hook=''' stage1_teach_text teaching_text(I_clk,I_rst_n,I_de && y==625 && x==0,format_col,format_row,I_ui_mode,I_teaching,
 I_run_state,I_occupied,I_expected_area,I_actual_area,I_area_dwell,teaching_glyph,teaching_override);
'''
    assert marker in s;s=s.replace(marker,hook+marker)
    s=s.replace('fm[567:565]==0 && stage_override?stage_glyph:decoded_glyph',
                'fm[567:565]==0 && teaching_override?teaching_glyph:fm[567:565]==0 && stage_override?stage_glyph:decoded_glyph')
    s=s.replace('refined_overlay_geometry coordinates(',
        "wire [639:0] point_geometry=I_point[22]?{I_meta[639:100],I_point[20:0],I_meta[78:0]}:I_meta[639:0];\n refined_overlay_geometry coordinates(")
    s=s.replace('I_geometry_commit,I_meta[639:0],','I_geometry_commit,point_geometry,')
    s=s.replace('if(I_show && I_detection_valid && I_meta[32])begin',
                'if(I_show && (I_point[22]?I_point[21]:(I_detection_valid && I_meta[32])))begin')
    out['rtl/color_regions/stage1_osd.v']=s
    out['rtl/color_regions/stage1_ui_formatter.v']=out['rtl/color_regions/stage1_ui_formatter.v'].replace('ROUTE RESERVED','TEACH EMPTY')+teaching_text_source()
    assert viewport_source() in (R/'rtl/color_regions/stage1_regions.v').read_text(encoding='utf-8'),'Teaching viewport differs from deterministic live wrapper'

def teaching_text_source():
    states=['EMPTY','READY','WAIT TIP','RECORD','LOADING','REPLAY','UNUSED','DONE','FAIL']
    reasons=['','TRACKING OFF','CAMERA NOT READY','VIDEO NOT READY','NO VALID TIP','STALE 250MS','BRIGHTNESS BUSY','GESTURE CANCELED',
             'CONTEXT CHANGED','METADATA MISMATCH','STOP FIRST','NO ROUTE','LIMIT 30S/FULL','STOPPED','CLEARED','NEED 2 TIMED POINTS']
    def cases(values,width,name):
        return '\n'.join(f'{i}:{name}="{s:<{width}}";' for i,s in enumerate(values))
    s=r'''
`default_nettype none
module stage1_teach_text(input wire clk,rst_n,latch,input wire [5:0] col,input wire row,input wire [1:0] mode,
 input wire [63:0] teaching,input wire [3:0] run_state,occupied,input wire [2:0] expected,actual,
 input wire [19:0] dwell,output reg [7:0] glyph,output wire override_enable);
 reg [63:0] f;reg [1:0] fm;reg [3:0] fs,fi;reg [2:0] fe,fa;
 reg [19:0] dwell_value,number,binary;reg [6:0] rem;reg [13:0] quotient;
 reg [15:0] bcd,adjusted,time_bcd,duration_bcd,count_bcd,dwell_bcd;
 reg [2:0] field;reg [1:0] conversion;reg [4:0] index;integer i;
 wire [7:0] shifted={rem,number[19]};wire take=shifted>=100;
 reg [63:0] state_word,motion_word,run_word;reg [255:0] reason_word;reg [7:0] ascii;
 function [7:0] encode;input [7:0] c;begin
 if(c>=48 && c<=57)encode=c-47;else if(c>=65 && c<=90)encode=c-54;
 else case(c)109:encode=37;115:encode=38;46:encode=39;58:encode=40;45:encode=41;47:encode=42;40:encode=43;41:encode=44;default:encode=0;endcase end endfunction
 assign override_enable=fm==3;
 always @*begin adjusted=bcd;for(i=0;i<4;i=i+1)if(bcd[i*4+:4]>=5)adjusted[i*4+:4]=bcd[i*4+:4]+3;end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin f<=0;fm<=0;fs<=0;fi<=0;fe<=0;fa<=0;dwell_value<=0;number<=0;binary<=0;rem<=0;quotient<=0;
 bcd<=0;time_bcd<=0;duration_bcd<=0;count_bcd<=0;dwell_bcd<=0;field<=0;conversion<=0;index<=0;end
 else begin
 if(conversion==1)begin number<=number<<1;rem<=take?shifted-100:shifted;quotient<={quotient[12:0],take};
 if(index==19)begin binary<={6'd0,quotient[12:0],take};bcd<=0;index<=0;conversion<=2;end else index<=index+1'b1;end
 else if(conversion==2)begin binary<=binary<<1;bcd<={adjusted[14:0],binary[19]};
 if(index==19)begin
 case(field)0:time_bcd<={adjusted[14:0],binary[19]};1:duration_bcd<={adjusted[14:0],binary[19]};
 2:count_bcd<={adjusted[14:0],binary[19]};3:dwell_bcd<={adjusted[14:0],binary[19]};endcase
 index<=0;bcd<=0;rem<=0;quotient<=0;field<=field+1'b1;
 case(field)
 0:begin number<={4'd0,f[50:35]};conversion<=1;end
 1:begin binary<={9'd0,f[18:8]};conversion<=2;end
 2:begin number<=dwell_value;conversion<=1;end
 default:conversion<=0;endcase
 end else index<=index+1'b1;end
 if(latch)begin f<=teaching;fm<=mode;fs<=run_state;fi<=occupied;fe<=expected;fa<=actual;dwell_value<=dwell;
 number<={4'd0,teaching[34:19]};field<=0;index<=0;rem<=0;quotient<=0;conversion<=1;end
 end end
 always @*begin
 state_word="EMPTY   ";case(f[3:0])
STATE_CASES
 endcase
 motion_word="        ";
 run_word="IDLE    ";case(fs)
 1:run_word="WAIT OUT";2:run_word="RUN     ";3:run_word="PAUSED  ";4:run_word="MOVE OUT";5:run_word="PASS    ";6:run_word="FAIL    ";7:run_word="STOPPED ";endcase
 reason_word=0;case(f[7:4])
REASON_CASES
 endcase
 ascii=32;glyph=0;
 if(fm==2)begin if(col>=21 && col<29)ascii=motion_word[(28-col)*8+:8];glyph=encode(ascii);end
 else if(fm==3)begin
 if(!row)begin
 case(col)0:ascii="T";1:ascii="E";2:ascii="A";3:ascii="C";4:ascii="H";
 15:ascii=48+time_bcd[11:8];16:ascii=48+time_bcd[7:4];17:ascii=".";18:ascii=48+time_bcd[3:0];19:ascii="/";
 20:ascii=48+duration_bcd[11:8];21:ascii=48+duration_bcd[7:4];22:ascii=".";23:ascii=48+duration_bcd[3:0];24:ascii="s";
 26:ascii="P";27:ascii=48+count_bcd[15:12];28:ascii=48+count_bcd[11:8];29:ascii=48+count_bcd[7:4];30:ascii=48+count_bcd[3:0];endcase
 if(col>=6 && col<14)ascii=state_word[(13-col)*8+:8];if(col>=32)ascii=reason_word[(63-col)*8+:8];
 end else if(f[55] && f[54])begin
 if(col<8)ascii=run_word[(7-col)*8+:8];
 case(col)9:ascii="N";10:ascii="E";11:ascii="X";12:ascii="T";14:ascii=fs!=5?65+fe:45;
 16:ascii="I";17:ascii="N";19:ascii=fi[0]?65:fi[1]?66:fi[2]?67:fi[3]?68:45;
 30:ascii="T";31:ascii=48+dwell_bcd[15:12];32:ascii=48+dwell_bcd[11:8];33:ascii=48+dwell_bcd[7:4];34:ascii=".";35:ascii=48+dwell_bcd[3:0];36:ascii="s";
 47:ascii="K";48:ascii="3";50:ascii="P";51:ascii="L";52:ascii="A";53:ascii="Y";55:ascii="K";56:ascii="4";58:ascii="S";59:ascii="T";60:ascii="O";61:ascii="P";endcase
 if(col>=21 && col<29)ascii=motion_word[(28-col)*8+:8];
 if(fs==6)case(col)47:ascii="E";48:ascii="X";49:ascii="P";50:ascii=32;51:ascii=65+fe;52:ascii=32;53:ascii="G";54:ascii="O";55:ascii="T";56:ascii=32;57:ascii=fa!=0?64+fa:45;58,59,60,61:ascii=32;endcase
 if(f[3:0]==7 && fs!=5 && col<8)ascii="INCOMP  "[(7-col)*8+:8];
 end else begin
 case(col)
HINT_CASES
 endcase
 if(f[55] && !f[54])begin
 if(col>=32)ascii=PLAY_KEYS[(63-col)*8+:8];
 else if(f[59:56]!=0)ascii="FINISH DRAFT. SEQ OFF            "[(31-col)*8+:8];
 else ascii="NO SAVED AREAS. SEQ OFF          "[(31-col)*8+:8];end
 end
 glyph=encode(ascii);end
 end
endmodule
`default_nettype wire
'''
    hint='K2 REC/STOP K3 PLAY K4 STOP K4 HOLD CLEAR'
    s=s.replace('STATE_CASES',cases(states,8,'state_word')).replace('REASON_CASES',cases(reasons,32,'reason_word'))
    s=s.replace('HINT_CASES','\n'.join(f'{i}:ascii=8\'d{ord(c)};' for i,c in enumerate(hint) if c!=' '))
    # Named constants avoid variable selection from literal strings in TD.
    constants='localparam [63:0] INCOMPLETE="INCOMP  ";localparam [255:0] DRAFT_OFF="'+ 'FINISH DRAFT. SEQ OFF'.ljust(32)+'",NO_AREAS="'+'NO SAVED AREAS. SEQ OFF'.ljust(32)+'";\n '
    constants+='localparam [255:0] PLAY_KEYS="'+'K3 PLAY K4 STOP K4 HOLD CLEAR'.ljust(32)+'";\n '
    s=s.replace('reg [63:0] state_word,motion_word,run_word;',constants+'reg [63:0] state_word,motion_word,run_word;')
    s=s.replace('"INCOMP  "[','INCOMPLETE[').replace('"FINISH DRAFT. SEQ OFF            "[','DRAFT_OFF[').replace('"NO SAVED AREAS. SEQ OFF          "[','NO_AREAS[')
    return s
