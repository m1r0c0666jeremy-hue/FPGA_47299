// Four independent sticky bring-up flags from the supplied Lab1 diagnostics.
// These indicate past activity, NOT current camera health or measured frame rate.
`default_nettype none
module camera_status (
    input wire I_cfg_clk, input wire I_rx_clk, input wire I_rst_n,
    input wire I_cfg_done, input wire I_hs_valid,
    input wire I_csi_valid, input wire I_frame_start,
    output wire [3:0] O_status_async
);
    reg cfg_seen, hs_seen, frame_once, frames_seen, width_seen;
    reg hs_valid_d;
    reg [10:0] payload_words;
    always @(posedge I_cfg_clk or negedge I_rst_n) begin
        if (!I_rst_n) cfg_seen <= 1'b0;
        else if (I_cfg_done) cfg_seen <= 1'b1;
    end
    always @(posedge I_rx_clk or negedge I_rst_n) begin
        if (!I_rst_n) begin
            hs_seen <= 1'b0;
            frame_once <= 1'b0;
            frames_seen <= 1'b0;
            width_seen <= 1'b0;
            hs_valid_d <= 1'b0;
            payload_words <= 11'd0;
        end else begin
            hs_valid_d <= I_hs_valid;
            if (I_hs_valid) hs_seen <= 1'b1;
            if (!hs_valid_d && I_hs_valid) payload_words <= 11'd0;
            else if (I_csi_valid) payload_words <= payload_words + 11'd1;
            if (hs_valid_d && !I_hs_valid && payload_words == 11'd400)
                width_seen <= 1'b1;
            if (I_frame_start) begin
                frame_once <= 1'b1;
                if (frame_once) frames_seen <= 1'b1;
            end
        end
    end
    assign O_status_async = {width_seen, frames_seen, hs_seen, cfg_seen};
endmodule
`default_nettype wire
