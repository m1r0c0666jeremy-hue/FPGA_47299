`timescale 1ns/1ps
module tb_pack;
    reg clk=0, rst=0, fs=0, valid=0;
    reg [95:0] data=0;
    wire out_fs, out_valid;
    wire [127:0] out_data;
    integer sent_bytes=0, received_bytes=0, words=0, fs_count=0;
    integer line_index, beat, b;
    reg checking=1;
    data_96bit_to_128bit dut(clk,rst,fs,valid,data,out_fs,out_valid,out_data);
    always #5 clk=~clk;
    function [7:0] pattern(input integer index);
        pattern = ((index * 37) ^ (index >> 8)) & 255;
    endfunction
    always @(posedge clk) begin
        #1;
        if(checking) begin
            if(out_fs) fs_count=fs_count+1;
            if(out_valid) begin
                for(integer j=0;j<16;j=j+1)
                    if(out_data[127-j*8 -:8] !== pattern(received_bytes+j))
                        $fatal(1,"packing byte %0d mismatch", received_bytes+j);
                received_bytes=received_bytes+16;
                words=words+1;
            end
        end
    end
    initial begin
        repeat(4) @(negedge clk); rst=1;
        fs=1; @(negedge clk); fs=0;
        for(line_index=0;line_index<3;line_index=line_index+1) begin
            for(beat=0;beat<320;beat=beat+1) begin
                valid=1;
                for(b=0;b<12;b=b+1) data[95-b*8 -:8]=pattern(sent_bytes+b);
                sent_bytes=sent_bytes+12;
                @(negedge clk);
            end
            valid=0;
            repeat(12) @(negedge clk);
        end
        if(words!=720 || received_bytes!=11520 || fs_count!=1)
            $fatal(1,"pack counts words=%0d bytes=%0d fs=%0d",words,received_bytes,fs_count);
        $display("PASS pack: 3 x 1280 RGB pixels, 96->128 bits, row blanking, SOF");
        checking=0;
        // Explicitly characterize the inherited limitation; do not label this robust reset.
        valid=1; data=96'h1234; @(negedge clk);
        rst=0; @(negedge clk);
        if(out_valid !== 1'b1) $fatal(1,"reference reset behavior changed; re-audit");
        $display("KNOWN_LIMITATION pack: I_rst_n ignored; reset during valid data does not flush group");
        $finish;
    end
    initial begin #100000; $fatal(1,"timeout"); end
endmodule
