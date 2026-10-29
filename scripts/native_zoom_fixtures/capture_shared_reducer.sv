`timescale 1ns/1ps
module tb;
reg clk=0;always #8.333 clk=~clk;
reg rst_n=0,sof=0,v=0,abort_frame=0;reg [95:0] rgb=0;
reg [127:0] models=0;wire ds,dv;wire [95:0] reduced;wire [32:0] tag;
native_downsample2 #(.WIDTH(32),.HEIGHT(8)) reducer(clk,rst_n,abort_frame,sof,v,rgb,33'd3,ds,dv,reduced,tag);
wire ov;wire [7:0] shared,parallel;reg [7:0] expected;reg [4:0] vp=0;
native_shared_classifier dut(clk,rst_n,dv,reduced,models,ov,shared);
genvar j;generate for(j=0;j<4;j=j+1)begin:ref_lane
stable_model_lane lane(clk,rst_n,reduced[95-j*24-:24],models,parallel[2*j+:2]);end endgenerate
integer frame,n,seed=32'h77302026,received=0;reg previous_valid=0;
always @(posedge clk)if(!rst_n)begin vp<=0;expected<=0;previous_valid<=0;end
else begin
 if(dv && previous_valid)$fatal(1,"actual native reducer violated nonadjacent quad contract");
 previous_valid<=dv;vp<={vp[3:0],dv};expected<=parallel;
end
always @(negedge clk)if(rst_n)begin
 if(ov!==vp[4])$fatal(1,"shared reducer valid mismatch");
 if(ov)begin if(shared!==expected)$fatal(1,"actual reducer classification mismatch");received=received+1;end
 models={$random(seed),$random(seed),$random(seed),$random(seed)};
end
initial begin
 repeat(4)@(negedge clk);rst_n=1;
 for(frame=0;frame<200;frame=frame+1)begin
  @(negedge clk);sof=1;v=0;@(negedge clk);sof=0;
  for(n=0;n<64;n=n+1)begin
   v=1;rgb={$random(seed),$random(seed),$random(seed)};@(negedge clk);
   if((n%7)==0)begin v=0;repeat(2)@(negedge clk);end
  end
  v=0;repeat(12)@(negedge clk);
  if(frame==50 || frame==150)begin rst_n=0;repeat(3)@(negedge clk);rst_n=1;end
 end
 repeat(12)@(negedge clk);
 if(received!=3200)$fatal(1,"reducer coverage %0d",received);
 $display("NATIVE_SHARED_REDUCER_PASS frames200 quads3200 actual_downsample nonadjacent_valid models_change/reset");$finish;
end
endmodule
