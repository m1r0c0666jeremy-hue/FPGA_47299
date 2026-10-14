// Source-space supported mask is scaled alongside RGB; never reclassify zoom.
`default_nettype none
module stable_preprocess(input wire I_clk,I_rst_n,input wire [1:0] I_mode,input wire I_pair,
 input wire I_vs,I_hs,I_de,input wire [23:0] I_rgb,input wire [1:0] I_mask,
 output reg O_vs,O_hs,O_de,output reg [23:0] O_rgb,output reg [1:0] O_mode);
 wire [9:0] gs={2'b0,I_rgb[23:16]}+{1'b0,I_rgb[15:8],1'b0}+{2'b0,I_rgb[7:0]}+2;
 wire [7:0] gray=gs[9:2];
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin O_vs<=0;O_hs<=0;O_de<=0;O_rgb<=0;O_mode<=0;end
 else begin O_vs<=I_vs;O_hs<=I_hs;O_de<=I_de;O_mode<=I_mode;
 case(I_mode)
 0:O_rgb<=I_rgb;
 1:O_rgb<=I_mask[0]?(I_pair?24'hffff40:24'hff6060):I_mask[1]?(I_pair?24'he080ff:24'h6090ff):{2'd0,gray[7:2],2'd0,gray[7:2],2'd0,gray[7:2]};
 2:O_rgb<={gray,gray,gray};3:O_rgb<=I_mask!=0?24'hffffff:0;
 endcase end end
endmodule
`default_nettype wire
