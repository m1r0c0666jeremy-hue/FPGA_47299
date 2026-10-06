// Fixed quarter-pixel bilinear RGB interpolation; no coefficient rounding.
// Two register stages. The convex weighted sum needs no saturation.
`default_nettype none
module bilinear_rgb (
    input wire I_clk,I_rst_n,
    input wire [23:0] I_p00,I_p10,I_p01,I_p11,
    input wire [1:0] I_fx,I_fy,
    input wire I_vs,I_hs,I_de,I_good,I_ok,
    output reg [23:0] O_rgb,
    output reg O_vs,O_hs,O_de,O_ok
);
    function [9:0] horizontal;
        input [7:0] left,right;
        input [1:0] frac;
        reg [9:0] l,r;
        begin
            l={2'b0,left};r={2'b0,right};
            case(frac)
                0:horizontal=l<<2;
                1:horizontal=(l<<1)+l+r;
                2:horizontal=(l+r)<<1;
                3:horizontal=l+(r<<1)+r;
            endcase
        end
    endfunction
    function [7:0] vertical;
        input [9:0] top,bottom;
        input [1:0] frac;
        reg [11:0] t,b,sum;
        begin
            t={2'b0,top};b={2'b0,bottom};
            case(frac)
                0:sum=t<<2;
                1:sum=(t<<1)+t+b;
                2:sum=(t+b)<<1;
                3:sum=t+(b<<1)+b;
            endcase
            sum=sum+12'd8;
            vertical=sum[11:4];
        end
    endfunction
    reg [9:0] h0[0:2],h1[0:2];
    reg [1:0] fy;
    reg vs,hs,de,good,ok;
    integer c;
    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n) begin
            fy<=0;vs<=0;hs<=0;de<=0;good<=0;ok<=0;
            O_rgb<=0;O_vs<=0;O_hs<=0;O_de<=0;O_ok<=0;
            for(c=0;c<3;c=c+1) begin h0[c]<=0;h1[c]<=0;end
        end else begin
            for(c=0;c<3;c=c+1) begin
                h0[c]<=horizontal(I_p00[c*8+:8],I_p10[c*8+:8],I_fx);
                h1[c]<=horizontal(I_p01[c*8+:8],I_p11[c*8+:8],I_fx);
                O_rgb[c*8+:8]<=(de && good)?vertical(h0[c],h1[c],fy):8'd0;
            end
            fy<=I_fy;vs<=I_vs;hs<=I_hs;de<=I_de;good<=I_good;ok<=I_ok;
            O_vs<=vs;O_hs<=hs;O_de<=de;O_ok<=ok;
        end
    end
endmodule
`default_nettype wire
