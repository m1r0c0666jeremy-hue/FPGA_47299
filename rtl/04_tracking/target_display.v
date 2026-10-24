// Commit the selected source-frame metadata and viewport in one pixel-domain
// transaction during vertical blanking. No unmatched/stale tip drives the ROI.
`default_nettype none
module target_display #(parameter STALE_DISPLAY_FRAMES=15)(
    input wire I_clk,I_rst_n,I_vs,I_de,I_snapshot,
    input wire [290:0] I_data,
    input wire I_tracking,I_show,I_conflict,I_live,
    input wire [7:0] I_session,
    input wire [1:0] I_zoom,I_mode,
    output reg O_commit,output reg [1:0] O_bank,
    output reg [31:0] O_frame_id,
    output reg [10:0] O_cx,O_x0,
    output reg [9:0] O_cy,O_y0,
    output reg [1:0] O_zoom,O_mode,
    output reg [255:0] O_meta,
    output reg O_show,output wire O_tip_valid,
    output wire [2:0] O_state,input wire I_pair,output reg O_pair,
    output wire O_detection_valid
);
    reg ever_enabled,ever_locked;
    reg [7:0] active_session;
    reg vs_d,in_blank;
    reg [7:0] age;
    reg [10:0] cx,nx;
    reg [9:0] cy,ny;
    wire fresh=(I_data[287:256]!=O_frame_id) || age<STALE_DISPLAY_FRAMES;
    wire associated=I_tracking && fresh && I_data[290] &&
                   I_data[242:235]==I_session && I_data[243]==I_pair && I_data[244] && I_data[31:0]==I_data[287:256];
    wire qualified=associated && I_data[32];
    reg active_detection;
    assign O_detection_valid=I_tracking && active_detection && active_session==I_session &&
        O_meta[243]==I_pair && O_meta[244] && I_live && age<STALE_DISPLAY_FRAMES;
    assign O_tip_valid=I_tracking && active_session==I_session && O_meta[243]==I_pair && O_meta[244] && O_meta[32] && I_live && age<STALE_DISPLAY_FRAMES;
    assign O_state=I_conflict?3'd5:!I_live?3'd6:
                   !I_tracking?(ever_enabled?3'd4:3'd0):O_tip_valid?3'd2:ever_locked?3'd3:3'd1;
    always @* begin
        cx=qualified?I_data[89:79]:O_cx;cy=qualified?I_data[99:90]:O_cy;
        nx=0;ny=O_y0;
        case(I_zoom)
        0:begin
            if(O_zoom!=0) ny=cy<312?0:cy>408?96:cy-312;
            else if(cy<O_y0+32) ny=cy<32?0:cy-32;
            else if(cy>O_y0+591) ny=cy>687?96:cy-591;
        end
        1:begin nx=cx<320?0:cx>960?640:cx-320;ny=cy<156?0:cy>564?408:cy-156;end
        default:begin nx=cx<160?0:cx>1120?960:cx-160;ny=cy<78?0:cy>642?564:cy-78;end
        endcase
    end
    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n) begin
            O_commit<=0;O_bank<=0;O_frame_id<=0;O_cx<=640;O_cy<=360;O_x0<=0;O_y0<=48;
            O_zoom<=0;O_mode<=0;O_meta<=0;O_show<=1;O_pair<=0;active_session<=0;active_detection<=0;
            ever_enabled<=0;ever_locked<=0;vs_d<=0;in_blank<=0;age<=0;
        end else begin
            vs_d<=I_vs;O_commit<=0;
            if(I_vs&&!vs_d) begin O_show<=I_show;O_pair<=I_pair;in_blank<=1;if(age<255)age<=age+1'b1;end
            if(I_de) in_blank<=0;
            if(I_tracking) ever_enabled<=1;
            if(!I_tracking || active_session!=I_session) ever_locked<=0;
            if(I_snapshot && in_blank && !I_de) begin
                in_blank<=0;O_commit<=1;O_bank<=I_data[289:288];O_frame_id<=I_data[287:256];
                O_cx<=cx;O_cy<=cy;O_x0<=nx;O_y0<=ny;O_zoom<=I_zoom;O_mode<=I_mode;
                O_meta<=I_data[255:0];O_meta[32]<=qualified;
                active_detection<=associated;
                active_session<=I_session;
                if(I_data[287:256]!=O_frame_id) age<=0;
                if(qualified) ever_locked<=1;
            end
        end
    end
endmodule
`default_nettype wire
