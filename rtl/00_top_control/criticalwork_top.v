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
      
    input wire [2:0]  I_button,          // 2026-10-04: was inout (bidirectional pad); board keys are pure inputs
    input wire [1:0]  I_switch,          // [1]=SW1(A4), [0]=SW2(B4); measured up=0
    input wire [1:0]  I_ui_switch,       // [1]=SW3(E11), [0]=SW4(D11)

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
wire [1:0] image_mode_pending;
reg [1:0] process_reset_bridge;
wire process_rst_n = process_reset_bridge[1];
// Only the new pixel-domain modules use this local reset release bridge.
always @(posedge S_hdmi_pixel_clk or negedge S_rst_n) begin
    if (!S_rst_n) process_reset_bridge <= 2'b00;
    else process_reset_bridge <= {process_reset_bridge[0],1'b1};
end
switch_mode_control u_switch_mode (
    .I_clk(S_hdmi_pixel_clk), .I_rst_n(process_rst_n),
    .I_switch(I_switch), .O_mode_pending(image_mode_pending)
);
wire [1:0] ui_zoom;
wire ui_tracking,ui_show,ui_conflict;
wire [7:0] ui_session;
wire [95:0] detect_rgb;
wire detect_sof,detect_valid;
wire gain_req, gain_up, gain_ack;
target_controls u_controls (
    .I_clk(S_hdmi_pixel_clk), .I_rst_n(process_rst_n),
    .I_keys_n(I_button), .I_ui_switch(I_ui_switch), .I_gain_ack(gain_ack),
    .O_gain_req(gain_req), .O_gain_up(gain_up), .O_zoom(ui_zoom),
    .O_tracking(ui_tracking),.O_show(ui_show),.O_session(ui_session),.O_conflict(ui_conflict)
);
PLL u_PLL(
        .refclk      ( I_sys_clk         ),
        .reset    	 ( ~I_rst_n          ),
        
        .clk0_out    ( S_100m_clk        ),
        .clk1_out    ( S_24m_clk         ),

        .clk4_out    ( S_hdmi_pixel_clk  ),
        .clk5_out    ( S_hdmi_serial_clk ),

        .lock        ( S_pll_lock        )

    );

// ---------------------------------------------------------------------------
// 2026-10-04 工程自有修改（见 docs/来源与修改记录.md、reports/验证报告.md 待办项）
//   1) PLL 锁定后同步释放的复位，替代直接把 S_pll_lock 当全局复位；
//   2) O_screen_pwm 改为心跳输出（引脚已从以太网 RGMII_TXD0 改到板载 LED1 = D10）。
// 其余端口与实例连接仍与厂家基线逐字一致，audit_project.py 继续核对。
// ---------------------------------------------------------------------------
// 2026-10-04 decision: a single global "synchronised release" reset was tried here and
// re-verified by a full re-build: Setup WNS went from +1.294ns to -1.418ns (TNS -7.029ns),
// because the reset net then launches from one 100MHz flop into every clock domain and is
// timed as ordinary logic.  Reverted to the vendor policy (asynchronous reset = PLL lock);
// per-domain reset bridges are a separate, properly scoped follow-up.
assign S_rst_n = S_pll_lock;

reg [25:0] S_heart_cnt;
always @(posedge S_100m_clk or negedge S_rst_n) begin
    if(!S_rst_n)
        S_heart_cnt <= 26'd0;
    else
        S_heart_cnt <= S_heart_cnt + 26'd1;
end

assign O_screen_pwm = S_heart_cnt[25];   // 100 MHz / 2^26 ~= 0.75 s toggle
camera_capture u_camera (
    .I_control_clk(S_100m_clk), .I_camera_ref_clk(S_24m_clk),
    .I_rst_n(S_rst_n), .I_gain_req(gain_req), .I_gain_up(gain_up), .O_gain_ack(gain_ack),
    .O_cam_scl(O_cam_scl), .IO_cam_sda(IO_cam_sda),
    .O_cam_24m(O_cam_24m), .O_cam_rst(O_cam_rst),
    .IO_rx_clk_pad_n(IO_rx_clk_pad_n), .IO_rx_clk_pad_p(IO_rx_clk_pad_p),
    .IO_rx_data_pad_n(IO_rx_data_pad_n), .IO_rx_data_pad_p(IO_rx_data_pad_p),
    .O_detect_rgb(detect_rgb),.O_detect_sof(detect_sof),.O_detect_valid(detect_valid),
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
    .I_process_rst_n(process_rst_n), .I_process_mode(image_mode_pending),
    .I_zoom(ui_zoom),.I_tracking(ui_tracking),.I_show(ui_show),.I_session(ui_session),.I_conflict(ui_conflict),
    .I_detect_rgb(detect_rgb),.I_detect_sof(detect_sof),.I_detect_valid(detect_valid),
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
