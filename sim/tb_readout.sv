`timescale 1ns/1ps
module tb_readout;
    reg ddr_clk=0,px_clk=0,rst=0,vs=0,read_en=0;
    always #7.5 ddr_clk=~ddr_clk;
    always #6.667 px_clk=~px_clk;
    reg wr_busy=1,ready=1;
    reg [1:0] read_buffer=0;
    wire busy,ddr_read;
    wire [24:0] address;
    wire [23:0] pixel;
    reg [11:0] delayed_valid=0;
    reg [127:0] delayed_data[0:11];
    integer received_pixels=0;
    reg check_pixels=0;
    reg do_check;
    video_out dut(rst,ddr_clk,busy,wr_busy,read_buffer,ddr_read,address,ready,
                  delayed_valid[11],delayed_data[11],px_clk,vs,read_en,pixel);
    function [7:0] pattern(input integer index);
        pattern=((index*37) ^ (index>>8)) & 255;
    endfunction
    function [127:0] word_at(input integer index);
        for(integer b=0;b<16;b=b+1) word_at[127-b*8 -:8]=pattern(index*16+b);
    endfunction
    always @(posedge ddr_clk) begin
        delayed_valid<={delayed_valid[10:0],ddr_read};
        delayed_data[0]<=word_at(address/8);
        for(integer i=1;i<12;i=i+1) delayed_data[i]<=delayed_data[i-1];
    end
    always @(posedge px_clk) begin
        do_check=dut.S_video_rd_en_1d && check_pixels;
        #1;
        if(do_check) begin
            if(pixel !== {pattern(received_pixels*3),pattern(received_pixels*3+1),pattern(received_pixels*3+2)})
                $fatal(1,"RGB readout pixel %0d mismatch: %h",received_pixels,pixel);
            received_pixels=received_pixels+1;
        end
    end
    initial begin
        repeat(6) @(negedge px_clk); rst=1;
        vs=1; repeat(40) @(negedge ddr_clk); vs=0;
        wr_busy=0;
        repeat(700) @(negedge ddr_clk);
        @(negedge px_clk); check_pixels=1; read_en=1;
        repeat(1280) @(negedge px_clk);
        read_en=0; repeat(8) @(negedge px_clk); check_pixels=0;
        if(received_pixels!=1280) $fatal(1,"pixel count %0d",received_pixels);
        if(dut.U_w128_d512_fifo.underflow_attempts || dut.U_w128_d512_fifo.overflow_attempts)
            $fatal(1,"normal FIFO over/underflow");
        // Stop the mock DDR and start a new display frame; reads are not empty-gated.
        wr_busy=1; repeat(700) @(negedge ddr_clk);
        read_buffer=2; vs=1; repeat(40) @(negedge ddr_clk); vs=0;
        if(address!=14000000) $fatal(1,"read buffer base address");
        @(negedge px_clk); read_en=1;
        repeat(40) @(negedge px_clk); read_en=0;
        if(dut.U_w128_d512_fifo.underflow_attempts==0) $fatal(1,"underflow scenario missing");
        $display("PASS memory read control with ideal FIFO: 128->24 bit RGB ordering, 1280 pixels, frame buffer address");
        $display("KNOWN_LIMITATION memory: display reads when FIFO empty; reference does not blank/recover underflow");
        $finish;
    end
    initial begin #100000; $fatal(1,"timeout"); end
endmodule
