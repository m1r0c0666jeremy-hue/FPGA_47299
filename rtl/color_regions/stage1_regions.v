// UI editor and image-bound region observations, entirely in the display domain.
`default_nettype none
module stage1_regions #(parameter CYCLES_PER_MS=75000)(input wire clk,rst_n,
 input wire [1:0] mode,input wire down2,click2,click3,click4,cancel,
 input wire tracking,video_ok,camera_ready,gain_busy,input wire [7:0] session,
 input wire pair,frame_commit,detection_valid,input wire [31:0] image_id,input wire [767:0] meta,
 output reg [2:0] region_count,output reg [3:0] draft_count,
 output reg [15:0] revision,output wire [671:0] render_vertices,
 output wire [15:0] render_counts,output wire [3:0] closed_mask,
 output wire [3:0] run_state,completed,occupied,output wire [2:0] expected_area,actual_area,
 output wire muted,alarm,output wire [1:0] trend,output wire [10:0] distance,
 output wire [19:0] dwell_ms,output reg [3:0] edit_error,output wire [3:0] start_error,
 output wire busy,tip_live,metrics_valid,output wire [671:0] saved_vertices,output wire [167:0] draft_vertices,output wire [3:0] tip_reason);

 // Only two corners per area are stored. Wide legacy ports are zero padded;
 // no arbitrary polygon, iterative multiplier/divider or bitmap is instantiated.
 reg [41:0] rectangles[0:3];reg [41:0] draft;
 reg seen;reg [31:0] last_id;reg [15:0] last_epoch,last_model;
 reg [7:0] last_session,session_last,point_session;reg [1:0] mode_last;
 reg [16:0] subms;reg [8:0] tip_age;reg [20:0] edit_point;
 reg [15:0] point_model,point_epoch;reg point_pair;reg point_pending;reg [2:0] edit_request;
 reg [3:0] point_failure;
 reg observation,configuration_changed,metrics_good;
 reg [3:0] observed_in,observed_near;
 wire packet_ok=detection_valid && meta[255] && meta[247] && meta[415:413]==4 &&
 meta[31:0]==image_id && meta[242:235]==session && meta[243]==pair && meta[244];
 wire source_ok=packet_ok && meta[32] && meta[89:79]<1280 && meta[99:90]<720;
 wire point_context=point_session==session && point_model==meta[559:544] && point_epoch==meta[719:704] && point_pair==pair;
 wire [3:0] live_reason=gain_busy?6:!camera_ready?2:!tracking?1:!video_ok?3:
 !packet_ok?9:!meta[32] || meta[89:79]>=1280 || meta[99:90]>=720?4:tip_age>=250?5:0;
 assign tip_reason=mode==1 && point_failure!=0?point_failure:live_reason;
 // The top gates tracking with camera-ready; preserve the specific cause.
 wire [3:0] point_reason=gain_busy?6:!camera_ready?2:!tracking?1:!packet_ok?9:!point_context?8:live_reason;
 wire execute_edit=mode==1 && mode==mode_last && session==session_last && !cancel;
 wire execute_point=execute_edit && tip_live && point_context;
 assign tip_live=tracking && camera_ready && video_ok && source_ok && tip_age<250 && !gain_busy;
 assign metrics_valid=metrics_good && tip_live && seen && image_id==last_id && session==last_session &&
 meta[719:704]==last_epoch && meta[559:544]==last_model;
 assign busy=edit_request!=0;
 assign trend=2'd0;assign distance=11'd0;
 reg [671:0] saved_data,draw_data;reg [15:0] draw_counts;reg [3:0] draw_closed;
 integer j,ov_index,data_index,obs_index;
 always @*begin
 saved_data=0;draw_data=0;draw_counts=0;draw_closed=0;
 for(j=0;j<4;j=j+1)begin
 saved_data[j*168+:42]=rectangles[j];draw_data[j*168+:42]=rectangles[j];
 if(j<region_count)begin draw_counts[j*4+:4]=2;draw_closed[j]=1;end
 else if(j==region_count && draft_count!=0)begin draw_data[j*168+:42]=draft;draw_counts[j*4+:4]=draft_count;end
 end end
 assign saved_vertices=saved_data;assign draft_vertices={126'd0,draft};
 assign render_vertices=draw_data;assign render_counts=draw_counts;assign closed_mask=draw_closed;
 wire [10:0] dx0=draft[10:0],dx1=draft[31:21];wire [9:0] dy0=draft[20:11],dy1=draft[41:32];
 wire [10:0] xmin=dx0<dx1?dx0:dx1,xmax=dx0>dx1?dx0:dx1;
 wire [9:0] ymin=dy0<dy1?dy0:dy1,ymax=dy0>dy1?dy0:dy1;
 wire [41:0] normalized={ymax,xmax,ymin,xmin};
 reg overlap;
 always @*begin overlap=0;
 for(ov_index=0;ov_index<4;ov_index=ov_index+1)if(ov_index<region_count &&
 xmin<=rectangles[ov_index][31:21] && xmax>=rectangles[ov_index][10:0] &&
 ymin<=rectangles[ov_index][41:32] && ymax>=rectangles[ov_index][20:11])overlap=1;
 end
 function contains;input [41:0] r;input [10:0] px;input [9:0] py;
 begin contains=px>=r[10:0] && px<=r[31:21] && py>=r[20:11] && py<=r[41:32];end endfunction
 function border_band;input [41:0] r;input [10:0] px;input [9:0] py;
 reg signed [12:0] l,t,h,b,sx,sy;
 begin l=$signed({2'd0,r[10:0]});h=$signed({2'd0,r[31:21]});
 t=$signed({3'd0,r[20:11]});b=$signed({3'd0,r[41:32]});
 sx=$signed({2'd0,px});sy=$signed({3'd0,py});
 // A two-source-pixel rectangular guard band. No Euclidean distance is claimed.
 border_band=sx>=l-13'sd2 && sx<=h+13'sd2 && sy>=t-13'sd2 && sy<=b+13'sd2 &&
 !(sx>l+13'sd2 && sx<h-13'sd2 && sy>t+13'sd2 && sy<b-13'sd2);
 end endfunction
 stage1_sequence #(.CYCLES_PER_MS(CYCLES_PER_MS)) sequence_controller(clk,rst_n,mode,region_count,draft_count,
 click2,click3,click4,!busy,tip_live,configuration_changed,observation,observed_in,observed_near,44'd0,
 run_state,expected_area,actual_area,completed,occupied,muted,alarm,,,dwell_ms,start_error,1'b0);
 // Payload is invalid above region/draft counts and is overwritten before reuse.
 always @(posedge clk)begin
 if(edit_request==1 && execute_point && region_count<4 && draft_count<2)begin
 if(draft_count==0)draft[20:0]<=edit_point;else draft[41:21]<=edit_point;end
 if(edit_request==2 && execute_point && draft_count==2 && region_count<4 &&
 xmax-xmin>=6 && ymax-ymin>=6 && !overlap)begin
 for(data_index=0;data_index<4;data_index=data_index+1)if(region_count==data_index)rectangles[data_index]<=normalized;
 end end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
 region_count<=0;draft_count<=0;revision<=0;seen<=0;last_id<=0;last_epoch<=0;last_model<=0;last_session<=0;
 session_last<=0;point_session<=0;point_model<=0;point_epoch<=0;point_pair<=0;point_failure<=0;mode_last<=0;subms<=0;tip_age<=250;
 edit_point<=0;point_pending<=0;edit_request<=0;observation<=0;configuration_changed<=0;
 observed_in<=0;observed_near<=0;metrics_good<=0;edit_error<=0;
 end else begin
 observation<=0;configuration_changed<=0;mode_last<=mode;session_last<=session;
 if(subms==CYCLES_PER_MS-1)begin subms<=0;if(tip_age<250)tip_age<=tip_age+1'b1;end
 else subms<=subms+1'b1;
 if(!seen || image_id!=last_id || session!=last_session || meta[719:704]!=last_epoch || meta[559:544]!=last_model)begin
 if(packet_ok && tracking && camera_ready && video_ok && !gain_busy)begin
 seen<=1;last_id<=image_id;last_session<=session;last_epoch<=meta[719:704];last_model<=meta[559:544];tip_age<=0;
 for(obs_index=0;obs_index<4;obs_index=obs_index+1)begin
 observed_in[obs_index]<=obs_index<region_count && contains(rectangles[obs_index],meta[89:79],meta[99:90]);
 observed_near[obs_index]<=obs_index<region_count && border_band(rectangles[obs_index],meta[89:79],meta[99:90]);end
 observation<=source_ok;metrics_good<=source_ok;
 if(seen && (meta[719:704]!=last_epoch || meta[559:544]!=last_model))begin configuration_changed<=1;observation<=0;end
 end end
 if(mode==1 && down2 && !cancel)begin point_failure<=0;edit_error<=0;point_pending<=tip_live && !busy;
 if(tip_live && !busy)begin edit_point<={meta[99:90],meta[89:79]};point_session<=session;point_model<=meta[559:544];
 point_epoch<=meta[719:704];point_pair<=pair;end
 else begin edit_error<=busy?4'd8:4'd5;point_failure<=busy?4'd0:live_reason;end end
 if(mode==1 && !busy && !cancel)begin
 if(click2)begin
 if(point_pending && tip_live && point_context)edit_request<=1;
 else begin edit_error<=point_failure!=0?4'd9:4'd5;if(point_failure==0)point_failure<=live_reason;end
 point_pending<=0;end
 else if(click3)begin edit_request<=4;point_failure<=0;end
 else if(click4)begin edit_request<=3;point_failure<=0;end
 end
 if(edit_request!=0)begin edit_request<=0;edit_error<=0;
 if(execute_edit)case(edit_request)
 1:if(region_count==4)edit_error<=4;else if(draft_count==2)edit_error<=6;
 else if(!execute_point)begin edit_error<=9;point_failure<=point_reason;end
 else begin draft_count<=draft_count+1'b1;revision<=revision+1'b1;configuration_changed<=1;metrics_good<=0;
 if(draft_count==1)edit_request<=2;end
 2:if(!execute_point)begin edit_error<=9;point_failure<=point_reason;end
 else if(draft_count!=2)edit_error<=1;else if(region_count==4)edit_error<=4;
 else if(xmax-xmin<6 || ymax-ymin<6)edit_error<=2;
 else if(overlap)edit_error<=3;
 else begin region_count<=region_count+1'b1;draft_count<=0;revision<=revision+1'b1;configuration_changed<=1;metrics_good<=0;end
 3:if(draft_count!=0)begin draft_count<=draft_count-1'b1;revision<=revision+1'b1;configuration_changed<=1;metrics_good<=0;end
 else if(region_count!=0)begin region_count<=region_count-1'b1;revision<=revision+1'b1;configuration_changed<=1;metrics_good<=0;end
 else edit_error<=7;
 4:if(draft_count!=0)begin draft_count<=0;revision<=revision+1'b1;configuration_changed<=1;metrics_good<=0;end
 default:begin end endcase
 else begin edit_error<=9;point_failure<=7;end end
 if(point_pending && (cancel || (!down2 && (!tip_live || !point_context))))begin
 point_pending<=0;edit_error<=9;point_failure<=cancel?4'd7:point_reason;end
 if(mode!=mode_last || session!=session_last)begin point_pending<=0;configuration_changed<=1;observation<=0;
 if(mode!=1)edit_request<=0;end
 end end
endmodule

// Region input validity uses committed image identity, not the reader's
// intentional VS blanking pulse. Active-video faults still invalidate at once.
module stage1_input_guard(input wire clk,rst_n,stream_n,tracking,camera_ready,gain_busy,
 input wire raw_video_ok,reader_de,frame_commit,input wire [7:0] session,input wire pair,
 input wire [31:0] image_id,input wire [15:0] image_epoch,input wire [31:0] image_us,
 input wire time_valid,input wire [767:0] meta,output wire associated,video_ok);
 reg admitted;
 assign associated=meta[255] && meta[247] && meta[415:413]==4 && meta[31:0]==image_id &&
 meta[719:704]==image_epoch && meta[671:640]==image_us && meta[720] && time_valid &&
 meta[242:235]==session && meta[243]==pair && meta[244]==tracking;
 wire active_fault=reader_de && !raw_video_ok;
 assign video_ok=admitted && stream_n && !active_fault;
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)admitted<=0;
 else if(!stream_n || !tracking || !camera_ready || gain_busy || !associated || active_fault)admitted<=0;
 else if(raw_video_ok)admitted<=1;
 end
endmodule
`default_nettype wire

