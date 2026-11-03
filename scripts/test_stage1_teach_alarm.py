"""Restart after a failed replay must not reassert the previous round alarm."""
import argparse,hashlib,json
from refined_testlib import R,run
from test_stage1_teach_integration import BENCH

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--unfiltered',action='store_true');a=ap.parse_args()
    src=BENCH.replace('wire tip,alarm;', 'wire tip,alarm,raw_alarm;reg checking_restart=0;')
    src=src.replace('.alarm(alarm)', '.alarm(raw_alarm)')
    src=src.replace('integer samples=0,clears=0;', ('assign alarm=raw_alarm;' if a.unfiltered else 'stage1_teach_alarm board_alarm(mode,teaching[3:0],raw_alarm,alarm);')+'''
always @(posedge clk)if(checking_restart)begin
if((teaching[3:0]==4 || teaching[3:0]==5) && alarm)$fatal(1,"previous failed round alarm leaked into restart");
if(scene.shared_controller.state==1)checking_restart<=0;end
integer samples=0,clears=0;''')
    src=src.replace('key(2,50);ms(100);same_frame=1;', 'checking_restart=1;key(2,50);ms(100);same_frame=1;')
    src=src.replace('STAGE1_TEACH_INTEGRATION_PASS keys/editor/viewport/guards/no-tip/play-only/PASS/FAIL/stale/clear','STAGE1_TEACH_ALARM_PASS fail/stop/restart/no-old-alarm')
    modules=[R/'rtl/color_regions'/n for n in ('stage1_regions.v','stage1_sequence.v','stage1_controls.v','refined_zoom_geometry.v')]
    if not a.unfiltered:
        wrapper=R/'rtl/color_regions/stage1_memory_video_out.v';link=wrapper.read_text(encoding='utf-8')
        assert '.alarm(stage1_raw_area_alarm)' in link
        assert 'replay_alarm_gate(I_ui_mode,teaching_status[3:0],stage1_raw_area_alarm,O_area_alarm)' in link
        modules.append(wrapper)
    out=run('stage1_teach_alarm',src,modules,expected_failure=a.unfiltered,timeout=180)
    record=R/'reports/refined/regression'/(out.name+'.json');d=json.loads(record.read_text())
    name='scripts/test_stage1_teach_integration.py';d['producer_inputs'][name]=hashlib.sha256((R/name).read_bytes()).hexdigest()
    record.write_text(json.dumps(d,indent=2),encoding='utf-8')

if __name__=='__main__':main()
