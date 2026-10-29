// Dense DDR row adapter with the existing output scaler/filter and 3 line banks.
`default_nettype none
module native_line_reader(
 input wire I_frame_commit,I_selected_good,I_rst_n,I_ddr_clk,I_write_busy,I_write_en,
 input wire [1:0] I_read_buffer,input wire [31:0] I_frame_id,input wire [127:0] I_models,
 input wire I_ddr_ready,I_ddr_valid,input wire [127:0] I_ddr_data,
 output wire O_read_busy,O_read_en,output wire [24:0] O_read_addr,
 input wire I_pixel_clk,I_vs,I_hs,I_de,input wire [10:0] I_x0,input wire [9:0] I_y0,
 input wire [2:0] I_zoom,output wire O_vs,O_hs,O_de,output wire [23:0] O_rgb,
 output wire [1:0] O_mask,output wire O_video_ok,input wire I_rotate,I_stream_n,
 output wire O_fault_toggle,output wire [127:0] O_ddr_diag,O_pixel_diag,
 input wire [31:0] I_accepted_reads,input wire I_unexpected_return);
 wire core_en,core_ready,core_valid,core_busy;wire [24:0] core_addr;
 wire [127:0] core_data;wire [31:0] core_accepted;
 wire [9:0] source_y,job_y0;wire [1:0] source_bank;wire [2:0] job_zoom;wire [10:0] job_x0;
 wire adapter_rst_n,adapter_fault;
 refined_reset_bridge adapter_reset(I_ddr_clk,I_rst_n && I_stream_n,adapter_rst_n);
 native_read_adapter adapter(.clk(I_ddr_clk),.rst_n(adapter_rst_n),
  .virtual_en(core_en),.virtual_addr(core_addr),.virtual_ready(core_ready),.virtual_valid(core_valid),.virtual_data(core_data),
  .virtual_accepted(core_accepted),.source_y(source_y),.source_bank(source_bank),
  .job_zoom(job_zoom),.job_x0(job_x0),.job_y0(job_y0),.write_busy(I_write_busy),.write_en(I_write_en),
  .ddr_ready(I_ddr_ready),.ddr_valid(I_ddr_valid),.ddr_data(I_ddr_data),
  .read_busy(O_read_busy),.read_en(O_read_en),.read_addr(O_read_addr),.unexpected_return(I_unexpected_return),.fault(adapter_fault));
 native_line_core core(.I_frame_commit(I_frame_commit),.I_selected_good(I_selected_good),.I_rst_n(I_rst_n),
  .I_ddr_clk(I_ddr_clk),.I_write_busy(I_write_busy),.I_write_en(I_write_en),
  .I_read_buffer(I_read_buffer),.I_frame_id(I_frame_id),.I_models(I_models),
  .I_ddr_ready(core_ready),.I_ddr_valid(core_valid),.I_ddr_data(core_data),
  .O_read_busy(core_busy),.O_read_en(core_en),.O_read_addr(core_addr),
  .I_pixel_clk(I_pixel_clk),.I_vs(I_vs),.I_hs(I_hs),.I_de(I_de),
  .I_x0(I_zoom==2?11'd0:I_x0),.I_y0(I_zoom==2?10'd0:I_y0),.I_zoom(I_zoom==2?3'd0:I_zoom),
  .O_vs(O_vs),.O_hs(O_hs),.O_de(O_de),.O_rgb(O_rgb),.O_mask(O_mask),.O_video_ok(O_video_ok),
  .I_rotate(I_rotate),.I_stream_n(I_stream_n),.O_fault_toggle(O_fault_toggle),
  .O_ddr_diag(O_ddr_diag),.O_pixel_diag(O_pixel_diag),.I_accepted_reads(core_accepted),
  .I_unexpected_return(I_unexpected_return || adapter_fault),
  .I_native_zoom(I_zoom),.I_native_x0(I_x0),.I_native_y0(I_y0),
  .O_job_zoom(job_zoom),.O_job_x0(job_x0),.O_job_y0(job_y0),.O_source_y(source_y),.O_source_bank(source_bank));
endmodule
`default_nettype wire
