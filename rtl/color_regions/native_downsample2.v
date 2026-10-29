// Exact 2x2 RGB average: add all four samples, round once, then divide by four.
// 640 x 54-bit row sums use three legal 20K RAM widths, no DSP multiplication.
// SOF is deliberately independent of output valid: configuration is frozen
// before the first reduced pixel, rather than one dense row later.
`default_nettype none
module native_downsample2 #(parameter WIDTH=2560,HEIGHT=1440)(
 input wire clk,rst_n,abort_frame,sof,valid,input wire [95:0] rgb,
 input wire [32:0] frame_tag,output reg out_sof,out_valid,
 output reg [95:0] out_rgb,output reg [32:0] out_tag);
 localparam GROUPS=WIDTH/4;
 reg [9:0] column;reg [10:0] row;reg active;
 wire [9:0] cx=sof?10'd0:column;wire [10:0] cy=sof?11'd0:row;
 wire take=valid && (active || sof);
 reg [53:0] sums;integer p,c;
 always @*begin
  sums=0;
  for(p=0;p<2;p=p+1)for(c=0;c<3;c=c+1)
   sums[53-(p*3+c)*9-:9]={1'b0,rgb[95-(p*2*3+c)*8-:8]}+
                                      {1'b0,rgb[95-((p*2+1)*3+c)*8-:8]};
 end
 (* ram_style="block" *) reg [53:0] line_sums[0:GROUPS-1];
 reg [53:0] previous_sums,current_sums;reg reduce;
 always @(posedge clk)begin
  if(take && !cy[0])line_sums[cx]<=sums;
  if(take && cy[0])previous_sums<=line_sums[cx];
 end
 reg [47:0] first_pair;reg have_pair;
 function [47:0] average;input [53:0] a,b;reg [9:0] total;integer j;begin
  for(j=0;j<6;j=j+1)begin
   total={1'b0,a[53-j*9-:9]}+{1'b0,b[53-j*9-:9]}+10'd2;
   average[47-j*8-:8]=total[9:2];
  end
 end endfunction
 wire [47:0] reduced_pair=average(previous_sums,current_sums);
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin column<=0;row<=0;active<=0;reduce<=0;current_sums<=0;
  first_pair<=0;have_pair<=0;out_sof<=0;out_valid<=0;out_rgb<=0;out_tag<=0;end
 else begin
  out_sof<=sof;out_valid<=0;reduce<=take && cy[0];
  if(take)begin
   current_sums<=sums;
   if(cx==GROUPS-1)begin column<=0;row<=cy+1'b1;if(cy==HEIGHT-1)active<=0;end
   else column<=cx+1'b1;
  end
  if(reduce && !sof)begin
   have_pair<=~have_pair;
   if(!have_pair)first_pair<=reduced_pair;
   else begin out_rgb<={first_pair,reduced_pair};out_valid<=1;end
  end
  if(sof)begin
   active<=1;column<=take?10'd1:10'd0;row<=0;have_pair<=0;out_tag<=frame_tag;
  end
  if(abort_frame)begin active<=0;reduce<=0;have_pair<=0;out_sof<=0;out_valid<=0;end
 end end
endmodule
`default_nettype wire
