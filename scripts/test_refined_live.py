"""Real detection, native/command vendor FIFOs, v4 banks, moving video and timing."""
from refined_testlib import R,run
from concurrent.futures import ThreadPoolExecutor
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--reader',choices=['stable','refined'],default='refined');a=ap.parse_args()
s=(R/'sim/tb_stable_live.sv').read_text(encoding='utf-8')
s=s.replace('wire [639:0] cm,dm','wire [767:0] cm,dm').replace('wire [674:0] sd,pd','wire [851:0] sd,pd').replace('wire [639:0] active','wire [767:0] active')
s=s.replace('wire [1:0] selected,zoom,mode;','wire [1:0] selected,mode;wire [2:0] zoom;').replace('reg [1:0] requested_zoom=1,requested_mode=0;','reg [2:0] requested_zoom=2;reg [1:0] requested_mode=0;')
s=s.replace('reg [1:0] last_zoom=1;','reg [2:0] last_zoom=2;').replace('reg [2:0] seen_zooms=0;','reg [4:0] seen_zooms=0;')
s=s.replace('requested_zoom=(frame+1)%3','requested_zoom=(frame+1)%5').replace('seen_zooms!=7','seen_zooms!=31')
s=s.replace('reg [127:0] models;', '''wire [31:0] now_us,gray,cap_now;reg [31:0] source_id=0,source_stamp=0;reg [31:0] expected_stamps[0:31];
refined_timebase tm(pc,rst,now_us,gray);refined_gray_sync ctime_sync(cc,rst,gray,cap_now);
wire [31:0] cfus,wfus,shown_us;wire [15:0] cepoch,wepoch,shown_epoch;wire ctime,wtime,shown_time;
wire lv;wire [31:0] lus,lage;
reg [127:0] models;''')
s=s.replace('reg ready=1,rdvalid=0;', 'wire ready;reg rdvalid=0;')
s=s.replace('video_in writer(', 'refined_video_in writer(').replace('wa,wd,ready);','wa,wd,ready,cfus,cepoch,ctime,wfus,wepoch,wtime);')
s=s.replace('stable_capture capture(', 'stable_capture #(.V4(1)) capture(').replace('ov,cm,dropped);','ov,cm,dropped);')
s=s.replace('cfid,cv,cm,dropped);', "cfid,cv,cm,dropped,source_id,source_stamp,cap_now,16'd7,1'b1,2'd1,42'h123456789ab,cfus,cepoch,ctime);")
s=s.replace('.WIDTH(640)', '.WIDTH(768)').replace('.WIDTH(675)', '.WIDTH(852)')
s=s.replace('stable_frame_store store(', 'stable_frame_store #(.V4(1)) store(').replace('write_id,wr,wa,dr,dm,','write_id,committed,commitaddr,dr,dm,').replace('ss,sd,sg);',"ss,sd,sg,wfus,wepoch,wtime,1'b0);")
s=s.replace('stable_display view(', 'stable_display #(.V4(1)) view(').replace("state,1'(ROTATE),);", "state,1'(ROTATE),,shown_us,shown_epoch,shown_time);")
s=s.replace("video_ok,1'(ROTATE));", "video_ok,1'(ROTATE),1'b1,,,,accepted_reads,unexpected);")
s=s.replace("2'd0,selected_id);", "2'd0,selected_id,commit,lv,lus,lage,128'd0,128'd0,39'd0,18'd0);\nrefined_performance performance(pc,rst,ovs,ode,video_ok,now_us,shown_us,selected_id,32'(source_id),shown_time,lv,lus,lage);")
for axis,N,origin in [('ox',1280,'x0'),('oy',624,'y0')]:
 old=f"ROTATE?{origin}+({N}>>zoom)-1-({axis}>>zoom):{origin}+({axis}>>zoom)"
 s=s.replace(old,f"{origin}+((ROTATE?{N-1}-{axis}:{axis})*ratio_q(zoom))/ratio_p(zoom)")
