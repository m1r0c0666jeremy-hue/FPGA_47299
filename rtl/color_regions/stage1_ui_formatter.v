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
6'd0:reserved_char=8'd30;
6'd1:reserved_char=8'd15;
6'd2:reserved_char=8'd11;
6'd3:reserved_char=8'd13;
6'd4:reserved_char=8'd18;
6'd6:reserved_char=8'd15;
6'd7:reserved_char=8'd23;
6'd8:reserved_char=8'd26;
6'd9:reserved_char=8'd30;
6'd10:reserved_char=8'd35;
endcase end endfunction
always @(row or col or fmode or fgain_failed or fgain or fshow or fn or fdraft or fstate or fexpected or factual or foccupied or fmuted or fprocess or fzoom or fpair or frotate or gain_bcd or target_bcd or actual_slot or dwell_bcd or rom_glyph)begin
 if(row)glyph=col>=42?rom_glyph:8'd0;
 else if(fmode==2)glyph=test_char(col);else if(fmode==1)glyph=edit_char(col);
 else if(fgain_failed)glyph=failed_char(col);else if(fgain)glyph=busy_char(col);
 else if(fmode==3)glyph=reserved_char(col);else glyph=normal_char(col);
 end
endmodule
`default_nettype wire

`default_nettype none
module stage1_teach_text(input wire clk,rst_n,latch,input wire [5:0] col,input wire row,input wire [1:0] mode,
 input wire [63:0] teaching,input wire [3:0] run_state,occupied,input wire [2:0] expected,actual,
 input wire [19:0] dwell,output reg [7:0] glyph,output wire override_enable);
 reg [63:0] f;reg [1:0] fm;reg [3:0] fs,fi;reg [2:0] fe,fa;
 reg [19:0] dwell_value,number,binary;reg [6:0] rem;reg [13:0] quotient;
 reg [15:0] bcd,adjusted,time_bcd,duration_bcd,count_bcd,dwell_bcd;
 reg [2:0] field;reg [1:0] conversion;reg [4:0] index;integer i;
 wire [7:0] shifted={rem,number[19]};wire take=shifted>=100;
 localparam [63:0] INCOMPLETE="INCOMP  ";localparam [255:0] DRAFT_OFF="FINISH DRAFT. SEQ OFF           ",NO_AREAS="NO SAVED AREAS. SEQ OFF         ";
 reg [63:0] state_word,motion_word,run_word;reg [255:0] reason_word;reg [7:0] ascii;
 function [7:0] encode;input [7:0] c;begin
 if(c>=48 && c<=57)encode=c-47;else if(c>=65 && c<=90)encode=c-54;
 else case(c)109:encode=37;115:encode=38;46:encode=39;58:encode=40;45:encode=41;47:encode=42;40:encode=43;41:encode=44;default:encode=0;endcase end endfunction
 assign override_enable=fm==3 || (fm==2 && !row && f[51] && col>=21 && col<29);
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
0:state_word="EMPTY   ";
1:state_word="READY   ";
2:state_word="WAIT TIP";
3:state_word="RECORD  ";
4:state_word="LOADING ";
5:state_word="REPLAY  ";
6:state_word="PAUSED  ";
7:state_word="DONE    ";
8:state_word="FAIL    ";
 endcase
 motion_word="        ";if(f[51])case(f[53:52])0:motion_word="MOVE    ";1:motion_word="APPROACH";2:motion_word="AWAY    ";3:motion_word="STILL   ";endcase
 run_word="IDLE    ";case(fs)
 1:run_word="WAIT OUT";2:run_word="RUN     ";3:run_word="PAUSED  ";4:run_word="MOVE OUT";5:run_word="PASS    ";6:run_word="FAIL    ";7:run_word="STOPPED ";endcase
 reason_word=0;case(f[7:4])
0:reason_word="                                ";
1:reason_word="TRACKING OFF                    ";
2:reason_word="CAMERA NOT READY                ";
3:reason_word="VIDEO NOT READY                 ";
4:reason_word="NO VALID TIP                    ";
5:reason_word="STALE 250MS                     ";
6:reason_word="BRIGHTNESS BUSY                 ";
7:reason_word="GESTURE CANCELED                ";
8:reason_word="CONTEXT CHANGED                 ";
9:reason_word="METADATA MISMATCH               ";
10:reason_word="STOP FIRST                      ";
11:reason_word="NO ROUTE                        ";
12:reason_word="LIMIT 60S/FULL                  ";
13:reason_word="STOPPED                         ";
14:reason_word="CLEARED                         ";
15:reason_word="NEED 2 TIMED POINTS             ";
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
 if(f[3:0]==7 && fs!=5 && col<8)ascii=INCOMPLETE[(7-col)*8+:8];
 end else begin
 case(col)
0:ascii=8'd75;
1:ascii=8'd50;
3:ascii=8'd82;
4:ascii=8'd69;
5:ascii=8'd67;
6:ascii=8'd47;
7:ascii=8'd83;
8:ascii=8'd84;
9:ascii=8'd79;
10:ascii=8'd80;
12:ascii=8'd75;
13:ascii=8'd51;
15:ascii=8'd80;
16:ascii=8'd76;
17:ascii=8'd65;
18:ascii=8'd89;
19:ascii=8'd47;
20:ascii=8'd80;
21:ascii=8'd65;
22:ascii=8'd85;
23:ascii=8'd83;
24:ascii=8'd69;
26:ascii=8'd75;
27:ascii=8'd52;
29:ascii=8'd83;
30:ascii=8'd84;
31:ascii=8'd79;
32:ascii=8'd80;
34:ascii=8'd75;
35:ascii=8'd52;
37:ascii=8'd72;
38:ascii=8'd79;
39:ascii=8'd76;
40:ascii=8'd68;
42:ascii=8'd67;
43:ascii=8'd76;
44:ascii=8'd69;
45:ascii=8'd65;
46:ascii=8'd82;
 endcase
 if(f[55] && !f[54] && col<32)begin
 if(f[59:56]!=0)ascii=DRAFT_OFF[(31-col)*8+:8];
 else ascii=NO_AREAS[(31-col)*8+:8];end
 end
 glyph=encode(ascii);end
 end
endmodule
`default_nettype wire
