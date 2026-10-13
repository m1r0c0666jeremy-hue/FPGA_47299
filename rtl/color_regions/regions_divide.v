// One unsigned restoring divider, used only after a frame. 32 iterations.
`default_nettype none
module regions_divide(input wire clk,rst_n,start,input wire [31:0] numerator,denominator,
 output reg busy,done,output reg [31:0] quotient);
 reg [31:0] work,den;reg [32:0] remainder;reg [5:0] count;
 wire [32:0] trial={remainder[31:0],work[31]};
 wire take=trial>={1'b0,den};
 wire [31:0] next_work={work[30:0],take};
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin busy<=0;done<=0;quotient<=0;work<=0;den<=0;remainder<=0;count<=0;end
  else begin
   done<=0;
   if(start && !busy)begin
    if(denominator==0)begin quotient<=0;done<=1;end
    else begin busy<=1;work<=numerator;den<=denominator;remainder<=0;count<=0;end
   end else if(busy)begin
    remainder<=take?trial-{1'b0,den}:trial;work<=next_work;
    if(count==31)begin quotient<=next_work;done<=1;busy<=0;end else count<=count+1'b1;
   end
  end
 end
endmodule
`default_nettype wire
