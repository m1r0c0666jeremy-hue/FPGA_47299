// Two complete lines in dual-clock block RAM. One mailbox transaction per line.
// DDR unit: 128 bits at address increments of 8; 3 words = 16 RGB888 pixels.
`default_nettype none
module scaling_line_reader (
    input wire I_rst_n,
    input wire I_ddr_clk, I_write_busy, I_write_en,
    input wire [1:0] I_read_buffer,
    input wire I_ddr_ready, I_ddr_valid,
    input wire [127:0] I_ddr_data,
    output wire O_read_busy, O_read_en,
    output wire [24:0] O_read_addr,
    input wire I_pixel_clk, I_vs, I_hs, I_de,
    input wire [10:0] I_x0,
    input wire [9:0] I_y0,
    input wire [1:0] I_zoom,
    output reg O_vs, O_hs, O_de,
    output reg [23:0] O_rgb,
    output reg O_video_ok
);
    // 384-bit groups avoid unaligned RGB reads across 128-bit boundaries.
    // Address bit 7 selects line bank; each bank uses groups 0..79.
    (* ram_style="block" *) reg [383:0] lines [0:255];
    reg [383:0] ram_q;
    reg req_toggle, req_bank, req_first;
    reg [9:0] req_y;
    reg [7:0] req_epoch;
    reg ack_toggle;
    (* async_reg="true", syn_preserve=1 *) reg req1, req2;
    (* async_reg="true", syn_preserve=1 *) reg [1:0] ddr_reset_bridge, pixel_reset_bridge;
    wire ddr_rst_n=ddr_reset_bridge[1];
    wire pixel_rst_n=pixel_reset_bridge[1];
    always @(posedge I_ddr_clk or negedge I_rst_n)
        if(!I_rst_n) ddr_reset_bridge<=0; else ddr_reset_bridge<={ddr_reset_bridge[0],1'b1};
    always @(posedge I_pixel_clk or negedge I_rst_n)
        if(!I_rst_n) pixel_reset_bridge<=0; else pixel_reset_bridge<={pixel_reset_bridge[0],1'b1};
    reg [1:0] state;
    localparam IDLE=0, WAIT_BUS=1, SEND=2, DRAIN=3;
    reg bank_d;
    reg [24:0] frame_base, line_base;
    reg [7:0] sent, received;
    reg [1:0] part;
    reg [6:0] group_index;
    reg [255:0] assembly;
    function [24:0] base_for;
        input [1:0] p;
        case(p) 0:base_for=0; 1:base_for=7000000; 2:base_for=14000000; 3:base_for=21000000; endcase
    endfunction
    // Reserve the next burst as soon as write ownership drops, including its
    // registered final beat. WAIT_BUS still waits for I_write_en to clear.
    // Otherwise a continuously nonempty camera FIFO can reclaim every gap.
    assign O_read_busy=(state==SEND) || ((state==WAIT_BUS) && !I_write_busy);
    assign O_read_en=(state==SEND) && I_ddr_ready;
    assign O_read_addr=line_base+{14'd0,sent,3'b000};
    // RAM write port deliberately has no reset; ready/epoch hides stale contents.
    always @(posedge I_ddr_clk) begin
        if((state==SEND || state==DRAIN) && I_ddr_valid && part==2)
            lines[{bank_d,group_index}] <= {assembly,I_ddr_data};
    end
    always @(posedge I_ddr_clk or negedge ddr_rst_n) begin
        if(!ddr_rst_n) begin
            req1<=0; req2<=0; ack_toggle<=0; state<=IDLE; bank_d<=0;
            frame_base<=0; line_base<=0; sent<=0; received<=0;
            part<=0; group_index<=0; assembly<=0;
        end else begin
            req1<=req_toggle; req2<=req1;
            case(state)
            IDLE: if(req2!=ack_toggle) begin
                bank_d<=req_bank;
                if(req_first) frame_base<=base_for(I_read_buffer);
                line_base<=(req_first?base_for(I_read_buffer):frame_base)+req_y*25'd1920;
                sent<=0; received<=0; part<=0; group_index<=0; state<=WAIT_BUS;
            end
            WAIT_BUS: if(!I_write_busy && !I_write_en) state<=SEND;
            SEND: if(O_read_en) begin
                if(sent==239) state<=DRAIN;
                else sent<=sent+1'b1;
            end
            endcase
            if((state==SEND || state==DRAIN) && I_ddr_valid) begin
                received<=received+1'b1;
                if(part==0) begin assembly[255:128]<=I_ddr_data; part<=1; end
                else if(part==1) begin assembly[127:0]<=I_ddr_data; part<=2; end
                else begin part<=0; group_index<=group_index+1'b1; end
                if(received==239) begin ack_toggle<=req2; state<=IDLE; end
            end
        end
    end
    (* async_reg="true", syn_preserve=1 *) reg ack1, ack2;
    reg pending;
    reg [1:0] ready;
    reg [9:0] tag0, tag1, prefetch_y, last_y, y0;
    reg [10:0] x0, x;
    reg [9:0] y;
    reg [1:0] zoom;
    reg [7:0] epoch;
    reg first_line, frame_live, abort_frame;
    reg vs1, vs2, vs3;
    wire frame_start=vs2&&!vs3; // viewport metadata has already committed.
    wire [10:0] sx=x0+(x>>zoom);
    wire [9:0] sy=y0+(y>>zoom);
    wire hit0=ready[0] && tag0==sy;
    wire hit1=ready[1] && tag1==sy;
    wire bank=hit1 && !hit0;
    wire good=frame_live && !abort_frame && (hit0||hit1);
    wire [1:0] row_mask=(1<<zoom)-1;
    reg [3:0] offset_d;
    reg vs_d,hs_d,de_d,good_d;
    always @(posedge I_pixel_clk) begin
        ram_q<=lines[{bank,sx[10:4]}];
    end
    always @(posedge I_pixel_clk or negedge pixel_rst_n) begin
        if(!pixel_rst_n) begin
            ack1<=0; ack2<=0; pending<=0; ready<=0; req_toggle<=0; req_bank<=0;
            req_y<=0; req_first<=0; req_epoch<=0; epoch<=0;
            tag0<=0; tag1<=0; prefetch_y<=48; last_y<=671; first_line<=1;
            frame_live<=0; abort_frame<=1; vs1<=0; vs2<=0; vs3<=0;
            x<=0; y<=0; x0<=0; y0<=48; zoom<=0;
            offset_d<=0; vs_d<=0; hs_d<=0; de_d<=0; good_d<=0;
            O_vs<=0; O_hs<=0; O_de<=0; O_rgb<=0; O_video_ok<=0;
        end else begin
            ack1<=ack_toggle; ack2<=ack1; vs1<=I_vs; vs2<=vs1; vs3<=vs2;
            vs_d<=I_vs; hs_d<=I_hs; de_d<=I_de; offset_d<=sx[3:0];
            good_d<=good && y<624;
            O_vs<=vs_d; O_hs<=hs_d; O_de<=de_d;
            O_rgb<=(de_d && good_d)?(ram_q >> ((15-offset_d)*24)):24'd0;
            O_video_ok<=frame_live && !abort_frame;
            if(I_de) begin
                if(x==1279) begin x<=0; y<=y+1'b1; end else x<=x+1'b1;
                if(y<624 && !good) abort_frame<=1;
                if(x==1279 && y<624 && (y[1:0]&row_mask)==row_mask && good)
                    ready[bank]<=0;
            end
            if(pending && ack2==req_toggle) begin
                pending<=0;
                if(req_epoch==epoch && !abort_frame) begin
                    ready[req_bank]<=1;
                    if(req_bank) tag1<=req_y; else tag0<=req_y;
                end
            end
            if(frame_live && !abort_frame && !pending && prefetch_y<=last_y && ready!=3) begin
                req_bank<=!ready[0]?0:1; req_y<=prefetch_y;
                req_first<=first_line; req_epoch<=epoch;
                req_toggle<=~req_toggle; pending<=1;
                first_line<=0; prefetch_y<=prefetch_y+1'b1;
            end
            if(frame_start) begin
                x<=0; y<=0; x0<=I_x0; y0<=I_y0; zoom<=I_zoom;
                epoch<=epoch+1'b1; ready<=0; frame_live<=1; abort_frame<=0;
                prefetch_y<=I_y0; last_y<=I_y0+(624>>I_zoom)-1;
                first_line<=1;
            end
        end
    end
endmodule
`default_nettype wire
