"""Run independent complete footer pixel oracles against the actual candidate OSD."""
from refined_testlib import R
from stage1_test_sources import OSD_ZERO_ARGS
s=(R/'scripts/test_osd_memory_ui.py').read_text(encoding='utf-8')
s=s.replace('refined_osd dut(', 'stage1_osd dut('+OSD_ZERO_ARGS)
s=s.replace("('refined_osd','refined_english_font_rom'", "('stage1_osd','refined_english_font_rom'")
s=s.replace('    run(prefix,src,mods,timeout=1800)',"    from stage1_test_sources import EXTRA_OSD\n    run(prefix,src,mods+EXTRA_OSD,timeout=1800)")
s=s.replace("R/'build/sim/osd_memory_ui'","R/'build/sim/stage1_footer_pixels'")
s=s.replace("f'{mode:<8} {zoom} {pair} {direction} STATE:{status:<16} {model:<8}'","f'{mode:<8} {zoom} {pair} {direction} STATE:{status:<16} {model:<8} BRT6/7'")
s=s.replace('osd_english_','stage1_english_')
exec(compile(s,str(R/'scripts/test_osd_memory_ui.py'),'exec'),{'__name__':'__main__','__file__':__file__})
