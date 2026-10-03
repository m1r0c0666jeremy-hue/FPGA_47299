`timescale 1ns/1ps
module tb_memory;
    reg cam_clk=0,ddr_clk=0,rst=0,fs=0,valid=0;
    always #8.333 cam_clk=~cam_clk;
    always #7.5 ddr_clk=~ddr_clk;
    reg [127:0] data=0;
    reg rd_busy=0,ready=1,pause=0,error=0;
    wire wr_busy,wr_en;
    wire [1:0] read_buffer;
    wire [24:0] address;
    wire [127:0] wr_data;
    integer writes=0,ddr_cycle=0;
    reg check_writes=0;
    video_in dut(rst,cam_clk,fs,valid,data,error,ddr_clk,pause,rd_busy,
                 wr_busy,read_buffer,wr_en,address,wr_data,ready);
    always @(negedge ddr_clk) begin
        ddr_cycle=ddr_cycle+1;
        ready=(ddr_cycle%7!=0); // DDR backpressure must preserve burst contents.
    end
    always @(posedge ddr_clk) begin
        if(check_writes && wr_en) begin
            if(address!==writes*8 || wr_data!==writes)
                $fatal(1,"write data/address order: n=%0d addr=%0d data=%0d",writes,address,wr_data);
            writes=writes+1;
        end
    end
    task frame_start;
        @(negedge cam_clk); fs=1;
        @(negedge cam_clk); fs=0;
        repeat(30) @(negedge cam_clk);
    endtask
    initial begin
        repeat(6) @(negedge cam_clk); rst=1;
        frame_start();
        if(read_buffer!==2) $fatal(1,"first buffer selection");
        check_writes=1;
        for(integer i=0;i<720;i=i+1) begin
            valid=1; data=i; @(negedge cam_clk);
        end
        valid=0;
        repeat(1500) @(negedge ddr_clk);
        if(writes!=720) $fatal(1,"burst lost: %0d",writes);
        check_writes=0;
        if(dut.U_w128_d512_fifo.overflow_attempts || dut.U_w128_d512_fifo.underflow_attempts)
            $fatal(1,"normal FIFO over/underflow");
        frame_start(); if(read_buffer!==3) $fatal(1,"buffer 3");
        frame_start(); if(read_buffer!==0) $fatal(1,"buffer 0");
        pause=1; frame_start(); if(read_buffer!==0) $fatal(1,"pause pointer");
        pause=0; frame_start(); if(read_buffer!==1) $fatal(1,"buffer 1");
        $display("PASS memory write control with ideal FIFO: 3x240 words, stalled DDR, buffer cycle and pause");
        rd_busy=1;
        for(integer i=0;i<530;i=i+1) begin valid=1; @(negedge cam_clk); end
        valid=0;
        if(dut.U_w128_d512_fifo.overflow_attempts==0) $fatal(1,"overflow scenario not exercised");
        $display("KNOWN_LIMITATION memory: camera keeps writing when FIFO full; no overflow recovery in reference");
        $finish;
    end
    initial begin #100000; $fatal(1,"timeout"); end
endmodule