// Shared unsigned division uses no DSPs. RAM payloads and arithmetic operands
// are never asynchronously reset; validity is owned by their controller.
`default_nettype none
module stage1_teach_div(input wire clk,rst_n,start,input wire [31:0] numerator,
 input wire [15:0] denominator,output reg done,output reg [31:0] quotient);
 reg busy;reg [5:0] left;reg [31:0] bits;reg [16:0] rem;reg [15:0] den;
 wire [17:0] shifted={rem,bits[31]};wire take=shifted>={2'd0,den};
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin busy<=0;left<=0;bits<=0;rem<=0;den<=1;done<=0;quotient<=0;end
 else begin done<=0;
 if(busy)begin rem<=take?shifted-{2'd0,den}:shifted;bits<={bits[30:0],take};
 if(left==1)begin quotient<={bits[30:0],take};busy<=0;done<=1;end else left<=left-1'b1;end
 if(start)begin busy<=1;left<=32;bits<=numerator;rem<=0;den<=denominator==0?16'd1:denominator;end
 end end
endmodule

// Motion uses Chebyshev point-to-rectangle distance max(dx,dy).
// Position spread still determines STILL independently of distance changes.
module stage1_motion #(parameter CYCLES_PER_MS=75000)(input wire clk,rst_n,active,sample,
 input wire [10:0] x,input wire [9:0] y,input wire [41:0] rectangle,
 input wire [18:0] identity,output reg [1:0] trend,output reg [10:0] distance,output reg valid);
 reg [16:0] subms;reg [15:0] now_ms,last_sample,first_ms,baseline_ms,calc_ms;
 reg [18:0] last_identity;reg seen,baseline_ready,warm;reg [10:0] baseline;
 reg [20:0] history[0:15];reg [15:0] times[0:15];reg [4:0] count;reg [3:0] wr,scan;
 reg [10:0] minx,maxx;reg [9:0] miny,maxy;reg still_now;
 reg [2:0] phase;
 reg [10:0] min_dist;reg [9:0] lasty;reg [10:0] lastx;
 wire [10:0] dx=x<rectangle[10:0]?rectangle[10:0]-x:x>rectangle[31:21]?x-rectangle[31:21]:11'd0;
 wire [10:0] ddy=y<rectangle[20:11]?{1'b0,rectangle[20:11]-y}:y>rectangle[41:32]?{1'b0,y-rectangle[41:32]}:11'd0;
 wire [15:0] sample_age=now_ms-last_sample,window_age=now_ms-first_ms,entry_age=calc_ms-times[scan];
 wire [15:0] baseline_age=calc_ms-baseline_ms;
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin subms<=0;now_ms<=0;last_sample<=0;first_ms<=0;baseline_ms<=0;calc_ms<=0;
 last_identity<=0;seen<=0;baseline_ready<=0;warm<=0;baseline<=0;count<=0;wr<=0;scan<=0;phase<=0;
 minx<=0;maxx<=0;miny<=0;maxy<=0;still_now<=0;trend<=0;distance<=0;valid<=0;min_dist<=0;lastx<=0;lasty<=0;end
 else begin
 if(subms==CYCLES_PER_MS-1)begin subms<=0;now_ms<=now_ms+1'b1;end else subms<=subms+1'b1;
 if(seen && window_age>=500)warm<=1;
 if(!active || identity!=last_identity)begin
 last_identity<=identity;seen<=0;baseline_ready<=0;warm<=0;count<=0;wr<=0;phase<=0;valid<=0;trend<=0;end
 else case(phase)
 0:if(sample && (!seen || sample_age>=50))begin
 if(!seen)first_ms<=now_ms;seen<=1;last_sample<=now_ms;calc_ms<=now_ms;
 history[wr]<={y,x};times[wr]<=now_ms;wr<=wr+1'b1;if(count<16)count<=count+1'b1;
 minx<=x;maxx<=x;miny<=y;maxy<=y;scan<=0;still_now<=warm || (window_age>=500 && seen);
 min_dist<=dx>ddy?dx:ddy;phase<=4;
 end
 4:begin
 if({1'b0,scan}<count && entry_age<=500)begin
 if(history[scan][10:0]<minx)minx<=history[scan][10:0];if(history[scan][10:0]>maxx)maxx<=history[scan][10:0];
 if(history[scan][20:11]<miny)miny<=history[scan][20:11];if(history[scan][20:11]>maxy)maxy<=history[scan][20:11];end
 if(scan==15)phase<=5;else scan<=scan+1'b1;
 end
 5:begin
 distance<=min_dist;valid<=1;
 if(!baseline_ready)begin baseline<=min_dist;baseline_ms<=calc_ms;baseline_ready<=1;trend<=0;end
 else if(baseline_age>=200)begin
 if(still_now && maxx-minx<=4 && maxy-miny<=4)trend<=3;
 else if({1'b0,min_dist}+12'd4<={1'b0,baseline})trend<=1;
 else if({1'b0,baseline}+12'd4<={1'b0,min_dist})trend<=2;else trend<=0;
 baseline<=min_dist;baseline_ms<=calc_ms;end
 phase<=0;
 end
 default:phase<=0;
 endcase
 end end
endmodule
`default_nettype wire

