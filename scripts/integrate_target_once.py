"""One-time, guarded source integration; kept as a reproducible change recipe."""
from pathlib import Path
import re
r=Path(__file__).resolve().parents[1]
assert 'target_controls u_controls' not in (r/'rtl/00_top_control/criticalwork_top.v').read_text(encoding='utf-8'), 'Already integrated; do not rerun this historical recipe.'
def edit(path,changes):
 p=r/path;s=p.read_text(encoding='utf-8-sig')
 for old,new in changes:
  assert old in s,(path,old[:100]);s=s.replace(old,new,1)
 p.write_text(s,encoding='utf-8')
edit('user_source/hdl_source/isp/isp_top.v',[
('    output [127:0] \tO_tdata', '    output [95:0] O_detect_rgb,\n    output O_detect_sof,O_detect_valid,\n    output [127:0] \tO_tdata'),
('  assign awb_O_tready = O_tready;', '  assign O_detect_rgb=awb_O_tdata;\n  assign O_detect_sof=awb_O_tuser;\n  assign O_detect_valid=awb_O_tvalid;\n  assign awb_O_tready = O_tready;')])
edit('rtl/01_camera/camera_capture.v',[
('    output wire O_capture_clk,', '    output wire [95:0] O_detect_rgb,\n    output wire O_detect_sof,O_detect_valid,\n    output wire O_capture_clk,'),
('isp_top u_isp_top (','isp_top u_isp_top (\n.O_detect_rgb(O_detect_rgb),.O_detect_sof(O_detect_sof),.O_detect_valid(O_detect_valid),')])
edit('user_source/hdl_source/video_in.v',[
('    input wire         I_camera_frame_start,','    input wire         I_camera_frame_start,\n    input wire [31:0] I_camera_frame_id,\n    output wire O_frame_begin,output wire [1:0] O_frame_bank,\n    output wire [31:0] O_frame_id,output wire O_capture_overflow,'),
('    assign S_fifo_rst =', '''    // Observe the SAME start/bank used by the existing writer. The frame ID
    // is bundled with the stretched frame pulse and held for a full frame.
    reg [31:0] camera_id_hold;
    always @(posedge I_camera_clk or negedge I_rst_n)
        if(!I_rst_n) camera_id_hold<=0;
        else if(I_camera_frame_start) camera_id_hold<=I_camera_frame_id;
    assign O_frame_begin=S_frame_start;
    assign O_frame_bank=S_video_in_wp;
    assign O_frame_id=camera_id_hold;
    assign O_capture_overflow=S_fifo_overflow;
    assign S_fifo_rst =''')])
edit('rtl/00_top_control/criticalwork_top.v',[
('wire [10:0] ui_cx;\nwire [9:0] ui_cy;\nwire [1:0] ui_zoom, ui_direction;\nwire [2:0] ui_status;', '''wire [1:0] ui_zoom;
wire ui_tracking,ui_show,ui_conflict;
wire [7:0] ui_session;
wire [95:0] detect_rgb;
wire detect_sof,detect_valid;'''),
('scaling_controls u_controls (','target_controls u_controls ('),
('    .O_gain_req(gain_req), .O_gain_up(gain_up), .O_cx(ui_cx), .O_cy(ui_cy),\n    .O_zoom(ui_zoom), .O_direction(ui_direction), .O_status(ui_status)',
 '    .O_gain_req(gain_req), .O_gain_up(gain_up), .O_zoom(ui_zoom),\n    .O_tracking(ui_tracking),.O_show(ui_show),.O_session(ui_session),.O_conflict(ui_conflict)'),
('    .O_capture_clk(S_csi_rx_clk),','    .O_detect_rgb(detect_rgb),.O_detect_sof(detect_sof),.O_detect_valid(detect_valid),\n    .O_capture_clk(S_csi_rx_clk),'),
('    .I_cx(ui_cx), .I_cy(ui_cy), .I_zoom(ui_zoom), .I_direction(ui_direction), .I_ui_status(ui_status),',
 '    .I_zoom(ui_zoom),.I_tracking(ui_tracking),.I_show(ui_show),.I_session(ui_session),.I_conflict(ui_conflict),\n    .I_detect_rgb(detect_rgb),.I_detect_sof(detect_sof),.I_detect_valid(detect_valid),')])
