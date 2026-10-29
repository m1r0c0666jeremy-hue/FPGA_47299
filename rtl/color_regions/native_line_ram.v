// Project-owned PH1P line memories. NOREG is the original one-cycle BRAM
// read latency; port B retains the vendor READBEFOREWRITE collision policy.
`default_nettype none
module native_line_ram #(parameter WIDTH=32,ADDR_BITS=10)(
 input wire clka,input wire wea,input wire [ADDR_BITS-1:0] addra,
 input wire [WIDTH-1:0] dia,input wire clkb,input wire [ADDR_BITS-1:0] addrb,
 output wire [WIDTH-1:0] dob);
`ifdef NATIVE_BEHAVIORAL_RAM
 reg [WIDTH-1:0] mem[0:(1<<ADDR_BITS)-1];reg [WIDTH-1:0] q;
 always @(posedge clka)if(wea)mem[addra]<=dia;
 always @(posedge clkb)q<=mem[addrb];
 assign dob=q;
`else
 PH1P_LOGIC_ERAM #(.DATA_WIDTH_A(WIDTH),.DATA_WIDTH_B(WIDTH),
 .ADDR_WIDTH_A(ADDR_BITS),.ADDR_WIDTH_B(ADDR_BITS),
 .DATA_DEPTH_A(1<<ADDR_BITS),.DATA_DEPTH_B(1<<ADDR_BITS),
 .MODE("DP"),.REGMODE_A("NOREG"),.REGMODE_B("NOREG"),
 .WRITEMODE_A("NORMAL"),.WRITEMODE_B("READBEFOREWRITE"),
 .IMPLEMENT("20K(FAST)"),.ECC_ENCODE("DISABLE"),.ECC_DECODE("DISABLE"),
 .CLKMODE("ASYNC"),.SSROVERCE("DISABLE"),.OREGSET_A("RESET"),.OREGSET_B("RESET"),
 .RESETMODE_A("ASYNC"),.RESETMODE_B("ASYNC"),
 .ASYNC_RESET_RELEASE_A("ASYNC"),.ASYNC_RESET_RELEASE_B("ASYNC"),
 .INIT_FILE("NONE"),.FILL_ALL("NONE")) ram(
 .dia(dia),.dib({WIDTH{1'b0}}),.addra(addra),.addrb(addrb),
 .cea(1'b1),.ceb(1'b1),.ocea(1'b0),.oceb(1'b0),.clka(clka),.clkb(clkb),
 .wea(wea),.web(1'b0),.bea(1'b0),.beb(1'b0),.rsta(1'b0),.rstb(1'b0),
 .doa(),.dob(dob),.ecc_sbiterr(),.ecc_dbiterr(),.ecc_sbiterrinj(1'b0),.ecc_dbiterrinj(1'b0));
`endif
endmodule
`default_nettype wire
