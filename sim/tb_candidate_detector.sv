`timescale 1ns/1ps
module tb_candidate_detector;
 parameter W=128,H=64;
 reg clk=0,rst=0,sof=0,valid=0,fault=0;reg [95:0] rgb=0;
 always #5 clk=~clk;
 wire ov;wire [255:0] om;wire [31:0] id;
 target_detector #(.WIDTH(W),.HEIGHT(H)) dut(clk,rst,sof,valid,fault,rgb,id,ov,om,1'b0,1'b1,8'd1);
 integer f,e,n,a,b,c,checked=0,expected_count;reg [95:0] d;reg [255:0] expected,mask;
 string stim,exp;
 always @(negedge clk) if(rst&&ov) begin
  n=$fscanf(e,"%h %h\n",expected,mask);
  if(n!=2 || (om&mask)!==(expected&mask)) $fatal(1,"detector #%0d actual=%h expected=%h mask=%h",checked,om,expected,mask);
  checked=checked+1;
 end
 initial begin
  if(!$value$plusargs("STIM=%s",stim)||!$value$plusargs("EXPECT=%s",exp)||!$value$plusargs("COUNT=%d",expected_count)) $fatal;
  f=$fopen(stim,"r");e=$fopen(exp,"r");if(!f||!e)$fatal;
  repeat(4) @(negedge clk);rst=1;
  while(!$feof(f)) begin
   @(negedge clk);#1;
   n=$fscanf(f,"%d %d %d %h\n",a,b,c,d);
   if(n==4) begin sof=a;valid=b;fault=c;rgb=d;end
  end
  @(negedge clk);#1;sof=0;valid=0;fault=0;
  repeat(300) @(negedge clk);
  if(checked!=expected_count)$fatal(1,"result count %0d expected %0d",checked,expected_count);
  $display("PASS detector %0dx%0d frames=%0d",W,H,checked);$finish;
 end
 initial begin #100000000;$fatal(1,"timeout");end
endmodule