# Dedicated reader preserves original ScalingTest sources/tests/outputs.
p=r/'rtl/05_roi_processing/scaling_line_reader.v';s=p.read_text(encoding='utf-8')
s=s.replace('module scaling_line_reader (','module target_line_reader (')
s=s.replace('    input wire I_rst_n,','    input wire I_frame_commit,I_selected_good,\n    input wire I_rst_n,',1)
s=s.replace('    reg vs1, vs2, vs3;', '''    reg vs1, vs2, vs3;
    reg commit1,commit2;
    (* async_reg="true", syn_preserve=1 *) reg live1,live2;''')
s=s.replace('wire frame_start=vs2&&!vs3;', 'wire frame_start=commit2;')
s=s.replace('    wire good=frame_live && !abort_frame && (hit0||hit1);','    wire good=frame_live && !abort_frame && live2 && (hit0||hit1);')
s=s.replace('frame_live<=0; abort_frame<=1; vs1<=0; vs2<=0; vs3<=0;', 'frame_live<=0; abort_frame<=1; vs1<=0; vs2<=0; vs3<=0;commit1<=0;commit2<=0;live1<=0;live2<=0;')
s=s.replace('ack1<=ack_toggle; ack2<=ack1; vs1<=I_vs; vs2<=vs1; vs3<=vs2;', '''ack1<=ack_toggle; ack2<=ack1; vs1<=I_vs; vs2<=vs1; vs3<=vs2;
            commit1<=I_frame_commit;commit2<=commit1;live1<=I_selected_good;live2<=live1;
            if(vs2&&!vs3) begin abort_frame<=1;frame_live<=0;end
            if(frame_live&&!live2) abort_frame<=1;''')
s=s.replace('O_video_ok<=frame_live && !abort_frame;', 'O_video_ok<=frame_live && !abort_frame && live2;')
(r/'rtl/05_roi_processing/target_line_reader.v').write_text(s,encoding='utf-8')
p=r/'rtl/10_memory_video_out/memory_video_out.v';s=p.read_text(encoding='utf-8')
s=s.replace('    input wire [10:0] I_cx, input wire [9:0] I_cy,\n    input wire [1:0] I_zoom, I_direction, input wire [2:0] I_ui_status,', '''    input wire [1:0] I_zoom,
    input wire I_tracking,I_show,I_conflict,input wire [7:0] I_session,
    input wire [95:0] I_detect_rgb,input wire I_detect_sof,I_detect_valid,''')
s=s.replace('video_in u_video_in(','''wire write_frame_begin,capture_overflow;
wire [1:0] write_frame_bank;
wire [31:0] write_frame_id,capture_frame_id;
video_in u_video_in(''')
s=s.replace('        .I_camera_frame_start ( S_ISP_O_tuser  ),','''        .I_camera_frame_start ( S_ISP_O_tuser  ),
        .I_camera_frame_id(capture_frame_id),.O_frame_begin(write_frame_begin),
        .O_frame_bank(write_frame_bank),.O_frame_id(write_frame_id),.O_capture_overflow(capture_overflow),''')
