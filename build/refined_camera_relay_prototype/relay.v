
`default_nettype none
module refined_camera_control_relay(
 input wire ref_clk,cam_clk,display_clk,rst_n,display_rst_n,
 input wire gain_req,gain_up,cam_gain_ack,cam_event,cam_ready,
 input wire [17:0] cam_status,
 output wire cam_req,cam_up,gain_ack,event_relay,ready_relay,
 output wire [17:0] ui_status);
 (* async_reg="true",syn_preserve=1 *) reg [1:0] reset_sync;
 wire ref_rst_n=reset_sync[1];
 always @(posedge ref_clk or negedge rst_n)
  if(!rst_n)reset_sync<=0;else reset_sync<={reset_sync[0],1'b1};
 (* async_reg="true",syn_preserve=1 *) reg [2:0] req_sync;
 (* async_reg="true",syn_preserve=1 *) reg [1:0] up_sync,ack_sync,event_sync,ready_sync;
 always @(posedge ref_clk or negedge ref_rst_n)begin
  if(!ref_rst_n)begin req_sync<=0;up_sync<=0;ack_sync<=0;event_sync<=0;ready_sync<=0;end
  else begin req_sync<={req_sync[1:0],gain_req};up_sync<={up_sync[0],gain_up};
   ack_sync<={ack_sync[0],cam_gain_ack};event_sync<={event_sync[0],cam_event};ready_sync<={ready_sync[0],cam_ready};end
 end
 assign cam_req=req_sync[2];assign cam_up=up_sync[1];assign gain_ack=ack_sync[1];
 assign event_relay=event_sync[1];assign ready_relay=ready_sync[1];
 wire [17:0] ref_status;wire cam_send_ready,ref_send_ready;
 target_mailbox #(.WIDTH(18)) cam_to_ref(.S_clk(cam_clk),.S_rst_n(rst_n),.S_send(cam_send_ready),
  .S_data(cam_status),.S_ready(cam_send_ready),.D_clk(ref_clk),.D_rst_n(ref_rst_n),.D_valid(),.D_data(ref_status));
 target_mailbox #(.WIDTH(18)) ref_to_display(.S_clk(ref_clk),.S_rst_n(ref_rst_n),.S_send(ref_send_ready),
  .S_data(ref_status),.S_ready(ref_send_ready),.D_clk(display_clk),.D_rst_n(display_rst_n),.D_valid(),.D_data(ui_status));
endmodule
`default_nettype wire
