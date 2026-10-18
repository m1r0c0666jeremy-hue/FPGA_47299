"""Re-run independently verified timing changes against actual formal RTL."""
import argparse
from refined_testlib import R,run,literal_fixture

ap=argparse.ArgumentParser();ap.add_argument('--part',required=True,choices=['camera','hue','mailbox']);args=ap.parse_args()
if args.part=='camera':
    formal=R/'rtl/color_regions/stable_top.v'
    candidate=R/'build/refined_camera_relay_prototype/stable_top.v'
    assert formal.read_bytes()==candidate.read_bytes(),'Camera relay differs from independently tested candidate'
    tb=literal_fixture(R/'scripts/refined_camera_relay_prototype.py','tb').replace('CAMERA_RELAY_PRIVATE_PASS','CAMERA_RELAY_EQUIVALENCE_PASS')
    run('camera_relay_equivalence',tb,[formal,R/'rtl/04_tracking/target_mailbox.v'])
elif args.part=='hue':
    formal=R/'rtl/color_regions/stable_model_lane.v'
    candidate=R/'build/refined_hue_retime_prototype/stable_model_lane.v'
    assert formal.read_bytes()==candidate.read_bytes(),'Hue differs from independently tested candidate'
    tb=literal_fixture(R/'scripts/refined_hue_retime_prototype.py','tb').replace('HUE_RETIME_PRIVATE_PASS','HUE_RETIME_EQUIVALENCE_PASS')
    run('hue_retime_equivalence',tb,[R/'build/refined_hue_retime_prototype/reference.v',formal])
else:
    formal=R/'rtl/color_regions/stable_memory_video_out.v'
    candidate=R/'build/refined_recovery_mailbox_prototype/stable_memory_video_out.v'
    # A comment may clarify the settling interval; executable RTL must match.
    import re
    strip=lambda text:re.sub(r'//[^\n]*','',text).replace('\r','')
    assert strip(formal.read_text(encoding='utf-8'))==strip(candidate.read_text(encoding='utf-8')),'Recovery mailbox differs from tested candidate'
    tb=literal_fixture(R/'scripts/refined_recovery_mailbox_prototype.py','tb').replace('RECOVERY_MAILBOX_PRIVATE_PASS','RECOVERY_MAILBOX_EQUIVALENCE_PASS')
    for phase in (0,1,4,9):
        run('recovery_mailbox_equivalence_'+str(phase),tb,[R/'rtl/04_tracking/target_mailbox.v',formal],args=['+PHASE='+str(phase)])
