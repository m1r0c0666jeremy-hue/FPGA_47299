`timescale 1ns/1ps
// Control-level boundary test with ideal FIFO, not a vendor PHY/IP simulation.
module tb_review_last_word;
    reg dc=0,pc=0,rst=0,vs=0,rd=0,returned=0;
    always #7.5 dc=~dc;
    always #6.667 pc=~pc;
    wire busy,req;
    wire [24:0] addr;
    wire [23:0] pixel;
    integer seen=0,wrong=0;
    reg checking=0,sample;
    video_out dut(rst,dc,busy,1'b1,2'b0,req,addr,1'b1,
                  returned,{16{8'ha5}},pc,vs,rd,pixel);
    always @(posedge pc) begin
        sample=checking && dut.S_video_rd_en_1d;
        #1;
        if(sample) begin
            seen=seen+1;
            if(pixel !== 24'ha5a5a5) begin
                wrong=wrong+1;
                $display("PIXEL_LOST index=%0d actual=%h",seen-1,pixel);
            end
        end
    end
    initial begin
        repeat(6) @(negedge pc); rst=1;
        vs=1; repeat(40) @(negedge dc); vs=0;
        // Exactly three 128-bit words = sixteen RGB pixels. No new data is needed.
        @(negedge dc); returned=1;
        repeat(3) @(negedge dc); returned=0;
        repeat(8) @(negedge pc);
        if(dut.U_w128_d512_fifo.count != 3) $fatal(1,"fixture did not enqueue three words");
        checking=1; rd=1;
        repeat(16) @(negedge pc); rd=0;
        repeat(4) @(negedge pc); checking=0;
        if(seen!=16 || wrong!=0)
            $fatal(1,"last FIFO word must remain usable: pixels=%0d lost=%0d",seen,wrong);
        $display("PASS all 16 pixels survive reading the final FIFO word"); $finish;
    end
    initial begin #10000; $fatal(1,"timeout"); end
endmodule
