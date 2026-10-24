`timescale 1ns/1ps
module tb_switch_mode_10_3;
    reg clk=0,rst=0;
    reg [1:0] sw=0;
    wire [1:0] pending;
    always #5 clk=~clk;
    switch_mode_control #(.STABLE_CYCLES(8)) dut(clk,rst,sw,pending);
    task set_switch(input [1:0] v,input integer hold);
        @(negedge clk);sw=v;repeat(hold) @(negedge clk);
    endtask
    initial begin
        repeat(4) @(negedge clk);rst=1;
        // Bounce for less than debounce duration: no intermediate mode accepted.
        set_switch(1,2);set_switch(0,2);set_switch(3,2);set_switch(0,3);
        if(pending!==0) $fatal(1,"bounce leaked into pending mode");
        for(integer i=0;i<4;i=i+1) begin
            set_switch(i[1:0],14);
            if(pending!==i[1:0]) $fatal(1,"switch mapping %0d",i);
        end
        rst=0;#1;if(pending!==0) $fatal(1,"reset");
        $display("PASS switch synchronizer/debounce: bounce rejected, all 4 mode words, reset");$finish;
    end
endmodule
