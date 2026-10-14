// Generated compact functional UI. No diagnostic panel or tool-tip estimator.
`default_nettype none
module stable_osd(
 input wire I_clk,I_rst_n,I_vs,I_hs,I_de,input wire [23:0] I_rgb,
 input wire [639:0] I_meta,input wire [10:0] I_x0,input wire [9:0] I_y0,
 input wire [1:0] I_zoom,I_mode,input wire [2:0] I_state,
 input wire I_tracking,I_show,I_video_ok,I_pair,I_detection_valid,I_sample_valid,
 output reg O_vs,O_hs,O_de,output reg [23:0] O_rgb
);
 reg [10:0] x;reg [9:0] y;reg vs_last;
 wire [2:0] na=I_meta[604]?I_meta[338:336]:0;
 wire [2:0] nb=I_meta[604]?I_meta[341:339]:0;
 wire [23:0] color_a=I_pair?24'hFFFF40:24'hFF6060,color_b=I_pair?24'hE080FF:24'h6090FF;
 function signed [13:0] mapx;input [10:0] v;begin mapx=($signed({3'b0,v})-$signed({3'b0,I_x0}))<<<I_zoom;end endfunction
 function signed [13:0] mapy;input [9:0] v;begin mapy=($signed({4'b0,v})-$signed({4'b0,I_y0}))<<<I_zoom;end endfunction
 function border;input signed [13:0] xx,yy,x0,x1,y0,y1;reg signed [13:0] l,r,t,b;begin
 l=xx-x0;r=x1-xx;t=yy-y0;b=y1-yy;
 border=!(l[13] || r[13] || t[13] || b[13]) && (l[13:1]==0 || r[13:1]==0 || t[13:1]==0 || b[13:1]==0);
 end endfunction
 function [11:0] bcd;input [7:0] value;reg [7:0] r;reg [3:0] h,t;integer z;begin
 h=value>=200?2:value>=100?1:0;r=value-(h==2?200:h==1?100:0);t=0;
 for(z=1;z<=9;z=z+1)if(r>=z*10)t=z;r=r-((t<<3)+(t<<1));bcd={h,t,r[3:0]};
 end endfunction
 wire [11:0] red_bcd=bcd(I_meta[407:400]),green_bcd=bcd(I_meta[399:392]),blue_bcd=bcd(I_meta[391:384]);
 reg [6:0] glyph;reg [3:0] gx,gy;reg text_on,back_on;reg [23:0] ink,back;
 reg [41:0] box;reg valid_box;reg signed [13:0] xx,yy,bx0,bx1,by0,by1,lx,ly,ldx,ldy;
 reg [5:0] col;reg row;integer j,lc;
 function [6:0] footer;input row;input [5:0] col;begin
 footer=0;
 if(!row)begin case(col)
0:footer=51;
1:footer=52;
2:footer=37;
3:footer=I_mode==0?41:I_mode==1?43:I_mode==2?47:I_mode==3?43:0;
4:footer=I_mode==0?42:I_mode==1?44:I_mode==2?48:I_mode==3?44:0;
5:footer=I_mode==0?0:I_mode==1?45:I_mode==2?0:I_mode==3?49:0;
6:footer=I_mode==0?0:I_mode==1?46:I_mode==2?0:I_mode==3?50:0;
8:footer=53;
9:footer=54;
10:footer=37;
11:footer=I_zoom==0?2:I_zoom==1?3:5;
14:footer=55;
15:footer=43;
16:footer=37;
17:footer=I_pair==0?56:I_pair==1?58:0;
18:footer=I_pair==0?57:I_pair==1?59:0;
21:footer=60;
22:footer=61;
23:footer=0;
24:footer=11;
25:footer=37;
26:footer=1+na;
27:footer=I_detection_valid && I_meta[605]?38:0;
29:footer=12;
30:footer=37;
31:footer=1+nb;
32:footer=I_detection_valid && I_meta[606]?38:0;
35:footer=122;
36:footer=123;
37:footer=29;
38:footer=3;
39:footer=0;
endcase end else begin case(col)
0:footer=62;
1:footer=63;
2:footer=37;
3:footer=I_state==0?64:I_state==1?66:I_state==2?69:I_state==3?71:I_state==4?69:I_state==5?75:I_state==6?79:I_state==7?84:0;
4:footer=I_state==0?65:I_state==1?67:I_state==2?70:I_state==3?72:I_state==4?70:I_state==5?76:I_state==6?80:I_state==7?85:0;
5:footer=I_state==0?0:I_state==1?68:I_state==2?0:I_state==3?69:I_state==4?73:I_state==5?77:I_state==6?81:I_state==7?86:0;
6:footer=I_state==0?0:I_state==1?0:I_state==2?0:I_state==3?70:I_state==4?74:I_state==5?78:I_state==6?82:I_state==7?0:0;
7:footer=I_state==0?0:I_state==1?0:I_state==2?0:I_state==3?0:I_state==4?0:I_state==5?0:I_state==6?83:I_state==7?0:0;
11:footer=I_detection_valid && 1'b0?87:0;
12:footer=I_detection_valid && 1'b0?71:0;
13:footer=I_detection_valid && 1'b0?69:0;
14:footer=I_detection_valid && 1'b0?70:0;
15:footer=I_detection_valid && 1'b0?64:0;
16:footer=I_detection_valid && 1'b0?88:0;
19:footer=28;
20:footer=17;
21:footer=12;
22:footer=37;
23:footer=I_mode==1 && I_show && I_sample_valid?1+red_bcd[11-:4]:39;
24:footer=I_mode==1 && I_show && I_sample_valid?1+red_bcd[7-:4]:39;
25:footer=I_mode==1 && I_show && I_sample_valid?1+red_bcd[3-:4]:39;
26:footer=40;
27:footer=I_mode==1 && I_show && I_sample_valid?1+green_bcd[11-:4]:39;
28:footer=I_mode==1 && I_show && I_sample_valid?1+green_bcd[7-:4]:39;
29:footer=I_mode==1 && I_show && I_sample_valid?1+green_bcd[3-:4]:39;
30:footer=40;
31:footer=I_mode==1 && I_show && I_sample_valid?1+blue_bcd[11-:4]:39;
32:footer=I_mode==1 && I_show && I_sample_valid?1+blue_bcd[7-:4]:39;
33:footer=I_mode==1 && I_show && I_sample_valid?1+blue_bcd[3-:4]:39;
endcase end
 if(row && col>=3 && col<19)begin
footer=0;
if(I_meta[36:33]==0 && I_tracking)case(col)
3:footer=64;
4:footer=65;
endcase
if(I_meta[36:33]==1 && I_tracking)case(col)
3:footer=68;
4:footer=93;
5:footer=61;
6:footer=89;
endcase
if(I_meta[36:33]==2 && I_tracking)case(col)
3:footer=94;
4:footer=95;
5:footer=68;
endcase
if(I_meta[36:33]==3 && I_tracking)case(col)
3:footer=96;
4:footer=97;
5:footer=68;
endcase
if(I_meta[36:33]==4 && I_tracking)case(col)
3:footer=98;
4:footer=43;
endcase
if(I_meta[36:33]==5 && I_tracking)case(col)
3:footer=99;
4:footer=100;
5:footer=101;
6:footer=102;
endcase
if(I_meta[36:33]==6 && I_tracking)case(col)
3:footer=68;
4:footer=93;
5:footer=103;
6:footer=61;
endcase
if(I_meta[36:33]==7 && I_tracking)case(col)
3:footer=104;
4:footer=105;
5:footer=106;
6:footer=107;
endcase
if(I_meta[36:33]==8 && I_tracking)case(col)
3:footer=84;
4:footer=108;
5:footer=86;
endcase

if(!I_tracking)case(col)
3:footer=64;
4:footer=65;
endcase
if(I_meta[567:565]==1)case(col)
3:footer=112;
4:footer=113;
5:footer=75;
6:footer=21;
7:footer=15;
8:footer=35;
9:footer=4;
endcase
if(I_meta[567:565]==2)case(col)
3:footer=114;
4:footer=115;
5:footer=116;
6:footer=75;
7:footer=21;
8:footer=15;
9:footer=35;
10:footer=4;
endcase
if(I_meta[567:565]==3)case(col)
3:footer=11;
4:footer=43;
5:footer=75;
6:footer=21;
7:footer=15;
8:footer=35;
9:footer=4;
endcase
if(I_meta[567:565]==4)case(col)
3:footer=12;
4:footer=43;
5:footer=75;
6:footer=21;
7:footer=15;
8:footer=35;
9:footer=4;
endcase

if(I_meta[564] && I_meta[567:565]!=0)case(col)
3:footer=117;
4:footer=90;
5:footer=118;
6:footer=119;
7:footer=68;
endcase
if(I_meta[563:560]!=0 && I_meta[567:565]!=0)case(col)
3:footer=117;
4:footer=90;
5:footer=99;
6:footer=120;
7:footer=103;
8:footer=121;
endcase
if(I_meta[563:560]!=0 && I_meta[567:565]!=0)begin if(col==15)footer=15;if(col==16)footer=1+I_meta[563:560];end
if(I_meta[568] && I_meta[567:565]==0)case(col)
3:footer=109;
4:footer=103;
5:footer=85;
6:footer=110;
7:footer=111;
endcase
end
 if(row && col>=19 && col<=33 && !(I_mode==1 && I_show))footer=0;
 if(row && col>=3 && col<19)begin
if(I_tracking && !I_detection_valid)begin footer=0;case(col)
3:footer=124;
4:footer=64;
5:footer=125;
6:footer=126;
endcase end
if(I_state==5)begin footer=0;case(col)
3:footer=75;
4:footer=76;
5:footer=77;
6:footer=78;
endcase end
if(I_state==7)begin footer=0;case(col)
3:footer=84;
4:footer=85;
5:footer=86;
endcase end
if(!I_video_ok || I_state==6)begin footer=0;case(col)
3:footer=79;
4:footer=80;
5:footer=81;
6:footer=82;
7:footer=83;
endcase end
end
 end endfunction
 always @*begin
   glyph=0;gx=0;gy=0;text_on=0;back_on=0;ink=24'hF0F4FF;back=24'h101824;
   box=0;valid_box=0;xx=$signed({3'b0,x});yy=$signed({4'b0,y});bx0=0;bx1=0;by0=0;by1=0;lx=0;ly=0;ldx=0;ldy=0;lc=0;col=0;row=0;
   if(y>=624)begin
     back_on=1;
     if((y>=632 && y<664)||(y>=676 && y<708))begin
       row=y>=676;col=x[10:5];glyph=footer(row,col);gx=x[4:1];gy=row?(y-676)>>1:(y-632)>>1;text_on=1;
     end
   end else if(I_video_ok)begin
     if(I_show && I_detection_valid)for(j=0;j<2;j=j+1)begin
       case(j)
         0:begin box=I_meta[141:100];valid_box=I_meta[245];end
         1:begin box=I_meta[183:142];valid_box=I_meta[246];end
         
         
       endcase
       bx0=mapx(box[10:0]);bx1=mapx(box[21:11])+(14'sd1<<<I_zoom)-1;
       by0=mapy(box[31:22]);by1=mapy(box[41:32])+(14'sd1<<<I_zoom)-1;
       if(valid_box && bx1>=0 && bx0<1280 && by1>=0 && by0<624)begin
         if(border(xx,yy,bx0,bx1,by0,by1))begin back_on=1;back=j==0?color_a:color_b;end
         lx=bx0<0?0:bx0>1216?1216:bx0;ly=by0>=18?by0-18:by1+3;
         if(ly>608)ly=608;if(ly<0)ly=0;
         ldx=xx-lx;ldy=yy-ly;
         if(ldx[13:6]==0 && ldy[13:4]==0)begin
           back_on=1;back=24'h101824;text_on=1;ink=j==0?color_a:color_b;
           gx=ldx[3:0];gy=ldy[3:0];lc=ldx[5:4];
           case(lc)
             0:glyph=j==0?(I_pair?58:56):(I_pair?59:57);
             1:glyph=43;2:glyph=j==0?11:12;3:glyph=2;
           endcase
         end
       end
     end
     if(I_show && I_detection_valid && I_meta[32])begin
       lx=mapx(I_meta[89:79]);ly=mapy(I_meta[99:90]);ldx=xx-lx;ldy=yy-ly;
       if((ldx>=-6 && ldx<=6 && ldy>=-1 && ldy<=1)||(ldy>=-6 && ldy<=6 && ldx>=-1 && ldx<=1))begin back_on=1;back=24'h40ff90;end
     end
     if(I_meta[567:565]!=0 && border(xx,yy,mapx(632),mapx(647)+(14'sd1<<<I_zoom)-1,mapy(352),mapy(367)+(14'sd1<<<I_zoom)-1))begin back_on=1;back=24'h80ff80;end
     if(I_show && I_tracking && I_meta[36:33]<=2 && border(xx,yy,mapx(320),mapx(959),mapy(180),mapy(539)))begin back_on=1;back=24'h40c080;end
     if(I_show && I_mode==1 && border(xx,yy,mapx(636),mapx(643)+(14'sd1<<<I_zoom)-1,mapy(356),mapy(363)+(14'sd1<<<I_zoom)-1))begin
       back_on=1;back=24'h80FF80;
     end
   end
 end
 wire [15:0] font_row;stable_glyph_rom font(I_clk,{glyph,gy},font_row);
 reg [3:0] gx_d;reg txt_d,back_d,vs_d,hs_d,de_d;reg [23:0] ink_d,bg_d,rgb_d;
 always @(posedge I_clk or negedge I_rst_n)begin
   if(!I_rst_n)begin
     x<=0;y<=0;vs_last<=0;gx_d<=0;txt_d<=0;back_d<=0;vs_d<=0;hs_d<=0;de_d<=0;ink_d<=0;bg_d<=0;rgb_d<=0;
     O_vs<=0;O_hs<=0;O_de<=0;O_rgb<=0;
   end else begin
     vs_last<=I_vs;if(I_vs && !vs_last)begin x<=0;y<=0;end
     else if(I_de)begin if(x==1279)begin x<=0;y<=y+1'b1;end else x<=x+1'b1;end
     gx_d<=gx;txt_d<=text_on;back_d<=back_on;ink_d<=ink;bg_d<=back;rgb_d<=I_rgb;vs_d<=I_vs;hs_d<=I_hs;de_d<=I_de;
     O_vs<=vs_d;O_hs<=hs_d;O_de<=de_d;O_rgb<=txt_d && font_row[15-gx_d]?ink_d:back_d?bg_d:rgb_d;
   end
 end
endmodule
`default_nettype wire
