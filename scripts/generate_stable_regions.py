"""Build only the production stable-region wiring/UI/project assets.

Hand-written RTL is never overwritten. --check is read-only. Legacy generation
and historical deliveries remain separate from this production source whitelist.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import argparse,json
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
def swap(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)
def assets():
    out={}
    cfg=json.loads((R/'rtl/03_tool_detection/target_config.json').read_text(encoding='utf-8'))
    assert cfg['D_mm']*2==cfg['L_mm'],'Production geometry currently implements K=1/2'
    for k,v in dict(stable_release=1,stable_tile_size=16,stable_deadline=212000,stable_marker_min=16,
                    stable_band_min=3,stable_same_color_gap=32,stable_loss_frames=15,
                    stable_window_deadzone=4,stable_window_step=24,stable_cal_window=16,stable_cal_frames=8,
                    regions_min_value=32,regions_min_chroma=16,regions_sat_num=1,regions_sat_den=4,
                    regions_area_min=48).items():assert cfg[k]==v,(k,'change RTL/independent oracle with configuration')
    s=(R/'user_source/hdl_source/isp/isp_top.v').read_text(encoding='utf-8')
    s=swap(s,'module isp_top (','module stable_isp (\n    input wire [11:0] I_gain_r,I_gain_b,\n    output wire [95:0] O_raw_rgb,output wire O_raw_sof,O_raw_valid,')
    s=swap(s,'awb #(\n    .IMG_HEIGHT(720 ),\n    .IMG_WIDTH (1280)\n) u_awb (','stable_awb u_awb (\n    .I_gain_r(I_gain_r),.I_gain_b(I_gain_b),')
    s=s.replace('    .I_tready(m_aixs_tready),\n','').replace('    .O_tready(awb_O_tready)\n','').replace('    .O_tvalid(awb_O_tvalid),','    .O_tvalid(awb_O_tvalid)')
    s=s.replace('  //assign m_aixs_tready = O_tready;','  assign m_aixs_tready = 1\'b1; // Fixed-gain four-pixel path accepts every camera group.')
    s=s.replace('data_96bit_to_128bit u_data_96bit_to_128bit(','stable_packer u_data_96bit_to_128bit(')
    s=s.replace('  assign O_detect_rgb=awb_O_tdata;','  assign O_raw_rgb=m_aixs_tdata_96;assign O_raw_sof=m_aixs_tuser;assign O_raw_valid=m_aixs_tvalid;\n  assign O_detect_rgb=awb_O_tdata;')
    out['rtl/color_regions/stable_isp.v']=s
    s=(R/'rtl/01_camera/camera_capture.v').read_text(encoding='utf-8')
    s=swap(s,'module camera_capture (','module stable_camera_capture (\n    input wire [11:0] I_gain_r,I_gain_b,\n    output wire [95:0] O_raw_rgb,output wire O_raw_sof,O_raw_valid,')
    s=swap(s,'isp_top u_isp_top (','stable_isp u_isp_top (\n.I_gain_r(I_gain_r),.I_gain_b(I_gain_b),.O_raw_rgb(O_raw_rgb),.O_raw_sof(O_raw_sof),.O_raw_valid(O_raw_valid),')
    out['rtl/color_regions/stable_camera_capture.v']=s
    s=(R/'rtl/color_regions/regions_frame_store.v').read_text(encoding='utf-8')
    s=s.replace('module regions_frame_store','module stable_frame_store').replace('[415:0]','[639:0]').replace('[450:0]','[674:0]').replace("==1;","==2;").replace("416'd0","640'd0").replace('O_data[415:0]','O_data[639:0]')
    out['rtl/color_regions/stable_frame_store.v']=s
    s=(R/'rtl/color_regions/regions_memory_video_out.v').read_text(encoding='utf-8')
    s=s.replace('module regions_memory_video_out','module stable_memory_video_out')
    s=swap(s,'input wire [95:0] I_detect_rgb,input wire I_detect_sof,I_detect_valid,','input wire [95:0] I_detect_rgb,input wire I_detect_sof,I_detect_valid,\n    input wire [127:0] I_models,input wire [15:0] I_revision,input wire [23:0] I_gains,\n    input wire [7:0] I_cal_status,input wire I_cal_active,I_needs_cal,I_frame_pair,')
    s=s.replace('[415:0]','[639:0]').replace('[450:0]','[674:0]').replace('.WIDTH(416)','.WIDTH(640)').replace('.WIDTH(451)','.WIDTH(675)')
    s=swap(s,'regions_capture #(.TILE_MIN(4),.SUPPORT_MIN(16),.AREA_MIN(16),.PADDING(64),.CONFIRM(3),.MAX_STEP(96)) u_detection(','stable_capture u_detection(\n        .I_models(I_models),.I_revision(I_revision),.I_gains(I_gains),.I_cal_status(I_cal_status),.I_cal_active(I_cal_active),.I_needs_cal(I_needs_cal),')
    s=s.replace('.I_pair(command_active[9])','.I_pair(I_frame_pair)')
    s=s.replace('regions_frame_store u_frame_store','stable_frame_store u_frame_store').replace('regions_display u_viewport','stable_display u_viewport').replace('regions_line_reader u_scaler','stable_line_reader u_scaler')
    s=swap(s,'.I_frame_commit(frame_commit),.I_selected_good(selected_good),','.I_frame_commit(frame_commit),.I_selected_good(selected_good),.I_models(active_meta[543:416]),')
    s=swap(s,'wire process_vs, process_hs, process_de;','wire process_vs, process_hs, process_de;wire [1:0] source_mask;')
    s=swap(s,'.O_rgb(S_hdmi_out_data), .O_video_ok(video_ok)','.O_rgb(S_hdmi_out_data), .O_mask(source_mask),.O_video_ok(video_ok)')
    s=s.replace('regions_preprocess u_image_preprocess','stable_preprocess u_image_preprocess').replace('regions_osd u_osd','stable_osd u_osd')
    s=swap(s,'.I_meta(active_meta),.I_x0(roi_x),','.I_tracking(I_tracking),.I_meta(active_meta),.I_x0(roi_x),')
    s=swap(s,'.I_de(S_hdmi_out_de), .I_rgb(S_hdmi_out_data),','.I_de(S_hdmi_out_de), .I_rgb(S_hdmi_out_data),.I_mask(source_mask),')
    out['rtl/color_regions/stable_memory_video_out.v']=s
    s=(R/'rtl/color_regions/regions_top.v').read_text(encoding='utf-8')
    s=swap(s,'wire gain_req, gain_up, gain_ack;','''wire gain_req, gain_up, gain_ack;
wire cal_enter,cal_sample,cal_cancel;wire [7:0] cal_status,ui_cal_status,capture_cal_status;
wire [95:0] raw_rgb;wire raw_sof,raw_valid;wire [11:0] wb_r,wb_b;
wire [127:0] color_models;wire [15:0] color_revision;wire [23:0] frame_gains;wire cal_active,needs_cal,frame_pair;
(* async_reg="true" *) reg [1:0] cal_reset_bridge;
wire cal_rst_n=cal_reset_bridge[1];
always @(posedge S_csi_rx_clk or negedge S_rst_n)if(!S_rst_n)cal_reset_bridge<=0;else cal_reset_bridge<={cal_reset_bridge[0],1'b1};
wire event_ready,event_valid;wire [4:0] event_data;reg [4:0] event_sent,event_previous;
wire [4:0] event_now={ui_pair,gain_req,cal_cancel,cal_sample,cal_enter};
wire event_send=event_ready && event_now!=event_sent;
always @(posedge S_hdmi_pixel_clk or negedge process_rst_n)if(!process_rst_n)event_sent<=0;else if(event_send)event_sent<=event_now;
always @(posedge S_csi_rx_clk or negedge cal_rst_n)if(!cal_rst_n)event_previous<=0;else if(event_valid)event_previous<=event_data;
target_mailbox #(.WIDTH(5)) cal_events(.S_clk(S_hdmi_pixel_clk),.S_rst_n(process_rst_n),.S_send(event_send),.S_data(event_now),.S_ready(event_ready),
.D_clk(S_csi_rx_clk),.D_rst_n(cal_rst_n),.D_valid(event_valid),.D_data(event_data));
stable_calibration calibration(.clk(S_csi_rx_clk),.rst_n(cal_rst_n),.sof(raw_sof),.valid(raw_valid),.rgb(raw_rgb),.pair(event_valid?event_data[4]:event_previous[4]),
.enter(event_valid && event_data[0]!=event_previous[0]),.sample(event_valid && event_data[1]!=event_previous[1]),
.cancel(event_valid && event_data[2]!=event_previous[2]),.gain_changed(event_valid && event_data[3]!=event_previous[3]),
.gain_r(wb_r),.gain_b(wb_b),.models(color_models),.revision(color_revision),.cal_active(cal_active),.needs_cal(needs_cal),.status(cal_status),.frame_pair(frame_pair),.frame_gains(frame_gains),.frame_status(capture_cal_status));
wire status_ready;reg [7:0] status_sent;wire status_send=status_ready && cal_status!=status_sent;
always @(posedge S_csi_rx_clk or negedge cal_rst_n)if(!cal_rst_n)status_sent<=0;else if(status_send)status_sent<=cal_status;
target_mailbox #(.WIDTH(8)) cal_feedback(.S_clk(S_csi_rx_clk),.S_rst_n(cal_rst_n),.S_send(status_send),.S_data(cal_status),.S_ready(status_ready),
.D_clk(S_hdmi_pixel_clk),.D_rst_n(process_rst_n),.D_valid(),.D_data(ui_cal_status));''')
    s=s.replace('target_controls #','stable_controls #')
    s=swap(s,'.I_keys_n(I_button), .I_ui_switch(I_ui_switch), .I_gain_ack(gain_ack),','.I_keys_n(I_button), .I_ui_switch(I_ui_switch), .I_gain_ack(gain_ack),.I_cal_status(ui_cal_status),\n    .O_cal_enter(cal_enter),.O_cal_sample(cal_sample),.O_cal_cancel(cal_cancel),')
    s=s.replace('camera_capture u_camera (','stable_camera_capture u_camera (\n    .I_gain_r(wb_r),.I_gain_b(wb_b),.O_raw_rgb(raw_rgb),.O_raw_sof(raw_sof),.O_raw_valid(raw_valid),')
    s=s.replace('regions_memory_video_out #','stable_memory_video_out #')
    s=swap(s,'.I_detect_rgb(detect_rgb),.I_detect_sof(detect_sof),.I_detect_valid(detect_valid),','.I_detect_rgb(detect_rgb),.I_detect_sof(detect_sof),.I_detect_valid(detect_valid),\n    .I_models(color_models),.I_revision(color_revision),.I_gains(frame_gains),.I_cal_status(capture_cal_status),.I_cal_active(capture_cal_status[7:5]!=0),.I_needs_cal(needs_cal),.I_frame_pair(frame_pair),')
    out['rtl/color_regions/stable_top.v']=s
    out.update(ui_assets())
    root=ET.fromstring((R/'td_project/target_color_regions.al').read_text(encoding='utf-8').replace('&','&amp;').replace('::','__TD_COLON__'))
    root.set('Path',(R/'td_project').as_posix())
    sources=root.find('Source_Files/Verilog')
    for node in list(sources):
        path=node.attrib.get('Path','')
        if '/color_regions/' in path or Path(path).name in ('target_controls.v','camera_capture.v'):sources.remove(node)
    names=['model_lane','awb','packer','calibration','controls','filter4','grid','tracker','capture','frame_store','display','line_reader','preprocess','osd','glyph_rom','isp','camera_capture','memory_video_out','top']
    names=['regions_divide']+['stable_'+n for n in names]
    for name in names:
        node=ET.SubElement(sources,'File',Path=f'../rtl/color_regions/{name}.v');info=ET.SubElement(node,'FileInfo')
        for k,v in [('UsedInSyn','true'),('UsedInP&R','true'),('BelongTo','design_1')]:ET.SubElement(info,'Attr',Name=k,Val=v)
    for n,node in enumerate(sources):
        info=node.find('FileInfo')
        for attr in list(info):
            if attr.attrib.get('Name')=='CompileOrder':info.remove(attr)
        ET.SubElement(info,'Attr',Name='CompileOrder',Val=str(n))
    ET.indent(root,space='    ')
    out['td_project/target_color_regions.al']='<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n'
    return out
def ui_assets():
    chars=' '+''.join(dict.fromkeys('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ:+-/原图色彩高亮灰度二值模式倍率配红蓝黄紫候选状态待命搜索中区域多个拥挤按键冲突视频未就绪无新帧更多判取样隐藏'))
    labels=['待命','中央选取','确认中','跟踪中','缺色','失锁保持','中央重选','尖端越界','无效帧']
    cal_labels=['请重新校准','白纸按KEY3','空背景按KEY3','A色按KEY3','B色按KEY3','采样处理中','采样失败重试']
    chars=''.join(dict.fromkeys(chars+''.join(labels+cal_labels)+'安路等待结果'))
    assert len(chars)<=128,len(chars)
    ids={c:i for i,c in enumerate(chars)}
    def text_cases(text,start=3):return '\n'.join(f'{start+i}:footer={ids[c]};' for i,c in enumerate(text))
    s=(R/'rtl/color_regions/regions_osd.v').read_text(encoding='utf-8')
    s=s.replace('module regions_osd','module stable_osd').replace('[415:0]','[639:0]').replace('regions_glyph_rom font','stable_glyph_rom font')
    s=s.replace('input wire I_show,I_video_ok,','input wire I_tracking,I_show,I_video_ok,')
    a=s.index(' if(row && col>=19');s=s[:a]+''' if(row && col>=3 && col<19)begin
footer=0;
'''+''.join(f'if(I_meta[36:33]=={n} && I_tracking)case(col)\n{text_cases(t)}\nendcase\n' for n,t in enumerate(labels))+'''
if(!I_tracking)case(col)
'''+text_cases('待命')+'\nendcase\n'+''.join(f'if(I_meta[567:565]=={n})case(col)\n{text_cases(cal_labels[n])}\nendcase\n' for n in range(1,5))+'''
if(I_meta[564] && I_meta[567:565]!=0)case(col)
'''+text_cases(cal_labels[5])+'''\nendcase
if(I_meta[563:560]!=0 && I_meta[567:565]!=0)case(col)
'''+text_cases(cal_labels[6])+'''\nendcase
if(I_meta[568] && I_meta[567:565]==0)case(col)
'''+text_cases(cal_labels[0])+'''\nendcase
end
'''+s[a:]
    s=s.replace('39:footer=2;','39:footer=3;').replace('35:footer=28;','35:footer=29;')
    s=s.replace('35:footer=29;',f'35:footer={ids["安"]};').replace('36:footer=2;',f'36:footer={ids["路"]};').replace('37:footer=39;',f'37:footer={ids["S"]};').replace('38:footer=1;',f'38:footer={ids["2"]};').replace('39:footer=3;','39:footer=0;')
    s=s.replace('if(I_meta[568] && I_meta[567:565]==0)case(col)',f'if(I_meta[563:560]!=0 && I_meta[567:565]!=0)begin if(col==15)footer={ids["E"]};if(col==16)footer={ids["0"]}+I_meta[563:560];end\nif(I_meta[568] && I_meta[567:565]==0)case(col)')
    # Live/stale state always wins over a historical tracking/calibration label.
    end=s.index(' end endfunction',s.index('function [6:0] footer'))
    priority=' if(row && col>=3 && col<19)begin\n'
    for condition,text in [('I_tracking && !I_detection_valid','等待结果'),('I_state==5','按键冲突'),('I_state==7','无新帧'),('!I_video_ok || I_state==6','视频未就绪')]:
        priority+=f'if({condition})begin footer=0;case(col)\n{text_cases(text)}\nendcase end\n'
    s=s[:end]+priority+'end\n'+s[end:]
    marker='     if(I_show && I_mode==1 && border('
    index=s.index(marker)
    s=s[:index]+'''     if(I_show && I_detection_valid && I_meta[32])begin
       lx=mapx(I_meta[89:79]);ly=mapy(I_meta[99:90]);ldx=xx-lx;ldy=yy-ly;
       if((ldx>=-6 && ldx<=6 && ldy>=-1 && ldy<=1)||(ldy>=-6 && ldy<=6 && ldx>=-1 && ldx<=1))begin back_on=1;back=24'h40ff90;end
     end
     if(I_meta[567:565]!=0 && border(xx,yy,mapx(632),mapx(647)+(14'sd1<<<I_zoom)-1,mapy(352),mapy(367)+(14'sd1<<<I_zoom)-1))begin back_on=1;back=24'h80ff80;end
     if(I_show && I_tracking && I_meta[36:33]<=2 && border(xx,yy,mapx(320),mapx(959),mapy(180),mapy(539)))begin back_on=1;back=24'h40c080;end
'''+s[index:]
    out={'rtl/color_regions/stable_osd.v':s}
    font=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',16);rows=[]
    for ch in chars:
        im=Image.new('1',(16,16));ImageDraw.Draw(im).text((0,-1),ch,font=font,fill=1)
        rows.extend(sum(int(im.getpixel((x,y)))<<(15-x) for x in range(16)) for y in range(16))
    rows+=[0]*(2048-len(rows))
    out['rtl/color_regions/stable_glyph_rom.v']='module stable_glyph_rom(input wire clk,input wire [10:0] addr,output reg [15:0] data);\n(* ram_style="block" *) reg [15:0] rom[0:2047];\ninitial begin\n'+''.join(f"rom[{i}]=16'h{v:04x};\n" for i,v in enumerate(rows))+'end\nalways @(posedge clk)data<=rom[addr];\nendmodule\n'
    return out
def generate(check=False):
    for name,s in assets().items():
        p=R/name;data=s.replace('\r\n','\n').encode('utf-8')
        if check:assert p.is_file() and p.read_bytes()==data,name
        else:
            if p.exists():p.read_bytes()
            p.write_bytes(data)
    print('STABLE_GENERATION_CHECK_PASS' if check else 'STABLE_GENERATED')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');generate(parser.parse_args().check)
