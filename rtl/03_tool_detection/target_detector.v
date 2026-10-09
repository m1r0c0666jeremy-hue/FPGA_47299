// AWB tap: four RGB888 pixels, FIRST pixel in [95:72], as serialized by
// data_96bit_to_128bit and the existing DDR line reader. No backpressure.
// Results are finalized at the NEXT SOF, so short AND overlong frames fail.
// See docs/LockingnTracking使用与实现.md for the 256-bit metadata layout.
`default_nettype none
module target_detector #(
    parameter WIDTH=1280, HEIGHT=720,
    parameter COLOR_MIN=80,COLOR_DIFF=32,RATIO_NUM=3,RATIO_DEN=2,
    parameter AREA_MIN=64,AREA_MAX=20000,FILL_PERCENT_MIN=30,
    parameter YP_MIN=80,YP_DIFF=24,YP_RATIO_NUM=5,YP_RATIO_DEN=4,YP_BALANCE=2
)(
    input wire I_clk,I_rst_n,I_sof,I_valid,I_frame_fault,
    input wire [95:0] I_rgb,
    output wire [31:0] O_frame_id,
    output reg O_valid,
    output reg [255:0] O_meta,
    input wire I_pair,I_enable,input wire [7:0] I_session
);
    reg sof_d,seen;
    wire sof=I_sof&&!sof_d;
    reg [31:0] frame_id;
    assign O_frame_id=frame_id;
    reg [19:0] pixels;
    reg frame_bad;
    reg [10:0] x;
    reg [9:0] y;
    reg [19:0] area[0:1];
    reg [30:0] sx[0:1],sy[0:1];
    reg [10:0] xmin[0:1],xmax[0:1];
    reg [9:0] ymin[0:1],ymax[0:1];
    reg [19:0] next_area[0:1];
    reg [30:0] next_sx[0:1],next_sy[0:1];
    reg [10:0] next_xmin[0:1],next_xmax[0:1];
    reg [9:0] next_ymin[0:1],next_ymax[0:1];
    integer c,lane,xx,yy;
    reg [7:0] r,g,b;
    reg [31:0] lo,hi,other;
    reg frame_pair,frame_enable;reg [7:0] frame_session;
    wire selected_pair=sof?I_pair:frame_pair;
    // Factors are compile-time parameters (1..16). Explicit add/shift avoids
    // spending scarce DSPs on four-pixel constant color-ratio comparisons.
    function [12:0] color_scale(input [7:0] value,input [4:0] factor);
        integer bit_index;
        begin
            color_scale=0;
            for(bit_index=0;bit_index<5;bit_index=bit_index+1)
                if(factor[bit_index]) color_scale=color_scale+({5'd0,value}<<bit_index);
        end
    endfunction
    reg hit;
    always @* begin
        xx=sof?0:x; yy=sof?0:y;r=0;g=0;b=0;hit=0;lo=0;hi=0;other=0;
        for(c=0;c<2;c=c+1) begin
            next_area[c]=sof?0:area[c];next_sx[c]=sof?0:sx[c];next_sy[c]=sof?0:sy[c];
            next_xmin[c]=sof?WIDTH-1:xmin[c];next_xmax[c]=sof?0:xmax[c];
            next_ymin[c]=sof?HEIGHT-1:ymin[c];next_ymax[c]=sof?0:ymax[c];
            for(lane=0;lane<4;lane=lane+1) begin
                r=I_rgb[95-lane*24-:8];g=I_rgb[87-lane*24-:8];b=I_rgb[79-lane*24-:8];
                if(selected_pair) begin
                    if(c==0) begin lo=r<g?r:g;hi=r>g?r:g;other=b;end
                    else begin lo=r<b?r:b;hi=r>b?r:b;other=g;end
                    hit=lo>=YP_MIN && lo>=other+YP_DIFF && color_scale(lo[7:0],YP_RATIO_DEN)>=color_scale(other[7:0],YP_RATIO_NUM) && hi<=color_scale(lo[7:0],YP_BALANCE);
                end else if(c==0) hit=(r>=COLOR_MIN && {1'b0,r}>={1'b0,g}+COLOR_DIFF &&
                    {1'b0,r}>={1'b0,b}+COLOR_DIFF && r*RATIO_DEN>=g*RATIO_NUM && r*RATIO_DEN>=b*RATIO_NUM);
                else hit=(b>=COLOR_MIN && {1'b0,b}>={1'b0,g}+COLOR_DIFF &&
                    {1'b0,b}>={1'b0,r}+COLOR_DIFF && b*RATIO_DEN>=g*RATIO_NUM && b*RATIO_DEN>=r*RATIO_NUM);
                if(hit) begin
                    next_area[c]=next_area[c]+1'b1;
                    next_sx[c]=next_sx[c]+xx+lane;next_sy[c]=next_sy[c]+yy;
                    if(xx+lane<next_xmin[c]) next_xmin[c]=xx+lane;
                    if(xx+lane>next_xmax[c]) next_xmax[c]=xx+lane;
                    if(yy<next_ymin[c]) next_ymin[c]=yy;
                    if(yy>next_ymax[c]) next_ymax[c]=yy;
                end
            end
        end
    end
    // Frozen frame statistics. One shared 32-cycle unsigned divider computes
    // all four centroids; no combinational variable divider is synthesized.
    reg [30:0] nums[0:3];
    reg [19:0] counts[0:1];
    reg [21:0] box_area[0:1];
    reg [255:0] result;
    reg [3:0] state;
    reg [1:0] component;
    reg [5:0] bits_left;
    reg [31:0] quotient;
    reg [32:0] remainder;
    reg [19:0] denominator;
    wire [32:0] trial={remainder[31:0],quotient[31]};
    wire subtract=trial>={13'd0,denominator};
    wire [31:0] qnext={quotient[30:0],subtract};
    integer i;
    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n) begin
            frame_pair<=0;frame_enable<=0;frame_session<=0;
            sof_d<=0;seen<=0;frame_id<=0;pixels<=0;frame_bad<=0;x<=0;y<=0;
            O_valid<=0;O_meta<=0;state<=0;component<=0;bits_left<=0;
            quotient<=0;remainder<=0;denominator<=1;result<=0;
            for(i=0;i<2;i=i+1) begin
                area[i]<=0;sx[i]<=0;sy[i]<=0;xmin[i]<=WIDTH-1;xmax[i]<=0;
                ymin[i]<=HEIGHT-1;ymax[i]<=0;counts[i]<=0;box_area[i]<=0;
            end
            for(i=0;i<4;i=i+1) nums[i]<=0;
        end else begin
            sof_d<=I_sof;O_valid<=0;
            if(sof) begin
                frame_pair<=I_pair;frame_enable<=I_enable;frame_session<=I_session;
                seen<=1;frame_id<=frame_id+1'b1;pixels<=I_valid?4:0;
                x<=I_valid?4:0;y<=0;frame_bad<=0;
                for(i=0;i<2;i=i+1) begin
                    area[i]<=I_valid?next_area[i]:0;sx[i]<=I_valid?next_sx[i]:0;sy[i]<=I_valid?next_sy[i]:0;
                    xmin[i]<=I_valid?next_xmin[i]:WIDTH-1;xmax[i]<=I_valid?next_xmax[i]:0;
                    ymin[i]<=I_valid?next_ymin[i]:HEIGHT-1;ymax[i]<=I_valid?next_ymax[i]:0;
                end
                // Normal frame interval is many thousands of clocks. A too-fast
                // SOF invalidates/cancels the unfinished transaction, never reuses it.
                if(seen) begin
                    result<=0;result[31:0]<=frame_id;
                    result[242:235]<=frame_session;result[243]<=frame_pair;result[244]<=frame_enable;
                    result[32]<=!frame_bad && !I_frame_fault && pixels==WIDTH*HEIGHT && state==0;
                    result[36:33]<=I_frame_fault?8:((!frame_bad && pixels==WIDTH*HEIGHT && state==0)?0:1);
                    result[110:100]<=xmin[0];result[121:111]<=xmax[0];
                    result[131:122]<=ymin[0];result[141:132]<=ymax[0];
                    result[152:142]<=xmin[1];result[163:153]<=xmax[1];
                    result[173:164]<=ymin[1];result[183:174]<=ymax[1];
                    result[203:184]<=area[0];result[223:204]<=area[1];
                    nums[0]<=sx[0];nums[1]<=sy[0];nums[2]<=sx[1];nums[3]<=sy[1];
                    for(i=0;i<2;i=i+1) begin
                        counts[i]<=area[i];
                        box_area[i]<=({1'b0,xmax[i]}-{1'b0,xmin[i]}+12'd1)*({1'b0,ymax[i]}-{1'b0,ymin[i]}+11'd1);
                    end
                    state<=1;component<=0;
                end
            end else if(seen && I_valid) begin
                if(pixels<WIDTH*HEIGHT) begin
                    pixels<=pixels+4;
                    if(x==WIDTH-4) begin x<=0;y<=y+1'b1;end else x<=x+4;
                    for(i=0;i<2;i=i+1) begin
                        area[i]<=next_area[i];sx[i]<=next_sx[i];sy[i]<=next_sy[i];
                        xmin[i]<=next_xmin[i];xmax[i]<=next_xmax[i];
                        ymin[i]<=next_ymin[i];ymax[i]<=next_ymax[i];
                    end
                end else frame_bad<=1;
            end
            if(!sof) case(state)
            1: begin
                if(counts[0]==0 || counts[1]==0) begin result[32]<=0;result[36:33]<=2;state<=5;end
                else if(counts[0]<AREA_MIN || counts[1]<AREA_MIN || counts[0]>AREA_MAX || counts[1]>AREA_MAX) begin
                    result[32]<=0;result[36:33]<=3;state<=5;
                end else if(counts[0]*100<box_area[0]*FILL_PERCENT_MIN || counts[1]*100<box_area[1]*FILL_PERCENT_MIN) begin
                    result[32]<=0;result[36:33]<=4;state<=5;
                end else state<=2;
            end
            2: begin
                quotient<={1'b0,nums[component]};remainder<=0;
                denominator<=counts[component[1]];bits_left<=32;state<=3;
            end
            3: begin
                quotient<=qnext;remainder<=subtract?trial-denominator:trial;bits_left<=bits_left-1'b1;
                if(bits_left==1) begin
                    case(component)
                    0:result[47:37]<=qnext[10:0];1:result[57:48]<=qnext[9:0];
                    2:result[68:58]<=qnext[10:0];3:result[78:69]<=qnext[9:0];
                    endcase
                    if(component==3) state<=5;else begin component<=component+1'b1;state<=2;end
                end
            end
            5:begin O_meta<=result;O_valid<=1;state<=0;end
            default:state<=0;
            endcase
        end
    end
endmodule
`default_nettype wire
