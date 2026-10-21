// Incremental supercover edges. Packed state RAM + two 8-pixel scanline buffers.
// No full-frame bitmap, per-pixel multiply, or extra video pipeline stage.
`default_nettype none
module stage1_render(input wire clk,rst_n,commit,input wire [671:0] vertices,
 input wire [15:0] counts,input wire [3:0] closed_mask,input wire [1:0] ui_mode,
 input wire [10:0] x0,input wire [9:0] y0,input wire [2:0] zoom,input wire rotate,
 input wire [3:0] run_state,completed,input wire [2:0] expected_area,actual_area,
 input wire [10:0] x,input wire [9:0] y,input wire de,
 output wire [3:0] pixel_mask,output reg [23:0] pixel_color,
 output reg label_on,output reg [7:0] label_glyph,output reg [2:0] label_gx,
 output reg [3:0] label_gy,output reg [23:0] label_color,
 output reg ready,output reg underrun);
 localparam IDLE=0,MAP=1,ORDER=2,DIV_HALF=3,WAIT_HALF=4,MUL_START=5,WAIT_MUL=6,
 DIV_INITIAL=7,WAIT_INITIAL=8,WRITE_EDGE=9,ROW_BEGIN=10,READ_EDGE=11,ROW_EDGE=12,
 GEN=13,WAIT_ROW=14,LABEL_PLACE=15,MAP_FINISH=16;
 reg [4:0] state;reg [4:0] edge_id;reg [3:0] field;
 reg [671:0] fv;reg [15:0] fc;reg [3:0] fclosed,fcompleted;reg [1:0] fmode;
 reg [10:0] fx0;reg [9:0] fy0;reg [2:0] fzoom,fexpected,factual;reg frotate;
 reg [3:0] fstate;
 reg signed [13:0] xa,ya,xb,yb;reg signed [15:0] dx,dy,half_q;
 reg [13:0] half_r;reg signed [47:0] product;reg product_negative;
 reg [127:0] work;reg write_is_row;
 (* ram_style="bram" *)reg [15:0] edge_mem[0:255];
 (* ram_style="bram" *)reg [31:0] line_mem[0:319];
 reg [15:0] edge_q;reg [31:0] line_q;
 reg [1:0] bank_valid;reg [9:0] bank_row[0:1];reg mask_valid_q;reg [2:0] offset_q;
 reg [9:0] row;reg [7:0] word_index;reg [1:0] region_phase;reg [31:0] pending;
 reg [10:0] span_lo[0:31],span_hi[0:31];reg [31:0] span_valid;
 reg [10:0] labels_x[0:3];reg [9:0] labels_y[0:3];reg [3:0] labels_valid;
 reg [1:0] label_id;reg label_up;reg [5:0] label_attempt;reg label_collision;
 reg [3:0] all_left,all_right,all_above,all_below;
 reg mstart;reg [1:0] mop;reg [47:0] ma,mb;wire mbusy,mdone;wire [47:0] mr,mrem;
 stage1_arith #(.DW(14)) line_alu(clk,rst_n,mstart,mop,ma,mb,mbusy,mdone,mr,mrem);
 wire signed [47:0] initial_quotient=product_negative?-$signed(mr)-(mrem!=0?48'sd1:48'sd0):$signed(mr);
 wire signed [47:0] initial_x=($signed({{34{xa[13]}},xa})<<<1)+initial_quotient;
 wire [1:0] region_id=edge_id[4:3];wire [3:0] vi={1'b0,edge_id[2:0]};
 wire [3:0] n=fc[region_id*4+:4];
 wire [3:0] ni=vi+1==n?(fclosed[region_id]?4'd0:vi):vi+1'b1;
 function [20:0] vertex_at;input [671:0] table_data;input [1:0] r;input [3:0] i;begin
case({r,i[2:0]})
5'd0:vertex_at=table_data[0+:21];
5'd1:vertex_at=table_data[21+:21];
5'd2:vertex_at=table_data[42+:21];
5'd3:vertex_at=table_data[63+:21];
5'd4:vertex_at=table_data[84+:21];
5'd5:vertex_at=table_data[105+:21];
5'd6:vertex_at=table_data[126+:21];
5'd7:vertex_at=table_data[147+:21];
5'd8:vertex_at=table_data[168+:21];
5'd9:vertex_at=table_data[189+:21];
5'd10:vertex_at=table_data[210+:21];
5'd11:vertex_at=table_data[231+:21];
5'd12:vertex_at=table_data[252+:21];
5'd13:vertex_at=table_data[273+:21];
5'd14:vertex_at=table_data[294+:21];
5'd15:vertex_at=table_data[315+:21];
5'd16:vertex_at=table_data[336+:21];
5'd17:vertex_at=table_data[357+:21];
5'd18:vertex_at=table_data[378+:21];
5'd19:vertex_at=table_data[399+:21];
5'd20:vertex_at=table_data[420+:21];
5'd21:vertex_at=table_data[441+:21];
5'd22:vertex_at=table_data[462+:21];
5'd23:vertex_at=table_data[483+:21];
5'd24:vertex_at=table_data[504+:21];
5'd25:vertex_at=table_data[525+:21];
5'd26:vertex_at=table_data[546+:21];
5'd27:vertex_at=table_data[567+:21];
5'd28:vertex_at=table_data[588+:21];
5'd29:vertex_at=table_data[609+:21];
5'd30:vertex_at=table_data[630+:21];
5'd31:vertex_at=table_data[651+:21];
endcase
if(i[3])vertex_at=0;end endfunction
 wire edge_used=n!=0 && (n==1?vi==0:(fclosed[region_id]?vi<n:vi+1<n));
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
 reg signed [13:0] map_ax,map_ay,map_bx,map_by;
 wire [20:0] map_point=vertex_at(fv,region_id,field[1]?ni:vi);
 wire signed [13:0] map_value=mapped(field[0]?{1'b0,map_point[20:11]}:map_point[10:0],
 field[0]?{1'b0,fy0}:fx0,fzoom,frotate,field[0]);
 reg [7:0] nibble;reg [10:0] base_x;reg [2:0] left_bit,right_bit;reg [7:0] edge_bits;
 wire [8:0] read_address=(y[0]?9'd160:9'd0)+{1'b0,x[10:3]};
 wire [8:0] write_address=(row[0]?9'd160:9'd0)+{1'b0,word_index};
 wire [31:0] generated_word={nibble[7],pending[30:28],nibble[6],pending[26:24],nibble[5],pending[22:20],nibble[4],pending[18:16],
 nibble[3],pending[14:12],nibble[2],pending[10:8],nibble[1],pending[6:4],nibble[0],pending[2:0]};
 always @(posedge clk)begin
 edge_q<=edge_mem[{edge_id,3'b000}+field[2:0]];
 if(state==WRITE_EDGE)edge_mem[{edge_id,3'b000}+field[2:0]]<=work[field*16+:16];
 line_q<=line_mem[read_address];
 if(state==GEN && region_phase==3)line_mem[write_address]<=generated_word;
 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin mask_valid_q<=0;offset_q<=0;end
 else begin mask_valid_q<=de && y<624 && bank_valid[y[0]] && bank_row[y[0]]==y && ready && !underrun;
 offset_q<=x[2:0];end end
 assign pixel_mask=mask_valid_q?(line_q>>(offset_q*4)):4'd0;
 function [23:0] color_for;input [1:0] r;input [3:0] status,done_mask;input [2:0] target,actual;input closed;
 begin color_for=24'h9098a0;
 if(!closed)color_for=24'h40d8ff;
 else if(status==6 && actual=={1'b0,r}+1'b1)color_for=24'hff4050;
 else if(done_mask[r])color_for=24'h40ff90;
 else if(target=={1'b0,r} && status!=0 && status!=5 && status!=6 && status!=7)color_for=24'hffe040;
 end endfunction
 integer j;reg [10:0] lx;reg [9:0] ly;reg [6:0] label_dx;
 always @*begin
 pixel_color=24'h9098a0;
 for(j=0;j<4;j=j+1)if(pixel_mask[j])pixel_color=color_for(j[1:0],fstate,fcompleted,fexpected,factual,fclosed[j]);
 label_on=0;label_glyph=0;label_gx=x[2:0];label_gy=0;label_color=24'h9098a0;label_dx=0;lx=0;ly=0;
 for(j=3;j>=0;j=j-1)begin lx=labels_x[j];ly=labels_y[j];
 if(ready && !underrun && labels_valid[j] && x>=lx && x<lx+48 && y>=ly && y<ly+16)begin
 label_on=1;label_dx=x-lx;label_gx=label_dx[2:0];label_gy=y-ly;label_color=color_for(j[1:0],fstate,fcompleted,fexpected,factual,fclosed[j]);
 case(label_dx[6:3])0:label_glyph=11;1:label_glyph=28;2:label_glyph=15;3:label_glyph=11;4:label_glyph=0;default:label_glyph=11+j;endcase
 end end end
 // Decode one packed edge, update its rational DDA, and emit a full row span.
 wire signed [15:0] cur_x=work[15:0],hq=work[45:30],end_x=work[109:94];
 wire [13:0] cur_r=work[29:16],hr=work[59:46],den=work[73:60];
 wire [9:0] first_y=work[83:74],last_y=work[93:84];
 wire valid_edge=work[110],first_native=work[111],last_native=work[112],horizontal=work[113],point_only=work[114];
 reg [127:0] advanced;reg signed [17:0] low_f,high_f,min_f,max_f,next_f;
 reg [14:0] rr,step_r;reg signed [17:0] step_q;
 reg [13:0] low_rem,high_rem,min_rem;reg signed [17:0] lo_pixel,hi_pixel;
 reg span_ok;
 always @*begin
 advanced=work;low_f=cur_x;low_rem=cur_r;high_f=cur_x;high_rem=cur_r;
 step_r={1'b0,hr}<<1;step_q=$signed(hq)<<<1;
 if(step_r>=den && den!=0)begin step_r=step_r-den;step_q=step_q+1;end
 if(first_native && row==first_y)begin step_q=$signed(hq);step_r={1'b0,hr};end
 rr={1'b0,cur_r}+step_r;next_f=$signed(cur_x)+step_q;
 if(rr>=den && den!=0)begin rr=rr-den;next_f=next_f+1;end
 if(horizontal)begin high_f=end_x;high_rem=0;end
 else if(last_native && row==last_y)begin high_f=end_x;high_rem=0;end
 else begin high_f=next_f;high_rem=rr[13:0];end
 if(low_f<high_f || (low_f==high_f && low_rem<=high_rem))begin min_f=low_f;max_f=high_f;min_rem=low_rem;end
 else begin min_f=high_f;max_f=low_f;min_rem=high_rem;end
 lo_pixel=(min_f>>>1)+((min_f[0] && min_rem!=0)?1:0);hi_pixel=(max_f+1)>>>1;
 if(fmode==1 && (point_only || (row==first_y && first_native) || (row==last_y && last_native)))begin
 lo_pixel=lo_pixel-2;hi_pixel=hi_pixel+2;end
 span_ok=valid_edge && row>=first_y && row<=last_y && hi_pixel>=0 && lo_pixel<1280;
 if(valid_edge && row>=first_y && row<last_y && !horizontal)begin advanced[15:0]=next_f[15:0];advanced[29:16]=rr[13:0];end
 end
 integer k;
 always @*begin nibble=0;base_x={word_index,3'b000};left_bit=0;right_bit=7;edge_bits=0;
 for(k=0;k<8;k=k+1)begin
 if(span_valid[{region_phase,k[2:0]}] && span_hi[{region_phase,k[2:0]}]>=base_x && span_lo[{region_phase,k[2:0]}]<=base_x+7)begin
 left_bit=span_lo[{region_phase,k[2:0]}]>base_x?span_lo[{region_phase,k[2:0]}][2:0]:3'd0;
 right_bit=span_hi[{region_phase,k[2:0]}]<base_x+7?span_hi[{region_phase,k[2:0]}][2:0]:3'd7;
 edge_bits=(8'hff<<left_bit)&(8'hff>>(7-right_bit));nibble=nibble|edge_bits;
 end end end
 integer label_index;
 always @*begin label_collision=0;
 for(label_index=0;label_index<4;label_index=label_index+1)
 if(label_index<label_id && labels_valid[label_index] && labels_valid[label_id] &&
 labels_x[label_id]<labels_x[label_index]+50 && labels_x[label_id]+50>labels_x[label_index] &&
 labels_y[label_id]<labels_y[label_index]+18 && labels_y[label_id]+18>labels_y[label_index])label_collision=1;
 end
 task next_prepared_edge;begin field<=0;write_is_row<=0;state<=WRITE_EDGE;end endtask
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin state<=IDLE;edge_id<=0;field<=0;fv<=0;fc<=0;fclosed<=0;fcompleted<=0;fmode<=0;
 fx0<=0;fy0<=0;fzoom<=0;fexpected<=0;factual<=0;frotate<=0;fstate<=0;
 xa<=0;ya<=0;xb<=0;yb<=0;dx<=0;dy<=0;half_q<=0;half_r<=0;product<=0;product_negative<=0;work<=0;write_is_row<=0;
 bank_valid<=0;bank_row[0]<=0;bank_row[1]<=0;row<=0;word_index<=0;region_phase<=0;pending<=0;span_valid<=0;
 labels_valid<=0;label_id<=0;label_up<=0;label_attempt<=0;mstart<=0;mop<=0;ma<=0;mb<=0;ready<=0;underrun<=0;
 map_ax<=0;map_ay<=0;map_bx<=0;map_by<=0;all_left<=15;all_right<=15;all_above<=15;all_below<=15;
 for(j=0;j<4;j=j+1)begin labels_x[j]<=0;labels_y[j]<=0;end
 end else begin mstart<=0;
 if(de && y<624 && fc!=0 && (!bank_valid[y[0]] || bank_row[y[0]]!=y))underrun<=1;
 case(state)
 MAP:begin
 case(field[1:0])0:map_ax<=map_value;1:map_ay<=map_value;2:map_bx<=map_value;3:map_by<=map_value;endcase
 if(field==3)begin field<=0;state<=MAP_FINISH;end else field<=field+1'b1;end
 MAP_FINISH:begin
 xa<=map_by<map_ay?map_bx:map_ax;ya<=map_by<map_ay?map_by:map_ay;
 xb<=map_by<map_ay?map_ax:map_bx;yb<=map_by<map_ay?map_ay:map_by;
 if(vi==0)begin
 labels_x[region_id]<=map_ax<0?0:map_ax>1232?1232:map_ax;
 labels_y[region_id]<=map_ay>=18?(map_ay>626?608:map_ay-18):(map_ay< -3?0:map_ay+3);
 end
 if(vi<n)begin
 all_left[region_id]<=all_left[region_id] && map_ax<0;all_right[region_id]<=all_right[region_id] && map_ax>=1280;
 all_above[region_id]<=all_above[region_id] && map_ay<0;all_below[region_id]<=all_below[region_id] && map_ay>=624;
 end
 work<=0;state<=ORDER;end
 ORDER:begin
 dx<=$signed(xb)-$signed(xa);dy<=$signed(yb)-$signed(ya);
 work[109:94]<=$signed(xb)<<<1;
 work[83:74]<=ya<0?0:ya>623?623:ya;work[93:84]<=yb<0?0:yb>623?623:yb;
 work[111]<=ya>=0 && ya<=623;work[112]<=yb>=0 && yb<=623;
 work[110]<=edge_used && yb>=0 && ya<=623;
 if(!edge_used || yb<0 || ya>623)next_prepared_edge();
 else if(ya==yb)begin work[15:0]<=$signed(xa)<<<1;work[113]<=1;work[114]<=n==1;
 if(n==1 && fmode==1)begin work[83:74]<=ya<2?0:ya-2;work[93:84]<=ya>621?623:ya+2;end
 next_prepared_edge();end else state<=DIV_HALF;
 end
 DIV_HALF:begin mop<=1;ma<=dx<0?-$signed(dx):$signed(dx);mb<={32'd0,dy};mstart<=1;state<=WAIT_HALF;end
 WAIT_HALF:if(mdone)begin
 if(dx<0)begin half_q<=-$signed(mr)-(mrem!=0);half_r<=mrem==0?0:dy-mrem;end
 else begin half_q<=mr[15:0];half_r<=mrem[13:0];end
 state<=MUL_START;end
 MUL_START:begin
 work[45:30]<=half_q;work[59:46]<=half_r;work[73:60]<=dy[13:0];
 if(ya>=0)begin work[15:0]<=$signed(xa)<<<1;work[29:16]<=0;next_prepared_edge();end
 else begin mop<=0;ma<={{32{dx[15]}},dx};mb<=-48'sd1-($signed(ya)<<<1);mstart<=1;state<=WAIT_MUL;end end
 WAIT_MUL:if(mdone)begin product<=$signed(mr);product_negative<=mr[47];state<=DIV_INITIAL;end
 DIV_INITIAL:begin mop<=1;ma<=product_negative?-$signed(product):product;mb<={32'd0,dy};mstart<=1;state<=WAIT_INITIAL;end
 WAIT_INITIAL:if(mdone)begin
 work[15:0]<=initial_x[15:0];
 work[29:16]<=product_negative?(mrem==0?0:dy-mrem):mrem;
 next_prepared_edge();end
 WRITE_EDGE:begin
 if(field==7)begin field<=0;
 if(write_is_row)begin if(edge_id==31)begin word_index<=0;region_phase<=0;state<=GEN;end
 else begin edge_id<=edge_id+1'b1;state<=READ_EDGE;end end
 else if(edge_id==31)begin row<=0;state<=LABEL_PLACE;label_id<=0;label_attempt<=0;label_up<=labels_y[0]>304;
 for(j=0;j<4;j=j+1)labels_valid[j]<=fc[j*4+:4]!=0 && !all_left[j] && !all_right[j] && !all_above[j] && !all_below[j];
 end else begin edge_id<=edge_id+1'b1;state<=MAP;end
 end else field<=field+1'b1;end
 LABEL_PLACE:begin
 if(!label_collision || !labels_valid[label_id])begin
 if(label_id==3)state<=ROW_BEGIN;
 else begin label_id<=label_id+1'b1;label_attempt<=0;label_up<=labels_y[label_id+1'b1]>304;end end
 else if(label_attempt==35)begin underrun<=1;state<=ROW_BEGIN;end
 else begin
 label_attempt<=label_attempt+1'b1;
 if(label_up && labels_y[label_id]>=18)labels_y[label_id]<=labels_y[label_id]-18;
 else if(!label_up && labels_y[label_id]<=590)labels_y[label_id]<=labels_y[label_id]+18;
 else begin label_up<=~label_up;labels_x[label_id]<=labels_x[label_id]>=64?labels_x[label_id]-64:labels_x[label_id]+64;end
 end end
 ROW_BEGIN:begin edge_id<=0;field<=0;span_valid<=0;bank_valid[row[0]]<=0;state<=READ_EDGE;end
 READ_EDGE:begin
 if(field!=0)work[(field-1'b1)*16+:16]<=edge_q;
 if(field==8)begin field<=0;state<=ROW_EDGE;end else field<=field+1'b1;end
 ROW_EDGE:begin
 span_valid[edge_id]<=span_ok;span_lo[edge_id]<=lo_pixel<0?0:lo_pixel[10:0];span_hi[edge_id]<=hi_pixel>1279?1279:hi_pixel[10:0];
 work<=advanced;field<=0;write_is_row<=1;state<=WRITE_EDGE;end
 GEN:begin
 for(j=0;j<8;j=j+1)pending[j*4+region_phase]<=nibble[j];
 if(region_phase==3)begin region_phase<=0;
 if(word_index==159)begin bank_valid[row[0]]<=1;bank_row[row[0]]<=row;ready<=1;state<=WAIT_ROW;end
 else word_index<=word_index+1'b1;end else region_phase<=region_phase+1'b1;end
 WAIT_ROW:if(row<623 && (row==0 || y>=row))begin row<=row+1'b1;state<=ROW_BEGIN;end
 default:begin end
 endcase
 if(commit)begin
 fv<=vertices;fc<=counts;fclosed<=closed_mask;fcompleted<=completed;fmode<=ui_mode;fx0<=x0;fy0<=y0;fzoom<=zoom;frotate<=rotate;
 fstate<=run_state;fexpected<=expected_area;factual<=actual_area;
 state<=counts==0?IDLE:MAP;edge_id<=0;field<=0;bank_valid<=0;ready<=counts==0;underrun<=0;labels_valid<=0;
 all_left<=15;all_right<=15;all_above<=15;all_below<=15;
 end
 end end
endmodule
`default_nettype wire
