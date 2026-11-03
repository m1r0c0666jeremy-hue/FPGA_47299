// Adapted from the supplied SC500 Lab1 design_top_wrapper.v.
// Vendor modules retain their original notices under user_source/.
// This wrapper preserves the reference datapath, packing, clocks and reset policy.
// Pin compatibility and physical camera/display operation remain unverified.
`default_nettype none
module stage1_memory_video_out #(parameter integer DEBUG_MODE = 0) (
    input wire [7:0] I_k_value,input wire I_k_adjust,input wire [1:0] I_ui_mode,input wire I_key_down2,I_key2,I_key3,I_key4,I_key_cancel,
    input wire I_gain_busy,I_gain_failed,input wire [2:0] I_gain_slot,input wire [6:0] I_gain_target,output wire O_area_alarm,
    input wire [31:0] I_source_id,I_source_us,I_capture_us,I_board_us,I_latest_gray,
    input wire I_source_time_valid,input wire [1:0] I_model_state,input wire [41:0] I_quality,
    input wire I_camera_event,I_camera_ready,input wire [17:0] I_camera_status,
    input wire I_sys_clk, input wire I_rst_n,
    input wire I_process_rst_n, input wire [1:0] I_process_mode,
    input wire [2:0] I_zoom,
    input wire I_rotate,input wire [1:0] I_diag,
    input wire I_pair,I_tracking,I_show,I_conflict,input wire [7:0] I_session,
    input wire [95:0] I_detect_rgb,input wire I_detect_sof,I_detect_valid,
    input wire [127:0] I_models,input wire [15:0] I_revision,input wire [23:0] I_gains,
    input wire [7:0] I_cal_status,input wire I_cal_active,I_needs_cal,I_frame_pair,
    input wire I_pixel_clk, input wire I_serial_clk,
    input wire I_capture_clk, input wire [127:0] I_rgb128,
    input wire I_data_valid, input wire I_frame_start,
    input wire [3:0] I_debug_status,
    output wire O_tmds_ch0_p, output wire O_tmds_ch1_p,
    output wire O_tmds_ch2_p, output wire O_tmds_clk_p,
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
wire [127:0]	S_ISP_O_tdata ;
wire 			S_ISP_O_tuser ;
wire 			S_ISP_O_tvalid;
wire        	S_csi_rx_clk;
wire        S_ddr_clk;
wire[24:0]  S_ddr_user_addr;
wire[127:0] S_ddr_user_rd_data;
wire        S_ddr_user_rd_en;
wire        S_ddr_user_rd_valid;
wire        S_ddr_user_ready;
wire[127:0] S_ddr_user_wr_data;
wire        S_ddr_user_wr_en;
wire S_init_calib_complete;wire [1:0] source_mask;
wire committed_write;wire [24:0] committed_address;wire [9:0] outstanding_reads;wire unexpected_return;
wire [31:0] accepted_reads;
wire controller_reset_n,stream_async_n,stream_pixel_n,read_fault_toggle,recovery_failed;
wire [15:0] stream_epoch,recovery_count;wire [1:0] recovery_retries;wire [3:0] recovery_reason;
wire [127:0] ddr_diagnostics,pixel_diagnostics;
refined_ddr_recovery #(.CYCLES_PER_MS(50000)) recover_ddr(.clk(I_sys_clk),.rst_n(I_rst_n),.init_ready(S_init_calib_complete),.fault_toggle(read_fault_toggle),
 .controller_n(controller_reset_n),.pipeline_n(stream_async_n),.epoch(stream_epoch),.recoveries(recovery_count),.retries(recovery_retries),.reason(recovery_reason),.failed(recovery_failed));
refined_reset_bridge pixel_stream_reset(I_pixel_clk,stream_async_n,stream_pixel_n);
wire        S_hdmi_de;
wire[3:0]   S_hdmi_debug_status;
wire        S_hdmi_hsync;
wire        S_hdmi_last;
wire[23:0]  S_hdmi_out_data;
wire        S_hdmi_out_de;
wire        S_hdmi_out_hsync;
wire        S_hdmi_out_vsync;
wire        S_hdmi_pixel_clk;
wire        S_hdmi_rst_n;
wire        S_hdmi_serial_clk;
wire        S_hdmi_user;
wire        S_hdmi_vsync;
wire        S_hdmi_window_rd_en;
wire[24:0]  S_mc_app_addr;
wire[2:0]   S_mc_app_cmd;
wire        S_mc_app_en;
wire[127:0] S_mc_app_rd_data;
wire        S_mc_app_rd_data_end;
wire        S_mc_app_rd_data_valid;
wire        S_mc_app_rdy;
wire[127:0] S_mc_app_wdf_data;
wire        S_mc_app_wdf_end;
wire[15:0]  S_mc_app_wdf_mask;
wire        S_mc_app_wdf_rdy;
wire        S_mc_app_wdf_wren;
wire        	S_rst_n;
wire[24:0]  S_vi_ddr_wr_addr;
wire[127:0] S_vi_ddr_wr_data;
wire        S_vi_ddr_wr_en;
wire        S_video_in_wr_busy;
wire        S_video_out_rd_busy;
wire[1:0]   S_video_out_rp;
wire        S_video_out_rst_n;
wire        S_video_out_vsync;
wire[23:0]  S_video_rd_data;
wire[24:0]  S_vo_ddr_rd_addr;
wire        S_vo_ddr_rd_en;

assign S_rst_n = I_rst_n;
assign S_hdmi_rst_n = I_rst_n;
assign S_hdmi_pixel_clk = I_pixel_clk;
assign S_hdmi_serial_clk = I_serial_clk;
assign S_csi_rx_clk = I_capture_clk;
assign S_ISP_O_tdata = I_rgb128;
assign S_ISP_O_tvalid = I_data_valid;
assign S_ISP_O_tuser = I_frame_start;
assign S_hdmi_debug_status = I_debug_status;
assign S_video_out_vsync = ~S_hdmi_vsync;
wire write_frame_begin,capture_overflow;
wire [1:0] write_frame_bank;
wire [31:0] write_frame_id,capture_frame_id;
wire [31:0] capture_frame_us,write_frame_us;wire [15:0] capture_epoch,write_epoch;wire capture_time_valid,write_time_valid;
refined_video_in u_video_in(
        .I_frame_us(capture_frame_us),.I_epoch(capture_epoch),.I_time_valid(capture_time_valid),
        .O_frame_us(write_frame_us),.O_epoch(write_epoch),.O_time_valid(write_time_valid),
        .I_rst_n              (  stream_async_n      ),

        .I_camera_clk         ( S_csi_rx_clk          ),
        .I_camera_frame_start ( S_ISP_O_tuser  ),
        .I_camera_frame_id(capture_frame_id),.O_frame_begin(write_frame_begin),
        .O_frame_bank(write_frame_bank),.O_frame_id(write_frame_id),.O_capture_overflow(capture_overflow),
        .I_camera_valid       ( S_ISP_O_tvalid ),
        .I_camera_data        ( S_ISP_O_tdata  ),
        .I_mipi_rx_error      ( 1'b0			      ),

        .I_ddr_clk            ( S_ddr_clk             ),
		.I_display_pause      ( 1'b0                  ),
        .I_video_out_rd_busy  ( S_video_out_rd_busy   ),
        .O_video_in_wr_busy   ( S_video_in_wr_busy    ),
        .O_video_out_rp       ( S_video_out_rp        ),

        .O_ddr_user_wr_en     ( S_vi_ddr_wr_en        ),
        .O_ddr_user_addr      ( S_vi_ddr_wr_addr      ),
        .O_ddr_user_wr_data   ( S_vi_ddr_wr_data      ),
        .I_ddr_user_ready     ( S_ddr_user_ready      )
    );

    assign S_ddr_user_wr_en    = S_vi_ddr_wr_en;

    assign S_ddr_user_rd_en    = S_vo_ddr_rd_en;

    assign S_ddr_user_addr     = S_vi_ddr_wr_en ? S_vi_ddr_wr_addr :
                                 S_vo_ddr_rd_en ? S_vo_ddr_rd_addr : 'd0;

    assign S_ddr_user_wr_data  = S_vi_ddr_wr_data;

    assign S_video_out_rst_n = S_hdmi_rst_n;

    wire [10:0] active_cx,roi_x;
    wire [9:0] active_cy,roi_y;
    wire active_rotate;wire [2:0] active_zoom;wire [1:0] frame_mode,selected_bank;
    wire [2:0] active_status;
    wire [31:0] selected_frame_id;
    wire [767:0] active_meta;wire [38:0] teach_desired_point,teach_active_point;wire [79:0] teaching_status;wire stage1_raw_area_alarm;
    wire [31:0] image_us,latest_image_id;wire [15:0] image_epoch;wire image_time_valid;
    wire latency_valid;wire [31:0] latency_us,frame_age;
    refined_gray_sync latest_source(I_pixel_clk,I_process_rst_n,I_latest_gray,latest_image_id);
    wire detection_valid,sample_valid;
    wire active_pair,active_show,tip_valid,video_ok,frame_commit,selected_good;
    (* async_reg="true", syn_preserve=1 *) reg [1:0] capture_reset,ddr_reset;
    wire capture_rst_n=capture_reset[1],ddr_rst_n=ddr_reset[1];
    always @(posedge I_capture_clk or negedge stream_async_n)
        if(!stream_async_n) capture_reset<=0;else capture_reset<={capture_reset[0],1'b1};
    always @(posedge S_ddr_clk or negedge stream_async_n)
        if(!stream_async_n) ddr_reset<=0;else ddr_reset<={ddr_reset[0],1'b1};
    // Control-session bundle prevents results from a previous enable cycle
    // from reappearing after rapid stop/restart.
    wire command_ready,command_valid;
    wire [17:0] command_data;
    reg [17:0] command_sent,command_active;
    wire [17:0] command_now={I_k_value,I_pair,I_session,I_tracking};
    wire command_send=command_now!=command_sent && command_ready;
    always @(posedge I_pixel_clk or negedge stream_pixel_n)
        if(!stream_pixel_n) command_sent<=0;else if(command_send) command_sent<=command_now;
    always @(posedge I_capture_clk or negedge capture_rst_n)
        if(!capture_rst_n) command_active<=0;else if(command_valid) command_active<=command_data;
    target_mailbox #(.WIDTH(18)) u_command(
        .S_clk(I_pixel_clk),.S_rst_n(stream_pixel_n),.S_send(command_send),.S_data(command_now),.S_ready(command_ready),
        .D_clk(I_capture_clk),.D_rst_n(capture_rst_n),.D_valid(command_valid),.D_data(command_data));
    wire capture_result,ddr_result,result_ready;
    wire [767:0] capture_meta,ddr_meta;
    stage1_k_capture #(.V4(1)) u_detection(.I_k_value(command_active[17:10]),
        .I_source_id(I_source_id),.I_source_us(I_source_us),.I_now_us(I_capture_us),.I_epoch(stream_epoch),
        .I_time_valid(I_source_time_valid),.I_model_state(I_model_state),.I_quality(I_quality),
        .O_frame_us(capture_frame_us),.O_epoch(capture_epoch),.O_time_valid(capture_time_valid),
        .I_models(I_models),.I_revision(I_revision),.I_gains(I_gains),.I_cal_status(I_cal_status),.I_cal_active(I_cal_active),.I_needs_cal(I_needs_cal),
        .I_clk(I_capture_clk),.I_rst_n(capture_rst_n),.I_sof(I_detect_sof),.I_valid(I_detect_valid),
        .I_fault(capture_overflow),.I_rgb(I_detect_rgb),.I_pair(I_frame_pair),.I_enable(command_active[0]),.I_session(command_active[8:1]),
        .I_result_ready(result_ready),.O_dropped(),.O_frame_id(capture_frame_id),.O_valid(capture_result),.O_meta(capture_meta));
    target_mailbox #(.WIDTH(768)) u_results(
        .S_clk(I_capture_clk),.S_rst_n(capture_rst_n),.S_send(capture_result),.S_data(capture_meta),.S_ready(result_ready),
        .D_clk(S_ddr_clk),.D_rst_n(ddr_rst_n),.D_valid(ddr_result),.D_data(ddr_meta));
    // At every display VS request an atomic bank/generation/result snapshot.
    reg vs_last;
    reg rotate_at_vs;reg [1:0] diag_at_vs,mode_at_vs;reg [2:0] zoom_at_vs;
    always @(posedge I_pixel_clk or negedge I_process_rst_n)
        if(!I_process_rst_n) begin vs_last<=0;mode_at_vs<=0;zoom_at_vs<=0;rotate_at_vs<=1;diag_at_vs<=0;end
        else begin vs_last<=S_hdmi_vsync;if(S_hdmi_vsync&&!vs_last) begin mode_at_vs<=I_process_mode;zoom_at_vs<=I_zoom;rotate_at_vs<=I_rotate;diag_at_vs<=I_diag;end end
    wire snap_request_ready,snap_request;wire [9:0] snapshot_command;
    target_mailbox #(.WIDTH(10)) u_snapshot_request(
        .S_clk(I_pixel_clk),.S_rst_n(stream_pixel_n),.S_send(S_hdmi_vsync&&!vs_last && snap_request_ready),.S_data(command_now[9:0]),.S_ready(snap_request_ready),
        .D_clk(S_ddr_clk),.D_rst_n(ddr_rst_n),.D_valid(snap_request),.D_data(snapshot_command));
    wire snapshot_ready,store_snapshot,pixel_snapshot;
    wire [851:0] store_data,pixel_data;
    (* async_reg="true" *) reg [1:0] camera_event_d;reg camera_event_last;
    always @(posedge S_ddr_clk or negedge ddr_rst_n)
    if(!ddr_rst_n)begin camera_event_d<=0;camera_event_last<=0;end
    else begin camera_event_d<={camera_event_d[0],I_camera_event};camera_event_last<=camera_event_d[1];end
    wire invalidate_camera=camera_event_d[1]!=camera_event_last;
    refined_frame_store #(.V4(1)) u_frame_store(
        .I_frame_us(write_frame_us),.I_epoch(write_epoch),.I_time_valid(write_time_valid),.I_invalidate(invalidate_camera),
        .I_clk(S_ddr_clk),.I_rst_n(ddr_rst_n),.I_begin(write_frame_begin),.I_bank(write_frame_bank),.I_frame_id(write_frame_id),
        .I_write(committed_write),.I_addr(committed_address),.I_result(ddr_result),.I_meta(ddr_meta),
        .I_snapshot(snap_request && snapshot_ready),.I_command(snapshot_command),.O_snapshot(store_snapshot),.O_data(store_data),.O_selected_good(selected_good));
    target_mailbox #(.WIDTH(852)) u_snapshot_response(
        .S_clk(S_ddr_clk),.S_rst_n(ddr_rst_n),.S_send(store_snapshot),.S_data(store_data),.S_ready(snapshot_ready),
        .D_clk(I_pixel_clk),.D_rst_n(stream_pixel_n),.D_valid(pixel_snapshot),.D_data(pixel_data));
    stage1_viewport #(.V4(1)) u_viewport(
        .O_image_us(image_us),.O_epoch(image_epoch),.O_time_valid(image_time_valid),
        .I_rotate(rotate_at_vs),.O_rotate(active_rotate),
        .I_clk(I_pixel_clk),.I_rst_n(stream_pixel_n),.I_vs(S_hdmi_vsync),.I_de(S_hdmi_de),
        .I_pair(I_pair),.O_pair(active_pair),.I_snapshot(pixel_snapshot),.I_data(pixel_data),.I_tracking(I_tracking),.I_show(I_show),.I_conflict(I_conflict),
        .I_live(video_ok && I_camera_ready && stream_pixel_n),.I_session(I_session),.I_zoom(zoom_at_vs),.I_mode(mode_at_vs),
        .O_commit(frame_commit),.O_bank(selected_bank),.O_frame_id(selected_frame_id),
        .O_cx(active_cx),.O_cy(active_cy),.O_x0(roi_x),.O_y0(roi_y),.O_zoom(active_zoom),.O_mode(frame_mode),
        .O_detection_valid(detection_valid),.O_meta(active_meta),.O_show(active_show),.O_sample_valid(sample_valid),.O_state(active_status),.I_point(teach_desired_point),.O_point(teach_active_point));
    refined_line_reader u_scaler (
        .I_stream_n(stream_async_n),.O_fault_toggle(read_fault_toggle),.O_ddr_diag(ddr_diagnostics),.O_pixel_diag(pixel_diagnostics),
        .I_accepted_reads(accepted_reads),.I_unexpected_return(unexpected_return),
        .I_rotate(active_rotate),
        .I_frame_commit(frame_commit && image_time_valid),.I_selected_good(selected_good),.I_models(active_meta[543:416]),
        .I_rst_n(S_rst_n), .I_ddr_clk(S_ddr_clk),
        .I_write_busy(S_video_in_wr_busy), .I_write_en(S_vi_ddr_wr_en), .I_read_buffer(selected_bank),.I_frame_id(selected_frame_id),
        .I_ddr_ready(S_ddr_user_ready && S_init_calib_complete), .I_ddr_valid(S_ddr_user_rd_valid),
        .I_ddr_data(S_ddr_user_rd_data), .O_read_busy(S_video_out_rd_busy),
        .O_read_en(S_vo_ddr_rd_en), .O_read_addr(S_vo_ddr_rd_addr),
        .I_pixel_clk(S_hdmi_pixel_clk), .I_vs(S_hdmi_vsync), .I_hs(S_hdmi_hsync), .I_de(S_hdmi_de),
        .I_x0(roi_x), .I_y0(roi_y), .I_zoom(active_zoom),
        .O_vs(S_hdmi_out_vsync), .O_hs(S_hdmi_out_hsync), .O_de(S_hdmi_out_de),
        .O_rgb(S_hdmi_out_data), .O_mask(source_mask),.O_video_ok(video_ok)
    );

    refined_mc_to_user_interface u_mc_to_user_interface(
        .O_write_commit(committed_write),.O_write_addr(committed_address),
        .O_outstanding_reads(outstanding_reads),.O_unexpected_return(unexpected_return),
        .O_accepted_reads(accepted_reads),
        .I_clk                   ( S_ddr_clk               ),
        .I_rst_n                 ( ddr_rst_n               ),

        .I_ddr_user_wr_en        ( S_ddr_user_wr_en        ),
        .I_ddr_user_rd_en        ( S_ddr_user_rd_en        ),
        .I_ddr_user_addr         ( S_ddr_user_addr         ),
        .I_ddr_user_wr_data      ( S_ddr_user_wr_data      ),
        .O_ddr_user_ready        ( S_ddr_user_ready        ),
        .O_ddr_user_rd_valid     ( S_ddr_user_rd_valid     ),
        .O_ddr_user_rd_data      ( S_ddr_user_rd_data      ),
            
        .O_mc_app_en             ( S_mc_app_en             ),
        .O_mc_app_addr           ( S_mc_app_addr           ),
        .O_mc_app_cmd            ( S_mc_app_cmd            ),
        .I_mc_app_rdy            ( S_mc_app_rdy            ),
        .O_mc_app_wdf_wren       ( S_mc_app_wdf_wren       ),
        .O_mc_app_wdf_data       ( S_mc_app_wdf_data       ),
        .O_mc_app_wdf_end        ( S_mc_app_wdf_end        ),
        .O_mc_app_wdf_mask       ( S_mc_app_wdf_mask       ),
        .I_mc_app_wdf_rdy        ( S_mc_app_wdf_rdy        ),
        .I_mc_app_rd_data        ( S_mc_app_rd_data        ),
        .I_mc_app_rd_data_end    ( S_mc_app_rd_data_end    ),
        .I_mc_app_rd_data_valid  ( S_mc_app_rd_data_valid  )
    );

    refined_ph1p35_ddr_wrapper u_ph1p35_324_ddr_wrapper(
        .I_sys_clk              ( I_sys_clk              ),
        .I_sys_rst_n            ( controller_reset_n     ),

        .O_ddr_clk              ( S_ddr_clk              ),
        .O_init_calib_complete  ( S_init_calib_complete  ),
        .I_mc_app_addr          ( S_mc_app_addr          ),
        .I_mc_app_cmd           ( S_mc_app_cmd           ),
        .I_mc_app_en            ( S_mc_app_en            ),
        .I_mc_app_wdf_data      ( S_mc_app_wdf_data      ),
        .I_mc_app_wdf_end       ( S_mc_app_wdf_end       ),
        .I_mc_app_wdf_mask      ( S_mc_app_wdf_mask      ),
        .I_mc_app_wdf_wren      ( S_mc_app_wdf_wren      ),
        .O_mc_app_rd_data       ( S_mc_app_rd_data       ),
        .O_mc_app_rd_data_end   ( S_mc_app_rd_data_end   ),
        .O_mc_app_rd_data_valid ( S_mc_app_rd_data_valid ),
        .O_mc_app_rdy           ( S_mc_app_rdy           ),
        .O_mc_app_wdf_rdy       ( S_mc_app_wdf_rdy       ),

        .ddr_addr               ( ddr_addr               ),
        .ddr_ba                 ( ddr_ba                 ),
        .ddr_cke                ( ddr_cke                ),
        .ddr_odt                ( ddr_odt                ),
        .ddr_cs_n               ( ddr_cs_n               ),
        .ddr_ras_n              ( ddr_ras_n              ),
        .ddr_cas_n              ( ddr_cas_n              ),
        .ddr_we_n               ( ddr_we_n               ),
        .ddr_ck_p               ( ddr_ck_p               ),
        .ddr_ck_n               ( ddr_ck_n               ),
        .ddr_dm                 ( ddr_dm                 ),
        .ddr_dq                 ( ddr_dq                 ),
        .ddr_dqs_p              ( ddr_dqs_p              ),
        .ddr_dqs_n              ( ddr_dqs_n              )
    );

    uivtc #(
        .H_ActiveSize ( 1280 ),
        .H_FrameSize  ( 1650 ),
        .H_SyncStart  ( 1390 ),
        .H_SyncEnd    ( 1430 ),
        .V_ActiveSize ( 720  ),
        .V_FrameSize  ( 750  ),
        .V_SyncStart  ( 725  ),
        .V_SyncEnd    ( 730  )
    )u_hdmi_vtc(
        .I_vtc_rstn    ( S_hdmi_rst_n    ),
        .I_vtc_clk     ( S_hdmi_pixel_clk ),
        .O_vtc_vs      ( S_hdmi_vsync     ),
        .O_vtc_hs      ( S_hdmi_hsync     ),
        .O_vtc_de_valid( S_hdmi_de        ),
        .O_vtc_user    ( S_hdmi_user      ),
        .O_vtc_last    ( S_hdmi_last      )
    );

    wire process_vs, process_hs, process_de;
    wire [23:0] process_rgb;
    wire [1:0] actual_mode;
    // Display-side RGB processing leaves the camera/DDR packed stream unchanged.
    stable_preprocess u_image_preprocess (
        .I_clk(S_hdmi_pixel_clk), .I_rst_n(I_process_rst_n),
        .I_mode(frame_mode),.I_pair(active_pair),
        .I_vs(S_hdmi_out_vsync), .I_hs(S_hdmi_out_hsync),
        .I_de(S_hdmi_out_de), .I_rgb(S_hdmi_out_data),.I_mask(source_mask),
        .O_vs(process_vs), .O_hs(process_hs), .O_de(process_de),
        .O_rgb(process_rgb), .O_mode(actual_mode)
    );

    wire osd_vs, osd_hs, osd_de;
    wire [23:0] osd_rgb;
    wire telemetry_ready;wire [127:0] ddr_ui;wire recovery_ui_ready;wire [38:0] recovery_ui;
    target_mailbox #(.WIDTH(128)) telemetry(.S_clk(S_ddr_clk),.S_rst_n(I_rst_n),.S_send(snap_request && telemetry_ready),.S_data(ddr_diagnostics),.S_ready(telemetry_ready),
     .D_clk(I_pixel_clk),.D_rst_n(I_process_rst_n),.D_valid(),.D_data(ddr_ui));
    refined_recovery_mailbox #(.WIDTH(39)) recovery_telemetry(.S_clk(I_sys_clk),.S_rst_n(I_rst_n),.S_send(recovery_ui_ready),
     .S_data({recovery_failed,recovery_reason,recovery_retries,recovery_count,stream_epoch}),.S_ready(recovery_ui_ready),
     .D_clk(I_pixel_clk),.D_rst_n(I_process_rst_n),.D_valid(),.D_data(recovery_ui));
    refined_performance performance(I_pixel_clk,I_process_rst_n,osd_vs,osd_de,video_ok && I_camera_ready && stream_pixel_n,
     I_board_us,image_us,selected_frame_id,latest_image_id,image_time_valid,latency_valid,latency_us,frame_age);
    wire area_associated,area_video;wire [3:0] area_tip_reason;
    wire teaching_image_ok;wire [3:0] teaching_image_reason;
    wire teaching_image_associated=active_meta[255] && active_meta[247] && active_meta[415:413]==4 &&
     active_meta[31:0]==selected_frame_id && active_meta[719:704]==image_epoch && active_meta[671:640]==image_us &&
     active_meta[720] && image_time_valid && active_meta[242:235]==I_session && active_meta[243]==I_pair && active_meta[244]==I_tracking;
    stage1_teach_image_guard teaching_video_guard(I_pixel_clk,I_process_rst_n,stream_pixel_n,I_camera_ready,I_gain_busy,
     video_ok,S_hdmi_out_de,teaching_image_associated,selected_frame_id,teaching_image_ok,teaching_image_reason);
    stage1_input_guard region_input(I_pixel_clk,I_process_rst_n,stream_pixel_n,I_tracking,I_camera_ready,I_gain_busy,
     video_ok,S_hdmi_out_de,frame_commit,I_session,I_pair,selected_frame_id,image_epoch,image_us,image_time_valid,active_meta,area_associated,area_video);
    wire [2:0] area_count,area_expected,area_actual;wire [3:0] area_draft,area_state,area_completed,area_occupied,area_closed,area_edit_error,area_start_error;
    wire [15:0] area_revision,area_counts;wire [671:0] area_vertices,area_saved_vertices;wire [167:0] area_draft_vertices;wire area_muted,area_busy,area_tip,area_metrics_valid;
    wire [1:0] area_trend;wire [10:0] area_distance;wire [19:0] area_dwell;
    stage1_teach_alarm replay_alarm_gate(I_ui_mode,teaching_status[3:0],stage1_raw_area_alarm,O_area_alarm);
    stage1_scene area_controller(.current_k(I_k_value),.clk(I_pixel_clk),.rst_n(I_process_rst_n),.mode(I_ui_mode),.down2(I_key_down2),.click2(I_key2),.click3(I_key3),.click4(I_key4),.cancel(I_key_cancel),
     .tracking(I_tracking),.video_ok(area_video),.camera_ready(I_camera_ready),.gain_busy(I_gain_busy),.session(I_session),.pair(I_pair),
     .frame_commit(frame_commit),.detection_valid(area_associated),.image_id(selected_frame_id),.meta(active_meta),
     .region_count(area_count),.draft_count(area_draft),.revision(area_revision),.render_vertices(area_vertices),.render_counts(area_counts),.closed_mask(area_closed),
     .run_state(area_state),.completed(area_completed),.occupied(area_occupied),.expected_area(area_expected),.actual_area(area_actual),.muted(area_muted),.alarm(stage1_raw_area_alarm),
     .trend(area_trend),.distance(area_distance),.dwell_ms(area_dwell),.edit_error(area_edit_error),.start_error(area_start_error),.busy(area_busy),.tip_live(area_tip),.metrics_valid(area_metrics_valid),.saved_vertices(area_saved_vertices),.draft_vertices(area_draft_vertices),.tip_reason(area_tip_reason),.image_healthy(teaching_image_ok),.image_reason(teaching_image_reason),
     .shown_point(teach_active_point),.desired_point(teach_desired_point),.teaching(teaching_status));
    stage1_osd u_osd (.I_k_value(I_k_value),.I_k_adjust(I_k_adjust),.I_teaching(teaching_status),.I_point(teach_active_point[22:0]),
     .I_ui_mode(I_ui_mode),.I_region_vertices(area_saved_vertices),.I_region_draft(area_draft_vertices),.I_region_counts(area_counts),.I_region_closed(area_closed),
     .I_area_count(area_count),.I_draft_count(area_draft),.I_run_state(area_state),.I_completed(area_completed),.I_occupied(area_occupied),
     .I_expected_area(area_expected),.I_actual_area(area_actual),.I_area_muted(area_muted),.I_area_trend(area_trend),.I_area_distance(area_distance),.I_area_dwell(area_dwell),
     .I_edit_error(area_edit_error),.I_start_error(area_start_error),.I_area_busy(area_busy || (area_tip && area_count!=0 && !area_metrics_valid)),.I_tip_live(area_tip),
     .I_gain_busy(I_gain_busy),.I_gain_failed(I_gain_failed),.I_gain_slot(I_gain_slot),.I_gain_target(I_gain_target),.I_tip_reason(area_tip_reason),
        .I_latency_valid(latency_valid),.I_latency_us(latency_us),.I_frame_age(frame_age),
        .I_ddr_diag(ddr_ui),.I_pixel_diag(pixel_diagnostics),.I_recovery(recovery_ui),.I_camera(I_camera_status),
        .I_geometry_commit(frame_commit),
        .I_rotate(active_rotate),.I_diag(diag_at_vs),.I_image_id(selected_frame_id),
        .I_clk(S_hdmi_pixel_clk),.I_rst_n(I_process_rst_n),
        .I_vs(process_vs),.I_hs(process_hs),.I_de(process_de),.I_rgb(process_rgb),
        .I_tracking(I_tracking),.I_meta(active_meta),.I_x0(roi_x),.I_y0(roi_y),.I_zoom(active_zoom),.I_mode(actual_mode),
        .I_detection_valid(detection_valid),.I_pair(active_pair),.I_state(active_status),.I_show(active_show),.I_sample_valid(sample_valid),.I_video_ok(video_ok && I_camera_ready && stream_pixel_n),
        .O_vs(osd_vs),.O_hs(osd_hs),.O_de(osd_de),.O_rgb(osd_rgb)
    );
    hdmi_tx u_hdmi_tx(
        .I_pixel_clk        ( S_hdmi_pixel_clk  ),
        .I_serial_clk       ( S_hdmi_serial_clk ),
        .I_rst              ( ~S_hdmi_rst_n     ),
        .I_key_in           ( 1'b0              ),
        .I_edid_read_trig   ( 1'b0              ),
        .O_edid_read_valid  (                   ),
        .O_edid_read_data   (                   ),
        .I_video_rgb_enable ( 1'b1              ),
        .I_video_in_vs      ( osd_vs           ),
        .I_video_in_de      ( osd_de           ),
        .I_video_in_user    ( 1'b0              ),
        .I_video_in_valid   ( 1'b0              ),
        .I_video_in_last    ( 1'b0              ),
        .O_video_in_ready   (                   ),
        .I_video_in_data    ( osd_rgb          ),
        .I_audio_valid      ( 1'b0              ),
        .I_audio_left_data  ( 24'd0             ),
        .I_audio_right_data ( 24'd0             ),
        .I_i2s_BCLK         ( 1'b0              ),
        .I_i2s_LRCK         ( 1'b0              ),
        .I_i2s_DOUT         ( 1'b0              ),
        .O_ddc_scl          (                   ),
        .O_hdmi_clk_p       (                   ),
        .O_hdmi_tx_p        (                   ),
        .O_tmds_ch0_p       ( O_tmds_ch0_p      ),
        .O_tmds_ch1_p       ( O_tmds_ch1_p      ),
        .O_tmds_ch2_p       ( O_tmds_ch2_p      ),
        .O_tmds_clk_p       ( O_tmds_clk_p      )
    );

endmodule
`default_nettype wire

