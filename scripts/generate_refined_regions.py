"""Independent refined project generation; never writes the user's original .al."""
from pathlib import Path
import argparse,hashlib,json,zipfile,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
def assets():
    from generate_refined_isp import isp_assets
    from refined_store_logic import store_asset
    from refined_controls_logic import control_asset
    from refined_shared_hue import shared_hue_asset
    from refined_hue_retime_logic import retime_hue_asset
    from refined_tracker_storage import tracker_asset
    from refined_camera_relay_logic import camera_top_asset
    isp=isp_assets()
    # A separate IP instance preserves the historical controller and constraints.
    # STRICT keeps an accepted read behind all previously accepted write commands;
    # NORMAL can reorder those commands internally after the application FIFO.
    ddr={}
    source_ip=R/'user_source/hdl_source/ph1p35_ddr/ddr2'
    for p in sorted(source_ip.rglob('*')):
        if not p.is_file():continue
        data=p.read_bytes()
        if p.relative_to(source_ip).as_posix()=='ddr2.v':
            assert data.count(b'.MC_REORDER("NORMAL")')==1
            data=data.replace(b'.MC_REORDER("NORMAL")',b'.MC_REORDER("STRICT")')
        ddr['ip/refined_ddr2/'+p.relative_to(source_ip).as_posix()]=data
    writer=(R/'user_source/hdl_source/video_in.v').read_text(encoding='utf-8').replace('module video_in (','module refined_video_in (')
    writer=writer.replace(' reg request,ack;',' wire camera_reset_n,ddr_reset_n;\n refined_reset_bridge cr(I_camera_clk,I_rst_n,camera_reset_n);\n refined_reset_bridge dr(I_ddr_clk,I_rst_n,ddr_reset_n);\n reg request,ack;')
    writer=writer.replace('posedge I_camera_clk or negedge I_rst_n','posedge I_camera_clk or negedge camera_reset_n').replace('if(!I_rst_n) begin\n   ack_c1','if(!camera_reset_n) begin\n   ack_c1')
    writer=writer.replace('posedge I_ddr_clk or negedge I_rst_n','posedge I_ddr_clk or negedge ddr_reset_n').replace('if(!I_rst_n) begin\n   req_d1','if(!ddr_reset_n) begin\n   req_d1')
    writer=writer.replace('input wire I_ddr_user_ready\n','input wire I_ddr_user_ready,\n input wire [31:0] I_frame_us,input wire [15:0] I_epoch,input wire I_time_valid,\n output wire [31:0] O_frame_us,output wire [15:0] O_epoch,output wire O_time_valid\n')
    writer=writer.replace('reg [31:0] camera_id_hold;','reg [31:0] camera_id_hold,stamp_hold;reg [15:0] epoch_hold;reg time_hold;\n assign O_frame_us=stamp_hold;assign O_epoch=epoch_hold;assign O_time_valid=time_hold;')
    writer=writer.replace('camera_id_hold<=0;', 'camera_id_hold<=0;stamp_hold<=0;epoch_hold<=0;time_hold<=0;')
    writer=writer.replace('camera_id_hold<=I_camera_frame_id;', 'camera_id_hold<=I_camera_frame_id;stamp_hold<=I_frame_us;epoch_hold<=I_epoch;time_hold<=I_time_valid;')
    source=(R/'user_source/hdl_source/ph1p35_ddr/ph1p35_324_ddr_wrapper.v').read_text(encoding='utf-8')
    source=source.replace('module ph1p35_324_ddr_wrapper (','module refined_ph1p35_ddr_wrapper (')
    source=source.replace('wire         ddrphy_rdy;', 'wire         ddrphy_rdy;\n    wire dhi_clk;')
    source=source.replace('assign O_mc_app_rdy            = paxi_arready || paxi_awready',
                          'assign O_mc_app_rdy            = I_mc_app_cmd[0] ? paxi_arready : paxi_awready')
    source=source.replace('assign O_mc_app_wdf_rdy        = paxi_awready',
                          'assign O_mc_app_wdf_rdy        = paxi_wready')
    source=source.replace('assign O_mc_app_rd_data        = paxi_rdata',
                          'assign O_mc_app_rd_data_end    = paxi_rlast;\n    assign O_mc_app_rd_data        = paxi_rdata')
    # The original .al remains user-owned and can be re-saved in TD. Generate
    # from the exact implementation-start snapshot, never from later UI saves.
    protection=json.loads((R/'reports/refined/protected_inputs.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(R/protection['backup']/'sources_before.zip') as z:
        original_project=z.read('td_project/target_color_regions.al')
        original_lane=z.read('rtl/color_regions/stable_model_lane.v').decode('utf-8').replace('\r\n','\n')
    assert hashlib.sha256(original_project).hexdigest()==protection['files'][str(R/'td_project/target_color_regions.al')]
    root=ET.fromstring(original_project.decode('utf-8').replace('&','&amp;').replace('::','__TD_COLON__'))
    root.set('Path',(R/'td_project').as_posix())
    root.find('Name').text='target_color_regions_refined'
    files=root.find('Source_Files/Verilog')
    for node in files:
        path=node.attrib.get('Path','')
        if path.endswith('/mc_to_user_interface.v'):node.set('Path','../rtl/color_regions/refined_mc_to_user_interface.v')
        if path.endswith('/ph1p35_324_ddr_wrapper.v'):node.set('Path','../rtl/color_regions/refined_ph1p35_ddr_wrapper.v')
        if path.endswith('/video_in.v'):node.set('Path','../rtl/color_regions/refined_video_in.v')
    extra=sorted((R/'rtl/color_regions').glob('refined_*.v'))
    existing={node.attrib.get('Path') for node in files}
    for path in extra:
        name='../'+path.relative_to(R).as_posix()
        if name in existing:continue
        node=ET.SubElement(files,'File',Path=name);info=ET.SubElement(node,'FileInfo')
        for k,v in [('UsedInSyn','true'),('UsedInP&R','true'),('BelongTo','design_1')]:ET.SubElement(info,'Attr',Name=k,Val=v)
    for index,node in enumerate(root.findall('./Source_Files/*/File')):
        if node.attrib.get('Path','').endswith('/ph1p35_ddr/ddr2/ddr2.xml'):
            node.set('Path','../ip/refined_ddr2/ddr2.xml')
        info=node.find('FileInfo')
        for attr in list(info):
            if attr.attrib.get('Name')=='CompileOrder':info.remove(attr)
        ET.SubElement(info,'Attr',Name='CompileOrder',Val=str(index))
    ET.indent(root,space='    ')
    project='<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n'
    from generate_refined_ui import ui_assets
    return {'rtl/color_regions/stable_top.v':camera_top_asset((R/'scripts/refined_camera_top_base.v.txt').read_text(encoding='utf-8')),'rtl/color_regions/stable_tracker.v':tracker_asset((R/'scripts/refined_tracker_storage_base.v.txt').read_text(encoding='utf-8')),'rtl/color_regions/stable_model_lane.v':retime_hue_asset(shared_hue_asset(original_lane)),'rtl/color_regions/refined_controls.v':control_asset((R/'rtl/color_regions/stable_controls.v').read_text(encoding='utf-8')),'rtl/color_regions/refined_frame_store.v':store_asset((R/'rtl/color_regions/stable_frame_store.v').read_text(encoding='utf-8')),**ddr,**isp,**ui_assets(),'rtl/color_regions/refined_ph1p35_ddr_wrapper.v':source,'rtl/color_regions/refined_video_in.v':writer,'td_project/target_color_regions_refined.al':project}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    for name,text in assets().items():
        path=R/name;data=text if isinstance(text,bytes) else text.replace('\r\n','\n').encode('utf-8')
        if a.check:assert path.read_bytes()==data,name
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print('REFINED_GENERATION_CHECK_PASS' if a.check else 'REFINED_GENERATED')
