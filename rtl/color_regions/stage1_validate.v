// Validate a draft without changing saved regions. Touching is deliberately invalid.
`default_nettype none
module stage1_validate #(parameter SHARED=0)(input wire clk,rst_n,start,input wire [2:0] region_count,
 input wire [15:0] counts,input wire [671:0] vertices,input wire [3:0] draft_count,
 input wire [167:0] draft,output reg busy,done,passed,output reg [3:0] error_code,
 output wire orientation_start,output wire [20:0] oa,ob,oc,
 input wire orientation_done,input wire signed [23:0] orientation_cross);
 reg [3:0] state,i,j;reg [1:0] old_region;reg external_pairs,reverse;
 reg seg_start,parity;wire seg_busy,seg_done,hit,overlap,ray_hit;
 wire [3:0] old_n=counts[old_region*4+:4];
 function [20:0] dp;input [167:0] table_data;input [3:0] index;begin
case(index)
4'd0:dp=table_data[0+:21];
4'd1:dp=table_data[21+:21];
4'd2:dp=table_data[42+:21];
4'd3:dp=table_data[63+:21];
4'd4:dp=table_data[84+:21];
4'd5:dp=table_data[105+:21];
4'd6:dp=table_data[126+:21];
4'd7:dp=table_data[147+:21];
default:dp=0;endcase end endfunction
 function [20:0] vp;input [671:0] table_data;input [1:0] r;input [3:0] index;begin
case({r,index[2:0]})
5'd0:vp=table_data[0+:21];
5'd1:vp=table_data[21+:21];
5'd2:vp=table_data[42+:21];
5'd3:vp=table_data[63+:21];
5'd4:vp=table_data[84+:21];
5'd5:vp=table_data[105+:21];
5'd6:vp=table_data[126+:21];
5'd7:vp=table_data[147+:21];
5'd8:vp=table_data[168+:21];
5'd9:vp=table_data[189+:21];
5'd10:vp=table_data[210+:21];
5'd11:vp=table_data[231+:21];
5'd12:vp=table_data[252+:21];
5'd13:vp=table_data[273+:21];
5'd14:vp=table_data[294+:21];
5'd15:vp=table_data[315+:21];
5'd16:vp=table_data[336+:21];
5'd17:vp=table_data[357+:21];
5'd18:vp=table_data[378+:21];
5'd19:vp=table_data[399+:21];
5'd20:vp=table_data[420+:21];
5'd21:vp=table_data[441+:21];
5'd22:vp=table_data[462+:21];
5'd23:vp=table_data[483+:21];
5'd24:vp=table_data[504+:21];
5'd25:vp=table_data[525+:21];
5'd26:vp=table_data[546+:21];
5'd27:vp=table_data[567+:21];
5'd28:vp=table_data[588+:21];
5'd29:vp=table_data[609+:21];
5'd30:vp=table_data[630+:21];
5'd31:vp=table_data[651+:21];
endcase
if(index[3])vp=0;end endfunction
 reg [20:0] a,b,c,d;reg [1:0] fetch;reg read_draft;reg [3:0] read_index;
 wire adjacent=j==i+1 || (i==0 && j+1==draft_count);
 wire [3:0] ray_n=reverse?draft_count:old_n;
 always @*begin
 read_draft=1;read_index=0;
 if(state==3)begin
 read_draft=fetch==2?!reverse:reverse;
 read_index=fetch==2?4'd0:fetch==1?(j+1==ray_n?4'd0:j+1'b1):j;
 end else begin
 case(fetch)
 0:read_index=i;
 1:read_index=i+1==draft_count?4'd0:i+1'b1;
 2:begin read_draft=!external_pairs;read_index=j;end
 3:begin read_draft=!external_pairs;read_index=j+1==(external_pairs?old_n:draft_count)?4'd0:j+1'b1;end
 endcase end end
 wire [20:0] vertex_q=read_draft?dp(draft,read_index):vp(vertices,old_region,read_index);
 // Validation already excludes every edge touch. Reuse its exact orientation
 // engine for half-open ray parity; no second distance/division engine is needed.
 stage1_segment #(.SHARED(SHARED)) segments(clk,rst_n,seg_start,a,b,c,d,seg_busy,seg_done,hit,overlap,ray_hit,orientation_start,oa,ob,oc,orientation_done,orientation_cross);
 task finish;input ok;input [3:0] why;begin busy<=0;done<=1;passed<=ok;error_code<=why;state<=0;end endtask
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin state<=0;i<=0;j<=0;old_region<=0;external_pairs<=0;reverse<=0;
 a<=0;b<=0;c<=0;d<=0;fetch<=0;seg_start<=0;parity<=0;busy<=0;done<=0;passed<=0;error_code<=0;end
 else begin done<=0;seg_start<=0;
 case(state)
 0:if(start)begin
 busy<=1;passed<=0;error_code<=0;i<=0;j<=1;external_pairs<=0;old_region<=0;reverse<=0;
 if(draft_count<3)finish(0,1);else if(draft_count>8 || region_count>=4)finish(0,4);else state<=1;end
 1:begin
 case(fetch)0:a<=vertex_q;1:b<=vertex_q;2:c<=vertex_q;3:d<=vertex_q;endcase
 if(fetch==3)begin fetch<=0;state<=5;end else fetch<=fetch+1'b1;end
 5:if(a==b || c==d)finish(0,2);else begin seg_start<=1;state<=2;end
 2:if(seg_done)begin
 if(hit && (external_pairs || !adjacent || overlap))finish(0,external_pairs?4'd3:4'd2);
 else if(external_pairs)begin
 if(j+1<old_n)begin j<=j+1'b1;state<=1;end
 else if(i+1<draft_count)begin i<=i+1'b1;j<=0;state<=1;end
 else if({1'b0,old_region}+1<region_count)begin old_region<=old_region+1'b1;i<=0;j<=0;state<=1;end
 else begin reverse<=0;old_region<=0;j<=0;parity<=0;state<=3;end
 end else begin
 if(j+1<draft_count)begin j<=j+1'b1;state<=1;end
 else if(i+2<draft_count)begin i<=i+1'b1;j<=i+2;state<=1;end
 else if(region_count==0)finish(1,0);
 else begin external_pairs<=1;old_region<=0;i<=0;j<=0;state<=1;end
 end end
 3:begin
 case(fetch)0:a<=vertex_q;1:b<=vertex_q;2:begin c<=vertex_q;d<=vertex_q;end endcase
 if(fetch==2)begin fetch<=0;state<=6;end else fetch<=fetch+1'b1;end
 6:begin seg_start<=1;state<=4;end
 4:if(seg_done)begin
 if(j+1<ray_n)begin parity<=parity^ray_hit;j<=j+1'b1;state<=3;end
 else if(parity^ray_hit)finish(0,3);
 else if({1'b0,old_region}+1<region_count)begin old_region<=old_region+1'b1;j<=0;parity<=0;state<=3;end
 else if(!reverse)begin reverse<=1;old_region<=0;j<=0;parity<=0;state<=3;end
 else finish(1,0);end
 default:state<=0;
 endcase end end
endmodule
`default_nettype wire
