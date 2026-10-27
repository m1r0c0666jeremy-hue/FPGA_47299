"""Stage-one K wrappers; the archived detector/capture implementations stay intact.

The wrappers share one sequential 20-bit ALU across both endpoint coordinates.
K travels with the command and is frozen with each owned capture bank.
"""
from pathlib import Path
R = Path(__file__).resolve().parents[1]


def tracker_source():
    s = (R/'rtl/color_regions/stable_tracker.v').read_text(encoding='utf-8')
    s = s.replace('module stable_tracker(', 'module stage1_k_tracker(')
    s = s.replace('output reg [3:0] tip_bounds);',
                  'output reg [3:0] tip_bounds,input wire [7:0] k_value);')
    old = ''' // Round the complete (3*A-B)/2 once, including negative/outside results.
 nt_x=half_away(($signed({3'd0,fax})<<<1)+$signed({3'd0,fax})-$signed({3'd0,fbx}));
 nt_y=half_away(($signed({4'd0,fay})<<<1)+$signed({4'd0,fay})-$signed({4'd0,fby}));'''
    assert old in s
    s = s.replace(old, '')
    marker = ' assign history_valid='
    helper = ''' reg k_axis,k_negative;reg [7:0] k_frozen,k_shift;
 reg [4:0] k_bit;reg [19:0] k_acc,k_addend,k_number,k_quotient,k_rounded;
 reg [6:0] k_remainder;reg [19:0] k_alu_a,k_alu_b;
 wire [19:0] k_sum=k_alu_a+k_alu_b;
 wire [10:0] k_a=k_axis?{1'b0,fay}:fax,k_b=k_axis?{1'b0,fby}:fbx;
 wire signed [11:0] k_delta=$signed({1'b0,k_a})-$signed({1'b0,k_b});
 wire [7:0] k_trial={k_remainder,k_number[19]};
 wire k_take=k_trial>=100;
 always @*begin
 k_alu_a=0;k_alu_b=0;
 case(state)
 11:begin k_alu_a=k_acc;k_alu_b={4'd0,k_a,5'd0};end
 12:begin k_alu_a=k_acc;k_alu_b={7'd0,k_a,2'd0};end
 13:begin k_alu_a=k_acc;k_alu_b=k_shift[0]?k_addend:20'd0;end
 14:begin k_alu_a=k_acc[19]?~k_acc:k_acc;k_alu_b=k_acc[19]?20'd1:20'd0;end
 15:begin k_alu_a={12'd0,k_trial};k_alu_b=k_take?-20'd100:20'd0;end
 16:begin k_alu_a=k_quotient;k_alu_b=k_remainder>=50?20'd1:20'd0;end
 17:begin k_alu_a=k_negative?~k_rounded:k_rounded;k_alu_b=k_negative?20'd1:20'd0;end
 default:begin end
 endcase end
'''
    assert marker in s
    s = s.replace(marker, helper+marker, 1)
    s = s.replace('state<=0;done<=0;', '''k_axis<=0;k_negative<=0;k_frozen<=50;k_shift<=0;k_bit<=0;
 k_acc<=0;k_addend<=0;k_number<=0;k_quotient<=0;k_rounded<=0;k_remainder<=0;nt_x<=0;nt_y<=0;
 state<=0;done<=0;''', 1)
    s = s.replace('0:if(start)begin', '0:if(start)begin\n k_frozen<=k_value;', 1)
    old = ' 5:begin\n tip_bounds<='
    assert old in s
    math = ''' // Build N=100*A+k*(A-B), then round the complete signed N/100.
 // Do not round the offset separately: negative half-pixel offsets differ.
 5:begin k_axis<=0;state<=10;end
 10:begin k_acc<={3'd0,k_a,6'd0};state<=11;end
 11:begin k_acc<=k_sum;state<=12;end
 12:begin k_acc<=k_sum;k_addend<={{8{k_delta[11]}},k_delta};k_shift<=k_frozen;k_bit<=0;state<=13;end
 13:begin k_acc<=k_sum;k_addend<=k_addend<<1;k_shift<=k_shift>>1;
 if(k_bit==7)state<=14;else k_bit<=k_bit+1'b1;end
 14:begin k_negative<=k_acc[19];k_number<=k_sum;k_quotient<=0;k_remainder<=0;k_bit<=0;state<=15;end
 15:begin k_number<=k_number<<1;k_quotient<={k_quotient[18:0],k_take};k_remainder<=k_sum[6:0];
 if(k_bit==19)state<=16;else k_bit<=k_bit+1'b1;end
 16:begin k_rounded<=k_sum;state<=17;end
 17:begin
 if(!k_axis)begin nt_x<=k_sum[13:0];k_axis<=1;state<=10;end
 else begin nt_y<=k_sum[13:0];state<=18;end end
 18:begin
 tip_bounds<='''
    s = s.replace(old, math)
    return '// Shared-K endpoint wrapper generated from the immutable detector.\n'+s


