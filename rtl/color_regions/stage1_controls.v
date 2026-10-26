// Stage-one UI: release-confirmed short keys; chords/long holds consume all keys.
`default_nettype none
module stage1_controls #(parameter CYCLES_PER_MS=75000,DEBOUNCE_MS=20,LONG_PRESS_MS=1000,CHORD_WINDOW_MS=100)(
 input wire I_clk,I_rst_n,input wire [2:0] I_keys_n,input wire [1:0] I_ui_switch,
 input wire I_gain_ack,input wire [7:0] I_cal_status,input wire I_pause,
 input wire [17:0] I_camera,
 output reg O_gain_req,O_gain_up,output reg [2:0] O_zoom,
 output reg O_tracking,O_show,output reg [7:0] O_session,
 output wire O_conflict,output reg O_pair,output reg O_cal_enter,O_cal_sample,O_cal_cancel,
 output reg O_rotate,output wire [1:0] O_diag,output reg [1:0] O_ui_mode,
 output reg O_down2,O_click2,O_click3,O_click4,O_cancel,
 output reg O_gain_busy,O_gain_failed,output reg [2:0] O_gain_slot,output wire [6:0] O_gain_target);
 (* async_reg="true" *)reg [2:0] k1,k2;(* async_reg="true" *)reg [1:0] s1,s2;
 (* async_reg="true" *)reg [1:0] ack_sync;
 reg [2:0] key_candidate,keys,previous,gesture,chord;reg [1:0] switch_candidate;
 reg [7:0] kd,sd;reg [16:0] ms;reg [15:0] held;reg [7:0] window_age;
 reg consumed,conflict,cal_ui,cal_seen;reg [6:0] target_gain,step_gain;
 reg [2:0] target_slot;reg gain_wait;reg [12:0] gain_age;
 wire tick=ms==CYCLES_PER_MS-1;wire [2:0] pressed=~keys;
 wire accepting_mode=tick && s2==switch_candidate && sd==DEBOUNCE_MS-1 && O_ui_mode!=switch_candidate;
 wire valid_chord=pressed==3 || pressed==5 || pressed==6;
 wire camera_ready=I_camera[17];wire [6:0] applied_gain=I_camera[6:0];
 assign O_gain_target=target_gain;
 assign O_conflict=conflict || pressed==7;assign O_diag=0;
 function [6:0] gain_at;input [2:0] slot;begin
 case(slot)0:gain_at=16;1:gain_at=32;2:gain_at=48;3:gain_at=64;4:gain_at=80;5:gain_at=90;default:gain_at=105;endcase end endfunction
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin k1<=7;k2<=7;s1<=0;s2<=0;ack_sync<=0;end
 else begin k1<=I_keys_n;k2<=k1;s1<=I_ui_switch;s2<=s1;ack_sync<={ack_sync[0],I_gain_ack};end end
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin key_candidate<=7;keys<=7;previous<=0;gesture<=0;chord<=0;switch_candidate<=0;
 kd<=0;sd<=0;ms<=0;held<=0;window_age<=0;consumed<=0;conflict<=0;cal_ui<=0;cal_seen<=0;
 O_gain_req<=0;O_gain_up<=0;O_zoom<=0;O_tracking<=0;O_show<=1;O_session<=0;O_pair<=0;
 O_cal_enter<=0;O_cal_sample<=0;O_cal_cancel<=0;O_rotate<=1;O_ui_mode<=0;
 O_down2<=0;O_click2<=0;O_click3<=0;O_click4<=0;O_cancel<=0;
 O_gain_busy<=0;O_gain_failed<=0;O_gain_slot<=5;target_slot<=5;target_gain<=90;step_gain<=90;gain_wait<=0;gain_age<=0;end
 else begin
 O_down2<=0;O_click2<=0;O_click3<=0;O_click4<=0;O_cancel<=0;
 if(tick)ms<=0;else ms<=ms+1'b1;
 if(I_cal_status[7:5]!=0)cal_seen<=1;
 if(cal_ui && cal_seen && I_cal_status[7:5]==0)begin cal_ui<=0;cal_seen<=0;end
 // Expected parameter events stop tracking but must not cancel this controller.
 if(O_gain_busy)begin
 if(tick && gain_age<5000)gain_age<=gain_age+1'b1;
 if(I_camera[16:13]==9 || gain_age==5000)begin O_gain_busy<=0;O_gain_failed<=1;gain_wait<=0;end
 else if(gain_wait)begin
 if(O_gain_req==ack_sync[1] && applied_gain==step_gain)gain_wait<=0;
 end else if(O_gain_req==ack_sync[1])begin
 if(applied_gain==target_gain)begin
 if(camera_ready)begin O_gain_busy<=0;O_gain_slot<=target_slot;end end
 else if(I_camera[16:13]==6 || I_camera[16:13]==7)begin
 O_gain_up<=applied_gain<target_gain;O_gain_req<=~O_gain_req;
 step_gain<=applied_gain<target_gain?applied_gain+1'b1:applied_gain-1'b1;gain_wait<=1;
 end end end
 if(tick)begin
 if(k2!=key_candidate)begin key_candidate<=k2;kd<=0;end
 else if(kd<DEBOUNCE_MS)begin kd<=kd+1'b1;if(kd==DEBOUNCE_MS-1)keys<=key_candidate;end
 if(s2!=switch_candidate)begin switch_candidate<=s2;sd<=0;end
 else if(sd<DEBOUNCE_MS)begin sd<=sd+1'b1;
 if(sd==DEBOUNCE_MS-1 && O_ui_mode!=switch_candidate)begin
 O_ui_mode<=switch_candidate;O_cancel<=1;consumed<=pressed!=0;
 if(cal_ui)begin O_cal_cancel<=~O_cal_cancel;cal_ui<=0;cal_seen<=0;end end end
 if(pressed!=previous)begin previous<=pressed;
 if(pressed==0)begin
 if(!consumed && chord==0 && held<LONG_PRESS_MS && !accepting_mode)begin
 if(cal_ui)begin
 if(gesture==1)begin O_cal_cancel<=~O_cal_cancel;cal_ui<=0;cal_seen<=0;end
 if(gesture==2)O_cal_sample<=~O_cal_sample;
 end else case(gesture)
 1:if(O_ui_mode==0)begin
 if(!O_gain_busy && camera_ready && O_gain_req==ack_sync[1])begin
 target_slot<=O_gain_slot==6?0:O_gain_slot+1'b1;target_gain<=gain_at(O_gain_slot==6?3'd0:O_gain_slot+1'b1);
 O_gain_busy<=1;O_gain_failed<=0;gain_wait<=0;gain_age<=0;O_tracking<=0;O_session<=O_session+1'b1;end
 else conflict<=1;end else O_click2<=1;
 2:if(O_ui_mode==0)O_zoom<=O_zoom==4?0:O_zoom+1'b1;else O_click3<=1;
 4:if(O_ui_mode==0)begin O_pair<=~O_pair;O_session<=O_session+1'b1;end
 else O_click4<=1;
 default:begin end
 endcase end
 gesture<=0;chord<=0;held<=0;window_age<=0;consumed<=0;conflict<=0;
 end else if(previous==0 && !consumed)begin
 gesture<=pressed;held<=0;window_age<=0;chord<=valid_chord?pressed:0;
 if(pressed==1 && !cal_ui && O_ui_mode==1 && !accepting_mode)O_down2<=1;
 if(pressed==7)begin consumed<=1;conflict<=1;O_cancel<=1;end
 end else if(!consumed && chord==0 && valid_chord && window_age<CHORD_WINDOW_MS)begin
 chord<=pressed;held<=0;O_cancel<=1;
 end else begin consumed<=1;O_cancel<=1;if(chord==0)conflict<=1;end
 end else if(pressed!=0)begin
 if(held<65535)held<=held+1'b1;if(window_age<CHORD_WINDOW_MS)window_age<=window_age+1'b1;end
 if(!consumed && held>=LONG_PRESS_MS-1 && pressed!=0 && !accepting_mode)begin
 consumed<=1;O_cancel<=1;
 if(!cal_ui)begin
 if(chord!=0)begin
 if(O_ui_mode==0)case(chord)
 5:if(!O_tracking && camera_ready && !O_gain_busy && O_gain_req==ack_sync[1])begin
 O_cal_enter<=~O_cal_enter;cal_ui<=1;cal_seen<=0;O_session<=O_session+1'b1;end else conflict<=1;
 6:O_rotate<=~O_rotate;
 default:begin end
 endcase else conflict<=1;
 end else if(gesture==1)O_show<=~O_show;
 else if(gesture==2)begin
 if(!O_tracking && (!camera_ready || O_gain_busy))conflict<=1;
 else begin O_tracking<=~O_tracking;O_session<=O_session+1'b1;end end
 else if(gesture==4 && O_ui_mode==3)O_click4<=1;
 end end end
 if(I_pause)begin O_tracking<=0;O_session<=O_session+1'b1;O_cancel<=1;
 if(cal_ui)begin O_cal_cancel<=~O_cal_cancel;cal_ui<=0;cal_seen<=0;end end
 end end
endmodule
`default_nettype wire
