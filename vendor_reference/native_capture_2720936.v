// Frozen four-lane capture from 272093698d78acd31789ce97f47164495bb6e370.
`default_nettype none
module frozen_native_capture #(parameter V4=0)(input wire I_clk,I_rst_n,I_sof,I_valid,I_fault,
 input wire [95:0] I_rgb,input wire I_pair,I_enable,input wire [7:0] I_session,
 input wire [127:0] I_models,input wire [15:0] I_revision,
 input wire [23:0] I_gains,input wire [7:0] I_cal_status,input wire I_cal_active,I_needs_cal,
 input wire I_result_ready,output reg [31:0] O_frame_id,
 output reg O_valid,output wire [(V4?768:640)-1:0] O_meta,output reg [31:0] O_dropped,
 input wire [31:0] I_source_id,I_source_us,I_now_us,input wire [15:0] I_epoch,
 input wire I_time_valid,input wire [1:0] I_model_state,input wire [41:0] I_quality,
 output reg [31:0] O_frame_us,output reg [15:0] O_epoch,output reg O_time_valid,input wire [7:0] I_k_value);
 wire clk=I_clk,rst_n=I_rst_n;reg last_sof,have,cb,accepted;
 wire sof=I_sof && !last_sof;wire nb=have?!cb:1'b0;
 reg [1:0] owned,pending,complete,closed;reg [3:0] invalid_drain[0:1];
 wire take=!owned[nb];reg [19:0] pixels;reg fault;reg [10:0] x;reg [9:0] y;
 wire [10:0] rx=sof?0:x;wire [9:0] ry=sof?0:y;
 reg [7:0] bank_k[0:1];reg [31:0] ids[0:1];reg [9:0] cmds[0:1];reg [127:0] models[0:1];
 reg [31:0] source_us[0:1];reg [15:0] epochs[0:1];reg [1:0] time_valid;
 reg [1:0] model_states[0:1];reg [41:0] qualities[0:1];
 reg [15:0] revs[0:1];reg [23:0] gains[0:1],mean[0:1];reg [7:0] status[0:1];reg [1:0] needs,sample_ok;
 reg [19:0] raw_a[0:1],raw_b[0:1],filtered_a[0:1],filtered_b[0:1];
 function [2:0] population;input [3:0] v;begin population={2'd0,v[0]}+v[1]+v[2]+v[3];end endfunction
 reg [13:0] sr,sg,sb;reg [6:0] sn;reg [10:0] ar,ag,ab;reg [2:0] an;integer i;
 always @*begin ar=0;ag=0;ab=0;an=0;
 for(i=0;i<4;i=i+1)if(rx+i>=636 && rx+i<644 && ry>=356 && ry<364)begin
 ar=ar+I_rgb[95-24*i-:8];ag=ag+I_rgb[87-24*i-:8];ab=ab+I_rgb[79-24*i-:8];an=an+1'b1;end end
 reg [3:0] vp;reg [1:0] tags[0:3];reg [10:0] xp[0:3];reg [9:0] yp[0:3];
 wire [7:0] mask;genvar lane;
 wire [3:0] raw_mask_a={mask[6],mask[4],mask[2],mask[0]},raw_mask_b={mask[7],mask[5],mask[3],mask[1]};
 // Calibration commits at pre-AWB SOF. The last two post-AWB groups of the
 // previous frame may still be in flight then: classify them with their bank's
 // frozen model, and select the new profile only at the post-AWB SOF itself.
 wire [127:0] pixel_models=sof?I_models:(have?models[cb]:I_models);
 generate for(lane=0;lane<4;lane=lane+1)begin:classify
 stable_model_lane u_lane(clk,rst_n,I_rgb[95-lane*24-:24],pixel_models,mask[lane*2+:2]);end endgenerate
 wire fv;wire [1:0] ft;wire [10:0] fx;wire [9:0] fy;wire [7:0] fa,fb;
 stable_filter4 filter(clk,rst_n,vp[3],xp[3],yp[3],tags[3],mask,fv,ft,fx,fy,fa,fb);
 reg gs,ts,wb;wire gb,gd,gfailed;wire [1023:0] candidates;wire [17:0] work_cycles;
 wire hist_valid;wire [83:0] hist_boxes;
 wire [9:0] hist_command;wire [15:0] hist_revision;wire [31:0] hist_frame;wire [4:0] hist_loss;wire [3:0] tip_bounds;
 wire detect_allowed=cmds[wb][0] && !needs[wb] && status[wb][7:5]==0;
 wire [1:0] selected_state;wire [31:0] history_gap=ids[wb]-hist_frame;
 wire history_for_bank_now=hist_valid && hist_command=={cmds[wb][9:1],detect_allowed} && hist_revision==revs[wb] &&
 history_gap!=0 && !history_gap[31] && history_gap<=15 && ({27'd0,hist_loss}+history_gap)<=15 &&
 (selected_state==2 || history_gap==1);
 // state 0 selects wb; state 1 freezes its history predicate and issues gs.
 // The grid samples both on the next edge. Its candidate/result cycles do not
 // change, and the history command/revision/frame/lifetime checks stay intact.
 reg history_for_bank;
 stable_grid grid(clk,rst_n,fv && ft[1],ft[0],fx,fy,fa,fb,gs,wb,
 history_for_bank,hist_boxes,history_for_bank,gb,gd,gfailed,candidates,work_cycles);
 wire td,tv;wire [127:0] a,b;wire [10:0] tx;wire [9:0] ty;wire [3:0] reason;
 wire work_complete=complete[wb] && !gfailed;
 stage1_k_tracker tracker(clk,rst_n,ts,ids[wb],{cmds[wb][9:1],detect_allowed},revs[wb],work_complete,
 candidates,td,a,b,tv,tx,ty,reason,hist_valid,hist_boxes,selected_state,hist_command,hist_revision,hist_frame,hist_loss,tip_bounds,bank_k[wb]);
 reg [2:0] state;reg [767:0] packet,waiting_packet;reg waiting_result;
 always @(posedge clk or negedge rst_n)
 if(!rst_n)history_for_bank<=0;
 else if(state==1)history_for_bank<=history_for_bank_now;
 // The mailbox samples only on O_valid. This independent pending bank is
 // already immutable until its next complete result copy; a second 640-bit
 // output register adds no protection. Do not issue a pulse on a copy cycle:
 // the following source edge must sample the packet identified by that pulse.
 assign O_meta=waiting_packet[(V4?768:640)-1:0];
 function [3:0] failure_stage;input c;reg [19:0] raw,filtered;reg [2:0] n,gr;begin
 raw=c?raw_b[wb]:raw_a[wb];filtered=c?filtered_b[wb]:filtered_a[wb];
 n=c?candidates[635:633]:candidates[123:121];gr=c?candidates[639:637]:candidates[127:125];
 failure_stage=!complete[wb]?6:gfailed?7:needs[wb] || status[wb][7:5]!=0?9:
 raw==0?1:filtered==0?2:n!=0?5:gr==3?3:4;end endfunction
 always @*begin
 packet=0;
 packet[230:224]=bank_k[wb][6:0];packet[248]=bank_k[wb][7];packet[249]=1;packet[31:0]=ids[wb];packet[32]=tv;packet[36:33]=reason;
 packet[47:37]=a[72:62];packet[57:48]=a[82:73];packet[68:58]=b[72:62];packet[78:69]=b[82:73];
 packet[89:79]=tx;packet[99:90]=ty;packet[141:100]=a[41:0];packet[183:142]=b[41:0];
 packet[203:184]=a[61:42];packet[223:204]=b[61:42];
 packet[232:231]=work_complete?0:2;packet[234:233]=work_complete?0:2;
 packet[242:235]=cmds[wb][8:1];packet[243]=cmds[wb][9];packet[244]=cmds[wb][0];
 packet[245]=a[120] && work_complete && detect_allowed;packet[246]=b[120] && work_complete && detect_allowed;
 packet[247]=complete[wb];packet[255]=1;packet[407:384]=mean[wb];packet[408]=sample_ok[wb];packet[415:413]=V4?4:3;
 packet[412:409]=tip_bounds;
 packet[543:416]=models[wb];packet[559:544]=revs[wb];packet[567:560]=status[wb];
 packet[568]=needs[wb];packet[592:569]=gains[wb];
 packet[594:593]=selected_state;
 // A single selected tool is identified within its user-started session.
 packet[603:595]={cmds[wb][8:1],cmds[wb][9]};
 packet[275:256]=raw_a[wb];packet[295:276]=raw_b[wb];packet[315:296]=filtered_a[wb];packet[335:316]=filtered_b[wb];
 packet[338:336]=work_complete?candidates[123:121]:0;packet[341:339]=work_complete?candidates[635:633]:0;
 packet[345:342]=failure_stage(0);packet[349:346]=failure_stage(1);
 packet[356:350]=a[89:83];packet[363:357]=b[89:83];packet[365:364]=a[93:92];packet[367:366]=a[95:94];
 packet[369:368]=a[97:96];packet[377:370]=a[111:104];packet[379:378]=a[99:98];packet[383:380]=a[103:100];
 packet[604]=complete[wb];packet[605]=work_complete && candidates[124];packet[606]=work_complete && candidates[636];
 packet[624:607]=complete[wb]?work_cycles:0;packet[639:625]=O_dropped>32767?15'd32767:O_dropped[14:0];
 packet[671:640]=source_us[wb];packet[703:672]=I_now_us;packet[719:704]=epochs[wb];
 packet[720]=time_valid[wb];packet[722:721]=model_states[wb];packet[764:723]=qualities[wb];
 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
 last_sof<=0;have<=0;cb<=0;accepted<=0;owned<=0;pending<=0;complete<=0;closed<=0;pixels<=0;fault<=0;x<=0;y<=0;
 sr<=0;sg<=0;sb<=0;sn<=0;needs<=0;sample_ok<=0;vp<=0;gs<=0;ts<=0;wb<=0;state<=0;
 waiting_packet<=0;waiting_result<=0;O_frame_id<=0;O_valid<=0;O_dropped<=0;O_frame_us<=0;O_epoch<=0;O_time_valid<=0;time_valid<=0;
 for(i=0;i<2;i=i+1)begin bank_k[i]<=50;ids[i]<=0;cmds[i]<=0;models[i]<=0;revs[i]<=0;gains[i]<=0;mean[i]<=0;status[i]<=0;invalid_drain[i]<=0;
 raw_a[i]<=0;raw_b[i]<=0;filtered_a[i]<=0;filtered_b[i]<=0;end
 for(i=0;i<4;i=i+1)begin xp[i]<=0;yp[i]<=0;tags[i]<=0;end end
 else begin
 last_sof<=I_sof;gs<=0;ts<=0;O_valid<=0;
 vp<={vp[2:0],I_valid && (sof || have) && (sof || pixels<921600)};
 xp[0]<=rx;yp[0]<=ry;tags[0]<=sof?{take,nb}:{accepted,cb};
 for(i=1;i<4;i=i+1)begin xp[i]<=xp[i-1];yp[i]<=yp[i-1];tags[i]<=tags[i-1];end
 if(vp[3] && tags[3][1])begin raw_a[tags[3][0]]<=raw_a[tags[3][0]]+population(raw_mask_a);
 raw_b[tags[3][0]]<=raw_b[tags[3][0]]+population(raw_mask_b);end
 if(fv && ft[1])begin filtered_a[ft[0]]<=filtered_a[ft[0]]+population(fa[3:0]);filtered_b[ft[0]]<=filtered_b[ft[0]]+population(fb[3:0]);end
 for(i=0;i<2;i=i+1)if(invalid_drain[i]!=0)begin
 invalid_drain[i]<=invalid_drain[i]-1'b1;if(invalid_drain[i]==1)pending[i]<=1;end
 if(sof)begin
 if(have && accepted)begin closed[cb]<=1;complete[cb]<=pixels==921600 && !fault && !I_fault;end
 if(have && accepted && pixels!=921600)begin complete[cb]<=0;invalid_drain[cb]<=8;end
 have<=1;cb<=nb;accepted<=take;O_frame_id<=V4?I_source_id:O_frame_id+1'b1;
 O_frame_us<=I_source_us;O_epoch<=I_epoch;O_time_valid<=I_time_valid;
 pixels<=I_valid?4:0;x<=I_valid?4:0;y<=0;fault<=0;sr<=0;sg<=0;sb<=0;sn<=0;
 if(take)begin
 raw_a[nb]<=0;raw_b[nb]<=0;filtered_a[nb]<=0;filtered_b[nb]<=0;
 bank_k[nb]<=I_k_value;owned[nb]<=1;closed[nb]<=0;complete[nb]<=0;ids[nb]<=V4?I_source_id:O_frame_id+1'b1;cmds[nb]<={I_pair,I_session,I_enable};
 source_us[nb]<=I_source_us;epochs[nb]<=I_epoch;time_valid[nb]<=I_time_valid;model_states[nb]<=I_model_state;qualities[nb]<=I_quality;
 models[nb]<=I_models;revs[nb]<=I_revision;gains[nb]<=I_gains;status[nb]<=I_cal_status;needs[nb]<=I_needs_cal;
 end else O_dropped<=O_dropped+1'b1;
 end else begin
 // video_in clears its sticky flag at its packed SOF, two clocks after our
 // RGB SOF. The first four groups provide that boundary settling interval;
 // a genuine new-frame overflow remains sticky and is caught afterwards.
 if(I_fault && pixels>=16)begin fault<=1;if(accepted)complete[cb]<=0;end
 if(I_valid && have)begin
 if(pixels<921600)begin
 pixels<=pixels+4;if(x==1276)begin x<=0;y<=y+1'b1;end else x<=x+4;
 sr<=sr+ar;sg<=sg+ag;sb<=sb+ab;sn<=sn+an;
 if(pixels==921596 && accepted)begin complete[cb]<=!fault && !I_fault;mean[cb]<={sr[13:6],sg[13:6],sb[13:6]};sample_ok[cb]<=sn==64;end
 end else begin fault<=1;if(accepted)complete[cb]<=0;end end end
 if(fv && ft[1] && fx==1276 && fy==719)pending[ft[0]]<=1;
 if(waiting_result && I_result_ready && state!=5)begin O_valid<=1;waiting_result<=0;end
 case(state)
 0:if(pending!=0)begin wb<=pending[0]?0:1;pending[pending[0]?0:1]<=0;state<=1;end
 1:if(complete[wb])begin gs<=1;state<=2;end else state<=3;
 2:if(gd)state<=3;
 3:if(closed[wb])begin ts<=1;state<=4;end
 4:if(td)state<=5;
 5:begin
 if(waiting_result)O_dropped<=O_dropped+1'b1;
 waiting_packet<=packet;waiting_result<=1;owned[wb]<=0;state<=0;
 end
 endcase end end
endmodule
`default_nettype wire
