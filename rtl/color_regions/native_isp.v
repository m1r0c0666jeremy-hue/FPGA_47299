// A single full-resolution demosaic and AWB path. Calibration and detection
// receive independently averaged pre/post-AWB views of the same cropped frame.
`default_nettype none
module native_isp #(parameter CROP_X=16,CROP_Y=252)(
 input wire clk,rst_n,abort_frame,sof,last,valid,input wire [39:0] data,
 input wire [32:0] frame_tag,input wire [11:0] gain_r,gain_b,
 output wire raw_sof,raw_valid,output wire [95:0] raw_rgb,
 output wire detect_sof,detect_valid,output wire [95:0] detect_rgb,
 output wire [32:0] raw_tag,detect_tag,
 output wire rgb_sof,rgb_valid,output wire [127:0] rgb128,
 output wire full_sof,full_valid,output wire [32:0] full_tag);
 wire ds,last_rgb;wire [127:0] demosaic;wire [95:0] raw_full;
 native_demosaic #(.IMG_WIDTH(2592),.IMG_HEIGHT(1944),.data_complete_delay(50),.BAYER_MODE("BGGR"))
 demosaic_core(.I_clk(clk),.I_rst_n(rst_n),.I_frame_tag(frame_tag),.O_frame_tag(full_tag),
  .axi4s_video_tdata(data),.axi4s_video_tdest(10'd0),.axi4s_video_tlast(last),
  .axi4s_video_tvalid(valid),.axi4s_video_tuser(sof),.axi4s_video_tready(),
  .O_tlast(last_rgb),.O_tuser(full_sof),.O_tdata(demosaic),.O_tvalid(full_valid),.O_tready(1'b1));
 data128_96 unpack_rgb(demosaic,raw_full);
 wire crop_sof,crop_valid,crop_last;wire [95:0] crop_rgb;wire [32:0] crop_tag;
 native_rgb_crop #(.CROP_X(CROP_X),.CROP_Y(CROP_Y)) crop(
  clk,rst_n,abort_frame,full_sof,full_valid,raw_full,full_tag,
  crop_sof,crop_valid,crop_last,crop_rgb,crop_tag);
 wire ignored_raw_sof;wire [32:0] low_raw_tag;
 native_downsample2 before_awb(clk,rst_n,abort_frame,crop_sof,crop_valid,crop_rgb,crop_tag,
  ignored_raw_sof,raw_valid,raw_rgb,low_raw_tag);
 // Freeze calibration at the SAME cropped SOF which freezes the AWB gains.
 assign raw_sof=crop_sof;assign raw_tag=crop_tag;
 wire wb_sof,wb_valid,wb_last;wire [95:0] wb_rgb;reg [32:0] wb_tag0,wb_tag1;
 always @(posedge clk or negedge rst_n)
 if(!rst_n)begin wb_tag0<=0;wb_tag1<=0;end
 else begin wb_tag0<=crop_tag;wb_tag1<=wb_tag0;end
 stable_awb wb(clk,rst_n,crop_last,crop_sof,crop_valid,crop_rgb,gain_r,gain_b,
  wb_last,wb_sof,wb_valid,wb_rgb);
 native_downsample2 after_awb(clk,rst_n,abort_frame,wb_sof,wb_valid,wb_rgb,wb_tag1,
  detect_sof,detect_valid,detect_rgb,detect_tag);
 stable_packer pack(clk,rst_n,wb_sof,wb_valid,wb_rgb,rgb_sof,rgb_valid,rgb128);
endmodule
`default_nettype wire
