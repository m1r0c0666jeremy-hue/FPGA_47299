// Four tagged lines, four read replicas. Fixed 4x bilinear for original/gray only.
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
    input wire [1:0] I_zoom, I_mode,
    output wire O_vs, O_hs, O_de,
    output wire [23:0] O_rgb,
    output wire O_video_ok
);
    // 384-bit groups avoid unaligned RGB reads across 128-bit boundaries.
    // Four 128-group banks; groups 0..79 contain source pixels. All replicas
    // receive identical DDR writes, each supplies one independent pixel read.
    (* ram_style="block" *) reg [383:0] lines00 [0:511];
    (* ram_style="block" *) reg [383:0] lines10 [0:511];
    (* ram_style="block" *) reg [383:0] lines01 [0:511];
    (* ram_style="block" *) reg [383:0] lines11 [0:511];
    reg req_toggle, req_first;
    reg [1:0] req_bank;
    reg [9:0] req_y;
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
    reg [1:0] bank_d;
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
        if((state==SEND || state==DRAIN) && I_ddr_valid && part==2) begin
            lines00[{bank_d,group_index}] <= {assembly,I_ddr_data};
            lines10[{bank_d,group_index}] <= {assembly,I_ddr_data};
            lines01[{bank_d,group_index}] <= {assembly,I_ddr_data};
            lines11[{bank_d,group_index}] <= {assembly,I_ddr_data};
        end
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
    reg pending, request_stale;
    reg [3:0] ready;
    reg [9:0] tags [0:3];
    reg [9:0] prefetch_y, last_y, y0, y;
    reg [10:0] x0, x;
    reg [1:0] zoom, mode;
    reg first_line, frame_live, abort_frame;
    reg vs1, vs2, vs3;
    wire frame_start=vs2&&!vs3; // viewport metadata has already committed
    wire interpolate=(zoom==2 && !mode[0]);
    // Clamp quarter-pixel coordinates before splitting integer/fraction parts.
    // Source pixel i is anchored at screen pixel 4*i+2, matching the crosshair.
    wire [10:0] qx=(x<2)?11'd0:(x>1278)?11'd1276:x-11'd2;
    wire [9:0] qy=(y<2)?10'd0:(y>622)?10'd620:y-10'd2;
    wire [10:0] sx0=x0+(interpolate?{2'b0,qx[10:2]}:(x>>zoom));
    wire [9:0] sy0=y0+(interpolate?{2'b0,qy[9:2]}:(y>>zoom));
    wire [10:0] sx1=(interpolate && qx[10:2]<319)?sx0+11'd1:sx0;
    wire [9:0] sy1=(interpolate && qy[9:2]<155)?sy0+10'd1:sy0;
    wire [1:0] fx=interpolate?qx[1:0]:2'd0;
    wire [1:0] fy=interpolate?qy[1:0]:2'd0;
    wire [1:0] bank0=sy0[1:0], bank1=sy1[1:0];
    wire hit0=ready[bank0] && tags[bank0]==sy0;
    wire hit1=ready[bank1] && tags[bank1]==sy1;
    wire good=frame_live && !abort_frame && hit0 && hit1;
    // Release only obsolete source rows; one delayed bank mask protects the
    // registered RAM address until its synchronous read has completed.
    reg [3:0] read_hold;
    integer k;
    always @(posedge I_pixel_clk or negedge pixel_rst_n) begin
        if(!pixel_rst_n) begin
            ack1<=0; ack2<=0; pending<=0; request_stale<=1;
            ready<=0; req_toggle<=0; req_bank<=0; req_y<=0; req_first<=0;
            prefetch_y<=48; last_y<=671; first_line<=1;
            frame_live<=0; abort_frame<=1; vs1<=0; vs2<=0; vs3<=0;
            x<=0; y<=0; x0<=0; y0<=48; zoom<=0; mode<=0; read_hold<=0;
            for(k=0;k<4;k=k+1) tags[k]<=0;
        end else begin
            ack1<=ack_toggle; ack2<=ack1; vs1<=I_vs; vs2<=vs1; vs3<=vs2;
            read_hold<=(I_de && y<624 && good)?((4'b1<<bank0)|(4'b1<<bank1)):4'b0;
            if(I_de) begin
                if(x==1279) begin x<=0; y<=y+1'b1; end else x<=x+1'b1;
                if(y<624 && !good) abort_frame<=1;
            end
            for(k=0;k<4;k=k+1)
                if(ready[k] && tags[k]<sy0 && !read_hold[k]) ready[k]<=0;
            if(pending && ack2==req_toggle) begin
                pending<=0;
                if(!request_stale && !abort_frame) begin
                    ready[req_bank]<=1; tags[req_bank]<=req_y;
                end
            end
            if(frame_live && !abort_frame && !pending && prefetch_y<=last_y &&
               !ready[prefetch_y[1:0]] && !read_hold[prefetch_y[1:0]]) begin
                req_bank<=prefetch_y[1:0]; req_y<=prefetch_y;
                req_first<=first_line; request_stale<=0;
                req_toggle<=~req_toggle; pending<=1;
                first_line<=0; prefetch_y<=prefetch_y+1'b1;
            end
            if(frame_start) begin
                x<=0; y<=0; x0<=I_x0; y0<=I_y0; zoom<=I_zoom; mode<=I_mode;
                ready<=0; frame_live<=1; abort_frame<=0; request_stale<=1;
                prefetch_y<=I_y0; last_y<=I_y0+(624>>I_zoom)-1; first_line<=1;
            end
        end
    end
    // Stage 1: registered RAM addresses and metadata.
    reg [8:0] addr00,addr10,addr01,addr11;
    reg [3:0] off0_s1,off1_s1,off0_s2,off1_s2;
    reg [1:0] fx_s1,fy_s1,fx_s2,fy_s2,fx_s3,fy_s3;
    reg [2:0] vs_pipe,hs_pipe,de_pipe,good_pipe,ok_pipe;
    reg [383:0] q00,q10,q01,q11;
    reg [23:0] p00,p10,p01,p11;
    // Stage 2: RAM data. Deliberately no reset on the RAM output registers.
    always @(posedge I_pixel_clk) begin
        q00<=lines00[addr00]; q10<=lines10[addr10];
        q01<=lines01[addr01]; q11<=lines11[addr11];
    end
    always @(posedge I_pixel_clk or negedge pixel_rst_n) begin
        if(!pixel_rst_n) begin
            addr00<=0;addr10<=0;addr01<=0;addr11<=0;
            off0_s1<=0;off1_s1<=0;off0_s2<=0;off1_s2<=0;
            fx_s1<=0;fy_s1<=0;fx_s2<=0;fy_s2<=0;fx_s3<=0;fy_s3<=0;
            vs_pipe<=0;hs_pipe<=0;de_pipe<=0;good_pipe<=0;ok_pipe<=0;
            p00<=0;p10<=0;p01<=0;p11<=0;
        end else begin
            addr00<={bank0,sx0[10:4]};addr10<={bank0,sx1[10:4]};
            addr01<={bank1,sx0[10:4]};addr11<={bank1,sx1[10:4]};
            off0_s1<=sx0[3:0];off1_s1<=sx1[3:0];
            off0_s2<=off0_s1;off1_s2<=off1_s1;
            fx_s1<=fx;fy_s1<=fy;fx_s2<=fx_s1;fy_s2<=fy_s1;fx_s3<=fx_s2;fy_s3<=fy_s2;
            vs_pipe<={vs_pipe[1:0],I_vs};hs_pipe<={hs_pipe[1:0],I_hs};de_pipe<={de_pipe[1:0],I_de};
            good_pipe<={good_pipe[1:0],good && y<624};
            ok_pipe<={ok_pipe[1:0],frame_live && !abort_frame && (!I_de || y>=624 || good)};
            // Stage 3: select adjacent RGB pixels, including group crossings.
            p00<=q00 >> ((15-off0_s2)*24);p10<=q10 >> ((15-off1_s2)*24);
            p01<=q01 >> ((15-off0_s2)*24);p11<=q11 >> ((15-off1_s2)*24);
        end
    end
    // Stages 4/5: exact horizontal sum then vertical sum and one rounding.
    bilinear_rgb u_bilinear(
        .I_clk(I_pixel_clk),.I_rst_n(pixel_rst_n),
        .I_p00(p00),.I_p10(p10),.I_p01(p01),.I_p11(p11),.I_fx(fx_s3),.I_fy(fy_s3),
        .I_vs(vs_pipe[2]),.I_hs(hs_pipe[2]),.I_de(de_pipe[2]),
        .I_good(good_pipe[2]),.I_ok(ok_pipe[2]),
        .O_rgb(O_rgb),.O_vs(O_vs),.O_hs(O_hs),.O_de(O_de),.O_ok(O_video_ok));
endmodule
`default_nettype wire
