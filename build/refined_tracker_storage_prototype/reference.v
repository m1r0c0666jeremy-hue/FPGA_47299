// One selected tool, three consecutive capture frames, signed K=D/L=1/2.
// Missing colours hide the tip immediately; identity expires after 15 new frames.
`default_nettype none
module reference_tracker(input wire clk,rst_n,start,input wire [31:0] frame_id,
 input wire [9:0] command,input wire [15:0] revision,input wire complete,
 input wire [1023:0] candidates,output reg done,
 output reg [127:0] a,b,output reg tip_valid,output reg [10:0] tip_x,
 output reg [9:0] tip_y,output reg [3:0] reason,
 output wire history_valid,output wire [83:0] history_boxes,output wire [1:0] selection_state,
 output wire [9:0] history_command,output wire [15:0] history_revision,output wire [31:0] history_frame,
 output wire [4:0] history_loss,output reg [3:0] tip_bounds);
 reg [4:0] state;reg [3:0] pair_index;reg [31:0] last_id;
 reg [9:0] last_command;reg [15:0] last_revision;
 reg have_id,locked,expired;reg [1:0] streak;reg [4:0] lost;
 reg frame_ok,advance;
 wire [31:0] gap=frame_id-last_id;
 wire [5:0] skipped_loss={1'b0,lost}+{1'b0,gap[4:0]}-1'b1;
 reg [127:0] olda,oldb,besta,bestb;reg [31:0] bestscore;
 reg [7:0] best_quality,rejected;reg [3:0] chosen_indices;reg [1:0] chosen_reason;
 reg [7:0] reject_bits;
 reg diagnostic_found;reg [127:0] diagnostic_a,diagnostic_b;reg [31:0] diagnostic_score;
 reg [7:0] diagnostic_quality,diagnostic_reject;reg [3:0] diagnostic_indices;
 reg have_a,have_b;reg [1:0] first_a,first_b;reg [127:0] single_a,single_b;integer ci;
 reg found;reg [10:0] fax,fbx;reg [9:0] fay,fby;
 reg [127:0] ca,cb;reg signed [12:0] dax,day,dbx,dby,dx,dy,odx,ody;
 wire [7:0] pair_quality={1'b0,ca[89:83]}+{1'b0,cb[89:83]};
 reg [31:0] distance,old_distance,score;reg match,guide;
 reg signed [13:0] nt_x,nt_y;reg [11:0] midx;reg [10:0] midy;
 // Two shared registered multipliers. Never chain a square, sum and comparison
 // through a second DSP in one cycle; all sixteen pairs have fixed latency.
 reg signed [12:0] mx0,my0,mx1,my1;
 reg signed [25:0] product0,product1;
 wire signed [26:0] product_sum=$signed({product0[25],product0})+$signed({product1[25],product1});
 function [12:0] abs13;input signed [12:0] n;begin abs13=n<0?-n:n;end endfunction
 function signed [13:0] half_away;input signed [13:0] n;begin half_away=n<0?-((-n+1)>>>1):((n+1)>>>1);end endfunction
 assign history_valid=locked || streak!=0;assign history_boxes={oldb[41:0],olda[41:0]};
 assign selection_state=expired?3:locked?2:streak!=0?1:0;
 assign history_command=last_command;assign history_revision=last_revision;
 assign history_frame=last_id;assign history_loss=lost;
 always @*begin
 have_a=0;have_b=0;first_a=0;first_b=0;single_a=0;single_b=0;
 for(ci=3;ci>=0;ci=ci-1)begin
 if(candidates[ci*128+120])begin have_a=1;first_a=ci;single_a=candidates[ci*128+:128];end
 if(candidates[(ci+4)*128+120])begin have_b=1;first_b=ci;single_b=candidates[(ci+4)*128+:128];end
 end
 ca=candidates[pair_index[1:0]*128+:128];cb=candidates[(4+pair_index[3:2])*128+:128];
 dx=$signed({2'd0,ca[72:62]})-$signed({2'd0,cb[72:62]});
 dy=$signed({3'd0,ca[82:73]})-$signed({3'd0,cb[82:73]});
 odx=$signed({2'd0,olda[72:62]})-$signed({2'd0,oldb[72:62]});
 ody=$signed({3'd0,olda[82:73]})-$signed({3'd0,oldb[82:73]});
 mx0=dx;my0=dx;mx1=dy;my1=dy;
 if(state==1)begin mx0=odx;my0=odx;mx1=ody;my1=ody;end
 if(state==6)begin mx0=dx;my0=odx;mx1=dy;my1=ody;end
 dax=$signed({2'd0,ca[72:62]})-$signed({2'd0,olda[72:62]});day=$signed({3'd0,ca[82:73]})-$signed({3'd0,olda[82:73]});
 dbx=$signed({2'd0,cb[72:62]})-$signed({2'd0,oldb[72:62]});dby=$signed({3'd0,cb[82:73]})-$signed({3'd0,oldb[82:73]});
 midx={1'b0,ca[72:62]}+cb[72:62];midy={1'b0,ca[82:73]}+cb[82:73];
 guide=midx>=640 && midx<1920 && midy>=360 && midy<1080;
 match=ca[120] && cb[120] && distance>=256 && distance<=360000;
 if(history_valid)begin
 match=match && abs13(dax)<=96 && abs13(day)<=96 && abs13(dbx)<=96 && abs13(dby)<=96 &&
 (product_sum>0) &&
 (distance<<2)>=((old_distance<<1)+old_distance) && ((distance<<1)+distance)<=(old_distance<<2) &&
 {2'd0,ca[61:42]}<=({2'd0,olda[61:42]}<<2) && {2'd0,olda[61:42]}<=({2'd0,ca[61:42]}<<2) &&
 {2'd0,cb[61:42]}<=({2'd0,oldb[61:42]}<<2) && {2'd0,oldb[61:42]}<=({2'd0,cb[61:42]}<<2);
 score=abs13(dax)+abs13(day)+abs13(dbx)+abs13(dby);
 end else begin
 match=match && guide && !expired;
 score=abs13($signed({1'b0,midx})-1280)+abs13($signed({2'd0,midy})-720);
 end
 // Only the best valid diagnostic pair contributes rejection bits. Empty slots
 // cannot turn an unrelated failed pair into a false missing-colour report.
 reject_bits=0;
 if(!ca[120] || !cb[120])reject_bits[0]=1;
 else begin
 reject_bits[2]=distance<256 || distance>360000;
 if(history_valid)begin
 reject_bits[3]=abs13(dax)>96 || abs13(day)>96 || abs13(dbx)>96 || abs13(dby)>96;
 reject_bits[4]=product_sum<=0;
 reject_bits[5]=(distance<<2)<((old_distance<<1)+old_distance) || ((distance<<1)+distance)>(old_distance<<2);
 reject_bits[6]={2'd0,ca[61:42]}>({2'd0,olda[61:42]}<<2) || {2'd0,olda[61:42]}>({2'd0,ca[61:42]}<<2) ||
 {2'd0,cb[61:42]}>({2'd0,oldb[61:42]}<<2) || {2'd0,oldb[61:42]}>({2'd0,cb[61:42]}<<2);
 end else begin reject_bits[1]=!guide;reject_bits[7]=expired;end end
 // Round the complete (3*A-B)/2 once, including negative/outside results.
 nt_x=half_away(($signed({3'd0,fax})<<<1)+$signed({3'd0,fax})-$signed({3'd0,fbx}));
 nt_y=half_away(($signed({4'd0,fay})<<<1)+$signed({4'd0,fay})-$signed({4'd0,fby}));
 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
 state<=0;done<=0;a<=0;b<=0;tip_valid<=0;tip_x<=0;tip_y<=0;reason<=0;pair_index<=0;last_id<=0;
 last_command<=0;last_revision<=0;have_id<=0;locked<=0;expired<=0;streak<=0;lost<=0;olda<=0;oldb<=0;
 besta<=0;bestb<=0;bestscore<=32'hffffffff;found<=0;fax<=0;fbx<=0;fay<=0;fby<=0;
 product0<=0;product1<=0;distance<=0;old_distance<=0;
 frame_ok<=0;advance<=0;
 best_quality<=0;rejected<=0;chosen_indices<=0;chosen_reason<=0;
 diagnostic_found<=0;diagnostic_a<=0;diagnostic_b<=0;diagnostic_score<=32'hffffffff;diagnostic_quality<=0;diagnostic_reject<=0;diagnostic_indices<=0;tip_bounds<=0;
 end else begin
 done<=0;
 case(state)
 0:if(start)begin
 tip_valid<=0;tip_bounds<=0;a<=single_a;b<=single_b;found<=0;bestscore<=32'hffffffff;pair_index<=0;state<=1;
 diagnostic_found<=0;diagnostic_score<=32'hffffffff;diagnostic_quality<=0;diagnostic_reject<=0;diagnostic_indices<={first_b,first_a};
 best_quality<=0;rejected<=0;chosen_indices<=0;chosen_reason<=0;
 frame_ok<=complete;advance<=1;
 if(!have_id || command!=last_command || revision!=last_revision)begin
 locked<=0;streak<=0;lost<=0;expired<=0;olda<=0;oldb<=0;
 last_id<=frame_id;
 end else if(gap==0 || gap[31])begin
 // A duplicate/backwards result is not a new capture frame and cannot consume
 // the identity deadline or move the last accepted frame backwards.
 frame_ok<=0;advance<=0;streak<=0;
 end else begin
 last_id<=frame_id;
 if(gap!=1)begin
 streak<=0;
 if(locked)begin
 if(gap>=16 || skipped_loss>=15)begin locked<=0;expired<=1;lost<=15;end
 else lost<=skipped_loss[4:0];end end end
 last_command<=command;last_revision<=revision;have_id<=1;
 end
 1:if(!command[0])begin locked<=0;streak<=0;lost<=0;expired<=0;reason<=frame_ok?0:8;a<=0;b<=0;state<=4;end
 else if(!frame_ok)begin
 // A bad observation hides annotations, but does not authorize a new tool.
 streak<=0;reason<=8;a<=0;b<=0;
 if(locked && advance)begin
 if(lost>=14)begin locked<=0;expired<=1;lost<=15;end else lost<=lost+1'b1;end
 state<=4;end
 else begin product0<=mx0*my0;product1<=mx1*my1;state<=7;end
 7:begin old_distance<=product_sum;state<=2;end
 2:begin product0<=mx0*my0;product1<=mx1*my1;state<=8;end
 8:begin distance<=product_sum;state<=6;end
 6:begin product0<=mx0*my0;product1<=mx1*my1;state<=9;end
 9:begin
 if(ca[120] && cb[120] && (!diagnostic_found || score<diagnostic_score || (score==diagnostic_score && pair_quality>diagnostic_quality)))begin
 diagnostic_found<=1;diagnostic_a<=ca;diagnostic_b<=cb;diagnostic_score<=score;diagnostic_quality<=pair_quality;diagnostic_reject<=reject_bits;diagnostic_indices<=pair_index;end
 if(match && (!found || score<bestscore || (score==bestscore && pair_quality>best_quality)))begin
 found<=1;bestscore<=score;best_quality<=pair_quality;besta<=ca;bestb<=cb;
 chosen_indices<=pair_index;chosen_reason<=history_valid?2:1;end
 if(pair_index==15)state<=3;else begin pair_index<=pair_index+1'b1;state<=2;end
 end
 3:begin
 if(found)begin
 a<=besta;b<=bestb;olda<=besta;oldb<=bestb;lost<=0;
 if(streak<3)streak<=streak+1'b1;
 if(streak==0 || !locked)begin fax<=besta[72:62];fay<=besta[82:73];fbx<=bestb[72:62];fby<=bestb[82:73];end
 else begin fax<=({1'b0,fax}+besta[72:62]+1)>>1;fay<=({1'b0,fay}+besta[82:73]+1)>>1;
 fbx<=({1'b0,fbx}+bestb[72:62]+1)>>1;fby<=({1'b0,fby}+bestb[82:73]+1)>>1;end
 if(streak>=2)begin locked<=1;reason<=3;end else reason<=2;
 state<=5;
 end else begin
 a<=diagnostic_found?diagnostic_a:single_a;b<=diagnostic_found?diagnostic_b:single_b;
 chosen_indices<=diagnostic_indices;rejected<=diagnostic_found?diagnostic_reject:(!have_a || !have_b)?8'd1:8'd0;
 streak<=0;reason<=expired?6:locked?5:(have_a^have_b)?4:1;
 if(locked)begin if(lost>=14)begin locked<=0;expired<=1;reason<=6;end else lost<=lost+1'b1;end
 state<=4;end end
 5:begin
 tip_bounds<={nt_y>=720,nt_y<0,nt_x>=1280,nt_x<0};
 if(streak>=3 && nt_x>=0 && nt_x<1280 && nt_y>=0 && nt_y<720)begin tip_valid<=1;tip_x<=nt_x[10:0];tip_y<=nt_y[9:0];end
 else if(streak>=3)reason<=7;
 state<=4;end
 4:begin
 // Output candidate A rank is no longer needed by consumers. Its 28 bits carry
 // an atomic decision diagnostic; geometry, count, quality and validity retain
 // their original offsets. Stored identity still uses untouched besta/bestb.
 a[119:92]<={4'd0,tip_bounds,(found?8'd0:rejected),(expired?4'd15:lost[3:0]),streak,
 (found?chosen_reason:((a[120] || b[120])?2'd3:2'd0)),chosen_indices[3:2],chosen_indices[1:0]};
 done<=1;state<=0;end
 endcase end end
endmodule
`default_nettype wire
