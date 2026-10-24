// ScalingTest UI. All times are milliseconds; synchronizers run every clock.
`default_nettype none
module scaling_controls #(
    parameter integer CYCLES_PER_MS = 75000,
    parameter integer DEBOUNCE_MS = 20
)(
    input wire I_clk, I_rst_n,
    input wire [2:0] I_keys_n,
    input wire [1:0] I_ui_switch,
    input wire I_gain_ack,
    output reg O_gain_req, O_gain_up,
    output reg [10:0] O_cx,
    output reg [9:0] O_cy,
    output reg [1:0] O_zoom,
    output wire [1:0] O_direction,
    output wire [2:0] O_status
);
    reg [2:0] keys1, keys2, key_candidate, keys;
    reg [1:0] sw1, sw2, sw_candidate, switches;
    (* async_reg="true", syn_preserve=1 *) reg ack1, ack2;
    reg armed;
    reg [19:0] ms_count;
    reg [7:0] key_stable, sw_stable;
    reg [2:0] active;
    reg [1:0] direction;
    reg [15:0] age;
    reg [9:0] repeat_count;
    reg boundary;
    wire tick = ms_count == CYCLES_PER_MS-1;
    wire [2:0] pressed = ~keys;
    wire single_key = pressed==1 || pressed==2 || pressed==4;
    wire start = pressed != active;
    wire [1:0] action_direction = start ? switches : direction;
    wire action = armed && single_key && (start ||
        (pressed==1 && repeat_count==149) ||
        (pressed==2 && ((age==399) || (age>=400 && repeat_count==79))) ||
        (pressed==4 && repeat_count==599));
    wire [3:0] step = (!start && age>=999) ? 4'd10 : 4'd2;
    assign O_direction = (armed && pressed==2 && active==2) ? direction : switches;
    // 0 idle, 1 moving, 2 edge, 3 conflict. 4 reserved for video-not-ready.
    assign O_status = (!armed || pressed==0) ? 0 : !single_key ? 3 :
                      pressed==2 ? (boundary ? 2 : 1) : 0;
    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n) begin
            keys1<=7; keys2<=7; sw1<=0; sw2<=0; ack1<=0; ack2<=0;
        end else begin
            keys1<=I_keys_n; keys2<=keys1; sw1<=I_ui_switch; sw2<=sw1;
            ack1<=I_gain_ack; ack2<=ack1;
        end
    end
    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n) begin
            ms_count<=0; key_candidate<=7; keys<=7; sw_candidate<=0; switches<=0;
            key_stable<=0; sw_stable<=0; armed<=0; active<=0;
            direction<=0; age<=0; repeat_count<=0; boundary<=0;
            O_cx<=640; O_cy<=360; O_zoom<=0; O_gain_req<=0; O_gain_up<=0;
        end else begin
            if(tick) ms_count<=0; else ms_count<=ms_count+1'b1;
            if(tick) begin
                if(keys2!=key_candidate) begin key_candidate<=keys2; key_stable<=0; end
                else if(key_stable<DEBOUNCE_MS) begin
                    key_stable<=key_stable+1'b1;
                    if(key_stable==DEBOUNCE_MS-1) keys<=key_candidate;
                end
                if(sw2!=sw_candidate) begin sw_candidate<=sw2; sw_stable<=0; end
                else if(sw_stable<DEBOUNCE_MS) begin
                    sw_stable<=sw_stable+1'b1;
                    if(sw_stable==DEBOUNCE_MS-1) switches<=sw_candidate;
                end
                if(key_stable==DEBOUNCE_MS && keys==7) armed<=1;
                if(!armed || !single_key) begin
                    active<=0; age<=0; repeat_count<=0; boundary<=0;
                end else begin
                    active<=pressed;
                    if(start) begin direction<=switches; age<=0; repeat_count<=0; boundary<=0; end
                    else begin
                        if(age!=65535) age<=age+1'b1;
                        if(action || (pressed==2 && age<399)) repeat_count<=0;
                        else repeat_count<=repeat_count+1'b1;
                    end
                    if(action) begin
                        case(pressed)
                        1: if(O_gain_req==ack2) begin
                            O_gain_up<=action_direction[1]; O_gain_req<=~O_gain_req;
                        end
                        2: begin
                            boundary<=0;
                            case(action_direction)
                            0: if(O_cy+step>=719) begin O_cy<=719; boundary<=1; end else O_cy<=O_cy+step;
                            1: if(O_cx+step>=1279) begin O_cx<=1279; boundary<=1; end else O_cx<=O_cx+step;
                            2: if(O_cx<=step) begin O_cx<=0; boundary<=1; end else O_cx<=O_cx-step;
                            3: if(O_cy<=step) begin O_cy<=0; boundary<=1; end else O_cy<=O_cy-step;
                            endcase
                        end
                        4: if(action_direction[0]) begin if(O_zoom<2) O_zoom<=O_zoom+1'b1; end
                           else if(O_zoom>0) O_zoom<=O_zoom-1'b1;
                        endcase
                    end
                end
            end
        end
    end
endmodule
`default_nettype wire
