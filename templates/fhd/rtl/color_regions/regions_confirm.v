// Two independent candidates per colour. Names indicate colour regions, not tools.
`default_nettype none
module regions_confirm #(parameter CONFIRM=3,MAX_STEP=96)(
 input wire clk,rst_n,start,input wire [31:0] frame_id,input wire [9:0] command,
 input wire frame_good,input wire [1:0] color_bad,input wire [511:0] candidates,
 output reg busy,done,output wire [511:0] confirmed,
 output reg [43:0] motion_x,output reg [39:0] motion_y
);
 reg [10:0] hx[0:3];reg [9:0] hy[0:3];reg [1:0] streak[0:3];reg [3:0] used,confirmed_valid;
 // Caller holds candidate fields from start until the completed packet is consumed.
 // Only validity changes here; copying four complete statistics records cost FFs
 // and routing without adding another lifetime boundary (capture owns that bank).
 genvar slot;
 generate for(slot=0;slot<4;slot=slot+1)begin:output_slot
   assign confirmed[slot*128+:128]={candidates[slot*128+121+:7],confirmed_valid[slot],candidates[slot*128+:120]};
 end endgenerate
 reg [31:0] last_frame;reg [9:0] last_command;reg have_frame,color,continuous,duplicate;
 reg [127:0] a,b;reg [13:0] c00,c01,c10,c11;reg swap;
 integer base,p0,p1,j;reg m0,m1;reg [1:0] n0,n1;
 function [10:0] distance_x;input [10:0] a0,b0;begin distance_x=a0>b0?a0-b0:b0-a0;end endfunction
 function [9:0] distance_y;input [9:0] a0,b0;begin distance_y=a0>b0?a0-b0:b0-a0;end endfunction
 function [13:0] cost;input [127:0] v;input old_used;input [10:0] x;input [9:0] y;
  reg [10:0] dx;reg [9:0] dy;
  begin dx=distance_x(v[72:62],x);dy=distance_y(v[82:73],y);
    cost=!v[120]?0:(!old_used || dx>MAX_STEP || dy>MAX_STEP)?14'd8191:dx+dy;
  end
 endfunction
 always @*begin
  base=color?2:0;a=candidates[base*128+:128];b=candidates[(base+1)*128+:128];
  c00=cost(a,used[base]&&continuous,hx[base],hy[base]);c01=cost(a,used[base+1]&&continuous,hx[base+1],hy[base+1]);
  c10=cost(b,used[base]&&continuous,hx[base],hy[base]);c11=cost(b,used[base+1]&&continuous,hx[base+1],hy[base+1]);
  swap=({1'b0,c01}+{1'b0,c10})<({1'b0,c00}+{1'b0,c11});p0=swap?base+1:base;p1=swap?base:base+1;
  m0=a[120] && (swap?c01:c00)<8191;m1=b[120] && (swap?c10:c11)<8191;
  n0=!a[120]?0:m0?(duplicate?streak[p0]:streak[p0]>=CONFIRM?CONFIRM:streak[p0]+1'b1):duplicate?0:1;
  n1=!b[120]?0:m1?(duplicate?streak[p1]:streak[p1]>=CONFIRM?CONFIRM:streak[p1]+1'b1):duplicate?0:1;
 end
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
    busy<=0;done<=0;confirmed_valid<=0;motion_x<=0;motion_y<=0;used<=0;
    last_frame<=0;last_command<=0;have_frame<=0;color<=0;continuous<=0;duplicate<=0;
    for(j=0;j<4;j=j+1)begin hx[j]<=0;hy[j]<=0;streak[j]<=0;end
  end else begin
   done<=0;
   if(start && !busy)begin
    busy<=1;color<=0;confirmed_valid<=0;motion_x<=0;motion_y<=0;
    continuous<=have_frame && (last_frame+32'd1==frame_id || last_frame==frame_id) && last_command==command;
    duplicate<=have_frame && last_frame==frame_id && last_command==command;
   end else if(busy)begin
    if(!frame_good || !command[0] || color_bad[color])begin
      used[base]<=0;used[base+1]<=0;streak[base]<=0;streak[base+1]<=0;
      confirmed_valid[base]<=0;confirmed_valid[base+1]<=0;
    end else begin
      used[base]<=a[120];used[base+1]<=b[120];streak[base]<=n0;streak[base+1]<=n1;
      hx[base]<=a[72:62];hy[base]<=a[82:73];hx[base+1]<=b[72:62];hy[base+1]<=b[82:73];
      confirmed_valid[base]<=a[120] && n0>=CONFIRM;
      confirmed_valid[base+1]<=b[120] && n1>=CONFIRM;
      motion_x[base*11+:11]<=m0?distance_x(a[72:62],hx[p0]):0;
      motion_y[base*10+:10]<=m0?distance_y(a[82:73],hy[p0]):0;
      motion_x[(base+1)*11+:11]<=m1?distance_x(b[72:62],hx[p1]):0;
      motion_y[(base+1)*10+:10]<=m1?distance_y(b[82:73],hy[p1]):0;
    end
    if(color)begin
      busy<=0;done<=1;last_frame<=frame_id;last_command<=command;have_frame<=frame_good;
    end else color<=1;
   end
  end
 end
endmodule
`default_nettype wire
