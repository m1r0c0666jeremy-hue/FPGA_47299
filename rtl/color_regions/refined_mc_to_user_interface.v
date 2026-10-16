// Project-owned command FIFO adapter. Address/data VALID never depend on READY.
// The supplied PAXI write mask is active high inhibit (zero writes all bytes).
`default_nettype none
module refined_mc_to_user_interface (
 input wire I_clk,I_rst_n,
 input wire I_ddr_user_wr_en,I_ddr_user_rd_en,
 input wire [24:0] I_ddr_user_addr,input wire [127:0] I_ddr_user_wr_data,
 output wire O_ddr_user_ready,O_ddr_user_rd_valid,output wire [127:0] O_ddr_user_rd_data,
 output wire O_mc_app_en,output wire [24:0] O_mc_app_addr,output wire [2:0] O_mc_app_cmd,
 input wire I_mc_app_rdy,output wire O_mc_app_wdf_wren,
 output wire [127:0] O_mc_app_wdf_data,output wire O_mc_app_wdf_end,
 output wire [15:0] O_mc_app_wdf_mask,input wire I_mc_app_wdf_rdy,
 input wire [127:0] I_mc_app_rd_data,input wire I_mc_app_rd_data_end,I_mc_app_rd_data_valid,
 output wire O_write_commit,output wire [24:0] O_write_addr,
 output reg [9:0] O_outstanding_reads,output reg O_unexpected_return,output reg [31:0] O_accepted_reads
);
 wire [154:0] head;wire empty,almost_full,full,head_valid;
 reg holding,read_command,address_done,data_done;
 reg [24:0] address;reg [127:0] payload;
 wire address_fire=holding && !address_done && I_mc_app_rdy;
 wire data_fire=holding && !read_command && !data_done && I_mc_app_wdf_rdy;
 wire complete=holding && (address_done || address_fire) && (read_command || data_done || data_fire);
 wire pop=!empty && (!holding || complete);
 assign O_ddr_user_ready=!almost_full;
 assign O_mc_app_en=holding && !address_done;
 assign O_mc_app_addr=address;
 assign O_mc_app_cmd=read_command?3'd1:3'd0;
 assign O_mc_app_wdf_wren=holding && !read_command && !data_done;
 assign O_mc_app_wdf_data=payload;
 assign O_mc_app_wdf_end=O_mc_app_wdf_wren;
 assign O_mc_app_wdf_mask=16'd0;
 assign O_ddr_user_rd_valid=I_mc_app_rd_data_valid;
 assign O_ddr_user_rd_data=I_mc_app_rd_data;
 assign O_write_commit=complete && !read_command;
 assign O_write_addr=address;
 w155_d512_fifo commands(.clk(I_clk),.rst(!I_rst_n),
  .we(I_ddr_user_wr_en || I_ddr_user_rd_en),
  .di({I_ddr_user_wr_en,I_ddr_user_rd_en,I_ddr_user_addr,I_ddr_user_wr_data}),
  .afull(almost_full),.full_flag(full),.wrusedw(),.re(pop),.valid(head_valid),
  .dout(head),.empty_flag(empty),.aempty(),.rdusedw());
 always @(posedge I_clk or negedge I_rst_n)begin
  if(!I_rst_n)begin holding<=0;read_command<=0;address_done<=0;data_done<=0;address<=0;payload<=0;
   O_outstanding_reads<=0;O_unexpected_return<=0;O_accepted_reads<=0;end
  else begin
   O_unexpected_return<=I_mc_app_rd_data_valid && O_outstanding_reads==0 && !(address_fire && read_command);
   if(address_fire && read_command)O_accepted_reads<=O_accepted_reads+1'b1;
   case({address_fire && read_command,I_mc_app_rd_data_valid})
    2'b10:O_outstanding_reads<=O_outstanding_reads+1'b1;
    2'b01:if(O_outstanding_reads!=0)O_outstanding_reads<=O_outstanding_reads-1'b1;
   endcase
   if(pop)begin holding<=1;read_command<=head[153];address<=head[152:128];payload<=head[127:0];address_done<=0;data_done<=0;end
   else if(complete)begin holding<=0;address_done<=0;data_done<=0;end
   else begin if(address_fire)address_done<=1;if(data_fire)data_done<=1;end
  end
 end
endmodule
`default_nettype wire
