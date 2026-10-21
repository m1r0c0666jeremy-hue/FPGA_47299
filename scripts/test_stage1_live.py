"""Actual detector/FIFOs/banks/view/reader connected to the editor and candidate OSD."""
from refined_testlib import R
s=(R/'scripts/test_refined_live.py').read_text(encoding='utf-8')
declarations='''
wire [2:0] an,ae,aa;wire [3:0] ad,ast,ac,ao,acl,aerr,aserr;wire [15:0] arev,anc;wire [671:0] avs;
wire am,alarm,ab,at,amv;wire [1:0] atrend;wire [10:0] adist;wire [19:0] adwell;
reg adown=0,ak2=0;integer point_phase=0,area_observations=0;
stage1_regions regions(pc,rst,2'd1,adown,ak2,1'b0,1'b0,1'b0,1'b1,video_ok,1'b1,1'b0,8'd1,1'(PAIR_MODE),
commit,detection,selected_id,active,an,ad,arev,avs,anc,acl,ast,ac,ao,ae,aa,am,alarm,atrend,adist,adwell,aerr,aserr,ab,at,amv);
always @(posedge pc)if(rst)begin
if(regions.observation)area_observations=area_observations+1;
case(point_phase)
0:if(at)begin adown<=1;point_phase<=1;end
1:begin adown<=0;ak2<=1;point_phase<=2;end
2:begin ak2<=0;point_phase<=3;end
endcase end
'''
extra="2'd1,avs,anc,acl,an,ae,aa,ad,ast,ac,ao,am,atrend,adist,adwell,aerr,aserr,ab,at,1'b0,1'b0,3'd5,"
replacement="s=s.replace('stable_osd osd', 'stage1_osd osd')\ns=s.replace('stage1_osd osd(', "+repr(declarations)+"+'stage1_osd osd('+"+repr(extra)+")"
s=s.replace("s=s.replace('stable_osd osd','refined_osd osd')",replacement)
s=s.replace('rtl/color_regions/refined_osd.v','rtl/color_regions/stage1_osd.v')
coverage='''if(ad!=1 || an!=0 || area_observations<3 || avs[20:0]===21'd0)$fatal(1,"live editor coverage points%0d areas%0d observations%0d phase%0d live%b source%b age%0d",ad,an,area_observations,point_phase,at,regions.source_ok,regions.tip_age);$display("STAGE1_LIVE_EDITOR_PASS observations%0d point%0d/%0d",area_observations,avs[10:0],avs[20:11]);$display("STABLE_LIVE_PASS'''
s=s.replace('\ndef execute(job):',"\nfrom stage1_test_sources import EXTRA_OSD\nmods += EXTRA_OSD+[R/'rtl/color_regions'/n for n in ('stage1_point.v','stage1_segment.v','stage1_validate.v','stage1_sequence.v','stage1_regions.v')]\n"+
"s=s.replace("+repr('$display("STABLE_LIVE_PASS')+','+repr(coverage)+")\n\ndef execute(job):")
s=s.replace("f'{a.reader}_v4_live_","f'stage1_v4_live_").replace('REFINED_LIVE_ALL_PASS','STAGE1_LIVE_ALL_PASS')
exec(compile(s,str(R/'scripts/test_refined_live.py'),'exec'),{'__name__':'__main__','__file__':__file__})
