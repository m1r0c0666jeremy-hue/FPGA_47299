"""Create the relocatable TD project and matching batch build from local files."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
baseline = root / 'vendor_reference/lab1/td_project'
project = (baseline / 'camera_to_dsi_display.al').read_text(encoding='utf-8-sig')
# TD's own .al format contains UsedInP&R; do not round-trip it through generic XML.
project = re.sub(r'(<Project\b[^>]*\bPath=")[^"]*', r'\g<1>.', project, count=1)
project = project.replace('<Name>camera_to_dsi_display</Name>', '<Name>criticalwork</Name>')
project = project.replace('design_top_wrapper', 'criticalwork_top')
project = project.replace('../user_source/hdl_source/criticalwork_top.v', '../rtl/00_top_control/criticalwork_top.v')
extra = ['00_top_control/status_sync.v', '01_camera/camera_capture.v',
         '01_camera/camera_status.v', '10_memory_video_out/memory_video_out.v']
entries = '\n'.join('''            <File Path="../rtl/%s">
                <FileInfo>
                    <Attr Name="UsedInSyn" Val="true"/>
                    <Attr Name="UsedInP&R" Val="true"/>
                    <Attr Name="BelongTo" Val="design_1"/>
                    <Attr Name="CompileOrder" Val="%d"/>
                </FileInfo>
            </File>''' % (path, 100 + index) for index, path in enumerate(extra))
project = project.replace('        </Verilog>', entries + '\n        </Verilog>')
project = project.replace('camera_to_dsi_display.sdc', 'criticalwork.sdc')
sdc = (baseline / 'camera_to_dsi_display.sdc').read_text(encoding='utf-8-sig')
sdc = sdc.replace('u_mipi_dphy_rx_ph1p_mipiio_wrapper/', 'u_camera/u_mipi_dphy_rx_ph1p_mipiio_wrapper/')
sdc = sdc.replace('u_ph1p35_324_ddr_wrapper/', 'u_video/u_ph1p35_324_ddr_wrapper/')
build = (root / 'scripts/build_baseline.tcl').read_text(encoding='utf-8')
build = build.replace('vendor_reference lab1 td_project camera_to_dsi_display.al', 'td_project criticalwork.al')
build = build.replace('vendor_reference lab1 user_source', 'user_source')
build = build.replace('vendor_reference lab1 td_project camera_to_dsi_display.sdc', 'td_project criticalwork.sdc')
build = build.replace('design_top_wrapper', 'criticalwork_top').replace('baseline', 'criticalwork')
build = build.replace('CRITICALWORK_BASELINE_COMPLETED', 'CRITICALWORK_BUILD_COMPLETED')
for relative, text in {'td_project/criticalwork.al': project,
                       'td_project/criticalwork.sdc': sdc,
                       'scripts/build_criticalwork.tcl': build}.items():
    target = root / relative
    if target.exists(): raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')
print('Created criticalwork.al, hierarchical constraints, and build script.')
