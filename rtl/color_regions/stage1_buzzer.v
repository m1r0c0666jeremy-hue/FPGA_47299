// C12 drives a low-side transistor: high is silent. 2kHz, 200ms on per second.
`default_nettype none
module stage1_buzzer #(parameter CLOCK_HZ=50000000)(input wire clk,rst_n,alarm_async,output wire buzzer);
 (* async_reg="true" *)reg [1:0] enable_sync;
 reg [25:0] period_count;reg [14:0] tone_count;reg tone;
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin enable_sync<=0;period_count<=0;tone_count<=0;tone<=1;end
 else begin enable_sync<={enable_sync[0],alarm_async};
 if(!enable_sync[1])begin period_count<=0;tone_count<=0;tone<=1;end
 else begin
 if(period_count==CLOCK_HZ-1)period_count<=0;else period_count<=period_count+1'b1;
 if(tone_count==CLOCK_HZ/4000-1)begin tone_count<=0;tone<=~tone;end else tone_count<=tone_count+1'b1;
 end end end
 assign buzzer=(!rst_n || !enable_sync[1] || period_count>=CLOCK_HZ/5)?1'b1:tone;
endmodule
`default_nettype wire
