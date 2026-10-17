module tb;reg clk=0;always #5 clk=~clk;reg rst=0;reg [23:0] rgb=0;reg [127:0] models=0;
 wire [1:0] a,b;reference_model_lane gold(clk,rst,rgb,models,a);stable_model_lane dut(clk,rst,rgb,models,b);
 reg [31:0] rng=32'h47299;integer n,dual=0;
 always @(posedge clk)begin #1;if(rst && n>8)begin
 if(a!==b || gold.n!==dut.n || gold.mx!==dut.mx || gold.mn!==dut.mn)$fatal(1,"hue pipeline mismatch n%0d rgb%h n%0d/%0d hit%b/%b",n,rgb,gold.n,dut.n,a,b);
 if(a==3)dual=dual+1;end end
 initial begin repeat(4)@(negedge clk);rst=1;
 for(n=0;n<150000;n=n+1)begin @(negedge clk);
 rng=rng*1664525+1013904223;rgb=rng[23:0];
 if(n%7==0)rgb={rng[7:0],rng[7:0],rng[7:0]};
 if(n%13==0)rgb=24'hff0000;if(n%17==0)rgb=24'h0000ff;if(n%19==0)rgb=24'hffff00;
 if(n%23==0)rgb=24'hff00ff;
 rng=rng*1664525+1013904223;models[31:0]=rng;rng=rng*1664525+1013904223;models[63:32]=rng;
 rng=rng*1664525+1013904223;models[95:64]=rng;rng=rng*1664525+1013904223;models[127:96]=rng;
 if(n%3==0)begin models[63]=1;models[127]=1;models[44:37]=0;models[36:29]=1;models[108:101]=0;models[100:93]=1;end
 end
 repeat(8)@(negedge clk);$display("SHARED_HUE_RTL_PASS 150000 dynamic RGB/model cycles, unchanged four-clock masks, numerator/max/min exact; dual%0d",dual);$finish;
 end endmodule