// Adapted from the supplied SC500 Lab1 design_top_wrapper.v.
// Vendor modules retain their original notices under user_source/.
// FHD profile: native DPHY/CSI/RAW byte-clock domain, whole-line admission,
// and a separate 60 MHz ISP/detection/packing domain. Physical operation still
// requires the independent FHD build and board acceptance.
`default_nettype none
module native_camera_capture #(parameter TIMING=0)(
    input wire [11:0] I_gain_r,I_gain_b,
    output wire [95:0] O_raw_rgb,output wire O_raw_sof,O_raw_valid,
    input wire I_control_clk, input wire I_camera_ref_clk, input wire I_processing_clk,
    input wire I_rst_n, input wire I_gain_req, I_gain_up, output wire O_gain_ack,
    output wire O_cam_scl, inout wire IO_cam_sda,
    output wire O_cam_24m, output wire O_cam_rst,
    inout wire IO_rx_clk_pad_n, inout wire IO_rx_clk_pad_p,
    inout wire [3:0] IO_rx_data_pad_n, inout wire [3:0] IO_rx_data_pad_p,
    output wire [95:0] O_detect_rgb,
    output wire O_detect_sof,O_detect_valid,
    output wire O_capture_clk, output wire [127:0] O_rgb128,
    output wire O_data_valid, output wire O_frame_start,
    output wire [3:0] O_status_async,
    output wire O_parameter_event,O_camera_ready,output wire [3:0] O_camera_fault,
    output wire [1:0] O_camera_retries,output wire [3:0] O_camera_phase,output wire [6:0] O_camera_gain,
    input wire [31:0] I_time_gray,output wire [31:0] O_source_id,O_source_us,O_now_us,O_latest_gray,
    output wire O_time_valid,
    input wire I_verdict_ready,output wire O_source_verdict,O_source_good,
    output wire [31:0] O_verdict_id
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
wire cfg_rst_n,receiver_enable,control_rst_n,capture_rst_n,processing_rst_n;
wire bridge_abort;wire isp_rst_n=processing_rst_n && !bridge_abort;
(* async_reg="true" *) reg [1:0] ready_capture;
wire [32:0] axis_tag,raw_tag,detect_tag;wire raw_known,detect_known;
wire [31:0] bridge_source_id,bridge_source_us,rx_now_us;
reg [31:0] source_sequence,source_us,latest_gray;
reg [31:0] ids[0:3],stamps[0:3];reg [3:0] known;
wire [31:0] next_source_id=source_sequence+1'b1;
assign O_latest_gray=latest_gray;
refined_gray_sync rx_time(S_csi_rx_clk,I_rst_n,I_time_gray,rx_now_us);
refined_gray_sync processing_time(I_processing_clk,I_rst_n,I_time_gray,O_now_us);
always @(posedge S_csi_rx_clk or negedge I_rst_n)
if(!I_rst_n)begin source_sequence<=0;source_us<=0;latest_gray<=0;end
else if(S_csi_frame_start)begin source_sequence<=next_source_id;source_us<=rx_now_us;latest_gray<=next_source_id^(next_source_id>>1);end
assign axis_tag={1'b1,bridge_source_id};
assign raw_known=raw_tag[32] && known[raw_tag[1:0]] && ids[raw_tag[1:0]]==raw_tag[31:0];
assign detect_known=detect_tag[32] && known[detect_tag[1:0]] && ids[detect_tag[1:0]]==detect_tag[31:0];
assign O_source_id=detect_tag[31:0];assign O_time_valid=detect_known;
assign O_source_us=stamps[detect_tag[1:0]];
always @(posedge I_processing_clk or negedge processing_rst_n)
if(!processing_rst_n)known<=0;
else if(bridge_abort)known<=0;
else if(S_axis_tuser)begin known[bridge_source_id[1:0]]<=1;ids[bridge_source_id[1:0]]<=bridge_source_id;stamps[bridge_source_id[1:0]]<=bridge_source_us;end
wire [95:0] raw_rgb_internal,detect_rgb_internal;
wire raw_sof_internal,raw_valid_internal,detect_sof_internal,detect_valid_internal;
wire complete_toggle,bad_toggle;reg forward_frame,detect_forward;
refined_reset_bridge cfg_reset(S_24m_clk,I_rst_n,cfg_rst_n);
refined_reset_bridge rx_control_reset(S_100m_clk,I_rst_n && receiver_enable,control_rst_n);
refined_reset_bridge rx_data_reset(S_csi_rx_clk,I_rst_n && receiver_enable,capture_rst_n);
refined_reset_bridge processing_reset(I_processing_clk,I_rst_n && receiver_enable,processing_rst_n);
assign S_100m_clk=I_control_clk;assign S_24m_clk=I_camera_ref_clk;assign S_rst_n=I_rst_n;
assign O_cam_rst=1'b1;assign O_cam_24m=S_24m_clk;assign O_capture_clk=I_processing_clk;
assign O_rgb128=S_ISP_O_tdata;
assign O_data_valid=S_ISP_O_tvalid && forward_frame && ready_capture[1];
assign O_frame_start=S_ISP_O_tuser && forward_frame && ready_capture[1];
assign O_raw_rgb=raw_rgb_internal;assign O_detect_rgb=detect_rgb_internal;
assign O_raw_sof=raw_sof_internal && ready_capture[1] && (!TIMING || raw_known);
assign O_raw_valid=raw_valid_internal && ready_capture[1] && (raw_sof_internal?(!TIMING || raw_known):forward_frame);
assign O_detect_sof=detect_sof_internal && forward_frame && ready_capture[1] && (!TIMING || detect_known);
assign O_detect_valid=detect_valid_internal && forward_frame && ready_capture[1] && (detect_sof_internal?(!TIMING || detect_known):detect_forward);
camera_status u_status(.I_cfg_clk(S_24m_clk),.I_rx_clk(S_csi_rx_clk),.I_rst_n(S_rst_n),
 .I_cfg_done(S_cam_cfg_done),.I_hs_valid(S_hs_rx_valid),.I_csi_valid(S_csi_valid),.I_frame_start(S_csi_frame_start),.O_status_async(O_status_async));
native_camera_config u_config(.clk(S_24m_clk),.rst_n(cfg_rst_n),.gain_req(I_gain_req),.gain_up(I_gain_up),
 .frame_toggle(complete_toggle),.bad_frame_toggle(bad_toggle),.gain_ack(O_gain_ack),.scl(O_cam_scl),.sda(IO_cam_sda),
 .ready(O_camera_ready),.receiver_enable(receiver_enable),.parameter_event(O_parameter_event),
 .fault(O_camera_fault),.retries(O_camera_retries),.phase(O_camera_phase),.requested_gain(),.applied_gain(O_camera_gain));
assign S_cam_cfg_done=O_camera_ready;
wire source_verdict,source_good;wire [31:0] source_verdict_id;
wire full_sof,full_valid;wire [32:0] full_tag;
native_source_gate full_frame_gate(.clk(I_processing_clk),.rst_n(processing_rst_n),
 .begin_frame(S_axis_tuser),.begin_id(bridge_source_id),
 .verdict(source_verdict),.verdict_good(source_good),.verdict_id(source_verdict_id),
 .full_sof(full_sof),.full_valid(full_valid),.full_tag(full_tag),
 .output_ready(I_verdict_ready),.output_valid(O_source_verdict),.output_good(O_source_good),
 .output_id(O_verdict_id),.good_toggle(complete_toggle),.bad_toggle(bad_toggle));
always @(posedge I_processing_clk or negedge processing_rst_n)begin
 if(!processing_rst_n)begin ready_capture<=0;forward_frame<=0;detect_forward<=0;end
 else begin
  ready_capture<={ready_capture[0],O_camera_ready};
  if(!ready_capture[1])begin forward_frame<=0;detect_forward<=0;end
  else begin
   if(raw_sof_internal)forward_frame<=!TIMING || raw_known;
   if(detect_sof_internal)detect_forward<=forward_frame && (!TIMING || detect_known);
  end
  if(bridge_abort)begin forward_frame<=0;detect_forward<=0;end
 end
end
wire S_csi_hs;reg csi_hs_old,csi_line_seen;reg [7:0] line_tail;
// CSI long-packet completion is delayed beyond the RAW unpack pipeline. Short
// SOF/EOF packets cannot generate an EOL. Internal RAW valid gaps are ignored.
always @(posedge S_csi_rx_clk or negedge capture_rst_n)
if(!capture_rst_n)begin csi_hs_old<=0;csi_line_seen<=0;line_tail<=0;end
else begin
 csi_hs_old<=S_csi_hs;line_tail<={line_tail[6:0],csi_hs_old && !S_csi_hs && csi_line_seen};
 if(S_csi_valid)csi_line_seen<=1;
 if(csi_hs_old && !S_csi_hs)csi_line_seen<=0;
end
    mipi_dphy_rx_ph1p_mipiio_wrapper#(
        .DPHY_RX_LOCATION      ( "DPHY0" ),
        .HS_EQUALIZER          ( "0dB"   ),
        .HS_VGA_GAIN           ( "8dB" ),
        .LANE_NUM              ( 2       ),
        .BYTE_NUM              ( 1       )
    )u_mipi_dphy_rx_ph1p_mipiio_wrapper(
        .I_lp_clk              ( S_100m_clk       ),
        .I_rst                 ( ~control_rst_n   ),

        .I_clk_lane_in_delay   ( 6'd0             ),
        .I_data_lane0_in_delay ( 6'd0             ),
        .I_data_lane1_in_delay ( 6'd0             ),
        .I_data_lane2_in_delay ( 6'd0             ),
        .I_data_lane3_in_delay ( 6'd0             ),

        .I_lane_invert         ( 2'b00            ),
     
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
.I_rst_n               ( capture_rst_n  	),
.I_hs_valid            ( S_hs_rx_valid     ),
.I_hs_data             ( S_hs_rx_data      ),

.O_csi_frame_start     ( S_csi_frame_start ),
.O_csi_frame_end       ( S_csi_frame_end   ),
.O_csi_valid           ( S_csi_valid       ),
.O_csi_hs              ( S_csi_hs          ),
.O_csi_data            ( S_csi_data        )
);

raw10_unpacket_2lane u_raw10_unpacket (
.I_clk  (S_csi_rx_clk),
.I_rst_n(capture_rst_n),

.I_csi_frame_start(S_csi_frame_start),
.I_csi_frame_end  (S_csi_frame_end),
.I_csi_valid      (S_csi_valid),
.I_csi_data       (S_csi_data),

.O_raw10_frame_start(S_raw10_frame_start),
.O_raw10_frame_end  (S_raw10_frame_end),
.O_raw10_valid      (S_raw10_valid),
.O_raw10_data       (S_raw10_data)
  );

wire packet_error,checked_eof;
native_csi_guard packet_guard(.clk(S_csi_rx_clk),.rst_n(capture_rst_n),
 .valid(S_hs_rx_valid),.data(S_hs_rx_data),.lane_error(|S_lane_error),
 .packet_error(packet_error),.frame_end(checked_eof));
native_raw_bridge u_raw_bridge(
 .I_rx_clk(S_csi_rx_clk),.I_processing_clk(I_processing_clk),.I_rst_n(I_rst_n && receiver_enable),
 .I_sof(S_raw10_frame_start),.I_eof(checked_eof),.I_packet_error(packet_error),.I_valid(S_raw10_valid),.I_line_end(line_tail[7]),
 .I_data(S_raw10_data),.I_source_id(source_sequence),.I_source_us(source_us),
 .O_data(S_axis_tdata),.O_valid(S_axis_tvalid),.O_sof(S_axis_tuser),.O_last(S_axis_tlast),.O_abort(bridge_abort),
 .O_source_id(bridge_source_id),.O_source_us(bridge_source_us),.O_overflows(),.O_bad_lines(),
 .O_verdict(source_verdict),.O_good(source_good),.O_verdict_id(source_verdict_id));

assign S_raw_tdata  = S_axis_tdata;
assign S_raw_tvalid = S_axis_tvalid;
assign S_raw_tlast  = S_axis_tlast;
assign S_raw_tuser  = S_axis_tuser;

native_isp #(.CROP_X(16),.CROP_Y(252)) u_isp_top(.clk(I_processing_clk),.rst_n(isp_rst_n),.abort_frame(bridge_abort),
 .sof(S_axis_tuser),.last(S_axis_tlast),.valid(S_axis_tvalid),.data(S_axis_tdata),
 .frame_tag(axis_tag),.gain_r(I_gain_r),.gain_b(I_gain_b),
 .raw_sof(raw_sof_internal),.raw_valid(raw_valid_internal),.raw_rgb(raw_rgb_internal),.raw_tag(raw_tag),
 .detect_sof(detect_sof_internal),.detect_valid(detect_valid_internal),.detect_rgb(detect_rgb_internal),.detect_tag(detect_tag),
 .rgb_sof(S_ISP_O_tuser),.rgb_valid(S_ISP_O_tvalid),.rgb128(S_ISP_O_tdata),
 .full_sof(full_sof),.full_valid(full_valid),.full_tag(full_tag));
endmodule
`default_nettype wire
