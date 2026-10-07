// Bundled-data CDC: hold payload until acknowledgement returns. Both domains
// share asynchronous assertion; each receives locally synchronized release.
`default_nettype none
module target_mailbox #(parameter WIDTH=256)(
    input wire S_clk,S_rst_n,S_send,
    input wire [WIDTH-1:0] S_data,
    output wire S_ready,
    input wire D_clk,D_rst_n,
    output reg D_valid,
    output reg [WIDTH-1:0] D_data
);
    reg request,ack;
    reg [WIDTH-1:0] payload;
    (* async_reg="true", syn_preserve=1 *) reg ack1,ack2,req1,req2,req3;
    assign S_ready=request==ack2;
    always @(posedge S_clk or negedge S_rst_n) begin
        if(!S_rst_n) begin request<=0;payload<=0;ack1<=0;ack2<=0;end
        else begin
            ack1<=ack;ack2<=ack1;
            if(S_send && S_ready) begin payload<=S_data;request<=~request;end
        end
    end
    always @(posedge D_clk or negedge D_rst_n) begin
        if(!D_rst_n) begin req1<=0;req2<=0;req3<=0;ack<=0;D_valid<=0;D_data<=0;end
        else begin
            req1<=request;req2<=req1;req3<=req2;D_valid<=0;
            if(req3!=ack) begin D_data<=payload;D_valid<=1;ack<=req3;end
        end
    end
endmodule
`default_nettype wire
