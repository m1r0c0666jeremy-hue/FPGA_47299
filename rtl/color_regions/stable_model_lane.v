// Runtime colour model: valid63, hue-low62:54, hue-high53:45,
// value-min44:37, chroma-min36:29, saturation code28:27 (3,4,6,8 /16).
// Wrapped intervals have low > high. Four clock pipeline, no pixel divider.
`default_nettype none
module stable_model_lane(input wire clk,rst_n,input wire [23:0] rgb,
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
 // Compute channel selection/chroma on the input-register stage.
 // Keep the original four-clock hit/model alignment; no extra pixel delay.
 reg [7:0] maximum1,minimum1,chroma1;
 reg signed [8:0] difference1;
 reg [1:0] sector1;
 reg [7:0] raw_maximum,raw_minimum,raw_a,raw_b;
 reg signed [8:0] raw_difference;
 reg [1:0] raw_sector;
 reg [10:0] hue_offset,hue_units;
 always @*begin
 raw_maximum=rgb[23:16]>rgb[15:8]?(rgb[23:16]>rgb[7:0]?rgb[23:16]:rgb[7:0]):(rgb[15:8]>rgb[7:0]?rgb[15:8]:rgb[7:0]);
 raw_minimum=rgb[23:16]<rgb[15:8]?(rgb[23:16]<rgb[7:0]?rgb[23:16]:rgb[7:0]):(rgb[15:8]<rgb[7:0]?rgb[15:8]:rgb[7:0]);
 if(raw_maximum==rgb[23:16])begin raw_a=rgb[15:8];raw_b=rgb[7:0];raw_sector=rgb[15:8]<rgb[7:0]?3:0;end
 else if(raw_maximum==rgb[15:8])begin raw_a=rgb[7:0];raw_b=rgb[23:16];raw_sector=1;end
 else begin raw_a=rgb[23:16];raw_b=rgb[15:8];raw_sector=2;end
 raw_difference=$signed({1'b0,raw_a})-$signed({1'b0,raw_b});
 mx=maximum1;mn=minimum1;
 case(sector1)
 0:hue_offset=0;
 1:hue_offset={3'd0,chroma1}<<1;
 2:hue_offset={3'd0,chroma1}<<2;
 3:hue_offset=({3'd0,chroma1}<<2)+({3'd0,chroma1}<<1);
 endcase
 hue_units=hue_offset+{{2{difference1[8]}},difference1};
 n=({7'd0,hue_units}<<6)-({7'd0,hue_units}<<2);
 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin r<=0;g<=0;b<=0;maximum1<=0;minimum1<=0;chroma1<=0;difference1<=0;sector1<=0;m<=0;d<=0;hn<=0;c0<=0;c1<=0;c2<=0;
 lo0<=0;hi0<=0;lo1<=0;hi1<=0;h2<=0;m2<=0;d2<=0;amplitude<=0;hit<=0;end
 else begin
 r<=rgb[23:16];g<=rgb[15:8];b<=rgb[7:0];c0<=models;
 maximum1<=raw_maximum;minimum1<=raw_minimum;chroma1<=raw_maximum-raw_minimum;difference1<=raw_difference;sector1<=raw_sector;
 m<=mx;d<=chroma1;hn<=n[16:0];c1<=c0;
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
