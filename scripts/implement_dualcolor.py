"""One-time migration recipe. Refuses to run twice; generation remains separate."""
from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
def read(p):return (r/p).read_text(encoding='utf-8-sig')
def write(p,s):(r/p).write_text(s,encoding='utf-8',newline='\n')
def edit(p,changes):
 s=read(p)
 for a,b in changes:
  assert a in s,(p,a)
  s=s.replace(a,b)
 write(p,s)
cfg=json.loads(read('rtl/03_tool_detection/target_config.json'))
assert 'yp_min' not in cfg,'Already migrated'
cfg.update(yp_min=80,yp_diff=24,yp_ratio_num=5,yp_ratio_den=4,yp_balance=2,long_press_ms=1000)
write('rtl/03_tool_detection/target_config.json',json.dumps(cfg,indent=2)+'\n')
edit('rtl/03_tool_detection/target_detector.v',[
 ('parameter AREA_MIN=64,AREA_MAX=20000,FILL_PERCENT_MIN=30','parameter AREA_MIN=64,AREA_MAX=20000,FILL_PERCENT_MIN=30,\n    parameter YP_MIN=80,YP_DIFF=24,YP_RATIO_NUM=5,YP_RATIO_DEN=4,YP_BALANCE=2'),
 ('output reg [255:0] O_meta','output reg [255:0] O_meta,\n    input wire I_pair,I_enable,input wire [7:0] I_session'),
 ('reg [7:0] r,g,b;','reg [7:0] r,g,b;\n    reg [31:0] lo,hi,other;\n    reg frame_pair,frame_enable;reg [7:0] frame_session;\n    wire selected_pair=sof?I_pair:frame_pair;'),
 ('xx=sof?0:x; yy=sof?0:y;r=0;g=0;b=0;hit=0;','xx=sof?0:x; yy=sof?0:y;r=0;g=0;b=0;hit=0;lo=0;hi=0;other=0;'),
 ('if(c==0) hit=', '''if(selected_pair) begin
                    if(c==0) begin lo=r<g?r:g;hi=r>g?r:g;other=b;end
                    else begin lo=r<b?r:b;hi=r>b?r:b;other=g;end
                    hit=lo>=YP_MIN && lo>=other+YP_DIFF && lo*YP_RATIO_DEN>=other*YP_RATIO_NUM && hi<=lo*YP_BALANCE;
                end else if(c==0) hit='''),
 ('sof_d<=0;seen<=0;frame_id<=0;', 'frame_pair<=0;frame_enable<=0;frame_session<=0;\n            sof_d<=0;seen<=0;frame_id<=0;'),
 ('seen<=1;frame_id<=frame_id+1\'b1;', 'frame_pair<=I_pair;frame_enable<=I_enable;frame_session<=I_session;\n                seen<=1;frame_id<=frame_id+1\'b1;'),
 ('result<=0;result[31:0]<=frame_id;', 'result<=0;result[31:0]<=frame_id;\n                    result[242:235]<=frame_session;result[243]<=frame_pair;result[244]<=frame_enable;')])
edit('rtl/04_tracking/target_tracker.v',[
 ('output reg [255:0] O_meta','output reg [255:0] O_meta,input wire I_pair'),
 ('wire good=geometry', 'wire matching=I_meta[242:235]==I_session && I_meta[243]==I_pair && I_meta[244];\n    wire good=geometry'),
 ('O_meta<=I_meta;O_meta[242:235]<=I_session;', 'O_meta<=I_meta;'),
 ('if(I_enable && I_session==session && I_meta[31:0]!=last_id)', 'if(I_enable && I_session==session && matching && I_meta[31:0]!=last_id)')])
edit('rtl/04_tracking/target_display.v',[
 ('output wire [2:0] O_state','output wire [2:0] O_state,input wire I_pair,output reg O_pair'),
 ('I_data[242:235]==I_session &&', 'I_data[242:235]==I_session && I_data[243]==I_pair && I_data[244] &&'),
 ('active_session==I_session && O_meta[32]', 'active_session==I_session && O_meta[243]==I_pair && O_meta[244] && O_meta[32]'),
 ('O_show<=0;active_session<=0;', 'O_show<=1;O_pair<=0;active_session<=0;'),
 ('if(I_vs&&!vs_d) begin in_blank<=1;', 'if(I_vs&&!vs_d) begin O_show<=I_show;O_pair<=I_pair;in_blank<=1;'),
 ('O_show<=I_show;active_session<=I_session;', 'active_session<=I_session;')])
