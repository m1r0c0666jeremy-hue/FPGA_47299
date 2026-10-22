module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;reg [1:0] op=0;reg [47:0] a=0,b=0;
wire bo,do_,bn,dn;wire [47:0] ro,rmo,rn,rmn;
baseline_arith #(.MW(24),.DW(14)) old(clk,rst,start,op,a,b,bo,do_,ro,rmo);
stage1_arith #(.MW(24),.DW(14)) candidate(clk,rst,start,op,a,b,bn,dn,rn,rmn);
reg [63:0] random_state=64'h1054a8c1329f607d;integer i,checks=0,resets=0;
task compare;begin
 if({bo,do_,ro,rmo}!=={bn,dn,rn,rmn})$fatal(1,"reset-free mismatch cycle%0d reset%b start%b op%0d old%b/%b/%h/%h new%b/%b/%h/%h",i,rst,start,op,bo,do_,ro,rmo,bn,dn,rn,rmn);
 checks=checks+1;end endtask
always @(posedge clk)begin #1;compare;end
always @(negedge rst)begin #1;compare;end
initial begin repeat(3)@(negedge clk);
for(i=0;i<200000;i=i+1)begin
 random_state=random_state^(random_state<<13);random_state=random_state^(random_state>>7);random_state=random_state^(random_state<<17);
 a=random_state[47:0];b={random_state[31:0],random_state[63:48]};op=random_state[49:48];start=random_state[50];
 if(i%257==0)begin rst=0;resets=resets+1;end else rst=1;
 if(i%1319==0)begin #2;rst=0;resets=resets+1;#2;rst=1;end
 @(negedge clk);
end
$display("PRIVATE_BOUNDED_DEFAULT_EQ_PASS MW%0d DW%0d comparisons%0d resets%0d",24,14,checks,resets);$finish;end endmodule