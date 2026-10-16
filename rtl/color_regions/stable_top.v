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
wire [2:0] ui_zoom;
wire ui_tracking,ui_show,ui_conflict,ui_pair;
wire [7:0] ui_session;
wire [95:0] detect_rgb;
wire detect_sof,detect_valid;
wire ui_rotate;wire [1:0] ui_diag;wire gain_req, gain_up, gain_ack;
wire cal_enter,cal_sample,cal_cancel;wire [7:0] cal_status,ui_cal_status,capture_cal_status;
wire [95:0] raw_rgb;wire raw_sof,raw_valid;wire [11:0] wb_r,wb_b;
wire [127:0] color_models;wire [15:0] color_revision;wire [23:0] frame_gains;wire cal_active,needs_cal,frame_pair;
wire [1:0] frame_model_state;wire [41:0] frame_quality;
wire camera_parameter_event,camera_ready;wire [3:0] camera_fault,camera_phase;wire [1:0] camera_retries;wire [6:0] camera_gain;
(* async_reg="true" *) reg [1:0] camera_event_sync;
(* async_reg="true" *) reg [1:0] camera_ready_sync;reg camera_event_previous;
wire camera_pause=camera_event_sync[1]!=camera_event_previous;
always @(posedge S_hdmi_pixel_clk or negedge process_rst_n)begin
 if(!process_rst_n)begin camera_event_sync<=0;camera_event_previous<=0;camera_ready_sync<=0;end
 else begin camera_event_sync<={camera_event_sync[0],camera_parameter_event};camera_event_previous<=camera_event_sync[1];camera_ready_sync<={camera_ready_sync[0],camera_ready};end
end
(* async_reg="true" *) reg [1:0] cal_reset_bridge;
wire cal_rst_n=cal_reset_bridge[1];
always @(posedge S_csi_rx_clk or negedge S_rst_n)if(!S_rst_n)cal_reset_bridge<=0;else cal_reset_bridge<={cal_reset_bridge[0],1'b1};
wire event_ready,event_valid;wire [4:0] event_data;reg [4:0] event_sent,event_previous;
wire [4:0] event_now={ui_pair,camera_event_sync[1],cal_cancel,cal_sample,cal_enter};
wire event_send=event_ready && event_now!=event_sent;
always @(posedge S_hdmi_pixel_clk or negedge process_rst_n)if(!process_rst_n)event_sent<=0;else if(event_send)event_sent<=event_now;
always @(posedge S_csi_rx_clk or negedge cal_rst_n)if(!cal_rst_n)event_previous<=0;else if(event_valid)event_previous<=event_data;
target_mailbox #(.WIDTH(5)) cal_events(.S_clk(S_hdmi_pixel_clk),.S_rst_n(process_rst_n),.S_send(event_send),.S_data(event_now),.S_ready(event_ready),
.D_clk(S_csi_rx_clk),.D_rst_n(cal_rst_n),.D_valid(event_valid),.D_data(event_data));
stable_calibration calibration(.clk(S_csi_rx_clk),.rst_n(cal_rst_n),.sof(raw_sof),.valid(raw_valid),.rgb(raw_rgb),.pair(event_valid?event_data[4]:event_previous[4]),
.enter(event_valid && event_data[0]!=event_previous[0]),.sample(event_valid && event_data[1]!=event_previous[1]),
.cancel(event_valid && event_data[2]!=event_previous[2]),.gain_changed(event_valid && event_data[3]!=event_previous[3]),
.gain_r(wb_r),.gain_b(wb_b),.models(color_models),.revision(color_revision),.cal_active(cal_active),.needs_cal(needs_cal),.status(cal_status),.frame_pair(frame_pair),.frame_gains(frame_gains),.frame_status(capture_cal_status),
.frame_model_state(frame_model_state),.frame_quality(frame_quality));
wire status_ready;reg [7:0] status_sent;wire status_send=status_ready && cal_status!=status_sent;
always @(posedge S_csi_rx_clk or negedge cal_rst_n)if(!cal_rst_n)status_sent<=0;else if(status_send)status_sent<=cal_status;
target_mailbox #(.WIDTH(8)) cal_feedback(.S_clk(S_csi_rx_clk),.S_rst_n(cal_rst_n),.S_send(status_send),.S_data(cal_status),.S_ready(status_ready),
.D_clk(S_hdmi_pixel_clk),.D_rst_n(process_rst_n),.D_valid(),.D_data(ui_cal_status));
stable_controls #(.LONG_PRESS_MS(1000)) u_controls (
    .I_pause(camera_pause),
    .I_clk(S_hdmi_pixel_clk), .I_rst_n(process_rst_n),
    .I_keys_n(I_button), .I_ui_switch(I_ui_switch), .I_gain_ack(gain_ack),.I_cal_status(ui_cal_status),
    .O_rotate(ui_rotate),.O_diag(ui_diag),.O_cal_enter(cal_enter),.O_cal_sample(cal_sample),.O_cal_cancel(cal_cancel),
    .O_gain_req(gain_req), .O_gain_up(gain_up), .O_zoom(ui_zoom),
    .O_pair(ui_pair),.O_tracking(ui_tracking),.O_show(ui_show),.O_session(ui_session),.O_conflict(ui_conflict)
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
stable_camera_capture u_camera (
    .O_parameter_event(camera_parameter_event),.O_camera_ready(camera_ready),.O_camera_fault(camera_fault),
    .O_camera_retries(camera_retries),.O_camera_phase(camera_phase),.O_camera_gain(camera_gain),
    .I_gain_r(wb_r),.I_gain_b(wb_b),.O_raw_rgb(raw_rgb),.O_raw_sof(raw_sof),.O_raw_valid(raw_valid),
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
stable_memory_video_out #(.DEBUG_MODE(DEBUG_MODE)) u_video (
    .I_sys_clk(I_sys_clk), .I_rst_n(S_rst_n),
    .I_process_rst_n(process_rst_n), .I_process_mode(image_mode_pending),
    .I_pair(ui_pair),.I_zoom(ui_zoom),.I_tracking(ui_tracking && camera_ready_sync[1]),.I_show(ui_show),.I_session(ui_session),.I_conflict(ui_conflict),
    .I_detect_rgb(detect_rgb),.I_detect_sof(detect_sof),.I_detect_valid(detect_valid),
    .I_rotate(ui_rotate),.I_diag(ui_diag),.I_models(color_models),.I_revision(color_revision),.I_gains(frame_gains),.I_cal_status(capture_cal_status),.I_cal_active(capture_cal_status[7:5]!=0),.I_needs_cal(needs_cal),.I_frame_pair(frame_pair),
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
