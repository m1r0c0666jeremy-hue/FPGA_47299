// Three immutable RGB/mask line banks. Full source rows are classified at two
// pixels/DDR clock; support filtering precedes nearest-neighbour zoom.
`default_nettype none
module stable_line_reader(input wire I_frame_commit,I_selected_good,I_rst_n,
 input wire I_ddr_clk,I_write_busy,I_write_en,input wire [1:0] I_read_buffer,
 input wire [31:0] I_frame_id,input wire [127:0] I_models,
 input wire I_ddr_ready,I_ddr_valid,input wire [127:0] I_ddr_data,
 output wire O_read_busy,O_read_en,output wire [24:0] O_read_addr,
 input wire I_pixel_clk,I_vs,I_hs,I_de,input wire [10:0] I_x0,input wire [9:0] I_y0,
 input wire [1:0] I_zoom,output reg O_vs,O_hs,O_de,output reg [23:0] O_rgb,
 output reg [1:0] O_mask,output reg O_video_ok);
 (* ram_style="block" *) reg [95:0] lines[0:1023];
 (* ram_style="block" *) reg [127:0] source[0:255];
 (* ram_style="block" *) reg [7:0] masks[0:1023];
 reg [95:0] pixel_q;reg [127:0] source_q;reg [383:0] linegroup;reg [7:0] mask_q;
 (* async_reg="true" *) reg [1:0] dr,pr;wire d_rst=dr[1],p_rst=pr[1];
 always @(posedge I_ddr_clk or negedge I_rst_n)if(!I_rst_n)dr<=0;else dr<={dr[0],1'b1};
 always @(posedge I_pixel_clk or negedge I_rst_n)if(!I_rst_n)pr<=0;else pr<={pr[0],1'b1};
 reg req,req_first;reg [1:0] req_slot,req_image;reg [31:0] req_id;
 reg [9:0] req_y;reg [31:0] req_epoch;reg [127:0] req_models;
 (* async_reg="true" *) reg req1,req2;reg ack;
 localparam IDLE=0,WAIT_BUS=1,SEND=2,RECEIVE=3,CLASS=4,CLOSE=5,LOAD0=6,LOAD1=7,LOAD2=8,LOAD3=9;
 reg [3:0] state;reg [1:0] slot,image;reg [31:0] image_id,job_epoch;
 reg [9:0] job_y;reg [127:0] models;reg [24:0] frame_base,line_base;
 reg [7:0] sent,received;reg [1:0] part;reg [6:0] group_index;reg [255:0] assembly;
 reg [9:0] pair_index;reg [2:0] pos;reg class_valid;reg [10:0] class_x;
 reg [9:0] class_y;reg [8:0] close_wait;
 function [24:0] base_for;input [1:0] b;begin case(b)0:base_for=0;1:base_for=7000000;2:base_for=14000000;3:base_for=21000000;endcase end endfunction
 wire [9:0] rgb_write_addr=(slot<<8)+(slot<<6)+pair_index[9:1];
 wire [7:0] source_addr=(group_index<<1)+group_index+(state==LOAD1?1:state==LOAD2?2:0);
 wire source_we=(state==SEND || state==RECEIVE) && I_ddr_valid;
 wire [7:0] source_port=source_we?received:source_addr;
 wire [47:0] pair_rgb=linegroup >> ((7-pair_index[2:0])*48);
 wire [3:0] hit;stable_model_lane c0(I_ddr_clk,d_rst,pair_rgb[47:24],models,hit[1:0]);
 stable_model_lane c1(I_ddr_clk,d_rst,pair_rgb[23:0],models,hit[3:2]);
 reg [3:0] vp;reg [10:0] xp[0:3];reg [9:0] yp[0:3];reg [3:0] half_mask;
 reg filter_valid;reg [10:0] filter_x;reg [9:0] filter_y;reg [7:0] filter_mask;
 wire fv;wire [1:0] ft;wire [10:0] fx;wire [9:0] fy;wire [3:0] fa,fb;
 stable_filter4 filter(I_ddr_clk,d_rst,filter_valid,filter_x,filter_y,2'd0,filter_mask,fv,ft,fx,fy,fa,fb);
 wire [1:0] mask_slot=fy%3;wire [9:0] mask_addr=(mask_slot<<8)+(mask_slot<<6)+fx[10:2];
 wire mask_finish=fv && fx==1276;wire notify_ready,notify;wire [77:0] notice;
 reg [7:0] mask_word;integer z;
 always @*for(z=0;z<4;z=z+1)begin mask_word[2*z]=fa[z];mask_word[2*z+1]=fb[z];end
 target_mailbox #(.WIDTH(78)) notify_mask(
 .S_clk(I_ddr_clk),.S_rst_n(d_rst),.S_send(mask_finish && notify_ready),.S_data({job_epoch,image_id,image,fy,mask_slot}),.S_ready(notify_ready),
 .D_clk(I_pixel_clk),.D_rst_n(p_rst),.D_valid(notify),.D_data(notice));
 assign O_read_busy=state==SEND || (state==WAIT_BUS && !I_write_busy);
 assign O_read_en=state==SEND && I_ddr_ready;
 assign O_read_addr=line_base+{14'd0,sent,3'd0};
 always @(posedge I_ddr_clk)begin
 source_q<=source[source_port];if(source_we)source[source_port]<=I_ddr_data;
 if(state==CLASS && !pair_index[0])lines[rgb_write_addr]<=linegroup>>((3-pair_index[2:1])*96);
 if(fv)masks[mask_addr]<=mask_word;
 end
 integer j;
 always @(posedge I_ddr_clk or negedge d_rst)begin
 if(!d_rst)begin req1<=0;req2<=0;ack<=0;state<=IDLE;slot<=0;image<=0;image_id<=0;job_epoch<=0;job_y<=0;models<=0;
 frame_base<=0;line_base<=0;sent<=0;received<=0;part<=0;group_index<=0;assembly<=0;linegroup<=0;pair_index<=0;pos<=0;
 class_valid<=0;class_x<=0;class_y<=0;close_wait<=0;vp<=0;half_mask<=0;filter_valid<=0;filter_x<=0;filter_y<=0;filter_mask<=0;
 for(j=0;j<4;j=j+1)begin xp[j]<=0;yp[j]<=0;end end
 else begin
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
 if(req_first)begin frame_base<=base_for(req_image);image<=req_image;image_id<=req_id;models<=req_models;end
 line_base<=(req_first?base_for(req_image):frame_base)+req_y*25'd1920;
 sent<=0;received<=0;part<=0;group_index<=0;state<=WAIT_BUS;end
 WAIT_BUS:if(!I_write_busy && !I_write_en)state<=SEND;
 SEND:if(O_read_en)begin if(sent==239)state<=RECEIVE;else sent<=sent+1'b1;end
 LOAD0:state<=LOAD1;
 LOAD1:begin linegroup[383:256]<=source_q;state<=LOAD2;end
 LOAD2:begin linegroup[255:128]<=source_q;state<=LOAD3;end
 LOAD3:begin linegroup[127:0]<=source_q;state<=CLASS;end
 CLASS:if(pair_index==639)begin state<=CLOSE;close_wait<=0;end
 else begin pair_index<=pair_index+1'b1;if(pair_index[2:0]==7)begin group_index<=group_index+1'b1;state<=LOAD0;end end
 CLOSE:begin close_wait<=close_wait+1'b1;
 if((job_y==0 && close_wait>=12) || (mask_finish && fy==(job_y==719?719:job_y-1)))begin ack<=req2;state<=IDLE;end end
 endcase
 if((state==SEND || state==RECEIVE) && I_ddr_valid)begin
 received<=received+1'b1;
 if(received==239)begin pair_index<=0;group_index<=0;state<=LOAD0;end end
 end end
 (* async_reg="true" *) reg ack1,ack2;(* async_reg="true" *) reg live1,live2;
 reg pending,frame_live,abort_frame,first;reg [2:0] ready;
 reg [9:0] tags[0:2];reg [10:0] x,x0;reg [9:0] y,y0,last_y,prefetch;
 reg [1:0] zoom,image_bank;reg [31:0] frame_id;reg [127:0] pixel_models;
 reg [31:0] epoch;reg vs_old;reg [3:0] offset_d;reg [1:0] moffset_d;reg good_d,vs_d,hs_d,de_d;
 wire [10:0] sx=x0+(x>>zoom);wire [9:0] sy=y0+(y>>zoom);wire [1:0] pb=sy%3;
 wire [1:0] next_slot=prefetch%3;wire good=frame_live && !abort_frame && live2 && ready[pb] && tags[pb]==sy;
 wire [9:0] rgb_read_addr=(pb<<8)+(pb<<6)+sx[10:2];wire [9:0] mask_read_addr=rgb_read_addr;
 always @(posedge I_pixel_clk)begin pixel_q<=lines[rgb_read_addr];mask_q<=masks[mask_read_addr];end
 always @(posedge I_pixel_clk or negedge p_rst)begin
 if(!p_rst)begin ack1<=0;ack2<=0;live1<=0;live2<=0;pending<=0;frame_live<=0;abort_frame<=1;first<=1;ready<=0;
 req<=0;req_first<=0;req_slot<=0;req_image<=0;req_id<=0;req_y<=0;req_epoch<=0;req_models<=0;
 x<=0;x0<=0;y<=0;y0<=48;last_y<=671;prefetch<=47;zoom<=0;image_bank<=0;frame_id<=0;pixel_models<=0;epoch<=0;vs_old<=0;
 offset_d<=0;moffset_d<=0;good_d<=0;vs_d<=0;hs_d<=0;de_d<=0;O_vs<=0;O_hs<=0;O_de<=0;O_rgb<=0;O_mask<=0;O_video_ok<=0;
 for(j=0;j<3;j=j+1)tags[j]<=0;end
 else begin
 ack1<=ack;ack2<=ack1;live1<=I_selected_good;live2<=live1;vs_old<=I_vs;
 vs_d<=I_vs;hs_d<=I_hs;de_d<=I_de;offset_d<=sx[3:0];moffset_d<=sx[1:0];good_d<=good && y<624;
 O_vs<=vs_d;O_hs<=hs_d;O_de<=de_d;O_rgb<=de_d && good_d?(pixel_q>>((3-offset_d[1:0])*24)):0;
 O_mask<=de_d && good_d?(mask_q>>(moffset_d*2)):0;O_video_ok<=frame_live && !abort_frame && live2;
 if(I_vs && !vs_old)begin frame_live<=0;abort_frame<=1;end
 if(frame_live && !live2)abort_frame<=1;
 if(I_de)begin
 if(x==1279)begin x<=0;y<=y+1'b1;end else x<=x+1'b1;
 if(y<624 && !good)abort_frame<=1;
 if(x==1279 && y<624 && ((y & ((1<<zoom)-1))==((1<<zoom)-1)) && good)ready[pb]<=0;
 end
 if(pending && ack2==req)pending<=0;
 if(notify && notice[77:46]==epoch && notice[45:14]==frame_id && notice[13:12]==image_bank &&
 notice[11:2]>=y0 && notice[11:2]<=last_y && !abort_frame)begin ready[notice[1:0]]<=1;tags[notice[1:0]]<=notice[11:2];end
 if(frame_live && !abort_frame && !pending && prefetch<720 && prefetch<=last_y+1 && !ready[next_slot])begin
 req_y<=prefetch;req_slot<=next_slot;req_first<=first;req_epoch<=epoch;req_image<=image_bank;req_id<=frame_id;req_models<=pixel_models;
 req<=~req;pending<=1;first<=0;prefetch<=prefetch+1'b1;
 end
 if(I_frame_commit)begin
 x<=0;y<=0;x0<=I_x0;y0<=I_y0;zoom<=I_zoom;image_bank<=I_read_buffer;frame_id<=I_frame_id;pixel_models<=I_models;
 epoch<=epoch+1'b1;ready<=0;frame_live<=1;abort_frame<=0;first<=1;
 prefetch<=I_y0==0?0:I_y0-1;last_y<=I_y0+(624>>I_zoom)-1;
 end end end
endmodule
`default_nettype wire
