// Decisions consume fresh source-image results only. All durations use wall milliseconds.
`default_nettype none
module stage1_sequence #(parameter CYCLES_PER_MS=75000,STALE_MS=250,TREND_MS=200,TREND_PIXELS=4)(
 input wire clk,rst_n,input wire [1:0] mode,input wire [2:0] region_count,input wire [3:0] draft_count,
 input wire start_key,pause_key,mute_key,can_start,live,configuration_changed,
 input wire sample,input wire [3:0] inside_mask,near_mask,input wire [43:0] distances,
 output reg [3:0] state,output reg [2:0] expected_area,actual_area,
 output reg [3:0] completed,occupied,output reg muted,
 output wire alarm,output reg [1:0] trend,output wire [10:0] distance,
 output wire [19:0] dwell_ms,output reg [3:0] start_error);
 localparam IDLE=0,ARM=1,RUN=2,PAUSED=3,RESUME=4,PASS=5,FAIL=6,INTERRUPTED=7;
 // Only bounded elapsed ages are observed; saturate at each decision limit.
 // A coincident millisecond tick starts the new age at one, matching the old
 // nonblocking timestamp subtraction exactly, including the 250ms watchdog.
 localparam AGEW=$clog2((STALE_MS>TREND_MS?STALE_MS:TREND_MS)+1);
 reg [16:0] subms;reg [AGEW-1:0] fresh_age,sample_age,trend_age;
 reg [10:0] previous_distance;reg [2:0] trend_target;reg trend_ready;
 reg [7:0] confirmations;reg [1:0] outside_count;reg [1:0] mode_last;
 reg [19:0] stays[0:3],last_stay;reg [3:0] stable_next,enters;reg [7:0] counts_next;
 integer j;reg [2:0] entered;reg multiple;reg [AGEW-1:0] elapsed;reg [20:0] sum_ms;
 wire tick=subms==CYCLES_PER_MS-1;
 wire [2:0] target=mode==1?(region_count==0?3'd0:region_count-1'b1):expected_area;
 assign distance=target<region_count?distances[target*11+:11]:11'd0;
 assign dwell_ms=occupied[0]?stays[0]:occupied[1]?stays[1]:occupied[2]?stays[2]:occupied[3]?stays[3]:
 last_stay;
 assign alarm=mode==2 && state==FAIL && !muted;
 always @*begin
 stable_next=occupied;counts_next=confirmations;enters=0;entered=0;multiple=0;
 for(j=0;j<4;j=j+1)begin
 if(j>=region_count || near_mask[j] || inside_mask[j]==occupied[j])counts_next[j*2+:2]=0;
 else if(confirmations[j*2+:2]==2)begin
 stable_next[j]=inside_mask[j];counts_next[j*2+:2]=0;enters[j]=inside_mask[j];end
 else counts_next[j*2+:2]=confirmations[j*2+:2]+1'b1;
 if(enters[j])begin if(entered!=0)multiple=1;entered=j+1;end
 end end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin subms<=0;fresh_age<=0;sample_age<=0;trend_age<=0;
 previous_distance<=0;trend_target<=0;trend_ready<=0;confirmations<=0;outside_count<=0;mode_last<=0;
 state<=IDLE;expected_area<=0;actual_area<=0;completed<=0;occupied<=0;muted<=0;trend<=0;start_error<=0;last_stay<=0;
 for(j=0;j<4;j=j+1)stays[j]<=0;
 end else begin
 if(tick)begin subms<=0;
 if(fresh_age<STALE_MS)fresh_age<=fresh_age+1'b1;
 if(sample_age<STALE_MS)sample_age<=sample_age+1'b1;
 if(trend_age<TREND_MS)trend_age<=trend_age+1'b1;
 end else subms<=subms+1'b1;
 mode_last<=mode;
 if(mute_key && mode==2 && state==FAIL)muted<=1;
 if(mode!=mode_last || configuration_changed)begin
 if(state==ARM || state==RUN || state==PAUSED || state==RESUME)state<=IDLE;
 occupied<=0;confirmations<=0;outside_count<=0;trend_ready<=0;trend<=0;end
 if(sample && live)begin
 fresh_age<=tick?1'b1:1'b0;sample_age<=tick?1'b1:1'b0;
 if((mode==1) || (mode==2 && (state==ARM || state==RUN || state==RESUME)))begin
 occupied<=stable_next;confirmations<=counts_next;
 elapsed=sample_age;
 for(j=0;j<4;j=j+1)begin
 if(enters[j])begin stays[j]<=0;last_stay<=0;end
 else if(occupied[j] && stable_next[j] && elapsed<STALE_MS)begin
 sum_ms={1'b0,stays[j]}+elapsed;stays[j]<=sum_ms>999900?20'd999900:sum_ms[19:0];
 last_stay<=sum_ms>999900?20'd999900:sum_ms[19:0];end
 end
 if(stable_next!=0 || target!=trend_target || !trend_ready)begin
 trend_ready<=stable_next==0;trend_target<=target;previous_distance<=distance;trend_age<=tick?1'b1:1'b0;trend<=0;
 end else if(trend_age>=TREND_MS)begin
 if({1'b0,distance}+TREND_PIXELS<={1'b0,previous_distance})trend<=1;
 else if({1'b0,previous_distance}+TREND_PIXELS<={1'b0,distance})trend<=2;else trend<=0;
 previous_distance<=distance;trend_age<=tick?1'b1:1'b0;end
 if(mode==2)begin
 if(state==ARM || state==RESUME)begin
 if(inside_mask==0 && near_mask==0)begin
 if(outside_count==2)begin state<=RUN;outside_count<=0;occupied<=0;confirmations<=0;sample_age<=tick?1'b1:1'b0;end
 else outside_count<=outside_count+1'b1;end else outside_count<=0;
 end else if(state==RUN && entered!=0)begin
 actual_area<=entered;
 if(multiple || entered!=expected_area+1'b1)state<=FAIL;
 else begin completed[expected_area]<=1;
 if(expected_area+1'b1==region_count)state<=PASS;else expected_area<=expected_area+1'b1;
 end end end
 end end
 if(mode==2 && pause_key)begin
 if(state==RUN && !(sample && live && entered!=0 &&
 (multiple || entered!=expected_area+1'b1 || expected_area+1'b1==region_count)))begin state<=PAUSED;trend_ready<=0;end
 else if(state==PAUSED && live)begin state<=RESUME;outside_count<=0;occupied<=0;confirmations<=0;sample_age<=tick?1'b1:1'b0;end end
 if(mode==2 && start_key && state!=RUN && state!=ARM && state!=RESUME)begin
 start_error<=0;
 if(region_count==0)start_error<=1;else if(draft_count!=0)start_error<=2;
 else if(!live)start_error<=3;else if(!can_start)start_error<=4;
 else begin state<=ARM;expected_area<=0;actual_area<=0;completed<=0;occupied<=0;confirmations<=0;outside_count<=0;
 muted<=0;trend<=0;trend_ready<=0;fresh_age<=tick?1'b1:1'b0;sample_age<=tick?1'b1:1'b0;last_stay<=0;
 for(j=0;j<4;j=j+1)stays[j]<=0;end end
 if(mode==2 && (state==ARM || state==RUN || state==PAUSED || state==RESUME) &&
 (!live || (!sample && fresh_age>=STALE_MS)))begin
 state<=INTERRUPTED;occupied<=0;confirmations<=0;trend_ready<=0;trend<=0;end
 end end
endmodule
`default_nettype wire
