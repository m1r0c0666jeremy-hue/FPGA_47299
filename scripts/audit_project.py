"""Read-only source, wrapper and project dependency audit; writes one report."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def code(path):
    return re.sub(r'/\*.*?\*/|//[^\n]*', '', path.read_text(encoding='utf-8-sig'), flags=re.S)
def compact(s):
    return re.sub(r'\s+', '', s)
manifest = json.loads((ROOT/'reports/source_manifest.json').read_text(encoding='utf-8'))
# 2026-10-04 工程自有改动（引脚核对 + 三处缺陷修复），逐个登记，审计仍能发现任何未记录的改动。
MODIFIED = {
    'user_source/constraints_source/pin.adc':
        'F620327DEE0EA50219C7E4967EC8B6BFD389488C0A9156CC991D1E9E6C5C9FC1',
    'user_source/hdl_source/video_in.v':
        '54E902F90CB973F6D10331B6F7D232E776CF0A02B45858FB8FFFDD59E9874123',
    'user_source/hdl_source/video_out.v':
        '4B396EE8ACF3F33686D694717A45B85E50A631A59C64C625F0E4A4228A9C0396',
    'user_source/hdl_source/data_96bit_to_128bit.v':
        '12757121B72C180D2F2C6B268DD5742F2506E6DDB13B02ADB2D053BE98E22299',
    'user_source/hdl_source/uics500_cfg/SC500GainTbl.v':
        'bbdb34c8a8cf7d22a23fa0facd05d365320a49060271560af4d68dcb6bd7cb1c',
    'user_source/hdl_source/uiisp_beta/ae_set.v':
        '94ebe22405c27c630e1e5a6e1c1f8bbe8a7244d50b4a67648d6701fc84f2046a',
    'user_source/hdl_source/uics500_cfg/uics500regAE.v':
        '5b648228ca9fcd1cdb8084f2bc93134fb9af22060d5ca92faa588dc6174ed055',
}
checks = []
for item in manifest['files']:
    p = ROOT/'vendor_reference/lab1'/item['path']
    assert sha(p) == item['sha256'], f'Baseline changed: {p}'
    if item['path'].startswith('user_source/'):
        want = MODIFIED.get(item['path'], item['sha256'])
        assert sha(ROOT/item['path']).lower() == want.lower(), f'Unexpected vendor source change: {item["path"]}'
checks.append(f'{len(manifest["files"])} baseline files match imported archive hashes; '
              f'working copy deviates only in {len(MODIFIED)} documented files (see reports/验证报告.md, 2026-10-04)')
project = ROOT/'td_project/criticalwork.al'
al = project.read_text(encoding='utf-8-sig')
paths = re.findall(r'<File Path="([^"]+)"', al)
for rel in paths:
    assert not Path(rel).is_absolute(), rel
    p = (project.parent/rel).resolve()
    assert p.is_relative_to(ROOT) and p.is_file(), rel
    assert '/sim/' not in p.as_posix() and '/vendor_reference/' not in p.as_posix(), rel
active = {rel.split('/')[2] for rel in paths if rel.startswith('../rtl/')}
assert active == {'00_top_control','01_camera','02_image_preprocess','10_memory_video_out'}, active
assert '<Device>PH1P35MDG324</Device>' in al and '<Speed>-3</Speed>' in al
checks.append(f'{len(paths)} project dependencies resolve inside project; four active RTL directories; no simulation models')
original = code(ROOT/'vendor_reference/lab1/user_source/hdl_source/design_top_wrapper.v')
top = code(ROOT/'rtl/00_top_control/criticalwork_top.v')
camera = code(ROOT/'rtl/01_camera/camera_capture.v')
video = code(ROOT/'rtl/10_memory_video_out/memory_video_out.v')
def ports(s):
    header = s[s.index('module '):s.index(');')]
    return [compact(x) for x in re.findall(r'\b(?:input|output|inout)\s+wire\s*(?:\[[^\]]+\]\s*)?\w+',header)]
expected = [p.replace('inoutwire[1:0]I_button', 'inputwire[1:0]I_button') for p in ports(original)]
actual_ports=ports(top)
assert actual_ports.count('inputwire[1:0]I_switch') == 1
assert [p for p in actual_ports if p != 'inputwire[1:0]I_switch'] == expected, 'Unexpected board port change'
cam_segment = original[original.index('ae_set u_ae_set'):original.index('video_in u_video_in')]
vid_segment = original[original.index('video_in u_video_in'):original.rindex('endmodule')]
vid_segment = vid_segment.replace('.DEBUG_MODE ( 0    )','.DEBUG_MODE ( DEBUG_MODE )')
pll_segment = original[original.index('PLL u_PLL'):original.index('ae_set u_ae_set')]
video_original=video
start=video_original.index('wire process_vs, process_hs, process_de;')
end=video_original.index('hdmi_tx u_hdmi_tx(',start)
video_original=video_original[:start]+video_original[end:]
video_original=re.sub(r'\(\s*process_vs\s*\)', '( S_hdmi_out_vsync )',video_original)
video_original=re.sub(r'\(\s*process_de\s*\)', '( S_hdmi_out_de )',video_original)
video_original=re.sub(r'\(\s*process_rgb\s*\)', '( S_hdmi_out_data )',video_original)
for segment, target in [(cam_segment,camera),(vid_segment,video_original),(pll_segment,top)]:
    assert compact(segment) in compact(target), 'Vendor instance connections changed'
for connection in ['.I_mode_pending(I_process_mode)', '.I_vs(S_hdmi_out_vsync)',
                   '.I_de(S_hdmi_out_de)', '.I_rgb(S_hdmi_out_data)',
                   '.O_vs(process_vs)', '.O_de(process_de)', '.O_rgb(process_rgb)',
                   '.I_video_in_vs(process_vs)', '.I_video_in_de(process_de)', '.I_video_in_data(process_rgb)']:
    assert connection in compact(video), connection
assert '.I_process_mode(image_mode_pending)' in compact(top)
assert '.I_switch(I_switch)' in compact(top)
pin_base=(ROOT/'user_source/constraints_source/pin.adc').read_text(encoding='utf-8')
pin_new=(ROOT/'td_project/imagepreprocess_10_3.adc').read_text(encoding='utf-8')
assert pin_new.startswith(pin_base)
assert re.search(r'I_switch\[1\].*LOCATION = A4',pin_new)
assert re.search(r'I_switch\[0\].*LOCATION = B4',pin_new)
checks.append('Camera/DDR/PLL connections retained; RGB processing inserted before HDMI, top switches connected, SW1=A4 SW2=B4')
old_sdc=(ROOT/'vendor_reference/lab1/td_project/camera_to_dsi_display.sdc').read_text()
new_sdc=(ROOT/'td_project/criticalwork.sdc').read_text()
assert new_sdc.replace('u_camera/','').replace('u_video/','')==old_sdc, 'Unexpected timing constraint change'
checks.append('Timing constraints differ only by camera/video hierarchy prefixes; no constraint relaxation')
artifacts=[]
for name in ['baseline','criticalwork','imagepreprocess_10_3']:
    p=ROOT/f'build/{name}/{name}.bit'
    artifacts.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    log=(ROOT/f'reports/{name}_build.log').read_text(encoding='utf-8',errors='replace')
    marker={'baseline':'CRITICALWORK_BASELINE_COMPLETED','criticalwork':'CRITICALWORK_BUILD_COMPLETED','imagepreprocess_10_3':'IMAGEPREPROCESS_10_3_BUILD_COMPLETED'}[name]
    assert marker in log and 'BUILD_FAILED:' not in log, name
checks.append('Baseline/teammate artifacts retained; ImagePreprocess new build marker and bitstream present')
result={'status':'PASS','checks':checks,'artifacts':artifacts,'hardware_status':'Manual and IO report match: camera/HDMI/clock, reset D5, buttons A9/B9, LED D10, SW1 A4 and SW2 B4. Teammate basic video success reported by Jeremy; new four-mode bit not tested on hardware.',
        'scope':'Static checks plus existing build evidence; not formal equivalence or hardware validation'}
(ROOT/'reports/imagepreprocess_10_3_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
