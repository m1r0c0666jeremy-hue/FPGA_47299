`timescale 1ns/1ps
module tb_stable_faults;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,valid=0,fault=0,ready=1;
wire [31:0] id,drop;wire ov;wire [639:0] meta;reg [127:0] models;integer emitted=0,last_id=0;
stable_capture dut(clk,rst,sof,valid,fault,{4{24'h303030}},1'b0,1'b1,8'd1,models,16'd0,24'h400400,8'd0,1'b0,1'b0,ready,id,ov,meta,drop);
function [63:0] model(input integer lo,hi);begin model=(64'h8000000000000000)|(64'(lo)<<54)|(64'(hi)<<45)|(64'd32<<37)|(64'd16<<29)|(64'd1<<27);end endfunction
always @(negedge clk)if(ov)begin
emitted=emitted+1;last_id=meta[31:0];
if((last_id==1 || last_id==3 || last_id==4) && (meta[247] || meta[32] || meta[245] || meta[246]))$fatal(1,"malformed frame accepted id%0d",last_id);
if(last_id==2 && !meta[247])$fatal(1,"previous sticky writer fault poisoned next frame");
end
task begin_frame;begin @(negedge clk);sof=1;valid=1;@(negedge clk);sof=0;end endtask
task rest_full;integer n;begin for(n=1;n<230400;n=n+1)begin valid=1;@(negedge clk);if(n==2)fault=0;end valid=0;end endtask
initial begin
models={model(195,255),model(345,30)};repeat(4)@(negedge clk);rst=1;
begin_frame;rest_full;repeat(250000)@(negedge clk);
if(emitted!=0)$fatal(1,"published frame before closing SOF; late extra pixels could invalidate it");
valid=1;@(negedge clk);valid=0;fault=1;
begin_frame;rest_full;begin_frame;
repeat(40)@(negedge clk);valid=0;repeat(600)@(negedge clk);begin_frame;
rest_full;valid=1;@(negedge clk);valid=0;begin_frame;
rest_full;repeat(600)@(negedge clk);ready=0;
begin_frame;rest_full;begin_frame;rest_full;begin_frame;rest_full;
@(negedge clk);sof=1;valid=0;@(negedge clk);sof=0;repeat(213000)@(negedge clk);
ready=1;repeat(1000)@(negedge clk);
if(last_id!=8 || !meta[247] || drop==0)$fatal(1,"newest mailbox recovery id%0d dropped%0d",last_id,drop);
$display("STABLE_FAULTS_PASS closed-frame validation, late extra, previous fault recovery, short/long, mailbox latest without blocking banks");$finish;end
initial begin #40000000;$fatal(1,"fault test timeout");end
endmodule
