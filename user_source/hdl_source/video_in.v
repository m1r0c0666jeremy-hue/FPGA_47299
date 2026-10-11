// Lab1-compatible 128-bit capture writer. Frame reset is a request/ack
// transaction; a camera-clock staging RAM retains incoming frame-head words.
// No camera backpressure. An exhausted staging buffer marks the frame bad.
`default_nettype none
module video_in (
 input wire I_rst_n,I_camera_clk,I_camera_frame_start,
 input wire [31:0] I_camera_frame_id,
 output wire O_frame_begin,output wire [1:0] O_frame_bank,
 output wire [31:0] O_frame_id,output wire O_capture_overflow,
 input wire I_camera_valid,input wire [127:0] I_camera_data,
 input wire I_mipi_rx_error,I_ddr_clk,I_display_pause,I_video_out_rd_busy,
 output wire O_video_in_wr_busy,output reg [1:0] O_video_out_rp,
 output reg O_ddr_user_wr_en,output reg [24:0] O_ddr_user_addr,
 output wire [127:0] O_ddr_user_wr_data,input wire I_ddr_user_ready
);
 reg request,ack;
 (* async_reg="true" *) reg ack_c1,ack_c2,req_d1,req_d2;
 reg [31:0] camera_id_hold;
 reg camera_error_hold,accept_frame,overflow,sof_d;
 wire sof=I_camera_frame_start&&!sof_d;
 wire transaction_free=request==ack_c2;
 // 256 words = 4096 bytes, not a frame buffer. RAM has synchronous read.
 (* ram_style="block" *) reg [127:0] staging[0:255];
 reg [7:0] wp,rp;
 reg [8:0] used;
 reg [127:0] staged_data;
 reg staged_valid;
 wire fifo_full;
 wire drain=accept_frame && transaction_free && !sof;
 wire fifo_push=drain && staged_valid && !fifo_full;
 wire pop=drain && (!staged_valid || fifo_push) && used!=0;
 wire push=I_camera_valid && accept_frame && !sof && (used<256 || pop);
 wire first_push=sof && transaction_free && I_camera_valid;
 wire staging_we=first_push || push;
 wire [7:0] staging_wa=first_push?8'd0:wp;
 // Keep RAM ports free of asynchronous reset for physical block RAM mapping.
 always @(posedge I_camera_clk) begin
  if(staging_we) staging[staging_wa]<=I_camera_data;
  if(pop) staged_data<=staging[rp];
 end
 always @(posedge I_camera_clk or negedge I_rst_n) begin
  if(!I_rst_n) begin
   ack_c1<=0;ack_c2<=0;request<=0;camera_id_hold<=0;camera_error_hold<=0;
   accept_frame<=0;overflow<=0;sof_d<=0;wp<=0;rp<=0;used<=0;staged_valid<=0;
  end else begin
   ack_c1<=ack;ack_c2<=ack_c1;sof_d<=I_camera_frame_start;
   if(sof) begin
    // A second SOF before acknowledgement is a malformed/too-fast frame.
    // Do not overwrite the bundled ID while the previous request is in flight.
    accept_frame<=transaction_free;overflow<=!transaction_free || I_mipi_rx_error;
    wp<=first_push?1:0;rp<=0;used<=first_push?1:0;staged_valid<=0;
    if(transaction_free) begin
     request<=!request;camera_id_hold<=I_camera_frame_id;camera_error_hold<=I_mipi_rx_error;
    end
   end else begin
    if(push) wp<=wp+1'b1;
    if(pop) begin rp<=rp+1'b1;staged_valid<=1;end
    else if(fifo_push) staged_valid<=0;
    case({push,pop}) 2'b10:used<=used+1'b1;2'b01:used<=used-1'b1;default:begin end endcase
    if(I_camera_valid && accept_frame && !push) begin overflow<=1;accept_frame<=0;end
   end
  end
 end
 assign O_capture_overflow=overflow;
 localparam RUN=0,QUIET=1,RESET_FIFO=2,PUBLISH=3,RELEASE=4;
 reg [2:0] phase;
 reg [4:0] guard_count;
 reg [1:0] bank;
 wire S_fifo_rst=!I_rst_n || phase==RESET_FIFO;
 wire [8:0] fifo_count;
 reg burst;
 reg [7:0] burst_count;
 wire read_word=phase==RUN && req_d2==ack && burst && I_ddr_user_ready;
 assign O_video_in_wr_busy=burst;
 assign O_frame_begin=phase==PUBLISH;
 assign O_frame_bank=bank;
 assign O_frame_id=camera_id_hold;
 function [24:0] base_for(input [1:0] b);
  case(b) 0:base_for=0;1:base_for=7000000;2:base_for=14000000;3:base_for=21000000;endcase
 endfunction
 w128_d512_fifo U_w128_d512_fifo(
  .rst(S_fifo_rst),.clkw(I_camera_clk),.we(fifo_push),.di(staged_data),
  .afull(),.full_flag(fifo_full),.wrusedw(),.clkr(I_ddr_clk),.re(read_word),
  .dout(O_ddr_user_wr_data),.rdusedw(fifo_count),.valid(),.empty_flag(),.aempty());
 always @(posedge I_ddr_clk or negedge I_rst_n) begin
  if(!I_rst_n) begin
   req_d1<=0;req_d2<=0;ack<=0;phase<=RUN;guard_count<=0;bank<=0;
   O_video_out_rp<=0;O_ddr_user_wr_en<=0;O_ddr_user_addr<=0;burst<=0;burst_count<=0;
  end else begin
   req_d1<=request;req_d2<=req_d1;
   O_ddr_user_wr_en<=read_word;
   if(O_ddr_user_wr_en) O_ddr_user_addr<=O_ddr_user_addr+8;
   case(phase)
    RUN:begin
     if(req_d2!=ack) begin phase<=QUIET;burst<=0;burst_count<=0;end
     else if(burst) begin
      if(read_word) begin
       if(burst_count==239) begin burst<=0;burst_count<=0;end
       else burst_count<=burst_count+1'b1;
      end
     end else if(fifo_count>=240 && !I_video_out_rd_busy) begin burst<=1;burst_count<=0;end
    end
    // Drain the last registered write using its OLD address before reset/begin.
    QUIET:if(!O_ddr_user_wr_en) begin phase<=RESET_FIFO;guard_count<=0;end
    RESET_FIFO:if(guard_count==15) begin phase<=PUBLISH;guard_count<=0;end
               else guard_count<=guard_count+1'b1;
    PUBLISH:begin
     O_ddr_user_addr<=base_for(bank);
     if(!I_display_pause) begin O_video_out_rp<=bank+2'd2;bank<=bank+1'b1;end
     phase<=RELEASE;guard_count<=0;
    end
    // Allow FIFO reset release before the camera observes the acknowledgement.
    RELEASE:if(guard_count==7) begin ack<=req_d2;phase<=RUN;end
            else guard_count<=guard_count+1'b1;
    default:phase<=QUIET;
   endcase
  end
 end
endmodule
`default_nettype wire
