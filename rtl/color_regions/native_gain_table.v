// Exact algebraic form of the supplied SC500GainTbl, including invalid levels.
module native_gain_table(input wire I_clk,I_rstn,input wire [6:0] I,output reg [15:0] O);
 wire [4:0] upper_step=I-7'd74;
 always @(posedge I_clk)begin
 if(I<32)O<={8'h03,3'b001,I[4:0]};
 else if(I<64)O<={8'h07,3'b001,I[4:0]};
 else if(I<74)O<={8'h0f,3'b001,I[4:0]};
 else if(I<=105)O<={8'h1f,3'b001,upper_step};
 else O<=0;
 end
endmodule