// Bundled-data CDC: hold payload until acknowledgement returns. Both domains
// share asynchronous assertion; each receives locally synchronized release.
`default_nettype none
module refined_recovery_mailbox #(parameter WIDTH=256)(
    input wire S_clk,S_rst_n,S_send,
    input wire [WIDTH-1:0] S_data,
    output wire S_ready,
    input wire D_clk,D_rst_n,
    output reg D_valid,
    output reg [WIDTH-1:0] D_data
);
    reg request,ack;
    reg [WIDTH-1:0] payload;
    (* async_reg="true", syn_preserve=1 *) reg ack1,ack_mid,ack2,req1,req2,req3;
    // A full source-clock period plus a half period resolve ACK before use.
    // First two samples use falling edges; final rising-edge stage preserves
    // the original source-side request/payload update edge.
    always @(negedge S_clk or negedge S_rst_n)begin
        if(!S_rst_n)begin ack1<=0;ack_mid<=0;end
        else begin ack1<=ack;ack_mid<=ack1;end
    end
    always @(posedge S_clk or negedge S_rst_n)
        if(!S_rst_n)ack2<=0;else ack2<=ack_mid;
    assign S_ready=request==ack2;
    always @(posedge S_clk or negedge S_rst_n) begin
        if(!S_rst_n) begin request<=0;payload<=0;end
        else begin

            if(S_send && S_ready) begin payload<=S_data;request<=~request;end
        end
    end
    always @(posedge D_clk or negedge D_rst_n) begin
        if(!D_rst_n) begin req1<=0;req2<=0;req3<=0;ack<=0;D_valid<=0;D_data<=0;end
        else begin
            req1<=request;req2<=req1;req3<=req2;D_valid<=0;
            if(req3!=ack) begin D_data<=payload;D_valid<=1;ack<=req3;end
        end
    end
endmodule
`default_nettype wire

