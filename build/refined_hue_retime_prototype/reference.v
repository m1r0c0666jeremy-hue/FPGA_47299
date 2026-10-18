// Runtime colour model: valid63, hue-low62:54, hue-high53:45,
// value-min44:37, chroma-min36:29, saturation code28:27 (3,4,6,8 /16).
// Wrapped intervals have low > high. Four clock pipeline, no pixel divider.
`default_nettype none
module reference_model_lane(input wire clk,rst_n,input wire [23:0] rgb,
 input wire [127:0] models,output reg [1:0] hit);
 reg [7:0] r,g,b,m,d;reg [16:0] hn;
 reg [127:0] c0,c1,c2;reg [16:0] lo0,hi0,lo1,hi1,h2;
 reg [7:0] m2,d2;reg [1:0] amplitude;
 reg [7:0] mx,mn;reg signed [17:0] n;
 function sat_ok;input [7:0] mm,dd;input [1:0] code;
 reg [11:0] limit;begin
 case(code)0:limit=({4'd0,mm}<<1)+mm;1:limit={4'd0,mm}<<2;
 2:limit=({4'd0,mm}<<2)+({4'd0,mm}<<1);3:limit={4'd0,mm}<<3;endcase
 sat_ok=({4'd0,dd}<<4)>=limit;
 end endfunction
 // Hue = 60 * (channel difference + sector * chroma).
 // For all byte RGB values hue_units is nonnegative and at most 6*255.
 // The 11-bit modular sum is exact in that range; the product fits 17 bits.
 reg [7:0] hue_a,hue_b,hue_chroma;
 reg signed [8:0] hue_difference;
 reg [10:0] hue_offset,hue_units;
 always @*begin
 mx=r>g?(r>b?r:b):(g>b?g:b);mn=r<g?(r<b?r:b):(g<b?g:b);
 hue_chroma=mx-mn;
 if(mx==r)begin hue_a=g;hue_b=b;
 hue_offset=g<b?(({3'd0,hue_chroma}<<2)+({3'd0,hue_chroma}<<1)):11'd0;end
 else if(mx==g)begin hue_a=b;hue_b=r;hue_offset={3'd0,hue_chroma}<<1;end
 else begin hue_a=r;hue_b=g;hue_offset={3'd0,hue_chroma}<<2;end
 hue_difference=$signed({1'b0,hue_a})-$signed({1'b0,hue_b});
 hue_units=hue_offset+{{2{hue_difference[8]}},hue_difference};
 n=({7'd0,hue_units}<<6)-({7'd0,hue_units}<<2);
 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin r<=0;g<=0;b<=0;m<=0;d<=0;hn<=0;c0<=0;c1<=0;c2<=0;
 lo0<=0;hi0<=0;lo1<=0;hi1<=0;h2<=0;m2<=0;d2<=0;amplitude<=0;hit<=0;end
 else begin
 r<=rgb[23:16];g<=rgb[15:8];b<=rgb[7:0];c0<=models;
 m<=mx;d<=mx-mn;hn<=n[16:0];c1<=c0;
 lo0<=c1[62:54]*d;hi0<=c1[53:45]*d;
 lo1<=c1[126:118]*d;hi1<=c1[117:109]*d;
 h2<=hn;m2<=m;d2<=d;c2<=c1;
 amplitude[0]<=c1[63] && d!=0 && m>=c1[44:37] && d>=c1[36:29] && sat_ok(m,d,c1[28:27]);
 amplitude[1]<=c1[127] && d!=0 && m>=c1[108:101] && d>=c1[100:93] && sat_ok(m,d,c1[92:91]);
 hit[0]<=amplitude[0] && (c2[62:54]>c2[53:45]?(h2>=lo0 || h2<hi0):(h2>=lo0 && h2<hi0));
 hit[1]<=amplitude[1] && (c2[126:118]>c2[117:109]?(h2>=lo1 || h2<hi1):(h2>=lo1 && h2<hi1));
 end end
endmodule
`default_nettype wire
