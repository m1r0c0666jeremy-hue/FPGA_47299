// Validate a draft without changing saved regions. Touching is deliberately invalid.
`default_nettype none
module stage1_validate(input wire clk,rst_n,start,input wire [2:0] region_count,
 input wire [15:0] counts,input wire [671:0] vertices,input wire [3:0] draft_count,
 input wire [167:0] draft,output reg busy,done,passed,output reg [3:0] error_code);
 reg [3:0] state,i,j;reg [1:0] old_region;reg external_pairs,reverse;
 reg seg_start,point_start;wire seg_busy,seg_done,hit,overlap,point_busy,point_done;
 wire [3:0] in_mask,near_mask;wire [43:0] distances;
 wire [3:0] old_n=counts[old_region*4+:4];
 function [20:0] dp;input [167:0] table_data;input [3:0] index;begin dp=table_data[index*21+:21];end endfunction
 function [20:0] vp;input [671:0] table_data;input [1:0] r;input [3:0] index;begin vp=table_data[({r,3'b000}+index)*21+:21];end endfunction
 wire [20:0] a=dp(draft,i),b=dp(draft,i+1==draft_count?4'd0:i+1'b1);
 wire [20:0] c=external_pairs?vp(vertices,old_region,j):dp(draft,j);
 wire [20:0] d=external_pairs?vp(vertices,old_region,j+1==old_n?4'd0:j+1'b1):dp(draft,j+1==draft_count?4'd0:j+1'b1);
 wire adjacent=j==i+1 || (i==0 && j+1==draft_count);
 stage1_segment segments(clk,rst_n,seg_start,a,b,c,d,seg_busy,seg_done,hit,overlap);
 wire [20:0] query_point=reverse?vp(vertices,old_region,0):dp(draft,0);
 stage1_point containment(clk,rst_n,point_start,reverse?3'd1:region_count,
 reverse?{12'd0,draft_count}:counts,reverse?{504'd0,draft}:vertices,
 query_point[10:0],query_point[20:11],point_busy,point_done,in_mask,near_mask,distances);
 task finish;input ok;input [3:0] why;begin busy<=0;done<=1;passed<=ok;error_code<=why;state<=0;end endtask
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin state<=0;i<=0;j<=0;old_region<=0;external_pairs<=0;reverse<=0;
 seg_start<=0;point_start<=0;busy<=0;done<=0;passed<=0;error_code<=0;end
 else begin done<=0;seg_start<=0;point_start<=0;
 case(state)
 0:if(start)begin
 busy<=1;passed<=0;error_code<=0;i<=0;j<=1;external_pairs<=0;old_region<=0;reverse<=0;
 if(draft_count<3)finish(0,1);else if(draft_count>8 || region_count>=4)finish(0,4);else state<=1;end
 1:if(a==b || c==d)finish(0,2);else begin seg_start<=1;state<=2;end
 2:if(seg_done)begin
 if(hit && (external_pairs || !adjacent || overlap))finish(0,external_pairs?4'd3:4'd2);
 else if(external_pairs)begin
 if(j+1<old_n)begin j<=j+1'b1;state<=1;end
 else if(i+1<draft_count)begin i<=i+1'b1;j<=0;state<=1;end
 else if({1'b0,old_region}+1<region_count)begin old_region<=old_region+1'b1;i<=0;j<=0;state<=1;end
 else begin reverse<=0;point_start<=1;state<=3;end
 end else begin
 if(j+1<draft_count)begin j<=j+1'b1;state<=1;end
 else if(i+2<draft_count)begin i<=i+1'b1;j<=i+2;state<=1;end
 else if(region_count==0)finish(1,0);
 else begin external_pairs<=1;old_region<=0;i<=0;j<=0;state<=1;end
 end end
 3:if(point_done)begin
 if(in_mask!=0)finish(0,3);
 else if(!reverse)begin reverse<=1;old_region<=0;state<=4;end
 else if({1'b0,old_region}+1<region_count)begin old_region<=old_region+1'b1;state<=4;end
 else finish(1,0);end
 4:begin point_start<=1;state<=3;end
 default:state<=0;
 endcase end end
endmodule
`default_nettype wire
