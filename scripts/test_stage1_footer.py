"""Run independent complete footer pixel oracles against the actual candidate OSD."""
from refined_testlib import R
from stage1_test_sources import OSD_ZERO_ARGS
s=(R/'scripts/test_osd_memory_ui.py').read_text(encoding='utf-8')
s=s.replace('refined_osd dut(', "stage1_osd dut("+OSD_ZERO_ARGS.replace("672'd0,","672'd0,168'd0,",1))
s=s.replace("('refined_osd','refined_english_font_rom'", "('stage1_osd','refined_english_font_rom'")
s=s.replace('    run(prefix,src,mods,timeout=1800)',"    from stage1_test_sources import EXTRA_OSD\n    run(prefix,src,mods+EXTRA_OSD,timeout=1800)")
s=s.replace("R/'build/sim/osd_memory_ui'","R/'build/sim'/('stage1_footer_behavior_'+hashlib.sha256((R/'scripts/test_stage1_footer.py').read_bytes()).hexdigest()[:12])")
# This is the user-visible contract, listed independently from generator ROMs.
short_states={'IDLE':'IDLE','CENTER SELECT':'CENTER SEL','CONFIRMING':'CONFIRMING','TRACKING':'TRACKING',
              'MISSING COLOR':'MISS COLOR','HOLD LOST':'HOLD LOST','RESELECT CENTER':'RESELECT',
              'TIP OUT OF VIEW':'TIP OUT','INVALID FRAME':'BAD FRAME','CAL WHITE':'CAL WHITE',
              'CAL BACKGROUND':'CAL BG','CAL A':'CAL A','CAL B':'CAL B','PROCESSING':'PROCESSING',
              'SAMPLE FAILED':'SAMPLE FAIL','RECALIBRATE':'RECALIBRATE','VIDEO NOT READY':'VIDEO WAIT',
              'KEY CONFLICT':'KEY CONFL','NO NEW FRAME':'NO NEW FR','WAIT RESULT':'WAIT RESULT'}
s=s.replace("    errors=[''",f"    short_states={short_states!r}\n    errors=[''")
s=s.replace("f'{mode:<8} {zoom} {pair} {direction} STATE:{status:<16} {model:<8}'","f'{mode:<8} ZOOM {zoom} {pair} {direction} BRT090 6/7 MARK ON  K0.50 {short_states[status]:<11}'")
s=s.replace("39'd0,18'd0);","39'd0,18'd90,7'd105,4'd0,80'd0,23'd0,8'd50,1'b0,8'd0,8'd0,1'b0);")
s=s.replace("pair='R/B'","pair='R/Y'").replace("pair='Y/P'","pair='B/P'")
# A late tracking transition must keep the already frozen frame, not erase it.
s=s.replace("case('wait_transition',['WAIT RESULT',''])", "case('wait_transition',overview())")
s=s.replace('osd_english_','stage1_english_')
exec(compile(s,str(R/'scripts/test_osd_memory_ui.py'),'exec'),{'__name__':'__main__','__file__':__file__})
