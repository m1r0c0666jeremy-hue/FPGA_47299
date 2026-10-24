`timescale 1ns/1ps
// Must be compiled against the file actually selected by criticalwork.al.
module tb_review_pack_reset;
    reg clk=0,rst=0,fs=0,valid=0;
    reg [95:0] data=96'h123456789abcdef012345678;
    wire out_fs,out_valid;
    wire [127:0] out_data;
    always #5 clk=~clk;
    data_96bit_to_128bit dut(clk,rst,fs,valid,data,out_fs,out_valid,out_data);
    initial begin
        repeat(4) @(negedge clk); rst=1;
        valid=1; @(negedge clk);
        rst=0; @(negedge clk);
        if(out_valid !== 0 || out_data !== 0 || out_fs !== 0)
            $fatal(1,"reset during valid input did not flush the active packer");
        valid=0; rst=1; @(negedge clk);
        valid=1; @(negedge clk);
        if(out_valid !== 0) $fatal(1,"first beat after reset should only buffer");
        @(negedge clk);
        if(out_valid !== 1 || out_data !== {data,data[95:64]})
            $fatal(1,"packing did not restart from a clean group");
        $display("PASS packer reset and restart"); $finish;
    end
    initial begin #2000; $fatal(1,"timeout"); end
endmodule
