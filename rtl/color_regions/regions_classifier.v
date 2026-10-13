// Generated for the functional entry only. No legacy classifier is instantiated.
`default_nettype none
module regions_color_lane(input wire clk,input wire [23:0] rgb,
 output reg [3:0] hit,output reg [1:0] quality);
 reg [7:0] r1,g1,b1,m1,lo1;
 reg [7:0] m2,d2;
 reg [11:0] n2;
 reg [1:0] q2,q3;
 reg [3:0] hit3;
 wire [7:0] mx=rgb[23:16]>=rgb[15:8]?(rgb[23:16]>=rgb[7:0]?rgb[23:16]:rgb[7:0]):
              (rgb[15:8]>=rgb[7:0]?rgb[15:8]:rgb[7:0]);
 wire [7:0] mn=rgb[23:16]<=rgb[15:8]?(rgb[23:16]<=rgb[7:0]?rgb[23:16]:rgb[7:0]):
              (rgb[15:8]<=rgb[7:0]?rgb[15:8]:rgb[7:0]);
 wire [11:0] delta={4'd0,m1}-{4'd0,lo1};
 wire [12:0] hue4={n2,1'b0}<<1;
 wire [12:0] dd={5'd0,d2};
 wire ok=m2>=24 && d2>=8 && ((dd<<4)>=({5'd0,m2}<<1)+{5'd0,m2});
 wire [3:0] hits={ok && hue4>=(dd+(dd<<4)) && hue4<((dd<<1)+(dd<<2)+(dd<<4)),
                  ok && hue4>=(dd+(dd<<1)) && hue4<(dd+(dd<<2)),
                  ok && hue4>=(dd+(dd<<2)+(dd<<3)) && hue4<(dd+(dd<<4)),
                  ok && (hue4<((dd<<1)) || hue4>=(dd+(dd<<1)+(dd<<2)+(dd<<4)))};
 wire unique_hit=(hits==1 || hits==2 || hits==4 || hits==8);
 always @(posedge clk) begin
   r1<=rgb[23:16];g1<=rgb[15:8];b1<=rgb[7:0];m1<=mx;lo1<=mn;
   m2<=m1;d2<=delta[7:0];
   if(m1==r1) begin
     if(g1>=b1)n2<={4'd0,g1}-{4'd0,b1};
     else n2<=(delta<<2)+(delta<<1)+{4'd0,g1}-{4'd0,b1};
   end else if(m1==g1)n2<=(delta<<1)+{4'd0,b1}-{4'd0,r1};
   else n2<=(delta<<2)+{4'd0,r1}-{4'd0,g1};
   q2<={1'b0,((delta<<2)>={4'd0,m1})}+{1'b0,((delta<<1)>={4'd0,m1})}+
        {1'b0,((delta<<2)>=({4'd0,m1}<<1)+{4'd0,m1})};
   hit3<=unique_hit?hits:4'd0;q3<=unique_hit?q2:2'd0;
   hit<=hit3;quality<=q3;
 end
endmodule
module regions_color4(input wire clk,rst_n,valid,input wire [95:0] rgb,
 output wire valid_out,output wire [15:0] hit,output wire [7:0] quality);
 reg [3:0] vp;
 always @(posedge clk or negedge rst_n)if(!rst_n)vp<=0;else vp<={vp[2:0],valid};
 assign valid_out=vp[3];
 genvar p;
 generate for(p=0;p<4;p=p+1)begin:lane
   regions_color_lane u(.clk(clk),.rgb(rgb[95-24*p-:24]),.hit(hit[4*p+:4]),.quality(quality[2*p+:2]));
 end endgenerate
endmodule
`default_nettype wire
