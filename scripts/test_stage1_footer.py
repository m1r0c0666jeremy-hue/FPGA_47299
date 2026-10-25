"""Run independent complete footer pixel oracles against the actual candidate OSD."""
from refined_testlib import R
from stage1_test_sources import OSD_ZERO_ARGS
s=(R/'scripts/test_osd_memory_ui.py').read_text(encoding='utf-8')
s=s.replace('refined_osd dut(', "stage1_osd dut("+OSD_ZERO_ARGS.replace("672'd0,","672'd0,168'd0,",1))
s=s.replace("('refined_osd','refined_english_font_rom'", "('stage1_osd','refined_english_font_rom'")
s=s.replace('    run(prefix,src,mods,timeout=1800)',"    from stage1_test_sources import EXTRA_OSD\n    run(prefix,src,mods+EXTRA_OSD,timeout=1800)")
s=s.replace("R/'build/sim/osd_memory_ui'","R/'build/sim'/('stage1_footer_behavior_'+hashlib.sha256((R/'scripts/test_stage1_footer.py').read_bytes()).hexdigest()[:12])")
s=s.replace("f'{mode:<8} {zoom} {pair} {direction} STATE:{status:<16} {model:<8}'","f'{mode:<8} ZOOM {zoom} {pair} {direction} BRT090 6/7 MARK ON  {status:<16}'")
s=s.replace("39'd0,18'd0);","39'd0,18'd90,7'd105,4'd0);")
s=s.replace('osd_english_','stage1_english_')
exec(compile(s,str(R/'scripts/test_osd_memory_ui.py'),'exec'),{'__name__':'__main__','__file__':__file__})
