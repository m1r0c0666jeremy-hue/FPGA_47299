"""Actual detector/FIFOs/banks/view/reader connected to the editor and candidate OSD."""
from refined_testlib import R
s=(R/'scripts/test_refined_live.py').read_text(encoding='utf-8')
# Exercise the corrected production DDR user clock133.333MHz with unchanged
# camera60MHz and pixel75MHz, including real asynchronous vendor FIFOs.
read_clock="s=(R/'sim/tb_stable_live.sv').read_text(encoding='utf-8')"
s=s.replace(read_clock,read_clock+"\ns=s.replace('always #7.5 dc=~dc;','always #3.75 dc=~dc;')")
declarations='''
wire [2:0] an,ae,aa;wire [3:0] ad,ast,ac,ao,acl,aerr,aserr;wire [15:0] arev,anc;wire [671:0] avs,asaved;wire [167:0] adraft;
wire am,alarm,ab,at,amv;wire associated,area_video;wire [1:0] atrend;wire [10:0] adist;wire [19:0] adwell;
wire adown,ak2;reg [2:0] real_keys=7;integer point_phase=0,area_observations=0,key_age=0,real_downs=0,real_clicks=0;
stage1_controls real_controls(.I_clk(pc),.I_rst_n(rst),.I_keys_n(real_keys),.I_ui_switch(2'd1),
.I_gain_ack(1'b0),.I_cal_status(8'd0),.I_pause(1'b0),.I_camera({1'b1,4'd7,4'd0,2'd0,7'd90}),
.O_down2(adown),.O_click2(ak2));
stage1_input_guard guard(pc,rst,rst,1'b1,1'b1,1'b0,video_ok,rde,commit,8'd1,1'(PAIR_MODE),selected_id,shown_epoch,shown_us,shown_time,active,associated,area_video);
stage1_scene regions(pc,rst,2'd1,adown,ak2,1'b0,1'b0,1'b0,1'b1,area_video,1'b1,1'b0,8'd1,1'(PAIR_MODE),
commit,associated,selected_id,active,an,ad,arev,avs,anc,acl,ast,ac,ao,ae,aa,am,alarm,atrend,adist,adwell,aerr,aserr,ab,at,amv,asaved,adraft,,area_video,4'd0,39'd0,,,8'd50);
always @(posedge pc)if(rst)begin
if(regions.real_controller.observation)area_observations=area_observations+1;
if(adown)real_downs=real_downs+1;if(ak2)real_clicks=real_clicks+1;
case(point_phase)
0:if(at && selected_id>=8)begin real_keys<=6;key_age<=0;point_phase<=1;end
1:if(key_age==3750000)begin real_keys<=7;key_age<=0;point_phase<=2;end else key_age<=key_age+1;
2:if(ak2)begin key_age<=0;point_phase<=3;end
3:if(key_age==128)begin if(ad==0)point_phase<=0;else point_phase<=4;end else key_age<=key_age+1;
endcase end
'''
extra="2'd1,asaved,adraft,anc,acl,an,ae,aa,ad,ast,ac,ao,am,atrend,adist,adwell,aerr,aserr,ab,at,1'b0,1'b0,3'd5,"
replacement="s=s.replace('stable_osd osd', 'stage1_osd osd')\ns=s.replace('stage1_osd osd(', "+repr(declarations)+"+'stage1_osd osd('+"+repr(extra)+")"
s=s.replace("s=s.replace('stable_osd osd','refined_osd osd')",replacement)
s=s.replace("39'd0,18'd0);","39'd0,18'd90,7'd105,4'd0,80'd0,23'd0,8'd50,1'b0,8'd0,8'd0,1'b0);")
s=s.replace('rtl/color_regions/refined_osd.v','rtl/color_regions/stage1_osd.v')
coverage='''if(real_downs==0 || real_clicks==0 || ad!=1 || an!=0 || area_observations<3 || avs[20:0]===21'd0)$fatal(1,"live editor coverage points%0d areas%0d observations%0d phase%0d live%b source%b age%0d",ad,an,area_observations,point_phase,at,regions.source_ok,regions.tip_age);$display("STAGE1_LIVE_EDITOR_PASS observations%0d point%0d/%0d",area_observations,avs[10:0],avs[20:11]);$display("STABLE_LIVE_PASS'''
s=s.replace('\ndef execute(job):',"\nfrom stage1_test_sources import EXTRA_OSD\nmods += EXTRA_OSD+[R/'rtl/color_regions'/n for n in ('stage1_sequence.v','stage1_regions.v','stage1_controls.v','stage1_memory_video_out.v')]\n"+
"s=s.replace("+repr('$display("STABLE_LIVE_PASS')+','+repr(coverage)+")\n\ndef execute(job):")
s=s.replace("f'{a.reader}_v4_live_","f'stage1_v4_live_").replace('REFINED_LIVE_ALL_PASS','STAGE1_LIVE_ALL_PASS')
s=s.replace('def execute(job):',"s=s.replace('frame==5','frame==12').replace('checked!=5*1280*624','checked!=12*1280*624').replace('transactions<5','transactions<12').replace('#200000000;','#500000000;')\ns=s.replace('stable_display #(.V4(1)) view(', 'stage1_viewport #(.V4(1)) view(').replace(\"state,1'(ROTATE),,shown_us,shown_epoch,shown_time);\",\"state,1'(ROTATE),,shown_us,shown_epoch,shown_time,39'd0,);\")\ns=s.replace('regions.source_ok','regions.real_controller.source_ok').replace('regions.tip_age','regions.real_controller.tip_age')\n\ndef execute(job):")
s=s.replace("5*jobs,'frames',3993600*jobs","12*jobs,'frames',9584640*jobs")
s=s.replace('timeout=3600','timeout=10800')
s=s.replace("s=s.replace('stable_capture capture(', 'stable_capture #(.V4(1)) capture(')", "s=s.replace('stable_capture capture(', 'stage1_k_capture #(.V4(1)) capture(')")
s=s.replace("cfus,cepoch,ctime);", "cfus,cepoch,ctime,8'd50);")

k_guard='if(!active[249] || {active[248],active[230:224]}!==8\'d50)$fatal(1,"same-image K metadata lost");\nif(active[603:595]'
s=s.replace('def execute(job):', 's=s.replace('+repr('if(active[603:595]')+','+repr(k_guard)+')\n'+'def execute(job):')
# Rebuild both physical colour fixtures while retaining independent geometry.
read="s=(R/'sim/tb_stable_live.sv').read_text(encoding='utf-8')"
patch="\ns=s.replace(\"PAIR_MODE?24'hc8c820:24'hc82020\",\"PAIR_MODE?24'h2020c8:24'hc82020\").replace(\"PAIR_MODE?24'hb420c8:24'h2020c8\",\"PAIR_MODE?24'hb420c8:24'hc8c820\")"
patch+="\ns=s.replace(\"{model(285,302),model(52,69)}:{model(255,330),model(45,75)}\",\"{model(285,302),model(232,249)}:{model(255,330),model(195,255)}\").replace(\"{model(232,249),model(352,9)}:{model(195,255),model(345,30)}\",\"{model(52,69),model(352,9)}:{model(45,75),model(345,30)}\")"
s=s.replace(read,read+patch)
exec(compile(s,str(R/'scripts/test_refined_live.py'),'exec'),{'__name__':'__main__','__file__':__file__})
