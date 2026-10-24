// Only for independent, persistent status bits. Never use for coherent data.
`default_nettype none
module status_sync (
    input wire I_clk, input wire I_rst_n,
    input wire [3:0] I_status_async,
    output reg [3:0] O_status
);
    reg [3:0] stage1;
    always @(posedge I_clk or negedge I_rst_n) begin
        if (!I_rst_n) begin
            stage1 <= 4'b0000;
            O_status <= 4'b0000;
        end else begin
            stage1 <= I_status_async;
            O_status <= stage1;
        end
    end
endmodule
`default_nettype wire
