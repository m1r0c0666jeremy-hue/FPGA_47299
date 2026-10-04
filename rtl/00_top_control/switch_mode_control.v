// SW1 is the high mode bit, SW2 the low bit. Both are active-high levels.
// Synchronize first, then accept a whole two-bit word only after 20 ms stable.
`default_nettype none
module switch_mode_control #(
    parameter integer STABLE_CYCLES = 1500000 // 75 MHz * 20 ms
)(
    input wire I_clk, input wire I_rst_n,
    input wire [1:0] I_switch,
    output reg [1:0] O_mode_pending
);
    reg [1:0] sync1, sync2, candidate;
    reg [20:0] stable_count;
    always @(posedge I_clk or negedge I_rst_n) begin
        if (!I_rst_n) begin
            sync1 <= 0; sync2 <= 0; candidate <= 0;
            stable_count <= 0; O_mode_pending <= 0;
        end else begin
            sync1 <= I_switch;
            sync2 <= sync1;
            if (sync2 != candidate) begin
                candidate <= sync2;
                stable_count <= 0;
            end else if (stable_count < STABLE_CYCLES-1) begin
                stable_count <= stable_count + 1'b1;
            end else begin
                O_mode_pending <= candidate;
            end
        end
    end
endmodule
`default_nettype wire
