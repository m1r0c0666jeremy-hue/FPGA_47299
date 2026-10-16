// Debounced single actions and three mutually exclusive deliberate chords.
// A chord must begin within 100 ms of the first key; every consumed gesture
// remains suppressed until ALL keys have been released.
`default_nettype none
module stable_controls #(parameter CYCLES_PER_MS=75000,DEBOUNCE_MS=20,LONG_PRESS_MS=1000,CHORD_WINDOW_MS=100)(
 input wire I_clk,I_rst_n,input wire [2:0] I_keys_n,input wire [1:0] I_ui_switch,
 input wire I_gain_ack,input wire [7:0] I_cal_status,
 output reg O_gain_req,O_gain_up,output reg [2:0] O_zoom,
 output reg O_tracking,O_show,output reg [7:0] O_session,
 output wire O_conflict,output reg O_pair,
 output reg O_cal_enter,O_cal_sample,O_cal_cancel,output reg O_rotate,output reg [1:0] O_diag,input wire I_pause);
 (* async_reg="true" *) reg [2:0] k1,k2;(* async_reg="true" *) reg [1:0] s1,s2;
 (* async_reg="true", syn_preserve=1 *) reg ack1,ack2;reg [2:0] kc,keys,previous,gesture,chord;
 reg [1:0] sc,sw;reg [7:0] kd,sd;reg [16:0] ms;
 reg [15:0] held;reg [7:0] window_age;reg consumed,did_action,cal_ui,cal_seen,conflict;
 wire tick=ms==CYCLES_PER_MS-1;wire [2:0] pressed=~keys;
 wire valid_chord=pressed==3 || pressed==5 || pressed==6;
 wire single=gesture==1 || gesture==2 || gesture==4;
 assign O_conflict=conflict || pressed==7;
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin k1<=7;k2<=7;s1<=0;s2<=0;ack1<=0;ack2<=0;end
 else begin k1<=I_keys_n;k2<=k1;s1<=I_ui_switch;s2<=s1;ack1<=I_gain_ack;ack2<=ack1;end end
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin kc<=7;keys<=7;previous<=0;gesture<=0;chord<=0;sc<=0;sw<=0;kd<=0;sd<=0;ms<=0;held<=0;window_age<=0;
 consumed<=0;did_action<=0;cal_ui<=0;cal_seen<=0;conflict<=0;O_gain_req<=0;O_gain_up<=0;O_zoom<=0;
 O_tracking<=0;O_show<=1;O_session<=0;O_pair<=0;O_cal_enter<=0;O_cal_sample<=0;O_cal_cancel<=0;O_rotate<=1;O_diag<=0;end
 else begin
 if(tick)ms<=0;else ms<=ms+1'b1;
 if(I_cal_status[7:5]!=0)cal_seen<=1;
 if(cal_ui && cal_seen && I_cal_status[7:5]==0)begin cal_ui<=0;cal_seen<=0;end
 if(tick)begin
 if(k2!=kc)begin kc<=k2;kd<=0;end else if(kd<DEBOUNCE_MS)begin kd<=kd+1'b1;if(kd==DEBOUNCE_MS-1)keys<=kc;end
 if(s2!=sc)begin sc<=s2;sd<=0;end else if(sd<DEBOUNCE_MS)begin sd<=sd+1'b1;if(sd==DEBOUNCE_MS-1)sw<=sc;end
 if(O_pair!=sw[1])begin O_pair<=sw[1];O_session<=O_session+1'b1;
 if(cal_ui)begin O_cal_cancel<=~O_cal_cancel;cal_ui<=0;cal_seen<=0;end end
 if(pressed!=previous)begin previous<=pressed;
 if(pressed==0)begin
 if(chord==0 && !consumed)begin
 if(gesture==2 && held<LONG_PRESS_MS)begin
 if(cal_ui)O_cal_sample<=~O_cal_sample;else begin O_tracking<=~O_tracking;O_session<=O_session+1'b1;end end
 if(!did_action && gesture==1)begin
 if(cal_ui)begin O_cal_cancel<=~O_cal_cancel;cal_ui<=0;cal_seen<=0;end
 else if(O_gain_req==ack2)begin O_gain_up<=sw[0];O_gain_req<=~O_gain_req;O_tracking<=0;O_session<=O_session+1'b1;end end
 if(!did_action && gesture==4 && !cal_ui)begin
 if(sw[0])begin if(O_zoom<4)O_zoom<=O_zoom+1'b1;end else if(O_zoom>0)O_zoom<=O_zoom-1'b1;end
 end
 gesture<=0;chord<=0;held<=0;window_age<=0;consumed<=0;did_action<=0;conflict<=0;
 end else if(gesture==0 && chord==0 && !consumed)begin
 gesture<=pressed;held<=0;window_age<=0;did_action<=0;
 if(valid_chord)chord<=pressed;else if(pressed==7)begin consumed<=1;conflict<=1;end
 end else if(chord!=0 || consumed)begin consumed<=1;end
 else if(valid_chord && single && window_age<CHORD_WINDOW_MS && !did_action)begin
 chord<=pressed;held<=0;consumed<=0;
 end else begin consumed<=1;conflict<=1;end
 end else if(pressed!=0)begin
 if(held<65535)held<=held+1'b1;if(window_age<CHORD_WINDOW_MS)window_age<=window_age+1'b1;
 end
 if(chord!=0 && pressed==chord && !consumed && held>=LONG_PRESS_MS-1)begin
 consumed<=1;
 case(chord)
 5:if(!O_tracking && !cal_ui && O_gain_req==ack2)begin O_cal_enter<=~O_cal_enter;cal_ui<=1;cal_seen<=0;O_session<=O_session+1'b1;end else conflict<=1;
 6:O_rotate<=~O_rotate;
 3:if(!cal_ui)O_diag<=O_diag==2?0:O_diag+1'b1;
 endcase end
 if(chord==0 && pressed==2 && !consumed && held>=LONG_PRESS_MS-1)begin consumed<=1;if(!cal_ui)O_show<=~O_show;end
 if(chord==0 && pressed==1 && !consumed && (held==CHORD_WINDOW_MS || (held>CHORD_WINDOW_MS && (held-CHORD_WINDOW_MS)%150==0)))begin
 did_action<=1;
 if(cal_ui)begin O_cal_cancel<=~O_cal_cancel;consumed<=1;cal_ui<=0;cal_seen<=0;end
 else if(O_gain_req==ack2)begin O_gain_up<=sw[0];O_gain_req<=~O_gain_req;O_tracking<=0;O_session<=O_session+1'b1;end end
 if(chord==0 && pressed==4 && !consumed && !cal_ui && (held==CHORD_WINDOW_MS || (held>CHORD_WINDOW_MS && (held-CHORD_WINDOW_MS)%600==0)))begin
 did_action<=1;if(sw[0])begin if(O_zoom<4)O_zoom<=O_zoom+1'b1;end else if(O_zoom>0)O_zoom<=O_zoom-1'b1;end
 end
 if(I_pause)begin O_tracking<=0;O_session<=O_session+1'b1;
 if(cal_ui)O_cal_cancel<=~O_cal_cancel;cal_ui<=0;cal_seen<=0;end
 end end
endmodule
`default_nettype wire
