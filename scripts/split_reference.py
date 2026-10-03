"""One-time, guarded extraction of the supplied top into functional wrappers.

This does not relocate or change any vendor IP. Refuses to overwrite outputs.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
original = (ROOT / 'vendor_reference/lab1/user_source/hdl_source/design_top_wrapper.v').read_text(encoding='utf-8-sig')
code = re.sub(r'/\*.*?\*/|//[^\n]*', '', original, flags=re.S)
declarations = dict((m.group(2), m.group(0)) for m in re.finditer(
    r'\bwire\s*(\[[^\]]+\]\s*)?(S_\w+)\s*;', code))
camera = code[code.index('ae_set u_ae_set'):code.index('video_in u_video_in')]
memory = code[code.index('video_in u_video_in'):code.rindex('endmodule')]
pll = code[code.index('PLL u_PLL'):code.index('ae_set u_ae_set')]
header = code[code.index('module design_top_wrapper'):code.index(');')+2]
top_header = header.replace('module design_top_wrapper (', 'module criticalwork_top #(parameter integer DEBUG_MODE = 0) (')

def wire_declarations(body, skip=()):
    names = set(re.findall(r'\bS_\w+\b', body)) - set(skip)
    missing = names - declarations.keys()
    assert not missing, missing
    return '\n'.join(declarations[n] for n in sorted(names)) + '\n'

notice = '''// Adapted from the supplied SC500 Lab1 design_top_wrapper.v.
// Vendor modules retain their original notices under user_source/.
// This wrapper preserves the reference datapath, packing, clocks and reset policy.
// Pin compatibility and physical camera/display operation remain unverified.
`default_nettype none
'''

camera_header = '''module camera_capture (
    input wire I_control_clk, input wire I_camera_ref_clk,
    input wire I_rst_n, input wire [1:0] I_button,
    output wire O_cam_scl, inout wire IO_cam_sda,
    output wire O_cam_24m, output wire O_cam_rst,
    inout wire IO_rx_clk_pad_n, inout wire IO_rx_clk_pad_p,
    inout wire [3:0] IO_rx_data_pad_n, inout wire [3:0] IO_rx_data_pad_p,
    output wire O_capture_clk, output wire [127:0] O_rgb128,
    output wire O_data_valid, output wire O_frame_start,
    output wire [3:0] O_status_async
);
'''
camera_aliases = '''
assign S_100m_clk = I_control_clk;
assign S_24m_clk = I_camera_ref_clk;
assign S_rst_n = I_rst_n;
assign O_cam_rst = 1'b1;
assign O_cam_24m = S_24m_clk;
assign O_capture_clk = S_csi_rx_clk;
assign O_rgb128 = S_ISP_O_tdata;
assign O_data_valid = S_ISP_O_tvalid;
assign O_frame_start = S_ISP_O_tuser;
camera_status u_status (
    .I_cfg_clk(S_24m_clk), .I_rx_clk(S_csi_rx_clk), .I_rst_n(S_rst_n),
    .I_cfg_done(S_cam_cfg_done), .I_hs_valid(S_hs_rx_valid),
    .I_csi_valid(S_csi_valid), .I_frame_start(S_csi_frame_start),
    .O_status_async(O_status_async)
);
'''
memory = memory.replace('.DEBUG_MODE ( 0    )', '.DEBUG_MODE ( DEBUG_MODE )')
assert '.DEBUG_MODE ( DEBUG_MODE )' in memory
ddr_ports = header[header.index('    output wire[12:0] ddr_addr'):header.rindex(');')].strip()
memory_header = '''module memory_video_out #(parameter integer DEBUG_MODE = 0) (
    input wire I_sys_clk, input wire I_rst_n,
    input wire I_pixel_clk, input wire I_serial_clk,
    input wire I_capture_clk, input wire [127:0] I_rgb128,
    input wire I_data_valid, input wire I_frame_start,
    input wire [3:0] I_debug_status,
    output wire O_tmds_ch0_p, output wire O_tmds_ch1_p,
    output wire O_tmds_ch2_p, output wire O_tmds_clk_p,
''' + ddr_ports + '\n);\n'
memory_aliases = '''
assign S_rst_n = I_rst_n;
assign S_hdmi_rst_n = I_rst_n;
assign S_hdmi_pixel_clk = I_pixel_clk;
assign S_hdmi_serial_clk = I_serial_clk;
assign S_csi_rx_clk = I_capture_clk;
assign S_ISP_O_tdata = I_rgb128;
assign S_ISP_O_tvalid = I_data_valid;
assign S_ISP_O_tuser = I_frame_start;
assign S_hdmi_debug_status = I_debug_status;
assign S_video_out_vsync = ~S_hdmi_vsync;
'''
top_body = '''
assign O_screen_pwm = 1'b1; // Original reference output; pin compatibility pending.
assign S_rst_n = S_pll_lock;
camera_capture u_camera (
    .I_control_clk(S_100m_clk), .I_camera_ref_clk(S_24m_clk),
    .I_rst_n(S_rst_n), .I_button(I_button),
    .O_cam_scl(O_cam_scl), .IO_cam_sda(IO_cam_sda),
    .O_cam_24m(O_cam_24m), .O_cam_rst(O_cam_rst),
    .IO_rx_clk_pad_n(IO_rx_clk_pad_n), .IO_rx_clk_pad_p(IO_rx_clk_pad_p),
    .IO_rx_data_pad_n(IO_rx_data_pad_n), .IO_rx_data_pad_p(IO_rx_data_pad_p),
    .O_capture_clk(S_csi_rx_clk), .O_rgb128(S_ISP_O_tdata),
    .O_data_valid(S_ISP_O_tvalid), .O_frame_start(S_ISP_O_tuser),
    .O_status_async(camera_status_async)
);
// These four independent sticky flags are not a coherent multi-bit data bus.
status_sync u_status_sync (
    .I_clk(S_hdmi_pixel_clk), .I_rst_n(S_rst_n),
    .I_status_async(camera_status_async), .O_status(S_hdmi_debug_status)
);
memory_video_out #(.DEBUG_MODE(DEBUG_MODE)) u_video (
    .I_sys_clk(I_sys_clk), .I_rst_n(S_rst_n),
    .I_pixel_clk(S_hdmi_pixel_clk), .I_serial_clk(S_hdmi_serial_clk),
    .I_capture_clk(S_csi_rx_clk), .I_rgb128(S_ISP_O_tdata),
    .I_data_valid(S_ISP_O_tvalid), .I_frame_start(S_ISP_O_tuser),
    .I_debug_status(S_hdmi_debug_status),
    .O_tmds_ch0_p(O_tmds_ch0_p), .O_tmds_ch1_p(O_tmds_ch1_p),
    .O_tmds_ch2_p(O_tmds_ch2_p), .O_tmds_clk_p(O_tmds_clk_p),
'''
ddr_names = re.findall(r'\b(ddr_\w+)\s*,?', ddr_ports)
top_body += ',\n'.join('    .%s(%s)' % (n, n) for n in ddr_names) + '\n);\n'

outputs = {
    'rtl/00_top_control/criticalwork_top.v': notice + top_header + '\n' + wire_declarations(top_body + pll) + 'wire [3:0] camera_status_async;\n' + pll + top_body + '\nendmodule\n`default_nettype wire\n',
    'rtl/01_camera/camera_capture.v': notice + camera_header + wire_declarations(camera + camera_aliases) + camera_aliases + camera + '\nendmodule\n`default_nettype wire\n',
    'rtl/10_memory_video_out/memory_video_out.v': notice + memory_header + wire_declarations(memory + memory_aliases) + memory_aliases + memory + '\nendmodule\n`default_nettype wire\n',
}
for relative, content in outputs.items():
    path = ROOT / relative
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', content), encoding='utf-8')
print('Created three functional wrappers without changing vendor sources.')
