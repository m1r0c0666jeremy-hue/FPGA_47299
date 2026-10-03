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
checks = []
for item in manifest['files']:
    p = ROOT/'vendor_reference/lab1'/item['path']
    assert sha(p) == item['sha256'], f'Baseline changed: {p}'
    if item['path'].startswith('user_source/'):
        assert sha(ROOT/item['path']) == item['sha256'], f'Vendor source changed: {item["path"]}'
checks.append(f'{len(manifest["files"])} baseline files match imported archive hashes; working vendor sources unchanged')
project = ROOT/'td_project/criticalwork.al'
al = project.read_text(encoding='utf-8-sig')
paths = re.findall(r'<File Path="([^"]+)"', al)
for rel in paths:
    assert not Path(rel).is_absolute(), rel
    p = (project.parent/rel).resolve()
    assert p.is_relative_to(ROOT) and p.is_file(), rel
    assert '/sim/' not in p.as_posix() and '/vendor_reference/' not in p.as_posix(), rel
active = {rel.split('/')[2] for rel in paths if rel.startswith('../rtl/')}
assert active == {'00_top_control','01_camera','10_memory_video_out'}, active
assert '<Device>PH1P35MDG324</Device>' in al and '<Speed>-3</Speed>' in al
checks.append(f'{len(paths)} project dependencies resolve inside project; only three active RTL directories; no simulation models')
original = code(ROOT/'vendor_reference/lab1/user_source/hdl_source/design_top_wrapper.v')
top = code(ROOT/'rtl/00_top_control/criticalwork_top.v')
camera = code(ROOT/'rtl/01_camera/camera_capture.v')
video = code(ROOT/'rtl/10_memory_video_out/memory_video_out.v')
def ports(s):
    header = s[s.index('module '):s.index(');')]
    return [compact(x) for x in re.findall(r'\b(?:input|output|inout)\s+wire\s*(?:\[[^\]]+\]\s*)?\w+',header)]
assert ports(top)==ports(original), 'Board ports changed'
cam_segment = original[original.index('ae_set u_ae_set'):original.index('video_in u_video_in')]
vid_segment = original[original.index('video_in u_video_in'):original.rindex('endmodule')]
vid_segment = vid_segment.replace('.DEBUG_MODE ( 0    )','.DEBUG_MODE ( DEBUG_MODE )')
pll_segment = original[original.index('PLL u_PLL'):original.index('ae_set u_ae_set')]
for segment, target in [(cam_segment,camera),(vid_segment,video),(pll_segment,top)]:
    assert compact(segment) in compact(target), 'Vendor instance connections changed'
checks.append('Board ports, PLL, camera and memory/display instance connections match baseline (DEBUG_MODE parameter exposed)')
old_sdc=(ROOT/'vendor_reference/lab1/td_project/camera_to_dsi_display.sdc').read_text()
new_sdc=(ROOT/'td_project/criticalwork.sdc').read_text()
assert new_sdc.replace('u_camera/','').replace('u_video/','')==old_sdc, 'Unexpected timing constraint change'
checks.append('Timing constraints differ only by camera/video hierarchy prefixes; no constraint relaxation')
artifacts=[]
for name in ['baseline','criticalwork']:
    p=ROOT/f'build/{name}/{name}.bit'
    artifacts.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    log=(ROOT/f'reports/{name}_build.log').read_text(encoding='utf-8',errors='replace')
    marker='CRITICALWORK_BASELINE_COMPLETED' if name=='baseline' else 'CRITICALWORK_BUILD_COMPLETED'
    assert marker in log and 'BUILD_FAILED:' not in log, name
checks.append('Both fresh build completion markers and bitstreams present')
result={'status':'PASS','checks':checks,'artifacts':artifacts,'hardware_status':'PINOUT UNVERIFIED - DO NOT PROGRAM BOARD',
        'scope':'Static checks plus existing build evidence; not formal equivalence or hardware validation'}
(ROOT/'reports/project_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
