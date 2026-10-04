// RGB888 display-stream processor, one pixel per valid clock, no backpressure.
// Modes: 00 original, 01 Sobel magnitude, 10 gray, 11 binary.
// Gray = round((R + 2*G + B)/4); binary threshold is inclusive.
// Sobel uses the causal 3x3 window ending at (x,y). Top two rows and left
// two columns are black in edge mode. Its window center is (x-1,y-1).
// Five register stages; RGB and HS/VS/DE receive identical pipeline delay.
`default_nettype none
module image_preprocess #(
    parameter integer WIDTH = 1280,
    parameter [7:0] BINARY_THRESHOLD = 8'd128
)(
    input wire I_clk, input wire I_rst_n,
    input wire [1:0] I_mode_pending,
    input wire I_vs, input wire I_hs, input wire I_de,
    input wire [23:0] I_rgb,
    output reg O_vs, output reg O_hs, output reg O_de,
    output reg [23:0] O_rgb,
    output wire [1:0] O_mode_active
);
    reg vs_d;
    reg [1:0] mode_active;
    reg [11:0] x, y;
    reg [11:0] x0;
    reg [23:0] rgb_pipe [0:3];
    reg [7:0] gray_pipe [0:3];
    reg [1:0] mode_pipe [0:3];
    reg [3:0] de_pipe, hs_pipe, vs_pipe, window_pipe;
    wire [9:0] gray_sum = {2'b0,I_rgb[23:16]} +
                         {1'b0,I_rgb[15:8],1'b0} + {2'b0,I_rgb[7:0]} + 10'd2;

    // Read-before-write synchronous line stores. Never reset the RAM array:
    // the window mask hides old/uninitialized rows until two new rows arrived.
    reg [7:0] previous_line [0:WIDTH-1];
    reg [7:0] previous_two_lines [0:WIDTH-1];
    reg [7:0] middle, top;
    always @(posedge I_clk) begin
        if (de_pipe[0]) begin
            middle <= previous_line[x0];
            top <= previous_two_lines[x0];
            previous_two_lines[x0] <= previous_line[x0];
            previous_line[x0] <= gray_pipe[0];
        end
    end

    reg [7:0] top_left2, top_left1, mid_left2, mid_left1;
    reg [7:0] bot_left2, bot_left1;
    reg [9:0] gx_pos, gx_neg, gy_pos, gy_neg;
    wire [9:0] abs_gx = (gx_pos >= gx_neg) ? gx_pos-gx_neg : gx_neg-gx_pos;
    wire [9:0] abs_gy = (gy_pos >= gy_neg) ? gy_pos-gy_neg : gy_neg-gy_pos;
    reg [10:0] magnitude;
    wire [7:0] edge_value = (magnitude > 11'd255) ? 8'hff : magnitude[7:0];
    integer i;
    assign O_mode_active = mode_active;
    always @(posedge I_clk or negedge I_rst_n) begin
        if (!I_rst_n) begin
            vs_d <= 0; mode_active <= 0; x <= 0; y <= 0; x0 <= 0;
            de_pipe <= 0; hs_pipe <= 0; vs_pipe <= 0; window_pipe <= 0;
            O_vs <= 0; O_hs <= 0; O_de <= 0; O_rgb <= 0;
            top_left2 <= 0; top_left1 <= 0; mid_left2 <= 0; mid_left1 <= 0;
            bot_left2 <= 0; bot_left1 <= 0;
            gx_pos <= 0; gx_neg <= 0; gy_pos <= 0; gy_neg <= 0; magnitude <= 0;
            for (i=0; i<4; i=i+1) begin
                rgb_pipe[i] <= 0; gray_pipe[i] <= 0; mode_pipe[i] <= 0;
            end
        end else begin
            vs_d <= I_vs;
            if (I_vs && !vs_d) begin
                mode_active <= I_mode_pending;
                x <= 0; y <= 0;
            end else if (I_de) begin
                if (x == WIDTH-1) begin x <= 0; y <= y + 1'b1; end
                else x <= x + 1'b1;
            end
            x0 <= x;
            rgb_pipe[0] <= I_rgb;
            gray_pipe[0] <= gray_sum[9:2];
            mode_pipe[0] <= mode_active;
            de_pipe <= {de_pipe[2:0],I_de};
            hs_pipe <= {hs_pipe[2:0],I_hs};
            vs_pipe <= {vs_pipe[2:0],I_vs};
            window_pipe <= {window_pipe[2:0],(x>=2 && y>=2)};
            for (i=1; i<4; i=i+1) begin
                rgb_pipe[i] <= rgb_pipe[i-1];
                gray_pipe[i] <= gray_pipe[i-1];
                mode_pipe[i] <= mode_pipe[i-1];
            end
            if (de_pipe[1]) begin
                top_left2 <= top_left1; top_left1 <= top;
                mid_left2 <= mid_left1; mid_left1 <= middle;
                bot_left2 <= bot_left1; bot_left1 <= gray_pipe[1];
                gx_pos <= {2'b0,top} + {1'b0,middle,1'b0} + {2'b0,gray_pipe[1]};
                gx_neg <= {2'b0,top_left2} + {1'b0,mid_left2,1'b0} + {2'b0,bot_left2};
                gy_pos <= {2'b0,bot_left2} + {1'b0,bot_left1,1'b0} + {2'b0,gray_pipe[1]};
                gy_neg <= {2'b0,top_left2} + {1'b0,top_left1,1'b0} + {2'b0,top};
            end else begin
                top_left2 <= 0; top_left1 <= 0; mid_left2 <= 0; mid_left1 <= 0;
                bot_left2 <= 0; bot_left1 <= 0;
            end
            magnitude <= {1'b0,abs_gx} + {1'b0,abs_gy};
            O_vs <= vs_pipe[3]; O_hs <= hs_pipe[3]; O_de <= de_pipe[3];
            if (!de_pipe[3]) O_rgb <= 0;
            else case (mode_pipe[3])
                2'b00: O_rgb <= rgb_pipe[3];
                2'b01: O_rgb <= window_pipe[3] ? {3{edge_value}} : 24'd0;
                2'b10: O_rgb <= {3{gray_pipe[3]}};
                2'b11: O_rgb <= (gray_pipe[3] >= BINARY_THRESHOLD) ? 24'hffffff : 24'd0;
            endcase
        end
    end
endmodule
`default_nettype wire
