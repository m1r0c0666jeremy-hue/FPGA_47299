`timescale 1ns/1ps
module tb_bilinear_rgb;
    reg clk=0,rst=0;always #5 clk=~clk;
    reg [23:0] p0=0,p1=0,p2=0,p3=0;
    reg [1:0] a=0,b=0;
    reg vs=0,hs=0,de=0,good=0,ok=0;
    wire [23:0] rgb;wire ovs,ohs,ode,ook;
    bilinear_rgb dut(clk,rst,p0,p1,p2,p3,a,b,vs,hs,de,good,ok,rgb,ovs,ohs,ode,ook);
    reg [23:0] ref0=0,ref1=0;
    reg [3:0] sync0=0,sync1=0;
    integer n,c,value,lo,hi,checked=0;
    reg [31:0] rng=32'h145839ab;
    function [31:0] random_next(input [31:0] v);
        reg [31:0] t;begin t=v^(v<<13);t=t^(t>>17);random_next=t^(t<<5);end
    endfunction
    always @(posedge clk) begin
        if(!rst) begin ref0<=0;ref1<=0;sync0<=0;sync1<=0;end
        else begin
            for(c=0;c<3;c=c+1) begin
                value=((4-a)*(4-b)*p0[c*8+:8]+a*(4-b)*p1[c*8+:8]+(4-a)*b*p2[c*8+:8]+a*b*p3[c*8+:8]+8)/16;
                lo=p0[c*8+:8];hi=lo;
                if(p1[c*8+:8]<lo)lo=p1[c*8+:8];if(p1[c*8+:8]>hi)hi=p1[c*8+:8];
                if(p2[c*8+:8]<lo)lo=p2[c*8+:8];if(p2[c*8+:8]>hi)hi=p2[c*8+:8];
                if(p3[c*8+:8]<lo)lo=p3[c*8+:8];if(p3[c*8+:8]>hi)hi=p3[c*8+:8];
                if(value<lo||value>hi)$fatal(1,"reference convexity");
                ref0[c*8+:8]<=(de&&good)?value:0;
            end
            ref1<=ref0;sync0<={vs,hs,de,ok};sync1<=sync0;
        end
    end
    always @(negedge clk) if(rst) begin
        if(rgb!==ref1 || {ovs,ohs,ode,ook}!==sync1)$fatal(1,"bilinear mismatch %h %h",rgb,ref1);
        checked=checked+1;
    end
    initial begin
        repeat(3) @(negedge clk);#1;rst=1;
        for(n=0;n<66048;n=n+1) begin
            @(negedge clk);#1;
            a=n%4;b=(n/4)%4;
            if(n<256) begin p0=(n&16)?24'hffffff:0;p1=(n&32)?24'hffffff:0;p2=(n&64)?24'hffffff:0;p3=(n&128)?24'hffffff:0;end
            else if(n<512)begin p0={3{8'(n)}};p1=p0;p2=p0;p3=p0;end
            else begin rng=random_next(rng);p0=rng;rng=random_next(rng);p1=rng;rng=random_next(rng);p2=rng;rng=random_next(rng);p3=rng;end
            vs=n%113==0;hs=n%17==0;de=n%29!=0;good=n%37!=0;ok=good;
            if(n==32768)begin rst=0;repeat(3)@(negedge clk);#1;rst=1;end
        end
        repeat(4)@(negedge clk);
        $display("PASS bilinear arithmetic: %0d checks, all fractions/extrema/constants/random/reset/sync",checked);$finish;
    end
endmodule
