`default_nettype none
module regions_preprocess(
 input wire I_clk,I_rst_n,input wire [1:0] I_mode,input wire I_pair,
 input wire I_vs,I_hs,I_de,input wire [23:0] I_rgb,
 output reg O_vs,O_hs,O_de,output reg [23:0] O_rgb,output reg [1:0] O_mode
);
 wire [3:0] hit;wire [1:0] quality;
 regions_color_lane classify(I_clk,I_rgb,hit,quality);
 reg [23:0] rgb[0:3];reg [7:0] gray[0:3];reg [1:0] mode[0:3];reg [3:0] vs,hs,de,pair;
 wire [9:0] gray_sum={2'b0,I_rgb[23:16]}+{1'b0,I_rgb[15:8],1'b0}+{2'b0,I_rgb[7:0]}+10'd2;
 wire a=pair[3]?hit[2]:hit[0],b=pair[3]?hit[3]:hit[1];integer i;
 always @(posedge I_clk or negedge I_rst_n)begin
   if(!I_rst_n)begin
     vs<=0;hs<=0;de<=0;pair<=0;O_vs<=0;O_hs<=0;O_de<=0;O_rgb<=0;O_mode<=0;
     for(i=0;i<4;i=i+1)begin rgb[i]<=0;gray[i]<=0;mode[i]<=0;end
   end else begin
     vs<={vs[2:0],I_vs};hs<={hs[2:0],I_hs};de<={de[2:0],I_de};pair<={pair[2:0],I_pair};
     rgb[0]<=I_rgb;gray[0]<=gray_sum[9:2];mode[0]<=I_mode;
     for(i=1;i<4;i=i+1)begin rgb[i]<=rgb[i-1];gray[i]<=gray[i-1];mode[i]<=mode[i-1];end
     O_vs<=vs[3];O_hs<=hs[3];O_de<=de[3];O_mode<=mode[3];
     case(mode[3])
       0:O_rgb<=rgb[3];
       1:O_rgb<=a?(pair[3]?24'hFFFF40:24'hFF6060):b?(pair[3]?24'hE080FF:24'h6090FF):{2'b0,gray[3][7:2],2'b0,gray[3][7:2],2'b0,gray[3][7:2]};
       2:O_rgb<={gray[3],gray[3],gray[3]};
       3:O_rgb<=a||b?24'hFFFFFF:0;
     endcase
   end
 end
endmodule
`default_nettype wire
