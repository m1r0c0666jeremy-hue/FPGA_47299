"""One-time, checked integration of the exported EN baseline's board wrapper."""
from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
p=R/'rtl/color_regions/stable_top.v';s=p.read_text(encoding='utf-8')
assert 'fhd_system_pll' not in s,'Already integrated'
s=s.replace('wire        \tS_24m_clk;','wire        \tS_24m_clk;\nwire S_processing_clk;\nwire system_pll_lock,hdmi_pll_lock;')
s=s.replace('switch_mode_control u_switch_mode','switch_mode_control #(.STABLE_CYCLES(1485000)) u_switch_mode')
s=s.replace('refined_controls #(.LONG_PRESS_MS(1000))','refined_controls #(.CYCLES_PER_MS(74250),.LONG_PRESS_MS(1000))')
s,n=re.subn(r'PLL u_PLL\(.*?\n    \);','''fhd_system_pll u_system_pll(.refclk(I_sys_clk),.reset(~I_rst_n),
 .clk0_out(S_100m_clk),.clk1_out(S_24m_clk),.clk2_out(S_processing_clk),.lock(system_pll_lock));
fhd_hdmi_pll u_hdmi_pll(.refclk(I_sys_clk),.reset(~I_rst_n),
 .clk0_out(S_hdmi_pixel_clk),.clk1_out(S_hdmi_serial_clk),.lock(hdmi_pll_lock));
assign S_pll_lock=system_pll_lock && hdmi_pll_lock;''',s,flags=re.S)
assert n==1
s=s.replace('.I_control_clk(S_100m_clk), .I_camera_ref_clk(S_24m_clk),','.I_control_clk(S_100m_clk), .I_camera_ref_clk(S_24m_clk), .I_processing_clk(S_processing_clk),')
assert '.I_processing_clk(S_processing_clk)' in s
p.write_text(s,encoding='utf-8')
