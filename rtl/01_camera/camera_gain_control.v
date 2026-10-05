// Bundled-data toggle mailbox: source holds direction until acknowledgement.
// ACK means step accepted; I2C delivery follows the existing configuration handshake.
`default_nettype none
module camera_gain_control (
    input wire I_clk, I_rst_n, I_req, I_up,
    input wire I_cam_done, I_ae_done,
    output reg O_ack, O_ae_req,
    output wire [15:0] O_ae,
    output reg [15:0] O_ag
);
    (* async_reg="true", syn_preserve=1 *) reg req1, req2, req3, up1, up2;
    (* async_reg="true", syn_preserve=1 *) reg [1:0] reset_bridge;
    wire local_rst_n=reset_bridge[1];
    always @(posedge I_clk or negedge I_rst_n)
        if(!I_rst_n) reset_bridge<=0; else reset_bridge<={reset_bridge[0],1'b1};
    reg [6:0] target;
    reg initialized;
    assign O_ae=16'd1990;
    always @(posedge I_clk or negedge local_rst_n) begin
        if(!local_rst_n) begin
            req1<=0; req2<=0; req3<=0; up1<=0; up2<=0;
            O_ack<=0; target<=90; O_ag<=90; O_ae_req<=0; initialized<=0;
        end else begin
            req1<=I_req; req2<=req1; req3<=req2; up1<=I_up; up2<=up1; O_ae_req<=0;
            if(req3!=O_ack) begin
                O_ack<=req3;
                if(up2) begin if(target<105) target<=target+1'b1; end
                else if(target>16) target<=target-1'b1;
            end
            if(!O_ae_req && I_cam_done && I_ae_done && (!initialized || O_ag!={9'd0,target})) begin
                O_ag<={9'd0,target}; O_ae_req<=1; initialized<=1;
            end
        end
    end
endmodule
`default_nettype wire
