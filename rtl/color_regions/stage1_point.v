// Exact source-coordinate containment, boundary band and floor Euclidean distance.
// The caller keeps vertices/counts stable until done. One request per new frame.
`default_nettype none
module stage1_point(input wire clk,rst_n,start,input wire [2:0] region_count,
 input wire [15:0] counts,input wire [671:0] vertices,
 input wire [10:0] px,input wire [9:0] py,
 output reg busy,done,output reg [3:0] inside_mask,near_mask,
 output reg [43:0] distances);
 reg [3:0] state;reg [3:0] phase;reg [1:0] region_id;reg [3:0] edge_id,n;
 reg [2:0] total;reg [10:0] qx,ax,bx;reg [9:0] qy,ay,by;
 reg signed [23:0] dx,dy,wx,wy,ex,ey;
 reg signed [47:0] dot,part,cross_value;
 reg [47:0] length2,best,endpoint_part,numerator;
 reg parity,near_edge;
 reg mstart;reg [1:0] mop;reg [47:0] ma,mb;wire mbusy,mdone;wire [47:0] mr;
 stage1_arith alu(clk,rst_n,mstart,mop,ma,mb,mbusy,mdone,mr,);
 function [20:0] point;input [671:0] table_data;input [1:0] r;input [3:0] i;begin point=table_data[({r,3'b000}+i)*21+:21];end endfunction
 reg [20:0] va,vb;
 always @*begin va=point(vertices,region_id,edge_id);vb=point(vertices,region_id,edge_id+1==n?4'd0:edge_id+1'b1);end
 wire signed [47:0] cross_next=part-$signed(mr);
 task take_distance;input [47:0] value;begin
 if(value<best)best<=value;
 if(edge_id+1==n)begin ma<=value<best?value:best;mop<=2;mstart<=1;state<=7;end
 else begin edge_id<=edge_id+1'b1;state<=1;end
 end endtask
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin state<=0;phase<=0;region_id<=0;edge_id<=0;n<=0;total<=0;
 qx<=0;qy<=0;ax<=0;ay<=0;bx<=0;by<=0;dx<=0;dy<=0;wx<=0;wy<=0;ex<=0;ey<=0;
 dot<=0;part<=0;cross_value<=0;length2<=0;best<=0;endpoint_part<=0;numerator<=0;parity<=0;near_edge<=0;
 mstart<=0;mop<=0;ma<=0;mb<=0;busy<=0;done<=0;inside_mask<=0;near_mask<=0;distances<=0;end
 else begin mstart<=0;done<=0;
 case(state)
 0:if(start)begin busy<=region_count!=0;inside_mask<=0;near_mask<=0;distances<=0;
 total<=region_count;qx<=px;qy<=py;region_id<=0;edge_id<=0;n<=counts[3:0];
 best<=48'hffffffffffff;parity<=0;near_edge<=0;
 if(region_count==0)done<=1;else state<=1;end
 1:begin ax<=va[10:0];ay<=va[20:11];bx<=vb[10:0];by<=vb[20:11];state<=2;end
 2:begin
 dx<=$signed({1'b0,bx})-$signed({1'b0,ax});dy<=$signed({1'b0,by})-$signed({1'b0,ay});
 wx<=$signed({1'b0,qx})-$signed({1'b0,ax});wy<=$signed({1'b0,qy})-$signed({1'b0,ay});
 ex<=$signed({1'b0,qx})-$signed({1'b0,bx});ey<=$signed({1'b0,qy})-$signed({1'b0,by});phase<=0;state<=3;end
 3:begin mop<=0;mstart<=1;state<=4;
 case(phase)
 0:begin ma<={{24{dx[23]}},dx};mb<={{24{dx[23]}},dx};end
 1:begin ma<={{24{dy[23]}},dy};mb<={{24{dy[23]}},dy};end
 2:begin ma<={{24{wx[23]}},wx};mb<={{24{dx[23]}},dx};end
 3:begin ma<={{24{wy[23]}},wy};mb<={{24{dy[23]}},dy};end
 4:begin ma<={{24{dx[23]}},dx};mb<={{24{wy[23]}},wy};end
 5:begin ma<={{24{dy[23]}},dy};mb<={{24{wx[23]}},wx};end
 6:begin ma<=cross_value;mb<=cross_value;end
 7:begin ma<=(dot<=0 || length2==0)?{{24{wx[23]}},wx}:{{24{ex[23]}},ex};
 mb<=(dot<=0 || length2==0)?{{24{wx[23]}},wx}:{{24{ex[23]}},ex};end
 default:begin ma<=(dot<=0 || length2==0)?{{24{wy[23]}},wy}:{{24{ey[23]}},ey};
 mb<=(dot<=0 || length2==0)?{{24{wy[23]}},wy}:{{24{ey[23]}},ey};end
 endcase end
 4:if(mdone)begin
 case(phase)
 0:begin length2<=mr;phase<=1;state<=3;end
 1:begin length2<=length2+mr;phase<=2;state<=3;end
 2:begin dot<=$signed(mr);phase<=3;state<=3;end
 3:begin dot<=dot+$signed(mr);phase<=4;state<=3;end
 4:begin part<=$signed(mr);phase<=5;state<=3;end
 5:begin cross_value<=cross_next;
 if((ay>qy)!=(by>qy))if((dy>0 && cross_next>0)||(dy<0 && cross_next<0))parity<=~parity;
 phase<=(dot>0 && dot<$signed(length2) && length2!=0)?6:7;state<=3;end
 6:begin numerator<=mr;if(mr<=(length2<<2))near_edge<=1;state<=5;end
 7:begin endpoint_part<=mr;phase<=8;state<=3;end
 default:begin if(endpoint_part+mr<=4)near_edge<=1;take_distance(endpoint_part+mr);end
 endcase end
 5:begin mop<=1;ma<=numerator;mb<=length2;mstart<=1;state<=6;end
 6:if(mdone)take_distance(mr);
 7:if(mdone)begin inside_mask[region_id]<=parity;near_mask[region_id]<=near_edge;
 distances[region_id*11+:11]<=mr[10:0];
 if({1'b0,region_id}+1==total)begin busy<=0;done<=1;state<=0;end
 else begin region_id<=region_id+1'b1;n<=counts[(region_id+1'b1)*4+:4];edge_id<=0;
 best<=48'hffffffffffff;parity<=0;near_edge<=0;state<=1;end end
 default:state<=0;
 endcase end end
endmodule
`default_nettype wire
