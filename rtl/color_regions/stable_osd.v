// Generated upright UI. Source geometry is mapped through the committed view.
// One shared decimal converter formats the selected footer before row624.
`default_nettype none
module stable_osd(
 input wire I_clk,I_rst_n,I_vs,I_hs,I_de,input wire [23:0] I_rgb,
 input wire [639:0] I_meta,input wire [10:0] I_x0,input wire [9:0] I_y0,
 input wire [1:0] I_zoom,I_mode,input wire [2:0] I_state,
 input wire I_tracking,I_show,I_video_ok,I_pair,I_detection_valid,I_sample_valid,
 output reg O_vs,O_hs,O_de,output reg [23:0] O_rgb,
 input wire I_rotate,input wire [1:0] I_diag,input wire [31:0] I_image_id
);
 localparam FONT=24,COLS=46;
 reg [10:0] x;reg [9:0] y;reg vs_last;
 reg [639:0] fm;reg [31:0] fimage;reg [1:0] fmode,fzoom,fdiag;
 reg [2:0] fstate;reg fpair,frotate,ftracking,fshow,fvideo,fdetection,fsample;
 reg [4:0] status_id;
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
 function [19:0] field_value;input [4:0] id;begin
 case(id)
 0:field_value=fm[203:184];1:field_value=fm[223:204];
 2:field_value=fm[275:256];3:field_value=fm[315:296];4:field_value=fm[295:276];5:field_value=fm[335:316];
 6:field_value=fm[356:350];7:field_value=fm[363:357];
 8:field_value=fm[478:470];9:field_value=fm[469:461];10:field_value=fm[460:453];11:field_value=fm[452:445];
 12:field_value=fm[542:534];13:field_value=fm[533:525];14:field_value=fm[524:517];15:field_value=fm[516:509];
 16:field_value=fm[592:581];17:field_value=fm[580:569];
 18:field_value=fm[407:400];19:field_value=fm[399:392];20:field_value=fm[391:384];
 21:field_value=fm[383:380];22:field_value=fm[624:607];23:field_value=fm[639:625];default:field_value=0;
 endcase end endfunction
 reg [23:0] numbers[0:23];reg [7:0] characters[0:127];
 reg [2:0] format_state;reg [4:0] field_index,bit_index;
 reg [19:0] binary;reg [23:0] decimal,adjusted;reg [5:0] format_col;reg format_row,footer_ready;
 integer nibble;
 always @*begin adjusted=decimal;for(nibble=0;nibble<6;nibble=nibble+1)
 if(decimal[nibble*4+:4]>=5)adjusted[nibble*4+:4]=decimal[nibble*4+:4]+3;end
reg [4:0] template_index;reg token_valid;reg [31:0] hex_value;reg [7:0] decoded_glyph;
wire [15:0] token_data;wire [7:0] dynamic_glyph;
wire [10:0] program_addr={template_index,format_col};
wire [8:0] dynamic_addr=token_data[12:8]==0?({7'd0,fmode}<<2)+{5'd0,token_data[3:0]}:
9'd64+({4'd0,status_id}<<4)+{5'd0,token_data[3:0]};
stable_footer_program_rom program_rom(I_clk,program_addr,token_data);
stable_footer_text_rom text_rom(I_clk,dynamic_addr,dynamic_glyph);
always @*begin
template_index=({3'd0,fdiag}<<1)+format_row;
if(fm[567:565]!=0)begin
if(!format_row)template_index=6;
else if(fm[563:560]!=0)template_index=12+{1'b0,fm[563:560]};
else if(fm[564])template_index=11;
else template_index=6+{2'd0,fm[567:565]};end
token_valid=1;case(token_data[7:4])
0:token_valid=1'b1;
1:token_valid=fsample && fmode==1 && fshow;
2:token_valid=fm[255] && fm[415:413]==3;
3:token_valid=fdetection && fm[245];
4:token_valid=fdetection && fm[246];
5:token_valid=fm[604];
default:token_valid=0;endcase
hex_value=0;case(token_data[12:8])
0:hex_value=fimage;
1:hex_value=fm[559:544];
2:hex_value=fm[345:342];
3:hex_value=fm[349:346];
4:hex_value=fm[377:370];
5:hex_value=fm[563:560];
endcase
decoded_glyph=0;case(token_data[15:13])
0:decoded_glyph=token_data[7:0];
1:decoded_glyph=token_valid?8'd1+((numbers[token_data[12:8]]>>(token_data[3:0]*4)) & 4'hf):8'd150;
2:decoded_glyph=token_valid?8'd1+((hex_value>>(token_data[3:0]*4)) & 4'hf):8'd150;
3:case(token_data[12:8])
0:decoded_glyph=fzoom==0?8'd2:fzoom==1?8'd3:8'd5;
1:decoded_glyph=fpair?8'd137:8'd135;
2:decoded_glyph=fpair?8'd138:8'd136;
3:decoded_glyph=frotate?8'd2:8'd1;
4:decoded_glyph=frotate?8'd9:8'd1;
5:decoded_glyph=frotate?8'd1:8'd1;
6:decoded_glyph=fm[444:443]==0?8'd4:fm[444:443]==1?8'd5:fm[444:443]==2?8'd7:8'd9;
7:decoded_glyph=fm[508:507]==0?8'd4:fm[508:507]==1?8'd5:fm[508:507]==2?8'd7:8'd9;
endcase
4:begin if(!token_valid)decoded_glyph=8'd150;else case(token_data[12:8])
0:decoded_glyph=8'd1+fm[338:336];
1:decoded_glyph=8'd1+fm[365:364];
2:decoded_glyph=8'd1+fm[341:339];
3:decoded_glyph=8'd1+fm[367:366];
4:decoded_glyph=8'd1+fm[369:368];
5:decoded_glyph=8'd1+fm[379:378];
endcase end
5:decoded_glyph=dynamic_glyph;
endcase end

 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin
 fm<=0;fimage<=0;fmode<=0;fzoom<=0;fdiag<=0;fstate<=6;fpair<=0;frotate<=1;ftracking<=0;fshow<=1;fvideo<=0;fdetection<=0;fsample<=0;
 format_state<=0;field_index<=0;bit_index<=0;binary<=0;decimal<=0;format_col<=0;format_row<=0;footer_ready<=0;
 end else begin
 case(format_state)
 1:begin binary<=field_value(field_index);decimal<=0;bit_index<=0;format_state<=2;end
 2:begin binary<=binary<<1;decimal<={adjusted[22:0],binary[19]};
 if(bit_index==19)begin numbers[field_index]<={adjusted[22:0],binary[19]};
 if(field_index==23)begin format_col<=0;format_row<=0;format_state<=3;end
 else begin field_index<=field_index+1'b1;format_state<=1;end end
 else bit_index<=bit_index+1'b1;end
 3:format_state<=4;
 4:format_state<=5;
 5:format_state<=6;
 6:format_state<=7;
 7:begin characters[(format_row?COLS:0)+format_col]<=decoded_glyph;
 format_state<=3;
 if(format_col==COLS-1)begin format_col<=0;if(format_row)begin footer_ready<=1;format_state<=0;end else format_row<=1;end
 else format_col<=format_col+1'b1;end
 endcase
 if(I_de && y==620 && x==0)begin
 fm<=I_meta;fimage<=I_image_id;fmode<=I_mode;fzoom<=I_zoom;fdiag<=I_diag;fstate<=I_state;
 fpair<=I_pair;frotate<=I_rotate;ftracking<=I_tracking;fshow<=I_show;fvideo<=I_video_ok;fdetection<=I_detection_valid;fsample<=I_sample_valid;
 field_index<=0;footer_ready<=0;format_state<=1;
 end end end
 function signed [13:0] mapx;input [10:0] v;reg signed [13:0] d;begin
 d=$signed({3'd0,v})-$signed({3'd0,I_x0});
 mapx=(I_rotate?($signed(14'd1280>>>I_zoom)-1-d):d)<<<I_zoom;end endfunction
 function signed [13:0] mapy;input [9:0] v;reg signed [13:0] d;begin
 d=$signed({4'd0,v})-$signed({4'd0,I_y0});
 mapy=(I_rotate?($signed(14'd624>>>I_zoom)-1-d):d)<<<I_zoom;end endfunction
 function border;input signed [13:0] xx,yy,x0,x1,y0,y1;reg signed [13:0] l,r,t,b;begin
 l=xx-x0;r=x1-xx;t=yy-y0;b=y1-yy;
 border=!(l[13] || r[13] || t[13] || b[13]) && (l[13:1]==0 || r[13:1]==0 || t[13:1]==0 || b[13:1]==0);end endfunction
 wire [23:0] color_a=I_pair?24'hffff40:24'hff6060,color_b=I_pair?24'he080ff:24'h6090ff;
 reg [5:0] footer_col;reg [4:0] footer_px;
 reg [7:0] footer_glyph;reg [4:0] footer_gy;reg footer_text,footer_row;
 reg [3:0] label_glyph,label_gx,label_gy;reg label_text,back_on,logo_on;
 reg [23:0] ink,back;reg [12:0] logo_addr;reg [41:0] box;reg valid_box;
 reg signed [13:0] xx,yy,bx0,bx1,by0,by1,lx,ly,ldx,ldy;
 integer j,lc;reg [9:0] logo_y;reg [10:0] logo_x;
 localparam [31:0] WAIT_WORD={8'd84,8'd37,8'd85,8'd86};
 wire footer_current=footer_ready && I_tracking==ftracking && I_video_ok==fvideo && I_detection_valid==fdetection && I_state==fstate;
 always @*begin
 footer_glyph=0;footer_gy=0;footer_text=0;footer_row=0;label_glyph=0;label_gx=0;label_gy=0;label_text=0;
 back_on=0;back=24'h101824;ink=24'hf0f4ff;logo_on=0;logo_addr=0;logo_y=0;logo_x=0;
 box=0;valid_box=0;xx=$signed({3'd0,x});yy=$signed({4'd0,y});bx0=0;bx1=0;by0=0;by1=0;lx=0;ly=0;ldx=0;ldy=0;lc=0;
 if(y>=624)begin
 back_on=1;
 if(x>=1152)back=24'hffffff;
 if(x>=1168 && x<1264 && y>=641 && y<703)begin
 logo_on=1;logo_y=y-641;logo_x=x-1168;logo_addr=(logo_y<<6)+(logo_y<<5)+logo_x;end
 if(x>=16 && x<16+COLS*FONT && ((y>=632+(32-FONT)/2 && y<632+(32-FONT)/2+FONT) ||
 (y>=676+(32-FONT)/2 && y<676+(32-FONT)/2+FONT)))begin
 footer_row=y>=676;footer_gy=footer_row?y-(676+(32-FONT)/2):y-(632+(32-FONT)/2);
 footer_text=1;
 if(footer_current)footer_glyph=characters[(footer_row?COLS:0)+footer_col];
 else if(footer_ready && !footer_row && footer_col<4)footer_glyph=WAIT_WORD>>((3-footer_col)*8);
 end
 end else if(I_video_ok)begin
 if(I_show && I_detection_valid)for(j=0;j<2;j=j+1)begin
 box=j==0?I_meta[141:100]:I_meta[183:142];valid_box=j==0?I_meta[245]:I_meta[246];
 bx0=mapx(I_rotate?box[21:11]:box[10:0]);bx1=mapx(I_rotate?box[10:0]:box[21:11])+(14'sd1<<<I_zoom)-1;
 by0=mapy(I_rotate?box[41:32]:box[31:22]);by1=mapy(I_rotate?box[31:22]:box[41:32])+(14'sd1<<<I_zoom)-1;
 if(valid_box && bx1>=0 && bx0<1280 && by1>=0 && by0<624)begin
 if(border(xx,yy,bx0,bx1,by0,by1))begin back_on=1;back=j==0?color_a:color_b;end
 lx=bx0<0?0:bx0>1216?1216:bx0;ly=by0>=18?by0-18:by1+3;
 if(ly>608)ly=608;if(ly<0)ly=0;ldx=xx-lx;ldy=yy-ly;
 if(ldx[13:6]==0 && ldy[13:4]==0)begin
 back_on=1;back=24'h101824;label_text=1;ink=j==0?color_a:color_b;label_gx=ldx[3:0];label_gy=ldy[3:0];lc=ldx[5:4];
 case(lc)0:label_glyph=j==0?(I_pair?3:1):(I_pair?4:2);1:label_glyph=5;2:label_glyph=j==0?6:7;3:label_glyph=8;endcase
 end end end
 if(I_show && I_detection_valid && I_meta[32])begin
 lx=mapx(I_meta[89:79]);ly=mapy(I_meta[99:90]);ldx=xx-lx;ldy=yy-ly;
 if((ldx>=-6 && ldx<=6 && ldy>=-1 && ldy<=1)||(ldy>=-6 && ldy<=6 && ldx>=-1 && ldx<=1))begin back_on=1;back=24'h40ff90;end end
 if(I_meta[567:565]!=0 && I_meta[567:565]!=2 && border(xx,yy,mapx(I_rotate?647:632),mapx(I_rotate?632:647)+(14'sd1<<<I_zoom)-1,
 mapy(I_rotate?367:352),mapy(I_rotate?352:367)+(14'sd1<<<I_zoom)-1))begin back_on=1;back=24'h80ff80;end
 if(I_show && I_tracking && I_meta[36:33]<=2 && border(xx,yy,mapx(I_rotate?959:320),mapx(I_rotate?320:959),mapy(I_rotate?539:180),mapy(I_rotate?180:539)))begin back_on=1;back=24'h40c080;end
 if(I_show && I_mode==1 && border(xx,yy,mapx(I_rotate?643:636),mapx(I_rotate?636:643)+(14'sd1<<<I_zoom)-1,
 mapy(I_rotate?363:356),mapy(I_rotate?356:363)+(14'sd1<<<I_zoom)-1))begin back_on=1;back=24'h80ff80;end
 end end
 wire [11:0] footer_addr=(footer_glyph<<4)+(footer_glyph<<3)+footer_gy;
 wire [FONT-1:0] footer_font_row;wire [15:0] label_font_row;wire [1:0] logo_pixel;
 stable_footer_glyph_rom footer_font(I_clk,footer_addr,footer_font_row);
 stable_glyph_rom label_font(I_clk,{label_glyph,label_gy},label_font_row);
 scaling_logo_rom logo(I_clk,logo_addr,logo_pixel);
 reg [4:0] footer_px_d;reg [3:0] label_gx_d;reg footer_d,label_d,logo_d,back_d,vs_d,hs_d,de_d;
 reg [23:0] ink_d,bg_d,rgb_d;
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin
 x<=0;y<=0;vs_last<=0;footer_col<=0;footer_px<=0;footer_px_d<=0;label_gx_d<=0;footer_d<=0;label_d<=0;logo_d<=0;back_d<=0;
 vs_d<=0;hs_d<=0;de_d<=0;ink_d<=0;bg_d<=0;rgb_d<=0;O_vs<=0;O_hs<=0;O_de<=0;O_rgb<=0;
 end else begin
 vs_last<=I_vs;if(I_vs && !vs_last)begin x<=0;y<=0;end
 else if(I_de)begin if(x==1279)begin x<=0;y<=y+1'b1;end else x<=x+1'b1;end
 if(I_de)begin if(x==0)begin footer_col<=0;footer_px<=0;end
 else if(x>=16 && x<16+COLS*FONT)begin if(footer_px==FONT-1)begin footer_px<=0;footer_col<=footer_col+1'b1;end else footer_px<=footer_px+1'b1;end end
 footer_px_d<=footer_px;label_gx_d<=label_gx;footer_d<=footer_text;label_d<=label_text;logo_d<=logo_on;back_d<=back_on;
 ink_d<=ink;bg_d<=back;rgb_d<=I_rgb;vs_d<=I_vs;hs_d<=I_hs;de_d<=I_de;
 O_vs<=vs_d;O_hs<=hs_d;O_de<=de_d;
 O_rgb<=logo_d?(logo_pixel==1?24'h1c2c4e:logo_pixel==2?24'hed1b23:24'hffffff):
 footer_d && footer_font_row[FONT-1-footer_px_d]?ink_d:
 label_d && label_font_row[15-label_gx_d]?ink_d:back_d?bg_d:rgb_d;
 end end
endmodule
`default_nettype wire
