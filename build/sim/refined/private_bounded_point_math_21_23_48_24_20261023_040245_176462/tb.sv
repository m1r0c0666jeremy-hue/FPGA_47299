module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;reg [1:0] op;reg [47:0] a,b;wire busy,done;wire [47:0] value,rem;
stage1_arith #(.MW(21),.DW(23),.NW(48),.SW(24)) dut(clk,rst,start,op,a,b,busy,done,value,rem);
reg [147:0] v[0:2049-1];reg [47:0] expected;integer i,t,want_latency;
initial begin $readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_arith_vectors/math_21_23.hex",v);repeat(3)@(negedge clk);rst=1;
for(i=0;i<2049;i=i+1)begin
{op,a,b,expected}=v[i];start=1;@(negedge clk);start=0;t=0;
while(!done && t<60)begin @(negedge clk);t=t+1;end
if(!done || value!==expected)$fatal(1,"arith case%0d op%0d a%h b%h got%h want%h",i,op,a,b,value,expected);
if(op==1 && b!=0 && rem!==a%b)$fatal(1,"division residue");
want_latency=op==0?21:op==1?(b==0?1:48):24;
if(t!=want_latency || busy)$fatal(1,"arithmetic changed latency %0d/%0d",t,want_latency);
@(negedge clk);end
$display("STAGE1_ARITH_PASS width=%0d divisor=%0d cases=%0d",21,23,2049);$finish;end endmodule