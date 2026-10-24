// Adapted from the supplied SC500 Lab1 design_top_wrapper.v.
// Vendor modules retain their original notices under user_source/.
// This wrapper preserves the reference datapath, packing, clocks and reset policy.
// Pin compatibility and physical camera/display operation remain unverified.
`default_nettype none
module camera_capture (
    input wire I_control_clk, input wire I_camera_ref_clk,
    input wire I_rst_n, input wire I_gain_req, I_gain_up, output wire O_gain_ack,
    output wire O_cam_scl, inout wire IO_cam_sda,
    output wire O_cam_24m, output wire O_cam_rst,
    inout wire IO_rx_clk_pad_n, inout wire IO_rx_clk_pad_p,
    inout wire [3:0] IO_rx_data_pad_n, inout wire [3:0] IO_rx_data_pad_p,
    output wire [95:0] O_detect_rgb,
    output wire O_detect_sof,O_detect_valid,
    output wire O_capture_clk, output wire [127:0] O_rgb128,
    output wire O_data_valid, output wire O_frame_start,
    output wire [3:0] O_status_async
);
wire        	S_100m_clk;
wire        	S_24m_clk;
wire [127:0]	S_ISP_O_tdata ;
wire 			S_ISP_O_tlast ;
wire			S_ISP_O_tready;
wire 			S_ISP_O_tuser ;
wire 			S_ISP_O_tvalid;
wire [15:0] 	S_ae;
wire 			S_ae_cfg_done;
wire 			S_ae_req;
wire [15:0] 	S_ag;
wire [39:0]		S_axis_tdata;
wire 			S_axis_tlast;
wire 			S_axis_tuser;
wire 			S_axis_tvalid;
wire 			S_cam_cfg_done;
wire[31:0]  	S_csi_data;
wire        	S_csi_frame_end;
wire        	S_csi_frame_start;
wire        	S_csi_rx_clk;
wire        	S_csi_valid;
wire[15:0]  	S_hs_rx_data;
wire        	S_hs_rx_valid;
wire[1:0]   	S_lane_error;
wire [39:0] 	S_raw10_data;
wire        	S_raw10_frame_end;
wire        	S_raw10_frame_start;
wire        	S_raw10_valid;
wire [39:0]		S_raw_tdata ;
wire			S_raw_tlast ;
wire 			S_raw_tuser ;
wire 			S_raw_tvalid;
wire        	S_rst_n;

assign S_100m_clk = I_control_clk;
assign S_24m_clk = I_camera_ref_clk;
assign S_rst_n = I_rst_n;
assign O_cam_rst = 1'b1;
assign O_cam_24m = S_24m_clk;
assign O_capture_clk = S_csi_rx_clk;
assign O_rgb128 = S_ISP_O_tdata;
assign O_data_valid = S_ISP_O_tvalid;
assign O_frame_start = S_ISP_O_tuser;
camera_status u_status (
    .I_cfg_clk(S_24m_clk), .I_rx_clk(S_csi_rx_clk), .I_rst_n(S_rst_n),
    .I_cfg_done(S_cam_cfg_done), .I_hs_valid(S_hs_rx_valid),
    .I_csi_valid(S_csi_valid), .I_frame_start(S_csi_frame_start),
    .O_status_async(O_status_async)
);
camera_gain_control u_gain_control (
    .I_clk(S_24m_clk), .I_rst_n(S_rst_n), .I_req(I_gain_req), .I_up(I_gain_up),
    .I_cam_done(S_cam_cfg_done), .I_ae_done(S_ae_cfg_done),
    .O_ack(O_gain_ack), .O_ae_req(S_ae_req), .O_ae(S_ae), .O_ag(S_ag)
);
    uicfgcs500_720p #(
      .CLK_DIV(24000000 / 100000 - 1)
  ) u_uicfgcs500 (
      .I_clk(S_24m_clk),  
      .I_rst_n(S_rst_n),  
      .I_ae_req(S_ae_req),
      .I_ae(S_ae),
      .I_ag(S_ag),
      .O_cam_scl(O_cam_scl),  
      .IO_cam_sda(IO_cam_sda),  
      .O_cfg_done(S_cam_cfg_done),  
      .O_ae_cfg_done(S_ae_cfg_done)  
  );
	
    mipi_dphy_rx_ph1p_mipiio_wrapper#(
        .DPHY_RX_LOCATION      ( "DPHY0" ),
        .HS_EQUALIZER          ( "0dB"   ),
        .HS_VGA_GAIN           ( "8dB" ),
        .LANE_NUM              ( 2       ),
        .BYTE_NUM              ( 1       )
    )u_mipi_dphy_rx_ph1p_mipiio_wrapper(
        .I_lp_clk              ( S_100m_clk       ),
        .I_rst                 ( ~S_rst_n         ),

        .I_clk_lane_in_delay   ( 6'd0             ),
        .I_data_lane0_in_delay ( 6'd0             ),
        .I_data_lane1_in_delay ( 6'd0             ),
        .I_data_lane2_in_delay ( 6'd0             ),
        .I_data_lane3_in_delay ( 6'd0             ),

        .I_lane_invert         ( 4'b0000          ),
     
        .O_hs_rx_clk           ( S_csi_rx_clk     ),
        .O_hs_rx_valid         ( S_hs_rx_valid    ),
        .O_hs_rx_data          ( S_hs_rx_data     ),
      
        .O_lp_rx_lane0_p       (  ),
        .O_lp_rx_lane0_n       (  ),
      
        .I_lp_tx_en            ( 1'b0             ),
        .I_lp_tx_lane0_p       ( 1'b1             ),
        .I_lp_tx_lane0_n       ( 1'b1             ),
      
        .O_lane_match_error    (                  ),
        .O_lane_error          ( S_lane_error     ),
      
        .IO_rx_clk_pad_n       ( IO_rx_clk_pad_n  ),
        .IO_rx_clk_pad_p       ( IO_rx_clk_pad_p  ),
        .IO_rx_data_pad_n      ( IO_rx_data_pad_n ),
        .IO_rx_data_pad_p      ( IO_rx_data_pad_p )
    );

csi_unpacket_2lane u_csi_unpacket(
.I_clk                 ( S_csi_rx_clk       ),
.I_rst_n               ( S_rst_n        	),
.I_hs_valid            ( S_hs_rx_valid     ),
.I_hs_data             ( S_hs_rx_data      ),

.O_csi_frame_start     ( S_csi_frame_start ),
.O_csi_frame_end       ( S_csi_frame_end   ),
.O_csi_valid           ( S_csi_valid       ),
.O_csi_data            ( S_csi_data        )
);

raw10_unpacket_2lane u_raw10_unpacket (
.I_clk  (S_csi_rx_clk),
.I_rst_n(S_rst_n),

.I_csi_frame_start(S_csi_frame_start),
.I_csi_frame_end  (S_csi_frame_end),
.I_csi_valid      (S_csi_valid),
.I_csi_data       (S_csi_data),

.O_raw10_frame_start(S_raw10_frame_start),
.O_raw10_frame_end  (S_raw10_frame_end),
.O_raw10_valid      (S_raw10_valid),
.O_raw10_data       (S_raw10_data)
  );

uial2axis #(
.IMG_WIDTH(1280),
.IMG_HEIGHT(720),
.INPUT_DATA_WIDTH(40)
) 
u_uial2axis (
.I_native_clk(S_csi_rx_clk),
.I_rst_n     (S_rst_n),
.I_data      (S_raw10_data       ),
.I_data_valid(S_raw10_valid      ),
.I_data_start(S_raw10_frame_start),
.I_data_end  (S_raw10_frame_end  ),
.axis_tvalid (S_axis_tvalid),
.axis_tdata  (S_axis_tdata ),
.axis_tuser  (S_axis_tuser ),
.axis_tlast  (S_axis_tlast )
);

assign S_raw_tdata  = S_axis_tdata;
assign S_raw_tvalid = S_axis_tvalid;
assign S_raw_tlast  = S_axis_tlast;
assign S_raw_tuser  = S_axis_tuser;

isp_top u_isp_top (
.O_detect_rgb(O_detect_rgb),.O_detect_sof(O_detect_sof),.O_detect_valid(O_detect_valid),
.axi4s_video_aclk(S_csi_rx_clk),
.I_rst_n         (S_rst_n),
.I_tlast         (S_raw_tlast	),
.I_tuser         (S_raw_tuser	),
.I_tdata         (S_raw_tdata	),
.I_tvalid        (S_raw_tvalid	),
.I_tdest         (),
.O_tready        (S_ISP_O_tready),
.O_tdata         (S_ISP_O_tdata ),
.O_tlast         (S_ISP_O_tlast ),
.O_tuser         (S_ISP_O_tuser ),
.O_tvalid        (S_ISP_O_tvalid),
.I_tready        ()
  );

endmodule
`default_nettype wire
