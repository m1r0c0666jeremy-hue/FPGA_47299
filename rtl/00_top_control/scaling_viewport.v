`default_nettype none
module scaling_viewport (
    input wire I_clk, I_rst_n, I_vs,
    input wire [10:0] I_cx,
    input wire [9:0] I_cy,
    input wire [1:0] I_zoom, I_direction, I_mode,
    input wire [2:0] I_status,
    output reg [10:0] O_cx, O_x0, O_cross_x,
    output reg [9:0] O_cy, O_y0, O_cross_y,
    output reg [1:0] O_zoom, O_direction, O_mode,
    output reg [2:0] O_status
);
    reg vs_d;
    reg [10:0] nx;
    reg [9:0] ny;
    always @* begin
        nx=0; ny=O_y0;
        case(I_zoom)
        0: begin
            if(O_zoom!=0) ny=(I_cy<312)?0:(I_cy>408)?96:I_cy-312;
            else if(I_cy < O_y0+32) ny=(I_cy<32)?0:I_cy-32;
            else if(I_cy > O_y0+591) ny=(I_cy>687)?96:I_cy-591;
        end
        1: begin
            nx=(I_cx<320)?0:(I_cx>960)?640:I_cx-320;
            ny=(I_cy<156)?0:(I_cy>564)?408:I_cy-156;
        end
        default: begin
            nx=(I_cx<160)?0:(I_cx>1120)?960:I_cx-160;
            ny=(I_cy<78)?0:(I_cy>642)?564:I_cy-78;
        end
        endcase
    end
    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n) begin
            vs_d<=0; O_cx<=640; O_cy<=360; O_x0<=0; O_y0<=48;
            O_mode<=0; O_zoom<=0; O_cross_x<=640; O_cross_y<=312; O_direction<=0; O_status<=0;
        end else begin
            vs_d<=I_vs;
            if(I_vs&&!vs_d) begin
                O_cx<=I_cx; O_cy<=I_cy; O_x0<=nx; O_y0<=ny; O_zoom<=I_zoom;
                O_cross_x<=((I_cx-nx)<<I_zoom)+((1<<I_zoom)>>1);
                O_cross_y<=((I_cy-ny)<<I_zoom)+((1<<I_zoom)>>1);
                O_mode<=I_mode; O_direction<=I_direction; O_status<=I_status;
            end
        end
    end
endmodule
`default_nettype wire
