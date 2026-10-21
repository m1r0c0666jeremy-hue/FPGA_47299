"""Deterministic stage-one wrappers; the archived English RTL is an immutable base."""
from pathlib import Path
import argparse,re,json,hashlib
R=Path(__file__).resolve().parents[1]
CHARS=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()'
MESSAGES=['TIP READY','TOO FEW POINTS','SELF CROSS/ZERO','AREA TOUCH/OVER','MAX 4 AREAS','TIP NOT READY',
          'MAX 8 POINTS','NO SAVED AREAS','BUSY','FINISH DRAFT','LEAVE ALL AREAS','KEY2 START','KEY2 RETEST',
          'KEY3 RESUME','TRACK LOST','BRT FAILED']
RUN_NAMES=['IDLE','WAIT OUT','RUN','PAUSED','MOVE OUT','PASS','FAIL','STOPPED']

def ui_assets():
    ids={c:i for i,c in enumerate(CHARS)}
    rom=[0]*512
    for base,stride,values in [(0,16,MESSAGES),(256,8,[s[:8] for s in RUN_NAMES]),(320,8,['STABLE','APPROACH','AWAY'])]:
        for i,s in enumerate(values):
            assert len(s)<=stride
            for j,c in enumerate(s):rom[base+i*stride+j]=ids[c]
    text='module stage1_ui_text(input wire clk,input wire [8:0] addr,output reg [7:0] q);\n(* rom_style="bram" *)reg [7:0] mem[0:511];\ninitial begin\n'
    text+=''.join(f"mem[{i}]=8'd{v};\n" for i,v in enumerate(rom))+'end\nalways @(posedge clk)q<=mem[addr];\nendmodule\n'
    def layout():return ["8'd0"]*64
    def put(line,start,s):
        for i,c in enumerate(s):line[start+i]=f"8'd{ids[c]}"
    def digits(line,start,word):
        for i in range(4):line[start+i]=f"8'd1+{word}[{(3-i)*4}+:4]"
    edit=layout();put(edit,0,'EDIT ');edit[5]="fn<4?8'd11+fn:8'd41"
    put(edit,7,'PTS ');edit[11]="8'd1+fdraft";put(edit,12,'/8 SAVE ');edit[20]="8'd1+fn";put(edit,21,'/4')
    for i in range(24,40):edit[i]='rom_glyph'
    put(edit,40,' D');digits(edit,42,'distance_bcd');put(edit,46,'PX IN ')
    edit[52]="foccupied[0]?8'd11:foccupied[1]?8'd12:foccupied[2]?8'd13:foccupied[3]?8'd14:8'd41"
    put(edit,54,'T');digits(edit,55,'dwell_bcd');edit[58]="8'd39";edit[59]="8'd1+dwell_bcd[3:0]";put(edit,60,'s')
    edit[62]="ftrend==1?8'd11:ftrend==2?8'd11:8'd29";edit[63]="ftrend==1?8'd26:ftrend==2?8'd33:8'd30"
    test=layout()
    for i in range(8):test[i]='rom_glyph'
    put(test,9,'NEXT ');test[14]="fexpected<fn && fstate!=5?8'd11+fexpected:8'd41"
    put(test,16,'IN ');test[19]=edit[52];put(test,22,'D');digits(test,23,'distance_bcd');put(test,27,'PX T')
    test[31]="8'd1+dwell_bcd[15:12]";test[32]="8'd1+dwell_bcd[11:8]";test[33]="8'd1+dwell_bcd[7:4]";put(test,34,'.');test[35]="8'd1+dwell_bcd[3:0]";put(test,36,'s')
    for i in range(38,46):test[i]='rom_glyph'
    for i in range(47,63):test[i]='rom_glyph'
    fail=layout();put(fail,47,'EXP ');fail[51]="8'd11+fexpected";put(fail,52,' GOT ');fail[57]="factual!=0?8'd10+factual:8'd41"
    for i in range(47,64):test[i]=f"fstate==6?({fail[i]}):({test[i]})"
    for i,c in enumerate('MUTE'):test[60+i]=f"fmuted?8'd{ids[c]}:({test[60+i]})"
    normal=layout();put(normal,54,'BRT');normal[57]="8'd2+fslot";put(normal,58,'/7')
    busy=layout();put(busy,0,'BRIGHTNESS BUSY ');busy[16]="8'd2+fslot";put(busy,17,'/7 TO ');busy[23]="fslot==6?8'd2:8'd3+fslot";put(busy,24,'/7')
    failed=layout();put(failed,0,'BRT FAILED. KEY2 RETRY')
    reserved=layout();put(reserved,0,'ROUTE RESERVED')
    ui='''`default_nettype none
module stage1_ui_formatter(input wire clk,rst_n,latch,input wire [5:0] col,
 input wire [1:0] mode,input wire [3:0] run_state,input wire [2:0] area_count,draft_area,expected_area,actual_area,
 input wire [3:0] draft_count,occupied,input wire [10:0] distance,input wire [19:0] dwell_ms,
 input wire [1:0] trend,input wire [3:0] edit_error,start_error,input wire busy,tip_live,muted,gain_busy,gain_failed,
 input wire [2:0] gain_slot,input wire show,
 output reg [7:0] glyph,output wire override_enable,force_footer,
 output wire [3:0] snapshot_state,output wire [1:0] snapshot_mode);
 reg [1:0] fmode,ftrend;reg [3:0] fstate,fn,fdraft,foccupied,fedit,fstart;
 reg [2:0] fexpected,factual,fslot;reg fbusy,ftip,fmuted,fgain,fgain_failed,fshow;
 reg [10:0] fdistance;reg [19:0] divider,binary_a,binary_b;reg [6:0] remainder;
 reg [13:0] quotient;reg [15:0] bcd_a,bcd_b,distance_bcd,dwell_bcd,adjust_a,adjust_b;
 reg [1:0] conversion;reg [4:0] bit_index;reg [3:0] message_id;reg [8:0] rom_addr;wire [7:0] rom_glyph;
 stage1_ui_text text_rom(clk,rom_addr,rom_glyph);
 wire [7:0] shifted_remainder={remainder,divider[19]};wire qbit=shifted_remainder>=100;
 assign snapshot_state=fstate;assign snapshot_mode=fmode;
 assign force_footer=run_state==1 || run_state==3 || run_state==4 || run_state==6 || run_state==7;
 assign override_enable=fmode!=0 || fgain || fgain_failed || col>=54 || (!fshow && (fstate==1 || fstate==3 || fstate==4 || fstate==6 || fstate==7));
 integer i;
 always @*begin adjust_a=bcd_a;adjust_b=bcd_b;
 for(i=0;i<4;i=i+1)begin if(bcd_a[i*4+:4]>=5)adjust_a[i*4+:4]=bcd_a[i*4+:4]+3;
 if(bcd_b[i*4+:4]>=5)adjust_b[i*4+:4]=bcd_b[i*4+:4]+3;end end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin fmode<=0;ftrend<=0;fstate<=0;fn<=0;fdraft<=0;foccupied<=0;fedit<=0;fstart<=0;
 fexpected<=0;factual<=0;fslot<=5;fbusy<=0;ftip<=0;fmuted<=0;fgain<=0;fgain_failed<=0;fshow<=1;
 fdistance<=0;divider<=0;binary_a<=0;binary_b<=0;remainder<=0;quotient<=0;
 bcd_a<=0;bcd_b<=0;distance_bcd<=0;dwell_bcd<=0;conversion<=0;bit_index<=0;end
 else begin
 if(conversion==1)begin
 divider<=divider<<1;remainder<=qbit?shifted_remainder-100:shifted_remainder;quotient<={quotient[12:0],qbit};
 if(bit_index==19)begin binary_a<={9'd0,fdistance};binary_b<={6'd0,quotient[12:0],qbit};bcd_a<=0;bcd_b<=0;bit_index<=0;conversion<=2;end
 else bit_index<=bit_index+1'b1;
 end else if(conversion==2)begin
 binary_a<=binary_a<<1;binary_b<=binary_b<<1;bcd_a<={adjust_a[14:0],binary_a[19]};bcd_b<={adjust_b[14:0],binary_b[19]};
 if(bit_index==19)begin distance_bcd<={adjust_a[14:0],binary_a[19]};dwell_bcd<={adjust_b[14:0],binary_b[19]};conversion<=0;end else bit_index<=bit_index+1'b1;
 end
 if(latch)begin fmode<=mode;fstate<=run_state;fn<={1'b0,area_count};fdraft<=draft_count;foccupied<=occupied;
 fexpected<=expected_area;factual<=actual_area;ftrend<=trend;fedit<=edit_error;fstart<=start_error;
 fbusy<=busy;ftip<=tip_live;fmuted<=muted;fgain<=gain_busy;fgain_failed<=gain_failed;fslot<=gain_slot;fshow<=show;
 fdistance<=distance;divider<=dwell_ms;remainder<=0;quotient<=0;bit_index<=0;conversion<=1;end
 end end
 always @*begin
 message_id=fbusy?8:fedit!=0?fedit:!ftip?5:0;
 if(fmode==2 || !fshow)begin
 if(fstart!=0)case(fstart)1:message_id=7;2:message_id=9;3:message_id=5;default:message_id=8;endcase
 else case(fstate)0:message_id=11;1,4:message_id=10;3:message_id=13;5:message_id=12;7:message_id=14;default:message_id=0;endcase
 end
 rom_addr=0;
 if(fmode==1 && col>=24 && col<40)rom_addr={1'b0,message_id,4'd0}+col-24;
 if(fmode==2 || (!fshow && force_footer))begin
 if(col<8)rom_addr=9'd256+{2'd0,fstate,3'd0}+col;
 else if(col>=38 && col<46)rom_addr=9'd320+{4'd0,ftrend,3'd0}+col-38;
 else if(col>=47 && col<63)rom_addr={1'b0,message_id,4'd0}+col-47;
 end
 glyph=0;
'''
    for name,line in [('edit',edit),('test',test),('normal',normal),('busy',busy),('failed',failed),('reserved',reserved)]:
        ui+=f'// {name} layout\n'
        cond={'edit':'fmode==1','test':'fmode==2 || (!fshow && force_footer)','normal':'1\'b1','busy':'fgain','failed':'fgain_failed','reserved':'fmode==3'}[name]
        # Select layouts below with a function, avoiding priority surprises.
    ui+='end\n'
    for name,line in [('edit',edit),('test',test),('normal',normal),('busy',busy),('failed',failed),('reserved',reserved)]:
        ui+=f'function [7:0] {name}_char;input [5:0] column;begin {name}_char=0;case(column)\n'
        ui+=''.join(f"6'd{i}:{name}_char={expr};\n" for i,expr in enumerate(line) if expr!="8'd0")+'endcase end endfunction\n'
    ui+='''always @(col or fmode or fshow or fstate or fgain_failed or fgain or fn or fdraft or fexpected or factual or fmuted or fslot or foccupied or ftrend or distance_bcd or dwell_bcd or rom_glyph or force_footer)begin
 if(fmode==2 || (!fshow && (fstate==1 || fstate==3 || fstate==4 || fstate==6 || fstate==7)))glyph=test_char(col);
 else if(fmode==1)glyph=edit_char(col);else if(fgain_failed)glyph=failed_char(col);
 else if(fgain)glyph=busy_char(col);else if(fmode==3)glyph=reserved_char(col);else glyph=normal_char(col);
 end
endmodule
`default_nettype wire
'''
    # glyph is driven by the dedicated layout block, not the address block.
    ui=ui.replace(' glyph=0;\n','')
    return text,ui

