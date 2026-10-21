// Generated upright UI. Source geometry is mapped through the committed view.
// One shared decimal converter formats the selected footer before row624.
`default_nettype none
module stage1_osd(
 input wire [1:0] I_ui_mode,input wire [671:0] I_region_vertices,input wire [15:0] I_region_counts,input wire [3:0] I_region_closed,
 input wire [2:0] I_area_count,I_expected_area,I_actual_area,input wire [3:0] I_draft_count,I_run_state,I_completed,I_occupied,
 input wire I_area_muted,input wire [1:0] I_area_trend,input wire [10:0] I_area_distance,input wire [19:0] I_area_dwell,
 input wire [3:0] I_edit_error,I_start_error,input wire I_area_busy,I_tip_live,I_gain_busy,I_gain_failed,input wire [2:0] I_gain_slot,
 input wire I_clk,I_rst_n,I_vs,I_hs,I_de,input wire [23:0] I_rgb,
 input wire [767:0] I_meta,input wire [10:0] I_x0,input wire [9:0] I_y0,
 input wire [2:0] I_zoom,input wire [1:0] I_mode,input wire [2:0] I_state,
 input wire I_tracking,I_show,I_video_ok,I_pair,I_detection_valid,I_sample_valid,
 output reg O_vs,O_hs,O_de,output reg [23:0] O_rgb,
 input wire I_rotate,input wire [1:0] I_diag,input wire [31:0] I_image_id,input wire I_geometry_commit,
 input wire I_latency_valid,input wire [31:0] I_latency_us,I_frame_age,
 input wire [127:0] I_ddr_diag,I_pixel_diag,input wire [38:0] I_recovery,input wire [17:0] I_camera
);
 localparam FONT=16,CHAR_WIDTH=8,COLS=64;
 reg [10:0] x;reg [9:0] y;reg vs_last;
 reg [767:0] fm;reg [31:0] fimage;reg [1:0] fmode;reg [2:0] fzoom;
 reg [2:0] fstate;reg fpair,frotate,ftracking,fshow,fvideo,fdetection,fsample;
 reg [4:0] status_id;wire [1:0] model_id=fm[722:721];
 reg flat_valid;reg [31:0] flatency,fage;
 always @*begin
 status_id=!ftracking?0:{1'b0,fm[36:33]};
 if(fm[568])status_id=15;
 if(fm[567:565]!=0)begin
 case(fm[567:565])1:status_id=9;2:status_id=10;3:status_id=11;4:status_id=12;default:status_id=9;endcase
 if(fm[564])status_id=13;if(fm[563:560]!=0)status_id=14;end
 if(ftracking && !fm[255])status_id=19;
 if(fm[255] && !fm[247])status_id=8;
 if(fstate==7)status_id=18;if(fstate==5)status_id=17;if(!fvideo || fstate==6)status_id=16;
 end
 // Only latency and frame age need decimal conversion in the overview.
 function [23:0] field_value;input id;begin
 field_value=id?(fage>999?24'd999:fage):(flatency>9999999?24'd9999999:flatency);
 end endfunction
 reg [31:0] numbers[0:1];reg [7:0] characters[0:127];
 reg [2:0] format_state;reg field_index;reg [4:0] bit_index;
 // The existing token wait states separate RAM selection and digit mux.
 // They add no footer/pixel latency and do not change character write cycles.
 reg [31:0] number_word_q,hex_word_q;reg [3:0] number_digit_q,hex_digit_q;
 reg [23:0] binary;reg [31:0] decimal,adjusted;reg [5:0] format_col;reg format_row,footer_ready;
 integer nibble;
 always @*begin adjusted=decimal;for(nibble=0;nibble<8;nibble=nibble+1)
 if(decimal[nibble*4+:4]>=5)adjusted[nibble*4+:4]=decimal[nibble*4+:4]+3;end
reg [4:0] template_index;reg token_valid;reg [31:0] hex_value;reg [7:0] decoded_glyph;
wire [15:0] token_data;wire [7:0] dynamic_glyph;
reg [9:0] template_start;reg [6:0] template_length;
always @*begin template_start=0;template_length=0;case(template_index)
0:begin template_start=10'd0;template_length=7'd53;end
1:begin template_start=10'd53;template_length=7'd41;end
2:begin template_start=10'd94;template_length=7'd42;end
3:begin template_start=10'd136;template_length=7'd46;end
4:begin template_start=10'd182;template_length=7'd60;end
5:begin template_start=10'd242;template_length=7'd45;end
6:begin template_start=10'd287;template_length=7'd47;end
7:begin template_start=10'd334;template_length=7'd53;end
8:begin template_start=10'd387;template_length=7'd23;end
9:begin template_start=10'd410;template_length=7'd36;end
10:begin template_start=10'd446;template_length=7'd39;end
11:begin template_start=10'd485;template_length=7'd40;end
12:begin template_start=10'd525;template_length=7'd40;end
13:begin template_start=10'd565;template_length=7'd37;end
14:begin template_start=10'd602;template_length=7'd39;end
15:begin template_start=10'd641;template_length=7'd40;end
16:begin template_start=10'd681;template_length=7'd40;end
17:begin template_start=10'd721;template_length=7'd41;end
18:begin template_start=10'd762;template_length=7'd42;end
19:begin template_start=10'd804;template_length=7'd42;end
20:begin template_start=10'd846;template_length=7'd40;end
endcase end
wire [9:0] program_addr=template_start+{4'd0,format_col};
reg program_in_range,program_in_range_q;
always @(posedge I_clk)begin program_in_range<=({1'b0,format_col}<template_length);program_in_range_q<=program_in_range;end
wire [8:0] dynamic_addr=token_data[12:8]==0?({7'd0,fmode}<<3)+{5'd0,token_data[2:0]}:
token_data[12:8]==1?9'd64+({4'd0,status_id}<<4)+{5'd0,token_data[3:0]}:
9'd384+({7'd0,model_id}<<3)+{5'd0,token_data[2:0]};
refined_footer_program_rom program_rom(I_clk,program_addr,token_data);
refined_english_text_rom text_rom(I_clk,dynamic_addr,dynamic_glyph);
always @*begin
template_index={4'd0,format_row};
if(fm[567:565]!=0)begin
if(!format_row)template_index=2;
else if(fm[563:560]!=0)template_index=8+{1'b0,fm[563:560]};
else if(fm[564])template_index=7;
else template_index=2+{2'd0,fm[567:565]};end
token_valid=1;case(token_data[7:4])
0:token_valid=1'b1;
1:token_valid=flat_valid && flatency<10000000;
2:token_valid=flat_valid && fage<1000;
3:token_valid=fm[255] && fm[415:413]==4;
default:token_valid=0;endcase
hex_value=0;case(token_data[12:8])
0:hex_value=fimage;
1:hex_value=fm[559:544];
2:hex_value=fm[563:560];
endcase
decoded_glyph=0;case(token_data[15:13])
0:decoded_glyph=token_data[7:0];
1:decoded_glyph=token_valid?8'd1+number_digit_q:8'd41;
2:decoded_glyph=token_valid?8'd1+hex_digit_q:8'd41;
3:case(token_data[12:8])
0:decoded_glyph=fzoom==0?8'd2:fzoom==1?8'd2:fzoom==2?8'd3:fzoom==3?8'd4:8'd5;
1:decoded_glyph=fzoom==0?8'd34:fzoom==1?8'd39:fzoom==2?8'd34:fzoom==3?8'd34:8'd34;
2:decoded_glyph=fzoom==0?8'd0:fzoom==1?8'd6:fzoom==2?8'd0:fzoom==3?8'd0:8'd0;
3:decoded_glyph=fzoom==0?8'd0:fzoom==1?8'd34:fzoom==2?8'd0:fzoom==3?8'd0:8'd0;
4:decoded_glyph=fpair==0?8'd28:8'd35;
5:decoded_glyph=fpair==0?8'd42:8'd42;
6:decoded_glyph=fpair==0?8'd12:8'd26;
7:decoded_glyph=frotate==0?8'd1:8'd2;
8:decoded_glyph=frotate==0?8'd1:8'd9;
9:decoded_glyph=frotate==0?8'd1:8'd1;
endcase
5:decoded_glyph=dynamic_glyph;
endcase
if(!program_in_range_q)decoded_glyph=0;
end
wire [3:0] region_pixel,stage_snapshot_state;wire [1:0] stage_snapshot_mode;
 wire [23:0] region_color,region_label_color;wire region_label_on,region_ready,region_underrun;
 wire [7:0] region_label_glyph,stage_glyph;wire [2:0] region_label_gx;wire [3:0] region_label_gy;
 wire stage_override,stage_force_footer;
 stage1_render region_render(I_clk,I_rst_n,I_geometry_commit,I_region_vertices,I_region_counts,I_region_closed,I_ui_mode,
 I_x0,I_y0,I_zoom,I_rotate,I_run_state,I_completed,I_expected_area,I_actual_area,x,y,I_de,
 region_pixel,region_color,region_label_on,region_label_glyph,region_label_gx,region_label_gy,region_label_color,region_ready,region_underrun);
 stage1_ui_formatter region_text(I_clk,I_rst_n,I_de && y==625 && x==0,format_col,I_ui_mode,I_run_state,I_area_count,3'd0,I_expected_area,I_actual_area,
 I_draft_count,I_occupied,I_area_distance,I_area_dwell,I_area_trend,I_edit_error,I_start_error,I_area_busy,I_tip_live,I_area_muted,I_gain_busy,I_gain_failed,
 I_gain_slot,I_show,stage_glyph,stage_override,stage_force_footer,stage_snapshot_state,stage_snapshot_mode);
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin
 flat_valid<=0;flatency<=0;fage<=0;
 fm<=0;fimage<=0;fmode<=0;fzoom<=0;fstate<=6;fpair<=0;frotate<=1;ftracking<=0;fshow<=1;fvideo<=0;fdetection<=0;fsample<=0;
 format_state<=0;field_index<=0;bit_index<=0;binary<=0;decimal<=0;format_col<=0;format_row<=0;footer_ready<=0;number_word_q<=0;hex_word_q<=0;number_digit_q<=0;hex_digit_q<=0;
 end else begin
 case(format_state)
 1:begin binary<=field_value(field_index);decimal<=0;bit_index<=0;format_state<=2;end
 2:begin binary<=binary<<1;decimal<={adjusted[30:0],binary[23]};
 if(bit_index==23)begin numbers[field_index]<={adjusted[30:0],binary[23]};
 if(field_index)begin format_col<=0;format_row<=0;format_state<=3;end
 else begin field_index<=field_index+1'b1;format_state<=1;end end
 else bit_index<=bit_index+1'b1;end
 3:format_state<=4;
 4:format_state<=5;
 5:begin number_word_q<=numbers[token_data[8]];hex_word_q<=hex_value;format_state<=6;end
 6:begin number_digit_q<=number_word_q>>(token_data[3:0]*4);hex_digit_q<=hex_word_q>>(token_data[3:0]*4);format_state<=7;end
 7:begin characters[(format_row?COLS:0)+format_col]<=!format_row && fm[567:565]==0 && stage_override?stage_glyph:decoded_glyph;
 format_state<=3;
 if(format_col==COLS-1)begin format_col<=0;if(format_row)begin footer_ready<=1;format_state<=0;end else format_row<=1;end
 else format_col<=format_col+1'b1;end
 endcase
 if(I_de && y==625 && x==0)begin
 flat_valid<=I_latency_valid;flatency<=I_latency_us;fage<=I_frame_age;
 fm<=I_meta;fimage<=I_image_id;fmode<=I_mode;fzoom<=I_zoom;fstate<=I_state;
 fpair<=I_pair;frotate<=I_rotate;ftracking<=I_tracking;fshow<=I_show;fvideo<=I_video_ok;fdetection<=I_detection_valid;fsample<=I_sample_valid;
 field_index<=0;footer_ready<=0;format_state<=1;
 end end end
 wire geometry_ready;wire [251:0] geometry;
 refined_overlay_geometry coordinates(I_clk,I_rst_n,I_geometry_commit,I_meta[639:0],I_x0,I_y0,I_zoom,I_rotate,geometry_ready,geometry);
 function border;input signed [13:0] xx,yy,x0,x1,y0,y1;reg signed [13:0] l,r,t,b;begin
 l=xx-x0;r=x1-xx;t=yy-y0;b=y1-yy;
 border=!(l[13] || r[13] || t[13] || b[13]) && (l[13:1]==0 || r[13:1]==0 || t[13:1]==0 || b[13:1]==0);end endfunction
 wire [23:0] color_a=I_pair?24'hffff40:24'hff6060,color_b=I_pair?24'he080ff:24'h6090ff;
 reg [5:0] footer_col;reg [4:0] footer_px;
 reg [7:0] footer_glyph;reg [4:0] footer_gy;reg footer_text,footer_row;
 reg [7:0] label_glyph;reg [3:0] label_gx,label_gy;reg [6:0] label_width;reg label_text,back_on,logo_on;
 reg [23:0] ink,back;reg [12:0] logo_addr;reg [41:0] box;reg valid_box;
 reg signed [13:0] xx,yy,bx0,bx1,by0,by1,lx,ly,ldx,ldy;
 integer j,lc;reg [9:0] logo_y;reg [10:0] logo_x;
 localparam [87:0] WAIT_WORD={8'd33,8'd11,8'd19,8'd30,8'd0,8'd28,8'd15,8'd29,8'd31,8'd22,8'd30};
 wire footer_current=stage_snapshot_state==I_run_state && stage_snapshot_mode==I_ui_mode && footer_ready && I_tracking==ftracking && I_video_ok==fvideo && I_detection_valid==fdetection && I_state==fstate;
 always @*begin
 footer_glyph=0;footer_gy=0;footer_text=0;footer_row=0;label_glyph=0;label_gx=0;label_gy=0;label_text=0;label_width=0;
 back_on=0;back=24'h101824;ink=24'hf0f4ff;logo_on=0;logo_addr=0;logo_y=0;logo_x=0;
 box=0;valid_box=0;xx=$signed({3'd0,x});yy=$signed({4'd0,y});bx0=0;bx1=0;by0=0;by1=0;lx=0;ly=0;ldx=0;ldy=0;lc=0;
 if(y>=624)begin
 back_on=1;
 if(x>=1167 && x<1265 && y>=640 && y<704)begin
 logo_on=1;logo_y=y-640;logo_x=x-1167;logo_addr=(logo_y<<6)+(logo_y<<5)+(logo_y<<1)+logo_x;end
 if(x>=16 && x<16+COLS*CHAR_WIDTH && ((y>=632+(32-FONT)/2 && y<632+(32-FONT)/2+FONT) ||
 (y>=676+(32-FONT)/2 && y<676+(32-FONT)/2+FONT)))begin
 footer_row=y>=676;footer_gy=footer_row?y-(676+(32-FONT)/2):y-(632+(32-FONT)/2);
 footer_text=I_show || stage_force_footer;if(!I_show && footer_row)footer_text=0;
 if(footer_current)footer_glyph=characters[(footer_row?COLS:0)+footer_col];
 else if(footer_ready && !footer_row && footer_col<11)footer_glyph=WAIT_WORD>>((10-footer_col)*8);
 end
 end else if(I_video_ok && geometry_ready)begin
 if(I_show && I_detection_valid)for(j=0;j<2;j=j+1)begin
 box=j==0?I_meta[141:100]:I_meta[183:142];valid_box=j==0?I_meta[245]:I_meta[246];
 bx0=$signed(geometry[j*56+:14]);bx1=$signed(geometry[j*56+14+:14]);
 by0=$signed(geometry[j*56+28+:14]);by1=$signed(geometry[j*56+42+:14]);
 if(valid_box && bx1>=0 && bx0<1280 && by1>=0 && by0<624)begin
 if(border(xx,yy,bx0,bx1,by0,by1))begin back_on=1;back=j==0?color_a:color_b;end
 label_width=j==0?(I_pair?72:48):(I_pair?72:56);
 lx=bx0<0?0:bx0>(1280-label_width)?(1280-label_width):bx0;ly=by0>=18?by0-18:by1+3;
 if(ly>608)ly=608;if(ly<0)ly=0;ldx=xx-lx;ldy=yy-ly;
 if(ldx>=0 && ldx<label_width && ldy[13:4]==0)begin
 back_on=1;back=24'h101824;label_text=1;ink=j==0?color_a:color_b;label_gx={1'b0,ldx[2:0]};label_gy=ldy[3:0];lc=ldx[6:3];
 case({I_pair,j[0]})
2'd0:case(lc)
0:label_glyph=8'd28;
1:label_glyph=8'd15;
2:label_glyph=8'd14;
3:label_glyph=8'd0;
4:label_glyph=8'd11;
5:label_glyph=8'd2;
endcase
2'd1:case(lc)
0:label_glyph=8'd12;
1:label_glyph=8'd22;
2:label_glyph=8'd31;
3:label_glyph=8'd15;
4:label_glyph=8'd0;
5:label_glyph=8'd12;
6:label_glyph=8'd2;
endcase
2'd2:case(lc)
0:label_glyph=8'd35;
1:label_glyph=8'd15;
2:label_glyph=8'd22;
3:label_glyph=8'd22;
4:label_glyph=8'd25;
5:label_glyph=8'd33;
6:label_glyph=8'd0;
7:label_glyph=8'd11;
8:label_glyph=8'd2;
endcase
2'd3:case(lc)
0:label_glyph=8'd26;
1:label_glyph=8'd31;
2:label_glyph=8'd28;
3:label_glyph=8'd26;
4:label_glyph=8'd22;
5:label_glyph=8'd15;
6:label_glyph=8'd0;
7:label_glyph=8'd12;
8:label_glyph=8'd2;
endcase
endcase
 end end end
 if(I_show && I_detection_valid && I_meta[32])begin
 lx=$signed(geometry[224+:14]);ly=$signed(geometry[238+:14]);ldx=xx-lx;ldy=yy-ly;
 if((ldx>=-6 && ldx<=6 && ldy>=-1 && ldy<=1)||(ldy>=-6 && ldy<=6 && ldx>=-1 && ldx<=1))begin back_on=1;back=24'h40ff90;end end
 if(I_meta[567:565]!=0 && border(xx,yy,$signed(geometry[168+:14]),$signed(geometry[182+:14]),$signed(geometry[196+:14]),$signed(geometry[210+:14])))begin back_on=1;back=24'h80ff80;end
 if(I_show && I_tracking && I_meta[36:33]<=2 && border(xx,yy,$signed(geometry[112+:14]),$signed(geometry[126+:14]),$signed(geometry[140+:14]),$signed(geometry[154+:14])))begin back_on=1;back=24'h40c080;end
 if(I_show && I_mode==1 && border(xx,yy,$signed(geometry[168+:14]),$signed(geometry[182+:14]),$signed(geometry[196+:14]),$signed(geometry[210+:14])))begin back_on=1;back=24'h80ff80;end
 end
 if(y<624 && I_show && I_video_ok && region_label_on && !back_on && !label_text)begin
 back_on=1;back=24'h101824;label_text=1;label_glyph=region_label_glyph;label_gx={1'b0,region_label_gx};label_gy=region_label_gy;ink=region_label_color;
 end end
 wire [9:0] shared_font_addr=footer_text?{footer_glyph[5:0],footer_gy[3:0]}:{label_glyph[5:0],label_gy};
 wire [7:0] shared_font_row;wire [1:0] logo_pixel;
 refined_english_font_rom shared_font(I_clk,shared_font_addr,shared_font_row);
 refined_logo_rom logo(I_clk,logo_addr,logo_pixel);
 reg [4:0] footer_px_d;reg [3:0] label_gx_d;reg footer_d,label_d,logo_d,back_d,vs_d,hs_d,de_d;
 reg [23:0] ink_d,bg_d,rgb_d;reg region_enable_d;
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin
 region_enable_d<=0;x<=0;y<=0;vs_last<=0;footer_col<=0;footer_px<=0;footer_px_d<=0;label_gx_d<=0;footer_d<=0;label_d<=0;logo_d<=0;back_d<=0;
 vs_d<=0;hs_d<=0;de_d<=0;ink_d<=0;bg_d<=0;rgb_d<=0;O_vs<=0;O_hs<=0;O_de<=0;O_rgb<=0;
 end else begin
 vs_last<=I_vs;if(I_vs && !vs_last)begin x<=0;y<=0;end
 else if(I_de)begin if(x==1279)begin x<=0;y<=y+1'b1;end else x<=x+1'b1;end
 if(I_de)begin if(x==0)begin footer_col<=0;footer_px<=0;end
 else if(x>=16 && x<16+COLS*CHAR_WIDTH)begin if(footer_px==CHAR_WIDTH-1)begin footer_px<=0;footer_col<=footer_col+1'b1;end else footer_px<=footer_px+1'b1;end end
 region_enable_d<=I_show && I_video_ok;footer_px_d<=footer_px;label_gx_d<=label_gx;footer_d<=footer_text;label_d<=label_text;logo_d<=logo_on;back_d<=back_on;
 ink_d<=ink;bg_d<=back;rgb_d<=I_rgb;vs_d<=I_vs;hs_d<=I_hs;de_d<=I_de;
 O_vs<=vs_d;O_hs<=hs_d;O_de<=de_d;
 O_rgb<=logo_d && logo_pixel!=0?(logo_pixel==1?24'h1c2c4e:logo_pixel==2?24'hed1b23:24'he0e8f4):
 footer_d && shared_font_row[7-footer_px_d[2:0]]?ink_d:
 label_d && shared_font_row[7-label_gx_d[2:0]]?ink_d:back_d?bg_d:region_enable_d && region_pixel!=0?region_color:rgb_d;
 end end
endmodule
`default_nettype wire
