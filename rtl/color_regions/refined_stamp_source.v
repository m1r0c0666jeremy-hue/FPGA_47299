// Full 32-bit SOF identity traverses the numerical pipeline. No inference from
// output frame counts, and no short-token alias after malformed input headers.
module refined_stamp_source(input wire clk,rst_n,input wire [31:0] time_gray,
 input wire csi_sof,raw10_sof,axis_sof,input wire [32:0] raw_tag,detect_tag,
 output wire [32:0] axis_tag,output reg [31:0] latest_gray,
 output wire raw_known,detect_known,output wire [31:0] detect_us,now_us);
reg [31:0] source_sequence,ids[0:3],stamps[0:3];reg [3:0] known;
reg [32:0] axis_hold;reg axis_used;
wire [31:0] next_id=source_sequence+1'b1;
refined_gray_sync time_sync(clk,rst_n,time_gray,now_us);
assign axis_tag=raw10_sof?{1'b1,source_sequence}:axis_used?33'd0:axis_hold;
assign raw_known=raw_tag[32] && known[raw_tag[1:0]] && ids[raw_tag[1:0]]==raw_tag[31:0];
assign detect_known=detect_tag[32] && known[detect_tag[1:0]] && ids[detect_tag[1:0]]==detect_tag[31:0];
assign detect_us=stamps[detect_tag[1:0]];
always @(posedge clk or negedge rst_n)
if(!rst_n)begin source_sequence<=0;known<=0;axis_hold<=0;axis_used<=1;latest_gray<=0;end
else begin
 if(csi_sof)begin source_sequence<=next_id;latest_gray<=next_id^(next_id>>1);
 ids[next_id[1:0]]<=next_id;stamps[next_id[1:0]]<=now_us;known[next_id[1:0]]<=1;end
 if(raw10_sof)begin axis_hold<={1'b1,source_sequence};axis_used<=axis_sof;end
 else if(axis_sof)axis_used<=1;
end
endmodule
