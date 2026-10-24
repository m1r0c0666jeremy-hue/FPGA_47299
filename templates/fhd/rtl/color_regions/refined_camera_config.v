// ACK-checked SC500 configuration, gain application and bounded local recovery.
`default_nettype none
module refined_camera_config #(
 // FHD profile supplies a true 24 MHz sensor/configuration reference.
 parameter integer CYCLES_PER_MS=24000,CLK_DIV=239,
 parameter integer BOOT_MS=100,TRANSACTION_MS=2,RESET_MS=1,BACKOFF_MS=20,FRAME_TIMEOUT_MS=500,MAX_RETRIES=3
)(input wire clk,rst_n,input wire gain_req,gain_up,frame_toggle,bad_frame_toggle,
 output reg gain_ack,output wire scl,inout wire sda,
 output reg ready,output wire receiver_enable,output reg parameter_event,
 output reg [3:0] fault,output reg [1:0] retries,output wire [3:0] phase,
 output reg [6:0] requested_gain,output reg [6:0] applied_gain);
 localparam BOOT=0,PREPARE=1,REQUEST=2,WAIT_BUSY=3,WAIT_END=4,DELAY=5,WAIT_FRAME=6,RUN=7,RETRY=8,DEAD=9;
 reg [3:0] state;assign phase=state;
 reg [14:0] subms;wire tick=subms==CYCLES_PER_MS-1;
 reg [10:0] elapsed,stable_ms;reg [8:0] index;reg gain_table,transaction_error;
 reg req,requested,frame_previous,bad_previous,gain_tag;reg [6:0] gain_for_table;reg [31:0] write_data;reg [1:0] good_frames;
 (* async_reg="true" *) reg [2:0] req_sync,frame_sync,bad_sync;
 (* async_reg="true" *) reg [1:0] up_sync,busy_sync,error_sync;
 wire busy,error;wire [31:0] init_data,ae_data;wire [8:0] init_size,ae_size;wire [15:0] gain_value;
 wire [31:0] selected_data=gain_table?ae_data:init_data;
 wire bus_rst_n=rst_n && state!=BOOT && state!=RETRY && state!=DEAD;
 assign receiver_enable=bus_rst_n;
 uics500reg_1080p30 table_init(index,init_data,init_size);
 SC500GainTbl gains(clk,rst_n,gain_for_table-7'd16,gain_value);
 uics500regAE table_gain(index,ae_data,ae_size,16'd1990,gain_value);
 uii2c #(.WMEN_LEN(4),.RMEN_LEN(1),.CLK_DIV(CLK_DIV)) bus(
 .I_clk(clk),.I_rstn(bus_rst_n),.O_iic_scl(scl),.IO_iic_sda(sda),.I_wr_data(write_data),
 .I_wr_cnt(8'd4),.O_rd_data(),.I_rd_cnt(8'd0),.I_iic_req(req),.I_iic_mode(1'b0),
 .O_iic_busy(busy),.O_iic_bus_error(error),.IO_iic_sda_dg());
 task fail;input [3:0] why;begin
  fault<=why;ready<=0;req<=0;elapsed<=0;stable_ms<=0;good_frames<=0;parameter_event<=~parameter_event;
  if(retries<MAX_RETRIES)begin retries<=retries+1'b1;state<=RETRY;end else state<=DEAD;
 end endtask
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin subms<=0;elapsed<=0;stable_ms<=0;state<=BOOT;index<=0;gain_table<=0;transaction_error<=0;
 req<=0;requested<=0;frame_previous<=0;bad_previous<=0;gain_tag<=0;gain_for_table<=90;write_data<=0;good_frames<=0;ready<=0;gain_ack<=0;
 parameter_event<=0;fault<=0;retries<=0;requested_gain<=90;applied_gain<=0;
 req_sync<=0;frame_sync<=0;bad_sync<=0;up_sync<=0;busy_sync<=0;error_sync<=0;end
 else begin
 req_sync<={req_sync[1:0],gain_req};frame_sync<={frame_sync[1:0],frame_toggle};bad_sync<={bad_sync[1:0],bad_frame_toggle};up_sync<={up_sync[0],gain_up};
 busy_sync<={busy_sync[0],busy};error_sync<={error_sync[0],error};frame_previous<=frame_sync[2];bad_previous<=bad_sync[2];
 if(tick)begin subms<=0;if(elapsed<2047)elapsed<=elapsed+1'b1;end else subms<=subms+1'b1;
 if(req_sync[2]!=requested)begin
  requested<=req_sync[2];parameter_event<=~parameter_event;
  if(up_sync[1])begin if(requested_gain<105)requested_gain<=requested_gain+1'b1;end
  else if(requested_gain>16)requested_gain<=requested_gain-1'b1;
  if(state==RUN)begin ready<=0;gain_table<=1;index<=0;state<=PREPARE;elapsed<=0;good_frames<=0;end
 end
 case(state)
 BOOT:if(tick && elapsed>=BOOT_MS-1)begin state<=PREPARE;elapsed<=0;index<=0;gain_table<=0;end
 PREPARE:begin
  req<=0;transaction_error<=0;
  if(gain_table && index==0)begin gain_tag<=requested;gain_for_table<=requested_gain;end
  if(index==(gain_table?ae_size:init_size))begin
   index<=0;elapsed<=0;
   if(!gain_table)begin gain_table<=1;state<=PREPARE;end
   else if(requested!=gain_tag)state<=PREPARE;
   else begin gain_ack<=gain_tag;applied_gain<=gain_for_table;good_frames<=0;state<=WAIT_FRAME;end
  end else if(!busy_sync[1])begin
   write_data<={selected_data[7:0],selected_data[15:8],selected_data[23:16],8'h6c};state<=REQUEST;elapsed<=0;
  end else if(tick && elapsed>=TRANSACTION_MS-1)fail(2);
 end
 REQUEST:begin req<=1;elapsed<=0;state<=WAIT_BUSY;end
 WAIT_BUSY:begin
  if(error_sync[1])transaction_error<=1;
  if(busy_sync[1])begin req<=0;state<=WAIT_END;end
  else if(tick && elapsed>=TRANSACTION_MS-1)fail(2);
 end
 WAIT_END:begin
  if(error_sync[1])transaction_error<=1;
  if(!busy_sync[1])begin
   if(transaction_error || error_sync[1])fail(1);
   else begin index<=index+1'b1;elapsed<=0;
    if(!gain_table && (index==0 || index==120))state<=DELAY;else state<=PREPARE;
   end
  end else if(tick && elapsed>=TRANSACTION_MS-1)fail(2);
 end
 DELAY:if(tick && elapsed>=(index==1?RESET_MS:10)-1)begin state<=PREPARE;elapsed<=0;end
 WAIT_FRAME:begin
  if(bad_sync[2]!=bad_previous)good_frames<=0;
  else if(frame_sync[2]!=frame_previous)begin elapsed<=0;if(good_frames==2)begin ready<=1;fault<=0;stable_ms<=0;state<=RUN;end else good_frames<=good_frames+1'b1;end
  else if(tick && elapsed>=FRAME_TIMEOUT_MS-1)fail(3);
 end
 RUN:begin
  if(frame_sync[2]!=frame_previous)elapsed<=0;
  else if(tick && elapsed>=FRAME_TIMEOUT_MS-1)fail(3);
  if(tick && stable_ms<2000)begin stable_ms<=stable_ms+1'b1;if(stable_ms==1999)retries<=0;end
  if(bad_sync[2]!=bad_previous)stable_ms<=0;
 end
 RETRY:if(tick && elapsed>=BACKOFF_MS-1)begin state<=PREPARE;elapsed<=0;index<=0;gain_table<=0;end
 DEAD:begin req<=0;ready<=0;end
 endcase
 if((state==RUN || state==WAIT_FRAME) && gain_tag!=requested)begin ready<=0;gain_table<=1;index<=0;state<=PREPARE;elapsed<=0;good_frames<=0;end
 end end
endmodule
`default_nettype wire
