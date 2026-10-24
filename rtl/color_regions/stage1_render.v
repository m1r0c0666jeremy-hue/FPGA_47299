// Incremental supercover edges. Packed state RAM + four scanlines with serial stamps.
// No full-frame bitmap, per-pixel multiply, or extra video pipeline stage.
`default_nettype none
module stage1_render #(parameter SPLIT_DRAFT=0)(input wire clk,rst_n,commit,input wire [671:0] vertices,
 input wire [15:0] counts,input wire [3:0] closed_mask,input wire [1:0] ui_mode,
 input wire [10:0] x0,input wire [9:0] y0,input wire [2:0] zoom,input wire rotate,
 input wire [3:0] run_state,completed,input wire [2:0] expected_area,actual_area,
 input wire [10:0] x,input wire [9:0] y,input wire de,
 output wire [3:0] pixel_mask,output reg [23:0] pixel_color,
 output reg label_on,output reg [7:0] label_glyph,output reg [2:0] label_gx,
 output reg [3:0] label_gy,output reg [23:0] label_color,
 output reg ready,output reg underrun,input wire [167:0] draft_vertices,input wire [2:0] draft_region,input wire draft_visible);

 // Rectangles only: four comparison-based outlines, no bitmap RAM or ALU.
 reg [41:0] points[0:3];reg [1:0] sizes[0:3];
 reg [3:0] fclosed,fcompleted;reg [1:0] fmode;
 reg [3:0] fstate;reg [2:0] fexpected,factual,fzoom;reg frotate;
 reg [10:0] fx0;reg [9:0] fy0;
 reg [1:0] state,region_id,field,label_id;reg [5:0] label_attempt;reg label_up;
 reg signed [13:0] map_ax,map_ay,map_bx,map_by;
 reg signed [13:0] left_x[0:3],right_x[0:3],top_y[0:3],bottom_y[0:3];
 reg [10:0] labels_x[0:3];reg [9:0] labels_y[0:3];reg [3:0] labels_valid;
 reg [3:0] mask_comb,mask_q;
 assign pixel_mask=mask_q;
 function signed [13:0] mapped;input [10:0] source,origin;input [2:0] z;input flip,axis_y;
 reg signed [13:0] delta,l,r;reg signed [14:0] t,u;begin
 delta=$signed({3'd0,source})-$signed({3'd0,origin});
 case(z)
 1:begin t=($signed(delta)<<<1)+$signed(delta);u=t+3;l=(t+1)>>>1;r=((u+1)>>>1)-1;end
 2:begin l=delta<<<1;r=((delta+1)<<<1)-1;end
 3:begin l=(delta<<<1)+delta;r=((delta+1)<<<1)+delta;end
 4:begin l=delta<<<2;r=((delta+1)<<<2)-1;end
 default:begin l=delta;r=delta;end
 endcase
 t=($signed({l[13],l})+$signed({r[13],r}))>>>1;
 mapped=flip?(axis_y?14'sd623:14'sd1279)-t:t;
 end endfunction
 function [23:0] color_for;input [1:0] r;input [3:0] status,done_mask;input [2:0] target,actual;input closed;
 begin color_for=24'h9098a0;
 if(!closed)color_for=24'h40d8ff;
 else if(status==6 && actual=={1'b0,r}+1'b1)color_for=24'hff4050;
 else if(done_mask[r])color_for=24'h40ff90;
 else if(target=={1'b0,r} && status!=0 && status!=5 && status!=6 && status!=7)color_for=24'hffe040;
 end endfunction
 wire [20:0] point_q=field[1] && sizes[region_id]>1?points[region_id][41:21]:points[region_id][20:0];
 wire signed [13:0] mapped_q=mapped(field[0]?{1'b0,point_q[20:11]}:point_q[10:0],
 field[0]?{1'b0,fy0}:fx0,fzoom,frotate,field[0]);
 wire signed [13:0] sort_l=map_ax<map_bx?map_ax:map_bx,sort_r=map_ax>map_bx?map_ax:map_bx;
 wire signed [13:0] sort_t=map_ay<map_by?map_ay:map_by,sort_b=map_ay>map_by?map_ay:map_by;
 reg collision;integer j,ci,mi,pi;
 always @*begin collision=0;
 for(ci=0;ci<4;ci=ci+1)if(ci<label_id && labels_valid[ci] && labels_valid[label_id] &&
 labels_x[label_id]<labels_x[ci]+50 && labels_x[label_id]+50>labels_x[ci] &&
 labels_y[label_id]<labels_y[ci]+18 && labels_y[label_id]+18>labels_y[ci])collision=1;
 end
 wire signed [13:0] sx=$signed({3'd0,x}),sy=$signed({4'd0,y});
 always @*begin mask_comb=0;
 for(mi=0;mi<4;mi=mi+1)if(de && x<1280 && y<624 && ready && !underrun && sizes[mi]!=0)begin
 if(sizes[mi]==1)begin
 if(fmode==1 && sx>=left_x[mi]-14'sd2 && sx<=left_x[mi]+14'sd2 && sy>=top_y[mi]-14'sd2 && sy<=top_y[mi]+14'sd2)mask_comb[mi]=1;
 end else begin
 if(((sx==left_x[mi] || sx==right_x[mi]) && sy>=top_y[mi] && sy<=bottom_y[mi]) ||
 ((sy==top_y[mi] || sy==bottom_y[mi]) && sx>=left_x[mi] && sx<=right_x[mi]))mask_comb[mi]=1;
 if(fmode==1 && ((sx>=left_x[mi]-14'sd2 && sx<=left_x[mi]+14'sd2 && sy>=top_y[mi]-14'sd2 && sy<=top_y[mi]+14'sd2) ||
 (sx>=right_x[mi]-14'sd2 && sx<=right_x[mi]+14'sd2 && sy>=bottom_y[mi]-14'sd2 && sy<=bottom_y[mi]+14'sd2)))mask_comb[mi]=1;
 end end end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)mask_q<=0;else if(commit)mask_q<=0;else mask_q<=mask_comb;end
 reg [6:0] label_dx;reg [10:0] lx;reg [9:0] ly;
 always @*begin
 pixel_color=24'h9098a0;
 for(pi=0;pi<4;pi=pi+1)if(mask_q[pi])pixel_color=color_for(pi[1:0],fstate,fcompleted,fexpected,factual,fclosed[pi]);
 label_on=0;label_glyph=0;label_gx=x[2:0];label_gy=0;label_color=24'h9098a0;label_dx=0;lx=0;ly=0;
 for(pi=3;pi>=0;pi=pi-1)begin lx=labels_x[pi];ly=labels_y[pi];
 if(ready && !underrun && labels_valid[pi] && x>=lx && x<lx+48 && y>=ly && y<ly+16)begin
 label_on=1;label_dx=x-lx;label_gx=label_dx[2:0];label_gy=y-ly;
 label_color=color_for(pi[1:0],fstate,fcompleted,fexpected,factual,fclosed[pi]);
 case(label_dx[6:3])0:label_glyph=11;1:label_glyph=28;2:label_glyph=15;3:label_glyph=11;4:label_glyph=0;default:label_glyph=11+pi;endcase
 end end end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
 state<=0;region_id<=0;field<=0;label_id<=0;label_attempt<=0;label_up<=0;
 fclosed<=0;fcompleted<=0;fmode<=0;fstate<=0;fexpected<=0;factual<=0;fzoom<=0;frotate<=0;fx0<=0;fy0<=0;
 map_ax<=0;map_ay<=0;map_bx<=0;map_by<=0;labels_valid<=0;ready<=0;underrun<=0;
 for(j=0;j<4;j=j+1)begin sizes[j]<=0;left_x[j]<=0;right_x[j]<=0;top_y[j]<=0;bottom_y[j]<=0;labels_x[j]<=0;labels_y[j]<=0;end
 end else begin
 if(state!=0 && de && y<624)underrun<=1;
 case(state)
 1:begin
 case(field)0:map_ax<=mapped_q;1:map_ay<=mapped_q;2:map_bx<=mapped_q;3:map_by<=mapped_q;endcase
 if(field==3)begin field<=0;state<=2;end else field<=field+1'b1;
 end
 2:begin
 left_x[region_id]<=sort_l;right_x[region_id]<=sort_r;top_y[region_id]<=sort_t;bottom_y[region_id]<=sort_b;
 labels_x[region_id]<=sort_l<0?0:sort_l>1232?1232:sort_l;
 labels_y[region_id]<=sort_t>=18?(sort_t>626?608:sort_t-18):(sort_t< -3?0:sort_t+3);
 labels_valid[region_id]<=sizes[region_id]!=0 && sort_r>=0 && sort_l<1280 && sort_b>=0 && sort_t<624;
 if(region_id==3)begin state<=3;label_id<=0;label_attempt<=0;label_up<=labels_y[0]>304;end
 else begin region_id<=region_id+1'b1;state<=1;end
 end
 3:if(!collision || !labels_valid[label_id])begin
 if(label_id==3)begin ready<=1;state<=0;end
 else begin label_id<=label_id+1'b1;label_attempt<=0;label_up<=labels_y[label_id+1'b1]>304;end
 end else if(label_attempt==35)begin underrun<=1;ready<=1;state<=0;end
 else begin label_attempt<=label_attempt+1'b1;
 if(label_up && labels_y[label_id]>=18)labels_y[label_id]<=labels_y[label_id]-18;
 else if(!label_up && labels_y[label_id]<=590)labels_y[label_id]<=labels_y[label_id]+18;
 else begin label_up<=~label_up;labels_x[label_id]<=labels_x[label_id]>=64?labels_x[label_id]-64:labels_x[label_id]+64;end
 end
 default:begin end
 endcase
 if(commit)begin
 fclosed<=closed_mask;fcompleted<=completed;fmode<=ui_mode;fstate<=run_state;fexpected<=expected_area;factual<=actual_area;
 fzoom<=zoom;frotate<=rotate;fx0<=x0;fy0<=y0;labels_valid<=0;ready<=counts==0;underrun<=de && y<624;
 region_id<=0;field<=0;state<=counts==0?0:1;label_attempt<=0;
 for(j=0;j<4;j=j+1)begin
 points[j]<=SPLIT_DRAFT && draft_visible && draft_region==j?draft_vertices[41:0]:vertices[j*168+:42];
 sizes[j]<=counts[j*4+:4]<=2?counts[j*4+:2]:2'd0;
 if(counts[j*4+:4]>2)underrun<=1;
 end end
 end end
endmodule
`default_nettype wire
