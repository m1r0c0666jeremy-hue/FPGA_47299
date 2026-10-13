// Four pixels in, up to three closed horizontal runs out. No input backpressure.
// Record: {ROI membership[1:0], local-edge clip, sumq[11:0], sy[19:0],
//          sx[19:0], xmax[10:0], xmin[10:0]} = 77 bits.
`default_nettype none
module regions_runs4 #(parameter WIDTH=1280)(
 input wire clk,rst_n,sof,valid,input wire [10:0] x,input wire [9:0] y,
 input wire [3:0] mask,clip,input wire [7:0] quality,membership,
 input wire [1:0] line_bank,input wire frame_bank,
 output reg [1:0] out_count,output reg [230:0] records,
 output reg eol,output reg [5:0] line_count,output reg overflow,
 output reg [1:0] out_line_bank,output reg out_frame_bank,output reg [9:0] out_y
);
 reg opened;reg [10:0] start_x;reg [19:0] sx,sy;reg [11:0] sq;
 reg [1:0] mem;reg clipped;reg [5:0] count;
 reg next_open,next_clip;reg [10:0] next_start;
 reg [19:0] next_sx,next_sy;reg [11:0] next_sq;reg [1:0] next_mem;
 reg [230:0] rec;reg [76:0] item;integer n,k,j,len,a;
 reg [19:0] gx,gy,tx,ty;reg [11:0] tq;reg [10:0] xlo,xhi;
 reg [1:0] tm;reg tc;reg [4:0] gq;reg [1:0] gm;reg gc;
 function [19:0] small_mul;
   input [10:0] value;input integer amount;
   reg [19:0] wide;
   begin wide={9'd0,value};case(amount)
    1:small_mul=wide;2:small_mul=wide<<1;3:small_mul=(wide<<1)+wide;
    4:small_mul=wide<<2;default:small_mul=0;endcase end
 endfunction
 always @* begin
   rec=0;n=0;next_open=0;next_start=start_x;next_sx=sx;next_sy=sy;
   next_sq=sq;next_mem=mem;next_clip=clipped;
   item=0;gx=0;gy=0;tx=0;ty=0;tq=0;xlo=0;xhi=0;tm=0;tc=0;
   len=0;j=0;gq=0;gm=0;gc=0;
   if(opened && !sof && !mask[0])begin
     rec[0+:77]={mem,clipped,sq,sy,sx,(x-11'd1),start_x};n=1;
   end
   for(k=0;k<4;k=k+1)begin
     if(mask[k] && (k==0 || !mask[k-1]))begin
       j=k;
       if(k<3 && mask[k+1])begin
         j=k+1;
         if(k<2 && mask[k+2])begin j=k+2;if(k==0 && mask[3])j=3;end
       end
       len=j-k+1;gx=small_mul(x,len);gy=small_mul({1'b0,y},len);
       // At most four lane constants; no coordinate multiply/divide.
       case({k[1:0],j[1:0]})
        4'h0:gx=gx;4'h1:gx=gx+1;4'h2:gx=gx+3;4'h3:gx=gx+6;
        4'h5:gx=gx+1;4'h6:gx=gx+3;4'h7:gx=gx+6;
        4'ha:gx=gx+2;4'hb:gx=gx+5;4'hf:gx=gx+3;
       endcase
       gq=0;gm=0;gc=0;
       for(a=0;a<4;a=a+1)if(a>=k && a<=j)begin
         gq=gq+quality[2*a+:2];gm=gm|membership[2*a+:2];gc=gc|clip[a];
       end
       xlo=x+k;xhi=x+j;tx=gx;ty=gy;tq=gq;tm=gm;tc=gc;
       if(k==0 && opened && !sof)begin
         xlo=start_x;tx=sx+gx;ty=sy+gy;tq=sq+gq;tm=mem|gm;tc=clipped|gc;
       end
       if(j!=3 || x==WIDTH-4)begin
         item={tm,tc,tq,ty,tx,xhi,xlo};rec[n*77+:77]=item;n=n+1;
       end else begin
         next_open=1;next_start=xlo;next_sx=tx;next_sy=ty;next_sq=tq;next_mem=tm;next_clip=tc;
       end
     end
   end
 end
 always @(posedge clk or negedge rst_n)begin
   if(!rst_n)begin
     opened<=0;start_x<=0;sx<=0;sy<=0;sq<=0;mem<=0;clipped<=0;count<=0;
     out_count<=0;records<=0;eol<=0;line_count<=0;overflow<=0;
     out_line_bank<=0;out_frame_bank<=0;out_y<=0;
   end else begin
     out_count<=0;eol<=0;overflow<=0;
     if(sof)begin opened<=0;count<=0;end
     if(valid)begin
       opened<=next_open;start_x<=next_start;sx<=next_sx;sy<=next_sy;sq<=next_sq;mem<=next_mem;clipped<=next_clip;
       out_count<=n;records<=rec;out_line_bank<=line_bank;out_frame_bank<=frame_bank;out_y<=y;
       overflow<=(sof?0:count)+n>32;
       if(x==WIDTH-4)begin eol<=1;line_count<=((sof?0:count)+n>32)?32:(sof?0:count)+n;count<=0;end
       else count<=((sof?0:count)+n>32)?33:(sof?0:count)+n;
     end
   end
 end
endmodule
`default_nettype wire
