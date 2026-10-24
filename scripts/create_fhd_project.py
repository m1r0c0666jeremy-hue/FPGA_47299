"""Independent project entry; exported baseline .al and external sources stay intact."""
from pathlib import Path
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
def load(path):
    return ET.fromstring(path.read_text(encoding='utf-8-sig').replace('&','&amp;').replace('::','__TD_COLON__'))
def save(root,path):
    ET.indent(root,space='    ')
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n',encoding='utf-8')
def create():
    root=load(R/'td_project/target_color_regions_refined.al')
    root.set('Path',(R/'td_project').as_posix());root.find('Name').text='target_color_regions_1080p30'
    files=root.find('Source_Files/Verilog')
    existing={n.attrib['Path'] for n in files}
    additions=list((R/'rtl/color_regions').glob('fhd_*.v'))+[R/'user_source/ip_source/PLL/RTL/ph1p_phy_pll_wrapper_25a56e5ce2f9.v']
    for path in sorted(additions):
        name='../'+path.relative_to(R).as_posix()
        if name in existing:continue
        node=ET.SubElement(files,'File',Path=name);info=ET.SubElement(node,'FileInfo')
        for key,value in [('UsedInSyn','true'),('UsedInP&R','true'),('BelongTo','design_1'),('CompileOrder',str(100+len(files)))]:ET.SubElement(info,'Attr',Name=key,Val=value)
    for group in root.findall('Source_Files/*'):
        for node in list(group):
            path=node.attrib.get('Path','')
            if path.endswith('/PLL/PLL.xml'):group.remove(node)
            elif path.endswith('target_lock.sdc'):node.set('Path','target_1080p30.sdc')
    target=R/'td_project/target_color_regions_1080p30.al';save(root,target)
    print(target)
    return target
if __name__=='__main__':create()
