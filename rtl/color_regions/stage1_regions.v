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
 run_state,expected_area,actual_area,completed,occupied,muted,alarm,,,dwell_ms,start_error);
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
