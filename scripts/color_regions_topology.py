"""Functional source whitelist. Originals and vendor IP remain byte-for-byte intact."""
from pathlib import Path
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
def replace(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def assets(cfg):
    out={}
    s=(R/'rtl/05_roi_processing/target_line_reader.v').read_text(encoding='utf-8')
    s=replace(s,'module target_line_reader (','module regions_line_reader (')
    s=replace(s,'input wire [1:0] I_read_buffer,','input wire [1:0] I_read_buffer, input wire [31:0] I_frame_id,')
    s=replace(s,'reg req_toggle, req_bank, req_first;', '''reg req_toggle, req_bank, req_first;
    reg [1:0] image_bank,req_image_bank;
    reg [31:0] image_id,req_image_id;
    (* syn_preserve=1 *) reg [31:0] frame_id_d;''')
    s=replace(s,'frame_base<=0; line_base<=0; sent<=0; received<=0;','frame_base<=0; frame_id_d<=0; line_base<=0; sent<=0; received<=0;')
    s=replace(s,'if(req_first) frame_base<=base_for(I_read_buffer);','if(req_first) begin frame_base<=base_for(req_image_bank);frame_id_d<=req_image_id;end')
    s=replace(s,'(req_first?base_for(I_read_buffer):frame_base)','(req_first?base_for(req_image_bank):frame_base)')
    s=replace(s,'req_y<=0; req_first<=0; req_epoch<=0; epoch<=0;','req_y<=0; req_first<=0; req_epoch<=0; epoch<=0;image_bank<=0;req_image_bank<=0;image_id<=0;req_image_id<=0;')
    s=replace(s,'req_first<=first_line; req_epoch<=epoch;','req_first<=first_line; req_epoch<=epoch;req_image_bank<=image_bank;req_image_id<=image_id;')
    s=replace(s,'x<=0; y<=0; x0<=I_x0; y0<=I_y0; zoom<=I_zoom;','x<=0; y<=0; x0<=I_x0; y0<=I_y0; zoom<=I_zoom;image_bank<=I_read_buffer;image_id<=I_frame_id;')
    out['rtl/color_regions/regions_line_reader.v']=s
    s=(R/'rtl/10_memory_video_out/memory_video_out.v').read_text(encoding='utf-8')
    s=replace(s,'module memory_video_out #','module regions_memory_video_out #')
    s=s.replace('[255:0]','[415:0]').replace('[290:0]','[450:0]')
    s=replace(s,'wire detection_valid;','wire detection_valid,sample_valid;')
    params=','.join(f'.{k.upper()}({cfg[k]})' for k in ('tile_min','support_min','area_min','padding','confirm','max_step'))
    s=replace(s,'target_capture_pipeline u_detection(',f'regions_capture #({params}) u_detection(')
    s=replace(s,'.O_frame_id(capture_frame_id),.O_valid(capture_result),.O_meta(capture_meta)', '.I_result_ready(result_ready),.O_dropped(),.O_frame_id(capture_frame_id),.O_valid(capture_result),.O_meta(capture_meta)')
    s=replace(s,'target_mailbox u_results(','target_mailbox #(.WIDTH(416)) u_results(')
    s=replace(s,'reg [1:0] mode_at_vs;','reg [1:0] mode_at_vs,zoom_at_vs;')
    s=replace(s,'begin vs_last<=0;mode_at_vs<=0;end','begin vs_last<=0;mode_at_vs<=0;zoom_at_vs<=0;end')
    s=replace(s,'if(S_hdmi_vsync&&!vs_last) mode_at_vs<=I_process_mode;', 'if(S_hdmi_vsync&&!vs_last) begin mode_at_vs<=I_process_mode;zoom_at_vs<=I_zoom;end ')
    s=replace(s,'wire snap_request_ready,snap_request,unused_request;', 'wire snap_request_ready,snap_request;wire [9:0] snapshot_command;')
    s=replace(s,'target_mailbox #(.WIDTH(1)) u_snapshot_request(', 'target_mailbox #(.WIDTH(10)) u_snapshot_request(')
    s=replace(s,".S_send(S_hdmi_vsync&&!vs_last),.S_data(1'b1)",'.S_send(S_hdmi_vsync&&!vs_last && snap_request_ready),.S_data(command_now)')
    s=replace(s,'.D_data(unused_request)','.D_data(snapshot_command)')
    s=replace(s,'target_frame_store u_frame_store(','regions_frame_store u_frame_store(')
    s=replace(s,'.I_snapshot(snap_request),.I_read_bank(S_video_out_rp)', '.I_snapshot(snap_request && snapshot_ready),.I_command(snapshot_command)')
    s=replace(s,'target_mailbox #(.WIDTH(291))','target_mailbox #(.WIDTH(451))')
    s=replace(s,'target_display u_viewport(','regions_display u_viewport(')
    s=replace(s,'.I_zoom(I_zoom),.I_mode(mode_at_vs)', '.I_zoom(zoom_at_vs),.I_mode(mode_at_vs)')
    s=replace(s,'.O_tip_valid(tip_valid)', '.O_sample_valid(sample_valid)')
    s=replace(s,'target_line_reader u_scaler (','regions_line_reader u_scaler (')
    s=replace(s,'.I_read_buffer(selected_bank)', '.I_read_buffer(selected_bank),.I_frame_id(selected_frame_id)')
    s=replace(s,'image_preprocess u_image_preprocess (','regions_preprocess u_image_preprocess (')
    s=replace(s,'.I_mode_pending(mode_at_vs)', '.I_mode(frame_mode),.I_pair(active_pair)')
    s=replace(s,'.O_mode_active(actual_mode)', '.O_mode(actual_mode)')
    s=replace(s,'target_osd u_osd (','regions_osd u_osd (')
    s=replace(s,'.I_tip_valid(tip_valid)', '.I_sample_valid(sample_valid)')
    out['rtl/color_regions/regions_memory_video_out.v']=s
    s=(R/'rtl/00_top_control/criticalwork_top.v').read_text(encoding='utf-8')
    s=replace(s,'memory_video_out #','regions_memory_video_out #')
    out['rtl/color_regions/regions_top.v']=s
    # No glob imports: abandoned diagnostics never enter this project implicitly.
    names=['classifier','runs4','run_labeler','divide','finalize','grid','confirm','capture','frame_store','display','preprocess','osd','glyph_rom','line_reader','memory_video_out','top']
    remove={'target_diagnostics.v','target_detector.v','target_tracker.v','target_capture_pipeline.v','target_frame_store.v','target_display.v','target_line_reader.v','target_osd.v','target_glyph_rom.v','memory_video_out.v','criticalwork_top.v','image_preprocess.v'}
    # TD writes literal '&' in attribute strings, which is not strict XML.
    root=ET.fromstring((R/'td_project/target_lock_candidates_ingress.al').read_text(encoding='utf-8').replace('&','&amp;').replace('::','__TD_COLON__'));root.find('Name').text='target_color_regions'
    sources=root.find('Source_Files/Verilog')
    for node in list(sources):
        path=node.attrib.get('Path','')
        if Path(path).name in remove or '/02_image_preprocess/' in path or '/09_osd_ui/' in path:sources.remove(node)
    for name in names:
        node=ET.SubElement(sources,'File',Path=f'../rtl/color_regions/regions_{name}.v');info=ET.SubElement(node,'FileInfo')
        for k,v in [('UsedInSyn','true'),('UsedInP&R','true'),('BelongTo','design_1')]:ET.SubElement(info,'Attr',Name=k,Val=v)
    for n,node in enumerate(sources):
        info=node.find('FileInfo')
        for a in list(info):
            if a.attrib.get('Name')=='CompileOrder':info.remove(a)
        ET.SubElement(info,'Attr',Name='CompileOrder',Val=str(n))
    ET.indent(root,space='    ')
    text=ET.tostring(root,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::').replace('target_lock_candidates_ingress','target_color_regions')
    out['td_project/target_color_regions.al']='<?xml version="1.0" encoding="UTF-8"?>\n'+text+'\n'
    out['scripts/build_target_color_regions.tcl']=(R/'scripts/build_target_lock_candidates_ingress.tcl').read_text(encoding='utf-8').replace('target_lock_candidates_ingress','target_color_regions').replace('TARGET_LOCK_CANDIDATES_INGRESS','TARGET_COLOR_REGIONS')
    return out
