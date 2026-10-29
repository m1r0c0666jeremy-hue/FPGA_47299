"""Freeze reviewed reusable templates for the independent native-zoom generator.

Run once per new source tree. Never overwrites a frozen template or user TD file.
"""
from pathlib import Path
import hashlib,json,re

R=Path(__file__).resolve().parents[1]
F=R.parent/'FPGA_47299-native-1080p'
D=R/'scripts/native_zoom_templates'
def main():
    D.mkdir(exist_ok=False)
    sources={
        'camera.v':F/'rtl/color_regions/stable_camera_capture.v',
        'raw_bridge.v':F/'rtl/color_regions/fhd_raw_bridge.v',
        'line_ram.v':F/'rtl/color_regions/fhd_isp_line_ram.v',
        'line_buffer.v':F/'rtl/color_regions/fhd_line_buffer_demosaic.v',
        'matrix.v':F/'rtl/color_regions/refined_raw_matrix_3x3_buffer.v',
        'zhenghe.v':F/'rtl/color_regions/refined_zhenghe.v',
        'clocks.v':F/'rtl/color_regions/fhd_system_pll.v',
        'demosaic.v':R/'rtl/color_regions/refined_demosaic.v',
        'camera_config.v':R/'rtl/color_regions/refined_camera_config.v',
        'controls.v':R/'rtl/color_regions/stage1_controls.v',
        'frame_store.v':R/'rtl/color_regions/refined_frame_store.v',
        'project.al':R/'td_project/target_color_regions_stage1.al',
    }
    provenance={}
    for name,p in sources.items():
        b=p.read_bytes();(D/name).write_bytes(b)
        provenance[name]={'source':str(p),'sha256':hashlib.sha256(b).hexdigest()}
    (D/'sources.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
    build=R/(R/'build/current_native_zoom_path.txt').read_text()
    text=(build/'sc500cs_official_reference.c').read_text(encoding='utf-8')
    body=text.split('static void sensor_init(void)',1)[1].split('/*\tsensor_init',1)[0]
    body=re.sub(r'//[^\n]*','',body)
    pairs=re.findall(r'write_cmos_sensor\(0x([0-9a-fA-F]+),\s*0x([0-9a-fA-F]+)\)',body)
    assert len(pairs)>80 and pairs[0]==('0103','01')
    assert not any(a=='0100' and v=='01' for a,v in pairs)
    pairs.append(('0100','01'))
    record=json.loads((build/'sensor_source.json').read_text())
    record.update(mode='2592x1944 RAW10 2lane 960Mbps 24MHz MCLK nominal30fps',
                  sequence=[[a.lower(),v.lower()] for a,v in pairs],
                  stream_start='Source preview_setting starts 0100=01 after sensor_init; preserve stop/reset sequence and delays.',
                  roi_origin=[16,252],roi_size=[2560,1440],hardware_status='UNVERIFIED')
    p=R/'vendor_reference/sc500cs_native_2592.json'
    assert not p.exists();p.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print('NATIVE_ZOOM_TEMPLATES_FROZEN',len(provenance),'sensor_writes',len(pairs))
if __name__=='__main__':main()
