// Two-bank dense DMA runs concurrently with four-pixel row reduction. Physical
// bursts release the camera writer during receive/processing. The line core
// retains zoom, reflection, classification and its immutable RGB banks.
`default_nettype none
module native_read_adapter(
 input wire clk,rst_n,input wire virtual_en,input wire [24:0] virtual_addr,
 output wire virtual_ready,output wire virtual_valid,output wire [127:0] virtual_data,
 output reg [31:0] virtual_accepted,
 input wire [9:0] source_y,input wire [1:0] source_bank,
 input wire [2:0] job_zoom,input wire [10:0] job_x0,input wire [9:0] job_y0,
 input wire write_busy,write_en,ddr_ready,ddr_valid,input wire [127:0] ddr_data,
 output wire read_busy,read_en,output wire [24:0] read_addr,
 input wire unexpected_return,output reg fault);
 localparam IDLE=0,WAIT_DATA=1,LOAD0=5,LOAD1=6,LOAD2=7,LOAD3=8,LOAD4=9,EMIT=10,FLUSH=11,BROKEN=12;
 localparam F_IDLE=0,F_WAIT=1,F_SEND=2,F_RECEIVE=3;
 reg [3:0] state;reg [1:0] fetch_state;reg dense;reg [1:0] bank;
 reg [10:0] base_x;reg [11:0] base_y;reg [9:0] logical_y;
 reg [2:0] fetch_index,process_index;reg [1:0] filled;reg [2:0] slot_index[0:1];
 reg [3:0] slot_offset[0:1];
 reg [7:0] accepted,returned,sent,received,words;
 reg [24:0] first_addr,line_address;
 reg [3:0] byte_offset;reg [6:0] group_index;reg [1:0] quad;
 reg [383:0] pixels,assembly;
 reg [3:0] flush_age;reg [17:0] elapsed;
 (* ram_style="block" *) reg [127:0] scratch[0:511];
 reg [127:0] scratch_q;reg [7:0] scratch_addr;
 wire active=state!=IDLE && state!=BROKEN;
 wire issue=virtual_en && virtual_ready;
 assign virtual_ready=state!=BROKEN && (state==IDLE || accepted<240);
 assign read_busy=fetch_state==F_SEND && !write_busy && !fault;
 assign read_en=fetch_state==F_SEND && !write_busy && !write_en && ddr_ready && !fault;
 assign read_addr=line_address+{14'd0,sent,3'd0};
 function [24:0] base_for;input [1:0] b;begin
 case(b)0:base_for=0;1:base_for=7000000;2:base_for=14000000;3:base_for=21000000;endcase end endfunction
 wire [11:0] candidate_y=dense?base_y:{1'b0,logical_y,1'b0}+fetch_index[0];
 wire [11:0] safe_y=candidate_y>1439?12'd1439:candidate_y;
 // Address unit is 16 bits. 7680 bytes/row -> 3840 units; x is always even.
 wire [24:0] y_address=({13'd0,safe_y}<<12)-({13'd0,safe_y}<<8);
 wire [24:0] x_address=dense?({14'd0,base_x}<<1)+{14'd0,base_x}:
                                      fetch_index[1]?25'd1920:25'd0;
 wire [24:0] raw_address=base_for(bank)+y_address+x_address;
 wire [7:0] group_word=({1'd0,group_index}<<1)+{1'd0,group_index};
 always @*begin
 case(state)
 LOAD1:scratch_addr=group_word+1'b1;
 LOAD2:scratch_addr=group_word+2'd2;
 LOAD3,LOAD4:scratch_addr=group_word+2'd3;
 EMIT:case(quad)
  0:scratch_addr=group_word+3'd4;
  1:scratch_addr=group_word+3'd5;
  default:scratch_addr=group_word+3'd6;
 endcase
 default:scratch_addr=group_word[7:0];
 endcase end
 always @(posedge clk)begin
  if((fetch_state==F_SEND || fetch_state==F_RECEIVE) && ddr_valid)
   scratch[{fetch_index[0],received[7:0]}]<=ddr_data;
  scratch_q<=scratch[{process_index[0],scratch_addr}];
 end
 wire dense_valid=state==EMIT;
 wire [95:0] dense_rgb=pixels[383:288];
 // Share one byte aligner at both first-load and rolling-word boundaries.
 wire [383:0] aligned_pixels=({assembly,scratch_q} << (byte_offset*8)) >> 128;
 wire reduced_sof,reduced_valid;wire [95:0] reduced_rgb;wire [32:0] unused_tag;
 native_downsample2 #(.WIDTH(1280),.HEIGHT(2)) average(
  clk,rst_n,1'b0,state==LOAD0 && !process_index[0] && !dense,dense_valid && !dense,
  dense_rgb,33'd0,reduced_sof,reduced_valid,reduced_rgb,unused_tag);
 wire packed_sof,packed_valid;wire [127:0] packed_data;
 stable_packer pack(clk,rst_n,state==LOAD0 && !process_index[0],
  dense?dense_valid:reduced_valid,dense?dense_rgb:reduced_rgb,packed_sof,packed_valid,packed_data);
 assign virtual_valid=packed_valid && active && !fault;
 assign virtual_data=packed_data;
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin state<=IDLE;fetch_state<=F_IDLE;fetch_index<=0;process_index<=0;filled<=0;
  slot_index[0]<=0;slot_index[1]<=0;slot_offset[0]<=0;slot_offset[1]<=0;
  dense<=0;bank<=0;base_x<=0;base_y<=0;logical_y<=0;
  accepted<=0;returned<=0;sent<=0;received<=0;words<=0;first_addr<=0;line_address<=0;
  byte_offset<=0;group_index<=0;quad<=0;pixels<=0;assembly<=0;flush_age<=0;elapsed<=0;
  fault<=0;virtual_accepted<=0;
 end else begin
  if(issue)begin virtual_accepted<=virtual_accepted+1'b1;accepted<=accepted+1'b1;end
  if(virtual_valid)begin
   returned<=returned+1'b1;
   if(returned>=accepted)begin fault<=1;state<=BROKEN;end
  end
  if(active)begin
   if(elapsed<262143)elapsed<=elapsed+1'b1;
   if(elapsed==133332)begin fault<=1;state<=BROKEN;end
  end
  case(fetch_state)
  F_IDLE:if(active && fetch_index<(dense?1:4) && !filled[fetch_index[0]])begin
   line_address<={raw_address[24:3],3'd0};slot_offset[fetch_index[0]]<={raw_address[2:0],1'b0};
   words<=raw_address[2:0]!=0?8'd241:8'd240;sent<=0;received<=0;fetch_state<=F_WAIT;
  end
  F_WAIT:if(!write_busy && !write_en)fetch_state<=F_SEND;
  F_SEND:if(read_en)begin sent<=sent+1'b1;if(sent==words-1)fetch_state<=F_RECEIVE;end
  F_RECEIVE:begin end
  endcase
  case(state)
  IDLE:if(issue)begin
   first_addr<=virtual_addr;accepted<=1;returned<=0;dense<=job_zoom==2;
   bank<=source_bank;base_x<=job_x0;base_y<={1'b0,job_y0,1'b0}+source_y;
   logical_y<=source_y;fetch_index<=0;process_index<=0;filled<=0;elapsed<=0;state<=WAIT_DATA;
  end
  WAIT_DATA:if(filled[process_index[0]] && slot_index[process_index[0]]==process_index)begin
   byte_offset<=slot_offset[process_index[0]];group_index<=0;state<=LOAD0;
  end
  LOAD0:state<=LOAD1;
  LOAD1:begin assembly[383:256]<=scratch_q;state<=LOAD2;end
  LOAD2:begin assembly[255:128]<=scratch_q;state<=LOAD3;end
  LOAD3:begin assembly[127:0]<=scratch_q;state<=LOAD4;end
  LOAD4:begin state<=EMIT;quad<=0;
   pixels<=aligned_pixels;
  end
  EMIT:begin
   case(quad)
   0:assembly[383:256]<=scratch_q;
   1:assembly[255:128]<=scratch_q;
   2:assembly[127:0]<=scratch_q;
   default:begin end
   endcase
   if(quad==3)begin
    if(group_index==79)begin filled[process_index[0]]<=0;state<=FLUSH;flush_age<=0;end
    else begin
     group_index<=group_index+1'b1;quad<=0;
     pixels<=aligned_pixels;
    end
   end else begin quad<=quad+1'b1;pixels<={pixels[287:0],96'd0};end
  end
  FLUSH:begin
   if(flush_age<15)flush_age<=flush_age+1'b1;
   if(flush_age==8)begin
    if(!dense && process_index!=3)begin process_index<=process_index+1'b1;state<=WAIT_DATA;end
    else if(returned==240 && accepted==240)state<=IDLE;
    else begin fault<=1;state<=BROKEN;end
   end
  end
  BROKEN:begin end
  default:begin fault<=1;state<=BROKEN;end
  endcase
  if((fetch_state==F_SEND || fetch_state==F_RECEIVE) && ddr_valid)begin
   received<=received+1'b1;
   if(received==words-1)begin
    filled[fetch_index[0]]<=1;slot_index[fetch_index[0]]<=fetch_index;
    fetch_index<=fetch_index+1'b1;fetch_state<=F_IDLE;
   end
   if(received>=sent && !(fetch_state==F_SEND && read_en))begin fault<=1;state<=BROKEN;end
  end
  if(issue && state!=IDLE && virtual_addr!=first_addr+({17'd0,accepted}<<3))begin fault<=1;state<=BROKEN;end
  if(unexpected_return)begin fault<=1;state<=BROKEN;end
 end end
endmodule
`default_nettype wire
