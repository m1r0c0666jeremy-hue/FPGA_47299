module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;reg [2:0] nr;reg [15:0] counts;reg [671:0] vertices;
reg [3:0] nd;reg [167:0] draft;wire busy,done,passed;wire [3:0] error_code;
wire os,od;wire [20:0] oa,ob,oc;wire signed [23:0] oq;
stage1_point shared(.clk(clk),.rst_n(rst),.start(1'b0),.region_count(3'd0),.counts(16'd0),.vertices(672'd0),
.px(11'd0),.py(10'd0),.orientation_start(os),.oa(oa),.ob(ob),.oc(oc),.orientation_done(od),.orientation_cross(oq));
wire [4:0] address;wire [20:0] value=vertices>>(address*21);
stage1_validate #(.SHARED(1),.SHARED_VERTEX(1)) dut(clk,rst,start,nr,counts,vertices,nd,draft,busy,done,passed,error_code,os,oa,ob,oc,od,oq,address,value);
reg [863:0] vectors[0:220-1];reg ep;integer i,t,max_cycles=0;
initial begin $readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_geometry_vectors/validate.hex",vectors);repeat(3)@(negedge clk);rst=1;
for(i=0;i<220;i=i+1)begin
{vertices,counts,nr,draft,nd,ep}=vectors[i];start=1;@(negedge clk);start=0;t=0;
while(!done && t<100000)begin @(negedge clk);t=t+1;end
if(!done || passed!==ep)$fatal(1,"validation case%0d nr%0d nd%0d pass%b/%b error%0d state%0d i%0d j%0d",i,nr,nd,passed,ep,error_code,dut.state,dut.i,dut.j);
if(t>max_cycles)max_cycles=t;@(negedge clk);end
$display("STAGE1_VALIDATE_PASS cases=%0d max_cycles=%0d",220,max_cycles);$finish;end
endmodule