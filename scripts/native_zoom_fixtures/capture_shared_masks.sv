module tb;
 reg clk=0;always #8.333 clk=~clk;reg rst_n=0,valid=0;reg [95:0] rgb=0;reg [127:0] models=0;
 wire ov;wire [7:0] shared,parallel;reg [7:0] expected;reg [4:0] vp=0;
 integer i,n=0,hits=0,seed=32'h47351;reg prior=0;
 native_shared_classifier dut(clk,rst_n,valid,rgb,models,ov,shared);
 genvar j;generate for(j=0;j<4;j=j+1)begin:ref_lane
 stable_model_lane lane(clk,rst_n,rgb[95-j*24-:24],models,parallel[2*j+:2]);end endgenerate
 always @(posedge clk)if(!rst_n)begin vp<=0;expected<=0;end
 else begin vp<={vp[3:0],valid};expected<=parallel;end
 task check;begin
 #1;if(ov!==vp[4])$fatal(1,"valid mismatch");
 if(ov)begin if(shared!==expected)$fatal(1,"mask mismatch i%0d got%h exp%h",i,shared,expected);n=n+1;hits=hits+|shared;end
 end endtask
 initial begin
 repeat(4)@(negedge clk);rst_n=1;
 for(i=0;i<100000;i=i+1)begin
 @(negedge clk);valid=!prior && (($random(seed)&7)!=0);prior=valid;
 rgb={$random(seed),$random(seed),$random(seed)};
 models={$random(seed),$random(seed),$random(seed),$random(seed)};
 // Include valid, wrapped/full/narrow hue models and all saturation codes.
 if((i%3)==0)begin models[63]=1;models[127]=1;models[44:37]=0;models[108:101]=0;
 models[36:29]=0;models[100:93]=0;models[62:54]=0;models[53:45]=359;
 models[126:118]=300;models[117:109]=60;end
 @(posedge clk);check;
 if(i==34567 || i==67891)begin @(negedge clk);rst_n=0;valid=0;prior=0;repeat(3)@(negedge clk);rst_n=1;end
 end
 @(negedge clk);valid=0;repeat(8)begin @(posedge clk);check;end
 if(n<40000 || hits<1000)$fatal(1,"coverage count%0d hits%0d",n,hits);
 $display("NATIVE_SHARED_MASKS_PASS %0d valid_quads %0d nonzero_masks one_cycle_delay models/change/reset min_gap2",n,hits);$finish;
 end endmodule