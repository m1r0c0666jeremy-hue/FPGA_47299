// Diagnostic-only model: AWB timing/packing/writer; divider fixed unity, RAM
// behavioral. Not ISP numeric verification or physical FIFO verification.
`timescale 1ns/1ps
module tb_target_ingress_probe;
 reg cc=0,dc=0,rst=0,sof=0,valid=0;always #8 cc=~cc;always #7.5 dc=~dc;
 reg [95:0] rgb=0;wire av,asf,al;wire [95:0] ar;
 awb #(.IMG_WIDTH(1280),.IMG_HEIGHT(4)) isp(cc,rst,1'b0,sof,rgb,valid,,al,asf,ar,av,1'b1);
 wire pv,psf;wire [127:0] pr;
 data_96bit_to_128bit packer(cc,rst,asf,av,ar,psf,pv,pr);
 wire wr,busy;wire [24:0] addr;wire [127:0] data;wire [1:0] rp;
 wire begin_frame,overflow;wire [1:0] wb;wire [31:0] fid;
 video_in writer(.I_rst_n(rst),.I_camera_clk(cc),.I_camera_frame_start(psf),.I_camera_frame_id(32'd1),
 .O_frame_begin(begin_frame),.O_frame_bank(wb),.O_frame_id(fid),.O_capture_overflow(overflow),
 .I_camera_valid(pv),.I_camera_data(pr),.I_mipi_rx_error(1'b0),.I_ddr_clk(dc),.I_display_pause(1'b0),
 .I_video_out_rd_busy(1'b0),.O_video_in_wr_busy(busy),.O_video_out_rp(rp),
 .O_ddr_user_wr_en(wr),.O_ddr_user_addr(addr),.O_ddr_user_wr_data(data),.I_ddr_user_ready(1'b1));
 integer cycle=0,first=-1,words=0,aw=0,dd=0,x,y;
 always @(posedge cc)if(rst)begin
  cycle=cycle+1;if(asf)begin $display("AWB SOF cycle=%0d valid=%0d",cycle,av);first=cycle;end
  if(av)aw=aw+1;
  if(pv)begin words=words+1;if(words<15)$display("packed cycle=%0d FIFO reset=%b",cycle,writer.S_fifo_rst);end
 end
 always @(posedge dc)if(rst&&wr)dd=dd+1;
 initial begin
  repeat(10)@(negedge cc);rst=1;repeat(10)@(negedge cc);
  sof=1;@(negedge cc);sof=0;
  for(y=0;y<4;y=y+1)begin
   for(x=0;x<320;x=x+1)begin valid=1;rgb={4{24'h804020}};@(negedge cc);end
   valid=0;repeat(100)@(negedge cc);
  end
  repeat(2000)@(negedge cc);
  $display("INGRESS_PROBE AWB_words=%0d packed_words=%0d DDR_writes=%0d expected=960",aw,words,dd);$finish;
 end
endmodule
module divider(input clk,rst,start,input [31:0] denominator,input [47:0] numerator,output [47:0] quotient,output done);
 assign quotient=48'h10000;assign done=start;
endmodule
module blk_mem_gen_awb_delay_signal(input clka,wea,input [10:0] addra,input [95:0] dia,input clkb,input [10:0] addrb,output reg [95:0] dob);
 reg [95:0] mem[0:2047];always @(posedge clka)if(wea)mem[addra]<=dia;
 always @(posedge clkb)dob<=mem[addrb];
endmodule
