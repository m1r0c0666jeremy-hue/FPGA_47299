// Frame-blanking coordinate pipeline: two extra preparation clocks; pixel timing is unchanged.
`default_nettype none
module refined_overlay_geometry(input wire clk,rst_n,commit,
 input wire [639:0] meta,input wire [10:0] x0,input wire [9:0] y0,
 input wire [2:0] zoom,input wire rotate,
 output reg ready,output reg [251:0] points);
 reg busy;reg [4:0] index;reg axis_y,endpoint,is_tip,large_sample;
 reg [10:0] source;reg [41:0] box;reg signed [13:0] delta;
 reg va,vb;reg [4:0] ia,ib;reg ea,eb,ta,tb,ra,rb,ya,yb;
 reg signed [13:0] da,lb,ub;reg [2:0] za;
 reg signed [14:0] middle;reg signed [13:0] mapped;
 function signed [13:0] ceiling;input signed [13:0] n;input [2:0] z;
 reg signed [13:0] triple;begin triple=(n<<<1)+n;
 case(z)1:ceiling=(triple+14'sd1)>>>1;2:ceiling=n<<<1;3:ceiling=triple;4:ceiling=n<<<2;default:ceiling=n;endcase
 end endfunction
 always @*begin
 axis_y=index<16?index[1]:index[0];is_tip=index>=16;endpoint=index[0]^rotate;
 large_sample=meta[567:565]!=0 && meta[567:565]!=2;
 box=index[2]?meta[183:142]:meta[141:100];source=0;
 if(index<8)begin
 if(axis_y)source=endpoint?{1'b0,box[41:32]}:{1'b0,box[31:22]};else source=endpoint?box[21:11]:box[10:0];end
 else if(index<12)source=axis_y?(endpoint?539:180):(endpoint?959:320);
 else if(index<16)source=axis_y?(endpoint?(large_sample?367:363):(large_sample?352:356)):(endpoint?(large_sample?647:643):(large_sample?632:636));
 else source=axis_y?{1'b0,meta[99:90]}:meta[89:79];
 delta=$signed({3'd0,source})-$signed(axis_y?{4'd0,y0}:{3'd0,x0});
 middle=($signed({lb[13],lb})+$signed({ub[13],ub}))>>>1;
 mapped=tb?middle[13:0]:eb?ub:lb;
 if(rb)mapped=(yb?14'sd623:14'sd1279)-mapped;
 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin ready<=0;busy<=0;index<=0;points<=0;
 va<=0;vb<=0;ia<=0;ib<=0;ea<=0;eb<=0;ta<=0;tb<=0;ra<=0;rb<=0;ya<=0;yb<=0;da<=0;lb<=0;ub<=0;za<=0;end
 else if(commit)begin ready<=0;busy<=1;index<=0;va<=0;vb<=0;end
 else begin
 va<=busy;vb<=va;
 if(busy)begin da<=delta;za<=zoom;ea<=endpoint;ta<=is_tip;ra<=rotate;ya<=axis_y;ia<=index;
 if(index==17)busy<=0;else index<=index+1'b1;end
 if(va)begin lb<=ceiling(da,za);ub<=ceiling(da+14'sd1,za)-14'sd1;
 eb<=ea;tb<=ta;rb<=ra;yb<=ya;ib<=ia;end
 if(vb)begin points[ib*14+:14]<=mapped;if(ib==17)ready<=1;end
 end end
endmodule
`default_nettype wire