`default_nettype none
module stage1_route #(parameter CYCLES_PER_MS=75000,MAX_MS=30000,MAX_POINTS=602)(
 input wire clk,rst_n,input wire [1:0] mode,input wire key2,key3,key4,clear,
 input wire image_ok,real_live,real_sample,input wire [3:0] real_reason,
 input wire [10:0] real_x,input wire [9:0] real_y,input wire [31:0] source_us,
 input wire [40:0] context_id,input wire frame_commit,sequence_fail,
 input wire [10:0] shown_x,input wire [9:0] shown_y,input wire [15:0] shown_ms,
 output reg [3:0] state,reason,output reg [10:0] count,
 output reg [15:0] elapsed_ms,duration_ms,output wire point_use,
 output reg point_valid,output reg [10:0] point_x,output reg [9:0] point_y,
 output reg [15:0] point_ms,output reg start_round,output wire running);
 localparam EMPTY=0,READY=1,WAIT_POINT=2,REC=3,PREP=4,PLAY=5,PAUSE=6,DONE=7,FAIL=8;
 (* ram_style="block" *)reg [39:0] memory[0:1023];
 reg [9:0] rdaddr;reg [39:0] rddata,p0,p1;
 reg [10:0] index;reg [16:0] subms;reg [15:0] record_ms,last_stamp;
 reg [31:0] first_us,last_us;reg [40:0] recording_context;
 reg [2:0] phase;reg [15:0] goal,computed_ms;
 reg [20:0] pending_point;reg pending_record,round_sent;
 reg div_start;reg [31:0] numerator;reg [15:0] denominator;wire div_done;wire [31:0] quotient;
 wire tick=subms==CYCLES_PER_MS-1;
 wire operating=state==WAIT_POINT || state==REC || point_use;
 wire context_bad=operating && recording_context!=context_id;
 wire record_fault=(state==WAIT_POINT || state==REC) && !real_live;
 wire fatal=operating && (!image_ok || context_bad || record_fault);
 wire first_write=state==WAIT_POINT && real_sample && real_live;
 wire more_write=state==REC && pending_record && div_done && quotient>last_stamp && quotient<=MAX_MS && count<MAX_POINTS;
 wire write_ok=rst_n && mode==3 && !clear && !fatal && !key2 &&
 !(state==REC && (record_ms>=MAX_MS || count>=MAX_POINTS));
 wire [15:0] stamp=quotient[15:0];
 wire [15:0] stopped_ms=record_ms>last_stamp?record_ms:last_stamp;
 assign point_use=state>=PREP && state<=FAIL;
 assign running=state==PLAY;
 stage1_teach_div divider(clk,rst_n,div_start,numerator,denominator,div_done,quotient);
 // Exactly one synchronous read and one synchronous write. Clearing a route
 // invalidates count and outstanding work; it does not reset the RAM array.
 always @(posedge clk)begin
 rddata<=memory[rdaddr];
 if(write_ok && (first_write || more_write))
 memory[first_write?10'd0:count[9:0]]<=first_write?{3'd0,16'd0,real_y,real_x}:{3'd0,stamp,pending_point};
 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
 state<=EMPTY;reason<=0;count<=0;elapsed_ms<=0;duration_ms<=0;point_valid<=0;point_x<=0;point_y<=0;point_ms<=0;start_round<=0;
 rdaddr<=0;p0<=0;p1<=0;index<=0;subms<=0;record_ms<=0;last_stamp<=0;first_us<=0;last_us<=0;recording_context<=0;
 phase<=0;goal<=0;computed_ms<=0;pending_point<=0;pending_record<=0;round_sent<=0;
 div_start<=0;numerator<=0;denominator<=1;
 end else begin
 div_start<=0;start_round<=0;
 if(tick)begin subms<=0;
 if(state==REC && record_ms<MAX_MS)begin record_ms<=record_ms+1'b1;elapsed_ms<=record_ms+1'b1;end
 if(state==PLAY && elapsed_ms<duration_ms)elapsed_ms<=elapsed_ms+1'b1;
 end else subms<=subms+1'b1;
 if(mode!=3 || clear || fatal || (key4 && state!=REC && state!=WAIT_POINT))begin
 if(state==REC)duration_ms<=stopped_ms;
 if(operating)state<=count!=0?READY:EMPTY;
 phase<=0;pending_record<=0;point_valid<=0;round_sent<=0;elapsed_ms<=0;
 if(clear)begin count<=0;duration_ms<=0;state<=EMPTY;reason<=14;end
 else if(fatal)reason<=(real_reason==1 || real_reason==2 || real_reason==6)?real_reason:context_bad?4'd8:real_reason==0?4'd3:real_reason;
 else if(key4 || operating)reason<=13;
 end else if(sequence_fail && state==PLAY)begin
 state<=FAIL;phase<=0;point_x<=shown_x;point_y<=shown_y;point_ms<=shown_ms;elapsed_ms<=shown_ms;reason<=0;
 end else if(key2)begin
 if(state==REC)begin state<=READY;duration_ms<=stopped_ms;pending_record<=0;phase<=0;reason<=13;end
 else if(point_use || state==WAIT_POINT)reason<=10;
 else if(!real_live || !image_ok)reason<=real_reason==0?4'd3:real_reason;
 else begin state<=WAIT_POINT;recording_context<=context_id;reason<=0;phase<=0;pending_record<=0;end
 end else if(key3 && state!=REC && state!=WAIT_POINT)begin
 if(state==PLAY)begin state<=PAUSE;phase<=0;end
 else if(state==PAUSE)state<=PLAY;
 else if(count<2 || duration_ms==0)reason<=15;
 else if(!image_ok)reason<=3;
 else begin state<=PREP;recording_context<=context_id;elapsed_ms<=0;point_ms<=0;point_valid<=0;
 phase<=1;rdaddr<=0;index<=1;reason<=0;round_sent<=0;computed_ms<=0;end
 end else begin
 if((key3 || key4) && (state==REC || state==WAIT_POINT))reason<=10;
 if(first_write)begin
 state<=REC;count<=1;record_ms<=0;last_stamp<=0;first_us<=source_us;last_us<=source_us;elapsed_ms<=0;duration_ms<=0;reason<=0;
 end
 if(state==REC)begin
 if(record_ms>=MAX_MS || count>=MAX_POINTS)begin state<=READY;duration_ms<=stopped_ms;pending_record<=0;reason<=12;end
 else if(more_write)begin count<=count+1'b1;last_stamp<=stamp;pending_record<=0;end
 else if(div_done && pending_record)pending_record<=0;
 else if(real_sample && source_us-last_us>=50000 && !pending_record)begin
 numerator<=source_us-first_us;denominator<=1000;div_start<=1;pending_point<={real_y,real_x};last_us<=source_us;pending_record<=1;
 end
 end
 if(state==PLAY && frame_commit && point_valid && !round_sent)begin start_round<=1;round_sent<=1;end
 if(state==PLAY && elapsed_ms==duration_ms && computed_ms==duration_ms && phase==0 && frame_commit && shown_ms==duration_ms)state<=DONE;
 case(phase)
 1:phase<=2;
 2:begin p0<=rddata;point_x<=rddata[10:0];point_y<=rddata[20:11];point_ms<=0;point_valid<=1;rdaddr<=1;phase<=3;end
 3:phase<=4;
 4:begin p1<=rddata;phase<=0;state<=PLAY;end
 5:phase<=6;
 6:begin p1<=rddata;phase<=7;end
 // Hold the latest sample at/before this 50ms replay deadline. Consume the
 // synchronous lookahead before publishing a point; coordinates and time
 // commit together. Tail silence is preserved through duration_ms.
 7:begin
 if(goal>=p1[36:21])begin
 p0<=p1;
 if(index+1'b1<count)begin index<=index+1'b1;rdaddr<=index+1'b1;phase<=5;end
 else begin point_x<=p1[10:0];point_y<=p1[20:11];point_ms<=goal;computed_ms<=goal;phase<=0;end
 end else begin point_x<=p0[10:0];point_y<=p0[20:11];point_ms<=goal;computed_ms<=goal;phase<=0;end
 end
 default:if(state==PLAY && elapsed_ms!=computed_ms &&
 (elapsed_ms>={1'b0,computed_ms}+17'd50 || elapsed_ms==duration_ms))begin
 goal<=elapsed_ms==duration_ms?duration_ms:computed_ms+16'd50;phase<=7;
 end
 endcase
 end
 end end
endmodule
`default_nettype wire