start=s.index('    wire [10:0] active_cx, roi_x, cross_x;');end=s.index('    mc_to_user_interface',start)
s=s[:start]+'''    wire [10:0] active_cx,roi_x;
    wire [9:0] active_cy,roi_y;
    wire [1:0] active_zoom,frame_mode,selected_bank;
    wire [2:0] active_status;
    wire [31:0] selected_frame_id;
    wire [255:0] active_meta;
    wire active_show,tip_valid,video_ok,frame_commit,selected_good;
    (* async_reg="true", syn_preserve=1 *) reg [1:0] capture_reset,ddr_reset;
    wire capture_rst_n=capture_reset[1],ddr_rst_n=ddr_reset[1];
    always @(posedge I_capture_clk or negedge I_rst_n)
        if(!I_rst_n) capture_reset<=0;else capture_reset<={capture_reset[0],1'b1};
    always @(posedge S_ddr_clk or negedge I_rst_n)
        if(!I_rst_n) ddr_reset<=0;else ddr_reset<={ddr_reset[0],1'b1};
    // Control-session bundle prevents results from a previous enable cycle
    // from reappearing after rapid stop/restart.
    wire command_ready,command_valid;
    wire [8:0] command_data;
    reg [8:0] command_sent,command_active;
    wire [8:0] command_now={I_session,I_tracking};
    wire command_send=command_now!=command_sent && command_ready;
    always @(posedge I_pixel_clk or negedge I_process_rst_n)
        if(!I_process_rst_n) command_sent<=0;else if(command_send) command_sent<=command_now;
    always @(posedge I_capture_clk or negedge capture_rst_n)
        if(!capture_rst_n) command_active<=0;else if(command_valid) command_active<=command_data;
    target_mailbox #(.WIDTH(9)) u_command(
        .S_clk(I_pixel_clk),.S_rst_n(I_process_rst_n),.S_send(command_send),.S_data(command_now),.S_ready(command_ready),
        .D_clk(I_capture_clk),.D_rst_n(capture_rst_n),.D_valid(command_valid),.D_data(command_data));
    wire capture_result,ddr_result,result_ready;
    wire [255:0] capture_meta,ddr_meta;
    target_capture_pipeline u_detection(
        .I_clk(I_capture_clk),.I_rst_n(capture_rst_n),.I_sof(I_detect_sof),.I_valid(I_detect_valid),
        .I_fault(capture_overflow),.I_rgb(I_detect_rgb),.I_enable(command_active[0]),.I_session(command_active[8:1]),
        .O_frame_id(capture_frame_id),.O_valid(capture_result),.O_meta(capture_meta));
    target_mailbox u_results(
        .S_clk(I_capture_clk),.S_rst_n(capture_rst_n),.S_send(capture_result),.S_data(capture_meta),.S_ready(result_ready),
        .D_clk(S_ddr_clk),.D_rst_n(ddr_rst_n),.D_valid(ddr_result),.D_data(ddr_meta));
    // At every display VS request an atomic bank/generation/result snapshot.
    reg vs_last;
    always @(posedge I_pixel_clk or negedge I_process_rst_n)
        if(!I_process_rst_n) vs_last<=0;else vs_last<=S_hdmi_vsync;
    wire snap_request_ready,snap_request,unused_request;
    target_mailbox #(.WIDTH(1)) u_snapshot_request(
        .S_clk(I_pixel_clk),.S_rst_n(I_process_rst_n),.S_send(S_hdmi_vsync&&!vs_last),.S_data(1'b1),.S_ready(snap_request_ready),
        .D_clk(S_ddr_clk),.D_rst_n(ddr_rst_n),.D_valid(snap_request),.D_data(unused_request));
    wire snapshot_ready,store_snapshot,pixel_snapshot;
    wire [290:0] store_data,pixel_data;
    target_frame_store u_frame_store(
        .I_clk(S_ddr_clk),.I_rst_n(ddr_rst_n),.I_begin(write_frame_begin),.I_bank(write_frame_bank),.I_frame_id(write_frame_id),
        .I_write(S_vi_ddr_wr_en),.I_addr(S_vi_ddr_wr_addr),.I_result(ddr_result),.I_meta(ddr_meta),
        .I_snapshot(snap_request),.I_read_bank(S_video_out_rp),.O_snapshot(store_snapshot),.O_data(store_data),.O_selected_good(selected_good));
    target_mailbox #(.WIDTH(291)) u_snapshot_response(
        .S_clk(S_ddr_clk),.S_rst_n(ddr_rst_n),.S_send(store_snapshot),.S_data(store_data),.S_ready(snapshot_ready),
        .D_clk(I_pixel_clk),.D_rst_n(I_process_rst_n),.D_valid(pixel_snapshot),.D_data(pixel_data));
    target_display u_viewport(
        .I_clk(I_pixel_clk),.I_rst_n(I_process_rst_n),.I_vs(S_hdmi_vsync),.I_de(S_hdmi_de),
        .I_snapshot(pixel_snapshot),.I_data(pixel_data),.I_tracking(I_tracking),.I_show(I_show),.I_conflict(I_conflict),
        .I_live(video_ok),.I_session(I_session),.I_zoom(I_zoom),.I_mode(I_process_mode),
        .O_commit(frame_commit),.O_bank(selected_bank),.O_frame_id(selected_frame_id),
        .O_cx(active_cx),.O_cy(active_cy),.O_x0(roi_x),.O_y0(roi_y),.O_zoom(active_zoom),.O_mode(frame_mode),
        .O_meta(active_meta),.O_show(active_show),.O_tip_valid(tip_valid),.O_state(active_status));
    target_line_reader u_scaler (
        .I_frame_commit(frame_commit),.I_selected_good(selected_good),
        .I_rst_n(S_rst_n), .I_ddr_clk(S_ddr_clk),
        .I_write_busy(S_video_in_wr_busy), .I_write_en(S_vi_ddr_wr_en), .I_read_buffer(selected_bank),
        .I_ddr_ready(S_ddr_user_ready && S_init_calib_complete), .I_ddr_valid(S_ddr_user_rd_valid),
        .I_ddr_data(S_ddr_user_rd_data), .O_read_busy(S_video_out_rd_busy),
        .O_read_en(S_vo_ddr_rd_en), .O_read_addr(S_vo_ddr_rd_addr),
        .I_pixel_clk(S_hdmi_pixel_clk), .I_vs(S_hdmi_vsync), .I_hs(S_hdmi_hsync), .I_de(S_hdmi_de),
        .I_x0(roi_x), .I_y0(roi_y), .I_zoom(active_zoom),
        .O_vs(S_hdmi_out_vsync), .O_hs(S_hdmi_out_hsync), .O_de(S_hdmi_out_de),
        .O_rgb(S_hdmi_out_data), .O_video_ok(video_ok)
    );

'''+s[end:]
s=s.replace('.I_mode_pending(I_process_mode)', '.I_mode_pending(frame_mode)')
start=s.index('    scaling_osd u_osd (');end=s.index('    hdmi_tx u_hdmi_tx',start)
s=s[:start]+'''    target_osd u_osd (
        .I_clk(S_hdmi_pixel_clk),.I_rst_n(I_process_rst_n),
        .I_vs(process_vs),.I_hs(process_hs),.I_de(process_de),.I_rgb(process_rgb),
        .I_meta(active_meta),.I_x0(roi_x),.I_y0(roi_y),.I_zoom(active_zoom),.I_mode(actual_mode),
        .I_state(active_status),.I_show(active_show),.I_tip_valid(tip_valid),.I_video_ok(video_ok),
        .O_vs(osd_vs),.O_hs(osd_hs),.O_de(osd_de),.O_rgb(osd_rgb)
    );
'''+s[end:]
# Commit arrives after VS; the algorithm's VS latch must see the user's mode
# at the original VS, while the metadata/ROI use the same stable debounce value.
s=s.replace('.I_mode_pending(frame_mode)', '.I_mode_pending(I_process_mode)')
p.write_text(s,encoding='utf-8')
al=(r/'td_project/scaling_test.al').read_text(encoding='utf-8').replace('scaling_test','target_lock')
for old,new in [('00_top_control/scaling_controls.v','00_top_control/target_controls.v'),('00_top_control/scaling_viewport.v','04_tracking/target_display.v'),('05_roi_processing/scaling_line_reader.v','05_roi_processing/target_line_reader.v'),('09_osd_ui/scaling_osd.v','09_osd_ui/target_osd.v'),('09_osd_ui/scaling_glyph_rom.v','09_osd_ui/target_glyph_rom.v')]:al=al.replace(old,new)
add=['03_tool_detection/target_detector.v','04_tracking/target_tracker.v','04_tracking/target_capture_pipeline.v','04_tracking/target_mailbox.v','04_tracking/target_frame_store.v']
al=al.replace('        <Verilog>','        <Verilog>\n'+'\n'.join(f'            <File Path="../rtl/{f}"><FileInfo><Attr Name="UsedInSyn" Val="true"/><Attr Name="UsedInP&amp;R" Val="true"/><Attr Name="BelongTo" Val="design_1"/><Attr Name="CompileOrder" Val="{120+i}"/></FileInfo></File>' for i,f in enumerate(add)))
# Match the vendor XML spelling used by TD (existing files use a literal &).
al=al.replace('UsedInP&amp;R','UsedInP&R')
(r/'td_project/target_lock.al').write_text(al,encoding='utf-8')
for ext in ['adc','sdc']:(r/f'td_project/target_lock.{ext}').write_bytes((r/f'td_project/scaling_test.{ext}').read_bytes())
s=(r/'scripts/build_scaling_test.tcl').read_text().replace('scaling_test','target_lock').replace('SCALING_TEST_BUILD_COMPLETED','TARGET_LOCK_BUILD_COMPLETED')
(r/'scripts/build_target_lock.tcl').write_text(s,encoding='utf-8')
print('Target topology integrated; original scaling modules and build outputs retained.')
