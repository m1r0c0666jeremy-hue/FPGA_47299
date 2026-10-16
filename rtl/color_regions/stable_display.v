// Image bank, v3 metadata, model and moving viewport commit together in blank.
`default_nettype none
module stable_display #(parameter STALE_DISPLAY_FRAMES=15,V4=0,MW=V4?768:640,SW=V4?852:675)(
 input wire I_clk,I_rst_n,I_vs,I_de,I_snapshot,input wire [SW-1:0] I_data,
 input wire I_tracking,I_show,I_conflict,I_live,input wire [7:0] I_session,
 input wire [2:0] I_zoom,input wire [1:0] I_mode,input wire I_pair,
 output reg O_commit,output reg [1:0] O_bank,output reg [31:0] O_frame_id,
 output reg [10:0] O_cx,O_x0,output reg [9:0] O_cy,O_y0,
 output reg [2:0] O_zoom,output reg [1:0] O_mode,output reg [MW-1:0] O_meta,
 output reg O_show,O_pair,output wire O_detection_valid,output wire O_sample_valid,output wire [2:0] O_state,input wire I_rotate,output reg O_rotate,
 output reg [31:0] O_image_us,output reg [15:0] O_epoch,output reg O_time_valid);
 reg vs_last,in_blank,associated;reg [7:0] age,session;
 wire match=I_data[MW+34] && I_data[255] && I_data[415:413]==(V4?4:3) && I_data[31:0]==I_data[MW+:32] &&
 (!V4 || I_data[719:704]==I_data[SW-2-:16]) &&
 I_data[242:235]==I_session && I_data[243]==I_pair && I_data[244]==I_tracking;
 assign O_detection_valid=associated && I_tracking && I_live && session==I_session && O_pair==I_pair && age<STALE_DISPLAY_FRAMES && O_meta[247];
 assign O_sample_valid=associated && I_live && session==I_session && O_pair==I_pair && age<STALE_DISPLAY_FRAMES && O_meta[247] && O_meta[408];
 assign O_state=I_conflict?5:!I_live?6:age>=STALE_DISPLAY_FRAMES?7:!I_tracking?0:!O_detection_valid?1:O_meta[32]?2:O_meta[36:33]==8?4:1;
 reg signed [12:0] dx,dy;reg [10:0] cx,hx;reg [9:0] cy,hy;
 wire [10:0] view_width;wire [9:0] view_height;
 refined_zoom_geometry view_geometry(I_zoom,I_rotate,view_width,view_height,,,,);
 always @*begin
 dx=$signed({2'd0,I_data[89:79]})-$signed({2'd0,O_cx});dy=$signed({3'd0,I_data[99:90]})-$signed({3'd0,O_cy});
 cx=O_cx;cy=O_cy;
 if(dx>4)cx=O_cx+(dx>24?24:dx);if(dx< -4)cx=O_cx+(dx< -24?-24:dx);
 if(dy>4)cy=O_cy+(dy>24?24:dy);if(dy< -4)cy=O_cy+(dy< -24?-24:dy);
 if(!match || !I_data[32] || I_data[MW+:32]==O_frame_id)begin cx=O_cx;cy=O_cy;end
 hx=view_width>>1;hy=view_height>>1;
 if(cx<hx)cx=hx;if(cx>1280-view_width+hx)cx=1280-view_width+hx;
 if(cy<hy)cy=hy;if(cy>720-view_height+hy)cy=720-view_height+hy;
 end
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin vs_last<=0;in_blank<=0;associated<=0;age<=0;session<=0;O_commit<=0;O_bank<=0;O_frame_id<=0;
 O_cx<=640;O_cy<=360;O_x0<=0;O_y0<=48;O_zoom<=0;O_mode<=0;O_meta<=0;O_show<=1;O_pair<=0;O_rotate<=1;O_image_us<=0;O_epoch<=0;O_time_valid<=0;end
 else begin
 vs_last<=I_vs;O_commit<=0;
 if(I_vs && !vs_last)begin
 in_blank<=1;O_show<=I_show;if(age<255)age<=age+1'b1;
 if(I_tracking && session!=I_session)begin O_cx<=640;O_cy<=360;end
 end
 if(I_de)in_blank<=0;
 if(session!=I_session || O_pair!=I_pair || O_meta[244]!=I_tracking)associated<=0;
 if(I_snapshot && in_blank && !I_de)begin
 in_blank<=0;O_commit<=1;O_bank<=I_data[MW+32+:2];O_frame_id<=I_data[MW+:32];
 if(V4)begin O_image_us<=I_data[803+:32];O_epoch<=I_data[835+:16];O_time_valid<=I_data[851] && I_data[802];end
 O_zoom<=I_zoom;O_mode<=I_mode;O_rotate<=I_rotate;O_pair<=I_pair;O_show<=I_show;session<=I_session;associated<=match;
 O_meta<=match?I_data[MW-1:0]:0;if(I_data[MW+:32]!=O_frame_id)age<=0;
 O_cx<=cx;O_cy<=cy;O_x0<=cx-hx;O_y0<=cy-hy;
 if(match && I_data[567:565]!=0)begin
 O_cx<=640;O_cy<=360;O_x0<=0;O_y0<=48;O_zoom<=0;O_mode<=0;
 end
 end end end
endmodule
`default_nettype wire
