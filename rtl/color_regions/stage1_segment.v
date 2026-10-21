// Inclusive segment intersection and positive-length collinear overlap.
`default_nettype none
module stage1_segment(input wire clk,rst_n,start,input wire [20:0] a,b,c,d,
 output reg busy,done,hit,overlap,output wire ray_hit);
 reg [20:0] aa,bb,cc,dd;reg [2:0] state;reg [1:0] orient;reg half;
 reg signed [11:0] dx,dy,wx,wy;reg signed [23:0] first;
 reg signed [23:0] o0,o1,o2,o3;
 reg mstart;wire mbusy,mdone;wire [47:0] mr;
 reg [47:0] ma,mb;stage1_arith #(.MW(12)) alu(clk,rst_n,mstart,2'd0,ma,mb,mbusy,mdone,mr,);
 assign ray_hit=(aa[20:11]>cc[20:11])!=(bb[20:11]>cc[20:11]) &&
 ((bb[20:11]>aa[20:11] && !o0[23] && o0!=0) || (bb[20:11]<aa[20:11] && o0[23]));
 function [10:0] lo;input [10:0] x,y;begin lo=x<y?x:y;end endfunction
 function [10:0] hi;input [10:0] x,y;begin hi=x>y?x:y;end endfunction
 wire box_hit=lo(aa[10:0],bb[10:0])<=hi(cc[10:0],dd[10:0]) && lo(cc[10:0],dd[10:0])<=hi(aa[10:0],bb[10:0]) &&
 lo({1'b0,aa[20:11]},{1'b0,bb[20:11]})<=hi({1'b0,cc[20:11]},{1'b0,dd[20:11]}) &&
 lo({1'b0,cc[20:11]},{1'b0,dd[20:11]})<=hi({1'b0,aa[20:11]},{1'b0,bb[20:11]});
 wire collinear=o0==0 && o1==0 && o2==0 && o3==0;
 wire x_span=lo(hi(aa[10:0],bb[10:0]),hi(cc[10:0],dd[10:0]))>hi(lo(aa[10:0],bb[10:0]),lo(cc[10:0],dd[10:0]));
 wire y_span=lo(hi({1'b0,aa[20:11]},{1'b0,bb[20:11]}),hi({1'b0,cc[20:11]},{1'b0,dd[20:11]}))>
 hi(lo({1'b0,aa[20:11]},{1'b0,bb[20:11]}),lo({1'b0,cc[20:11]},{1'b0,dd[20:11]}));
 reg [20:0] u,v,p;
 always @*begin
 u=orient[1]?cc:aa;v=orient[1]?dd:bb;
 case(orient)0:p=cc;1:p=dd;2:p=aa;default:p=bb;endcase end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin state<=0;orient<=0;half<=0;aa<=0;bb<=0;cc<=0;dd<=0;
 dx<=0;dy<=0;wx<=0;wy<=0;first<=0;o0<=0;o1<=0;o2<=0;o3<=0;
 mstart<=0;ma<=0;mb<=0;busy<=0;done<=0;hit<=0;overlap<=0;end
 else begin mstart<=0;done<=0;
 case(state)
 0:if(start)begin aa<=a;bb<=b;cc<=c;dd<=d;busy<=1;orient<=0;state<=1;end
 1:begin
 dx<=$signed({1'b0,v[10:0]})-$signed({1'b0,u[10:0]});
 dy<=$signed({1'b0,v[20:11]})-$signed({1'b0,u[20:11]});
 wx<=$signed({1'b0,p[10:0]})-$signed({1'b0,u[10:0]});
 wy<=$signed({1'b0,p[20:11]})-$signed({1'b0,u[20:11]});half<=0;state<=2;end
 2:begin mstart<=1;ma<=half?{{36{dy[11]}},dy}:{{36{dx[11]}},dx};
 mb<=half?{{36{wx[11]}},wx}:{{36{wy[11]}},wy};state<=3;end
 3:if(mdone)begin
 if(!half)begin first<=$signed(mr);half<=1;state<=2;end
 else begin
 case(orient)0:o0<=first-$signed(mr);1:o1<=first-$signed(mr);2:o2<=first-$signed(mr);3:o3<=first-$signed(mr);endcase
 if(orient==3)state<=4;else begin orient<=orient+1'b1;state<=1;end end end
 4:begin
 hit<=box_hit && (o0==0 || o1==0 || o0[23]!=o1[23]) && (o2==0 || o3==0 || o2[23]!=o3[23]);
 overlap<=collinear && box_hit && (aa[10:0]!=bb[10:0]?x_span:y_span);
 busy<=0;done<=1;state<=0;end
 default:state<=0;
 endcase end end
endmodule
`default_nettype wire
