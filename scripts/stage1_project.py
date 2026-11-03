"""Read-only TD project compatibility; original saved bytes stay untouched."""
import re,xml.etree.ElementTree as ET
OPTIONAL_REVIEWED_EXCLUSIONS=('../rtl/color_regions/stable_display.v',)
REVIEWED_EXCLUSIONS=('../rtl/01_camera/camera_gain_control.v', '../user_source/hdl_source/video_out.v', '../user_source/hdl_source/signal_delay.v', '../user_source/hdl_source/awb.v', '../user_source/hdl_source/isp/isp_top.v', '../user_source/hdl_source/isp/demosaic_4x_2_0/demosaic.v', '../user_source/hdl_source/isp/demosaic_4x_2_0/raw_matrix_3x3_buffer.v', '../user_source/hdl_source/isp/demosaic_4x_2_0/zhenghe.v', '../user_source/hdl_source/isp/data96_128/data96_128.v', '../user_source/hdl_source/uics500_cfg/uicfgcs500_720p.v', '../user_source/hdl_source/uiisp_beta/ae_set.v', '../user_source/hdl_source/hdmi_mixer.v', '../user_source/hdl_source/uics500_cfg/uics500reg_1080p30.v', '../rtl/09_osd_ui/scaling_logo_rom.v', '../rtl/color_regions/stable_footer_program_rom.v', '../rtl/color_regions/stable_footer_text_rom.v', '../rtl/color_regions/stable_footer_glyph_rom.v', '../rtl/color_regions/stable_controls.v', '../rtl/color_regions/stable_frame_store.v', '../rtl/color_regions/stable_line_reader.v', '../rtl/color_regions/stable_osd.v', '../rtl/color_regions/stable_glyph_rom.v', '../rtl/color_regions/refined_controls.v', '../user_source/ip_source/blk_mem_gen_awb_delay_signal/blk_mem_gen_awb_delay_signal.xml', '../user_source/ip_source/divider/divider.ipc')

def _parse(text):
    return ET.fromstring(re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;',text).replace('::','__TD_COLON__'))

def check_project(path,expected):
    current=_parse(path.read_text(encoding='utf-8'));reference=_parse(expected)
    def exclusions(root):
        return {f.get('Path') for f in root.findall('./Source_Files/*/File')
                if any(a.get('Name')=='AutoExcluded' and a.get('Val')=='true' for a in f.findall('./FileInfo/Attr'))}
    # TD may mark the historical display unused after stage1_viewport replaced it.
    # This is the sole additional reviewed exclusion; dependency/order/top checks
    # remain exact, and the user's saved project is never rewritten.
    current_exclusions=exclusions(current)
    assert set(REVIEWED_EXCLUSIONS)<=current_exclusions<=set(REVIEWED_EXCLUSIONS+OPTIONAL_REVIEWED_EXCLUSIONS),'TD exclusion set changed'
    def orders(root):
        result=[]
        for group in root.find('Source_Files'):
            rows=[]
            for f in group.findall('File'):
                values=[int(a.get('Val')) for a in f.findall('./FileInfo/Attr') if a.get('Name')=='CompileOrder']
                if values:rows.append((values[0],f.get('Path')))
            assert len({n for n,p in rows})==len(rows),'Duplicate compile order'
            result.append((group.tag,tuple(p for n,p in sorted(rows))))
        return tuple(sorted(result))
    assert orders(current)==orders(reference),'TD relative compile order changed'
    def canonical(node,file_path=''):
        if node.tag=='File':file_path=node.get('Path')
        attrs=dict(node.attrib)
        if node.tag=='Attr' and attrs.get('Name')=='CompileOrder':
            assert attrs.get('Val','').isdigit(),'Invalid TD compile order'
            attrs['Val']='TD_RENUMBERED'
        if node.tag=='Attr' and attrs.get('Name')=='AutoExcluded' and file_path in REVIEWED_EXCLUSIONS+OPTIONAL_REVIEWED_EXCLUSIONS:
            assert attrs.get('Val')=='true'
            return None
        children=[c for n in node if (c:=canonical(n,file_path)) is not None]
        if node.tag in ('Verilog','VHDL','IP','ADC','SDC','FileInfo'):children.sort(key=repr)
        return (node.tag,tuple(sorted(attrs.items())),(node.text or '').strip(),tuple(children))
    assert canonical(current)==canonical(reference),'TD project dependency/top/device/constraint/settings mismatch'
    return len(current.findall('./Source_Files/*/File'))
