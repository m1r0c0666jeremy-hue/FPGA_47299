// RAW10 clock-domain bridge. A line is published only after its real packet
// end and exactly GROUPS valid groups. No partial line reaches the ISP.
// The data FIFO has 1024 x 40 bits; four small bundled-data descriptors carry
// the source identity/timestamp. Only single-step Gray pointers cross clocks.
`default_nettype none
module fhd_raw_bridge #(
 parameter GROUPS=480,HEIGHT=1080,GAP=96,IDLE_LIMIT=30000000
)(input wire I_rx_clk,I_processing_clk,I_rst_n,
 input wire I_sof,I_eof,I_valid,I_line_end,input wire [39:0] I_data,
 input wire [31:0] I_source_id,I_source_us,
 output reg [39:0] O_data,output reg O_valid,O_sof,O_last,O_abort,
 output reg [31:0] O_source_id,O_source_us,
 output reg [31:0] O_overflows,O_bad_lines);
 wire wr_reset_n,rd_reset_n;
 refined_reset_bridge wr_reset(I_rx_clk,I_rst_n,wr_reset_n);
 refined_reset_bridge rd_reset(I_processing_clk,I_rst_n,rd_reset_n);
 function [10:0] ungray11;input [10:0] g;integer j;begin
  ungray11[10]=g[10];for(j=9;j>=0;j=j-1)ungray11[j]=ungray11[j+1]^g[j];end endfunction
 function [2:0] ungray3;input [2:0] g;begin ungray3={g[2],g[2]^g[1],g[2]^g[1]^g[0]};end endfunction
 reg [10:0] wr_pointer,line_start,rd_pointer,rd_gray;
 reg [2:0] desc_wr,desc_wr_gray,desc_rd,desc_rd_gray;
 // {first-line, last-line, frame ID, original CSI SOF timestamp}.
 reg [65:0] descriptors[0:3];
 (* async_reg="true" *) reg [10:0] rd_gray_w1,rd_gray_w2;
 (* async_reg="true" *) reg [2:0] desc_rd_w1,desc_rd_w2,desc_wr_r1,desc_wr_r2;
 reg frame_active,drop_frame,line_admitted;
 reg [9:0] line_count;reg [10:0] line_index;
 reg [31:0] frame_id,frame_us,abort_id;
 reg [31:0] abort_count,abort_gray;
 wire [10:0] used=wr_pointer-ungray11(rd_gray_w2);
 wire enough_space=used<=1024-GROUPS;
 wire descriptor_full=(desc_wr-ungray3(desc_rd_w2))==4;
 wire accept=I_valid && !I_sof && frame_active && !drop_frame && line_count<GROUPS &&
             (line_admitted || (line_count==0 && enough_space && !descriptor_full));
 wire [39:0] ram_data;
 fhd_isp_line_ram #(.WIDTH(40),.ADDR_BITS(10)) raw_fifo(
 .clka(I_rx_clk),.wea(accept),.addra(wr_pointer[9:0]),.dia(I_data),
 .clkb(I_processing_clk),.addrb(rd_pointer[9:0]),.dob(ram_data));
 task reject_frame;input overflow;begin
  drop_frame<=1;line_admitted<=0;line_count<=0;wr_pointer<=line_start;
  abort_id<=frame_id;abort_count<=abort_count+1'b1;
  abort_gray<=((abort_count+32'd1)>>1)^(abort_count+32'd1);
  if(overflow)O_overflows<=O_overflows+1'b1;else O_bad_lines<=O_bad_lines+1'b1;
 end endtask
 always @(posedge I_rx_clk or negedge wr_reset_n)begin
 if(!wr_reset_n)begin
  wr_pointer<=0;line_start<=0;desc_wr<=0;desc_wr_gray<=0;
  rd_gray_w1<=0;rd_gray_w2<=0;desc_rd_w1<=0;desc_rd_w2<=0;
  frame_active<=0;drop_frame<=1;line_admitted<=0;line_count<=0;line_index<=0;
  frame_id<=0;frame_us<=0;abort_id<=0;abort_count<=0;abort_gray<=0;O_overflows<=0;O_bad_lines<=0;
 end else begin
  rd_gray_w1<=rd_gray;rd_gray_w2<=rd_gray_w1;
  desc_rd_w1<=desc_rd_gray;desc_rd_w2<=desc_rd_w1;
  if(I_sof)begin
   if(frame_active && !drop_frame && (line_count!=0 || line_index!=HEIGHT))reject_frame(0);
   frame_active<=1;drop_frame<=0;line_admitted<=0;line_count<=0;line_index<=0;
   frame_id<=I_source_id;frame_us<=I_source_us;wr_pointer<=line_start;
  end else if(I_eof)begin
   if(frame_active && !drop_frame && (line_index!=HEIGHT || line_count!=0))reject_frame(0);
   frame_active<=0;
  end else if(I_line_end && frame_active && !drop_frame)begin
   if(I_valid || !line_admitted || line_count!=GROUPS || line_index>=HEIGHT)reject_frame(0);
   else begin
    descriptors[desc_wr[1:0]]<={line_index==0,line_index==HEIGHT-1,frame_id,frame_us};
    desc_wr<=desc_wr+1'b1;desc_wr_gray<=((desc_wr+3'd1)>>1)^(desc_wr+3'd1);
    line_index<=line_index+1'b1;line_count<=0;line_admitted<=0;line_start<=wr_pointer;
   end
  end else if(I_valid && frame_active && !drop_frame)begin
   if(line_count>=GROUPS)reject_frame(0);
   else if(!line_admitted && (!enough_space || descriptor_full))reject_frame(1);
   else begin
    if(line_count==0)begin line_start<=wr_pointer;line_admitted<=1;end
    line_count<=line_count+1'b1;wr_pointer<=wr_pointer+1'b1;
   end
  end
 end end

 (* async_reg="true" *) reg [31:0] abort_sync0,abort_sync1,abort_sync2;
 // A monotonically incremented Gray event counter survives multiple failures
 // while the processing clock is stopped. The latest bundled identity settles
 // through two stages before the three-stage event counter is acted upon.
 (* async_reg="true" *) reg [31:0] abort_id_r1,abort_id_r2;
 reg [31:0] abort_previous;
 reg invalid_id_valid,await_sof,emit_line,fetch_valid,fetch_first,fetch_last,read_frame_active;
 reg [31:0] invalid_id;
 reg [1:0] state;localparam IDLE=0,READ_LINE=1,LINE_GAP=2;
 reg [9:0] beat;reg [7:0] gap_count;reg [24:0] idle_count;
 wire [65:0] descriptor=descriptors[desc_rd[1:0]];
 wire [31:0] descriptor_id=descriptor[63:32];
 wire newer=!invalid_id_valid || $signed(descriptor_id-invalid_id)>0;
 wire fresh=descriptor[65] && newer;
 wire fault_arrived=abort_sync2!=abort_previous;
 always @(posedge I_processing_clk or negedge rd_reset_n)begin
 if(!rd_reset_n)begin
  rd_pointer<=0;rd_gray<=0;desc_rd<=0;desc_rd_gray<=0;desc_wr_r1<=0;desc_wr_r2<=0;
  abort_sync0<=0;abort_sync1<=0;abort_sync2<=0;abort_id_r1<=0;abort_id_r2<=0;abort_previous<=0;
  invalid_id_valid<=0;invalid_id<=0;await_sof<=1;emit_line<=0;read_frame_active<=0;
  fetch_valid<=0;fetch_first<=0;fetch_last<=0;state<=IDLE;beat<=0;gap_count<=0;idle_count<=0;
  O_data<=0;O_valid<=0;O_sof<=0;O_last<=0;O_abort<=0;O_source_id<=0;O_source_us<=0;
 end else begin
  desc_wr_r1<=desc_wr_gray;desc_wr_r2<=desc_wr_r1;
  abort_sync0<=abort_gray;abort_sync1<=abort_sync0;abort_sync2<=abort_sync1;
  abort_id_r1<=abort_id;abort_id_r2<=abort_id_r1;
  abort_previous<=abort_sync2;O_abort<=0;
  O_data<=ram_data;O_valid<=fetch_valid && emit_line && !fault_arrived;
  O_sof<=fetch_valid && fetch_first && emit_line && !fault_arrived;
  O_last<=fetch_valid && fetch_last && emit_line && !fault_arrived;
  fetch_valid<=0;fetch_first<=0;fetch_last<=0;
  if(state==IDLE && desc_rd_gray==desc_wr_r2 && read_frame_active)begin
   if(idle_count==IDLE_LIMIT-1)begin O_abort<=1;await_sof<=1;emit_line<=0;read_frame_active<=0;idle_count<=0;end
   else idle_count<=idle_count+1'b1;
  end else idle_count<=0;
  case(state)
  IDLE:if(desc_rd_gray!=desc_wr_r2)begin
   emit_line<=fresh || (!await_sof && descriptor_id==O_source_id);
   if(fresh)begin await_sof<=0;read_frame_active<=1;O_source_id<=descriptor_id;O_source_us<=descriptor[31:0];end
   state<=READ_LINE;beat<=0;
  end
  READ_LINE:begin
   fetch_valid<=1;fetch_first<=beat==0 && descriptor[65];fetch_last<=beat==GROUPS-1;
   rd_pointer<=rd_pointer+1'b1;rd_gray<=((rd_pointer+11'd1)>>1)^(rd_pointer+11'd1);
   if(beat==GROUPS-1)begin
    if(descriptor[64])read_frame_active<=0;
    desc_rd<=desc_rd+1'b1;desc_rd_gray<=((desc_rd+3'd1)>>1)^(desc_rd+3'd1);
    state<=LINE_GAP;gap_count<=GAP;
   end else beat<=beat+1'b1;
  end
  LINE_GAP:if(gap_count==0)state<=IDLE;else gap_count<=gap_count-1'b1;
  endcase
  if(fault_arrived)begin
   invalid_id<=abort_id_r2;invalid_id_valid<=1;await_sof<=1;emit_line<=0;read_frame_active<=0;O_abort<=1;
   O_valid<=0;O_sof<=0;O_last<=0;
  end
 end end
endmodule
`default_nettype wire
