module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;reg [2:0] nr;reg [15:0] counts;
reg [671:0] vertices;reg [10:0] px;reg [9:0] py;wire busy,done;wire [3:0] im,nm;wire [43:0] ds;
stage1_point dut(clk,rst,start,nr,counts,vertices,px,py,busy,done,im,nm,ds,1'b0,21'd0,21'd0,21'd0,,);
reg [763:0] vectors[0:516-1];reg [3:0] ei,en;reg [43:0] ed;integer i,t,max_cycles=0;
initial begin $readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_geometry_vectors/point.hex",vectors);repeat(3)@(negedge clk);rst=1;
for(i=0;i<516;i=i+1)begin
{vertices,counts,nr,px,py,ei,en,ed}=vectors[i];start=1;@(negedge clk);start=0;t=0;
while(!done && t<20000)begin @(negedge clk);t=t+1;end
if(!done || im!==ei || nm!==en || ds!==ed)$fatal(1,"point case%0d p%0d/%0d inside%h/%h near%h/%h dist%h/%h state%0d",i,px,py,im,ei,nm,en,ds,ed,dut.state);
if(t>max_cycles)max_cycles=t;@(negedge clk);
end
$display("STAGE1_POINT_PASS cases=%0d max_cycles=%0d",516,max_cycles);$finish;end
endmodule