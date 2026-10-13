// Pixel-domain immutable image/metadata/viewport transaction in vertical blank.
`default_nettype none
module regions_display #(parameter STALE_DISPLAY_FRAMES=15)(
 input wire I_clk,I_rst_n,I_vs,I_de,I_snapshot,input wire [450:0] I_data,
 input wire I_tracking,I_show,I_conflict,I_live,input wire [7:0] I_session,
 input wire [1:0] I_zoom,I_mode,input wire I_pair,
 output reg O_commit,output reg [1:0] O_bank,output reg [31:0] O_frame_id,
 output reg [10:0] O_cx,O_x0,output reg [9:0] O_cy,O_y0,
 output reg [1:0] O_zoom,O_mode,output reg [415:0] O_meta,
 output reg O_show,O_pair,output wire O_detection_valid,output wire O_sample_valid,output wire [2:0] O_state
);
 reg vs_last,in_blank,associated;reg [7:0] age,session;
 wire match=I_data[450] && I_data[255] && I_data[415:413]==1 && I_data[31:0]==I_data[447:416] &&
       I_data[242:235]==I_session && I_data[243]==I_pair && I_data[244]==I_tracking;
 assign O_detection_valid=associated && I_tracking && I_live && session==I_session && O_pair==I_pair && age<STALE_DISPLAY_FRAMES && O_meta[247];
 assign O_sample_valid=associated && I_live && session==I_session && O_pair==I_pair && age<STALE_DISPLAY_FRAMES && O_meta[247] && O_meta[408];
 wire any_box=O_meta[245] || O_meta[246] || O_meta[318] || O_meta[382];
 wire multiple=O_meta[319] || O_meta[383] || (O_meta[245] && O_meta[318]) || (O_meta[246] && O_meta[382]);
 assign O_state=I_conflict?3'd5:!I_live?3'd6:age>=STALE_DISPLAY_FRAMES?3'd7:!I_tracking?3'd0:
       !O_detection_valid?3'd1:(O_meta[232:231]==2 || O_meta[234:233]==2)?3'd4:multiple?3'd3:any_box?3'd2:3'd1;
 always @(posedge I_clk or negedge I_rst_n)begin
  if(!I_rst_n)begin
   vs_last<=0;in_blank<=0;associated<=0;age<=0;session<=0;O_commit<=0;O_bank<=0;O_frame_id<=0;
   O_cx<=640;O_cy<=360;O_x0<=0;O_y0<=48;O_zoom<=0;O_mode<=0;O_meta<=0;O_show<=1;O_pair<=0;
  end else begin
   vs_last<=I_vs;O_commit<=0;
   if(I_vs && !vs_last)begin in_blank<=1;O_show<=I_show;if(age<255)age<=age+1'b1;end
   if(I_de)in_blank<=0;
   if(session!=I_session || O_pair!=I_pair || O_meta[244]!=I_tracking)associated<=0;
   if(I_snapshot && in_blank && !I_de)begin
    in_blank<=0;O_commit<=1;O_bank<=I_data[449:448];O_frame_id<=I_data[447:416];
    O_zoom<=I_zoom;O_mode<=I_mode;O_pair<=I_pair;O_show<=I_show;session<=I_session;associated<=match;
    O_meta<=match?I_data[415:0]:416'd0;
    if(I_data[447:416]!=O_frame_id)age<=0;
    case(I_zoom)
      0:begin O_x0<=0;O_y0<=48;end
      1:begin O_x0<=320;O_y0<=204;end
      default:begin O_x0<=480;O_y0<=282;end
    endcase
   end
  end
 end
endmodule
`default_nettype wire
