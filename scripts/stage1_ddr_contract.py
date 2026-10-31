"""Approved stable DDR reference correction; no vendor IP regeneration."""
from pathlib import Path
from fractions import Fraction
import hashlib,re
R=Path(__file__).resolve().parents[1]

def contract(root=R):
    # Jeremy explicitly deferred correction on2026-10-31 for the existing-clock
    # RY/BP+FPS release. This is an exact pinned profile, never a general waiver.
    legacy_inputs={'rtl/color_regions/stage1_top.v': 'd4be1904f2d680bdc27b9a2e5d9850ce06e7a4294389b147f392fda21d772b05', 'rtl/color_regions/stage1_memory_video_out.v': '62f0485ed29df4b8616fb627b5cb9ae0c499504e6ee683f3b44988e6fc5e1b71', 'rtl/color_regions/refined_ph1p35_ddr_wrapper.v': '45e8b20fb67f2f2cba3115101c4913ede786d6d3a5bbb40b89a8dd60a45627f3', 'ip/refined_ddr2/ddr2.v': 'be1ec6b3ab75185ed027b97e490e7c6df981edabe2608de37bb7fa6261cfc210', 'user_source/ip_source/PLL/PLL.v': '1137946f04514e440b6c6cfd6695715dd6ae48d213af0c7314932b9f5e671037', 'rtl/color_regions/refined_line_reader.v': '6359e2a2bc68e4c5f1c274569522f2fc154b1659e7295769664d24a137f1b9fd'}
    # Authorized display-only retiming; DDR clock/IP bytes remain identical.
    retimed_legacy_inputs=dict(legacy_inputs, **{'rtl/color_regions/stage1_memory_video_out.v': '52057799973d187982924d4234e0b59ed70e5d5cb372066b26892910a20e957c', 'rtl/color_regions/refined_line_reader.v': '2f0d4feeabbddb4d95acc4ad63c3617e227bc4751d46c2e81be20e871632c5c2'})
    legacy_profile=any(all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items()) for pins in (legacy_inputs,retimed_legacy_inputs))
    if legacy_profile:
        return dict(profile='LEGACY_50MHZ_REFERENCE_CORRECTION_DEFERRED',
            reference_mhz=50,ip_nominal_reference_mhz=100,supervisor_mhz=50,
            vco_mhz=float(Fraction(50,3)*32),user_mhz=float(Fraction(200,3)),
            user_period_ns=15.0,reader_timeout_cycles=133334,
            reader_timeout_us=float(Fraction(133334)*15/1000),
            configuration_matched=False,correction_deferred_by_user=True,
            risk='Actual50MHz reference differs from nominal100MHz IP; VCO below documented minimum. Flower root cause unresolved; board verification required.',
            timeout_note='Legacy elapsed reader timeout about2ms retained.',analog_or_board_pass=False)
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
