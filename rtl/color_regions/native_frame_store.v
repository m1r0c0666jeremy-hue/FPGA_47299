// Select the ACTUAL image bank together with matching functional metadata.
// A completed empty result wins over an older non-empty result.
`default_nettype none
module native_frame_store #(parameter WORDS=691200,V4=0,MW=V4?768:640,SW=V4?852:675)(
 input wire I_clk,I_rst_n,I_begin,input wire [1:0] I_bank,input wire [31:0] I_frame_id,
 input wire I_write,input wire [24:0] I_addr,input wire I_result,input wire [MW-1:0] I_meta,
 input wire I_snapshot,input wire [9:0] I_command,
 output reg O_snapshot,output reg [SW-1:0] O_data,output wire O_selected_good,
 input wire [31:0] I_frame_us,input wire [15:0] I_epoch,input wire I_time_valid,I_invalidate,
 input wire I_source_verdict,I_source_good,input wire [31:0] I_source_id
);
 reg [31:0] ids[0:3],stamps[0:3];reg [15:0] epochs[0:3];reg [3:0] timed;reg [MW-1:0] metadata[0:3];
 reg [3:0] known,complete,has_meta;reg [3:0] source_seen,source_good,qualified;
 reg selected_once;reg [1:0] selected;reg [31:0] selected_id;
 reg [3:0] write_bad;reg [19:0] count[0:3];reg [24:0] expected[0:3];
 // Accepted FIFO commands can outlive a camera bank switch. Commit each actual
 // PAXI write against its address bank, never against the latest camera bank.
 wire [3:0] committing_each={I_addr>=21000000,
  I_addr>=14000000 && I_addr<21000000,
  I_addr>=7000000 && I_addr<14000000,I_addr<7000000};
 reg [3:0] co,hit,eligible;
 // A bank cannot be selected until its ID comparison flags have settled.
 // Normal complete frames take 172800 writes, far longer than this one clock.
 reg [3:0] settled_first;reg [3:0] id_settled,newer[0:3],predecessor[0:3];wire [3:0] select_co=co & id_settled & qualified;
 integer ai,aj;
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin id_settled<=0;settled_first<=0;for(ai=0;ai<4;ai=ai+1)begin newer[ai]<=0;predecessor[ai]<=0;end end
 else begin
 settled_first<=known;id_settled<=settled_first;if(I_begin)begin settled_first[I_bank]<=0;id_settled[I_bank]<=0;end
 if(V4 && I_invalidate)begin settled_first<=0;id_settled<=0;end
 for(ai=0;ai<4;ai=ai+1)for(aj=0;aj<4;aj=aj+1)begin
 newer[ai][aj]<=$signed(ids[ai]-ids[aj])>0;
 predecessor[ai][aj]<=ids[ai]+32'd1==ids[aj];
 end end end
 reg [1:0] newest_table[0:15];integer mi;reg [1:0] ml,mh;
 always @(posedge I_clk)for(mi=0;mi<16;mi=mi+1)begin
 ml=(mi&2) && (!(mi&1) || newer[1][0])?1:0;
 mh=(mi&8) && (!(mi&4) || newer[3][2])?3:2;
 newest_table[mi]<=((mi>>mh)&1) && (!((mi>>ml)&1) || newer[mh][ml])?mh:ml;
 end
 reg [9:0] tags[0:3];
 reg found,new_result_found;reg [1:0] newest,chosen,write_slot,lo,hi;integer i;
 wire result_ok=I_result && I_meta[255] && I_meta[415:413]==(V4?4:3) && !(V4 && I_invalidate);
 wire [9:0] result_tag={I_meta[243],I_meta[242:235],I_meta[244]};
 function [24:0] base_for;input [1:0] b;begin
  case(b)0:base_for=0;1:base_for=7000000;2:base_for=14000000;3:base_for=21000000;endcase
 end endfunction
 assign O_selected_good=selected_once && known[selected] && complete[selected] && source_seen[selected] && source_good[selected] && !(I_source_verdict && I_source_id==selected_id && !I_source_good) && ids[selected]==selected_id && !(I_begin && I_bank==selected) && !(V4 && I_invalidate);
 always @*begin
  qualified=source_seen & source_good;
  for(i=0;i<4;i=i+1)if(I_source_verdict && known[i] && ids[i]==I_source_id)qualified[i]=I_source_good && (!source_seen[i] || source_good[i]);
  co=complete;hit=0;eligible=0;write_slot=0;
  for(i=0;i<4;i=i+1)begin
   hit[i]=result_ok && known[i] && ids[i]==I_meta[31:0] && !(I_begin && I_bank==i);
   if(V4)hit[i]=hit[i] && epochs[i]==I_meta[719:704] && timed[i] && I_meta[720] && stamps[i]==I_meta[671:640];
   if(hit[i])write_slot=i;
  end
  for(i=0;i<4;i=i+1)if(I_write && known[i] && committing_each[i])begin
   if(I_addr!=expected[i] || count[i]>=WORDS)co[i]=0;
   else if(count[i]==WORDS-1 && !write_bad[i])co[i]=1;
  end
  if(I_begin)co[I_bank]=0;
  if(V4 && I_invalidate)co=0;
  for(i=0;i<4;i=i+1)eligible[i]=select_co[i] && known[i] &&
    (hit[i]?result_tag==I_command:has_meta[i] && tags[i]==I_command);
  // Three fixed comparisons replace nested variable-index comparison trees.
  lo=select_co[1] && (!select_co[0] || newer[1][0])?1:0;
  hi=select_co[3] && (!select_co[2] || newer[3][2])?3:2;
  newest=newest_table[select_co];
  found=|select_co;
  chosen=newest;new_result_found=0;
  for(i=0;i<4;i=i+1)if(found && eligible[i] && predecessor[i][newest])begin chosen=i;new_result_found=1;end
  if(found && eligible[newest])begin chosen=newest;new_result_found=1;end
 end
 // Data RAM has one write address and no reset. has_meta hides old contents.
 always @(posedge I_clk)if(|hit)metadata[write_slot]<=I_meta;
 integer j;
 always @(posedge I_clk or negedge I_rst_n)begin
  if(!I_rst_n)begin
   source_seen<=0;source_good<=0;known<=0;complete<=0;has_meta<=0;write_bad<=0;selected_once<=0;timed<=0;
   selected<=0;selected_id<=0;O_snapshot<=0;O_data<=0;
   for(j=0;j<4;j=j+1)begin ids[j]<=0;tags[j]<=0;count[j]<=0;expected[j]<=0;end
  end else begin
   complete<=co;
   if(|hit)begin has_meta[write_slot]<=1;tags[write_slot]<=result_tag;end
   O_snapshot<=0;
   for(j=0;j<4;j=j+1)if(I_write && known[j] && committing_each[j])begin
    if(I_addr!=expected[j] || count[j]>=WORDS)write_bad[j]<=1;
    else begin expected[j]<=expected[j]+8;count[j]<=count[j]+1'b1;end
   end
   for(j=0;j<4;j=j+1)if(I_source_verdict && known[j] && ids[j]==I_source_id)begin
     source_seen[j]<=1;source_good[j]<=I_source_good && (!source_seen[j] || source_good[j]);
   end
   if(I_begin)begin
     source_seen[I_bank]<=0;source_good[I_bank]<=0;
     count[I_bank]<=0;expected[I_bank]<=base_for(I_bank);write_bad[I_bank]<=I_write && committing_each[I_bank];
     known[I_bank]<=1;has_meta[I_bank]<=0;ids[I_bank]<=I_frame_id;
     stamps[I_bank]<=I_frame_us;epochs[I_bank]<=I_epoch;timed[I_bank]<=I_time_valid;
   end
   if(I_snapshot)begin
    selected<=chosen;selected_id<=ids[chosen];selected_once<=found;O_snapshot<=1;
    O_data<=0;O_data[MW+:35]<={found,chosen,ids[chosen]};
    if(V4)O_data[SW-1-:49]<={found && timed[chosen],epochs[chosen],stamps[chosen]};
    if(found && new_result_found)O_data[MW-1:0]<=hit[chosen]?I_meta:metadata[chosen];
   end
   if(V4 && I_invalidate)begin source_seen<=0;source_good<=0;known<=0;complete<=0;has_meta<=0;selected_once<=0;timed<=0;end
  end
 end
endmodule
`default_nettype wire
