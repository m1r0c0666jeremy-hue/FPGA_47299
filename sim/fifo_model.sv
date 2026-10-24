// SIMULATION ONLY. Ideal queued FIFO for testing video_in/video_out control.
// Not a model of PH1P35 RAM timing, synchronizer latency, CDC safety, or PHY.
`timescale 1ns/1ps
module w128_d512_fifo(
    input rst,clkw,clkr,we, input [127:0] di, input re,
    output reg [127:0] dout=0, output reg valid=0,
    output full_flag,empty_flag,afull,aempty,
    output [8:0] wrusedw,rdusedw
);
    reg [127:0] mem[0:511];
    integer wp=0,rp=0,overflow_attempts=0,underflow_attempts=0;
    wire [31:0] count=wp-rp;
    assign full_flag=count>=510;
    assign empty_flag=count==0;
    assign afull=count>=253;
    assign aempty=count<=2;
    assign wrusedw=count[8:0];
    assign rdusedw=count[8:0];
    always @(posedge clkw or posedge rst) begin
        if(rst) wp<=0;
        else if(we) begin
            if(full_flag) overflow_attempts<=overflow_attempts+1;
            else begin mem[wp%512]<=di; wp<=wp+1; end
        end
    end
    always @(posedge clkr or posedge rst) begin
        if(rst) begin rp<=0; dout<=0; valid<=0; end
        else begin
            valid<=0;
            if(re) begin
                if(empty_flag) underflow_attempts<=underflow_attempts+1;
                else begin dout<=mem[rp%512]; rp<=rp+1; valid<=1; end
            end
        end
    end
endmodule