// Image health is independent of a detected tool. Intentional vertical blank
// cannot clear admission; synthetic points cannot refresh the image watchdog.
`default_nettype none
module stage1_teach_image_guard #(parameter CYCLES_PER_MS=75000)(input wire clk,rst_n,stream_n,
 input wire camera_ready,gain_busy,raw_video,reader_de,associated,input wire [31:0] image_id,
 output wire healthy,output wire [3:0] reason);
 reg admitted,seen;reg [31:0] last_id;reg [8:0] age;reg [16:0] subms;
 wire active_fault=reader_de && !raw_video;
 assign healthy=admitted && stream_n && camera_ready && !gain_busy && associated && !active_fault && age<250;
 assign reason=gain_busy?6:!camera_ready?2:!stream_n || active_fault?3:!associated?9:age>=250?5:!admitted?3:0;
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin admitted<=0;seen<=0;last_id<=0;age<=250;subms<=0;end
 else begin
 if(subms==CYCLES_PER_MS-1)begin subms<=0;if(age<250)age<=age+1'b1;end else subms<=subms+1'b1;
 if(!stream_n || !camera_ready || gain_busy || !associated || active_fault)admitted<=0;
 else if(raw_video)begin admitted<=1;
 if(!seen || image_id!=last_id)begin seen<=1;last_id<=image_id;age<=0;end end
 end end
endmodule

// One chosen point is consumed by the viewport, crosshair and area observer.
// The editor supplies real validity/geometry. One shared sequence below
// consumes either real or replay observations; unused editor sequence outputs
// are eliminated by synthesis, preserving standalone editor compatibility.
module stage1_scene #(parameter CYCLES_PER_MS=75000)(input wire clk,rst_n,
 input wire [1:0] mode,input wire down2,click2,click3,click4,cancel,
 input wire tracking,video_ok,camera_ready,gain_busy,input wire [7:0] session,
 input wire pair,frame_commit,detection_valid,input wire [31:0] image_id,input wire [767:0] meta,
 output wire [2:0] region_count,output wire [3:0] draft_count,
 output wire [15:0] revision,output wire [671:0] render_vertices,
 output wire [15:0] render_counts,output wire [3:0] closed_mask,
 output wire [3:0] run_state,completed,occupied,output wire [2:0] expected_area,actual_area,
 output wire muted,alarm,output wire [1:0] trend,output wire [10:0] distance,
 output wire [19:0] dwell_ms,output wire [3:0] edit_error,start_error,
 output wire busy,tip_live,metrics_valid,output wire [671:0] saved_vertices,output wire [167:0] draft_vertices,
 output wire [3:0] tip_reason,input wire image_healthy,input wire [3:0] image_reason,
 input wire [38:0] shown_point,output wire [38:0] desired_point,output wire [63:0] teaching);
 wire [3:0] real_state,real_completed,real_occupied,real_start,real_reason;
 wire [2:0] real_expected,real_actual;wire real_muted,real_alarm,real_tip;
 wire [19:0] real_dwell;
 stage1_regions #(.CYCLES_PER_MS(CYCLES_PER_MS)) real_controller(clk,rst_n,mode,down2,click2,click3,click4,cancel,
 tracking,video_ok,camera_ready,gain_busy,session,pair,frame_commit,detection_valid,image_id,meta,
 region_count,draft_count,revision,render_vertices,render_counts,closed_mask,real_state,real_completed,real_occupied,
 real_expected,real_actual,real_muted,real_alarm,,,real_dwell,edit_error,real_start,busy,real_tip,metrics_valid,saved_vertices,draft_vertices,real_reason);
 reg real_seen,tracking_last;reg [31:0] real_last;reg [40:0] last_context;
 reg [15:0] generation,revision_last,last_virtual_ms;reg sample_seen,replay_started,source_last;
 wire [40:0] context_id={session,pair,meta[719:704],meta[559:544]};
 wire real_sample=real_tip && (!real_seen || real_last!=image_id || context_id!=last_context);
 wire [3:0] route_state,route_reason;wire [10:0] route_count,px;wire [9:0] py;
 wire [15:0] elapsed,duration,point_ms;wire use_point,point_valid,start_round,running;
 wire [3:0] replay_state,replay_completed,replay_occupied,replay_error;
 wire [2:0] replay_expected,replay_actual;wire replay_muted,replay_alarm;wire [19:0] replay_dwell;
 wire [15:0] virtual_age=shown_point[38:23]-last_virtual_ms;
 wire virtual_sample=frame_commit && running && shown_point[22] && shown_point[21] && (!sample_seen || virtual_age>=50);
 wire seq_enabled=region_count!=0 && draft_count==0;
 wire [1:0] sequence_mode=mode==3?(use_point && seq_enabled && route_state!=4?2'd2:2'd0):mode;
 wire sequence_changed=context_id!=last_context || revision!=revision_last || use_point!=source_last;
 wire [10:0] chosen_x=use_point?shown_point[10:0]:meta[89:79];
 wire [9:0] chosen_y=use_point?shown_point[20:11]:meta[99:90];
 reg [3:0] inside_mask,near_mask;integer ri;reg [41:0] rect;
 always @*begin inside_mask=0;near_mask=0;rect=0;
 for(ri=0;ri<4;ri=ri+1)begin rect=saved_vertices[ri*168+:42];
 if(ri<region_count)begin
 inside_mask[ri]=chosen_x>=rect[10:0] && chosen_x<=rect[31:21] && chosen_y>=rect[20:11] && chosen_y<=rect[41:32];
 near_mask[ri]=$signed({2'd0,chosen_x})>=$signed({2'd0,rect[10:0]})-13'sd2 &&
 $signed({2'd0,chosen_x})<=$signed({2'd0,rect[31:21]})+13'sd2 &&
 $signed({3'd0,chosen_y})>=$signed({3'd0,rect[20:11]})-13'sd2 &&
 $signed({3'd0,chosen_y})<=$signed({3'd0,rect[41:32]})+13'sd2 &&
 !(chosen_x>rect[10:0]+11'd2 && chosen_x+11'd2<rect[31:21] &&
 chosen_y>rect[20:11]+10'd2 && chosen_y+10'd2<rect[41:32]);
 end end end
 wire [3:0] route_cause=gain_busy?4'd6:!camera_ready?4'd2:tracking_last && !tracking?4'd1:!image_healthy?image_reason:real_reason;
 stage1_route #(.CYCLES_PER_MS(CYCLES_PER_MS)) route(clk,rst_n,mode,click2,click3,click4 && !cancel,click4 && cancel,
 image_healthy,real_tip,real_sample,route_cause,meta[89:79],meta[99:90],meta[671:640],context_id,
 frame_commit,replay_started && replay_state==6,shown_point[10:0],shown_point[20:11],shown_point[38:23],
 route_state,route_reason,route_count,elapsed,duration,use_point,point_valid,px,py,point_ms,start_round,running);
 assign desired_point={point_ms,use_point,point_valid,py,px};
 stage1_sequence #(.CYCLES_PER_MS(CYCLES_PER_MS)) shared_controller(
 .clk(clk),.rst_n(rst_n),.mode(sequence_mode),.region_count(region_count),.draft_count(draft_count),
 .start_key(use_point?start_round:click2),.pause_key(!use_point && click3),.mute_key(!use_point && click4),
 .can_start(!busy),.live(use_point?image_healthy && point_valid:real_tip),.configuration_changed(sequence_changed),
 .sample((use_point?virtual_sample:real_sample) && !sequence_changed),.inside_mask(inside_mask),.near_mask(near_mask),.distances(44'd0),
 .state(run_state),.expected_area(expected_area),.actual_area(actual_area),.completed(completed),.occupied(occupied),
 .muted(muted),.alarm(alarm),.trend(),.distance(),.dwell_ms(dwell_ms),.start_error(start_error),.freeze(use_point && !running));
 assign replay_state=run_state;
 assign tip_live=use_point?image_healthy && point_valid:real_tip;
 assign tip_reason=mode==3?route_reason:real_reason;
 wire motion_valid;wire [10:0] motion_x=use_point?shown_point[10:0]:meta[89:79];
 wire [9:0] motion_y=use_point?shown_point[20:11]:meta[99:90];
 wire motion_active=(mode==2 || (mode==3 && running)) && seq_enabled && tip_live && expected_area<region_count &&
 (run_state==1 || run_state==2 || run_state==4);
 reg [41:0] target_rect;integer ti;
 always @*begin target_rect=0;
 for(ti=0;ti<4;ti=ti+1)if(expected_area==ti)target_rect=saved_vertices[ti*168+:42];end
 stage1_motion #(.CYCLES_PER_MS(CYCLES_PER_MS)) motion(clk,rst_n,motion_active,use_point?virtual_sample:real_sample,
 motion_x,motion_y,target_rect,{generation,expected_area},trend,distance,motion_valid);
 assign teaching={4'd0,draft_count,use_point,seq_enabled,trend,motion_valid,duration,elapsed,route_count,route_reason,route_state};
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin real_seen<=0;tracking_last<=0;real_last<=0;last_context<=0;generation<=0;revision_last<=0;last_virtual_ms<=0;sample_seen<=0;replay_started<=0;source_last<=0;end
 else begin
 if(real_sample)begin real_seen<=1;real_last<=image_id;end
 if(context_id!=last_context || revision!=revision_last || start_round)generation<=generation+1'b1;
 last_context<=context_id;revision_last<=revision;tracking_last<=tracking;source_last<=use_point;
 if(!use_point || route_state==4)begin replay_started<=0;sample_seen<=0;last_virtual_ms<=0;end
 else begin
 if(replay_state==1 || replay_state==2)replay_started<=1;
 if(virtual_sample)begin last_virtual_ms<=shown_point[38:23];sample_seen<=1;end
 end end end
endmodule
`default_nettype wire

