// Asynchronous assertion, independently synchronized release in each clock domain.
`default_nettype none
module refined_reset_bridge(input wire clk,async_n,output wire reset_n);
 (* async_reg="true",syn_preserve=1 *) reg [1:0] release_pipe;
 always @(posedge clk or negedge async_n)if(!async_n)release_pipe<=0;else release_pipe<={release_pipe[0],1'b1};
 assign reset_n=release_pipe[1];
endmodule
`default_nettype wire
