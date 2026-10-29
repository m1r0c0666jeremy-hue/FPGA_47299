// Four-pixel RGB crop. Coordinates are in the full unrotated sensor frame.
`default_nettype none
module native_rgb_crop #(
 parameter FULL_WIDTH=2592,FULL_HEIGHT=1944,CROP_X=16,CROP_Y=252,
 parameter CROP_WIDTH=2560,CROP_HEIGHT=1440
)(input wire clk,rst_n,abort_frame,sof,valid,
 input wire [95:0] rgb,input wire [32:0] frame_tag,
 output reg out_sof,out_valid,out_last,output reg [95:0] out_rgb,
 output reg [32:0] out_tag);
 reg [11:0] x;reg [10:0] y;reg active;
 localparam PHASE=CROP_X%4;
 reg [95:0] previous_rgb;
 wire [11:0] px=sof?12'd0:x;
 wire [10:0] py=sof?11'd0:y;
 wire [11:0] sample_x=PHASE==0?px:px-12'd4+PHASE;
 wire [191:0] shifted={previous_rgb,rgb} << (PHASE*24);
 wire [95:0] aligned_rgb=PHASE==0?rgb:shifted[191:96];
 wire roi_inside=sample_x>=CROP_X && sample_x<CROP_X+CROP_WIDTH &&
             py>=CROP_Y && py<CROP_Y+CROP_HEIGHT;
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin x<=0;y<=0;active<=0;previous_rgb<=0;out_sof<=0;out_valid<=0;out_last<=0;out_rgb<=0;out_tag<=0;end
 else begin
  out_sof<=0;out_valid<=0;out_last<=0;
  if(sof)begin x<=0;y<=0;active<=1;end
  if(valid && (active || sof))begin
   previous_rgb<=rgb;
   if(px==FULL_WIDTH-4)begin x<=0;y<=py+1'b1;if(py==FULL_HEIGHT-1)active<=0;end
   else x<=px+12'd4;
   if(roi_inside)begin
    out_valid<=1;out_rgb<=aligned_rgb;out_tag<=frame_tag;
    out_sof<=sample_x==CROP_X && py==CROP_Y;
    out_last<=sample_x==CROP_X+CROP_WIDTH-4;
   end
  end
  if(abort_frame)begin active<=0;out_sof<=0;out_valid<=0;out_last<=0;end
 end end
endmodule
`default_nettype wire