edit('rtl/00_top_control/criticalwork_top.v',[
 ('wire ui_tracking,ui_show,ui_conflict;', 'wire ui_tracking,ui_show,ui_conflict,ui_pair;'),
 ('target_controls ', 'target_controls #(.LONG_PRESS_MS(1000)) '),
 ('.O_tracking(ui_tracking),', '.O_pair(ui_pair),.O_tracking(ui_tracking),'),
 ('.I_zoom(ui_zoom),.I_tracking', '.I_pair(ui_pair),.I_zoom(ui_zoom),.I_tracking')])
edit('rtl/10_memory_video_out/memory_video_out.v',[
 ('input wire I_tracking,I_show,I_conflict', 'input wire I_pair,I_tracking,I_show,I_conflict'),
 ('wire active_show,tip_valid', 'wire active_pair,active_show,tip_valid'),
 ('[8:0] command_', '[9:0] command_'),
 ('{I_session,I_tracking}', '{I_pair,I_session,I_tracking}'),
 ('#(.WIDTH(9)) u_command', '#(.WIDTH(10)) u_command'),
 ('.I_enable(command_active[0]),', '.I_pair(command_active[9]),.I_enable(command_active[0]),'),
 ('.I_snapshot(pixel_snapshot),', '.I_pair(I_pair),.O_pair(active_pair),.I_snapshot(pixel_snapshot),'),
 ('.I_state(active_status),', '.I_pair(active_pair),.I_state(active_status),')])
edit('scripts/generate_target.py',[
 ("assert 1<=cfg['confirm_frames']", "assert 0<=cfg['yp_min']<=255 and 0<=cfg['yp_diff']<=255\nassert 1<=cfg['yp_ratio_num']<=16 and 1<=cfg['yp_ratio_den']<=16 and 1<=cfg['yp_balance']<=16\nassert 1<=cfg['long_press_ms']<=60000\nassert 1<=cfg['confirm_frames']"),
 ("('FILL_PERCENT_MIN','fill_percent_min')", "('FILL_PERCENT_MIN','fill_percent_min'),('YP_MIN','yp_min'),('YP_DIFF','yp_diff'),('YP_RATIO_NUM','yp_ratio_num'),('YP_RATIO_DEN','yp_ratio_den'),('YP_BALANCE','yp_balance')"),
 ('input wire [95:0] I_rgb,input wire I_enable', 'input wire [95:0] I_rgb,input wire I_pair,input wire I_enable'),
 ('.I_rgb(I_rgb),.O_frame_id', '.I_pair(I_pair),.I_enable(I_enable),.I_session(I_session),.I_rgb(I_rgb),.O_frame_id'),
 ('.I_valid(dv),.I_meta(dm)', '.I_pair(I_pair),.I_valid(dv),.I_meta(dm)'),
 (' KEY3启停"', '"'),
 ("static=['模式：'", "labels=['红色标记点A','蓝色标记点B','黄色标记点A','紫色标记点B','十字准心T','估算尖端']\nstatic=labels+['配色：红蓝黄紫','标注：开关','模式：'"),
 ("'@ROW2@':case_text('红A前 蓝B后 估算尖端：(',0)", "'@ROW2@':case_text('配色：',0)+'\\n'+case_text('估算尖端：(',7)"),
 ("'@ROW3@':case_text(row3)", "'@PAIR_NAMES@':multi(['红蓝','黄紫'],'I_pair'),'@A_NAMES@':multi([labels[0],labels[2]],'I_pair'),'@B_NAMES@':multi([labels[1],labels[3]],'I_pair'),'@TIP_NAME@':case_text(labels[4]),'@TIP_NOTE@':case_text(labels[5]),'@SHOW_NAME@':multi(['关','开'],'I_show'),'@ROW3@':case_text(row3)+'\\n'+case_text('标注：',27)"),
 ("print(f'Generated", "top=ROOT/'rtl/00_top_control/criticalwork_top.v'\ntop.write_text(re.sub(r'LONG_PRESS_MS\\(\\d+\\)',f\"LONG_PRESS_MS({cfg['long_press_ms']})\",top.read_text(encoding='utf-8')),encoding='utf-8',newline='\\n')\nprint(f'Generated")])
# Independent project/output; keep existing constraints and previous bit untouched.
write('td_project/target_lock_dualcolor.al',read('td_project/target_lock.al').replace('<Name>target_lock</Name>','<Name>target_lock_dualcolor</Name>'))
write('scripts/build_target_lock_dualcolor.tcl',read('scripts/build_target_lock.tcl').replace('target_lock','target_lock_dualcolor').replace('TARGET_LOCK_BUILD_COMPLETED','TARGET_LOCK_DUALCOLOR_BUILD_COMPLETED').replace('target_lock_dualcolor.adc','target_lock.adc').replace('target_lock_dualcolor.sdc','target_lock.sdc'))
print('Dual-color interfaces migrated; run generate_target.py after updating OSD template.')
