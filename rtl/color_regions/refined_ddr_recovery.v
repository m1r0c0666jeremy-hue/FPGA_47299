// Independent reference-clock supervisor remains alive when DDR user clock stops.
`default_nettype none
module refined_ddr_recovery #(parameter integer CYCLES_PER_MS=100000,INIT_MS=2000,RESET_MS=1,MAX_RETRIES=3)(
 input wire clk,rst_n,init_ready,fault_toggle,
 output wire controller_n,pipeline_n,output reg [15:0] epoch,recoveries,
 output reg [1:0] retries,output reg [3:0] reason,output wire failed);
 localparam WAIT_INIT=0,RUN=1,RESET=2,DEAD=3;
 reg [1:0] state;reg [16:0] subms;reg [10:0] elapsed,stable_ms;reg fault_previous;
 (* async_reg="true" *) reg [2:0] fault_sync;(* async_reg="true" *) reg [1:0] ready_sync;
 wire tick=subms==CYCLES_PER_MS-1;
 assign controller_n=rst_n && state!=RESET && state!=DEAD;
 assign pipeline_n=rst_n && state==RUN && ready_sync[1];
 assign failed=state==DEAD;
 task recover;input [3:0] why;begin
  reason<=why;elapsed<=0;stable_ms<=0;epoch<=epoch+1'b1;
  if(recoveries!=65535)recoveries<=recoveries+1'b1;
  if(retries<MAX_RETRIES)begin retries<=retries+1'b1;state<=RESET;end else state<=DEAD;
 end endtask
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin state<=WAIT_INIT;subms<=0;elapsed<=0;stable_ms<=0;epoch<=0;recoveries<=0;retries<=0;reason<=0;fault_previous<=0;fault_sync<=0;ready_sync<=0;end
 else begin
 fault_sync<={fault_sync[1:0],fault_toggle};ready_sync<={ready_sync[0],init_ready};fault_previous<=fault_sync[2];
 if(tick)begin subms<=0;if(elapsed<2047)elapsed<=elapsed+1'b1;end else subms<=subms+1'b1;
 case(state)
 WAIT_INIT:if(ready_sync[1])begin elapsed<=0;stable_ms<=0;state<=RUN;end else if(tick && elapsed>=INIT_MS-1)recover(5);
 RUN:begin
  if(!ready_sync[1])recover(3);
  else if(fault_sync[2]!=fault_previous)recover(4);
  if(tick && stable_ms<2000)begin stable_ms<=stable_ms+1'b1;if(stable_ms==1999)retries<=0;end
 end
 RESET:if(tick && elapsed>=RESET_MS-1)begin state<=WAIT_INIT;elapsed<=0;ready_sync<=0;end
 DEAD:begin end
 endcase
 end end
endmodule
`default_nettype wire
