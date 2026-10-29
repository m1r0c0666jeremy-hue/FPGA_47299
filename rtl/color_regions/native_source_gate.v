// A crop is not a source frame. Publish only after the original 1944-row frame
// and the demosaic output both finish with the same ID. Failed tail rows may
// arrive after all cropped RGB and detector pixels have already been produced.
`default_nettype none
module native_source_gate #(parameter GROUPS=2592*1944/4)(
 input wire clk,rst_n,begin_frame,input wire [31:0] begin_id,
 input wire verdict,verdict_good,input wire [31:0] verdict_id,
 input wire full_sof,full_valid,input wire [32:0] full_tag,
 input wire output_ready,output wire output_valid,output wire output_good,
 output wire [31:0] output_id,output reg good_toggle,bad_toggle);
 reg [31:0] ids[0:3];reg [3:0] known,seen,good,pixels_done,reported,measured,failed;
 reg [31:0] pixel_id;reg pixel_active;reg [20:0] count;
 reg found;reg [1:0] selected;integer i,j;
 always @*begin found=0;selected=0;
 for(i=3;i>=0;i=i-1)if(known[i] && seen[i] && !reported[i] &&
   (!good[i] || pixels_done[i]))begin found=1;selected=i;end end
 assign output_valid=found;assign output_good=good[selected];assign output_id=ids[selected];
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin known<=0;seen<=0;good<=0;pixels_done<=0;reported<=0;measured<=0;failed<=0;
  pixel_id<=0;pixel_active<=0;count<=0;good_toggle<=0;bad_toggle<=0;
  for(j=0;j<4;j=j+1)ids[j]<=0;
 end else begin
  for(j=0;j<4;j=j+1)if(known[j] && seen[j] && !measured[j] && (!good[j] || pixels_done[j]))begin
   measured[j]<=1;if(good[j])good_toggle<=~good_toggle;else bad_toggle<=~bad_toggle;
  end
  if(found && output_ready)reported[selected]<=1;
  if(full_sof)begin pixel_active<=full_tag[32];pixel_id<=full_tag[31:0];count<=full_valid?1:0;end
  else if(full_valid && pixel_active && full_tag[31:0]==pixel_id)begin
   if(count<GROUPS)count<=count+1'b1;
   if(count==GROUPS-1 && known[pixel_id[1:0]] && ids[pixel_id[1:0]]==pixel_id)
    pixels_done[pixel_id[1:0]]<=1;
  end
  if(verdict && known[verdict_id[1:0]] && ids[verdict_id[1:0]]==verdict_id)begin
   seen[verdict_id[1:0]]<=1;good[verdict_id[1:0]]<=verdict_good && !failed[verdict_id[1:0]];
   if(!verdict_good)begin
    failed[verdict_id[1:0]]<=1;
    if(good[verdict_id[1:0]])begin reported[verdict_id[1:0]]<=0;measured[verdict_id[1:0]]<=0;end
   end
  end
  // A source verdict cannot erase an ISP overflow, even on the same clock.
  if(full_valid && !full_sof && pixel_active && full_tag[31:0]==pixel_id && count>=GROUPS &&
     known[pixel_id[1:0]] && ids[pixel_id[1:0]]==pixel_id)begin
   failed[pixel_id[1:0]]<=1;good[pixel_id[1:0]]<=0;seen[pixel_id[1:0]]<=1;
   if(!failed[pixel_id[1:0]])begin reported[pixel_id[1:0]]<=0;measured[pixel_id[1:0]]<=0;end
  end
  if(begin_frame)begin
   ids[begin_id[1:0]]<=begin_id;known[begin_id[1:0]]<=1;seen[begin_id[1:0]]<=0;
   good[begin_id[1:0]]<=0;pixels_done[begin_id[1:0]]<=0;reported[begin_id[1:0]]<=0;measured[begin_id[1:0]]<=0;failed[begin_id[1:0]]<=0;
  end
 end end
endmodule
`default_nettype wire
