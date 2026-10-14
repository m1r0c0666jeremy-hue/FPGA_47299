// 96-to-128 stream packer. Gaps preserve byte phase; SOF discards partial words.
`default_nettype none
module stable_packer(input wire I_clk,I_rst_n,I_96b_frame_start,I_96b_valid,
 input wire [95:0] I_96b_data,output reg O_128b_frame_start,O_128b_valid,
 output reg [127:0] O_128b_data);
 reg [95:0] remainder;reg [6:0] bits;
 reg [191:0] joined;reg [7:0] total;
 always @*begin
 total=(I_96b_frame_start?0:bits)+96;
 joined=({96'd0,(I_96b_frame_start?96'd0:remainder)}<<96)|I_96b_data;
 end
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin remainder<=0;bits<=0;O_128b_frame_start<=0;O_128b_valid<=0;O_128b_data<=0;end
 else begin O_128b_frame_start<=I_96b_frame_start;O_128b_valid<=0;
 if(I_96b_frame_start)begin bits<=0;remainder<=0;end
 if(I_96b_valid)begin
 if(total>=128)begin O_128b_valid<=1;O_128b_data<=joined>>(total-128);bits<=total-128;
 remainder<=joined & ((192'd1<<(total-128))-1'b1);end
 else begin bits<=total;remainder<=I_96b_data;end
 end end end
endmodule
`default_nettype wire
