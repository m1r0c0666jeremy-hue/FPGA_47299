// Three immutable RGB/mask line banks. Full source rows are classified at two
// pixels/DDR clock; support filtering precedes nearest-neighbour zoom.
`default_nettype none
module refined_line_reader #(parameter integer JOB_TIMEOUT_CYCLES=133334,DRAIN_TIMEOUT_CYCLES=133334)(input wire I_frame_commit,I_selected_good,I_rst_n,
 input wire I_ddr_clk,I_write_busy,I_write_en,input wire [1:0] I_read_buffer,
 input wire [31:0] I_frame_id,input wire [127:0] I_models,
 input wire I_ddr_ready,I_ddr_valid,input wire [127:0] I_ddr_data,
 output wire O_read_busy,O_read_en,output wire [24:0] O_read_addr,
 input wire I_pixel_clk,I_vs,I_hs,I_de,input wire [10:0] I_x0,input wire [9:0] I_y0,
 input wire [2:0] I_zoom,output reg O_vs,O_hs,O_de,output reg [23:0] O_rgb,
 output reg [1:0] O_mask,output reg O_video_ok,input wire I_rotate,
 input wire I_stream_n,output reg O_fault_toggle,output reg [127:0] O_ddr_diag,output reg [127:0] O_pixel_diag,
 input wire [31:0] I_accepted_reads,input wire I_unexpected_return);
 (* ram_style="block" *) reg [95:0] lines[0:1023];
 (* ram_style="block" *) reg [127:0] source[0:255];
 (* ram_style="block" *) reg [7:0] masks[0:1023];
 reg [95:0] pixel_q;reg [127:0] source_q;reg [383:0] linegroup,next_linegroup;reg [7:0] mask_q;
 (* async_reg="true" *) reg [1:0] dr,pr;wire d_global=dr[1],p_global=pr[1];wire d_rst,p_rst;
 refined_reset_bridge data_reset(I_ddr_clk,I_rst_n && I_stream_n,d_rst);
 refined_reset_bridge pixel_reset(I_pixel_clk,I_rst_n && I_stream_n,p_rst);
 always @(posedge I_ddr_clk or negedge I_rst_n)if(!I_rst_n)dr<=0;else dr<={dr[0],1'b1};
 always @(posedge I_pixel_clk or negedge I_rst_n)if(!I_rst_n)pr<=0;else pr<={pr[0],1'b1};
 reg req,req_first,req_rotate;reg [1:0] req_slot,req_image;reg [31:0] req_id;
 reg [9:0] req_y;reg [31:0] req_epoch;reg [127:0] req_models;
 (* async_reg="true" *) reg req1,req2;reg ack;
 localparam IDLE=0,WAIT_BUS=1,SEND=2,RECEIVE=3,CLASS=4,CLOSE=5,LOAD0=6,LOAD1=7,LOAD2=8,LOAD3=9,DRAIN=10,BROKEN=11;
 reg job_rotate,frame_rotate;reg [3:0] state;reg [1:0] slot,image;reg [31:0] image_id,job_epoch;
 reg [9:0] job_y;reg [127:0] models;reg [24:0] frame_base,line_base;
 reg [7:0] sent,received;reg [1:0] part;reg [6:0] group_index;reg [255:0] assembly;
 reg [9:0] pair_index;reg [2:0] pos;reg class_valid;reg [10:0] class_x;
 reg [9:0] class_y;reg [8:0] close_wait;
 reg [17:0] job_cycles,bus_wait,return_wait,drain_cycles;reg [8:0] issued;
 reg close_done,timeout_event;reg [3:0] timeout_cause;reg [1:0] failed_jobs;
 reg [31:0] accepted_base;wire [31:0] accepted_delta=I_accepted_reads-accepted_base;
 function [24:0] base_for;input [1:0] b;begin case(b)0:base_for=0;1:base_for=7000000;2:base_for=14000000;3:base_for=21000000;endcase end endfunction
 wire [9:0] rgb_write_addr=(slot<<8)+(slot<<6)+pair_index[9:1];
 wire [6:0] fetch_group=group_index+(state==CLASS && group_index<79?7'd1:7'd0);
 wire [6:0] fetch_block=job_rotate?7'd79-fetch_group:fetch_group;
 wire [1:0] fetch_word=state==CLASS?(pair_index[2:0]==1?1:pair_index[2:0]==2?2:0):(state==LOAD1?1:state==LOAD2?2:0);
 wire [7:0] source_addr=({1'b0,fetch_block}<<1)+fetch_block+fetch_word;
 wire source_we=(state==SEND || state==RECEIVE) && I_ddr_valid;
 wire [7:0] source_port=source_we?received:source_addr;
 wire [47:0] ordered_pair=linegroup >> ((job_rotate?pair_index[2:0]:7-pair_index[2:0])*48);
 wire [47:0] pair_rgb=job_rotate?{ordered_pair[23:0],ordered_pair[47:24]}:ordered_pair;
 wire [95:0] ordered_quad=linegroup >> ((job_rotate?pair_index[2:1]:3-pair_index[2:1])*96);
 wire [95:0] pixel_quad=job_rotate?{ordered_quad[23:0],ordered_quad[47:24],ordered_quad[71:48],ordered_quad[95:72]}:ordered_quad;
 wire [3:0] hit;stable_model_lane c0(I_ddr_clk,d_rst,pair_rgb[47:24],models,hit[1:0]);
 stable_model_lane c1(I_ddr_clk,d_rst,pair_rgb[23:0],models,hit[3:2]);
 reg [3:0] vp;reg [10:0] xp[0:3];reg [9:0] yp[0:3];reg [3:0] half_mask;
 reg filter_valid;reg [10:0] filter_x;reg [9:0] filter_y;reg [7:0] filter_mask;
 wire fv;wire [1:0] ft;wire [10:0] fx;wire [9:0] fy;wire [7:0] fa,fb;
 stable_filter4 filter(I_ddr_clk,d_rst,filter_valid,filter_x,filter_y,2'd0,filter_mask,fv,ft,fx,fy,fa,fb);
 wire [1:0] mask_slot=fy%3;wire [9:0] mask_addr=(mask_slot<<8)+(mask_slot<<6)+fx[10:2];
 wire mask_finish=fv && fx==1276;wire notify_ready,notify;wire [77:0] notice;
 reg [77:0] notice0,notice1;reg [1:0] notice_count;
 wire notice_send=notice_count!=0 && notify_ready;
 reg [7:0] mask_word;integer z;
 always @*for(z=0;z<4;z=z+1)begin mask_word[2*z]=fa[z];mask_word[2*z+1]=fb[z];end
 target_mailbox #(.WIDTH(78)) notify_mask(
 .S_clk(I_ddr_clk),.S_rst_n(d_rst),.S_send(notice_send),.S_data(notice0),.S_ready(notify_ready),
 .D_clk(I_pixel_clk),.D_rst_n(p_rst),.D_valid(notify),.D_data(notice));
 assign O_read_busy=state==SEND || state==DRAIN || state==BROKEN || (state==WAIT_BUS && !I_write_busy);
 assign O_read_en=state==SEND && I_ddr_ready;
 assign O_read_addr=line_base+{14'd0,sent,3'd0};
 always @(posedge I_ddr_clk)begin
 source_q<=source[source_port];if(source_we)source[source_port]<=I_ddr_data;
 if(state==CLASS && !pair_index[0])lines[rgb_write_addr]<=pixel_quad;
 if(fv)masks[mask_addr]<=mask_word;
 end
 integer j;
 always @(posedge I_ddr_clk or negedge d_rst)begin
 if(!d_rst)begin req1<=0;req2<=0;ack<=0;job_rotate<=1;frame_rotate<=1;state<=IDLE;slot<=0;image<=0;image_id<=0;job_epoch<=0;job_y<=0;models<=0;
 job_cycles<=0;bus_wait<=0;return_wait<=0;drain_cycles<=0;issued<=0;accepted_base<=0;close_done<=0;timeout_event<=0;timeout_cause<=0;failed_jobs<=0;notice0<=0;notice1<=0;notice_count<=0;
 frame_base<=0;line_base<=0;sent<=0;received<=0;part<=0;group_index<=0;assembly<=0;linegroup<=0;next_linegroup<=0;pair_index<=0;pos<=0;
 class_valid<=0;class_x<=0;class_y<=0;close_wait<=0;vp<=0;half_mask<=0;filter_valid<=0;filter_x<=0;filter_y<=0;filter_mask<=0;
 for(j=0;j<4;j=j+1)begin xp[j]<=0;yp[j]<=0;end end
 else begin
 timeout_event<=0;
 if(state!=IDLE && job_cycles!=262143)job_cycles<=job_cycles+1'b1;
 if(state==WAIT_BUS && bus_wait!=262143)bus_wait<=bus_wait+1'b1;
 if(state==RECEIVE && return_wait!=262143)return_wait<=return_wait+1'b1;
 if(O_read_en)issued<=issued+1'b1;
 case({mask_finish,notice_send})
  2'b01:begin notice0<=notice1;notice_count<=notice_count-1'b1;end
  2'b10:if(notice_count<2)begin
   if(notice_count==0)notice0<={job_epoch,image_id,image,fy,mask_slot};else notice1<={job_epoch,image_id,image,fy,mask_slot};notice_count<=notice_count+1'b1;end
  2'b11:if(notice_count==1)notice0<={job_epoch,image_id,image,fy,mask_slot};else begin notice0<=notice1;notice1<={job_epoch,image_id,image,fy,mask_slot};end
 endcase
 req1<=req;req2<=req1;class_valid<=state==CLASS;pos<=pair_index[2:0];class_x<={pair_index,1'b0};class_y<=job_y;
 vp<={vp[2:0],state==CLASS};xp[0]<={pair_index,1'b0};yp[0]<=job_y;
 for(j=1;j<4;j=j+1)begin xp[j]<=xp[j-1];yp[j]<=yp[j-1];end
 filter_valid<=0;
 if(vp[3])begin
 if(!xp[3][1])half_mask<=hit;
 else begin filter_valid<=1;filter_x<=xp[3]-2;filter_y<=yp[3];filter_mask<={hit,half_mask};end end
 case(state)
 IDLE:if(req2!=ack)begin
 slot<=req_slot;job_y<=req_y;job_epoch<=req_epoch;
 job_rotate<=req_first?req_rotate:frame_rotate;
 if(req_first)begin frame_rotate<=req_rotate;frame_base<=base_for(req_image);image<=req_image;image_id<=req_id;models<=req_models;end
 line_base<=(req_first?base_for(req_image):frame_base)+((req_first?req_rotate:frame_rotate)?10'd719-req_y:req_y)*25'd1920;
 sent<=0;received<=0;part<=0;group_index<=0;job_cycles<=0;bus_wait<=0;return_wait<=0;issued<=0;accepted_base<=I_accepted_reads;close_done<=0;state<=WAIT_BUS;end
 WAIT_BUS:if(!I_write_busy && !I_write_en)state<=SEND;
 SEND:if(O_read_en)begin if(sent==239)state<=RECEIVE;else sent<=sent+1'b1;end
 LOAD0:state<=LOAD1;
 LOAD1:begin linegroup[383:256]<=source_q;state<=LOAD2;end
 LOAD2:begin linegroup[255:128]<=source_q;state<=LOAD3;end
 LOAD3:begin linegroup[127:0]<=source_q;state<=CLASS;end
 CLASS:begin
 if(pair_index[2:0]==1)next_linegroup[383:256]<=source_q;
 if(pair_index[2:0]==2)next_linegroup[255:128]<=source_q;
 if(pair_index[2:0]==3)next_linegroup[127:0]<=source_q;
 if(pair_index==639)begin state<=CLOSE;close_wait<=0;end
 else begin pair_index<=pair_index+1'b1;if(pair_index[2:0]==7)begin group_index<=group_index+1'b1;linegroup<=next_linegroup;end end
 end
 CLOSE:begin if(close_wait!=511)close_wait<=close_wait+1'b1;
 if((job_y==0 && close_wait>=12) || (mask_finish && fy==(job_y==719?719:job_y-1)))close_done<=1;
 if(close_done && notice_count==0)begin ack<=req2;state<=IDLE;failed_jobs<=0;end end
 DRAIN:begin
  if(I_ddr_valid)received<=received+1'b1;
  if({1'b0,received}==issued || (I_ddr_valid && {1'b0,received}+9'd1==issued))begin
   if(failed_jobs==3)begin timeout_event<=1;state<=BROKEN;end
   else begin ack<=req2;state<=IDLE;end end
  else if(drain_cycles>=DRAIN_TIMEOUT_CYCLES-1)begin timeout_event<=1;timeout_cause<=4;state<=BROKEN;end
  else drain_cycles<=drain_cycles+1'b1;
 end
 BROKEN:begin end
 endcase
 if((state==SEND || state==RECEIVE) && I_ddr_valid)begin
 received<=received+1'b1;
 if(received==239)begin pair_index<=0;group_index<=0;state<=LOAD0;end end
 if(state!=IDLE && state!=DRAIN && state!=BROKEN &&
 (job_cycles>=JOB_TIMEOUT_CYCLES-1 || (mask_finish && notice_count==2 && !notice_send)))begin
  timeout_event<=1;drain_cycles<=0;timeout_cause<=mask_finish?7:state==WAIT_BUS?6:4;
  if(failed_jobs<3)failed_jobs<=failed_jobs+1'b1;state<=DRAIN;
 end
 if(I_unexpected_return && state!=BROKEN)begin timeout_event<=1;timeout_cause<=8;state<=BROKEN;end
 end end
 // Survive a local stream reset so the fault remains photographable afterwards.
 always @(posedge I_ddr_clk or negedge d_global)begin
 if(!d_global)begin O_fault_toggle<=0;O_ddr_diag<=0;end
 else begin
 if(d_rst && state==CLOSE && close_done && notice_count==0)begin
  O_ddr_diag[17:0]<=job_cycles;
  if(bus_wait>O_ddr_diag[35:18])O_ddr_diag[35:18]<=bus_wait;
  if(return_wait>O_ddr_diag[53:36])O_ddr_diag[53:36]<=return_wait;
  // Once a fault is recorded, its beat counts stay paired with that cause
  // until another fault or KEY1. Good rows must not replace the fault snapshot.
  if(O_ddr_diag[75:72]==0)begin
   O_ddr_diag[62:54]<=accepted_delta[8:0];O_ddr_diag[71:63]<={1'b0,received};end
 end
 if(d_rst && mask_finish && !notify_ready && O_ddr_diag[103:88]!=65535)O_ddr_diag[103:88]<=O_ddr_diag[103:88]+1'b1;
 if(timeout_event && d_rst)begin
  // Preserve failed-job peaks before the coordinated stream reset clears
  // the working counters. Successful rows alone underreport black-flash waits.
  if(bus_wait>O_ddr_diag[35:18])O_ddr_diag[35:18]<=bus_wait;
  if(return_wait>O_ddr_diag[53:36])O_ddr_diag[53:36]<=return_wait;
  O_ddr_diag[75:72]<=timeout_cause;
  if(O_ddr_diag[87:76]!=4095)O_ddr_diag[87:76]<=O_ddr_diag[87:76]+1'b1;
  O_ddr_diag[62:54]<=accepted_delta[8:0];O_ddr_diag[71:63]<={1'b0,received};
  if(state==BROKEN)O_fault_toggle<=~O_fault_toggle;
 end
 if(I_unexpected_return && O_ddr_diag[119:104]!=65535)O_ddr_diag[119:104]<=O_ddr_diag[119:104]+1'b1;
 end end
 (* async_reg="true" *) reg ack1,ack2;(* async_reg="true" *) reg live1,live2;
 reg pending,frame_live,abort_frame,first;reg [2:0] ready;
 reg [9:0] tags[0:2];reg [10:0] x,x0;reg [9:0] y,y0,last_y,prefetch;
 reg pixel_rotate;reg [2:0] zoom;reg [1:0] image_bank;reg [31:0] frame_id;reg [127:0] pixel_models;
 wire [10:0] view_width;wire [9:0] view_height;wire [2:0] view_p,view_q,view_phase_x,view_phase_y;
 refined_zoom_geometry viewport(I_zoom,I_rotate,view_width,view_height,view_p,view_q,view_phase_x,view_phase_y);
 reg [2:0] scale_p,scale_q,x_phase,x_remainder,y_remainder;
 reg [10:0] source_x;reg [9:0] source_y;
 wire [3:0] x_step={1'b0,x_remainder}+scale_q,y_step={1'b0,y_remainder}+scale_q;
 reg [31:0] epoch;reg vs_old;reg [3:0] offset_d;reg [1:0] moffset_d;reg good_d,vs_d,hs_d,de_d;
 wire [10:0] view_x0=I_rotate?1280-view_width-I_x0:I_x0;
 wire [9:0] view_y0=I_rotate?720-view_height-I_y0:I_y0;
 wire [10:0] sx=x0+source_x;wire [9:0] sy=y0+source_y;wire [1:0] pb=sy%3;
 wire [1:0] next_slot=prefetch%3;wire good=frame_live && !abort_frame && live2 && ready[pb] && tags[pb]==sy;
 reg diagnostic_vs_old,diagnostic_de_seen;reg fault_recorded;reg [17:0] pixel_clock,ready_time[0:2];reg [2:0] used_line;
 always @(posedge I_pixel_clk or negedge p_global)begin
 if(!p_global)begin diagnostic_vs_old<=0;diagnostic_de_seen<=0;O_pixel_diag<=0;O_pixel_diag[126:109]<=18'h3ffff;fault_recorded<=0;pixel_clock<=0;used_line<=0;ready_time[0]<=0;ready_time[1]<=0;ready_time[2]<=0;end
 else begin
 diagnostic_vs_old<=I_vs;if(I_de)diagnostic_de_seen<=1;
 if(I_vs && !diagnostic_vs_old)begin fault_recorded<=0;diagnostic_de_seen<=0;end
 pixel_clock<=pixel_clock+1'b1;
 if(I_frame_commit)begin fault_recorded<=0;used_line<=0;end
 if(p_rst && notify && notice[77:46]==epoch && notice[45:14]==frame_id && notice[13:12]==image_bank)begin ready_time[notice[1:0]]<=pixel_clock;used_line[notice[1:0]]<=0;end
 if(p_rst && I_de && x==0 && y<624 && good && !used_line[pb])begin
  used_line[pb]<=1;
  if((pixel_clock-ready_time[pb])<O_pixel_diag[126:109])O_pixel_diag[126:109]<=pixel_clock-ready_time[pb];
 end
 if(p_rst && frame_live && !abort_frame && !fault_recorded && (!live2 || (I_de && y<624 && !good)))begin
  fault_recorded<=1;O_pixel_diag[3:0]<=!live2?3:!ready[pb]?1:2;
  if(O_pixel_diag[19:4]!=65535)O_pixel_diag[19:4]<=O_pixel_diag[19:4]+1'b1;
  O_pixel_diag[30:20]<=x;O_pixel_diag[40:31]<=y;O_pixel_diag[50:41]<=sy;O_pixel_diag[60:51]<=tags[pb];O_pixel_diag[92:61]<=frame_id;
 end
 if(I_de && !diagnostic_de_seen && !frame_live && !fault_recorded)begin O_pixel_diag[3:0]<=5;fault_recorded<=1;
 O_pixel_diag[30:20]<=0;O_pixel_diag[40:31]<=0;O_pixel_diag[50:41]<=0;O_pixel_diag[60:51]<=0;O_pixel_diag[92:61]<=frame_id;
 if(O_pixel_diag[108:93]!=65535)O_pixel_diag[108:93]<=O_pixel_diag[108:93]+1'b1;end
 end end
 wire [9:0] rgb_read_addr=(pb<<8)+(pb<<6)+sx[10:2];wire [9:0] mask_read_addr=rgb_read_addr;
 always @(posedge I_pixel_clk)begin pixel_q<=lines[rgb_read_addr];mask_q<=masks[mask_read_addr];end
 // Stream recovery blanks RGB, but cannot interrupt the free-running HDMI sync.
 always @(posedge I_pixel_clk or negedge p_global)begin
 if(!p_global)begin offset_d<=0;moffset_d<=0;good_d<=0;vs_d<=0;hs_d<=0;de_d<=0;O_vs<=0;O_hs<=0;O_de<=0;O_rgb<=0;O_mask<=0;O_video_ok<=0;end
 else begin
 vs_d<=I_vs;hs_d<=I_hs;de_d<=I_de;offset_d<=sx[3:0];moffset_d<=sx[1:0];good_d<=p_rst && good && y<624;
 O_vs<=vs_d;O_hs<=hs_d;O_de<=de_d;O_rgb<=de_d && good_d && p_rst?(pixel_q>>((3-offset_d[1:0])*24)):0;
 O_mask<=de_d && good_d && p_rst?(mask_q>>(moffset_d*2)):0;O_video_ok<=p_rst && frame_live && !abort_frame && live2;
 end end
 always @(posedge I_pixel_clk or negedge p_rst)begin
 if(!p_rst)begin ack1<=0;ack2<=0;live1<=0;live2<=0;pending<=0;frame_live<=0;abort_frame<=1;first<=1;ready<=0;
 req<=0;req_first<=0;req_rotate<=1;req_slot<=0;req_image<=0;req_id<=0;req_y<=0;req_epoch<=0;req_models<=0;
 pixel_rotate<=1;x<=0;x0<=0;y<=0;y0<=48;last_y<=671;prefetch<=47;zoom<=0;image_bank<=0;frame_id<=0;pixel_models<=0;epoch<=0;vs_old<=0;
 scale_p<=1;scale_q<=1;x_phase<=0;x_remainder<=0;y_remainder<=0;source_x<=0;source_y<=0;
 for(j=0;j<3;j=j+1)tags[j]<=0;end
 else begin
 ack1<=ack;ack2<=ack1;live1<=I_selected_good;live2<=live1;vs_old<=I_vs;
 if(I_vs && !vs_old)begin frame_live<=0;abort_frame<=1;end
 if(frame_live && !live2)abort_frame<=1;
 if(I_de)begin
 if(x==1279)begin x<=0;y<=y+1'b1;source_x<=0;x_remainder<=x_phase;
  if(y_step>=scale_p)begin y_remainder<=y_step-scale_p;source_y<=source_y+1'b1;end else y_remainder<=y_step;
 end else begin x<=x+1'b1;
  if(x_step>=scale_p)begin x_remainder<=x_step-scale_p;source_x<=source_x+1'b1;end else x_remainder<=x_step;
 end
 if(y<624 && !good)abort_frame<=1;
 if(x==1279 && y<624 && y_step>=scale_p && good)ready[pb]<=0;
 end
 if(pending && ack2==req)pending<=0;
 if(notify && notice[77:46]==epoch && notice[45:14]==frame_id && notice[13:12]==image_bank &&
 notice[11:2]>=y0 && notice[11:2]<=last_y && !abort_frame)begin ready[notice[1:0]]<=1;tags[notice[1:0]]<=notice[11:2];end
 if(frame_live && !abort_frame && !pending && prefetch<720 && prefetch<=last_y+1 && !ready[next_slot])begin
 req_rotate<=pixel_rotate;req_y<=prefetch;req_slot<=next_slot;req_first<=first;req_epoch<=epoch;req_image<=image_bank;req_id<=frame_id;req_models<=pixel_models;
 req<=~req;pending<=1;first<=0;prefetch<=prefetch+1'b1;
 end
 if(I_frame_commit)begin
 x<=0;y<=0;pixel_rotate<=I_rotate;x0<=view_x0;y0<=view_y0;zoom<=I_zoom;image_bank<=I_read_buffer;frame_id<=I_frame_id;pixel_models<=I_models;
 scale_p<=view_p;scale_q<=view_q;x_phase<=view_phase_x;x_remainder<=view_phase_x;y_remainder<=view_phase_y;source_x<=0;source_y<=0;
 epoch<=epoch+1'b1;ready<=0;frame_live<=1;abort_frame<=0;first<=1;
 prefetch<=view_y0==0?0:view_y0-1;last_y<=view_y0+view_height-1;
 end end end
endmodule
`default_nettype wire
