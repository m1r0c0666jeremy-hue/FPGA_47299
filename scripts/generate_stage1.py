"""Deterministic stage-one wrappers; the archived English RTL is an immutable base."""
from pathlib import Path
import argparse,re,json,hashlib
R=Path(__file__).resolve().parents[1]
CHARS=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()'
MESSAGES=['TIP READY','SET TWO CORNERS','RECT TOO SMALL','AREA TOUCH/OVER','MAX 4 AREAS','TIP NOT READY',
          'MAX 2 CORNERS','NO SAVED AREAS','BUSY','FINISH DRAFT','LEAVE ALL AREAS','KEY2 START','KEY2 RETEST',
          'KEY3 RESUME','TRACK LOST','BRT FAILED']
RUN_NAMES=['IDLE','WAIT OUT','RUN','PAUSED','MOVE OUT','PASS','FAIL','STOPPED']

from stage1_behavior_ui import ui_assets

def assets():
    out={}
    text,ui=ui_assets();out['rtl/color_regions/stage1_ui_text.v']=text;out['rtl/color_regions/stage1_ui_formatter.v']=ui
    top=(R/'rtl/color_regions/stable_top.v').read_text(encoding='utf-8')
    top=top.replace('output wire       O_screen_pwm,','output wire       O_buzzer,\n    output wire       O_screen_pwm,')
    a=top.index('refined_controls #');b=top.index('\nPLL u_PLL',a)
    top=top[:a]+'''wire [1:0] stage_mode;wire stage_down,stage_k2,stage_k3,stage_k4,stage_cancel,stage_gain_busy,stage_gain_failed,stage_alarm;
wire [2:0] stage_gain_slot;wire [6:0] stage_gain_target;
stage1_controls u_controls(.I_clk(S_hdmi_pixel_clk),.I_rst_n(process_rst_n),.I_keys_n(I_button),.I_ui_switch(I_ui_switch),
 .I_gain_ack(gain_ack),.I_cal_status(ui_cal_status),.I_pause(camera_pause),.I_camera(camera_ui_status),
 .O_gain_req(gain_req),.O_gain_up(gain_up),.O_zoom(ui_zoom),.O_tracking(ui_tracking),.O_show(ui_show),.O_session(ui_session),
 .O_conflict(ui_conflict),.O_pair(ui_pair),.O_cal_enter(cal_enter),.O_cal_sample(cal_sample),.O_cal_cancel(cal_cancel),
 .O_rotate(ui_rotate),.O_diag(ui_diag),.O_ui_mode(stage_mode),.O_down2(stage_down),.O_click2(stage_k2),.O_click3(stage_k3),
 .O_click4(stage_k4),.O_cancel(stage_cancel),.O_gain_busy(stage_gain_busy),.O_gain_failed(stage_gain_failed),.O_gain_slot(stage_gain_slot),.O_gain_target(stage_gain_target));
stage1_buzzer #(.CLOCK_HZ(75000000)) buzzer_driver(S_hdmi_pixel_clk,process_rst_n,stage_alarm,O_buzzer);
'''+top[b:]
    top=top.replace('stable_memory_video_out #','stage1_memory_video_out #')
    top=top.replace('u_video (','''u_video (
    .I_ui_mode(stage_mode),.I_key_down2(stage_down),.I_key2(stage_k2),.I_key3(stage_k3),.I_key4(stage_k4),.I_key_cancel(stage_cancel),
    .I_gain_busy(stage_gain_busy),.I_gain_failed(stage_gain_failed),.I_gain_slot(stage_gain_slot),.I_gain_target(stage_gain_target),.O_area_alarm(stage_alarm),''')
    out['rtl/color_regions/stage1_top.v']=top
    video=(R/'rtl/color_regions/stable_memory_video_out.v').read_text(encoding='utf-8').replace('module stable_memory_video_out','module stage1_memory_video_out')
    video=video.replace('input wire [31:0] I_source_id','''input wire [1:0] I_ui_mode,input wire I_key_down2,I_key2,I_key3,I_key4,I_key_cancel,
    input wire I_gain_busy,I_gain_failed,input wire [2:0] I_gain_slot,input wire [6:0] I_gain_target,output wire O_area_alarm,
    input wire [31:0] I_source_id''')
    addition='''wire area_associated,area_video;wire [3:0] area_tip_reason;
    stage1_input_guard region_input(I_pixel_clk,I_process_rst_n,stream_pixel_n,I_tracking,I_camera_ready,I_gain_busy,
     video_ok,S_hdmi_out_de,frame_commit,I_session,I_pair,selected_frame_id,image_epoch,image_us,image_time_valid,active_meta,area_associated,area_video);
    wire [2:0] area_count,area_expected,area_actual;wire [3:0] area_draft,area_state,area_completed,area_occupied,area_closed,area_edit_error,area_start_error;
    wire [15:0] area_revision,area_counts;wire [671:0] area_vertices,area_saved_vertices;wire [167:0] area_draft_vertices;wire area_muted,area_busy,area_tip,area_metrics_valid;
    wire [1:0] area_trend;wire [10:0] area_distance;wire [19:0] area_dwell;
    stage1_regions area_controller(.clk(I_pixel_clk),.rst_n(I_process_rst_n),.mode(I_ui_mode),.down2(I_key_down2),.click2(I_key2),.click3(I_key3),.click4(I_key4),.cancel(I_key_cancel),
     .tracking(I_tracking),.video_ok(area_video),.camera_ready(I_camera_ready),.gain_busy(I_gain_busy),.session(I_session),.pair(I_pair),
     .frame_commit(frame_commit),.detection_valid(area_associated),.image_id(selected_frame_id),.meta(active_meta),
     .region_count(area_count),.draft_count(area_draft),.revision(area_revision),.render_vertices(area_vertices),.render_counts(area_counts),.closed_mask(area_closed),
     .run_state(area_state),.completed(area_completed),.occupied(area_occupied),.expected_area(area_expected),.actual_area(area_actual),.muted(area_muted),.alarm(O_area_alarm),
     .trend(area_trend),.distance(area_distance),.dwell_ms(area_dwell),.edit_error(area_edit_error),.start_error(area_start_error),.busy(area_busy),.tip_live(area_tip),.metrics_valid(area_metrics_valid),.saved_vertices(area_saved_vertices),.draft_vertices(area_draft_vertices),.tip_reason(area_tip_reason));
    stage1_osd u_osd (
     .I_ui_mode(I_ui_mode),.I_region_vertices(area_saved_vertices),.I_region_draft(area_draft_vertices),.I_region_counts(area_counts),.I_region_closed(area_closed),
     .I_area_count(area_count),.I_draft_count(area_draft),.I_run_state(area_state),.I_completed(area_completed),.I_occupied(area_occupied),
     .I_expected_area(area_expected),.I_actual_area(area_actual),.I_area_muted(area_muted),.I_area_trend(area_trend),.I_area_distance(area_distance),.I_area_dwell(area_dwell),
     .I_edit_error(area_edit_error),.I_start_error(area_start_error),.I_area_busy(area_busy || (area_tip && area_count!=0 && !area_metrics_valid)),.I_tip_live(area_tip),
     .I_gain_busy(I_gain_busy),.I_gain_failed(I_gain_failed),.I_gain_slot(I_gain_slot),.I_gain_target(I_gain_target),.I_tip_reason(area_tip_reason),'''
    assert 'refined_osd u_osd (' in video
    video=video.replace('refined_osd u_osd (',addition)
    out['rtl/color_regions/stage1_memory_video_out.v']=video
    osd=(R/'rtl/color_regions/refined_osd.v').read_text(encoding='utf-8').replace('module refined_osd(','module stage1_osd(')
    osd=osd.replace('input wire I_clk,I_rst_n,I_vs','''input wire [1:0] I_ui_mode,input wire [671:0] I_region_vertices,input wire [167:0] I_region_draft,input wire [15:0] I_region_counts,input wire [3:0] I_region_closed,
 input wire [2:0] I_area_count,I_expected_area,I_actual_area,input wire [3:0] I_draft_count,I_run_state,I_completed,I_occupied,
 input wire I_area_muted,input wire [1:0] I_area_trend,input wire [10:0] I_area_distance,input wire [19:0] I_area_dwell,
 input wire [3:0] I_edit_error,I_start_error,input wire I_area_busy,I_tip_live,I_gain_busy,I_gain_failed,input wire [2:0] I_gain_slot,
 input wire I_clk,I_rst_n,I_vs''')
    osd=osd.replace('input wire [17:0] I_camera\n', 'input wire [17:0] I_camera,input wire [6:0] I_gain_target,input wire [3:0] I_tip_reason\n')
    hook='''wire [3:0] region_pixel,stage_snapshot_state;wire [1:0] stage_snapshot_mode;
 wire [23:0] region_color,region_label_color;wire region_label_on,region_ready,region_underrun;
 wire [7:0] region_label_glyph,stage_glyph;wire [2:0] region_label_gx;wire [3:0] region_label_gy;
 wire stage_override,stage_force_footer;
 stage1_render #(.SPLIT_DRAFT(1)) region_render(I_clk,I_rst_n,I_geometry_commit,I_region_vertices,I_region_counts,I_region_closed,I_ui_mode,
 I_x0,I_y0,I_zoom,I_rotate,I_run_state,I_completed,I_expected_area,I_actual_area,x,y,I_de,
 region_pixel,region_color,region_label_on,region_label_glyph,region_label_gx,region_label_gy,region_label_color,region_ready,region_underrun,I_region_draft,I_area_count,I_draft_count!=0);
 stage1_ui_formatter region_text(I_clk,I_rst_n,I_de && y==625 && x==0,format_col,I_ui_mode,I_run_state,I_area_count,3'd0,I_expected_area,I_actual_area,
 I_draft_count,I_occupied,I_area_distance,I_area_dwell,I_area_trend,I_edit_error,I_start_error,(I_area_busy || region_underrun || (!region_ready && I_region_counts!=0)),I_tip_live,I_area_muted,I_gain_busy,I_gain_failed,
 I_gain_slot,I_show,stage_glyph,stage_override,stage_force_footer,stage_snapshot_state,stage_snapshot_mode,format_row,I_camera[6:0],I_gain_target,I_zoom,I_mode,I_pair,I_rotate,status_id,I_tip_reason);
'''
    osd=osd.replace(' always @(posedge I_clk or negedge I_rst_n)begin\n if(!I_rst_n)begin\n flat_valid',hook+' always @(posedge I_clk or negedge I_rst_n)begin\n if(!I_rst_n)begin\n flat_valid',1)
    osd=osd.replace('characters[(format_row?COLS:0)+format_col]<=decoded_glyph;',"characters[(format_row?COLS:0)+format_col]<=fm[567:565]==0 && stage_override?stage_glyph:decoded_glyph;")
    osd=osd.replace('wire footer_current=footer_ready &&','wire footer_current=stage_snapshot_state==I_run_state && stage_snapshot_mode==I_ui_mode && footer_ready &&')
    # Both footer rows remain visible when video overlays are disabled.
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
    stage_files=[p for p in stage_files if p not in ('stage1_top.v','stage1_memory_video_out.v','stage1_osd.v','stage1_arith.v','stage1_point.v','stage1_segment.v','stage1_validate.v')]
    additions=''
    for i,name in enumerate(stage_files,100):
        additions+=f'''            <File Path="../rtl/color_regions/{name}"><FileInfo><Attr Name="UsedInSyn" Val="true" /><Attr Name="UsedInP&amp;R" Val="true" /><Attr Name="BelongTo" Val="design_1" /><Attr Name="CompileOrder" Val="{i}" /></FileInfo></File>\n'''.replace('P&amp;R','P&R')
    project=project.replace('        </Verilog>',additions+'        </Verilog>')
    from stage1_project import check_project
    check_project(R/'td_project/target_color_regions_stage1.al',project)
    build=(R/'scripts/run_refined_build.py').read_text(encoding='utf-8')
    # Vendor AdderChainThresholdHigh uses min_ripple_len=18. Expose the same
    # synthesis-only choice without enabling expensive extra gate mapping.
    build=build.replace("ap.add_argument('--checkpoint',action='store_true')", "ap.add_argument('--min-ripple-len',type=int,choices=range(1,65))\nap.add_argument('--checkpoint',action='store_true')")
    build=build.replace("if a.infer_fsm!='project':", "if a.min_ripple_len is not None:t=t.replace('    optimize_rtl',f'    set_param rtl min_ripple_len {a.min_ripple_len}\\n    optimize_rtl')\nif a.infer_fsm!='project':")
    build=build.replace('infer_fsm=a.infer_fsm,','infer_fsm=a.infer_fsm,min_ripple_len=a.min_ripple_len,')
    build=build.replace('from osd_memory_branch import check_branch','from stage1_policy import check_branch')
    build=build.replace('from audit_refined import canonical_build_inputs','from stage1_policy import canonical_build_inputs')
    build=build.replace('target_color_regions_refined.al','target_color_regions_stage1.al')
    build=build.replace("R/'td_project/target_lock.adc'","R/'td_project/stage1_pins.adc'")
    build=build.replace("f'refined_{a.stage}_{stamp}'","f'stage1_{a.stage}_{stamp}'")
    build=build.replace("script=out/'run.tcl';script.write_text(t,encoding='utf-8')","t=t.replace('td_project target_lock.adc','td_project stage1_pins.adc')\nscript=out/'run.tcl';script.write_text(t,encoding='utf-8')")
    from stage1_build_reuse import add_gate_reuse
    out['scripts/run_stage1_build.py']=add_gate_reuse(build)
    route=(R/'scripts/run_refined_route.py').read_text(encoding='utf-8')
    route=route.replace('from osd_memory_branch import check_branch','from stage1_policy import check_branch')
    route=route.replace("f'refined_route_{stamp}'","f'stage1_route_{stamp}'")
    out['scripts/run_stage1_route.py']=route
    from stage1_teaching_codegen import decorate
    decorate(out)
    from stage1_k_datapath import decorate as decorate_k
    decorate_k(out)
    from stage1_display_shared import decorate as decorate_display
    decorate_display(out)
    from stage1_release1030 import decorate as decorate_release
    decorate_release(out)
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
