// Independent volatile red/blue and yellow/purple profiles. Acquisition is
// frame-validated; 512 four-pixel words preserve eight 16x16 source windows.
// Hue and quantiles run serially after sampling. A failed/cancelled transaction
// cannot partially replace a production profile.
`default_nettype none
module stable_calibration(input wire clk,rst_n,sof,valid,input wire [95:0] rgb,
 input wire pair,enter,sample,cancel,gain_changed,
 output wire [11:0] gain_r,gain_b,output wire [127:0] models,
 output reg [15:0] revision,output wire cal_active,needs_cal,
 output wire [7:0] status,output reg frame_pair,output wire [23:0] frame_gains,
 output reg [7:0] frame_status);
 function [63:0] model;input [8:0] lo,hi;input [7:0] mv,dc;input [1:0] sc;begin
 model={1'b1,lo,hi,mv,dc,sc,27'd0};end endfunction
 function [127:0] defaults;input p;begin defaults=p?
 {model(255,330,32,16,1),model(45,75,32,16,1)}:
 {model(195,255,32,16,1),model(345,30,32,16,1)};end endfunction
 reg [127:0] profiles[0:1];reg [11:0] gr[0:1],gb[0:1];reg [1:0] calibrated,required;
 reg [2:0] phase;reg cp;reg [3:0] error;reg [11:0] staged_r,staged_b;reg [63:0] staged_a,staged_model;
 reg [11:0] active_r,active_b;reg [127:0] active_models;reg active_need;
 assign cal_active=phase!=0;assign needs_cal=active_need;
 wire use_staged=phase>=2 && pair==cp && !cancel && !gain_changed;
 assign gain_r=use_staged?staged_r:gr[pair];assign gain_b=use_staged?staged_b:gb[pair];
 assign models=active_models;
 assign frame_gains={active_r,active_b};
 reg collecting,waiting,frame_open;
 reg [5:0] state;assign status={phase,(state!=0 || collecting || waiting),error}; // v3: phase[7:5], busy4, error[3:0]
 (* ram_style="block" *) reg [95:0] samples[0:511];reg [95:0] sample_q;
 reg [8:0] sample_addr;reg sample_write;reg [8:0] sample_wraddr;
 (* ram_style="block" *) reg [95:0] background[0:511];reg [95:0] background_q;
 reg background_valid;
 // Eight stratified positions per axis. Four adjacent pixels at each position;
 // frame-dependent offsets stay inside their 160x90 source cells.
 reg [10:0] background_x;reg [9:0] background_y;
 (* ram_style="block" *) reg [11:0] hist[0:2047];reg [11:0] hq;
 reg [10:0] hist_addr;reg hist_write;reg [11:0] hist_data;
 always @(posedge clk)begin sample_q<=samples[sample_addr];background_q<=background[sample_addr];
 if(sample_write)begin if(phase==2)background[sample_wraddr]<=rgb;else samples[sample_wraddr]<=rgb;end
 hq<=hist[hist_addr];if(hist_write)hist[hist_addr]<=hist_data;end
 reg [3:0] frames;reg [6:0] groups;
 reg [19:0] pixels;reg [10:0] x;reg [9:0] y;
 wire [10:0] rx=sof?0:x;wire [9:0] ry=sof?0:y;
 wire [5:0] jitter_x={frames[2:0],3'b000};
 wire [2:0] jitter_index=frames[2:0]+(frames[2:0]<<1);
 wire background_hit=valid && rx==background_x && ry==background_y;
 wire window_hit=valid && rx>=632 && rx<648 && ry>=352 && ry<368;
 reg [19:0] sr,sg,sb;reg [11:0] bad_white;
 reg [10:0] ar,ag,ab;reg [2:0] bad_group;integer i;
 always @*begin ar=0;ag=0;ab=0;bad_group=0;
 for(i=0;i<4;i=i+1)begin
 ar=ar+rgb[95-i*24-:8];ag=ag+rgb[87-i*24-:8];ab=ab+rgb[79-i*24-:8];
 if(rgb[95-i*24-:8]<16 || rgb[87-i*24-:8]<16 || rgb[79-i*24-:8]<16 ||
 rgb[95-i*24-:8]>240 || rgb[87-i*24-:8]>240 || rgb[79-i*24-:8]>240)bad_group=bad_group+1'b1;
 end end
 localparam IDLE=0,WHITE_R=1,WHITE_R_WAIT=2,WHITE_B=3,WHITE_B_WAIT=4,CLEAR=5,
 PIX_ADDR=6,PIX_WAIT=7,PIX_R=8,PIX_B=9,PIX_M=10,PIX_H=11,H_WAIT=12,S_START=13,S_WAIT=14,
 H_ADDR=15,H_READ=16,H_WRITE=17,PIX_NEXT=18,PEAK_ADDR=19,PEAK_READ=20,
 QUANT_ADDR=21,QUANT_READ=22,MODEL_END=23,
 REPLAY_CLEAR=24,REPLAY_ADDR=25,REPLAY_WAIT=26,REPLAY_WRITE=27,
 SELECT_INIT=28,SELECT_ADDR=29,SELECT_READ=30,SELECT_CHECK=31,
 RETAIN_START=32,RETAIN_WAIT=33,SELECT_NEXT=34,PUBLISH=35;
 reg ds;reg [31:0] numerator,denominator;wire dbusy,ddone;wire [31:0] quotient;
 regions_divide u_div(clk,rst_n,ds,numerator,denominator,dbusy,ddone,quotient);
 reg [10:0] clear_index,pi;reg [1:0] channel;reg pass;
 reg [7:0] r,g,b,m,d;reg [19:0] product;reg [8:0] hue,peak;reg [4:0] sat;
 reg [11:0] eligible,cluster,peak_count,dark_count,weak_count;reg [8:0] frame_samples[0:7],frame_eligible[0:7];
 reg [11:0] window_sum;reg [5:0] peak_slot;reg [1:0] peak_step;
 reg replaying,negative,best_valid,retention_seen;
 reg [6:0] option_index;reg [1:0] option_m,option_d,option_s;reg option_narrow;
 reg [3:0] select_slot;reg [2:0] retain_frame;
 reg [8:0] retained[0:7];reg [11:0] positive_sum,negative_sum,best_negative,best_positive;
 reg negative_ok;reg [8:0] worst_retained,best_worst;
 reg [63:0] best_model;reg [9:0] best_cost;
 reg [8:0] scan;reg [1:0] quant;reg [11:0] cumulative;
 reg [5:0] hlo,hhi;reg got_lo,got_hi;reg [7:0] mlow,dlow;reg [4:0] slow;
 reg [8:0] mxh,mnh;reg [7:0] mx,mn;reg signed [17:0] hn;
 reg family,in_cluster;reg [8:0] circular;reg signed [10:0] diff;
 wire [23:0] pixel=(negative?background_q:sample_q) >> ((3-pi[1:0])*24);
 function [7:0] apply_gain;input [19:0] p;reg [20:0] q;begin q={1'b0,p}+512;apply_gain=q>=261632?255:q[17:10];end endfunction
 function [8:0] wrap;input signed [11:0] n;begin wrap=n<0?n+360:n>=360?n-360:n;end endfunction
 function hue_in;input [8:0] h,lo,hi;begin hue_in=lo>hi?(h>=lo || h<hi):(h>=lo && h<hi);end endfunction
 wire [11:0] q05=(cluster+19)/20,q95=cluster-cluster/20,q10=(cluster+9)/10;
 reg [7:0] min_m,min_d;reg [1:0] sat_code;reg all_frames;
 function [7:0] m_option;input [1:0] n;input [7:0] low,base;reg [7:0] a;begin
 case(n)0:a=base;1:a=low>16?low-16:0;2:a=low>8?low-8:0;default:a=low;endcase
 m_option=a<base?base:a;end endfunction
 function [7:0] d_option;input [1:0] n;input [7:0] low,base;reg [7:0] a;begin
 case(n)0:a=base;1:a=low>4?low-4:0;default:a=low;endcase
 d_option=a<base?base:a;end endfunction
 function sat_ok;input [7:0] mm,dd;input [1:0] code;reg [11:0] a;begin
 case(code)0:a=({4'd0,mm}<<1)+mm;1:a={4'd0,mm}<<2;
 2:a=({4'd0,mm}<<2)+({4'd0,mm}<<1);3:a={4'd0,mm}<<3;endcase
 sat_ok=({4'd0,dd}<<4)>=a;end endfunction
 reg [7:0] om,od;reg [8:0] olo,ohi;reg [63:0] option_model;
 reg option_unique,option_hit,retention_ok;reg [9:0] option_cost;
 wire [8:0] next_worst=quotient[8:0]<worst_retained?quotient[8:0]:worst_retained;
 always @*begin
 sample_addr=pi[10:2];sample_write=collecting && frame_open && (phase==2?background_hit:window_hit) && groups<64;
 sample_wraddr={frames[2:0],groups[5:0]};end
 always @*begin
 mx=r>g?(r>b?r:b):(g>b?g:b);mn=r<g?(r<b?r:b):(g<b?g:b);
 if(mx==r)begin hn=60*($signed({1'b0,g})-$signed({1'b0,b}));if(hn<0)hn=hn+360*(mx-mn);end
 else if(mx==g)hn=120*(mx-mn)+60*($signed({1'b0,b})-$signed({1'b0,r}));
 else hn=240*(mx-mn)+60*($signed({1'b0,r})-$signed({1'b0,g}));
 family=cp?(phase==3?(hue>=30 && hue<90):(hue>=255 && hue<345)):
 (phase==3?(hue>=330 || hue<45):(hue>=165 && hue<270));
 diff=$signed({2'd0,hue})-$signed({2'd0,peak});if(diff>180)diff=diff-360;if(diff< -180)diff=diff+360;
 in_cluster=diff>= -30 && diff<=30;
 hist_addr=0;hist_write=0;hist_data=0;
 if(state==CLEAR)begin hist_addr=clear_index;hist_write=1;hist_data=0;end
 if(state==H_ADDR || state==H_READ || state==H_WRITE)begin
 case(channel)0:hist_addr={2'd0,hue};1:hist_addr=512+m;2:hist_addr=768+d;3:hist_addr=1024+sat;endcase
 if(state==H_WRITE)begin hist_write=1;hist_data=hq+1'b1;end end
 if(state==PEAK_ADDR || state==PEAK_READ)begin
 if(peak_step==0)hist_addr=wrap($signed({6'd0,peak_slot})-30);
 else if(peak_step==1)hist_addr=wrap($signed({3'd0,scan})-31);
 else hist_addr=wrap($signed({3'd0,scan})+30);
 end
 circular=wrap($signed({3'd0,peak})+$signed({3'd0,scan})-30);
 if(state==QUANT_ADDR || state==QUANT_READ)begin
 case(quant)0:hist_addr={2'd0,circular};1:hist_addr=512+scan;2:hist_addr=768+scan;3:hist_addr=1024+scan;endcase end
 min_m=mlow>>1;if(min_m<24)min_m=24;
 min_d=({2'd0,dlow}*3)>>2;if(min_d<8)min_d=8;
 sat_code=(slow*3)>=32?3:(slow*3)>=24?2:(slow*3)>=16?1:0;
 staged_model=model(wrap($signed({3'd0,peak})+$signed({6'd0,hlo})-38),
 wrap($signed({3'd0,peak})+$signed({6'd0,hhi})-21),min_m,min_d,sat_code);
 all_frames=1;for(i=0;i<8;i=i+1)
 if(frame_samples[i]<16 || ({3'd0,frame_samples[i]}*5)<({3'd0,frame_eligible[i]}*3))all_frames=0;
 om=m_option(option_m,mlow,min_m);od=d_option(option_d,dlow,min_d);
 olo=wrap($signed({3'd0,peak})+$signed({6'd0,hlo})-(option_narrow?34:38));
 ohi=wrap($signed({3'd0,peak})+$signed({6'd0,hhi})-(option_narrow?25:21));
 option_model=model(olo,ohi,om,od,option_s);
 option_unique=option_s>=sat_code &&
 (option_m==0 || om!=m_option(option_m-1'b1,mlow,min_m)) &&
 (option_d==0 || od!=d_option(option_d-1'b1,dlow,min_d));
 option_hit=m>=om && d>=od && sat_ok(m,d,option_s) && hue_in(hue,olo,ohi);
 option_cost={2'd0,om-min_m}+{2'd0,od-min_d}+({8'd0,option_s-sat_code}<<4)+(option_narrow?10'd32:10'd0);
 retention_ok=positive_sum>=256 && positive_sum*10>=cluster*9;
 for(i=0;i<8;i=i+1)if(retained[i]<16 || ({3'd0,retained[i]}*5)<({3'd0,frame_samples[i]}*4))retention_ok=0;
 if(state==REPLAY_CLEAR)begin hist_addr=clear_index;hist_write=1;hist_data=0;end
 if(state==REPLAY_ADDR || state==REPLAY_WAIT || state==REPLAY_WRITE)begin
 hist_addr=(negative?11'd768:11'd0)+{option_index,3'b000}+pi[10:8];
 if(state==REPLAY_WRITE && option_unique && option_hit)begin hist_write=1;hist_data=hq+1'b1;end end
 if(state==SELECT_ADDR || state==SELECT_READ)hist_addr=(select_slot[3]?11'd768:11'd0)+{option_index,3'b000}+select_slot[2:0];
 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
 profiles[0]<=defaults(0);profiles[1]<=defaults(1);gr[0]<=1024;gr[1]<=1024;gb[0]<=1024;gb[1]<=1024;calibrated<=0;required<=0;
 phase<=0;cp<=0;error<=0;staged_r<=1024;staged_b<=1024;staged_a<=0;active_r<=1024;active_b<=1024;active_models<=defaults(0);active_need<=0;
 revision<=0;frame_pair<=0;frame_status<=0;state<=0;collecting<=0;waiting<=0;frame_open<=0;frames<=0;groups<=0;pixels<=0;x<=0;y<=0;
 sr<=0;sg<=0;sb<=0;bad_white<=0;ds<=0;numerator<=0;denominator<=0;clear_index<=0;pi<=0;channel<=0;pass<=0;
 r<=0;g<=0;b<=0;m<=0;d<=0;product<=0;hue<=0;peak<=0;sat<=0;eligible<=0;cluster<=0;peak_count<=0;scan<=0;dark_count<=0;weak_count<=0;
 quant<=0;cumulative<=0;hlo<=0;hhi<=0;got_lo<=0;got_hi<=0;mlow<=0;dlow<=0;slow<=0;
 background_valid<=0;background_x<=52;background_y<=17;
 window_sum<=0;peak_slot<=0;peak_step<=0;replaying<=0;negative<=0;best_valid<=0;retention_seen<=0;
 option_index<=0;option_m<=0;option_d<=0;option_s<=0;option_narrow<=0;select_slot<=0;retain_frame<=0;
 positive_sum<=0;negative_sum<=0;best_negative<=0;best_positive<=0;negative_ok<=0;
 worst_retained<=256;best_worst<=0;best_model<=0;best_cost<=0;
 for(i=0;i<8;i=i+1)begin frame_samples[i]<=0;frame_eligible[i]<=0;retained[i]<=0;end
 end else begin
 ds<=0;
 if(sof)begin
 if(frame_pair!=pair || active_r!=gain_r || active_b!=gain_b || active_models!=profiles[pair] || active_need!=(gain_changed?1'b1:required[pair]))revision<=revision+1'b1;
 frame_pair<=pair;active_r<=gain_r;active_b<=gain_b;active_models<=profiles[pair];active_need<=gain_changed?1'b1:required[pair];
 // UI feedback is live; image metadata describes the immutable RAW-SOF state.
 // A successful publication at this edge first applies to the following SOF.
 frame_status<=gain_changed?8'h09:(cancel || (phase!=0 && pair!=cp))?8'd0:status;
 pixels<=valid?4:0;x<=valid?4:0;y<=0;
 if(waiting)begin waiting<=0;collecting<=1;frame_open<=1;frames<=0;groups<=0;background_x<=52;background_y<=17;end
 else if(collecting)begin
 if(pixels!=921600 || groups!=64)begin collecting<=0;frame_open<=0;error<=1;end
 else if(frames==7)begin collecting<=0;frame_open<=0;
 if(phase==2)begin background_valid<=1;phase<=3;state<=IDLE;end
 else state<=phase==1?WHITE_R:CLEAR;
 clear_index<=0;pass<=0;eligible<=0;cluster<=0;peak_count<=0;peak<=0;dark_count<=0;weak_count<=0;
 replaying<=0;negative<=0;window_sum<=0;peak_slot<=0;peak_step<=0;
 for(i=0;i<8;i=i+1)begin frame_samples[i]<=0;frame_eligible[i]<=0;end end
 else begin frames<=frames+1'b1;groups<=0;
 background_x<=52+{(frames[2:0]+3'd1),3'b000};
 background_y<=17+{(jitter_index+3'd3),3'b000};end end
 end else if(valid)begin
 if(pixels<921600)begin pixels<=pixels+4;if(x==1276)begin x<=0;y<=y+1'b1;end else x<=x+4;end
 else pixels<=921601;end
 if(sample_write)begin groups<=groups+1'b1;
 if(phase==2)begin if(groups[2:0]==7)begin background_x<=52+jitter_x;background_y<=background_y+90;end
 else background_x<=background_x+160;end
 if(phase==1)begin sr<=sr+ar;sg<=sg+ag;sb<=sb+ab;bad_white<=bad_white+bad_group;end end
 case(state)
 WHITE_R:if(bad_white>102 || sg<131072 || sg>458752 || sr==0 || sb==0)begin error<=2;state<=IDLE;end
 else begin numerator<=sg<<10;denominator<=sr;ds<=1;state<=WHITE_R_WAIT;end
 WHITE_R_WAIT:if(ddone)begin if(quotient<512 || quotient>2048)begin error<=3;state<=IDLE;end
 else begin staged_r<=quotient[11:0];state<=WHITE_B;end end
 WHITE_B:begin numerator<=sg<<10;denominator<=sb;ds<=1;state<=WHITE_B_WAIT;end
 WHITE_B_WAIT:if(ddone)begin if(quotient<512 || quotient>2048)begin error<=3;state<=IDLE;end
 else begin staged_b<=quotient[11:0];phase<=2;error<=0;state<=IDLE;end end
 CLEAR:begin
 if(clear_index==2047)begin pi<=0;state<=PIX_ADDR;end else clear_index<=clear_index+1'b1;end
 PIX_ADDR:state<=PIX_WAIT;PIX_WAIT:state<=PIX_R;
 PIX_R:begin product<=pixel[23:16]*staged_r;g<=pixel[15:8];state<=PIX_B;end
 PIX_B:begin r<=apply_gain(product);product<=pixel[7:0]*staged_b;state<=PIX_M;end
 PIX_M:begin b<=apply_gain(product);state<=PIX_H;end
 PIX_H:begin m<=mx;d<=mx-mn;
 if(!replaying && !pass)begin
 if(mx<24)dark_count<=dark_count+1'b1;
 else if(mx-mn<8 || (mx-mn)*16<mx*3)weak_count<=weak_count+1'b1;end
 if(mx<24 || mx-mn<8 || (mx-mn)*16<mx*3)state<=PIX_NEXT;
 else begin numerator<={14'd0,hn[17:0]};denominator<=mx-mn;ds<=1;state<=H_WAIT;end end
 H_WAIT:if(ddone)begin hue<=quotient[8:0];
 if(replaying)begin option_index<=0;option_m<=0;option_d<=0;option_s<=0;option_narrow<=0;state<=REPLAY_ADDR;end
 else state<=S_START;end
 S_START:begin
 // Mixed non-neutral colours count against the dominant material even when
 // they fall outside the expected A/B family. Neutral paper was rejected above.
 if(!pass)begin eligible<=eligible+1'b1;frame_eligible[pi[10:8]]<=frame_eligible[pi[10:8]]+1'b1;end
 if(!family || (pass && !in_cluster))state<=PIX_NEXT;
 else begin numerator<=d<<4;denominator<=m;ds<=1;state<=S_WAIT;end end
 S_WAIT:if(ddone)begin sat<=quotient[4:0];channel<=pass?1:0;
 if(pass)begin cluster<=cluster+1'b1;frame_samples[pi[10:8]]<=frame_samples[pi[10:8]]+1'b1;end
 state<=H_ADDR;end
 H_ADDR:state<=H_READ;H_READ:state<=H_WRITE;
 H_WRITE:if(!pass || channel==3)state<=PIX_NEXT;else begin channel<=channel+1'b1;state<=H_ADDR;end
 PIX_NEXT:if(pi==2047)begin
 scan<=0;
 if(replaying)begin
 if(!negative)begin negative<=1;pi<=0;state<=PIX_ADDR;end
 else begin option_index<=0;option_m<=0;option_d<=0;option_s<=0;option_narrow<=0;state<=SELECT_INIT;end end
 else if(!pass)state<=PEAK_ADDR;
 else if(cluster<256 || cluster*5<eligible*3 || !all_frames)begin
 error<=cluster<256?(dark_count>=1024?8:weak_count>=1024?10:4):4;state<=IDLE;end
 else begin quant<=0;cumulative<=0;got_lo<=0;got_hi<=0;state<=QUANT_ADDR;end
 end else begin pi<=pi+1'b1;state<=PIX_ADDR;end
 PEAK_ADDR:state<=PEAK_READ;
 PEAK_READ:begin
 if(peak_step==0)begin window_sum<=window_sum+hq;
 if(peak_slot==60)begin peak_count<=window_sum+hq;peak<=0;scan<=1;peak_step<=1;end
 else peak_slot<=peak_slot+1'b1;state<=PEAK_ADDR;end
 else if(peak_step==1)begin window_sum<=window_sum-hq;peak_step<=2;state<=PEAK_ADDR;end
 else begin window_sum<=window_sum+hq;
 if(window_sum+hq>peak_count)begin peak_count<=window_sum+hq;peak<=scan;end
 if(scan==359)begin pass<=1;clear_index<=512;state<=CLEAR;end
 else begin scan<=scan+1'b1;peak_step<=1;state<=PEAK_ADDR;end end end
 QUANT_ADDR:state<=QUANT_READ;
 QUANT_READ:begin cumulative<=cumulative+hq;
 if(quant==0)begin
 if(!got_lo && cumulative+hq>=q05)begin hlo<=scan[5:0];got_lo<=1;end
 if(!got_hi && cumulative+hq>=q95)begin hhi<=scan[5:0];got_hi<=1;end end
 else if(!got_lo && cumulative+hq>=(quant==3?q10:q05))begin
 got_lo<=1;case(quant)1:mlow<=scan[7:0];2:dlow<=scan[7:0];3:slow<=scan[4:0];endcase end
 if(scan==(quant==0?60:quant==3?16:255))begin
 scan<=0;cumulative<=0;got_lo<=0;if(quant==3)state<=MODEL_END;else begin quant<=quant+1'b1;state<=QUANT_ADDR;end end
 else begin scan<=scan+1'b1;state<=QUANT_ADDR;end end
 MODEL_END:begin
 if(!background_valid)begin error<=6;state<=IDLE;end
 else begin clear_index<=0;replaying<=1;negative<=0;best_valid<=0;retention_seen<=0;state<=REPLAY_CLEAR;end end
 REPLAY_CLEAR:if(clear_index==1535)begin pi<=0;state<=PIX_ADDR;end else clear_index<=clear_index+1'b1;
 REPLAY_ADDR:if(!negative && (!family || !in_cluster))state<=PIX_NEXT;else state<=REPLAY_WAIT;
 REPLAY_WAIT:state<=REPLAY_WRITE;
 REPLAY_WRITE:begin
 if(option_index==95)state<=PIX_NEXT;
 else begin option_index<=option_index+1'b1;option_narrow<=~option_narrow;
 if(option_narrow)begin option_s<=option_s+1'b1;if(option_s==3)begin option_d<=option_d+1'b1;
 if(option_d==2)begin option_d<=0;option_m<=option_m+1'b1;end end end
 state<=REPLAY_ADDR;end end
 SELECT_INIT:begin select_slot<=0;positive_sum<=0;negative_sum<=0;negative_ok<=1;worst_retained<=256;state<=SELECT_ADDR;end
 SELECT_ADDR:state<=SELECT_READ;
 SELECT_READ:begin
 if(!select_slot[3])begin retained[select_slot[2:0]]<=hq[8:0];positive_sum<=positive_sum+hq;end
 else begin negative_sum<=negative_sum+hq;if(hq>1)negative_ok<=0;end
 if(select_slot==15)state<=SELECT_CHECK;else begin select_slot<=select_slot+1'b1;state<=SELECT_ADDR;end end
 SELECT_CHECK:begin
 if(option_unique && retention_ok)retention_seen<=1;
 if(option_unique && retention_ok && negative_ok && negative_sum<=4)begin retain_frame<=0;state<=RETAIN_START;end
 else state<=SELECT_NEXT;end
 RETAIN_START:begin numerator<={15'd0,retained[retain_frame],8'd0};denominator<={23'd0,frame_samples[retain_frame]};ds<=1;state<=RETAIN_WAIT;end
 RETAIN_WAIT:if(ddone)begin worst_retained<=next_worst;
 if(retain_frame==7)begin
 if(!best_valid || negative_sum<best_negative || (negative_sum==best_negative &&
 (next_worst>best_worst || (next_worst==best_worst && (positive_sum>best_positive ||
 (positive_sum==best_positive && option_cost<best_cost))))))begin
 best_valid<=1;best_model<=option_model;best_negative<=negative_sum;best_worst<=next_worst;best_positive<=positive_sum;best_cost<=option_cost;end
 state<=SELECT_NEXT;end else begin retain_frame<=retain_frame+1'b1;state<=RETAIN_START;end end
 SELECT_NEXT:begin
 if(option_index==95)state<=PUBLISH;
 else begin option_index<=option_index+1'b1;option_narrow<=~option_narrow;
 if(option_narrow)begin option_s<=option_s+1'b1;if(option_s==3)begin option_d<=option_d+1'b1;
 if(option_d==2)begin option_d<=0;option_m<=option_m+1'b1;end end end
 state<=SELECT_INIT;end end
 PUBLISH:begin if(!cancel && !gain_changed && pair==cp)begin
 if(!best_valid)begin error<=retention_seen?6:7;state<=IDLE;end
 else if(phase==3)begin staged_a<=best_model;phase<=4;error<=0;state<=IDLE;end
 else if(hue_in(staged_a[62:54],best_model[62:54],best_model[53:45]) ||
 hue_in(best_model[62:54],staged_a[62:54],staged_a[53:45]))begin error<=5;state<=IDLE;end
 else begin profiles[cp]<={best_model,staged_a};gr[cp]<=staged_r;gb[cp]<=staged_b;calibrated[cp]<=1;
 required[cp]<=0;phase<=0;error<=0;state<=IDLE;end end end
 endcase
 if(enter && phase==0)begin background_valid<=0;cp<=pair;phase<=1;error<=0;state<=IDLE;collecting<=0;waiting<=0;frame_open<=0;end
 if(sample && phase!=0 && state==IDLE && !dbusy && !collecting && !waiting)begin waiting<=1;error<=0;sr<=0;sg<=0;sb<=0;bad_white<=0;end
 if(cancel || (phase!=0 && pair!=cp))begin phase<=0;state<=IDLE;collecting<=0;waiting<=0;frame_open<=0;error<=0;end
 if(gain_changed)begin phase<=0;state<=IDLE;collecting<=0;waiting<=0;frame_open<=0;
 // Brightness changes invalidate both profiles without discarding their last
 // complete values. Failed/cancelled relearning still preserves those values;
 // only reset/power loss restores defaults. required blocks tool tracking.
 calibrated<=0;required<=3;error<=9;end
 end end
endmodule
`default_nettype wire
