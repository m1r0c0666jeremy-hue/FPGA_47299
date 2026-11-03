// Bounded iterative arithmetic. No inferred multiplication, division or DSP.
`default_nettype none
module stage1_arith #(parameter MW=24,DW=48,NW=48,SW=24)(input wire clk,rst_n,start,input wire [1:0] op,
 input wire [47:0] a,b,output reg busy,done,output reg [47:0] result,output reg [47:0] residue);
 reg [1:0] mode;reg [5:0] count;reg negative;
 reg [2*MW-1:0] acc;reg [NW-1:0] numer;reg [DW-1:0] denom;reg [MW-1:0] multiplier;reg [SW-1:0] root;
 localparam RW=(DW+1)>(SW+2)?DW+1:SW+2;
 reg [RW-1:0] remainder;
 // The low product half also holds the unconsumed multiplier bits. Add only
 // into the high half, then shift the entire product once. Latency stays MW.
 wire [MW:0] high_sum={1'b0,acc[2*MW-1:MW]}+(acc[0]?{1'b0,multiplier}:{(MW+1){1'b0}});
 wire [2*MW-1:0] add_product={high_sum,acc[MW-1:1]};
 wire [2*MW-1:0] signed_product=negative?(~add_product+1'b1):add_product;
 wire [DW:0] div_rem={remainder[DW-1:0],numer[NW-1]};
 wire div_bit=div_rem>={1'b0,denom};
 wire [NW-1:0] div_q={numer[NW-2:0],div_bit};
 wire [SW+1:0] sqrt_rem=(remainder[SW+1:0]<<2)|{{SW{1'b0}},numer[NW-1:NW-2]};
 wire [SW+1:0] trial=({2'd0,root}<<2)|1'b1;
 wire sqrt_bit=sqrt_rem>=trial;
 wire [SW-1:0] sqrt_q={root[SW-2:0],sqrt_bit};
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin busy<=0;done<=0;result<=0;residue<=0;mode<=0;count<=0;negative<=0;
 acc<=0;multiplier<=0;numer<=0;denom<=0;remainder<=0;root<=0;end
 else begin done<=0;
 if(start && !busy)begin
 busy<=1;mode<=op;count<=0;acc<={{MW{1'b0}},(b[MW-1]?(~b[MW-1:0]+1'b1):b[MW-1:0])};remainder<=0;root<=0;
 numer<=op[1]?{a[2*SW-1:0],{(NW-2*SW){1'b0}}}:a[NW-1:0];denom<=b[DW-1:0];negative<=a[MW-1]^b[MW-1];
 multiplier<=a[MW-1]?(~a[MW-1:0]+1'b1):a[MW-1:0];
 end else if(busy)begin
 case(mode)
 0:begin acc<=add_product;
 if(count==MW-1)begin result<={{(48-2*MW){signed_product[2*MW-1]}},signed_product};busy<=0;done<=1;end end
 1:begin
 numer<=div_q;remainder<=div_bit?div_rem-{1'b0,denom}:div_rem;
 if(count==NW-1 || denom==0)begin result<=denom==0?48'hffffffffffff:div_q;
 residue<=div_bit?div_rem-{1'b0,denom}:div_rem;busy<=0;done<=1;end end
 default:begin numer<=numer<<2;root<=sqrt_q;remainder<=sqrt_bit?sqrt_rem-trial:sqrt_rem;
 if(count==SW-1)begin result<={{(48-SW){1'b0}},sqrt_q};busy<=0;done<=1;end end
 endcase
 count<=count+1'b1;
 end end end
endmodule
`default_nettype wire
