`default_nettype none
module stage1_ui_formatter(input wire clk,rst_n,latch,input wire [5:0] col,
 input wire [1:0] mode,input wire [3:0] run_state,input wire [2:0] area_count,draft_area,expected_area,actual_area,
 input wire [3:0] draft_count,occupied,input wire [10:0] distance,input wire [19:0] dwell_ms,
 input wire [1:0] trend,input wire [3:0] edit_error,start_error,input wire busy,tip_live,muted,gain_busy,gain_failed,
 input wire [2:0] gain_slot,input wire show,output reg [7:0] glyph,output wire override_enable,force_footer,
 output wire [3:0] snapshot_state,output wire [1:0] snapshot_mode,
 input wire row,input wire [6:0] gain_actual,gain_target,input wire [2:0] zoom,
 input wire [1:0] process_mode,input wire pair,rotate,input wire [4:0] status,input wire [3:0] tip_reason);
 reg [1:0] fmode,fprocess;reg [3:0] fstate,fn,fdraft,foccupied,fedit,fstart,freason;
 reg [2:0] fexpected,factual,fslot,fzoom;reg [4:0] fstatus;
 reg status_pending;reg fbusy,ftip,fmuted,fgain,fgain_failed,fshow,fpair,frotate;
 reg [6:0] fgain_actual;reg [11:0] gain_bcd,target_bcd;
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
 integer i;
 always @*begin adjusted=bcd;for(i=0;i<4;i=i+1)if(bcd[i*4+:4]>=5)adjusted[i*4+:4]=bcd[i*4+:4]+3;
 case(fgain_actual)16:actual_slot=0;32:actual_slot=1;48:actual_slot=2;64:actual_slot=3;80:actual_slot=4;90:actual_slot=5;105:actual_slot=6;default:actual_slot=7;endcase end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin fmode<=0;fstate<=0;fn<=0;fdraft<=0;foccupied<=0;fedit<=0;fstart<=0;freason<=0;
 status_pending<=0;fexpected<=0;factual<=0;fslot<=5;fzoom<=0;fprocess<=0;fstatus<=0;fpair<=0;frotate<=1;
 fbusy<=0;ftip<=0;fmuted<=0;fgain<=0;fgain_failed<=0;fshow<=1;fgain_actual<=90;
 gain_bcd<=12'h090;target_bcd<=12'h090;divider<=0;binary<=0;remainder<=0;quotient<=0;
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
 fgain_actual<=gain_actual;gain_bcd<=decimal7(gain_actual);target_bcd<=decimal7(gain_target);
 divider<=dwell_ms;remainder<=0;quotient<=0;bit_index<=0;conversion<=1;end end end
 always @*begin
 message_id=fbusy?8:fedit!=0?fedit:!ftip?5:0;
 if(fmode==2)begin
 if(fbusy)message_id=8;else if(fstart!=0)case(fstart)1:message_id=7;2:message_id=10;3:message_id=5;default:message_id=8;endcase
 else case(fstate)0:message_id=12;1,4:message_id=11;3:message_id=14;5:message_id=13;7:message_id=15;default:message_id=0;endcase end
 rom_addr=0;
 if(row && col>=42)rom_addr=10'd704+{1'b0,freason,5'd0}+col-42;
 else if(fmode==1 && col>=24 && col<40)rom_addr={2'd0,message_id,4'd0}+col-24;
 else if(fmode==2)begin if(col<8)rom_addr=10'd256+{3'd0,fstate,3'd0}+col;
 else if(col>=47 && col<63)rom_addr={2'd0,message_id,4'd0}+col-47;end
 else if(fmode==0 && col>=47 && col<63)rom_addr=10'd384+{1'b0,fstatus,4'd0}+col-47;
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
6'd41:edit_char=8'd11;
6'd42:edit_char=8'd31;
6'd43:edit_char=8'd30;
6'd44:edit_char=8'd25;
6'd46:edit_char=8'd29;
6'd47:edit_char=8'd11;
6'd48:edit_char=8'd32;
6'd49:edit_char=8'd15;
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
6'd31:test_char=8'd1+dwell_bcd[12+:4];
6'd32:test_char=8'd1+dwell_bcd[8+:4];
6'd33:test_char=8'd1+dwell_bcd[4+:4];
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
6'd0:normal_char=fprocess==0?8'd28:fprocess==1?8'd18:fprocess==2?8'd17:8'd23;
6'd1:normal_char=fprocess==0?8'd11:fprocess==1?8'd19:fprocess==2?8'd28:8'd11;
6'd2:normal_char=fprocess==0?8'd33:fprocess==1?8'd22:fprocess==2?8'd11:8'd29;
6'd3:normal_char=fprocess==0?8'd0:fprocess==1?8'd19:fprocess==2?8'd35:8'd21;
6'd4:normal_char=fprocess==0?8'd0:fprocess==1?8'd30:fprocess==2?8'd0:8'd0;
6'd5:normal_char=fprocess==0?8'd0:fprocess==1?8'd15:fprocess==2?8'd0:8'd0;
6'd6:normal_char=fprocess==0?8'd0:fprocess==1?8'd0:fprocess==2?8'd0:8'd0;
6'd7:normal_char=fprocess==0?8'd0:fprocess==1?8'd0:fprocess==2?8'd0:8'd0;
6'd9:normal_char=8'd36;
6'd10:normal_char=8'd25;
6'd11:normal_char=8'd25;
6'd12:normal_char=8'd23;
6'd14:normal_char=fzoom==0?8'd2:fzoom==1?8'd2:fzoom==2?8'd3:fzoom==3?8'd4:8'd5;
6'd15:normal_char=fzoom==0?8'd34:fzoom==1?8'd39:fzoom==2?8'd34:fzoom==3?8'd34:8'd34;
6'd16:normal_char=fzoom==0?8'd0:fzoom==1?8'd6:fzoom==2?8'd0:fzoom==3?8'd0:8'd0;
6'd17:normal_char=fzoom==0?8'd0:fzoom==1?8'd34:fzoom==2?8'd0:fzoom==3?8'd0:8'd0;
6'd19:normal_char=fpair?8'd35:8'd28;
6'd20:normal_char=fpair?8'd42:8'd42;
6'd21:normal_char=fpair?8'd26:8'd12;
6'd23:normal_char=frotate?8'd2:8'd1;
6'd24:normal_char=frotate?8'd9:8'd1;
6'd25:normal_char=frotate?8'd1:8'd1;
6'd27:normal_char=8'd12;
6'd28:normal_char=8'd28;
6'd29:normal_char=8'd30;
6'd30:normal_char=8'd1+gain_bcd[8+:4];
6'd31:normal_char=8'd1+gain_bcd[4+:4];
6'd32:normal_char=8'd1+gain_bcd[0+:4];
6'd34:normal_char=actual_slot<7?8'd2+actual_slot:8'd41;
6'd35:normal_char=8'd42;
6'd36:normal_char=8'd8;
6'd38:normal_char=8'd23;
6'd39:normal_char=8'd11;
6'd40:normal_char=8'd28;
6'd41:normal_char=8'd21;
6'd43:normal_char=fshow?8'd25:8'd25;
6'd44:normal_char=fshow?8'd24:8'd16;
6'd45:normal_char=fshow?8'd0:8'd16;
6'd47:normal_char=rom_glyph;
6'd48:normal_char=rom_glyph;
6'd49:normal_char=rom_glyph;
6'd50:normal_char=rom_glyph;
6'd51:normal_char=rom_glyph;
6'd52:normal_char=rom_glyph;
6'd53:normal_char=rom_glyph;
6'd54:normal_char=rom_glyph;
6'd55:normal_char=rom_glyph;
6'd56:normal_char=rom_glyph;
6'd57:normal_char=rom_glyph;
6'd58:normal_char=rom_glyph;
6'd59:normal_char=rom_glyph;
6'd60:normal_char=rom_glyph;
6'd61:normal_char=rom_glyph;
6'd62:normal_char=rom_glyph;
endcase end endfunction
function [7:0] busy_char;input [5:0] column;begin busy_char=0;case(column)
6'd0:busy_char=8'd12;
6'd1:busy_char=8'd28;
6'd2:busy_char=8'd30;
6'd3:busy_char=8'd1+gain_bcd[8+:4];
6'd4:busy_char=8'd1+gain_bcd[4+:4];
6'd5:busy_char=8'd1+gain_bcd[0+:4];
6'd7:busy_char=8'd30;
6'd8:busy_char=8'd25;
6'd9:busy_char=8'd1+target_bcd[8+:4];
6'd10:busy_char=8'd1+target_bcd[4+:4];
6'd11:busy_char=8'd1+target_bcd[0+:4];
6'd13:busy_char=8'd12;
6'd14:busy_char=8'd31;
6'd15:busy_char=8'd29;
6'd16:busy_char=8'd35;
6'd19:busy_char=fpair?8'd35:8'd28;
6'd20:busy_char=fpair?8'd42:8'd42;
6'd21:busy_char=fpair?8'd26:8'd12;
6'd23:busy_char=frotate?8'd2:8'd1;
6'd24:busy_char=frotate?8'd9:8'd1;
6'd25:busy_char=frotate?8'd1:8'd1;
6'd27:busy_char=8'd12;
6'd28:busy_char=8'd28;
6'd29:busy_char=8'd30;
6'd30:busy_char=8'd1+gain_bcd[8+:4];
6'd31:busy_char=8'd1+gain_bcd[4+:4];
6'd32:busy_char=8'd1+gain_bcd[0+:4];
6'd34:busy_char=actual_slot<7?8'd2+actual_slot:8'd41;
6'd35:busy_char=8'd42;
6'd36:busy_char=8'd8;
6'd38:busy_char=8'd23;
6'd39:busy_char=8'd11;
6'd40:busy_char=8'd28;
6'd41:busy_char=8'd21;
6'd43:busy_char=fshow?8'd25:8'd25;
6'd44:busy_char=fshow?8'd24:8'd16;
6'd45:busy_char=fshow?8'd0:8'd16;
6'd47:busy_char=rom_glyph;
6'd48:busy_char=rom_glyph;
6'd49:busy_char=rom_glyph;
6'd50:busy_char=rom_glyph;
6'd51:busy_char=rom_glyph;
6'd52:busy_char=rom_glyph;
6'd53:busy_char=rom_glyph;
6'd54:busy_char=rom_glyph;
6'd55:busy_char=rom_glyph;
6'd56:busy_char=rom_glyph;
6'd57:busy_char=rom_glyph;
6'd58:busy_char=rom_glyph;
6'd59:busy_char=rom_glyph;
6'd60:busy_char=rom_glyph;
6'd61:busy_char=rom_glyph;
6'd62:busy_char=rom_glyph;
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
6'd21:failed_char=fpair?8'd26:8'd12;
6'd23:failed_char=frotate?8'd2:8'd1;
6'd24:failed_char=frotate?8'd9:8'd1;
6'd25:failed_char=frotate?8'd1:8'd1;
6'd27:failed_char=8'd12;
6'd28:failed_char=8'd28;
6'd29:failed_char=8'd30;
6'd30:failed_char=8'd1+gain_bcd[8+:4];
6'd31:failed_char=8'd1+gain_bcd[4+:4];
6'd32:failed_char=8'd1+gain_bcd[0+:4];
6'd34:failed_char=actual_slot<7?8'd2+actual_slot:8'd41;
6'd35:failed_char=8'd42;
6'd36:failed_char=8'd8;
6'd38:failed_char=8'd23;
6'd39:failed_char=8'd11;
6'd40:failed_char=8'd28;
6'd41:failed_char=8'd21;
6'd43:failed_char=fshow?8'd25:8'd25;
6'd44:failed_char=fshow?8'd24:8'd16;
6'd45:failed_char=fshow?8'd0:8'd16;
6'd47:failed_char=rom_glyph;
6'd48:failed_char=rom_glyph;
6'd49:failed_char=rom_glyph;
6'd50:failed_char=rom_glyph;
6'd51:failed_char=rom_glyph;
6'd52:failed_char=rom_glyph;
6'd53:failed_char=rom_glyph;
6'd54:failed_char=rom_glyph;
6'd55:failed_char=rom_glyph;
6'd56:failed_char=rom_glyph;
6'd57:failed_char=rom_glyph;
6'd58:failed_char=rom_glyph;
6'd59:failed_char=rom_glyph;
6'd60:failed_char=rom_glyph;
6'd61:failed_char=rom_glyph;
6'd62:failed_char=rom_glyph;
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
always @(row or col or fmode or fgain_failed or fgain or fshow or fn or fdraft or fstate or fexpected or factual or foccupied or fmuted or fprocess or fzoom or fpair or frotate or gain_bcd or target_bcd or actual_slot or dwell_bcd or rom_glyph)begin
 if(row)glyph=col>=42?rom_glyph:8'd0;
 else if(fmode==2)glyph=test_char(col);else if(fmode==1)glyph=edit_char(col);
 else if(fgain_failed)glyph=failed_char(col);else if(fgain)glyph=busy_char(col);
 else if(fmode==3)glyph=reserved_char(col);else glyph=normal_char(col);
 end
endmodule
`default_nettype wire
