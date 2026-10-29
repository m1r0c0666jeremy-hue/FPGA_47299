// Check physical packet length independently of the vendor unpacker's counter.
// This checks geometry/packet termination; CSI ECC and payload CRC are not decoded.
`default_nettype none
module native_csi_guard #(parameter ROW_BYTES=3240)(
 input wire clk,rst_n,valid,input wire [15:0] data,input wire lane_error,
 output reg packet_error,output reg frame_end);
 reg active;reg [7:0] kind;reg [15:0] count,word_count;
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin active<=0;kind<=0;count<=0;word_count<=0;packet_error<=0;frame_end<=0;end
 else begin
  packet_error<=lane_error;frame_end<=0;
  if(valid)begin
   if(!active)begin active<=1;kind<=data[15:8];word_count<={8'd0,data[7:0]};count<=1;end
   else begin
    if(count==1)word_count<={data[15:8],word_count[7:0]};
    if(count!=65535)count<=count+1'b1;else packet_error<=1;
   end
  end else if(active)begin
   active<=0;
   if(kind==8'h2b)begin
    if(word_count!=ROW_BYTES || count!=(ROW_BYTES+6)/2)packet_error<=1;
   end else if(kind==0 || kind==1)begin
    if(count!=2)packet_error<=1;
    else if(kind==1)frame_end<=1;
   end else packet_error<=1;
  end
 end end
endmodule
`default_nettype wire