// Image bank, v3 metadata, model and moving viewport commit together in blank.
`default_nettype none
module stage1_viewport #(parameter STALE_DISPLAY_FRAMES=15,V4=0,MW=V4?768:640,SW=V4?852:675)(
 input wire I_clk,I_rst_n,I_vs,I_de,I_snapshot,input wire [SW-1:0] I_data,
 input wire I_tracking,I_show,I_conflict,I_live,input wire [7:0] I_session,
 input wire [2:0] I_zoom,input wire [1:0] I_mode,input wire I_pair,
 output reg O_commit,output reg [1:0] O_bank,output reg [31:0] O_frame_id,
 output reg [10:0] O_cx,O_x0,output reg [9:0] O_cy,O_y0,
 output reg [2:0] O_zoom,output reg [1:0] O_mode,output reg [MW-1:0] O_meta,
 output reg O_show,O_pair,output wire O_detection_valid,output wire O_sample_valid,output wire [2:0] O_state,input wire I_rotate,output reg O_rotate,
 output reg [31:0] O_image_us,output reg [15:0] O_epoch,output reg O_time_valid,input wire [38:0] I_point,output reg [38:0] O_point);
 reg vs_last,in_blank,associated;reg [7:0] age,session;
 wire match=I_data[MW+34] && I_data[255] && I_data[415:413]==(V4?4:3) && I_data[31:0]==I_data[MW+:32] &&
 (!V4 || I_data[719:704]==I_data[SW-2-:16]) &&
 I_data[242:235]==I_session && I_data[243]==I_pair && I_data[244]==I_tracking;
 assign O_detection_valid=associated && I_tracking && I_live && session==I_session && O_pair==I_pair && age<STALE_DISPLAY_FRAMES && O_meta[247];
 assign O_sample_valid=associated && I_live && session==I_session && O_pair==I_pair && age<STALE_DISPLAY_FRAMES && O_meta[247] && O_meta[408];
 assign O_state=I_conflict?5:!I_live?6:age>=STALE_DISPLAY_FRAMES?7:!I_tracking?0:!O_detection_valid?1:O_meta[32]?2:O_meta[36:33]==8?4:1;
 reg signed [12:0] dx,dy;reg [10:0] cx,hx;reg [9:0] cy,hy;
 wire [10:0] view_width;wire [9:0] view_height;
 refined_zoom_geometry view_geometry(I_zoom,I_rotate,view_width,view_height,,,,);
 always @*begin
 dx=$signed({2'd0,(I_point[22]?I_point[10:0]:I_data[89:79])})-$signed({2'd0,O_cx});dy=$signed({3'd0,(I_point[22]?I_point[20:11]:I_data[99:90])})-$signed({3'd0,O_cy});
 cx=O_cx;cy=O_cy;
 if(dx>4)cx=O_cx+(dx>24?24:dx);if(dx< -4)cx=O_cx+(dx< -24?-24:dx);
 if(dy>4)cy=O_cy+(dy>24?24:dy);if(dy< -4)cy=O_cy+(dy< -24?-24:dy);
 if(!match || (I_point[22]?!I_point[21]:(!I_data[32] || I_data[MW+:32]==O_frame_id)))begin cx=O_cx;cy=O_cy;end
 hx=view_width>>1;hy=view_height>>1;
 if(cx<hx)cx=hx;if(cx>1280-view_width+hx)cx=1280-view_width+hx;
 if(cy<hy)cy=hy;if(cy>720-view_height+hy)cy=720-view_height+hy;
 end
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin vs_last<=0;in_blank<=0;associated<=0;age<=0;session<=0;O_commit<=0;O_bank<=0;O_frame_id<=0;
 O_cx<=640;O_cy<=360;O_x0<=0;O_y0<=48;O_zoom<=0;O_mode<=0;O_meta<=0;O_show<=1;O_pair<=0;O_rotate<=1;O_image_us<=0;O_epoch<=0;O_time_valid<=0;O_point<=0;end
 else begin
 vs_last<=I_vs;O_commit<=0;
 if(I_vs && !vs_last)begin
 in_blank<=1;O_show<=I_show;if(age<255)age<=age+1'b1;
 if(I_tracking && session!=I_session)begin O_cx<=640;O_cy<=360;end
 end
 if(I_de)in_blank<=0;
 if(session!=I_session || O_pair!=I_pair || O_meta[244]!=I_tracking)associated<=0;
 if(I_snapshot && in_blank && !I_de)begin
 in_blank<=0;O_commit<=1;O_point<=I_point[22]?I_point:{16'd0,1'b0,I_data[32],I_data[99:79]};O_bank<=I_data[MW+32+:2];O_frame_id<=I_data[MW+:32];
 if(V4)begin O_image_us<=I_data[803+:32];O_epoch<=I_data[835+:16];O_time_valid<=I_data[851] && I_data[802];end
 O_zoom<=I_zoom;O_mode<=I_mode;O_rotate<=I_rotate;O_pair<=I_pair;O_show<=I_show;session<=I_session;associated<=match;
 O_meta<=match?I_data[MW-1:0]:0;if(I_data[MW+:32]!=O_frame_id)age<=0;
 O_cx<=cx;O_cy<=cy;O_x0<=cx-hx;O_y0<=cy-hy;
 if(match && I_data[567:565]!=0)begin
 O_cx<=640;O_cy<=360;O_x0<=0;O_y0<=48;O_zoom<=0;O_mode<=0;
 end
 end end end
endmodule
`default_nettype wire
