// Small binary-to-decimal pipeline for the live candidate panel. No dividers.
`default_nettype none
module target_diagnostics(
 input wire I_clk,I_rst_n,input wire [19:0] I_count_a,I_count_b,
 input wire [6:0] I_fill_a,I_fill_b,
 output reg [23:0] O_count_a,O_count_b,output reg [11:0] O_fill_a,O_fill_b
);
 reg [4:0] step;
 reg [19:0] a,b,fa,fb;
 reg [23:0] da,db,dfa,dfb;
 function [23:0] next_decimal(input [23:0] old,input bit_in);
  reg [23:0] corrected;integer j;
  begin
   corrected=old;
   for(j=0;j<6;j=j+1) if(old[j*4+:4]>=5) corrected[j*4+:4]=old[j*4+:4]+4'd3;
   next_decimal={corrected[22:0],bit_in};
  end
 endfunction
 always @(posedge I_clk or negedge I_rst_n) begin
  if(!I_rst_n) begin
   step<=0;a<=0;b<=0;fa<=0;fb<=0;da<=0;db<=0;dfa<=0;dfb<=0;
   O_count_a<=0;O_count_b<=0;O_fill_a<=0;O_fill_b<=0;
  end else if(step==0) begin
   a<=I_count_a;b<=I_count_b;fa<={13'd0,I_fill_a};fb<={13'd0,I_fill_b};
   da<=0;db<=0;dfa<=0;dfb<=0;step<=1;
  end else if(step<=20) begin
   da<=next_decimal(da,a[19]);db<=next_decimal(db,b[19]);
   dfa<=next_decimal(dfa,fa[19]);dfb<=next_decimal(dfb,fb[19]);
   a<=a<<1;b<=b<<1;fa<=fa<<1;fb<=fb<<1;step<=step+1'b1;
  end else begin
   O_count_a<=da;O_count_b<=db;O_fill_a<=dfa[11:0];O_fill_b<=dfb[11:0];step<=0;
  end
 end
endmodule
`default_nettype wire
