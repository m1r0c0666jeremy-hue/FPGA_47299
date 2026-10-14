// Existing single-key actions plus a deliberate standby calibration chord.
// Calibration commands are toggle tokens, transferred as one coherent bundle.
`default_nettype none
module stable_controls #(parameter CYCLES_PER_MS=75000,DEBOUNCE_MS=20,LONG_PRESS_MS=1000)(
 input wire I_clk,I_rst_n,input wire [2:0] I_keys_n,input wire [1:0] I_ui_switch,
 input wire I_gain_ack,input wire [7:0] I_cal_status,
 output reg O_gain_req,O_gain_up,output reg [1:0] O_zoom,
 output reg O_tracking,O_show,output reg [7:0] O_session,
 output wire O_conflict,output reg O_pair,
 output reg O_cal_enter,O_cal_sample,O_cal_cancel);
 (* async_reg="true" *) reg [2:0] k1,k2;(* async_reg="true" *) reg [1:0] s1,s2;
 (* async_reg="true", syn_preserve=1 *) reg ack1,ack2;reg [2:0] kc,keys,previous;
 reg [1:0] sc,sw;reg [7:0] kd,sd;reg [16:0] ms;
 reg [15:0] held;reg consumed,did_action,cal_ui,cal_seen;
 wire tick=ms==CYCLES_PER_MS-1;wire [2:0] pressed=~keys;
 assign O_conflict=pressed!=0 && pressed!=1 && pressed!=2 && pressed!=4 && pressed!=5;
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin k1<=7;k2<=7;s1<=0;s2<=0;ack1<=0;ack2<=0;end
 else begin k1<=I_keys_n;k2<=k1;s1<=I_ui_switch;s2<=s1;ack1<=I_gain_ack;ack2<=ack1;end end
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin kc<=7;keys<=7;previous<=0;sc<=0;sw<=0;kd<=0;sd<=0;ms<=0;held<=0;
 consumed<=0;did_action<=0;cal_ui<=0;cal_seen<=0;O_gain_req<=0;O_gain_up<=0;O_zoom<=0;
 O_tracking<=0;O_show<=1;O_session<=0;O_pair<=0;O_cal_enter<=0;O_cal_sample<=0;O_cal_cancel<=0;end
 else begin
 if(tick)ms<=0;else ms<=ms+1'b1;
 if(I_cal_status[7:5]!=0)cal_seen<=1;
 if(cal_ui && cal_seen && I_cal_status[7:5]==0)begin cal_ui<=0;cal_seen<=0;end
 if(tick)begin
 if(k2!=kc)begin kc<=k2;kd<=0;end else if(kd<DEBOUNCE_MS)begin kd<=kd+1'b1;if(kd==DEBOUNCE_MS-1)keys<=kc;end
 if(s2!=sc)begin sc<=s2;sd<=0;end else if(sd<DEBOUNCE_MS)begin sd<=sd+1'b1;if(sd==DEBOUNCE_MS-1)sw<=sc;end
 if(O_pair!=sw[1])begin O_pair<=sw[1];O_session<=O_session+1'b1;
 if(cal_ui)begin O_cal_cancel<=~O_cal_cancel;cal_ui<=0;cal_seen<=0;end end
 if(pressed!=previous)begin
 if(pressed==0)begin
 if(!consumed && previous==2 && held<LONG_PRESS_MS)begin
 if(cal_ui)O_cal_sample<=~O_cal_sample;else begin O_tracking<=~O_tracking;O_session<=O_session+1'b1;end end
 if(!consumed && !did_action && previous==1)begin
 if(cal_ui)begin O_cal_cancel<=~O_cal_cancel;cal_ui<=0;cal_seen<=0;end
 else if(O_gain_req==ack2)begin O_gain_up<=sw[0];O_gain_req<=~O_gain_req;O_tracking<=0;O_session<=O_session+1'b1;end end
 if(!consumed && !did_action && previous==4 && !cal_ui)begin
 if(sw[0])begin if(O_zoom<2)O_zoom<=O_zoom+1'b1;end else if(O_zoom>0)O_zoom<=O_zoom-1'b1;end
 consumed<=0;did_action<=0;
 end
 held<=0;previous<=pressed;
 if(pressed==5 || O_conflict)begin consumed<=0;did_action<=0;end
 end else if(pressed!=0 && held<65535)held<=held+1'b1;
 if(O_conflict)consumed<=1;
 if(pressed==5 && !consumed && held>=LONG_PRESS_MS-1)begin
 consumed<=1;if(!O_tracking && !cal_ui && O_gain_req==ack2)begin O_cal_enter<=~O_cal_enter;cal_ui<=1;cal_seen<=0;O_session<=O_session+1'b1;end end
 if(pressed==2 && !consumed && held>=LONG_PRESS_MS-1)begin consumed<=1;if(!cal_ui)O_show<=~O_show;end
 if(pressed==1 && !consumed && (held==50 || (held>50 && (held-50)%150==0)))begin
 did_action<=1;
 if(cal_ui)begin O_cal_cancel<=~O_cal_cancel;consumed<=1;cal_ui<=0;cal_seen<=0;end
 else if(O_gain_req==ack2)begin O_gain_up<=sw[0];O_gain_req<=~O_gain_req;O_tracking<=0;O_session<=O_session+1'b1;end end
 if(pressed==4 && !consumed && !cal_ui && (held==50 || (held>50 && (held-50)%600==0)))begin
 did_action<=1;if(sw[0])begin if(O_zoom<2)O_zoom<=O_zoom+1'b1;end else if(O_zoom>0)O_zoom<=O_zoom-1'b1;end
 end end end
endmodule
`default_nettype wire
