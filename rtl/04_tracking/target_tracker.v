`default_nettype none
module target_tracker #(
    parameter L_MM=40,D_MM=20,WIDTH=1280,HEIGHT=720,
    parameter SEP_MIN=16,SEP_MAX=600,MAX_STEP=96,CONFIRM_FRAMES=3
)(
    input wire I_clk,I_rst_n,I_enable,
    input wire [7:0] I_session,
    input wire I_valid,
    input wire [255:0] I_meta,
    output reg O_valid,
    output reg [255:0] O_meta,input wire I_pair
);
    localparam signed [47:0] K_Q16=(D_MM*65536+L_MM/2)/L_MM;
    wire signed [12:0] ax=$signed({2'b0,I_meta[47:37]}),ay=$signed({3'b0,I_meta[57:48]});
    wire signed [12:0] bx=$signed({2'b0,I_meta[68:58]}),by=$signed({3'b0,I_meta[78:69]});
    wire signed [12:0] dx=ax-bx,dy=ay-by;
    wire signed [47:0] txq=ax*48'sd65536+dx*K_Q16;
    wire signed [47:0] tyq=ay*48'sd65536+dy*K_Q16;
    // Round to nearest, ties away from zero. Do NOT round K*delta first.
    wire signed [47:0] tx=txq>=0 ? (txq+48'sd32768)>>>16 : -(((-txq)+48'sd32768)>>>16);
    wire signed [47:0] ty=tyq>=0 ? (tyq+48'sd32768)>>>16 : -(((-tyq)+48'sd32768)>>>16);
    wire [25:0] distance2=dx*dx+dy*dy;
    reg prev_good,ever_locked;
    reg [7:0] session;
    reg [7:0] streak;
    reg [31:0] last_id;
    reg signed [12:0] pax,pay,pbx,pby;
    wire jump=(ax-pax>MAX_STEP || pax-ax>MAX_STEP || ay-pay>MAX_STEP || pay-ay>MAX_STEP ||
               bx-pbx>MAX_STEP || pbx-bx>MAX_STEP || by-pby>MAX_STEP || pby-by>MAX_STEP);
    wire geometry=I_meta[32] && distance2>=SEP_MIN*SEP_MIN && distance2<=SEP_MAX*SEP_MAX &&
                  tx>=0 && tx<WIDTH && ty>=0 && ty<HEIGHT;
    wire matching=I_meta[242:235]==I_session && I_meta[243]==I_pair && I_meta[244];
    wire good=geometry && (!prev_good || (!jump && I_meta[31:0]==last_id+1'b1));
    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n) begin
            prev_good<=0;ever_locked<=0;session<=0;streak<=0;last_id<=0;
            pax<=0;pay<=0;pbx<=0;pby<=0;O_valid<=0;O_meta<=0;
        end else begin
            O_valid<=0;
            if(!I_enable || I_session!=session) begin
                session<=I_session;streak<=0;prev_good<=0;ever_locked<=0;
            end
            if(I_valid) begin
                O_valid<=1;O_meta<=I_meta;O_meta[32]<=0;
                O_meta[234:232]<=I_enable?(ever_locked?3:1):0;
                O_meta[89:79]<=tx[10:0];O_meta[99:90]<=ty[9:0];
                if(I_enable && I_session==session && matching && I_meta[31:0]!=last_id) begin
                    last_id<=I_meta[31:0];prev_good<=geometry;
                    pax<=ax;pay<=ay;pbx<=bx;pby<=by;
                    if(good) begin
                        if(streak<CONFIRM_FRAMES) streak<=streak+1'b1;
                        if(streak>=CONFIRM_FRAMES-1) begin O_meta[32]<=1;O_meta[234:232]<=2;ever_locked<=1;end
                    end else begin
                        streak<=0;
                        if(I_meta[32]) begin
                            if(distance2<SEP_MIN*SEP_MIN || distance2>SEP_MAX*SEP_MAX) O_meta[36:33]<=5;
                            else if(tx<0 || tx>=WIDTH || ty<0 || ty>=HEIGHT) O_meta[36:33]<=6;
                            else O_meta[36:33]<=7;
                        end
                    end
                end
            end
        end
    end
endmodule
`default_nettype wire
