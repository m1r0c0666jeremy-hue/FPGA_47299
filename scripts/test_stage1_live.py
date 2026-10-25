"""Actual detector/FIFOs/banks/view/reader connected to the editor and candidate OSD."""
from refined_testlib import R
s=(R/'scripts/test_refined_live.py').read_text(encoding='utf-8')
declarations='''
wire [2:0] an,ae,aa;wire [3:0] ad,ast,ac,ao,acl,aerr,aserr;wire [15:0] arev,anc;wire [671:0] avs,asaved;wire [167:0] adraft;
wire am,alarm,ab,at,amv;wire associated,area_video;wire [1:0] atrend;wire [10:0] adist;wire [19:0] adwell;
wire adown,ak2;reg [2:0] real_keys=7;integer point_phase=0,area_observations=0,key_age=0,real_downs=0,real_clicks=0;
stage1_controls real_controls(.I_clk(pc),.I_rst_n(rst),.I_keys_n(real_keys),.I_ui_switch(2'd1),
.I_gain_ack(1'b0),.I_cal_status(8'd0),.I_pause(1'b0),.I_camera({1'b1,4'd7,4'd0,2'd0,7'd90}),
.O_down2(adown),.O_click2(ak2));
stage1_input_guard guard(pc,rst,rst,1'b1,1'b1,1'b0,video_ok,rde,commit,8'd1,1'(PAIR_MODE),selected_id,shown_epoch,shown_us,shown_time,active,associated,area_video);
stage1_regions regions(pc,rst,2'd1,adown,ak2,1'b0,1'b0,1'b0,1'b1,area_video,1'b1,1'b0,8'd1,1'(PAIR_MODE),
commit,associated,selected_id,active,an,ad,arev,avs,anc,acl,ast,ac,ao,ae,aa,am,alarm,atrend,adist,adwell,aerr,aserr,ab,at,amv,asaved,adraft,);
always @(posedge pc)if(rst)begin
if(regions.observation)area_observations=area_observations+1;
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
s=s.replace("39'd0,18'd0);","39'd0,18'd90,7'd105,4'd0);")
s=s.replace('rtl/color_regions/refined_osd.v','rtl/color_regions/stage1_osd.v')
coverage='''if(real_downs==0 || real_clicks==0 || ad!=1 || an!=0 || area_observations<3 || avs[20:0]===21'd0)$fatal(1,"live editor coverage points%0d areas%0d observations%0d phase%0d live%b source%b age%0d",ad,an,area_observations,point_phase,at,regions.source_ok,regions.tip_age);$display("STAGE1_LIVE_EDITOR_PASS observations%0d point%0d/%0d",area_observations,avs[10:0],avs[20:11]);$display("STABLE_LIVE_PASS'''
s=s.replace('\ndef execute(job):',"\nfrom stage1_test_sources import EXTRA_OSD\nmods += EXTRA_OSD+[R/'rtl/color_regions'/n for n in ('stage1_sequence.v','stage1_regions.v','stage1_controls.v')]\n"+
"s=s.replace("+repr('$display("STABLE_LIVE_PASS')+','+repr(coverage)+")\n\ndef execute(job):")
s=s.replace("f'{a.reader}_v4_live_","f'stage1_v4_live_").replace('REFINED_LIVE_ALL_PASS','STAGE1_LIVE_ALL_PASS')
s=s.replace('def execute(job):',"s=s.replace('frame==5','frame==12').replace('checked!=5*1280*624','checked!=12*1280*624').replace('transactions<5','transactions<12').replace('#200000000;','#500000000;')\n\ndef execute(job):")
s=s.replace("5*jobs,'frames',3993600*jobs","12*jobs,'frames',9584640*jobs")
s=s.replace('timeout=3600','timeout=10800')
exec(compile(s,str(R/'scripts/test_refined_live.py'),'exec'),{'__name__':'__main__','__file__':__file__})
