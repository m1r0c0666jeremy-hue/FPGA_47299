`timescale 1ns/1ps
module tb_dualcolor_tracker;
 parameter L=40,D=20;
 reg clk=0,rst=0,en=0,iv=0;reg [7:0] session=0;reg [255:0] im=0;
 always #5 clk=~clk;
 wire ov;wire [255:0] om;
 target_tracker #(.L_MM(L),.D_MM(D)) dut(clk,rst,en,session,iv,im,ov,om,1'b0);
 integer f,n,enable_arg,session_arg,checked=0;reg [255:0] next_meta,expected;
 string path;
 initial begin
  if(!$value$plusargs("CASES=%s",path))$fatal;
  f=$fopen(path,"r");if(!f)$fatal;
  repeat(4) @(negedge clk);rst=1;
  while(!$feof(f)) begin
   n=$fscanf(f,"%d %d %h %h\n",enable_arg,session_arg,next_meta,expected);
   if(n==4) begin
    @(negedge clk);en=enable_arg;session=session_arg;iv=0;
    repeat(4) @(negedge clk);
    im=next_meta;iv=1;
    @(negedge clk);iv=0;
    if(!ov || om!==expected)$fatal(1,"tracker L=%0d D=%0d case=%0d actual=%h expected=%h",L,D,checked,om,expected);
    checked=checked+1;
   end
  end
  $display("PASS tracker L=%0d D=%0d cases=%0d",L,D,checked);$finish;
 end
endmodule