def assets():
    out={}
    text,ui=ui_assets();out['rtl/color_regions/stage1_ui_text.v']=text;out['rtl/color_regions/stage1_ui_formatter.v']=ui
    top=(R/'rtl/color_regions/stable_top.v').read_text(encoding='utf-8')
    top=top.replace('output wire       O_screen_pwm,','output wire       O_buzzer,\n    output wire       O_screen_pwm,')
    a=top.index('refined_controls #');b=top.index('\nPLL u_PLL',a)
    top=top[:a]+'''wire [1:0] stage_mode;wire stage_down,stage_k2,stage_k3,stage_k4,stage_cancel,stage_gain_busy,stage_gain_failed,stage_alarm;
wire [2:0] stage_gain_slot;
stage1_controls u_controls(.I_clk(S_hdmi_pixel_clk),.I_rst_n(process_rst_n),.I_keys_n(I_button),.I_ui_switch(I_ui_switch),
 .I_gain_ack(gain_ack),.I_cal_status(ui_cal_status),.I_pause(camera_pause),.I_camera(camera_ui_status),
 .O_gain_req(gain_req),.O_gain_up(gain_up),.O_zoom(ui_zoom),.O_tracking(ui_tracking),.O_show(ui_show),.O_session(ui_session),
 .O_conflict(ui_conflict),.O_pair(ui_pair),.O_cal_enter(cal_enter),.O_cal_sample(cal_sample),.O_cal_cancel(cal_cancel),
 .O_rotate(ui_rotate),.O_diag(ui_diag),.O_ui_mode(stage_mode),.O_down2(stage_down),.O_click2(stage_k2),.O_click3(stage_k3),
 .O_click4(stage_k4),.O_cancel(stage_cancel),.O_gain_busy(stage_gain_busy),.O_gain_failed(stage_gain_failed),.O_gain_slot(stage_gain_slot));
stage1_buzzer buzzer_driver(I_sys_clk,I_rst_n && S_rst_n,stage_alarm,O_buzzer);
'''+top[b:]
    top=top.replace('stable_memory_video_out #','stage1_memory_video_out #')
    top=top.replace('u_video (','''u_video (
    .I_ui_mode(stage_mode),.I_key_down2(stage_down),.I_key2(stage_k2),.I_key3(stage_k3),.I_key4(stage_k4),.I_key_cancel(stage_cancel),
    .I_gain_busy(stage_gain_busy),.I_gain_failed(stage_gain_failed),.I_gain_slot(stage_gain_slot),.O_area_alarm(stage_alarm),''')
    out['rtl/color_regions/stage1_top.v']=top
    video=(R/'rtl/color_regions/stable_memory_video_out.v').read_text(encoding='utf-8').replace('module stable_memory_video_out','module stage1_memory_video_out')
    video=video.replace('input wire [31:0] I_source_id','''input wire [1:0] I_ui_mode,input wire I_key_down2,I_key2,I_key3,I_key4,I_key_cancel,
    input wire I_gain_busy,I_gain_failed,input wire [2:0] I_gain_slot,output wire O_area_alarm,
    input wire [31:0] I_source_id''')
    addition='''wire [2:0] area_count,area_expected,area_actual;wire [3:0] area_draft,area_state,area_completed,area_occupied,area_closed,area_edit_error,area_start_error;
    wire [15:0] area_revision,area_counts;wire [671:0] area_vertices;wire area_muted,area_busy,area_tip;
    wire [1:0] area_trend;wire [10:0] area_distance;wire [19:0] area_dwell;
    stage1_regions area_controller(.clk(I_pixel_clk),.rst_n(I_process_rst_n),.mode(I_ui_mode),.down2(I_key_down2),.click2(I_key2),.click3(I_key3),.click4(I_key4),.cancel(I_key_cancel),
     .tracking(I_tracking),.video_ok(video_ok && stream_pixel_n),.camera_ready(I_camera_ready),.gain_busy(I_gain_busy),.session(I_session),.pair(I_pair),
     .frame_commit(frame_commit),.detection_valid(detection_valid),.image_id(selected_frame_id),.meta(active_meta),
     .region_count(area_count),.draft_count(area_draft),.revision(area_revision),.render_vertices(area_vertices),.render_counts(area_counts),.closed_mask(area_closed),
     .run_state(area_state),.completed(area_completed),.occupied(area_occupied),.expected_area(area_expected),.actual_area(area_actual),.muted(area_muted),.alarm(O_area_alarm),
     .trend(area_trend),.distance(area_distance),.dwell_ms(area_dwell),.edit_error(area_edit_error),.start_error(area_start_error),.busy(area_busy),.tip_live(area_tip));
    stage1_osd u_osd (
     .I_ui_mode(I_ui_mode),.I_region_vertices(area_vertices),.I_region_counts(area_counts),.I_region_closed(area_closed),
     .I_area_count(area_count),.I_draft_count(area_draft),.I_run_state(area_state),.I_completed(area_completed),.I_occupied(area_occupied),
     .I_expected_area(area_expected),.I_actual_area(area_actual),.I_area_muted(area_muted),.I_area_trend(area_trend),.I_area_distance(area_distance),.I_area_dwell(area_dwell),
     .I_edit_error(area_edit_error),.I_start_error(area_start_error),.I_area_busy(area_busy),.I_tip_live(area_tip),
     .I_gain_busy(I_gain_busy),.I_gain_failed(I_gain_failed),.I_gain_slot(I_gain_slot),'''
    assert 'refined_osd u_osd (' in video
    video=video.replace('refined_osd u_osd (',addition)
    out['rtl/color_regions/stage1_memory_video_out.v']=video
    osd=(R/'rtl/color_regions/refined_osd.v').read_text(encoding='utf-8').replace('module refined_osd(','module stage1_osd(')
    osd=osd.replace('input wire I_clk,I_rst_n,I_vs','''input wire [1:0] I_ui_mode,input wire [671:0] I_region_vertices,input wire [15:0] I_region_counts,input wire [3:0] I_region_closed,
 input wire [2:0] I_area_count,I_expected_area,I_actual_area,input wire [3:0] I_draft_count,I_run_state,I_completed,I_occupied,
 input wire I_area_muted,input wire [1:0] I_area_trend,input wire [10:0] I_area_distance,input wire [19:0] I_area_dwell,
 input wire [3:0] I_edit_error,I_start_error,input wire I_area_busy,I_tip_live,I_gain_busy,I_gain_failed,input wire [2:0] I_gain_slot,
 input wire I_clk,I_rst_n,I_vs''')
    hook='''wire [3:0] region_pixel,stage_snapshot_state;wire [1:0] stage_snapshot_mode;
 wire [23:0] region_color,region_label_color;wire region_label_on,region_ready,region_underrun;
 wire [7:0] region_label_glyph,stage_glyph;wire [2:0] region_label_gx;wire [3:0] region_label_gy;
 wire stage_override,stage_force_footer;
 stage1_render region_render(I_clk,I_rst_n,I_geometry_commit,I_region_vertices,I_region_counts,I_region_closed,I_ui_mode,
 I_x0,I_y0,I_zoom,I_rotate,I_run_state,I_completed,I_expected_area,I_actual_area,x,y,I_de,
 region_pixel,region_color,region_label_on,region_label_glyph,region_label_gx,region_label_gy,region_label_color,region_ready,region_underrun);
 stage1_ui_formatter region_text(I_clk,I_rst_n,I_de && y==625 && x==0,format_col,I_ui_mode,I_run_state,I_area_count,3'd0,I_expected_area,I_actual_area,
 I_draft_count,I_occupied,I_area_distance,I_area_dwell,I_area_trend,I_edit_error,I_start_error,I_area_busy,I_tip_live,I_area_muted,I_gain_busy,I_gain_failed,
 I_gain_slot,I_show,stage_glyph,stage_override,stage_force_footer,stage_snapshot_state,stage_snapshot_mode);
'''
    osd=osd.replace(' always @(posedge I_clk or negedge I_rst_n)begin\n if(!I_rst_n)begin\n flat_valid',hook+' always @(posedge I_clk or negedge I_rst_n)begin\n if(!I_rst_n)begin\n flat_valid',1)
    osd=osd.replace('characters[(format_row?COLS:0)+format_col]<=decoded_glyph;',"characters[(format_row?COLS:0)+format_col]<=!format_row && fm[567:565]==0 && stage_override?stage_glyph:decoded_glyph;")
    osd=osd.replace('wire footer_current=footer_ready &&','wire footer_current=stage_snapshot_state==I_run_state && stage_snapshot_mode==I_ui_mode && footer_ready &&')
    osd=osd.replace('footer_text=1;','footer_text=I_show || stage_force_footer;if(!I_show && footer_row)footer_text=0;')
    marker=' end end\n wire [9:0] shared_font_addr='
    assert marker in osd
    osd=osd.replace(marker,''' end
 if(y<624 && I_show && I_video_ok && region_label_on && !back_on && !label_text)begin
 back_on=1;back=24'h101824;label_text=1;label_glyph=region_label_glyph;label_gx={1'b0,region_label_gx};label_gy=region_label_gy;ink=region_label_color;
 end end
 wire [9:0] shared_font_addr=''')
    osd=osd.replace('reg [23:0] ink_d,bg_d,rgb_d;','reg [23:0] ink_d,bg_d,rgb_d;reg region_enable_d;')
    osd=osd.replace('x<=0;y<=0;vs_last<=0;','region_enable_d<=0;x<=0;y<=0;vs_last<=0;')
    osd=osd.replace('footer_px_d<=footer_px;','region_enable_d<=I_show && I_video_ok;footer_px_d<=footer_px;')
    osd=osd.replace('label_d && shared_font_row[7-label_gx_d[2:0]]?ink_d:back_d?bg_d:rgb_d;',
                    'label_d && shared_font_row[7-label_gx_d[2:0]]?ink_d:back_d?bg_d:region_enable_d && region_pixel!=0?region_color:rgb_d;')
    out['rtl/color_regions/stage1_osd.v']=osd
    pins=(R/'td_project/target_lock.adc').read_text(encoding='utf-8')
    out['td_project/stage1_pins.adc']=pins+'\n# Board manual p20-21 / supplied 13_music: C12, high=silent.\nset_pin_assignment { O_buzzer } { LOCATION = C12; IOSTANDARD = LVCMOS33; DRIVESTRENGTH = 8; PULLTYPE = PULLUP; }\n'
    project=(R/'td_project/target_color_regions_refined.al').read_text(encoding='utf-8')
    project=re.sub(r'(<Project[^>]* Path=")[^"]+',r'\g<1>'+str(R/'td_project').replace('\\','/'),project,count=1)
    project=project.replace('<Name>target_color_regions_refined</Name>','<Name>target_color_regions_stage1</Name>')
    for old,new in [('stable_top.v','stage1_top.v'),('stable_memory_video_out.v','stage1_memory_video_out.v'),('refined_osd.v','stage1_osd.v')]:
        project=project.replace('../rtl/color_regions/'+old,'../rtl/color_regions/'+new)
    project=project.replace('Path="target_lock.adc"','Path="stage1_pins.adc"')
    stage_files=sorted(p.name for p in (R/'rtl/color_regions').glob('stage1_*.v'))
    stage_files=sorted(set(stage_files)|{Path(k).name for k in out if k.endswith('.v')})
    stage_files=[p for p in stage_files if p not in ('stage1_top.v','stage1_memory_video_out.v','stage1_osd.v')]
    additions=''
    for i,name in enumerate(stage_files,100):
        additions+=f'''            <File Path="../rtl/color_regions/{name}"><FileInfo><Attr Name="UsedInSyn" Val="true" /><Attr Name="UsedInP&amp;R" Val="true" /><Attr Name="BelongTo" Val="design_1" /><Attr Name="CompileOrder" Val="{i}" /></FileInfo></File>\n'''.replace('P&amp;R','P&R')
    project=project.replace('        </Verilog>',additions+'        </Verilog>')
    out['td_project/target_color_regions_stage1.al']=project
    build=(R/'scripts/run_refined_build.py').read_text(encoding='utf-8')
    build=build.replace('from osd_memory_branch import check_branch','from stage1_policy import check_branch')
    build=build.replace('from audit_refined import canonical_build_inputs','from stage1_policy import canonical_build_inputs')
    build=build.replace('target_color_regions_refined.al','target_color_regions_stage1.al')
    build=build.replace("R/'td_project/target_lock.adc'","R/'td_project/stage1_pins.adc'")
    build=build.replace("f'refined_{a.stage}_{stamp}'","f'stage1_{a.stage}_{stamp}'")
    build=build.replace("script=out/'run.tcl';script.write_text(t,encoding='utf-8')","t=t.replace('td_project target_lock.adc','td_project stage1_pins.adc')\nscript=out/'run.tcl';script.write_text(t,encoding='utf-8')")
    out['scripts/run_stage1_build.py']=build
    route=(R/'scripts/run_refined_route.py').read_text(encoding='utf-8')
    route=route.replace('from osd_memory_branch import check_branch','from stage1_policy import check_branch')
    route=route.replace("f'refined_route_{stamp}'","f'stage1_route_{stamp}'")
    out['scripts/run_stage1_route.py']=route
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
    generated=assets()
    for name,s in generated.items():
        p=R/name
        if a.check:assert p.is_file() and p.read_bytes()==s.encode('utf-8'),'Generated mismatch '+name
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(s.encode('utf-8'))
    print('STAGE1_GENERATOR_CHECK_PASS' if a.check else 'STAGE1_GENERATED',len(generated))

if __name__=='__main__':main()