def capture_source():
    s = (R/'rtl/color_regions/stable_capture.v').read_text(encoding='utf-8')
    s = s.replace('module stable_capture #', 'module stage1_k_capture #')
    s = s.replace('output reg O_time_valid);', 'output reg O_time_valid,input wire [7:0] I_k_value);')
    s = s.replace('reg [31:0] ids[0:1];', 'reg [7:0] bank_k[0:1];reg [31:0] ids[0:1];')
    s = s.replace('stable_tracker tracker(', 'stage1_k_tracker tracker(')
    s = s.replace('hist_frame,hist_loss,tip_bounds);', 'hist_frame,hist_loss,tip_bounds,bank_k[wb]);')
    s = s.replace('packet=0;', '''packet=0;
 packet[230:224]=bank_k[wb][6:0];packet[248]=bank_k[wb][7];packet[249]=1;''', 1)
    s = s.replace('begin ids[i]<=0;', 'begin bank_k[i]<=50;ids[i]<=0;', 1)
    s = s.replace('owned[nb]<=1;closed[nb]<=0;', 'bank_k[nb]<=I_k_value;owned[nb]<=1;closed[nb]<=0;', 1)
    assert 'bank_k[nb]<=I_k_value;' in s
    return '// K and command are frozen at the same accepted image start.\n'+s


def decorate(out):
    top = out['rtl/color_regions/stage1_top.v']
    top = top.replace('wire [2:0] stage_gain_slot;', 'wire [7:0] stage_k_value;wire stage_k_adjust;wire [2:0] stage_gain_slot;')
    top = top.replace('.O_gain_target(stage_gain_target));',
                      '.O_gain_target(stage_gain_target),.O_k_value(stage_k_value),.O_k_adjust(stage_k_adjust));')
    top = top.replace('.I_ui_mode(stage_mode),', '.I_k_value(stage_k_value),.I_k_adjust(stage_k_adjust),.I_ui_mode(stage_mode),')
    out['rtl/color_regions/stage1_top.v'] = top
    v = out['rtl/color_regions/stage1_memory_video_out.v']
    v = v.replace('input wire [1:0] I_ui_mode,', 'input wire [7:0] I_k_value,input wire I_k_adjust,input wire [1:0] I_ui_mode,', 1)
    v = v.replace('wire [9:0] command_data;', 'wire [17:0] command_data;')
    v = v.replace('reg [9:0] command_sent,command_active;', 'reg [17:0] command_sent,command_active;')
    v = v.replace('wire [9:0] command_now={I_pair,I_session,I_tracking};',
                  'wire [17:0] command_now={I_k_value,I_pair,I_session,I_tracking};')
    v = v.replace('target_mailbox #(.WIDTH(10)) u_command(', 'target_mailbox #(.WIDTH(18)) u_command(')
    v = v.replace('.S_data(command_now),.S_ready(snap_request_ready)', '.S_data(command_now[9:0]),.S_ready(snap_request_ready)')
    v = v.replace('stable_capture #(.V4(1)) u_detection(', 'stage1_k_capture #(.V4(1)) u_detection(.I_k_value(command_active[17:10]),')
    v = v.replace('stage1_scene area_controller(', 'stage1_scene area_controller(.current_k(I_k_value),')
    v = v.replace('stage1_osd u_osd (', 'stage1_osd u_osd (.I_k_value(I_k_value),.I_k_adjust(I_k_adjust),')
    # Definitions stay in an existing project member: no user TD file changes.
    v += '\n'+capture_source()+'\n'+tracker_source()
    out['rtl/color_regions/stage1_memory_video_out.v'] = v
    s = out['rtl/color_regions/stage1_osd.v']
    s = s.replace('input wire [22:0] I_point\n', 'input wire [22:0] I_point,input wire [7:0] I_k_value,input wire I_k_adjust\n', 1)
    s = s.replace('status_id,I_tip_reason);', 'status_id,I_tip_reason,I_k_value,I_k_adjust);')
    s = s.replace('teaching_glyph,teaching_override);', 'teaching_glyph,teaching_override,I_k_value);')
    s = s.replace('reg [4:0] status_id;', '''reg [7:0] stage_camera_snapshot;
 wire stage_camera_dead=stage_camera_snapshot[7:4]==9 && stage_camera_snapshot[3:0]>=1 && stage_camera_snapshot[3:0]<=5;
 always @(posedge I_clk or negedge I_rst_n)
 if(!I_rst_n)stage_camera_snapshot<=0;
 else if(I_de && y==625 && x==0)stage_camera_snapshot<=I_camera[16:9];
 reg [4:0] status_id;''', 1)
    marker='if(!fvideo || fstate==6)status_id=16;'
    assert marker in s
    s = s.replace(marker,marker+'''
 if(stage_camera_dead)case(stage_camera_snapshot[3:0])
 1:status_id=20;2:status_id=21;3:status_id=22;4:status_id=23;5:status_id=24;
 endcase''', 1)
    marker='characters[(format_row?COLS:0)+format_col]<='
    assert marker in s
    # Name a latched fatal camera fault even with stale calibration metadata or
    # replay's whole-row override. Keep normal/calibration/replay layouts exact.
    s = s.replace(marker,marker+'format_row && stage_camera_dead && format_col>=42?stage_glyph:', 1)
    out['rtl/color_regions/stage1_osd.v'] = s
