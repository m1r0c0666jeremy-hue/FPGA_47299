`timescale 1ns/1ps
module tb_status;
    reg cfg_clk=0, rx_clk=0, px_clk=0, rst=0;
    always #21 cfg_clk=~cfg_clk;
    always #8 rx_clk=~rx_clk;
    always #6.667 px_clk=~px_clk;
    reg cfg=0, hs=0, valid=0, fs=0;
    wire [3:0] raw_status, synced;
    camera_status dut(cfg_clk,rx_clk,rst,cfg,hs,valid,fs,raw_status);
    status_sync sync(px_clk,rst,raw_status,synced);
    task check(input [3:0] expected);
        repeat(5) @(negedge px_clk);
        if(synced !== expected) $fatal(1,"status %b != %b",synced,expected);
    endtask
    task packet(input integer words);
        @(negedge rx_clk); hs=1;
        @(negedge rx_clk); valid=1;
        repeat(words) @(negedge rx_clk);
        valid=0; hs=0;
        repeat(3) @(negedge rx_clk);
    endtask
    initial begin
        repeat(5) @(negedge rx_clk); check(0); rst=1;
        @(negedge cfg_clk); cfg=1;
        @(negedge cfg_clk); cfg=0;
        check(1);
        packet(399); check(3); // Wrong width must not assert width_seen.
        @(negedge rx_clk); fs=1;
        @(negedge rx_clk); fs=0;
        check(3);
        packet(400); check(11);
        @(negedge rx_clk); fs=1;
        @(negedge rx_clk); fs=0;
        check(15);
        repeat(10) @(negedge rx_clk); check(15); // Sticky, not live health.
        rst=0; check(0);
        rst=1; check(0);
        $display("PASS status: invalid/valid width, two frames, CDC flags, reset");
        $finish;
    end
    initial begin #100000; $fatal(1,"timeout"); end
endmodule
