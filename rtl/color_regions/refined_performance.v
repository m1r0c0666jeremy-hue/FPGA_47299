// Endpoint is the exact clock edge consumed by the HDMI encoder. Exposure and
// monitor scan/response are outside this measurement. Unsigned wrap is allowed
// only within half the 32-bit microsecond range.
module refined_performance(input wire clk,rst_n,vs,de,live,
 input wire [31:0] now_us,image_us,image_id,latest_id,input wire time_valid,
 output reg valid,output reg [31:0] latency_us,frame_age);
reg vs_old,seen;
wire [31:0] elapsed=now_us-image_us,age=latest_id-image_id;
always @(posedge clk or negedge rst_n)
if(!rst_n)begin vs_old<=0;seen<=0;valid<=0;latency_us<=0;frame_age<=0;end
else begin
 vs_old<=vs;if(vs && !vs_old)begin seen<=0;valid<=0;end
 if(!live)valid<=0;
 if(de && !seen)begin seen<=1;latency_us<=elapsed;frame_age<=age;
 valid<=live && time_valid && !elapsed[31] && !age[31];end
end
endmodule
