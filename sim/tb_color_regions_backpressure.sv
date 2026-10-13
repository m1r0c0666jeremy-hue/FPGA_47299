`timescale 1ns/1ps
module tb_color_regions_backpressure;
reg clk=0;always #5 clk=~clk;
reg rst=0,sof=0,v=0,ready=0;wire [31:0] id,drop;wire ov;wire [415:0] meta;
regions_capture dut(clk,rst,sof,v,1'b0,96'h502828502828502828502828,1'b0,1'b1,8'd1,ready,id,ov,meta,drop);
integer n=0,k;reg [31:0] expected[0:2];
always @(negedge clk)if(ov)begin
 if(!ready || meta[31:0]!==expected[n] || meta[247] || meta[245] || meta[246] || meta[318] || meta[382])$fatal(1,"busy output/id rejection %0d %h",n,meta[31:0]);
 n=n+1;
end
task short_frame;begin
 @(negedge clk);sof=1;@(negedge clk);sof=0;v=1;
 repeat(20)@(negedge clk);v=0;repeat(500)@(negedge clk);
end endtask
initial begin
 expected[0]=32'hffffffff;expected[1]=0;expected[2]=3;
 repeat(3)@(negedge clk);rst=1;repeat(2000)@(negedge clk);dut.O_frame_id=32'hfffffffe;
 short_frame;short_frame;short_frame;short_frame;
 if(n!=0 || drop!=1)$fatal(1,"busy mailbox published or no ownership rejection");
 ready=1;repeat(140000)@(negedge clk);
 if(n!=2)$fatal(1,"frozen bank packets not preserved");
 short_frame; // frame3 owns a released bank; prior rejected frame2 is counted.
 @(negedge clk);sof=1;@(negedge clk);sof=0;
 repeat(100000)@(negedge clk);
 if(n!=3 || drop!=2)$fatal(1,"busy recovery outputs%0d dropped%0d",n,drop);
 $display("PASS backpressure: frozen banks preserved, busy output waits, skipped IDs not forged, frame wrap and recovery");$finish;
end
initial begin #4000000;$fatal(1,"timeout");end
endmodule
