// Bounded iterative arithmetic. No inferred multiplication, division or DSP.
`default_nettype none
module stage1_arith(input wire clk,rst_n,start,input wire [1:0] op,
 input wire [47:0] a,b,output reg busy,done,output reg [47:0] result,output reg [47:0] residue);
 reg [1:0] mode;reg [5:0] count;reg negative;
 reg [47:0] acc,shifted,numer,denom;reg [23:0] multiplier,root;
 reg [49:0] remainder;
 wire [47:0] add_product=acc+(multiplier[0]?shifted:48'd0);
 wire [49:0] div_rem={1'b0,remainder[47:0],numer[47]};
 wire div_bit=div_rem>={2'd0,denom};
 wire [47:0] div_q={numer[46:0],div_bit};
 wire [49:0] sqrt_rem=(remainder<<2)|{48'd0,numer[47:46]};
 wire [49:0] trial=({26'd0,root}<<2)|50'd1;
 wire sqrt_bit=sqrt_rem>=trial;
 wire [23:0] sqrt_q={root[22:0],sqrt_bit};
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin busy<=0;done<=0;result<=0;residue<=0;mode<=0;count<=0;negative<=0;
 acc<=0;shifted<=0;multiplier<=0;numer<=0;denom<=0;remainder<=0;root<=0;end
 else begin done<=0;
 if(start && !busy)begin
 busy<=1;mode<=op;count<=0;acc<=0;remainder<=0;root<=0;
 numer<=a;denom<=b;negative<=a[23]^b[23];
 shifted<={24'd0,(a[23]?(~a[23:0]+24'd1):a[23:0])};
 multiplier<=b[23]?(~b[23:0]+24'd1):b[23:0];
 end else if(busy)begin
 case(mode)
 0:begin acc<=add_product;shifted<=shifted<<1;multiplier<=multiplier>>1;
 if(count==23)begin result<=negative?(~add_product+48'd1):add_product;busy<=0;done<=1;end end
 1:begin
 numer<=div_q;remainder<=div_bit?div_rem-{2'd0,denom}:div_rem;
 if(count==47 || denom==0)begin result<=denom==0?48'hffffffffffff:div_q;
 residue<=div_bit?div_rem-{2'd0,denom}:div_rem;busy<=0;done<=1;end end
 default:begin numer<=numer<<2;root<=sqrt_q;remainder<=sqrt_bit?sqrt_rem-trial:sqrt_rem;
 if(count==23)begin result<={24'd0,sqrt_q};busy<=0;done<=1;end end
 endcase
 count<=count+1'b1;
 end end end
endmodule
`default_nettype wire
