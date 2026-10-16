"""Independent refined project generation; never writes the user's original .al."""
from pathlib import Path
import argparse, xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
def assets():
    source=(R/'user_source/hdl_source/ph1p35_ddr/ph1p35_324_ddr_wrapper.v').read_text(encoding='utf-8')
    source=source.replace('module ph1p35_324_ddr_wrapper (','module refined_ph1p35_ddr_wrapper (')
    source=source.replace('wire         ddrphy_rdy;', 'wire         ddrphy_rdy;\n    wire dhi_clk;')
    source=source.replace('assign O_mc_app_rdy            = paxi_arready || paxi_awready',
                          'assign O_mc_app_rdy            = I_mc_app_cmd[0] ? paxi_arready : paxi_awready')
    source=source.replace('assign O_mc_app_wdf_rdy        = paxi_awready',
                          'assign O_mc_app_wdf_rdy        = paxi_wready')
    source=source.replace('assign O_mc_app_rd_data        = paxi_rdata',
                          'assign O_mc_app_rd_data_end    = paxi_rlast;\n    assign O_mc_app_rd_data        = paxi_rdata')
    root=ET.fromstring((R/'td_project/target_color_regions.al').read_text(encoding='utf-8').replace('&','&amp;').replace('::','__TD_COLON__'))
    root.set('Path',(R/'td_project').as_posix())
    root.find('Name').text='target_color_regions_refined'
    files=root.find('Source_Files/Verilog')
    for node in files:
        path=node.attrib.get('Path','')
        if path.endswith('/mc_to_user_interface.v'):node.set('Path','../rtl/color_regions/refined_mc_to_user_interface.v')
        if path.endswith('/ph1p35_324_ddr_wrapper.v'):node.set('Path','../rtl/color_regions/refined_ph1p35_ddr_wrapper.v')
    extra=sorted((R/'rtl/color_regions').glob('refined_*.v'))
    existing={node.attrib.get('Path') for node in files}
    for path in extra:
        name='../'+path.relative_to(R).as_posix()
        if name in existing:continue
        node=ET.SubElement(files,'File',Path=name);info=ET.SubElement(node,'FileInfo')
        for k,v in [('UsedInSyn','true'),('UsedInP&R','true'),('BelongTo','design_1')]:ET.SubElement(info,'Attr',Name=k,Val=v)
    ET.indent(root,space='    ')
    project='<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n'
    return {'rtl/color_regions/refined_ph1p35_ddr_wrapper.v':source,'td_project/target_color_regions_refined.al':project}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    for name,text in assets().items():
        path=R/name;data=text.replace('\r\n','\n').encode('utf-8')
        if a.check:assert path.read_bytes()==data,name
        else:path.write_bytes(data)
    print('REFINED_GENERATION_CHECK_PASS' if a.check else 'REFINED_GENERATED')
