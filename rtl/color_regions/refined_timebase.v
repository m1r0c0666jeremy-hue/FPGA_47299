// 75 MHz pixel clock, one common microsecond epoch. Never stream-reset.
module refined_timebase(input wire clk,rst_n,output reg [31:0] us,output reg [31:0] gray);
reg [6:0] tick;
wire [31:0] next_us=us+1'b1;
always @(posedge clk or negedge rst_n)
if(!rst_n)begin tick<=0;us<=0;gray<=0;end
else if(tick==74)begin tick<=0;us<=next_us;gray<=(next_us>>1)^next_us;end
else tick<=tick+1'b1;
endmodule
module refined_gray_sync(input wire clk,rst_n,input wire [31:0] gray,output wire [31:0] binary);
(* async_reg="true" *) reg [31:0] g0,g1;
always @(posedge clk or negedge rst_n)
if(!rst_n)begin g0<=0;g1<=0;end else begin g0<=gray;g1<=g0;end
wire [31:0] a=g1^(g1>>16),b=a^(a>>8),c=b^(b>>4),d=c^(c>>2);
assign binary=d^(d>>1);
endmodule
