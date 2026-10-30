"""Deterministic native-zoom wrappers derived from frozen, hashed templates."""
from pathlib import Path
import re,json,hashlib,argparse
R=Path(__file__).resolve().parents[1]
T=R/'scripts/native_zoom_templates'

def template(name):
    raw=(T/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==json.loads((T/'sources.json').read_text(encoding='utf-8'))[name]['sha256'],name
    return raw.decode('utf-8').replace('\r\n','\n')

def replace(s,old,new,n=1):
    assert old in s,'native generator anchor missing: '+old[:100]
    return s.replace(old,new,n)

def share_native_capture(s):
    # Only the native wrapper changes; original stage1 capture stays immutable.
    a=s.index('module stage1_k_capture #');b=s.index('\nendmodule',a)+len('\nendmodule')
    c=s[a:b]
    c=replace(c,'reg [3:0] vp;reg [1:0] tags[0:3];reg [10:0] xp[0:3];reg [9:0] yp[0:3];',
      'reg [4:0] vp;reg [1:0] tags[0:4];reg [10:0] xp[0:4];reg [9:0] yp[0:4];')
    ga=c.index(' generate for(lane=0;lane<4;lane=lane+1)begin:classify');gb=c.index('endgenerate',ga)+len('endgenerate')
    c=c[:ga]+" wire shared_mask_valid;\n native_shared_classifier classify(clk,rst_n,I_valid,I_rgb,pixel_models,shared_mask_valid,mask);"+c[gb:]
    c=replace(c,'vp[3],xp[3],yp[3],tags[3]','vp[4],xp[4],yp[4],tags[4]')
    c=replace(c,'vp<={vp[2:0],','vp<={vp[3:0],')
    c=replace(c,'for(i=0;i<4;i=i+1)begin xp[i]','for(i=0;i<5;i=i+1)begin xp[i]')
    c=replace(c,'for(i=1;i<4;i=i+1)begin xp[i]','for(i=1;i<5;i=i+1)begin xp[i]')
    c=replace(c,'if(vp[3] && tags[3][1])begin raw_a[tags[3][0]]<=raw_a[tags[3][0]]+population(raw_mask_a);\n raw_b[tags[3][0]]<=raw_b[tags[3][0]]+population(raw_mask_b);',
      'if(vp[4] && tags[4][1])begin raw_a[tags[4][0]]<=raw_a[tags[4][0]]+population(raw_mask_a);\n raw_b[tags[4][0]]<=raw_b[tags[4][0]]+population(raw_mask_b);')
    assert 'vp[3]' not in c and 'tags[3]' not in c
    return s[:a]+c+s[b:]+SHARED_CLASSIFIER

SHARED_CLASSIFIER='// Native reducer emits nonadjacent valid quads. Two unchanged classifiers\n// process the two pixel pairs on successive clocks; masks gain one clock.\n`default_nettype none\nmodule native_shared_classifier(input wire clk,rst_n,valid,input wire [95:0] rgb,\n input wire [127:0] models,output wire ov,output wire [7:0] mask);\n reg second;reg [47:0] tail_rgb;reg [127:0] tail_models;reg [4:0] vp;\n reg [3:0] head_mask;wire [3:0] hit;\n wire [47:0] pair_rgb=second?tail_rgb:rgb[95:48];\n wire [127:0] pair_models=second?tail_models:models;\n stable_model_lane a(clk,rst_n,pair_rgb[47:24],pair_models,hit[1:0]);\n stable_model_lane b(clk,rst_n,pair_rgb[23:0],pair_models,hit[3:2]);\n assign ov=vp[4];assign mask={hit,head_mask};\n always @(posedge clk or negedge rst_n)\n if(!rst_n)begin second<=0;tail_rgb<=0;tail_models<=0;vp<=0;head_mask<=0;end\n else begin\n  second<=valid;vp<={vp[3:0],valid};\n  if(valid)begin tail_rgb<=rgb[47:0];tail_models<=models;end\n  if(vp[3])head_mask<=hit;\n end\nendmodule\n`default_nettype wire\n'

def assets():
    out={}
    config=json.loads((R/'rtl/color_regions/native_zoom_config.json').read_text(encoding='utf-8'))
    assert (config['sensor_width'],config['sensor_height'],config['crop_width'],config['crop_height'])==(2592,1944,2560,1440)
    assert isinstance(config['crop_x'],int) and 0<=config['crop_x']<=32
    assert isinstance(config['crop_y'],int) and 0<=config['crop_y']<=504
    def put(name,s):out['rtl/color_regions/'+name+'.v']=s
    s=template('line_ram.v').replace('fhd_isp_line_ram','native_line_ram').replace('ADDR_BITS=9','ADDR_BITS=10').replace('FHD_BEHAVIORAL_RAM','NATIVE_BEHAVIORAL_RAM')
    put('native_line_ram',s)
    s=template('line_buffer.v').replace('fhd_line_buffer_demosaic','native_line_buffer').replace('fhd_isp_line_ram','native_line_ram')
    s=s.replace('addra[8:0]','addra[9:0]').replace('addrb[8:0]','addrb[9:0]')
    put('native_line_buffer',s)
    s=template('matrix.v').replace('refined_raw_matrix_3x3_buffer','native_raw_matrix').replace('refined_zhenghe','native_zhenghe').replace('fhd_line_buffer_demosaic','native_line_buffer')
    put('native_raw_matrix',s)
    s=template('zhenghe.v').replace('refined_zhenghe','native_zhenghe').replace('fhd_isp_line_ram','native_line_ram')
    s=s.replace('addra[8:0]','addra[9:0]').replace('addrb[8:0]','addrb[9:0]')
    put('native_zhenghe',s)
    s=template('demosaic.v').replace('refined_demosaic','native_demosaic').replace('refined_raw_matrix_3x3_buffer','native_raw_matrix')
    put('native_demosaic',s)
    s=template('clocks.v').replace('fhd_system_pll','native_system_pll')
    put('native_system_pll',s)
    sensor=json.loads((R/'vendor_reference/sc500cs_native_2592.json').read_text(encoding='utf-8'))
    pairs=sensor['sequence']
    s='// SC500CS full-size table; fixed upstream commit and SHA in vendor_reference/sc500cs_native_2592.json.\n'
    s+='module native_sensor_table(input wire [8:0] REG_INDEX,output reg [31:0] REG_DATA,output wire [8:0] REG_SIZE);\n'
    s+=f"assign REG_SIZE=9'd{len(pairs)};\nalways @*case(REG_INDEX)\n"
    for i,(a,v) in enumerate(pairs):s+=f"9'd{i}:REG_DATA={{16'h{a},8'h{v}}};\n"
    s+="default:REG_DATA=0;endcase\nendmodule\n"
    put('native_sensor_table',s)
    put('native_gain_table', '''// Exact algebraic form of the supplied SC500GainTbl, including invalid levels.
module native_gain_table(input wire I_clk,I_rstn,input wire [6:0] I,output reg [15:0] O);
 wire [4:0] upper_step=I-7'd74;
 always @(posedge I_clk)begin
 if(I<32)O<={8'h03,3'b001,I[4:0]};
 else if(I<64)O<={8'h07,3'b001,I[4:0]};
 else if(I<74)O<={8'h0f,3'b001,I[4:0]};
 else if(I<=105)O<={8'h1f,3'b001,upper_step};
 else O<=0;
 end
endmodule
''')
    s=template('camera_config.v').replace('refined_camera_config','native_camera_config')
    s=s.replace('CYCLES_PER_MS=23810,CLK_DIV=239','CYCLES_PER_MS=24000,CLK_DIV=240')
    s=s.replace('uics500reg_720p60 table_init','native_sensor_table table_init')
    s=replace(s,'SC500GainTbl gains','native_gain_table gains')
    s=s.replace('PLL clk1 is 23.809524 MHz. Round up so each millisecond is conservative.','Native camera reference is exactly 24 MHz; HDMI retains its original PLL.')
    s=replace(s,'index==114',f"index=={len(pairs)-2}")
    put('native_camera_config',s)
    s=template('controls.v').replace('module stage1_controls','module native_controls')
    s=replace(s,'O_zoom==4?0:O_zoom+1\'b1','O_zoom==2?0:O_zoom+1\'b1')
    put('native_controls',s)
    s=template('raw_bridge.v').replace('fhd_raw_bridge','native_raw_bridge').replace('fhd_isp_line_ram','native_line_ram')
    s=s.replace('1024 x 40','2048 x 40').replace('GROUPS=480,HEIGHT=1080','GROUPS=648,HEIGHT=1944')
    s=replace(s,'input wire I_sof,I_eof,I_valid,I_line_end,','input wire I_sof,I_eof,I_valid,I_line_end,I_packet_error,')
    s=replace(s,'if(frame_active && !drop_frame && (line_count!=0 || line_index!=HEIGHT))reject_frame(0);',
      'if(frame_active && !drop_frame)reject_frame(0);')
    s=replace(s,'end else if(I_eof)begin','end else if(I_packet_error && frame_active && !drop_frame)begin reject_frame(0);\n  end else if(I_eof)begin')
    s=replace(s,'if(descriptor[64])read_frame_active<=0;','// Keep waiting for the original EOF, including after the last line.')
    s=replace(s,'output reg [31:0] O_overflows,O_bad_lines);','output reg [31:0] O_overflows,O_bad_lines,\n output reg O_verdict,O_good,output reg [31:0] O_verdict_id);')
    s=replace(s,'function [10:0] ungray11;input [10:0] g;integer j;begin\n  ungray11[10]=g[10];for(j=9;j>=0;j=j-1)ungray11[j]=ungray11[j+1]^g[j];end endfunction',
      'function [11:0] ungray12;input [11:0] g;integer j;begin\n  ungray12[11]=g[11];for(j=10;j>=0;j=j-1)ungray12[j]=ungray12[j+1]^g[j];end endfunction')
    s=s.replace('reg [10:0] wr_pointer','reg [11:0] wr_pointer').replace('reg [10:0] rd_gray_w1','reg [11:0] rd_gray_w1')
    s=s.replace('wire [10:0] used=wr_pointer-ungray11','wire [11:0] used=wr_pointer-ungray12').replace('used<=1024-GROUPS','used<=2048-GROUPS')
    s=s.replace('.ADDR_BITS(10)','.ADDR_BITS(11)').replace('wr_pointer[9:0]','wr_pointer[10:0]').replace('rd_pointer[9:0]','rd_pointer[10:0]').replace("11'd1","12'd1")
    anchor=' wire [39:0] ram_data;'
    s=replace(s,anchor,''' wire verdict_ready,good_arrived;wire [31:0] good_id;
 reg good_send;reg [31:0] good_hold;
 target_mailbox #(.WIDTH(32)) source_eof(
 .S_clk(I_rx_clk),.S_rst_n(wr_reset_n),.S_send(good_send),.S_data(good_hold),.S_ready(verdict_ready),
 .D_clk(I_processing_clk),.D_rst_n(rd_reset_n),.D_valid(good_arrived),.D_data(good_id));
'''+anchor)
    s=replace(s,'wr_pointer<=0;line_start<=0;', 'good_send<=0;good_hold<=0;wr_pointer<=0;line_start<=0;')
    s=replace(s,'rd_gray_w1<=rd_gray;rd_gray_w2<=rd_gray_w1;', 'good_send<=0;rd_gray_w1<=rd_gray;rd_gray_w2<=rd_gray_w1;')
    s=replace(s,'if(frame_active && !drop_frame && (line_index!=HEIGHT || line_count!=0))reject_frame(0);',
      '''if(frame_active && !drop_frame)begin
    if(line_index!=HEIGHT || line_count!=0)reject_frame(0);
    else if(verdict_ready)begin good_send<=1;good_hold<=frame_id;end
    else reject_frame(1);
   end''')
    s=replace(s,'O_data<=0;O_valid<=0;', 'O_verdict<=0;O_good<=0;O_verdict_id<=0;O_data<=0;O_valid<=0;')
    s=replace(s,'abort_previous<=abort_sync2;O_abort<=0;', '''abort_previous<=abort_sync2;O_abort<=0;O_verdict<=0;
  if(good_arrived && (!invalid_id_valid || $signed(good_id-invalid_id)>0))begin
   O_verdict<=1;O_good<=1;O_verdict_id<=good_id;
   if(good_id==O_source_id)read_frame_active<=0;
  end''')
    s=replace(s,'invalid_id<=abort_id_r2;invalid_id_valid<=1;', 'O_verdict<=1;O_good<=0;O_verdict_id<=abort_id_r2;invalid_id<=abort_id_r2;invalid_id_valid<=1;')
    s=replace(s,'begin O_abort<=1;await_sof<=1;', 'begin O_verdict<=1;O_good<=0;O_verdict_id<=O_source_id;O_abort<=1;await_sof<=1;')
    put('native_raw_bridge',s)
    s=template('camera.v').replace('module stable_camera_capture','module native_camera_capture')
    s=replace(s,'output wire O_time_valid\n', '''output wire O_time_valid,
    input wire I_verdict_ready,output wire O_source_verdict,O_source_good,
    output wire [31:0] O_verdict_id
''')
    s=s.replace('refined_camera_config u_config','native_camera_config u_config')
    s=s.replace('reg complete_toggle,bad_toggle,frame_open,forward_frame,detect_forward;\nreg [20:0] raw_count;reg old_raw_sof;',
                'wire complete_toggle,bad_toggle;reg forward_frame,detect_forward;')
    s=s.replace('S_ISP_O_tvalid && forward_frame && ready_capture[1] && detect_forward',
                'S_ISP_O_tvalid && forward_frame && ready_capture[1]')
    s=s.replace('S_ISP_O_tuser && forward_frame && ready_capture[1] && detect_forward',
                'S_ISP_O_tuser && forward_frame && ready_capture[1]')
    a=s.index('always @(posedge I_processing_clk or negedge processing_rst_n)begin\n if(!processing_rst_n)begin complete_toggle')
    b=s.index('wire S_csi_hs;',a)
    s=s[:a]+'''wire source_verdict,source_good;wire [31:0] source_verdict_id;
wire full_sof,full_valid;wire [32:0] full_tag;
native_source_gate full_frame_gate(.clk(I_processing_clk),.rst_n(processing_rst_n),
 .begin_frame(S_axis_tuser),.begin_id(bridge_source_id),
 .verdict(source_verdict),.verdict_good(source_good),.verdict_id(source_verdict_id),
 .full_sof(full_sof),.full_valid(full_valid),.full_tag(full_tag),
 .output_ready(I_verdict_ready),.output_valid(O_source_verdict),.output_good(O_source_good),
 .output_id(O_verdict_id),.good_toggle(complete_toggle),.bad_toggle(bad_toggle));
always @(posedge I_processing_clk or negedge processing_rst_n)begin
 if(!processing_rst_n)begin ready_capture<=0;forward_frame<=0;detect_forward<=0;end
 else begin
  ready_capture<={ready_capture[0],O_camera_ready};
  if(!ready_capture[1])begin forward_frame<=0;detect_forward<=0;end
  else begin
   if(raw_sof_internal)forward_frame<=!TIMING || raw_known;
   if(detect_sof_internal)detect_forward<=forward_frame && (!TIMING || detect_known);
  end
  if(bridge_abort)begin forward_frame<=0;detect_forward<=0;end
 end
end
'''+s[b:]
    s=s.replace('fhd_raw_bridge u_raw_bridge','native_raw_bridge u_raw_bridge')
    s=replace(s,'native_raw_bridge u_raw_bridge(','''wire packet_error,checked_eof;
native_csi_guard packet_guard(.clk(S_csi_rx_clk),.rst_n(capture_rst_n),
 .valid(S_hs_rx_valid),.data(S_hs_rx_data),.lane_error(|S_lane_error),
 .packet_error(packet_error),.frame_end(checked_eof));
native_raw_bridge u_raw_bridge(''')
    s=replace(s,'.I_eof(S_raw10_frame_end)', '.I_eof(checked_eof),.I_packet_error(packet_error)')
    s=replace(s,'.O_source_id(bridge_source_id),.O_source_us(bridge_source_us),.O_overflows(),.O_bad_lines());',
        '.O_source_id(bridge_source_id),.O_source_us(bridge_source_us),.O_overflows(),.O_bad_lines(),\n .O_verdict(source_verdict),.O_good(source_good),.O_verdict_id(source_verdict_id));')
    a=s.index('stable_isp u_isp_top (')
    s=s[:a]+'''native_isp #(.CROP_X(NATIVE_CROP_X),.CROP_Y(NATIVE_CROP_Y)) u_isp_top(.clk(I_processing_clk),.rst_n(isp_rst_n),.abort_frame(bridge_abort),
 .sof(S_axis_tuser),.last(S_axis_tlast),.valid(S_axis_tvalid),.data(S_axis_tdata),
 .frame_tag(axis_tag),.gain_r(I_gain_r),.gain_b(I_gain_b),
 .raw_sof(raw_sof_internal),.raw_valid(raw_valid_internal),.raw_rgb(raw_rgb_internal),.raw_tag(raw_tag),
 .detect_sof(detect_sof_internal),.detect_valid(detect_valid_internal),.detect_rgb(detect_rgb_internal),.detect_tag(detect_tag),
 .rgb_sof(S_ISP_O_tuser),.rgb_valid(S_ISP_O_tvalid),.rgb128(S_ISP_O_tdata),
 .full_sof(full_sof),.full_valid(full_valid),.full_tag(full_tag));
endmodule
`default_nettype wire
'''
    s=s.replace('NATIVE_CROP_X',str(config['crop_x'])).replace('NATIVE_CROP_Y',str(config['crop_y']))
    put('native_camera_capture',s)
    s=template('line_core.v').replace('module refined_line_reader','module native_line_core')
    s=replace(s,'input wire [31:0] I_accepted_reads,input wire I_unexpected_return);', '''input wire [31:0] I_accepted_reads,input wire I_unexpected_return,
 input wire [2:0] I_native_zoom,input wire [10:0] I_native_x0,input wire [9:0] I_native_y0,
 output reg [2:0] O_job_zoom,output reg [10:0] O_job_x0,output reg [9:0] O_job_y0,
 output wire [9:0] O_source_y,output wire [1:0] O_source_bank);''')
    s=replace(s,'reg req,req_first,req_rotate;', '''reg [2:0] native_frame_zoom,req_native_zoom;
 reg [10:0] native_frame_x0,req_native_x0;reg [9:0] native_frame_y0,req_native_y0;
 reg req,req_first,req_rotate;''')
    s=replace(s,' assign O_read_addr=', ' assign O_source_y=job_rotate?10\'d719-job_y:job_y;assign O_source_bank=image;\n assign O_read_addr=')
    s=replace(s,'job_cycles<=0;bus_wait<=0;return_wait<=0;drain_cycles<=0;',
      'O_job_zoom<=0;O_job_x0<=0;O_job_y0<=0;job_cycles<=0;bus_wait<=0;return_wait<=0;drain_cycles<=0;')
    s=replace(s,'slot<=req_slot;job_y<=req_y;job_epoch<=req_epoch;',
      'O_job_zoom<=req_native_zoom;O_job_x0<=req_native_x0;O_job_y0<=req_native_y0;slot<=req_slot;job_y<=req_y;job_epoch<=req_epoch;')
    s=replace(s,'pixel_rotate<=1;x<=0;',
      'native_frame_zoom<=0;native_frame_x0<=0;native_frame_y0<=0;req_native_zoom<=0;req_native_x0<=0;req_native_y0<=0;pixel_rotate<=1;x<=0;')
    s=replace(s,'pixel_rotate<=I_rotate;x0<=view_x0;',
      'native_frame_zoom<=I_native_zoom;native_frame_x0<=I_native_x0;native_frame_y0<=I_native_y0;pixel_rotate<=I_rotate;x0<=view_x0;')
    s=replace(s,'req<=~req;',
      'req_native_zoom<=native_frame_zoom;req_native_x0<=native_frame_x0;req_native_y0<=native_frame_y0;req<=~req;')
    s=replace(s,''' wire [47:0] ordered_pair=linegroup >> ((job_rotate?pair_index[2:0]:7-pair_index[2:0])*48);
 wire [47:0] pair_rgb=job_rotate?{ordered_pair[23:0],ordered_pair[47:24]}:ordered_pair;
''','')
    s=replace(s,' wire [3:0] hit;stable_model_lane',
      " wire [47:0] pair_rgb=pair_index[0]?pixel_quad[47:0]:pixel_quad[95:48];\n wire [3:0] hit;stable_model_lane")
    # Exact bounded arithmetic only; preserve buffers and every pipeline stage.
    s=replace(s,' function [24:0] base_for;', ''' // Since 4 == 1 (mod 3), sum the five base-4 digits (range 0..15).
 function [1:0] row_mod3;input [9:0] n;reg [3:0] sum;begin
 sum={2'd0,n[1:0]}+{2'd0,n[3:2]}+{2'd0,n[5:4]}+
     {2'd0,n[7:6]}+{2'd0,n[9:8]};
 case(sum)
 0,3,6,9,12,15:row_mod3=0;
 1,4,7,10,13:row_mod3=1;
 2,5,8,11,14:row_mod3=2;
 default:row_mod3=2'bxx;
 endcase end endfunction
 // Retain the original expression's 25-bit subtraction/multiplication wrap,
 // including req_y > 719. Truncating to 10 bits here would change bad inputs.
 wire [24:0] address_y=(req_first?req_rotate:frame_rotate)?
                         25'd719-{15'd0,req_y}:{15'd0,req_y};
 wire [24:0] row_offset=(address_y<<11)-(address_y<<7);
 function [24:0] base_for;''')
    for signal in ('fy','sy','prefetch'):
        s=replace(s,signal+'%3','row_mod3('+signal+')')
    s=replace(s,"((req_first?req_rotate:frame_rotate)?10'd719-req_y:req_y)*25'd1920",'row_offset')
    put('native_line_core',s)
    s=template('frame_store.v').replace('module refined_frame_store','module native_frame_store')
    s=s.replace('parameter WORDS=172800','parameter WORDS=691200')
    s=s.replace('reg [18:0] count','reg [19:0] count')
    s=replace(s,'I_time_valid,I_invalidate\n',
      'I_time_valid,I_invalidate,\n input wire I_source_verdict,I_source_good,input wire [31:0] I_source_id\n')
    s=replace(s,'reg [3:0] known,complete,has_meta;',
      'reg [3:0] known,complete,has_meta;reg [3:0] source_seen,source_good,qualified;')
    s=replace(s,'complete[selected] && ids[selected]',
      'complete[selected] && source_seen[selected] && source_good[selected] && !(I_source_verdict && I_source_id==selected_id && !I_source_good) && ids[selected]')
    s=replace(s,'select_co=co & id_settled','select_co=co & id_settled & qualified')
    s=replace(s,'  co=complete;hit=0;eligible=0;write_slot=0;', '''  qualified=source_seen & source_good;
  for(i=0;i<4;i=i+1)if(I_source_verdict && known[i] && ids[i]==I_source_id)qualified[i]=I_source_good && (!source_seen[i] || source_good[i]);
  co=complete;hit=0;eligible=0;write_slot=0;''')
    s=replace(s,'known<=0;complete<=0;has_meta<=0;write_bad<=0;',
      'source_seen<=0;source_good<=0;known<=0;complete<=0;has_meta<=0;write_bad<=0;')
    s=replace(s,'   if(I_begin)begin', '''   for(j=0;j<4;j=j+1)if(I_source_verdict && known[j] && ids[j]==I_source_id)begin
     source_seen[j]<=1;source_good[j]<=I_source_good && (!source_seen[j] || source_good[j]);
   end
   if(I_begin)begin
     source_seen[I_bank]<=0;source_good[I_bank]<=0;''')
    s=replace(s,'if(V4 && I_invalidate)begin known<=0;',
      'if(V4 && I_invalidate)begin source_seen<=0;source_good<=0;known<=0;')
    # ID ordering settles long before a complete native frame. Cache the four-
    # bank winner for every availability mask, off the snapshot address path.
    s=replace(s,'reg [3:0] id_settled,newer','reg [3:0] settled_first;reg [3:0] id_settled,newer')
    s=replace(s,'id_settled<=0;for(ai=','id_settled<=0;settled_first<=0;for(ai=')
    s=replace(s,'id_settled<=known;if(I_begin)id_settled[I_bank]<=0;',
      'settled_first<=known;id_settled<=settled_first;if(I_begin)begin settled_first[I_bank]<=0;id_settled[I_bank]<=0;end')
    s=replace(s,'if(V4 && I_invalidate)id_settled<=0;',
      'if(V4 && I_invalidate)begin settled_first<=0;id_settled<=0;end')
    s=replace(s,'reg [9:0] tags[0:3];', '''reg [1:0] newest_table[0:15];integer mi;reg [1:0] ml,mh;
 always @(posedge I_clk)for(mi=0;mi<16;mi=mi+1)begin
 ml=(mi&2) && (!(mi&1) || newer[1][0])?1:0;
 mh=(mi&8) && (!(mi&4) || newer[3][2])?3:2;
 newest_table[mi]<=((mi>>mh)&1) && (!((mi>>ml)&1) || newer[mh][ml])?mh:ml;
 end
 reg [9:0] tags[0:3];''')
    s=replace(s,'newest=select_co[hi] && (!select_co[lo] || newer[hi][lo])?hi:lo;',
      'newest=newest_table[select_co];')
    # Qualify each physical bank directly. A decoded variable array read put
    # the 25-bit address/count mux in front of the snapshot selection path.
    s=replace(s,' wire [1:0] committing=I_addr>=21000000?3:I_addr>=14000000?2:I_addr>=7000000?1:0;',
      ''' wire [3:0] committing_each={I_addr>=21000000,
  I_addr>=14000000 && I_addr<21000000,
  I_addr>=7000000 && I_addr<14000000,I_addr<7000000};''')
    s=replace(s,'''  if(I_write && known[committing])begin
   if(I_addr!=expected[committing] || count[committing]>=WORDS)co[committing]=0;
   else if(count[committing]==WORDS-1 && !write_bad[committing])co[committing]=1;
  end''','''  for(i=0;i<4;i=i+1)if(I_write && known[i] && committing_each[i])begin
   if(I_addr!=expected[i] || count[i]>=WORDS)co[i]=0;
   else if(count[i]==WORDS-1 && !write_bad[i])co[i]=1;
  end''')
    s=replace(s,'''   if(I_write && known[committing])begin
    if(I_addr!=expected[committing] || count[committing]>=WORDS)write_bad[committing]<=1;
    else begin expected[committing]<=expected[committing]+8;count[committing]<=count[committing]+1'b1;end
   end''','''   for(j=0;j<4;j=j+1)if(I_write && known[j] && committing_each[j])begin
    if(I_addr!=expected[j] || count[j]>=WORDS)write_bad[j]<=1;
    else begin expected[j]<=expected[j]+8;count[j]<=count[j]+1'b1;end
   end''')
    s=replace(s,'I_write && committing==I_bank','I_write && committing_each[I_bank]')
    put('native_frame_store',s)
    from generate_stage1 import assets as stage_assets
    base=stage_assets()
    s=base['rtl/color_regions/stage1_memory_video_out.v'].replace('module stage1_memory_video_out','module native_memory_video_out')
    s=replace(s,'input wire [31:0] I_source_id',
      'input wire I_source_verdict,I_source_good,input wire [31:0] I_verdict_id,output wire O_verdict_ready,\n    input wire [31:0] I_source_id')
    s=replace(s,'input wire I_sys_clk, input wire I_rst_n,','input wire I_sys_clk, input wire I_ddr_ref_clk,input wire I_rst_n,')
    s=replace(s,'.I_sys_clk              ( I_sys_clk              )','.I_sys_clk              ( I_ddr_ref_clk          )')
    # Dense packing and reduced SOF can coincide. The writer must freeze the
    # source identity itself, not yesterday's registered detector frame ID.
    s=replace(s,'.I_camera_frame_id(capture_frame_id)', '.I_camera_frame_id(I_source_id)')
    s=replace(s,'.I_frame_us(capture_frame_us),.I_epoch(capture_epoch),.I_time_valid(capture_time_valid)',
      '.I_frame_us(I_source_us),.I_epoch(stream_epoch),.I_time_valid(I_source_time_valid)')
    s=replace(s,'refined_frame_store #(.V4(1)) u_frame_store(', '''wire source_ddr_valid;wire [32:0] source_ddr_data;
    target_mailbox #(.WIDTH(33)) u_source_verdict(
     .S_clk(I_capture_clk),.S_rst_n(capture_rst_n),.S_send(I_source_verdict && O_verdict_ready),
     .S_data({I_source_good,I_verdict_id}),.S_ready(O_verdict_ready),
     .D_clk(S_ddr_clk),.D_rst_n(ddr_rst_n),.D_valid(source_ddr_valid),.D_data(source_ddr_data));
    native_frame_store #(.V4(1)) u_frame_store(
        .I_source_verdict(source_ddr_valid),.I_source_good(source_ddr_data[32]),.I_source_id(source_ddr_data[31:0]),''')
    s=s.replace('refined_line_reader u_scaler','native_line_reader u_scaler')
    s=share_native_capture(s)
    put('native_memory_video_out',s)
    s=base['rtl/color_regions/stage1_top.v']
    s=s.replace('stage1_controls u_controls','native_controls u_controls')
    s=s.replace('stable_camera_capture #','native_camera_capture #')
    s=s.replace('stage1_memory_video_out #','native_memory_video_out #')
    s=replace(s,'wire        \tS_24m_clk;', '''wire        \tS_24m_clk;
wire native_ref_clk,native_processing_clk,native_pll_lock;
wire native_source_verdict,native_source_good,native_verdict_ready;wire [31:0] native_verdict_id;
native_system_pll u_native_pll(.refclk(I_sys_clk),.reset(~I_rst_n),.lock(native_pll_lock),
 .clk0_out(),.clk1_out(native_ref_clk),.clk2_out(native_processing_clk));''')
    s=s.replace('.cam_clk(S_24m_clk)','.cam_clk(native_ref_clk)')
    s=replace(s,'assign S_rst_n = S_pll_lock;', 'assign S_rst_n = S_pll_lock && native_pll_lock;')
    s=replace(s,'.I_camera_ref_clk(S_24m_clk)', '.I_camera_ref_clk(native_ref_clk),.I_processing_clk(native_processing_clk)')
    s=replace(s,'u_camera (', '''u_camera (
    .I_verdict_ready(native_verdict_ready),.O_source_verdict(native_source_verdict),
    .O_source_good(native_source_good),.O_verdict_id(native_verdict_id),''')
    s=replace(s,'u_video (', '''u_video (
    .I_source_verdict(native_source_verdict),.I_source_good(native_source_good),
    .I_verdict_id(native_verdict_id),.O_verdict_ready(native_verdict_ready),''')
    s=replace(s,'.I_sys_clk(I_sys_clk), .I_rst_n(S_rst_n)', '.I_sys_clk(I_sys_clk),.I_ddr_ref_clk(S_100m_clk), .I_rst_n(S_rst_n)')
    s=replace(s,'.gain_changed(event_valid && event_data[3]!=event_previous[3])',
      '.gain_changed((event_valid && event_data[3]!=event_previous[3]) || (cal_active && native_source_verdict && native_verdict_ready && !native_source_good))')
    put('native_top',s)
    project=template('project.al')
    project=project.replace('<Name>target_color_regions_stage1</Name>','<Name>target_color_regions_native_zoom</Name>')
    project=project.replace('../rtl/color_regions/stage1_top.v','../rtl/color_regions/native_top.v')
    project=project.replace('../rtl/color_regions/stage1_memory_video_out.v','../rtl/color_regions/native_memory_video_out.v')
    project=project.replace('Path="target_lock.sdc"','Path="native_zoom.sdc"')
    existing=set(re.findall(r'<File Path="([^"]+)"',project))
    native_files=sorted(set(p.name for p in (R/'rtl/color_regions').glob('native_*.v')) |
                        {Path(n).name for n in out if n.endswith('.v')})
    addition=''
    for i,name in enumerate(native_files,400):
        path='../rtl/color_regions/'+name
        if path in existing:continue
        addition+=f'            <File Path="{path}"><FileInfo><Attr Name="UsedInSyn" Val="true" /><Attr Name="UsedInP&R" Val="true" /><Attr Name="BelongTo" Val="design_1" /><Attr Name="CompileOrder" Val="{i}" /></FileInfo></File>\n'
    project=replace(project,'        </Verilog>',addition+'        </Verilog>')
    out['td_project/target_color_regions_native_zoom.al']=project
    s=(R/'td_project/target_lock.sdc').read_text(encoding='utf-8')
    s=s.replace('-period 4.167 -waveform {0.000 2.083}','-period 2.083 -waveform {0.000 1.042}')
    s='\n'.join(line for line in s.splitlines() if not line.startswith('rename_clock -name {pll_clk_24m}'))+'\n'
    s=s.replace('sys_clk_50m pll_clk_100m pll_clk_24m HDMI_PIXEL_CLK HDMI_SERIAL_CLK',
      'sys_clk_50m pll_clk_100m HDMI_PIXEL_CLK HDMI_SERIAL_CLK')
    a=s.index('set_clock_groups -asynchronous')
    s=s[:a]+'''rename_clock -name {NATIVE_REF_CLK} [get_clocks {u_native_pll/u_core/u_PH1P_PHY_PLL.clkc[1]}]
rename_clock -name {NATIVE_PROCESS_CLK} [get_clocks {u_native_pll/u_core/u_PH1P_PHY_PLL.clkc[2]}]

'''+s[a:]
    s=replace(s,'    -group [get_clocks {u_video/u_ph1p35_324_ddr_wrapper/u_ddr2/ddr_clk',
      '    -group [get_clocks {NATIVE_REF_CLK NATIVE_PROCESS_CLK}] \\\n    -group [get_clocks {u_video/u_ph1p35_324_ddr_wrapper/u_ddr2/ddr_clk')
    # The historical 23.81MHz clock no longer drives camera logic. Keep all
    # existing operative timing constraints; omit its now-empty legacy target.
    s='\n'.join(line for line in s.splitlines() if not line.startswith('set_false_path -from [get_clocks {pll_clk_24m}]') and 'u_camera/u_gain_control/' not in line)+'\n'
    out['td_project/native_zoom.sdc']=s
    s=base['scripts/run_stage1_build.py']
    s=s.replace('from stage1_policy import','from native_zoom_policy import')
    s=s.replace('target_color_regions_stage1.al','target_color_regions_native_zoom.al')
    s=s.replace('target_lock.sdc','native_zoom.sdc')
    s=s.replace("f'stage1_{a.stage}_{stamp}'","f'native_zoom_{a.stage}_{stamp}'")
    marker="paths={project,R/'td_project/stage1_pins.adc',R/'td_project/native_zoom.sdc',R/'rtl/03_tool_detection/target_config.json'}"
    s=replace(s,marker,marker+"\npaths.update({R/'rtl/color_regions/native_zoom_config.json',R/'vendor_reference/sc500cs_native_2592.json'})")
    s=replace(s,'canonical_build_inputs(before)', '''canonical_build_inputs(before)
for name,value in before.items():
 raw=subprocess.check_output(['git','show',created_head+':'+name],cwd=R)
 assert hashlib.sha256(raw).hexdigest()==value,'Commit current compiler input before building: '+name''')
    s=replace(s,"assert prior['stage']=='place' and prior['exit_code']==0 and prior['inputs_unchanged']",
      "assert prior['stage']=='place' and prior['inputs_unchanged']")
    s=replace(s,"assert 'REFINED_PLACED_CHECKPOINT_READY' in (parent/'td.log').read_text(encoding='utf-8')",'''parent_log=(parent/'td.log').read_text(encoding='utf-8')
 from native_gate_recovery import gate_recovery_proof
 recovery=gate_recovery_proof(parent,prior['exit_code'],parent_log)
 from refined_build_report import assess
 assert assess(parent,'synth')['resource_pass'],'Gate RAM/DSP/register limit exceeded' ''')
    s=replace(s,'gate_proof=dict(parent=parent.relative_to(R).as_posix(),',
      'gate_proof=dict(recovery=recovery,parent=parent.relative_to(R).as_posix(),')
    s=replace(s,"t=(R/'scripts/build_target_color_regions.tcl').read_text(encoding='utf-8')",
      "t=(R/'scripts/build_target_color_regions.tcl').read_text(encoding='utf-8').replace('target_lock.sdc','native_zoom.sdc')")
    s=replace(s,"script=out/'run.tcl';script.write_text(t,encoding='utf-8')",'''t=t.replace('puts stderr "BUILD_FAILED: $message"', 'catch {report_area -io_info -file failed_partial.area}\\n catch {report_timing_summary -file failed_partial.timing}\\n puts stderr "BUILD_FAILED: $message"')
script=out/'run.tcl';script.write_text(t,encoding='utf-8')''')
    out['scripts/run_native_zoom_build.py']=s
    s=base['scripts/run_stage1_route.py'].replace('from stage1_policy import','from native_zoom_policy import')
    s=s.replace("f'stage1_route_{stamp}'","f'native_zoom_route_{stamp}'")
    out['scripts/run_native_zoom_route.py']=s
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
    outputs=assets()
    for name,s in outputs.items():
        p=R/name;b=s.encode('utf-8')
        if a.check:assert p.read_bytes()==b,'Generated native mismatch '+name
        elif not p.exists() or p.read_bytes()!=b:p.write_bytes(b)
    print('NATIVE_ZOOM_GENERATOR_CHECK_PASS' if a.check else 'NATIVE_ZOOM_GENERATED',len(outputs))
if __name__=='__main__':main()
