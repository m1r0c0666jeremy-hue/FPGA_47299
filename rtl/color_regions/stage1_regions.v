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
 output wire busy,tip_live,metrics_valid);
 reg [671:0] vertices;reg [15:0] counts;reg [167:0] draft;
 reg commit_d,seen;reg [31:0] last_id,job_id;reg [7:0] session_last,job_session,point_session;
 reg [15:0] job_revision,point_model;reg [1:0] mode_last;reg [16:0] subms;reg [8:0] tip_age;
 reg [15:0] last_epoch,last_model,job_epoch,job_model;reg [7:0] last_session;
 reg [20:0] recent_tip,edit_point;reg point_pending;reg [1:0] edit_request;
 reg validate_start,evaluate_start;wire validating,validated,passed,evaluating,evaluated;
 wire [3:0] validation_error,in_mask,near_mask;wire [43:0] point_distances;
 reg observation;reg [3:0] observed_in,observed_near;reg [43:0] observed_dist;
 reg [10:0] job_x;reg [9:0] job_y;reg configuration_changed;
 reg metrics_good;
 wire source_ok=detection_valid && meta[255] && meta[247] && meta[32] && meta[415:413]==4 &&
 meta[31:0]==image_id && meta[242:235]==session && meta[243]==pair && meta[244] &&
 meta[89:79]<1280 && meta[99:90]<720;
 assign tip_live=tracking && camera_ready && video_ok && source_ok && tip_age<250 && !gain_busy;
 assign metrics_valid=metrics_good && tip_live && job_revision==revision && job_session==session && job_epoch==meta[719:704] && job_model==meta[559:544];
 assign busy=validating || edit_request!=0;
 reg [671:0] draw_data;reg [15:0] draw_counts;reg [3:0] draw_closed;
 integer j;
 always @*begin draw_data=vertices;draw_counts=counts;draw_closed=0;
 for(j=0;j<4;j=j+1)begin
 if(j<region_count)draw_closed[j]=1;
 if(region_count==j && draft_count!=0)begin draw_data[j*168+:168]=draft;draw_counts[j*4+:4]=draft_count;end
 end
 end
 assign render_vertices=draw_data;assign render_counts=draw_counts;assign closed_mask=draw_closed;
 stage1_validate validator(clk,rst_n,validate_start,region_count,counts,vertices,draft_count,draft,validating,validated,passed,validation_error);
 stage1_point geometry(clk,rst_n,evaluate_start,region_count,counts,vertices,job_x,job_y,evaluating,evaluated,in_mask,near_mask,point_distances);
 stage1_sequence #(.CYCLES_PER_MS(CYCLES_PER_MS)) sequence_controller(clk,rst_n,mode,region_count,draft_count,
 click2,click3,click4,!busy,tip_live,configuration_changed,observation,observed_in,observed_near,observed_dist,
 run_state,expected_area,actual_area,completed,occupied,muted,alarm,trend,distance,dwell_ms,start_error);
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin vertices<=0;counts<=0;draft<=0;region_count<=0;draft_count<=0;revision<=0;
 commit_d<=0;seen<=0;last_id<=0;job_id<=0;session_last<=0;job_session<=0;point_session<=0;
 job_revision<=0;point_model<=0;mode_last<=0;subms<=0;tip_age<=250;recent_tip<=0;edit_point<=0;
 last_epoch<=0;last_model<=0;job_epoch<=0;job_model<=0;last_session<=0;
 point_pending<=0;edit_request<=0;validate_start<=0;evaluate_start<=0;observation<=0;
 observed_in<=0;observed_near<=0;observed_dist<=0;job_x<=0;job_y<=0;configuration_changed<=0;edit_error<=0;metrics_good<=0;end
 else begin
 validate_start<=0;evaluate_start<=0;observation<=0;configuration_changed<=0;commit_d<=frame_commit;mode_last<=mode;session_last<=session;
 if(job_revision!=revision || job_session!=session || job_epoch!=meta[719:704] || job_model!=meta[559:544])metrics_good<=0;
 if(subms==CYCLES_PER_MS-1)begin subms<=0;if(tip_age<250)tip_age<=tip_age+1'b1;end else subms<=subms+1'b1;
 // A committed view may need several thousand clocks to prefetch image rows.
 // Admit its result when video becomes ready, even if the commit pulse has
 // already ended. Seen source identity still prevents counting a held frame.
 if(!seen || image_id!=last_id || session!=last_session || meta[719:704]!=last_epoch || meta[559:544]!=last_model)begin
 if(source_ok && tracking && camera_ready && video_ok && !gain_busy)begin
 seen<=1;last_id<=image_id;last_session<=session;last_epoch<=meta[719:704];last_model<=meta[559:544];
 recent_tip<={meta[99:90],meta[89:79]};tip_age<=0;
 if(!evaluating && !validating && edit_request==0 && !validate_start)begin
 job_x<=meta[89:79];job_y<=meta[99:90];job_id<=image_id;job_session<=session;job_revision<=revision;
 job_epoch<=meta[719:704];job_model<=meta[559:544];evaluate_start<=1;
 end end end
 if(evaluated && tip_live && job_id==image_id && job_session==session && job_revision==revision && job_epoch==meta[719:704] && job_model==meta[559:544])begin
 observed_in<=in_mask;observed_near<=near_mask;observed_dist<=point_distances;observation<=1;metrics_good<=1;end
 if(mode==1 && down2)begin
 point_pending<=tip_live && !busy;
 if(tip_live && !busy)begin edit_point<={meta[99:90],meta[89:79]};point_session<=session;point_model<=meta[559:544];end
 else edit_error<=busy?4'd8:4'd5;end
 if(mode==1 && !busy)begin
 if(click2)begin
 if(point_pending && tip_live && point_session==session && point_model==meta[559:544])edit_request<=1;
 else edit_error<=5;point_pending<=0;end
 else if(click3)edit_request<=2;else if(click4)edit_request<=3;
 end
 if(edit_request!=0 && !evaluating && !validating && !evaluate_start)begin
 edit_request<=0;edit_error<=0;
 case(edit_request)
 1:if(region_count==4)edit_error<=4;else if(draft_count==8)edit_error<=6;
 else begin for(j=0;j<8;j=j+1)if(draft_count==j)draft[j*21+:21]<=edit_point;
 draft_count<=draft_count+1'b1;revision<=revision+1'b1;configuration_changed<=1;end
 2:if(draft_count<3)edit_error<=1;else begin validate_start<=1;end
 3:begin
 if(draft_count!=0)begin draft_count<=draft_count-1'b1;revision<=revision+1'b1;configuration_changed<=1;end
 else if(region_count!=0)begin
 region_count<=region_count-1'b1;
 for(j=0;j<4;j=j+1)if(region_count==j+1)begin counts[j*4+:4]<=0;vertices[j*168+:168]<=0;end
 revision<=revision+1'b1;configuration_changed<=1;end else edit_error<=7;end
 default:begin end
 endcase end
 if(validated)begin
 if(passed)begin
 for(j=0;j<4;j=j+1)if(region_count==j)begin vertices[j*168+:168]<=draft;counts[j*4+:4]<=draft_count;end
 region_count<=region_count+1'b1;
 draft_count<=0;draft<=0;revision<=revision+1'b1;configuration_changed<=1;edit_error<=0;
 end else edit_error<=validation_error;end
 if(cancel || (!down2 && (!tip_live || session!=point_session || meta[559:544]!=point_model)))point_pending<=0;
 if(mode!=mode_last || session!=session_last)begin point_pending<=0;configuration_changed<=1;
 if(mode!=1)edit_request<=0;end
 end end
endmodule
`default_nettype wire
