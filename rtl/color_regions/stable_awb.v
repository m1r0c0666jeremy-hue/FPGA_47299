// Fixed per-frame Q2.10 gains. The first SOF pixel uses the new complete profile.
`default_nettype none
module stable_awb(input wire I_clk,I_rst_n,I_tlast,I_tuser,I_tvalid,
 input wire [95:0] I_tdata,input wire [11:0] I_gain_r,I_gain_b,
 output reg O_tlast,O_tuser,O_tvalid,output reg [95:0] O_tdata);
 reg [11:0] gr,gb;wire [11:0] er=I_tuser?I_gain_r:gr,eb=I_tuser?I_gain_b:gb;
 reg [19:0] pr[0:3],pb[0:3];reg [7:0] pg[0:3];reg v,s,l;integer i;
 function [7:0] clip;input [19:0] p;reg [20:0] q;begin q={1'b0,p}+512;clip=q>=261632?255:q[17:10];end endfunction
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin gr<=1024;gb<=1024;v<=0;s<=0;l<=0;O_tdata<=0;O_tlast<=0;O_tuser<=0;O_tvalid<=0;
 for(i=0;i<4;i=i+1)begin pr[i]<=0;pb[i]<=0;pg[i]<=0;end end
 else begin
 if(I_tuser)begin gr<=I_gain_r;gb<=I_gain_b;end
 v<=I_tvalid;s<=I_tuser;l<=I_tlast;O_tvalid<=v;O_tuser<=s;O_tlast<=l;
 for(i=0;i<4;i=i+1)begin
 pr[i]<=I_tdata[95-i*24-:8]*er;pg[i]<=I_tdata[87-i*24-:8];pb[i]<=I_tdata[79-i*24-:8]*eb;
 O_tdata[95-i*24-:24]<={clip(pr[i]),pg[i],clip(pb[i])};end
 end end
endmodule
`default_nettype wire
