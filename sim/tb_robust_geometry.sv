`timescale 1ns/1ps
module tb_robust_geometry;
 reg clk=0,rst=0,en=1,iv=0,pair=0;always #5 clk=~clk;
 reg [7:0] session=1;reg [255:0] meta=0;wire ov;wire [255:0] out;
 target_tracker #(.SEP_MAX(1468)) dut(clk,rst,en,session,iv,meta,ov,out,pair);
 integer id=0,j,k,expected_x,checks=0;
 task case_three(input integer ax,input integer bx,input integer tip,input integer valid_pair);
  begin
   @(negedge clk);session=session+1;repeat(3)@(negedge clk);
   for(j=0;j<3;j=j+1)begin
    id=id+1;meta=0;meta[31:0]=id;meta[32]=1;
    meta[47:37]=ax;meta[57:48]=360;meta[68:58]=bx;meta[78:69]=360;
    meta[203:184]=120000;meta[223:204]=4000;
    meta[242:235]=session;meta[243]=pair;meta[244]=1;meta[247:245]=7;
    iv=1;@(negedge clk);iv=0;
    if(!ov || out[32]!== (valid_pair && j==2))$fatal(1,"3-frame geometry lock");
    if(out[203:184]!=120000 || out[223:204]!=4000)$fatal(1,"unequal areas altered");
    if(out[32] && (out[89:79]!=tip || out[99:90]!=360))$fatal(1,"centers/tip");
    if(!valid_pair && out[36:33]!=(ax-bx<16 && bx-ax<16?5:6))$fatal(1,"geometry reason");
    checks=checks+1;repeat(3)@(negedge clk);
   end
  end
 endtask
 initial begin
  repeat(5)@(negedge clk);rst=1;
  for(k=0;k<2;k=k+1)begin
   pair=k;
   case_three(750,100,1075,1); // distance 650 formerly rejected
   case_three(400,1100,50,1); // negative extrapolation, distance 700
   case_three(900,100,1300,0); // retain tip out-of-range rejection
   case_three(500,490,505,0); // retain minimum separation
  end
  $display("PASS robust geometry: %0d frames, both palettes, 120000/4000 unequal areas, 650/700px center distance, out-of-range and too-close rejection",checks);$finish;
 end
endmodule
