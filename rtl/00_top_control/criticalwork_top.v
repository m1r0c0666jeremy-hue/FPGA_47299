// Adapted from the supplied SC500 Lab1 design_top_wrapper.v.
// Vendor modules retain their original notices under user_source/.
// This wrapper preserves the reference datapath, packing, clocks and reset policy.
// Pin compatibility and physical camera/display operation remain unverified.
`default_nettype none
module criticalwork_top #(parameter integer DEBUG_MODE = 0) (
    input wire        I_sys_clk,
    input wire        I_rst_n,
      
    output wire       O_cam_scl,
    inout  wire       IO_cam_sda,
    output wire       O_cam_24m,
    output wire       O_cam_rst,
      
    inout wire [1:0]  I_button,

    output wire       O_screen_pwm,
    output wire       O_tmds_ch0_p,
    output wire       O_tmds_ch1_p,
    output wire       O_tmds_ch2_p,
    output wire       O_tmds_clk_p,

    inout wire        IO_rx_clk_pad_n, 
    inout wire        IO_rx_clk_pad_p, 
    inout wire[3:0]   IO_rx_data_pad_n,
    inout wire[3:0]   IO_rx_data_pad_p,

    output wire[12:0] ddr_addr,
    output wire[ 1:0] ddr_ba,
    output wire[ 0:0] ddr_cke,
    output wire[ 0:0] ddr_odt,
    output wire[ 0:0] ddr_cs_n,
    output wire       ddr_ras_n,
    output wire       ddr_cas_n,
    output wire       ddr_we_n,
    output wire[ 0:0] ddr_ck_p,
    output wire[ 0:0] ddr_ck_n,
    inout wire[1:0]   ddr_dm,
    inout wire[15:0]  ddr_dq,
    inout wire[1:0]   ddr_dqs_p,
    inout wire[1:0]   ddr_dqs_n   
);
wire        	S_100m_clk;
wire        	S_24m_clk;
wire [127:0]	S_ISP_O_tdata ;
wire 			S_ISP_O_tuser ;
wire 			S_ISP_O_tvalid;
wire        	S_csi_rx_clk;
wire[3:0]   S_hdmi_debug_status;
wire        S_hdmi_pixel_clk;
wire        S_hdmi_serial_clk;
wire        	S_pll_lock;
wire        	S_rst_n;
wire [3:0] camera_status_async;
PLL u_PLL(
        .refclk      ( I_sys_clk         ),
        .reset    	 ( ~I_rst_n          ),
        
        .clk0_out    ( S_100m_clk        ),
        .clk1_out    ( S_24m_clk         ),

        .clk4_out    ( S_hdmi_pixel_clk  ),
        .clk5_out    ( S_hdmi_serial_clk ),

        .lock        ( S_pll_lock        )

    );

assign O_screen_pwm = 1'b1; // Original reference output; pin compatibility pending.
assign S_rst_n = S_pll_lock;
camera_capture u_camera (
    .I_control_clk(S_100m_clk), .I_camera_ref_clk(S_24m_clk),
    .I_rst_n(S_rst_n), .I_button(I_button),
    .O_cam_scl(O_cam_scl), .IO_cam_sda(IO_cam_sda),
    .O_cam_24m(O_cam_24m), .O_cam_rst(O_cam_rst),
    .IO_rx_clk_pad_n(IO_rx_clk_pad_n), .IO_rx_clk_pad_p(IO_rx_clk_pad_p),
    .IO_rx_data_pad_n(IO_rx_data_pad_n), .IO_rx_data_pad_p(IO_rx_data_pad_p),
    .O_capture_clk(S_csi_rx_clk), .O_rgb128(S_ISP_O_tdata),
    .O_data_valid(S_ISP_O_tvalid), .O_frame_start(S_ISP_O_tuser),
    .O_status_async(camera_status_async)
);
// These four independent sticky flags are not a coherent multi-bit data bus.
status_sync u_status_sync (
    .I_clk(S_hdmi_pixel_clk), .I_rst_n(S_rst_n),
    .I_status_async(camera_status_async), .O_status(S_hdmi_debug_status)
);
memory_video_out #(.DEBUG_MODE(DEBUG_MODE)) u_video (
    .I_sys_clk(I_sys_clk), .I_rst_n(S_rst_n),
    .I_pixel_clk(S_hdmi_pixel_clk), .I_serial_clk(S_hdmi_serial_clk),
    .I_capture_clk(S_csi_rx_clk), .I_rgb128(S_ISP_O_tdata),
    .I_data_valid(S_ISP_O_tvalid), .I_frame_start(S_ISP_O_tuser),
    .I_debug_status(S_hdmi_debug_status),
    .O_tmds_ch0_p(O_tmds_ch0_p), .O_tmds_ch1_p(O_tmds_ch1_p),
    .O_tmds_ch2_p(O_tmds_ch2_p), .O_tmds_clk_p(O_tmds_clk_p),
    .ddr_addr(ddr_addr),
    .ddr_ba(ddr_ba),
    .ddr_cke(ddr_cke),
    .ddr_odt(ddr_odt),
    .ddr_cs_n(ddr_cs_n),
    .ddr_ras_n(ddr_ras_n),
    .ddr_cas_n(ddr_cas_n),
    .ddr_we_n(ddr_we_n),
    .ddr_ck_p(ddr_ck_p),
    .ddr_ck_n(ddr_ck_n),
    .ddr_dm(ddr_dm),
    .ddr_dq(ddr_dq),
    .ddr_dqs_p(ddr_dqs_p),
    .ddr_dqs_n(ddr_dqs_n)
);

endmodule
`default_nettype wire
