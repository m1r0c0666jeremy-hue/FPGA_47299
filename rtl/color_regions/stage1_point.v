// Exact source-coordinate containment, boundary band and floor Euclidean distance.
// The caller keeps vertices/counts stable until done. One request per new frame.
`default_nettype none
module stage1_point(input wire clk,rst_n,start,input wire [2:0] region_count,
 input wire [15:0] counts,input wire [671:0] vertices,
 input wire [10:0] px,input wire [9:0] py,
 output reg busy,done,output reg [3:0] inside_mask,near_mask,
 output reg [43:0] distances,
 input wire orientation_start,input wire [20:0] oa,ob,oc,
 output reg orientation_done,output reg signed [23:0] orientation_cross);
 reg orientation_only;
 reg [3:0] state;reg [3:0] phase;reg [1:0] region_id;reg [3:0] edge_id,n;
 reg [2:0] total;reg [10:0] qx,ax,bx;reg [9:0] qy,ay,by;
 // Coordinates are bounded to 1280x720. Differences need signed 12 bits;
 // squared endpoint distances fit 22 bits, orientation/dot products 24 bits.
 reg signed [11:0] dx,dy,wx,wy,ex,ey;
 reg signed [23:0] dot,part,cross_value;
 reg [21:0] length2,best,endpoint_part;reg [47:0] numerator;
 reg parity,near_edge;
 reg mstart;reg [1:0] mop;reg [47:0] ma,mb;wire mbusy,mdone;wire [47:0] mr;
 // A source-space triangle has |cross| <= 1279*719 = 919601.
 // Signed 21-bit multiplication therefore covers cross squared exactly.
 stage1_arith #(.MW(21),.DW(23)) alu(clk,rst_n,mstart,mop,ma,mb,mbusy,mdone,mr,);
 function [20:0] point;input [671:0] table_data;input [1:0] r;input [3:0] i;begin
case({r,i[2:0]})
5'd0:point=table_data[0+:21];
5'd1:point=table_data[21+:21];
5'd2:point=table_data[42+:21];
5'd3:point=table_data[63+:21];
5'd4:point=table_data[84+:21];
5'd5:point=table_data[105+:21];
5'd6:point=table_data[126+:21];
5'd7:point=table_data[147+:21];
5'd8:point=table_data[168+:21];
5'd9:point=table_data[189+:21];
5'd10:point=table_data[210+:21];
5'd11:point=table_data[231+:21];
5'd12:point=table_data[252+:21];
5'd13:point=table_data[273+:21];
5'd14:point=table_data[294+:21];
5'd15:point=table_data[315+:21];
5'd16:point=table_data[336+:21];
5'd17:point=table_data[357+:21];
5'd18:point=table_data[378+:21];
5'd19:point=table_data[399+:21];
5'd20:point=table_data[420+:21];
5'd21:point=table_data[441+:21];
5'd22:point=table_data[462+:21];
5'd23:point=table_data[483+:21];
5'd24:point=table_data[504+:21];
5'd25:point=table_data[525+:21];
5'd26:point=table_data[546+:21];
5'd27:point=table_data[567+:21];
5'd28:point=table_data[588+:21];
5'd29:point=table_data[609+:21];
5'd30:point=table_data[630+:21];
5'd31:point=table_data[651+:21];
endcase
if(i[3])point=0;end endfunction
 wire [3:0] read_index=state==8?(edge_id+1==n?4'd0:edge_id+1'b1):edge_id;
 wire [20:0] vertex_q=point(vertices,region_id,read_index);
 wire signed [23:0] cross_next=part-$signed(mr[23:0]);
 task take_distance;input [21:0] value;begin
 if(value<best)best<=value;
 if(edge_id+1==n)begin ma<=value<best?value:best;mop<=2;mstart<=1;state<=7;end
 else begin edge_id<=edge_id+1'b1;state<=1;end
 end endtask
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin state<=0;phase<=0;region_id<=0;edge_id<=0;n<=0;total<=0;
 qx<=0;qy<=0;ax<=0;ay<=0;bx<=0;by<=0;dx<=0;dy<=0;wx<=0;wy<=0;ex<=0;ey<=0;
 dot<=0;part<=0;cross_value<=0;length2<=0;best<=0;endpoint_part<=0;numerator<=0;parity<=0;near_edge<=0;
 mstart<=0;mop<=0;ma<=0;mb<=0;busy<=0;done<=0;inside_mask<=0;near_mask<=0;distances<=0;orientation_only<=0;orientation_done<=0;orientation_cross<=0;end
 else begin mstart<=0;done<=0;orientation_done<=0;
 case(state)
 0:if(orientation_start)begin
 orientation_only<=1;busy<=1;ax<=oa[10:0];ay<=oa[20:11];bx<=ob[10:0];by<=ob[20:11];
 qx<=oc[10:0];qy<=oc[20:11];state<=2;
 end else if(start)begin orientation_only<=0;busy<=region_count!=0;inside_mask<=0;near_mask<=0;distances<=0;
 total<=region_count;qx<=px;qy<=py;region_id<=0;edge_id<=0;n<=counts[3:0];
 best<=22'h3fffff;parity<=0;near_edge<=0;
 if(region_count==0)done<=1;else state<=1;end
 1:begin ax<=vertex_q[10:0];ay<=vertex_q[20:11];state<=8;end
 8:begin bx<=vertex_q[10:0];by<=vertex_q[20:11];state<=2;end
 2:begin
 dx<=$signed({1'b0,bx})-$signed({1'b0,ax});dy<=$signed({1'b0,by})-$signed({1'b0,ay});
 wx<=$signed({1'b0,qx})-$signed({1'b0,ax});wy<=$signed({1'b0,qy})-$signed({1'b0,ay});
 ex<=$signed({1'b0,qx})-$signed({1'b0,bx});ey<=$signed({1'b0,qy})-$signed({1'b0,by});phase<=orientation_only?4:0;state<=3;end
 3:begin mop<=0;mstart<=1;state<=4;
 case(phase)
 0:begin ma<={{36{dx[11]}},dx};mb<={{36{dx[11]}},dx};end
 1:begin ma<={{36{dy[11]}},dy};mb<={{36{dy[11]}},dy};end
 2:begin ma<={{36{wx[11]}},wx};mb<={{36{dx[11]}},dx};end
 3:begin ma<={{36{wy[11]}},wy};mb<={{36{dy[11]}},dy};end
 4:begin ma<={{36{dx[11]}},dx};mb<={{36{wy[11]}},wy};end
 5:begin ma<={{36{dy[11]}},dy};mb<={{36{wx[11]}},wx};end
 6:begin ma<=cross_value;mb<=cross_value;end
 7:begin ma<=(dot<=0 || length2==0)?{{36{wx[11]}},wx}:{{36{ex[11]}},ex};
 mb<=(dot<=0 || length2==0)?{{36{wx[11]}},wx}:{{36{ex[11]}},ex};end
 default:begin ma<=(dot<=0 || length2==0)?{{36{wy[11]}},wy}:{{36{ey[11]}},ey};
 mb<=(dot<=0 || length2==0)?{{36{wy[11]}},wy}:{{36{ey[11]}},ey};end
 endcase end
 4:if(mdone)begin
 case(phase)
 0:begin length2<=mr;phase<=1;state<=3;end
 1:begin length2<=length2+mr;phase<=2;state<=3;end
 2:begin dot<=$signed(mr);phase<=3;state<=3;end
 3:begin dot<=dot+$signed(mr);phase<=4;state<=3;end
 4:begin part<=$signed(mr);phase<=5;state<=3;end
 5:if(orientation_only)begin orientation_cross<=cross_next;orientation_done<=1;busy<=0;state<=0;end
 else begin cross_value<=cross_next;
 if((ay>qy)!=(by>qy))if((dy>0 && cross_next>0)||(dy<0 && cross_next<0))parity<=~parity;
 phase<=(dot>0 && dot<$signed({1'b0,length2}) && length2!=0)?6:7;state<=3;end
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
 best<=22'h3fffff;parity<=0;near_edge<=0;state<=1;end end
 default:state<=0;
 endcase end end
endmodule
`default_nettype wire
