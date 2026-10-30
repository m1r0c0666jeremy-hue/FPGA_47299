"""Approved stable DDR reference correction; no vendor IP regeneration."""
from pathlib import Path
from fractions import Fraction
import hashlib,re
R=Path(__file__).resolve().parents[1]

def contract(root=R):
    top=(root/'rtl/color_regions/stage1_top.v').read_text(encoding='utf-8')
    video=(root/'rtl/color_regions/stage1_memory_video_out.v').read_text(encoding='utf-8')
    assert '.I_sys_clk(I_sys_clk),.I_ddr_ref_clk(S_100m_clk), .I_rst_n(S_rst_n)' in top
    assert '.clk0_out    ( S_100m_clk' in top
    assert 'input wire I_sys_clk, input wire I_ddr_ref_clk,input wire I_rst_n,' in video
    assert '.I_sys_clk              ( I_ddr_ref_clk          )' in video
    assert '.I_sys_rst_n            ( ddr_ref_reset_n        )' in video
    assert 'refined_reset_bridge ddr_reference_reset(I_ddr_ref_clk,controller_reset_n,ddr_ref_reset_n);' in video
    assert 'refined_ddr_recovery #(.CYCLES_PER_MS(50000)) recover_ddr(.clk(I_sys_clk)' in video
    wrapper=root/'rtl/color_regions/refined_ph1p35_ddr_wrapper.v'
    assert hashlib.sha256(wrapper.read_bytes()).hexdigest()=='45e8b20fb67f2f2cba3115101c4913ede786d6d3a5bbb40b89a8dd60a45627f3'
    pll=(root/'user_source/ip_source/PLL/PLL.v').read_text(encoding='utf-8')
    for field,value in [('FIN','"50.000000000"'),('REFCLK_DIV','1'),('FBCLK_DIV','2'),('CLKC0_DIV','15'),('PLL_FEED_TYPE','"EXTERNAL"'),('FBKCLK','"CLKC0_EXT"')]:
        assert re.search(r'\.'+field+r'\s*\(\s*'+re.escape(value)+r'\s*\)',pll),field
    ip=(root/'ip/refined_ddr2/ddr2.v').read_text(encoding='utf-8')
    for field,value in [('tCK','1876'),('PLL0_REFCLK_FREQ','100.0'),('PLL0_REFCLK_DIV','3'),('PLL0_FBKCLK_DIV','32'),('PLL0_CLK2_DIV','2'),('PLL0_CLK3_DIV','21')]:
        assert '.'+field+'('+value+')' in ip,field
    reader=(root/'rtl/color_regions/refined_line_reader.v').read_text(encoding='utf-8')
    assert 'JOB_TIMEOUT_CYCLES=133334,DRAIN_TIMEOUT_CYCLES=133334' in reader
    vco=Fraction(100,3)*32;ddr=vco/2;user=vco/8
    assert 800<=vco<=1600 and float(ddr*2)<=1066.667
    return dict(reference_mhz=100,supervisor_mhz=50,vco_mhz=float(vco),ddr_ck_mhz=float(ddr),
        ddr_data_mbps=float(ddr*2),user_mhz=float(user),user_period_ns=7.5,
        reader_timeout_cycles=133334,reader_timeout_us=float(Fraction(133334)*Fraction(15,2)/1000),
        timeout_note='Nominal1ms restored; previous misclocked elapsed timeout was about2ms',
        analog_or_board_pass=False)