// Suppress a latched previous sequence result during replay preload/restart.
`default_nettype none
module stage1_teach_alarm(input wire [1:0] mode,input wire [3:0] route_state,input wire raw_alarm,output wire alarm);
assign alarm=raw_alarm && (mode!=2'd3 || route_state==4'd8);
endmodule
`default_nettype wire

// K and command are frozen at the same accepted image start.
// Production capture: classifier -> pixel support -> fixed grid -> one tool.
// 640-bit protocol v3 includes bank-owned colour/candidate/decision diagnostics.
// immutable colour models/revision/calibration status belonging to this frame.
`default_nettype none
module stage1_k_capture #(parameter V4=0)(input wire I_clk,I_rst_n,I_sof,I_valid,I_fault,
 input wire [95:0] I_rgb,input wire I_pair,I_enable,input wire [7:0] I_session,
 input wire [127:0] I_models,input wire [15:0] I_revision,
 input wire [23:0] I_gains,input wire [7:0] I_cal_status,input wire I_cal_active,I_needs_cal,
 input wire I_result_ready,output reg [31:0] O_frame_id,
 output reg O_valid,output wire [(V4?768:640)-1:0] O_meta,output reg [31:0] O_dropped,
 input wire [31:0] I_source_id,I_source_us,I_now_us,input wire [15:0] I_epoch,
 input wire I_time_valid,input wire [1:0] I_model_state,input wire [41:0] I_quality,
 output reg [31:0] O_frame_us,output reg [15:0] O_epoch,output reg O_time_valid,input wire [7:0] I_k_value);
 wire clk=I_clk,rst_n=I_rst_n;reg last_sof,have,cb,accepted;
 wire sof=I_sof && !last_sof;wire nb=have?!cb:1'b0;
 reg [1:0] owned,pending,complete,closed;reg [3:0] invalid_drain[0:1];
 wire take=!owned[nb];reg [19:0] pixels;reg fault;reg [10:0] x;reg [9:0] y;
 wire [10:0] rx=sof?0:x;wire [9:0] ry=sof?0:y;
 reg [7:0] bank_k[0:1];reg [31:0] ids[0:1];reg [9:0] cmds[0:1];reg [127:0] models[0:1];
 reg [31:0] source_us[0:1];reg [15:0] epochs[0:1];reg [1:0] time_valid;
 reg [1:0] model_states[0:1];reg [41:0] qualities[0:1];
 reg [15:0] revs[0:1];reg [23:0] gains[0:1],mean[0:1];reg [7:0] status[0:1];reg [1:0] needs,sample_ok;
 reg [19:0] raw_a[0:1],raw_b[0:1],filtered_a[0:1],filtered_b[0:1];
 function [2:0] population;input [3:0] v;begin population={2'd0,v[0]}+v[1]+v[2]+v[3];end endfunction
 reg [13:0] sr,sg,sb;reg [6:0] sn;reg [10:0] ar,ag,ab;reg [2:0] an;integer i;
 always @*begin ar=0;ag=0;ab=0;an=0;
 for(i=0;i<4;i=i+1)if(rx+i>=636 && rx+i<644 && ry>=356 && ry<364)begin
 ar=ar+I_rgb[95-24*i-:8];ag=ag+I_rgb[87-24*i-:8];ab=ab+I_rgb[79-24*i-:8];an=an+1'b1;end end
 reg [3:0] vp;reg [1:0] tags[0:3];reg [10:0] xp[0:3];reg [9:0] yp[0:3];
 wire [7:0] mask;genvar lane;
 wire [3:0] raw_mask_a={mask[6],mask[4],mask[2],mask[0]},raw_mask_b={mask[7],mask[5],mask[3],mask[1]};
 // Calibration commits at pre-AWB SOF. The last two post-AWB groups of the
 // previous frame may still be in flight then: classify them with their bank's
 // frozen model, and select the new profile only at the post-AWB SOF itself.
 wire [127:0] pixel_models=sof?I_models:(have?models[cb]:I_models);
 generate for(lane=0;lane<4;lane=lane+1)begin:classify
 stable_model_lane u_lane(clk,rst_n,I_rgb[95-lane*24-:24],pixel_models,mask[lane*2+:2]);end endgenerate
 wire fv;wire [1:0] ft;wire [10:0] fx;wire [9:0] fy;wire [7:0] fa,fb;
 stable_filter4 filter(clk,rst_n,vp[3],xp[3],yp[3],tags[3],mask,fv,ft,fx,fy,fa,fb);
 reg gs,ts,wb;wire gb,gd,gfailed;wire [1023:0] candidates;wire [17:0] work_cycles;
 wire hist_valid;wire [83:0] hist_boxes;
 wire [9:0] hist_command;wire [15:0] hist_revision;wire [31:0] hist_frame;wire [4:0] hist_loss;wire [3:0] tip_bounds;
 wire detect_allowed=cmds[wb][0] && !needs[wb] && status[wb][7:5]==0;
 wire [1:0] selected_state;wire [31:0] history_gap=ids[wb]-hist_frame;
 wire history_for_bank_now=hist_valid && hist_command=={cmds[wb][9:1],detect_allowed} && hist_revision==revs[wb] &&
 history_gap!=0 && !history_gap[31] && history_gap<=15 && ({27'd0,hist_loss}+history_gap)<=15 &&
 (selected_state==2 || history_gap==1);
 // state 0 selects wb; state 1 freezes its history predicate and issues gs.
 // The grid samples both on the next edge. Its candidate/result cycles do not
 // change, and the history command/revision/frame/lifetime checks stay intact.
 reg history_for_bank;
 stable_grid grid(clk,rst_n,fv && ft[1],ft[0],fx,fy,fa,fb,gs,wb,
 history_for_bank,hist_boxes,history_for_bank,gb,gd,gfailed,candidates,work_cycles);
 wire td,tv;wire [127:0] a,b;wire [10:0] tx;wire [9:0] ty;wire [3:0] reason;
 wire work_complete=complete[wb] && !gfailed;
 stage1_k_tracker tracker(clk,rst_n,ts,ids[wb],{cmds[wb][9:1],detect_allowed},revs[wb],work_complete,
 candidates,td,a,b,tv,tx,ty,reason,hist_valid,hist_boxes,selected_state,hist_command,hist_revision,hist_frame,hist_loss,tip_bounds,bank_k[wb]);
 reg [2:0] state;reg [767:0] packet,waiting_packet;reg waiting_result;
 always @(posedge clk or negedge rst_n)
 if(!rst_n)history_for_bank<=0;
 else if(state==1)history_for_bank<=history_for_bank_now;
 // The mailbox samples only on O_valid. This independent pending bank is
 // already immutable until its next complete result copy; a second 640-bit
 // output register adds no protection. Do not issue a pulse on a copy cycle:
 // the following source edge must sample the packet identified by that pulse.
 assign O_meta=waiting_packet[(V4?768:640)-1:0];
 function [3:0] failure_stage;input c;reg [19:0] raw,filtered;reg [2:0] n,gr;begin
 raw=c?raw_b[wb]:raw_a[wb];filtered=c?filtered_b[wb]:filtered_a[wb];
 n=c?candidates[635:633]:candidates[123:121];gr=c?candidates[639:637]:candidates[127:125];
 failure_stage=!complete[wb]?6:gfailed?7:needs[wb] || status[wb][7:5]!=0?9:
 raw==0?1:filtered==0?2:n!=0?5:gr==3?3:4;end endfunction
 always @*begin
 packet=0;
 packet[230:224]=bank_k[wb][6:0];packet[248]=bank_k[wb][7];packet[249]=1;packet[31:0]=ids[wb];packet[32]=tv;packet[36:33]=reason;
 packet[47:37]=a[72:62];packet[57:48]=a[82:73];packet[68:58]=b[72:62];packet[78:69]=b[82:73];
 packet[89:79]=tx;packet[99:90]=ty;packet[141:100]=a[41:0];packet[183:142]=b[41:0];
 packet[203:184]=a[61:42];packet[223:204]=b[61:42];
 packet[232:231]=work_complete?0:2;packet[234:233]=work_complete?0:2;
 packet[242:235]=cmds[wb][8:1];packet[243]=cmds[wb][9];packet[244]=cmds[wb][0];
 packet[245]=a[120] && work_complete && detect_allowed;packet[246]=b[120] && work_complete && detect_allowed;
 packet[247]=complete[wb];packet[255]=1;packet[407:384]=mean[wb];packet[408]=sample_ok[wb];packet[415:413]=V4?4:3;
 packet[412:409]=tip_bounds;
 packet[543:416]=models[wb];packet[559:544]=revs[wb];packet[567:560]=status[wb];
 packet[568]=needs[wb];packet[592:569]=gains[wb];
 packet[594:593]=selected_state;
 // A single selected tool is identified within its user-started session.
 packet[603:595]={cmds[wb][8:1],cmds[wb][9]};
 packet[275:256]=raw_a[wb];packet[295:276]=raw_b[wb];packet[315:296]=filtered_a[wb];packet[335:316]=filtered_b[wb];
 packet[338:336]=work_complete?candidates[123:121]:0;packet[341:339]=work_complete?candidates[635:633]:0;
 packet[345:342]=failure_stage(0);packet[349:346]=failure_stage(1);
 packet[356:350]=a[89:83];packet[363:357]=b[89:83];packet[365:364]=a[93:92];packet[367:366]=a[95:94];
 packet[369:368]=a[97:96];packet[377:370]=a[111:104];packet[379:378]=a[99:98];packet[383:380]=a[103:100];
 packet[604]=complete[wb];packet[605]=work_complete && candidates[124];packet[606]=work_complete && candidates[636];
 packet[624:607]=complete[wb]?work_cycles:0;packet[639:625]=O_dropped>32767?15'd32767:O_dropped[14:0];
 packet[671:640]=source_us[wb];packet[703:672]=I_now_us;packet[719:704]=epochs[wb];
 packet[720]=time_valid[wb];packet[722:721]=model_states[wb];packet[764:723]=qualities[wb];
 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
 last_sof<=0;have<=0;cb<=0;accepted<=0;owned<=0;pending<=0;complete<=0;closed<=0;pixels<=0;fault<=0;x<=0;y<=0;
 sr<=0;sg<=0;sb<=0;sn<=0;needs<=0;sample_ok<=0;vp<=0;gs<=0;ts<=0;wb<=0;state<=0;
 waiting_packet<=0;waiting_result<=0;O_frame_id<=0;O_valid<=0;O_dropped<=0;O_frame_us<=0;O_epoch<=0;O_time_valid<=0;time_valid<=0;
 for(i=0;i<2;i=i+1)begin bank_k[i]<=50;ids[i]<=0;cmds[i]<=0;models[i]<=0;revs[i]<=0;gains[i]<=0;mean[i]<=0;status[i]<=0;invalid_drain[i]<=0;
 raw_a[i]<=0;raw_b[i]<=0;filtered_a[i]<=0;filtered_b[i]<=0;end
 for(i=0;i<4;i=i+1)begin xp[i]<=0;yp[i]<=0;tags[i]<=0;end end
 else begin
 last_sof<=I_sof;gs<=0;ts<=0;O_valid<=0;
 vp<={vp[2:0],I_valid && (sof || have) && (sof || pixels<921600)};
 xp[0]<=rx;yp[0]<=ry;tags[0]<=sof?{take,nb}:{accepted,cb};
 for(i=1;i<4;i=i+1)begin xp[i]<=xp[i-1];yp[i]<=yp[i-1];tags[i]<=tags[i-1];end
 if(vp[3] && tags[3][1])begin raw_a[tags[3][0]]<=raw_a[tags[3][0]]+population(raw_mask_a);
 raw_b[tags[3][0]]<=raw_b[tags[3][0]]+population(raw_mask_b);end
 if(fv && ft[1])begin filtered_a[ft[0]]<=filtered_a[ft[0]]+population(fa[3:0]);filtered_b[ft[0]]<=filtered_b[ft[0]]+population(fb[3:0]);end
 for(i=0;i<2;i=i+1)if(invalid_drain[i]!=0)begin
 invalid_drain[i]<=invalid_drain[i]-1'b1;if(invalid_drain[i]==1)pending[i]<=1;end
 if(sof)begin
 if(have && accepted)begin closed[cb]<=1;complete[cb]<=pixels==921600 && !fault && !I_fault;end
 if(have && accepted && pixels!=921600)begin complete[cb]<=0;invalid_drain[cb]<=8;end
 have<=1;cb<=nb;accepted<=take;O_frame_id<=V4?I_source_id:O_frame_id+1'b1;
 O_frame_us<=I_source_us;O_epoch<=I_epoch;O_time_valid<=I_time_valid;
 pixels<=I_valid?4:0;x<=I_valid?4:0;y<=0;fault<=0;sr<=0;sg<=0;sb<=0;sn<=0;
 if(take)begin
 raw_a[nb]<=0;raw_b[nb]<=0;filtered_a[nb]<=0;filtered_b[nb]<=0;
 bank_k[nb]<=I_k_value;owned[nb]<=1;closed[nb]<=0;complete[nb]<=0;ids[nb]<=V4?I_source_id:O_frame_id+1'b1;cmds[nb]<={I_pair,I_session,I_enable};
 source_us[nb]<=I_source_us;epochs[nb]<=I_epoch;time_valid[nb]<=I_time_valid;model_states[nb]<=I_model_state;qualities[nb]<=I_quality;
 models[nb]<=I_models;revs[nb]<=I_revision;gains[nb]<=I_gains;status[nb]<=I_cal_status;needs[nb]<=I_needs_cal;
 end else O_dropped<=O_dropped+1'b1;
 end else begin
 // video_in clears its sticky flag at its packed SOF, two clocks after our
 // RGB SOF. The first four groups provide that boundary settling interval;
 // a genuine new-frame overflow remains sticky and is caught afterwards.
 if(I_fault && pixels>=16)begin fault<=1;if(accepted)complete[cb]<=0;end
 if(I_valid && have)begin
 if(pixels<921600)begin
 pixels<=pixels+4;if(x==1276)begin x<=0;y<=y+1'b1;end else x<=x+4;
 sr<=sr+ar;sg<=sg+ag;sb<=sb+ab;sn<=sn+an;
 if(pixels==921596 && accepted)begin complete[cb]<=!fault && !I_fault;mean[cb]<={sr[13:6],sg[13:6],sb[13:6]};sample_ok[cb]<=sn==64;end
 end else begin fault<=1;if(accepted)complete[cb]<=0;end end end
 if(fv && ft[1] && fx==1276 && fy==719)pending[ft[0]]<=1;
 if(waiting_result && I_result_ready && state!=5)begin O_valid<=1;waiting_result<=0;end
 case(state)
 0:if(pending!=0)begin wb<=pending[0]?0:1;pending[pending[0]?0:1]<=0;state<=1;end
 1:if(complete[wb])begin gs<=1;state<=2;end else state<=3;
 2:if(gd)state<=3;
 3:if(closed[wb])begin ts<=1;state<=4;end
 4:if(td)state<=5;
 5:begin
 if(waiting_result)O_dropped<=O_dropped+1'b1;
 waiting_packet<=packet;waiting_result<=1;owned[wb]<=0;state<=0;
 end
 endcase end end
endmodule
`default_nettype wire

