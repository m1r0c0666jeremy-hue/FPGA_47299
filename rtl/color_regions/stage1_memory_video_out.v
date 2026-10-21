// Adapted from the supplied SC500 Lab1 design_top_wrapper.v.
// Vendor modules retain their original notices under user_source/.
// This wrapper preserves the reference datapath, packing, clocks and reset policy.
// Pin compatibility and physical camera/display operation remain unverified.
`default_nettype none
module stage1_memory_video_out #(parameter integer DEBUG_MODE = 0) (
    input wire [1:0] I_ui_mode,input wire I_key_down2,I_key2,I_key3,I_key4,I_key_cancel,
    input wire I_gain_busy,I_gain_failed,input wire [2:0] I_gain_slot,output wire O_area_alarm,
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
    wire [767:0] active_meta;
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
    wire [9:0] command_data;
    reg [9:0] command_sent,command_active;
    wire [9:0] command_now={I_pair,I_session,I_tracking};
    wire command_send=command_now!=command_sent && command_ready;
    always @(posedge I_pixel_clk or negedge stream_pixel_n)
        if(!stream_pixel_n) command_sent<=0;else if(command_send) command_sent<=command_now;
    always @(posedge I_capture_clk or negedge capture_rst_n)
        if(!capture_rst_n) command_active<=0;else if(command_valid) command_active<=command_data;
    target_mailbox #(.WIDTH(10)) u_command(
        .S_clk(I_pixel_clk),.S_rst_n(stream_pixel_n),.S_send(command_send),.S_data(command_now),.S_ready(command_ready),
        .D_clk(I_capture_clk),.D_rst_n(capture_rst_n),.D_valid(command_valid),.D_data(command_data));
    wire capture_result,ddr_result,result_ready;
    wire [767:0] capture_meta,ddr_meta;
    stable_capture #(.V4(1)) u_detection(
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
        .S_clk(I_pixel_clk),.S_rst_n(stream_pixel_n),.S_send(S_hdmi_vsync&&!vs_last && snap_request_ready),.S_data(command_now),.S_ready(snap_request_ready),
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
    stable_display #(.V4(1)) u_viewport(
        .O_image_us(image_us),.O_epoch(image_epoch),.O_time_valid(image_time_valid),
        .I_rotate(rotate_at_vs),.O_rotate(active_rotate),
        .I_clk(I_pixel_clk),.I_rst_n(stream_pixel_n),.I_vs(S_hdmi_vsync),.I_de(S_hdmi_de),
        .I_pair(I_pair),.O_pair(active_pair),.I_snapshot(pixel_snapshot),.I_data(pixel_data),.I_tracking(I_tracking),.I_show(I_show),.I_conflict(I_conflict),
        .I_live(video_ok && I_camera_ready && stream_pixel_n),.I_session(I_session),.I_zoom(zoom_at_vs),.I_mode(mode_at_vs),
        .O_commit(frame_commit),.O_bank(selected_bank),.O_frame_id(selected_frame_id),
        .O_cx(active_cx),.O_cy(active_cy),.O_x0(roi_x),.O_y0(roi_y),.O_zoom(active_zoom),.O_mode(frame_mode),
        .O_detection_valid(detection_valid),.O_meta(active_meta),.O_show(active_show),.O_sample_valid(sample_valid),.O_state(active_status));
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
    wire [2:0] area_count,area_expected,area_actual;wire [3:0] area_draft,area_state,area_completed,area_occupied,area_closed,area_edit_error,area_start_error;
    wire [15:0] area_revision,area_counts;wire [671:0] area_vertices;wire area_muted,area_busy,area_tip,area_metrics_valid;
    wire [1:0] area_trend;wire [10:0] area_distance;wire [19:0] area_dwell;
    stage1_regions area_controller(.clk(I_pixel_clk),.rst_n(I_process_rst_n),.mode(I_ui_mode),.down2(I_key_down2),.click2(I_key2),.click3(I_key3),.click4(I_key4),.cancel(I_key_cancel),
     .tracking(I_tracking),.video_ok(video_ok && stream_pixel_n),.camera_ready(I_camera_ready),.gain_busy(I_gain_busy),.session(I_session),.pair(I_pair),
     .frame_commit(frame_commit),.detection_valid(detection_valid),.image_id(selected_frame_id),.meta(active_meta),
     .region_count(area_count),.draft_count(area_draft),.revision(area_revision),.render_vertices(area_vertices),.render_counts(area_counts),.closed_mask(area_closed),
     .run_state(area_state),.completed(area_completed),.occupied(area_occupied),.expected_area(area_expected),.actual_area(area_actual),.muted(area_muted),.alarm(O_area_alarm),
     .trend(area_trend),.distance(area_distance),.dwell_ms(area_dwell),.edit_error(area_edit_error),.start_error(area_start_error),.busy(area_busy),.tip_live(area_tip),.metrics_valid(area_metrics_valid));
    stage1_osd u_osd (
     .I_ui_mode(I_ui_mode),.I_region_vertices(area_vertices),.I_region_counts(area_counts),.I_region_closed(area_closed),
     .I_area_count(area_count),.I_draft_count(area_draft),.I_run_state(area_state),.I_completed(area_completed),.I_occupied(area_occupied),
     .I_expected_area(area_expected),.I_actual_area(area_actual),.I_area_muted(area_muted),.I_area_trend(area_trend),.I_area_distance(area_distance),.I_area_dwell(area_dwell),
     .I_edit_error(area_edit_error),.I_start_error(area_start_error),.I_area_busy(area_busy || (area_tip && area_count!=0 && !area_metrics_valid)),.I_tip_live(area_tip),
     .I_gain_busy(I_gain_busy),.I_gain_failed(I_gain_failed),.I_gain_slot(I_gain_slot),
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
