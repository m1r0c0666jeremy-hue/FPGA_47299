// Select the ACTUAL image bank together with matching functional metadata.
// A completed empty result wins over an older non-empty result.
`default_nettype none
module regions_frame_store #(parameter WORDS=172800)(
 input wire I_clk,I_rst_n,I_begin,input wire [1:0] I_bank,input wire [31:0] I_frame_id,
 input wire I_write,input wire [24:0] I_addr,input wire I_result,input wire [415:0] I_meta,
 input wire I_snapshot,input wire [9:0] I_command,
 output reg O_snapshot,output reg [450:0] O_data,output wire O_selected_good
);
 reg [31:0] ids[0:3];reg [415:0] metadata[0:3];
 reg [3:0] known,complete,has_meta;
 reg active,write_bad,selected_once;reg [1:0] writing,selected;reg [31:0] selected_id;
 reg [18:0] count;reg [24:0] expected;
 reg [3:0] co,hit,eligible;reg [9:0] tags[0:3];
 reg found,new_result_found;reg [1:0] newest,chosen,write_slot,lo,hi;integer i;
 wire result_ok=I_result && I_meta[255] && I_meta[415:413]==1;
 wire [9:0] result_tag={I_meta[243],I_meta[242:235],I_meta[244]};
 function [24:0] base_for;input [1:0] b;begin
  case(b)0:base_for=0;1:base_for=7000000;2:base_for=14000000;3:base_for=21000000;endcase
 end endfunction
 assign O_selected_good=selected_once && known[selected] && complete[selected] && ids[selected]==selected_id && !(I_begin && I_bank==selected);
 always @*begin
  co=complete;hit=0;eligible=0;write_slot=0;
  for(i=0;i<4;i=i+1)begin
   hit[i]=result_ok && known[i] && ids[i]==I_meta[31:0] && !(I_begin && I_bank==i);
   if(hit[i])write_slot=i;
  end
  if(I_write && active)begin
   if(I_addr!=expected || count>=WORDS)co[writing]=0;
   else if(count==WORDS-1 && !write_bad)co[writing]=1;
  end
  if(I_begin)co[I_bank]=0;
  for(i=0;i<4;i=i+1)eligible[i]=co[i] && known[i] &&
    (hit[i]?result_tag==I_command:has_meta[i] && tags[i]==I_command);
  // Three fixed comparisons replace nested variable-index comparison trees.
  lo=co[1] && (!co[0] || $signed(ids[1]-ids[0])>0)?1:0;
  hi=co[3] && (!co[2] || $signed(ids[3]-ids[2])>0)?3:2;
  newest=co[hi] && (!co[lo] || $signed(ids[hi]-ids[lo])>0)?hi:lo;
  found=|co;
  chosen=newest;new_result_found=0;
  for(i=0;i<4;i=i+1)if(found && eligible[i] && ids[i]+32'd1==ids[newest])begin chosen=i;new_result_found=1;end
  if(found && eligible[newest])begin chosen=newest;new_result_found=1;end
 end
 // Data RAM has one write address and no reset. has_meta hides old contents.
 always @(posedge I_clk)if(|hit)metadata[write_slot]<=I_meta;
 integer j;
 always @(posedge I_clk or negedge I_rst_n)begin
  if(!I_rst_n)begin
   known<=0;complete<=0;has_meta<=0;active<=0;write_bad<=0;selected_once<=0;
   writing<=0;selected<=0;selected_id<=0;count<=0;expected<=0;O_snapshot<=0;O_data<=0;
   for(j=0;j<4;j=j+1)begin ids[j]<=0;tags[j]<=0;end
  end else begin
   complete<=co;
   if(|hit)begin has_meta[write_slot]<=1;tags[write_slot]<=result_tag;end
   O_snapshot<=0;
   if(I_write && active)begin
    if(I_addr!=expected || count>=WORDS)write_bad<=1;
    else begin expected<=expected+8;count<=count+1'b1;end
   end
   if(I_begin)begin
     writing<=I_bank;count<=0;expected<=base_for(I_bank);active<=1;write_bad<=I_write;
     known[I_bank]<=1;has_meta[I_bank]<=0;ids[I_bank]<=I_frame_id;
   end
   if(I_snapshot)begin
    selected<=chosen;selected_id<=ids[chosen];selected_once<=found;O_snapshot<=1;
    O_data<={found,chosen,ids[chosen],416'd0};
    if(found && new_result_found)O_data[415:0]<=hit[chosen]?I_meta:metadata[chosen];
   end
  end
 end
endmodule
`default_nettype wire