// Shared-K endpoint wrapper generated from the immutable detector.
// One selected tool, three consecutive capture frames, signed K=D/L=1/2.
// Missing colours hide the tip immediately; identity expires after 15 new frames.
`default_nettype none
module stage1_k_tracker(input wire clk,rst_n,start,input wire [31:0] frame_id,
 input wire [9:0] command,input wire [15:0] revision,input wire complete,
 input wire [1023:0] candidates,output reg done,
 output reg [127:0] a,b,output reg tip_valid,output reg [10:0] tip_x,
 output reg [9:0] tip_y,output reg [3:0] reason,
 output wire history_valid,output wire [83:0] history_boxes,output wire [1:0] selection_state,
 output wire [9:0] history_command,output wire [15:0] history_revision,output wire [31:0] history_frame,
 output wire [4:0] history_loss,output reg [3:0] tip_bounds,input wire [7:0] k_value);
 reg [4:0] state;reg [3:0] pair_index;reg [31:0] last_id;
 reg [9:0] last_command;reg [15:0] last_revision;
 reg have_id,locked,expired;reg [1:0] streak;reg [4:0] lost;
 reg frame_ok,advance;
 wire [31:0] gap=frame_id-last_id;
 wire [5:0] skipped_loss={1'b0,lost}+{1'b0,gap[4:0]}-1'b1;
 reg [127:0] olda,oldb;reg [31:0] bestscore;
 reg [7:0] best_quality,rejected;reg [3:0] chosen_indices;reg [1:0] chosen_reason;
 reg [7:0] reject_bits;
 reg diagnostic_found;reg [31:0] diagnostic_score;
 reg [7:0] diagnostic_quality,diagnostic_reject;reg [3:0] diagnostic_indices;
 reg have_a,have_b;reg [1:0] first_a,first_b;reg [127:0] single_a,single_b;integer ci;
 reg found;reg [10:0] fax,fbx;reg [9:0] fay,fby;
 reg [127:0] ca,cb;reg signed [12:0] dax,day,dbx,dby,dx,dy,odx,ody;
 wire [7:0] pair_quality={1'b0,ca[89:83]}+{1'b0,cb[89:83]};
 reg [31:0] distance,old_distance,score;reg match,guide;
 reg signed [13:0] nt_x,nt_y;reg [11:0] midx;reg [10:0] midy;
 // Two shared registered multipliers. Never chain a square, sum and comparison
 // through a second DSP in one cycle; all sixteen pairs have fixed latency.
 reg signed [12:0] mx0,my0,mx1,my1;
 reg signed [25:0] product0,product1;
 wire signed [26:0] product_sum=$signed({product0[25],product0})+$signed({product1[25],product1});
 function [12:0] abs13;input signed [12:0] n;begin abs13=n<0?-n:n;end endfunction
 function signed [13:0] half_away;input signed [13:0] n;begin half_away=n<0?-((-n+1)>>>1):((n+1)>>>1);end endfunction
 reg k_axis,k_negative;reg [7:0] k_frozen,k_shift;
 reg [4:0] k_bit;reg [19:0] k_acc,k_addend,k_number,k_quotient,k_rounded;
 reg [6:0] k_remainder;reg [19:0] k_alu_a,k_alu_b;
 wire [19:0] k_sum=k_alu_a+k_alu_b;
 wire [10:0] k_a=k_axis?{1'b0,fay}:fax,k_b=k_axis?{1'b0,fby}:fbx;
 wire signed [11:0] k_delta=$signed({1'b0,k_a})-$signed({1'b0,k_b});
 wire [7:0] k_trial={k_remainder,k_number[19]};
 wire k_take=k_trial>=100;
 always @*begin
 k_alu_a=0;k_alu_b=0;
 case(state)
 11:begin k_alu_a=k_acc;k_alu_b={4'd0,k_a,5'd0};end
 12:begin k_alu_a=k_acc;k_alu_b={7'd0,k_a,2'd0};end
 13:begin k_alu_a=k_acc;k_alu_b=k_shift[0]?k_addend:20'd0;end
 14:begin k_alu_a=k_acc[19]?~k_acc:k_acc;k_alu_b=k_acc[19]?20'd1:20'd0;end
 15:begin k_alu_a={12'd0,k_trial};k_alu_b=k_take?-20'd100:20'd0;end
 16:begin k_alu_a=k_quotient;k_alu_b=k_remainder>=50?20'd1:20'd0;end
 17:begin k_alu_a=k_negative?~k_rounded:k_rounded;k_alu_b=k_negative?20'd1:20'd0;end
 default:begin end
 endcase end
 assign history_valid=locked || streak!=0;assign history_boxes={oldb[41:0],olda[41:0]};
 assign selection_state=expired?3:locked?2:streak!=0?1:0;
 assign history_command=last_command;assign history_revision=last_revision;
 assign history_frame=last_id;assign history_loss=lost;
 always @*begin
 have_a=0;have_b=0;first_a=0;first_b=0;single_a=0;single_b=0;
 for(ci=3;ci>=0;ci=ci-1)begin
 if(candidates[ci*128+120])begin have_a=1;first_a=ci;single_a=candidates[ci*128+:128];end
 if(candidates[(ci+4)*128+120])begin have_b=1;first_b=ci;single_b=candidates[(ci+4)*128+:128];end
 end
 ca=candidates[pair_index[1:0]*128+:128];cb=candidates[(4+pair_index[3:2])*128+:128];
 dx=$signed({2'd0,ca[72:62]})-$signed({2'd0,cb[72:62]});
 dy=$signed({3'd0,ca[82:73]})-$signed({3'd0,cb[82:73]});
 odx=$signed({2'd0,olda[72:62]})-$signed({2'd0,oldb[72:62]});
 ody=$signed({3'd0,olda[82:73]})-$signed({3'd0,oldb[82:73]});
 mx0=dx;my0=dx;mx1=dy;my1=dy;
 if(state==1)begin mx0=odx;my0=odx;mx1=ody;my1=ody;end
 if(state==6)begin mx0=dx;my0=odx;mx1=dy;my1=ody;end
 dax=$signed({2'd0,ca[72:62]})-$signed({2'd0,olda[72:62]});day=$signed({3'd0,ca[82:73]})-$signed({3'd0,olda[82:73]});
 dbx=$signed({2'd0,cb[72:62]})-$signed({2'd0,oldb[72:62]});dby=$signed({3'd0,cb[82:73]})-$signed({3'd0,oldb[82:73]});
 midx={1'b0,ca[72:62]}+cb[72:62];midy={1'b0,ca[82:73]}+cb[82:73];
 guide=midx>=640 && midx<1920 && midy>=360 && midy<1080;
 match=ca[120] && cb[120] && distance>=256 && distance<=360000;
 if(history_valid)begin
 match=match && abs13(dax)<=96 && abs13(day)<=96 && abs13(dbx)<=96 && abs13(dby)<=96 &&
 (product_sum>0) &&
 (distance<<2)>=((old_distance<<1)+old_distance) && ((distance<<1)+distance)<=(old_distance<<2) &&
 {2'd0,ca[61:42]}<=({2'd0,olda[61:42]}<<2) && {2'd0,olda[61:42]}<=({2'd0,ca[61:42]}<<2) &&
 {2'd0,cb[61:42]}<=({2'd0,oldb[61:42]}<<2) && {2'd0,oldb[61:42]}<=({2'd0,cb[61:42]}<<2);
 score=abs13(dax)+abs13(day)+abs13(dbx)+abs13(dby);
 end else begin
 match=match && guide && !expired;
 score=abs13($signed({1'b0,midx})-1280)+abs13($signed({2'd0,midy})-720);
 end
 // Only the best valid diagnostic pair contributes rejection bits. Empty slots
 // cannot turn an unrelated failed pair into a false missing-colour report.
 reject_bits=0;
 if(!ca[120] || !cb[120])reject_bits[0]=1;
 else begin
 reject_bits[2]=distance<256 || distance>360000;
 if(history_valid)begin
 reject_bits[3]=abs13(dax)>96 || abs13(day)>96 || abs13(dbx)>96 || abs13(dby)>96;
 reject_bits[4]=product_sum<=0;
 reject_bits[5]=(distance<<2)<((old_distance<<1)+old_distance) || ((distance<<1)+distance)>(old_distance<<2);
 reject_bits[6]={2'd0,ca[61:42]}>({2'd0,olda[61:42]}<<2) || {2'd0,olda[61:42]}>({2'd0,ca[61:42]}<<2) ||
 {2'd0,cb[61:42]}>({2'd0,oldb[61:42]}<<2) || {2'd0,oldb[61:42]}>({2'd0,cb[61:42]}<<2);
 end else begin reject_bits[1]=!guide;reject_bits[7]=expired;end end

 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
 k_axis<=0;k_negative<=0;k_frozen<=50;k_shift<=0;k_bit<=0;
 k_acc<=0;k_addend<=0;k_number<=0;k_quotient<=0;k_rounded<=0;k_remainder<=0;nt_x<=0;nt_y<=0;
 state<=0;done<=0;a<=0;b<=0;tip_valid<=0;tip_x<=0;tip_y<=0;reason<=0;pair_index<=0;last_id<=0;
 last_command<=0;last_revision<=0;have_id<=0;locked<=0;expired<=0;streak<=0;lost<=0;olda<=0;oldb<=0;
 bestscore<=32'hffffffff;found<=0;fax<=0;fbx<=0;fay<=0;fby<=0;
 product0<=0;product1<=0;distance<=0;old_distance<=0;
 frame_ok<=0;advance<=0;
 best_quality<=0;rejected<=0;chosen_indices<=0;chosen_reason<=0;
 diagnostic_found<=0;diagnostic_score<=32'hffffffff;diagnostic_quality<=0;diagnostic_reject<=0;diagnostic_indices<=0;tip_bounds<=0;
 end else begin
 done<=0;
 case(state)
 0:if(start)begin
 k_frozen<=k_value;
 tip_valid<=0;tip_bounds<=0;a<=single_a;b<=single_b;found<=0;bestscore<=32'hffffffff;pair_index<=0;state<=1;
 diagnostic_found<=0;diagnostic_score<=32'hffffffff;diagnostic_quality<=0;diagnostic_reject<=0;diagnostic_indices<={first_b,first_a};
 best_quality<=0;rejected<=0;chosen_indices<=0;chosen_reason<=0;
 frame_ok<=complete;advance<=1;
 if(!have_id || command!=last_command || revision!=last_revision)begin
 locked<=0;streak<=0;lost<=0;expired<=0;olda<=0;oldb<=0;
 last_id<=frame_id;
 end else if(gap==0 || gap[31])begin
 // A duplicate/backwards result is not a new capture frame and cannot consume
 // the identity deadline or move the last accepted frame backwards.
 frame_ok<=0;advance<=0;streak<=0;
 end else begin
 last_id<=frame_id;
 if(gap!=1)begin
 streak<=0;
 if(locked)begin
 if(gap>=16 || skipped_loss>=15)begin locked<=0;expired<=1;lost<=15;end
 else lost<=skipped_loss[4:0];end end end
 last_command<=command;last_revision<=revision;have_id<=1;
 end
 1:if(!command[0])begin locked<=0;streak<=0;lost<=0;expired<=0;reason<=frame_ok?0:8;a<=0;b<=0;state<=4;end
 else if(!frame_ok)begin
 // A bad observation hides annotations, but does not authorize a new tool.
 streak<=0;reason<=8;a<=0;b<=0;
 if(locked && advance)begin
 if(lost>=14)begin locked<=0;expired<=1;lost<=15;end else lost<=lost+1'b1;end
 state<=4;end
 else begin product0<=mx0*my0;product1<=mx1*my1;state<=7;end
 7:begin old_distance<=product_sum;state<=2;end
 2:begin product0<=mx0*my0;product1<=mx1*my1;state<=8;end
 8:begin distance<=product_sum;state<=6;end
 6:begin product0<=mx0*my0;product1<=mx1*my1;state<=9;end
 9:begin
 if(ca[120] && cb[120] && (!diagnostic_found || score<diagnostic_score || (score==diagnostic_score && pair_quality>diagnostic_quality)))begin
 diagnostic_found<=1;diagnostic_score<=score;diagnostic_quality<=pair_quality;diagnostic_reject<=reject_bits;diagnostic_indices<=pair_index;end
 if(match && (!found || score<bestscore || (score==bestscore && pair_quality>best_quality)))begin
 found<=1;bestscore<=score;best_quality<=pair_quality;
 chosen_indices<=pair_index;chosen_reason<=history_valid?2:1;end
 if(pair_index==15)begin
 // stable_capture holds the published candidate bus through tracker done.
 // Select the existing read port instead of retaining four 128-bit copies.
 if(match && (!found || score<bestscore || (score==bestscore && pair_quality>best_quality)))pair_index<=15;
 else if(found)pair_index<=chosen_indices;
 else if(ca[120] && cb[120] && (!diagnostic_found || score<diagnostic_score || (score==diagnostic_score && pair_quality>diagnostic_quality)))pair_index<=15;
 else pair_index<=diagnostic_indices;
 state<=3;
 end else begin pair_index<=pair_index+1'b1;state<=2;end
 end
 3:begin
 if(found)begin
 a<=ca;b<=cb;olda<=ca;oldb<=cb;lost<=0;
 if(streak<3)streak<=streak+1'b1;
 if(streak==0 || !locked)begin fax<=ca[72:62];fay<=ca[82:73];fbx<=cb[72:62];fby<=cb[82:73];end
 else begin fax<=({1'b0,fax}+ca[72:62]+1)>>1;fay<=({1'b0,fay}+ca[82:73]+1)>>1;
 fbx<=({1'b0,fbx}+cb[72:62]+1)>>1;fby<=({1'b0,fby}+cb[82:73]+1)>>1;end
 if(streak>=2)begin locked<=1;reason<=3;end else reason<=2;
 state<=5;
 end else begin
 a<=diagnostic_found?ca:single_a;b<=diagnostic_found?cb:single_b;
 chosen_indices<=diagnostic_indices;rejected<=diagnostic_found?diagnostic_reject:(!have_a || !have_b)?8'd1:8'd0;
 streak<=0;reason<=expired?6:locked?5:(have_a^have_b)?4:1;
 if(locked)begin if(lost>=14)begin locked<=0;expired<=1;reason<=6;end else lost<=lost+1'b1;end
 state<=4;end end
 // Build N=100*A+k*(A-B), then round the complete signed N/100.
 // Do not round the offset separately: negative half-pixel offsets differ.
 5:begin k_axis<=0;state<=10;end
 10:begin k_acc<={3'd0,k_a,6'd0};state<=11;end
 11:begin k_acc<=k_sum;state<=12;end
 12:begin k_acc<=k_sum;k_addend<={{8{k_delta[11]}},k_delta};k_shift<=k_frozen;k_bit<=0;state<=13;end
 13:begin k_acc<=k_sum;k_addend<=k_addend<<1;k_shift<=k_shift>>1;
 if(k_bit==7)state<=14;else k_bit<=k_bit+1'b1;end
 14:begin k_negative<=k_acc[19];k_number<=k_sum;k_quotient<=0;k_remainder<=0;k_bit<=0;state<=15;end
 15:begin k_number<=k_number<<1;k_quotient<={k_quotient[18:0],k_take};k_remainder<=k_sum[6:0];
 if(k_bit==19)state<=16;else k_bit<=k_bit+1'b1;end
 16:begin k_rounded<=k_sum;state<=17;end
 17:begin
 if(!k_axis)begin nt_x<=k_sum[13:0];k_axis<=1;state<=10;end
 else begin nt_y<=k_sum[13:0];state<=18;end end
 18:begin
 tip_bounds<={nt_y>=720,nt_y<0,nt_x>=1280,nt_x<0};
 if(streak>=3 && nt_x>=0 && nt_x<1280 && nt_y>=0 && nt_y<720)begin tip_valid<=1;tip_x<=nt_x[10:0];tip_y<=nt_y[9:0];end
 else if(streak>=3)reason<=7;
 state<=4;end
 4:begin
 // Output candidate A rank is no longer needed by consumers. Its 28 bits carry
 // an atomic decision diagnostic; geometry, count, quality and validity retain
 // their original offsets. Stored identity still uses untouched ca/cb.
 a[119:92]<={4'd0,tip_bounds,(found?8'd0:rejected),(expired?4'd15:lost[3:0]),streak,
 (found?chosen_reason:((a[120] || b[120])?2'd3:2'd0)),chosen_indices[3:2],chosen_indices[1:0]};
 done<=1;state<=0;end
 endcase end end
endmodule
`default_nettype wire
