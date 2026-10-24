// KEY2 gain, KEY3 tracking toggle, KEY4 zoom. No manual cursor movement.
`default_nettype none
module target_controls #(parameter CYCLES_PER_MS=75000,DEBOUNCE_MS=20,LONG_PRESS_MS=1000)(
    input wire I_clk,I_rst_n,input wire [2:0] I_keys_n,
    input wire [1:0] I_ui_switch,input wire I_gain_ack,
    output reg O_gain_req,O_gain_up,output reg [1:0] O_zoom,
    output reg O_tracking,output reg O_show,
    output reg [7:0] O_session,output wire O_conflict,output reg O_pair
);
    (* async_reg="true", syn_preserve=1 *) reg [2:0] keys1,keys2;
    (* async_reg="true", syn_preserve=1 *) reg [1:0] sw1,sw2;
    (* async_reg="true", syn_preserve=1 *) reg ack1,ack2;
    reg [2:0] kc,keys,active;
    reg [1:0] sc,switches,direction;
    reg [7:0] ks,ss;
    reg [19:0] ms;
    reg [9:0] repeat_count;
    reg armed,key3_ready;
    reg key3_pending,key3_long;
    reg [15:0] key3_ms;
    wire tick=ms==CYCLES_PER_MS-1;
    wire [2:0] pressed=~keys;
    wire single_key=pressed==1 || pressed==2 || pressed==4;
    wire start=pressed!=active;
    wire [1:0] action_direction=start?switches:direction;
    wire pair_change=O_pair!=switches[1];
    wire short_release=key3_pending && !key3_long && pressed==0 && key3_ms<LONG_PRESS_MS-1;
    assign O_conflict=pressed!=0 && !single_key;
    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n) begin keys1<=7;keys2<=7;sw1<=0;sw2<=0;ack1<=0;ack2<=0;end
        else begin keys1<=I_keys_n;keys2<=keys1;sw1<=I_ui_switch;sw2<=sw1;ack1<=I_gain_ack;ack2<=ack1;end
    end
    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n) begin
            kc<=7;keys<=7;active<=0;sc<=0;switches<=0;direction<=0;ks<=0;ss<=0;ms<=0;
            repeat_count<=0;armed<=0;key3_ready<=0;O_gain_req<=0;O_gain_up<=0;
            O_zoom<=0;O_tracking<=0;O_session<=0;O_show<=1;O_pair<=0;
            key3_pending<=0;key3_long<=0;key3_ms<=0;
        end else begin
            if(tick) ms<=0;else ms<=ms+1'b1;
            if(tick) begin
                if(keys2!=kc) begin kc<=keys2;ks<=0;end
                else if(ks<DEBOUNCE_MS) begin ks<=ks+1'b1;if(ks==DEBOUNCE_MS-1) keys<=kc;end
                if(sw2!=sc) begin sc<=sw2;ss<=0;end
                else if(ss<DEBOUNCE_MS) begin ss<=ss+1'b1;if(ss==DEBOUNCE_MS-1) switches<=sc;end
                if(ks==DEBOUNCE_MS && keys==7) begin armed<=1;key3_ready<=1;end
                if(pair_change) O_pair<=switches[1];
                if(pair_change || short_release) O_session<=O_session+1'b1;
                if(short_release) O_tracking<=~O_tracking;
                // A gesture is consumed by conflict or the first long event.
                if(O_conflict || (key3_pending && pressed!=0 && pressed!=2)) begin
                    key3_ready<=0;key3_pending<=0;key3_ms<=0;
                end else if(key3_pending) begin
                    if(!key3_long && key3_ms>=LONG_PRESS_MS-1) begin
                        O_show<=~O_show;key3_long<=1;
                    end else if(!key3_long) key3_ms<=key3_ms+1'b1;
                    if(pressed==0) begin key3_pending<=0;key3_ms<=0;end
                end
                if(!armed || !single_key) begin active<=0;repeat_count<=0;end
                else begin
                    active<=pressed;
                    if(start) begin direction<=switches;repeat_count<=0;end
                    else repeat_count<=repeat_count+1'b1;
                    case(pressed)
                    1:if(start || repeat_count==149) begin
                        repeat_count<=0;
                        if(O_gain_req==ack2) begin O_gain_up<=action_direction[0];O_gain_req<=~O_gain_req;end
                    end
                    2:begin
                        repeat_count<=0;
                        if(start && key3_ready) begin
                            key3_pending<=1;key3_long<=0;key3_ms<=0;key3_ready<=0;
                        end
                    end
                    4:if(start || repeat_count==599) begin
                        repeat_count<=0;
                        if(action_direction[0]) begin if(O_zoom<2) O_zoom<=O_zoom+1'b1;end
                        else if(O_zoom>0) O_zoom<=O_zoom-1'b1;
                    end
                    endcase
                end
            end
        end
    end
endmodule
`default_nettype wire
