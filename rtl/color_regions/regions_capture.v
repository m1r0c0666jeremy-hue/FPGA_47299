// Functional capture branch. The video stream is never stalled by this module.
// Raw SOF owns the public frame ID; classification has four clocks of sideband.
`default_nettype none
module regions_capture #(parameter TILE_MIN=4,SUPPORT_MIN=16,AREA_MIN=16,PADDING=64,CONFIRM=3,MAX_STEP=96)(
 input wire I_clk,I_rst_n,I_sof,I_valid,I_fault,input wire [95:0] I_rgb,
 input wire I_pair,I_enable,input wire [7:0] I_session,input wire I_result_ready,
 output reg [31:0] O_frame_id,output reg O_valid,output reg [415:0] O_meta,
 output reg [31:0] O_dropped
);
 wire clk=I_clk,rst_n=I_rst_n;wire [9:0] command={I_pair,I_session,I_enable};
 reg sof_old,have_frame,cap_bank,accepted;wire sof=I_sof && !sof_old;
 wire next_bank=have_frame?!cap_bank:1'b0;
 reg [1:0] owned,pending,complete;reg [3:0] closed;
 reg [31:0] ids[0:1];reg [9:0] commands[0:1];reg [23:0] means[0:1];reg [1:0] samples;
 reg [19:0] pixels;reg fault;reg [10:0] x;reg [9:0] y;reg [1:0] row_bank;
 reg [13:0] sr,sg,sb;reg [6:0] sn;integer k,rp;
 reg [10:0] group_r,group_g,group_b;reg [2:0] group_n;
 wire [10:0] raw_x=sof?0:x;wire [9:0] raw_y=sof?0:y;
 always @*begin
   group_r=0;group_g=0;group_b=0;group_n=0;
   for(rp=0;rp<4;rp=rp+1)if(raw_x+rp>=636 && raw_x+rp<644 && raw_y>=356 && raw_y<364)begin
     group_r=group_r+I_rgb[95-24*rp-:8];group_g=group_g+I_rgb[87-24*rp-:8];
     group_b=group_b+I_rgb[79-24*rp-:8];group_n=group_n+1'b1;
   end
 end
 wire [1:0] grid_ready,grid_bad;wire take=grid_ready[next_bank] && !owned[next_bank];
 reg [3:0] sp,ap,bp;reg [10:0] xp[0:3];reg [9:0] yp[0:3],cp[0:3];reg [1:0] lp[0:3];
 wire cv;wire [15:0] hits;wire [7:0] quality;
 regions_color4 u_color(clk,rst_n,I_valid,I_rgb,cv,hits,quality);
 wire dv=cv && ap[3];wire ds=sp[3] && ap[3];
 reg [167:0] next_rois,frame_rois,active_rois;reg [3:0] next_rv,frame_rv,active_rv;
 reg [9:0] roi_command;
 wire [167:0] rois=sp[3]?frame_rois:active_rois;
 wire [3:0] roi_valid=sp[3]?frame_rv:active_rv;
 reg [3:0] ha,hb,ma,mb,ca,cb;reg [7:0] member_a,member_b;
 reg [41:0] box;integer p,j,px;reg in_roi;
 reg [3:0] cover_a,cover_b;
 always @*begin
   ha=0;hb=0;ma=0;mb=0;ca=0;cb=0;member_a=0;member_b=0;box=0;px=0;in_roi=0;cover_a=0;cover_b=0;
   for(p=0;p<4;p=p+1)begin
     ha[p]=cp[3][0] && (cp[3][9]?hits[p*4+2]:hits[p*4]);
     hb[p]=cp[3][0] && (cp[3][9]?hits[p*4+3]:hits[p*4+1]);px=xp[3]+p;
     cover_a={yp[3]==719,yp[3]==0,px==1279,px==0};cover_b=cover_a;
     for(j=0;j<4;j=j+1)begin
       box=rois[j*42+:42];in_roi=roi_valid[j] && px>=box[10:0] && px<=box[21:11] && yp[3]>=box[31:22] && yp[3]<=box[41:32];
       if(in_roi)begin
         if(j<2)begin
           member_a[p*2+j]=1;ma[p]=ha[p];
         end else begin
           member_b[p*2+j-2]=1;mb[p]=hb[p];
         end
       end
       if(roi_valid[j])begin
         if(j<2)begin
           cover_a[0]=cover_a[0] || (px>box[10:0] && px<=box[21:11]+1 && yp[3]>=box[31:22] && yp[3]<=box[41:32]);
           cover_a[1]=cover_a[1] || (px+1>=box[10:0] && px<box[21:11] && yp[3]>=box[31:22] && yp[3]<=box[41:32]);
           cover_a[2]=cover_a[2] || (px>=box[10:0] && px<=box[21:11] && yp[3]>box[31:22] && yp[3]<=box[41:32]+1);
           cover_a[3]=cover_a[3] || (px>=box[10:0] && px<=box[21:11] && yp[3]+1>=box[31:22] && yp[3]<box[41:32]);
         end else begin
           cover_b[0]=cover_b[0] || (px>box[10:0] && px<=box[21:11]+1 && yp[3]>=box[31:22] && yp[3]<=box[41:32]);
           cover_b[1]=cover_b[1] || (px+1>=box[10:0] && px<box[21:11] && yp[3]>=box[31:22] && yp[3]<=box[41:32]);
           cover_b[2]=cover_b[2] || (px>=box[10:0] && px<=box[21:11] && yp[3]>box[31:22] && yp[3]<=box[41:32]+1);
           cover_b[3]=cover_b[3] || (px>=box[10:0] && px<=box[21:11] && yp[3]+1>=box[31:22] && yp[3]<box[41:32]);
         end
       end
     end
     // Test the union's exterior, including identical or merely adjacent ROIs.
     ca[p]=ma[p] && !(&cover_a);cb[p]=mb[p] && !(&cover_b);
   end
 end
 wire [1:0] label_bad[0:1];wire [1:0] close_pulse,close_bank;
 wire [7:0] labels[0:3];wire [9:0] edges[0:3];
 wire [148:0] stat_q[0:1];wire [13:0] edge_q[0:1];
 wire [7:0] stat_addr;wire stat_write;wire [148:0] stat_data;wire [9:0] edge_addr;
 reg worker_bank,worker_color;reg fs,gs,cs;
 genvar c;
 generate for(c=0;c<2;c=c+1)begin:colour
   wire [1:0] ec,lb;wire [230:0] rec;wire eol,overflow,fb;wire [5:0] total;wire [9:0] ry;wire [8:0] maxcycles;
   regions_runs4 runs(clk,rst_n,ds,dv,xp[3],yp[3],c==0?ma:mb,c==0?ca:cb,quality,
      c==0?member_a:member_b,lp[3],bp[3],ec,rec,eol,total,overflow,lb,fb,ry);
   regions_run_labeler labels_unit(clk,rst_n,ds,bp[3],ec,rec,eol,overflow,total,lb,fb,ry,
      label_bad[c],close_pulse[c],close_bank[c],labels[c*2],labels[c*2+1],edges[c*2],edges[c*2+1],
      stat_addr,stat_write && worker_color==c,stat_data,stat_q[c],edge_addr,edge_q[c],maxcycles);
 end endgenerate
 wire grid_busy,grid_done,grid_failed;wire [167:0] grid_boxes;wire [3:0] grid_valid;wire [1:0] grid_more;
 regions_grid #(.TILE_MIN(TILE_MIN),.SUPPORT_MIN(SUPPORT_MIN),.PADDING(PADDING)) grid(clk,rst_n,ds,bp[3],dv,xp[3],yp[3],ha,hb,gs,worker_bank,
   grid_busy,grid_done,grid_failed,grid_ready,grid_bad,grid_boxes,grid_valid,grid_more);
 wire final_busy,final_done,final_failed,final_more;wire [1:0] final_clip;wire [127:0] f0,f1;
 wire [1:0] worker_bad={label_bad[1][worker_bank],label_bad[0][worker_bank]};
 wire final_invalid=!complete[worker_bank] || worker_bad[worker_color] || !closed[worker_bank*2+worker_color];
 regions_finalize #(.AREA_MIN(AREA_MIN)) finalizer(clk,rst_n,fs,worker_bank,labels[{worker_color,worker_bank}],edges[{worker_color,worker_bank}],
   final_invalid,final_busy,final_done,final_failed,f0,f1,final_more,final_clip,
   stat_addr,stat_write,stat_data,stat_q[worker_color],edge_addr,edge_q[worker_color]);
 reg [511:0] candidates;reg [1:0] failed,more;reg [3:0] clipped;
 wire confirm_busy,confirm_done;wire [511:0] confirmed;wire [43:0] dx;wire [39:0] dy;
 regions_confirm #(.CONFIRM(CONFIRM),.MAX_STEP(MAX_STEP)) confirm(clk,rst_n,cs,ids[worker_bank],commands[worker_bank],complete[worker_bank],failed,
   candidates,confirm_busy,confirm_done,confirmed,dx,dy);
 reg [3:0] state;reg [8:0] drain;reg [415:0] packet;reg [127:0] a,b,a2,b2;
 always @*begin
   a=confirmed[127:0];a2=confirmed[255:128];b=confirmed[383:256];b2=confirmed[511:384];packet=0;
   packet[31:0]=ids[worker_bank];packet[47:37]=a[72:62];packet[57:48]=a[82:73];
   packet[68:58]=b[72:62];packet[78:69]=b[82:73];packet[141:100]=a[41:0];packet[183:142]=b[41:0];
   packet[203:184]=a[61:42];packet[223:204]=b[61:42];packet[230:224]=a[89:83];packet[254:248]=b[89:83];
   packet[232:231]=failed[0]?2'd2:|clipped[1:0]?2'd1:0;packet[234:233]=failed[1]?2'd2:|clipped[3:2]?2'd1:0;
   packet[242:235]=commands[worker_bank][8:1];packet[243]=commands[worker_bank][9];packet[244]=commands[worker_bank][0];
   packet[245]=a[120];packet[246]=b[120];packet[247]=complete[worker_bank];packet[255]=1;
   packet[319:256]={more[0],a2[120],a2[61:42],a2[41:0]};packet[383:320]={more[1],b2[120],b2[61:42],b2[41:0]};
   packet[407:384]=means[worker_bank];packet[408]=samples[worker_bank] && complete[worker_bank];
   packet[412:411]=grid_more;packet[415:413]=1;
 end
 // Bounding-box union and clipped expansion are only evaluated after a frame.
 function [41:0] union_box;input [41:0] a0,b0;reg [41:0] v;begin
   v[10:0]=a0[10:0]<b0[10:0]?a0[10:0]:b0[10:0];v[21:11]=a0[21:11]>b0[21:11]?a0[21:11]:b0[21:11];
   v[31:22]=a0[31:22]<b0[31:22]?a0[31:22]:b0[31:22];v[41:32]=a0[41:32]>b0[41:32]?a0[41:32]:b0[41:32];union_box=v;
 end endfunction
 function [41:0] expand;input [41:0] a0;input [11:0] ex,ey;reg [12:0] xx,yy;reg [41:0] v;begin
   v[10:0]=a0[10:0]>ex?a0[10:0]-ex:0;v[31:22]=a0[31:22]>ey?a0[31:22]-ey:0;
   xx={2'b0,a0[21:11]}+ex;yy={3'b0,a0[41:32]}+ey;
   v[21:11]=xx>1279?1279:xx[10:0];v[41:32]=yy>719?719:yy[9:0];expand=v;
 end endfunction
 reg [167:0] frozen_rois[0:1];reg [3:0] frozen_rv[0:1];
 reg [41:0] chosen,expanded;reg found;reg [127:0] cv0;integer t,ci;
 reg [1:0] roi_index;
 reg [167:0] roi_work;reg [3:0] roi_work_valid;
 // Reuse one ROI expansion/union datapath for four frame-background slots.
 // Five extra clocks fit within the frame budget; pixel processing is unchanged.
 always @*begin
     chosen=0;expanded=0;found=0;cv0=0;ci=0;
     for(t=0;t<2;t=t+1)begin
       ci=(roi_index[1]?2:0)+t;cv0=candidates[ci*128+:128];
       if(cv0[120] && cv0[90+roi_index[0]])begin
         expanded=expand(cv0[41:0],PADDING+{dx[ci*11+:11],1'b0},PADDING+{1'b0,dy[ci*10+:10],1'b0});
         chosen=found?union_box(chosen,expanded):expanded;found=1;
       end
     end
     if(clipped[roi_index] && frozen_rv[worker_bank][roi_index])begin chosen=expand(frozen_rois[worker_bank][42*roi_index+:42],2*PADDING,2*PADDING);found=1;end
 end
 always @(posedge clk or negedge rst_n)begin
   if(!rst_n)begin
     sof_old<=0;have_frame<=0;cap_bank<=0;accepted<=0;owned<=0;pending<=0;complete<=0;closed<=0;
     pixels<=0;fault<=0;x<=0;y<=0;row_bank<=0;sr<=0;sg<=0;sb<=0;sn<=0;samples<=0;
     sp<=0;ap<=0;bp<=0;next_rois<=0;next_rv<=0;frame_rois<=0;frame_rv<=0;active_rois<=0;active_rv<=0;roi_command<=0;
     worker_bank<=0;worker_color<=0;fs<=0;gs<=0;cs<=0;candidates<=0;failed<=0;more<=0;clipped<=0;state<=0;drain<=0;
     O_frame_id<=0;O_valid<=0;O_meta<=0;O_dropped<=0;roi_index<=0;
     for(k=0;k<2;k=k+1)begin ids[k]<=0;commands[k]<=0;means[k]<=0;frozen_rois[k]<=0;frozen_rv[k]<=0;end
     for(k=0;k<4;k=k+1)begin xp[k]<=0;yp[k]<=0;cp[k]<=0;lp[k]<=0;end
   end else begin
     sof_old<=I_sof;O_valid<=0;fs<=0;gs<=0;cs<=0;
     sp<={sp[2:0],sof};ap<={ap[2:0],sof?take:(accepted && pixels<921600)};bp<={bp[2:0],sof?next_bank:cap_bank};
     xp[0]<=raw_x;yp[0]<=raw_y;cp[0]<=sof?command:commands[cap_bank];lp[0]<=sof?0:row_bank;
     for(k=1;k<4;k=k+1)begin xp[k]<=xp[k-1];yp[k]<=yp[k-1];cp[k]<=cp[k-1];lp[k]<=lp[k-1];end
     if(sp[3])begin active_rois<=frame_rois;active_rv<=frame_rv;end
     for(k=0;k<2;k=k+1)if(close_pulse[k])closed[close_bank[k]*2+k]<=1;
     if(sof)begin
       if(have_frame && accepted)begin
         pending[cap_bank]<=1;complete[cap_bank]<=pixels==921600 && !fault && !I_fault;
         means[cap_bank]<={sr[13:6],sg[13:6],sb[13:6]};samples[cap_bank]<=sn==64;
       end
       if(have_frame && !accepted)O_dropped<=O_dropped+1'b1;
       have_frame<=1;O_frame_id<=O_frame_id+1'b1;cap_bank<=next_bank;accepted<=take;
       pixels<=I_valid?4:0;fault<=I_fault;x<=I_valid?4:0;y<=0;row_bank<=0;
       sr<=0;sg<=0;sb<=0;sn<=0;
       frame_rois<=command==roi_command?next_rois:0;frame_rv<=command==roi_command && I_enable?next_rv:0;
       if(take)begin
         owned[next_bank]<=1;closed[next_bank*2+:2]<=0;ids[next_bank]<=O_frame_id+1'b1;commands[next_bank]<=command;
         frozen_rois[next_bank]<=command==roi_command?next_rois:0;frozen_rv[next_bank]<=command==roi_command && I_enable?next_rv:0;
       end
     end else begin
       if(I_fault)fault<=1;
       if(I_valid && have_frame)begin
         if(pixels<921600)begin
           pixels<=pixels+4;
           if(x==1276)begin x<=0;y<=y+1'b1;row_bank<=row_bank==2?0:row_bank+1'b1;end else x<=x+4;
           sr<=sr+group_r;sg<=sg+group_g;sb<=sb+group_b;sn<=sn+group_n;
         end else fault<=1;
       end
     end
     case(state)
       0:if(pending!=0)begin
         worker_bank<=pending[0]?0:1;pending[pending[0]?0:1]<=0;drain<=0;state<=1;
       end
       1:begin
         drain<=drain+1'b1;
         if(closed[worker_bank*2+:2]==3 || drain==400)begin worker_color<=0;fs<=1;state<=2;candidates<=0;failed<=0;more<=0;clipped<=0;end
       end
       2:if(final_done)begin
         candidates[worker_color*256+:256]<={f1,f0};failed[worker_color]<=final_failed;
         more[worker_color]<=final_more;clipped[worker_color*2+:2]<=final_clip;
         if(!worker_color)begin worker_color<=1;state<=3;end else begin gs<=1;state<=4;end
       end
       3:begin fs<=1;state<=2;end
       4:if(grid_done)begin cs<=1;state<=5;end
       5:if(confirm_done)begin
         roi_work<=complete[worker_bank] && commands[worker_bank][0] && !grid_failed?grid_boxes:0;
         roi_work_valid<=complete[worker_bank] && commands[worker_bank][0] && !grid_failed?grid_valid:0;
         roi_index<=0;state<=7;
       end
       7:begin
         if(found && !failed[roi_index[1]] && complete[worker_bank] && commands[worker_bank][0] && !grid_failed)begin
           roi_work[roi_index*42+:42]<=chosen;roi_work_valid[roi_index]<=1;
         end
         if(roi_index==3)state<=8;
         else roi_index<=roi_index+1'b1;
       end
       8:begin // Atomically publish all four slots, including SOF collisions.
         next_rois<=roi_work;next_rv<=roi_work_valid;roi_command<=commands[worker_bank];state<=6;
       end
       6:if(I_result_ready)begin O_meta<=packet;O_valid<=1;owned[worker_bank]<=0;state<=0;end
     endcase
   end
 end
endmodule
`default_nettype wire
