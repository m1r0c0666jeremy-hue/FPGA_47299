// UI editor and image-bound region observations, entirely in the display domain.
`default_nettype none
module stage1_regions_frozen #(parameter CYCLES_PER_MS=75000)(input wire clk,rst_n,
 input wire [1:0] mode,input wire down2,click2,click3,click4,cancel,
 input wire tracking,video_ok,camera_ready,gain_busy,input wire [7:0] session,
 input wire pair,frame_commit,detection_valid,input wire [31:0] image_id,input wire [767:0] meta,
 output reg [2:0] region_count,output reg [3:0] draft_count,
 output reg [15:0] revision,output wire [671:0] render_vertices,
 output wire [15:0] render_counts,output wire [3:0] closed_mask,
 output wire [3:0] run_state,completed,occupied,output wire [2:0] expected_area,actual_area,
 output wire muted,alarm,output wire [1:0] trend,output wire [10:0] distance,
 output wire [19:0] dwell_ms,output reg [3:0] edit_error,output wire [3:0] start_error,
 output wire busy,tip_live,metrics_valid,output wire [671:0] saved_vertices,output wire [167:0] draft_vertices);
 reg [671:0] vertices;reg [15:0] counts;reg [167:0] draft;
 assign saved_vertices=vertices;assign draft_vertices=draft;
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
 // Editor validation and live point evaluation are mutually exclusive. Reuse
 // the exact point engine's cross product rather than a second multiplier.
 wire os,od;wire [20:0] oa,ob,oc;wire signed [23:0] cross_q;
 wire [4:0] point_address,validate_address;
 wire [4:0] vertex_address=validating || validate_start?validate_address:point_address;
 function [20:0] read_vertex;input [671:0] data;input [4:0] index;begin case(index)
5'd0:read_vertex=data[0+:21];
5'd1:read_vertex=data[21+:21];
5'd2:read_vertex=data[42+:21];
5'd3:read_vertex=data[63+:21];
5'd4:read_vertex=data[84+:21];
5'd5:read_vertex=data[105+:21];
5'd6:read_vertex=data[126+:21];
5'd7:read_vertex=data[147+:21];
5'd8:read_vertex=data[168+:21];
5'd9:read_vertex=data[189+:21];
5'd10:read_vertex=data[210+:21];
5'd11:read_vertex=data[231+:21];
5'd12:read_vertex=data[252+:21];
5'd13:read_vertex=data[273+:21];
5'd14:read_vertex=data[294+:21];
5'd15:read_vertex=data[315+:21];
5'd16:read_vertex=data[336+:21];
5'd17:read_vertex=data[357+:21];
5'd18:read_vertex=data[378+:21];
5'd19:read_vertex=data[399+:21];
5'd20:read_vertex=data[420+:21];
5'd21:read_vertex=data[441+:21];
5'd22:read_vertex=data[462+:21];
5'd23:read_vertex=data[483+:21];
5'd24:read_vertex=data[504+:21];
5'd25:read_vertex=data[525+:21];
5'd26:read_vertex=data[546+:21];
5'd27:read_vertex=data[567+:21];
5'd28:read_vertex=data[588+:21];
5'd29:read_vertex=data[609+:21];
5'd30:read_vertex=data[630+:21];
5'd31:read_vertex=data[651+:21];
endcase end endfunction
 wire [20:0] shared_vertex=read_vertex(vertices,vertex_address);
 stage1_validate #(.SHARED(1),.SHARED_VERTEX(1)) validator(clk,rst_n,validate_start,region_count,counts,vertices,draft_count,draft,validating,validated,passed,validation_error,os,oa,ob,oc,od,cross_q,validate_address,shared_vertex);
 stage1_point #(.SHARED_VERTEX(1)) geometry(clk,rst_n,evaluate_start,region_count,counts,vertices,job_x,job_y,evaluating,evaluated,in_mask,near_mask,point_distances,os,oa,ob,oc,od,cross_q,point_address,shared_vertex);
 stage1_sequence #(.CYCLES_PER_MS(CYCLES_PER_MS)) sequence_controller(clk,rst_n,mode,region_count,draft_count,
 click2,click3,click4,!busy,tip_live,configuration_changed,observation,observed_in,observed_near,observed_dist,
 run_state,expected_area,actual_area,completed,occupied,muted,alarm,trend,distance,dwell_ms,start_error);
// Private: data is valid only below reset region/point counts. Every live
 // vertex is written before its count is committed. Control reset is unchanged.
 integer data_index;
 always @(posedge clk)begin
 if(edit_request!=0 && !evaluating && !validating && !evaluate_start)begin
 case(edit_request)
 1:if(region_count<4 && draft_count<8)begin
 for(data_index=0;data_index<8;data_index=data_index+1)
 if(draft_count==data_index)draft[data_index*21+:21]<=edit_point;
 end
 // Deleted regions are excluded by count/closed flags and overwritten on reuse.
 default:begin end
 endcase end
 if(validated && passed)begin
 for(data_index=0;data_index<4;data_index=data_index+1)
 if(region_count==data_index)vertices[data_index*168+:168]<=draft;
 // Empty draft is invalid; each subsequently valid point is overwritten.
 end
 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin counts<=0;region_count<=0;draft_count<=0;revision<=0;
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
 else begin
 draft_count<=draft_count+1'b1;revision<=revision+1'b1;configuration_changed<=1;end
 2:if(draft_count<3)edit_error<=1;else begin validate_start<=1;end
 3:begin
 if(draft_count!=0)begin draft_count<=draft_count-1'b1;revision<=revision+1'b1;configuration_changed<=1;end
 else if(region_count!=0)begin
 region_count<=region_count-1'b1;
 for(j=0;j<4;j=j+1)if(region_count==j+1)counts[j*4+:4]<=0;
 revision<=revision+1'b1;configuration_changed<=1;end else edit_error<=7;end
 default:begin end
 endcase end
 if(validated)begin
 if(passed)begin
 for(j=0;j<4;j=j+1)if(region_count==j)counts[j*4+:4]<=draft_count;
 region_count<=region_count+1'b1;
 draft_count<=0;revision<=revision+1'b1;configuration_changed<=1;edit_error<=0;
 end else edit_error<=validation_error;end
 if(cancel || (!down2 && (!tip_live || session!=point_session || meta[559:544]!=point_model)))point_pending<=0;
 if(mode!=mode_last || session!=session_last)begin point_pending<=0;configuration_changed<=1;
 if(mode!=1)edit_request<=0;end
 end end
endmodule
`default_nettype wire