s=s.replace('function [23:0] pixel', '''function integer ratio_p(input integer z);case(z)1,3:ratio_p=3;2:ratio_p=2;4:ratio_p=4;default:ratio_p=1;endcase endfunction
function integer ratio_q(input integer z);ratio_q=z==1?2:1;endfunction
function [23:0] pixel''')
s=s.replace('active[415:413]!=3','active[415:413]!=4')
s=s.replace('if(active[603:595]', '''if(shown_us!==expected_stamps[selected_id] || !shown_time || shown_epoch!=7 || active[671:640]!=shown_us || active[719:704]!=7 || !active[720] || active[722:721]!=1 || active[764:723]!=42'h123456789ab || active[703:672]<active[671:640])$fatal(1,"v4 timing/model identity lost");
if(active[603:595]''')
s=s.replace('models=models_for(f);revision=', 'source_id=f;source_stamp=cap_now;expected_stamps[f]=source_stamp;models=models_for(f);revision=')
s=s.replace('ready=dc_cycle%19!=0 && dc_cycle%23!=0;rdvalid=0;', 'rdvalid=0;')
s=s.replace('if(re)begin\nif(wrbusy || wr)$fatal(1,"DDR arbitration collision");rbank=ra/7000000;rword=(ra%7000000)/8;', 'if(app_en && cmd[0] && address_ready)begin\nrbank=app_addr/7000000;rword=(app_addr%7000000)/8;')
s=s.replace('reg [31:0] bank_ids', '''wire app_en,wren,committed,unexpected;wire [24:0] app_addr,commitaddr;wire [2:0] cmd;wire [127:0] app_data;wire [9:0] outstanding;wire [31:0] accepted_reads;
wire address_ready=cmd[0]?(dc_cycle%19!=0 && dc_cycle%23!=0):(dc_cycle%13!=0);
wire data_ready=dc_cycle%7!=0;
refined_mc_to_user_interface adapter(.I_clk(dc),.I_rst_n(rst),.I_ddr_user_wr_en(wr),.I_ddr_user_rd_en(re),.I_ddr_user_addr(wr?wa:ra),.I_ddr_user_wr_data(wd),
.O_ddr_user_ready(ready),.O_mc_app_en(app_en),.O_mc_app_addr(app_addr),.O_mc_app_cmd(cmd),.I_mc_app_rdy(address_ready),
.O_mc_app_wdf_wren(wren),.O_mc_app_wdf_data(app_data),.I_mc_app_wdf_rdy(data_ready),.I_mc_app_rd_data(rddata),.I_mc_app_rd_data_end(rdvalid),.I_mc_app_rd_data_valid(rdvalid),
.O_write_commit(committed),.O_write_addr(commitaddr),.O_outstanding_reads(outstanding),.O_unexpected_return(unexpected),.O_accepted_reads(accepted_reads));
reg [31:0] bank_ids''')
s=s.replace('if(beginf)begin', 'if(unexpected)$fatal(1,"unexpected PAXI return");\nif(committed && app_data!==word(bank_ids[commitaddr/7000000],(commitaddr%7000000)/8))$fatal(1,"committed data mismatch");\nif(beginf)begin')
s=s.replace('640/675 CDC','768/852 CDC').replace('three zooms','five rational zooms')
s=s.replace('stable_line_reader reader',a.reader+'_line_reader reader')
# Declare shared handshake nets before their consumers (strict nettype parser).
declaration='wire app_en,wren,committed,unexpected;wire [24:0] app_addr,commitaddr;wire [2:0] cmd;wire [127:0] app_data;wire [9:0] outstanding;wire [31:0] accepted_reads;'
s=s.replace(declaration,'').replace(',dc_cycle=0', '')
s=s.replace('reg cc=0',declaration+'\ninteger dc_cycle=0;\nreg cc=0',1)
mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('stable_awb','stable_packer','stable_capture','stable_model_lane','stable_filter4','stable_grid','regions_divide','stable_tracker','stable_frame_store','stable_display','stable_line_reader','stable_preprocess','stable_osd','stable_glyph_rom','stable_footer_glyph_rom','stable_footer_program_rom','stable_footer_text_rom','refined_zoom_geometry','refined_overlay_geometry','refined_logo_rom','refined_reset_bridge','refined_video_in','refined_mc_to_user_interface','refined_timebase','refined_performance')]
mods += [R/'rtl/04_tracking/target_mailbox.v']
mods=[R/f'rtl/color_regions/{a.reader}_line_reader.v' if p.name=='stable_line_reader.v' else p for p in mods]
mods += [R/'user_source/ip_source'/n for n in ('w128_d512_fifo/w128_d512_fifo.v','w128_d512_fifo/soft_fifo_al_4057d6b76aa6.v','w155_d512_fifo/w155_d512_fifo.v','w155_d512_fifo/soft_fifo_al_f58e8b3e1f3d.v')]
def execute(job):
 pair,rot=job
 return run(f'{a.reader}_v4_live_{pair}_{rot}',s,mods,top='tb_stable_live',compile_args=[f'-Ptb_stable_live.PAIR_MODE={pair}',f'-Ptb_stable_live.ROTATE={rot}'],timeout=3600)
with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(execute,[(p,r) for p in (0,1) for r in (0,1)]))
print('REFINED_LIVE_ALL_PASS 4 jobs, 20 frames, 15974400 image pixels, actual command/native FIFOs and v4 source-time banks')
