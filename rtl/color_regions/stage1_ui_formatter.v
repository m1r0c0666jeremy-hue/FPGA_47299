`default_nettype none
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
 if(fbusy)message_id=8;
 else if(fstart!=0)case(fstart)1:message_id=7;2:message_id=9;3:message_id=5;default:message_id=8;endcase
 else case(fstate)0:message_id=11;1,4:message_id=10;3:message_id=13;5:message_id=12;7:message_id=14;default:message_id=0;endcase
 end
 rom_addr=0;
 if(fmode==1 && col>=24 && col<40)rom_addr={1'b0,message_id,4'd0}+col-24;
 if(fmode==2 || (!fshow && force_footer))begin
 if(col<8)rom_addr=9'd256+{2'd0,fstate,3'd0}+col;
 else if(col>=38 && col<46)rom_addr=9'd320+{4'd0,ftrend,3'd0}+col-38;
 else if(col>=47 && col<63)rom_addr={1'b0,message_id,4'd0}+col-47;
 end
// edit layout
// test layout
// normal layout
// busy layout
// failed layout
// reserved layout
end
function [7:0] edit_char;input [5:0] column;begin edit_char=0;case(column)
6'd0:edit_char=8'd15;
6'd1:edit_char=8'd14;
6'd2:edit_char=8'd19;
6'd3:edit_char=8'd30;
6'd5:edit_char=fn<4?8'd11+fn:8'd41;
6'd7:edit_char=8'd26;
6'd8:edit_char=8'd30;
6'd9:edit_char=8'd29;
6'd11:edit_char=8'd1+fdraft;
6'd12:edit_char=8'd42;
6'd13:edit_char=8'd3;
6'd15:edit_char=8'd29;
6'd16:edit_char=8'd11;
6'd17:edit_char=8'd32;
6'd18:edit_char=8'd15;
6'd20:edit_char=8'd1+fn;
6'd21:edit_char=8'd42;
6'd22:edit_char=8'd5;
6'd24:edit_char=rom_glyph;
6'd25:edit_char=rom_glyph;
6'd26:edit_char=rom_glyph;
6'd27:edit_char=rom_glyph;
6'd28:edit_char=rom_glyph;
6'd29:edit_char=rom_glyph;
6'd30:edit_char=rom_glyph;
6'd31:edit_char=rom_glyph;
6'd32:edit_char=rom_glyph;
6'd33:edit_char=rom_glyph;
6'd34:edit_char=rom_glyph;
6'd35:edit_char=rom_glyph;
6'd36:edit_char=rom_glyph;
6'd37:edit_char=rom_glyph;
6'd38:edit_char=rom_glyph;
6'd39:edit_char=rom_glyph;
6'd54:edit_char=8'd30;
6'd55:edit_char=8'd1+dwell_bcd[12+:4];
6'd56:edit_char=8'd1+dwell_bcd[8+:4];
6'd57:edit_char=8'd1+dwell_bcd[4+:4];
6'd58:edit_char=8'd39;
6'd59:edit_char=8'd1+dwell_bcd[3:0];
6'd60:edit_char=8'd38;
endcase end endfunction
function [7:0] test_char;input [5:0] column;begin test_char=0;case(column)
6'd0:test_char=rom_glyph;
6'd1:test_char=rom_glyph;
6'd2:test_char=rom_glyph;
6'd3:test_char=rom_glyph;
6'd4:test_char=rom_glyph;
6'd5:test_char=rom_glyph;
6'd6:test_char=rom_glyph;
6'd7:test_char=rom_glyph;
6'd9:test_char=8'd24;
6'd10:test_char=8'd15;
6'd11:test_char=8'd34;
6'd12:test_char=8'd30;
6'd14:test_char=fexpected<fn && fstate!=5?8'd11+fexpected:8'd41;
6'd16:test_char=8'd19;
6'd17:test_char=8'd24;
6'd19:test_char=foccupied[0]?8'd11:foccupied[1]?8'd12:foccupied[2]?8'd13:foccupied[3]?8'd14:8'd41;
6'd30:test_char=8'd30;
6'd31:test_char=8'd1+dwell_bcd[15:12];
6'd32:test_char=8'd1+dwell_bcd[11:8];
6'd33:test_char=8'd1+dwell_bcd[7:4];
6'd34:test_char=8'd39;
6'd35:test_char=8'd1+dwell_bcd[3:0];
6'd36:test_char=8'd38;
6'd47:test_char=fstate==6?(8'd15):(rom_glyph);
6'd48:test_char=fstate==6?(8'd34):(rom_glyph);
6'd49:test_char=fstate==6?(8'd26):(rom_glyph);
6'd50:test_char=fstate==6?(8'd0):(rom_glyph);
6'd51:test_char=fstate==6?(8'd11+fexpected):(rom_glyph);
6'd52:test_char=fstate==6?(8'd0):(rom_glyph);
6'd53:test_char=fstate==6?(8'd17):(rom_glyph);
6'd54:test_char=fstate==6?(8'd25):(rom_glyph);
6'd55:test_char=fstate==6?(8'd30):(rom_glyph);
6'd56:test_char=fstate==6?(8'd0):(rom_glyph);
6'd57:test_char=fstate==6?(factual!=0?8'd10+factual:8'd41):(rom_glyph);
6'd58:test_char=fstate==6?(8'd0):(rom_glyph);
6'd59:test_char=fstate==6?(8'd0):(rom_glyph);
6'd60:test_char=fmuted?8'd23:(fstate==6?(8'd0):(rom_glyph));
6'd61:test_char=fmuted?8'd31:(fstate==6?(8'd0):(rom_glyph));
6'd62:test_char=fmuted?8'd30:(fstate==6?(8'd0):(rom_glyph));
6'd63:test_char=fmuted?8'd15:(fstate==6?(8'd0):(8'd0));
endcase end endfunction
function [7:0] normal_char;input [5:0] column;begin normal_char=0;case(column)
6'd54:normal_char=8'd12;
6'd55:normal_char=8'd28;
6'd56:normal_char=8'd30;
6'd57:normal_char=8'd2+fslot;
6'd58:normal_char=8'd42;
6'd59:normal_char=8'd8;
endcase end endfunction
function [7:0] busy_char;input [5:0] column;begin busy_char=0;case(column)
6'd0:busy_char=8'd12;
6'd1:busy_char=8'd28;
6'd2:busy_char=8'd19;
6'd3:busy_char=8'd17;
6'd4:busy_char=8'd18;
6'd5:busy_char=8'd30;
6'd6:busy_char=8'd24;
6'd7:busy_char=8'd15;
6'd8:busy_char=8'd29;
6'd9:busy_char=8'd29;
6'd11:busy_char=8'd12;
6'd12:busy_char=8'd31;
6'd13:busy_char=8'd29;
6'd14:busy_char=8'd35;
6'd16:busy_char=8'd2+fslot;
6'd17:busy_char=8'd42;
6'd18:busy_char=8'd8;
6'd20:busy_char=8'd30;
6'd21:busy_char=8'd25;
6'd23:busy_char=fslot==6?8'd2:8'd3+fslot;
6'd24:busy_char=8'd42;
6'd25:busy_char=8'd8;
endcase end endfunction
function [7:0] failed_char;input [5:0] column;begin failed_char=0;case(column)
6'd0:failed_char=8'd12;
6'd1:failed_char=8'd28;
6'd2:failed_char=8'd30;
6'd4:failed_char=8'd16;
6'd5:failed_char=8'd11;
6'd6:failed_char=8'd19;
6'd7:failed_char=8'd22;
6'd8:failed_char=8'd15;
6'd9:failed_char=8'd14;
6'd10:failed_char=8'd39;
6'd12:failed_char=8'd13;
6'd13:failed_char=8'd18;
6'd14:failed_char=8'd15;
6'd15:failed_char=8'd13;
6'd16:failed_char=8'd21;
6'd18:failed_char=8'd13;
6'd19:failed_char=8'd11;
6'd20:failed_char=8'd23;
endcase end endfunction
function [7:0] reserved_char;input [5:0] column;begin reserved_char=0;case(column)
6'd0:reserved_char=8'd28;
6'd1:reserved_char=8'd25;
6'd2:reserved_char=8'd31;
6'd3:reserved_char=8'd30;
6'd4:reserved_char=8'd15;
6'd6:reserved_char=8'd28;
6'd7:reserved_char=8'd15;
6'd8:reserved_char=8'd29;
6'd9:reserved_char=8'd15;
6'd10:reserved_char=8'd28;
6'd11:reserved_char=8'd32;
6'd12:reserved_char=8'd15;
6'd13:reserved_char=8'd14;
endcase end endfunction
function [7:0] minimal_char;input [5:0] column;begin minimal_char=0;case(column)
6'd0:minimal_char=fstate==6?(8'd16):fstate==3?(8'd26):fstate==7?(8'd19):(8'd33);
6'd1:minimal_char=fstate==6?(8'd11):fstate==3?(8'd11):fstate==7?(8'd24):(8'd11);
6'd2:minimal_char=fstate==6?(8'd19):fstate==3?(8'd31):fstate==7?(8'd26):(8'd19);
6'd3:minimal_char=fstate==6?(8'd22):fstate==3?(8'd29):fstate==7?(8'd31):(8'd30);
6'd4:minimal_char=fstate==6?(8'd0):fstate==3?(8'd15):fstate==7?(8'd30):(8'd0);
6'd5:minimal_char=fstate==6?(8'd15):fstate==3?(8'd14):fstate==7?(8'd0):(8'd25);
6'd6:minimal_char=fstate==6?(8'd34):fstate==3?(8'd39):fstate==7?(8'd22):(8'd31);
6'd7:minimal_char=fstate==6?(8'd26):fstate==3?(8'd0):fstate==7?(8'd25):(8'd30);
6'd8:minimal_char=fstate==6?(8'd0):fstate==3?(8'd21):fstate==7?(8'd29):(8'd39);
6'd9:minimal_char=fstate==6?(8'd11+fexpected):fstate==3?(8'd15):fstate==7?(8'd30):(8'd0);
6'd10:minimal_char=fstate==6?(8'd0):fstate==3?(8'd35):fstate==7?(8'd39):(8'd22);
6'd11:minimal_char=fstate==6?(8'd17):fstate==3?(8'd4):fstate==7?(8'd0):(8'd15);
6'd12:minimal_char=fstate==6?(8'd25):fstate==3?(8'd0):fstate==7?(8'd21):(8'd11);
6'd13:minimal_char=fstate==6?(8'd30):fstate==3?(8'd28):fstate==7?(8'd15):(8'd32);
6'd14:minimal_char=fstate==6?(8'd0):fstate==3?(8'd15):fstate==7?(8'd35):(8'd15);
6'd15:minimal_char=fstate==6?(factual!=0?8'd10+factual:8'd41):fstate==3?(8'd29):fstate==7?(8'd3):(8'd0);
6'd16:minimal_char=fstate==6?(8'd39):fstate==3?(8'd31):fstate==7?(8'd0):(8'd11);
6'd17:minimal_char=fstate==6?(8'd0):fstate==3?(8'd23):fstate==7?(8'd28):(8'd22);
6'd18:minimal_char=fstate==6?(8'd21):fstate==3?(8'd15):fstate==7?(8'd15):(8'd22);
6'd19:minimal_char=fstate==6?(8'd15):fstate==3?(8'd0):fstate==7?(8'd30):(8'd0);
6'd20:minimal_char=fstate==6?(8'd35):fstate==3?(8'd0):fstate==7?(8'd15):(8'd11);
6'd21:minimal_char=fstate==6?(8'd3):fstate==3?(8'd0):fstate==7?(8'd29):(8'd28);
6'd22:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd30):(8'd15);
6'd23:minimal_char=fstate==6?(8'd28):fstate==3?(8'd0):fstate==7?(8'd0):(8'd11);
6'd24:minimal_char=fstate==6?(8'd15):fstate==3?(8'd0):fstate==7?(8'd0):(8'd29);
6'd25:minimal_char=fstate==6?(8'd30):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd26:minimal_char=fstate==6?(8'd15):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd27:minimal_char=fstate==6?(8'd29):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd28:minimal_char=fstate==6?(8'd30):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd29:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd30:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd31:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd32:minimal_char=fstate==6?(fmuted?8'd23:8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd33:minimal_char=fstate==6?(fmuted?8'd31:8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd34:minimal_char=fstate==6?(fmuted?8'd30:8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd35:minimal_char=fstate==6?(fmuted?8'd15:8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd36:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd37:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd38:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd39:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd40:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd41:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd42:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd43:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd44:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd45:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd46:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd47:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd48:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd49:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd50:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd51:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd52:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd53:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd54:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd55:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd56:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd57:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd58:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd59:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd60:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd61:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd62:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
6'd63:minimal_char=fstate==6?(8'd0):fstate==3?(8'd0):fstate==7?(8'd0):(8'd0);
endcase end endfunction
always @(col or fmode or fshow or fstate or fgain_failed or fgain or fn or fdraft or fexpected or factual or fmuted or fslot or foccupied or ftrend or distance_bcd or dwell_bcd or rom_glyph or force_footer)begin
 if(!fshow && (fstate==1 || fstate==3 || fstate==4 || fstate==6 || fstate==7))glyph=minimal_char(col);
 else if(fmode==2)glyph=test_char(col);
 else if(fmode==1)glyph=edit_char(col);else if(fgain_failed)glyph=failed_char(col);
 else if(fgain)glyph=busy_char(col);else if(fmode==3)glyph=reserved_char(col);else glyph=normal_char(col);
 end
endmodule
`default_nettype wire
