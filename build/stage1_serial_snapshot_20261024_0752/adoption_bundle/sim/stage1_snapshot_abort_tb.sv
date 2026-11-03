module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,rrst=0,c=0,rc=0;reg[671:0] v=0;
wire[3:0]m,rm;wire[23:0]color,rcolor,lc,rlc;wire lon,rlon,ready,rready,u,ru;wire[7:0]g,rg;wire[2:0]gx,rgx;wire[3:0]gy,rgy;
stage1_render dut(clk,rst,c,v,16'h0003,4'h1,2'd2,11'd0,10'd200,3'd0,1'b0,4'd0,4'd0,3'd0,3'd0,11'd0,10'd0,1'b0,m,color,lon,g,gx,gy,lc,ready,u,168'd0,3'd0,1'b0);
stage1_render_clean_reference refdut(clk,rrst,rc,v,16'h0003,4'h1,2'd2,11'd0,10'd200,3'd0,1'b0,4'd0,4'd0,3'd0,3'd0,11'd0,10'd0,1'b0,rm,rcolor,rlon,rg,rgx,rgy,rlc,rready,ru,168'd0,3'd0,1'b0);

integer k,cases=0,case_id,wait_clocks=0,max_wait=0;
always @(posedge clk)if(!rst)wait_clocks=0;else if(dut.state==22 && dut.mbusy)wait_clocks=wait_clocks+1;
initial begin
for(case_id=0;case_id<8;case_id=case_id+1)begin
@(negedge clk);rst=0;rrst=0;c=0;rc=0;v=0;
v[20:0]={10'd100,11'd100};v[41:21]={10'd200,11'd600};v[62:42]={10'd500,11'd200};
repeat(3)@(negedge clk);rst=1;c=1;@(negedge clk);c=0;
case(case_id)
0:wait(dut.mstart && dut.mop==1 && !dut.mbusy);
1:wait(dut.mbusy && dut.line_alu.mode==1 && dut.line_alu.count==0);
2:wait(dut.mbusy && dut.line_alu.mode==1 && dut.line_alu.count==1);
3:wait(dut.mbusy && dut.line_alu.mode==1 && dut.line_alu.count==23);
4:wait(dut.mbusy && dut.line_alu.mode==1 && dut.line_alu.count==46);
5:wait(dut.mbusy && dut.line_alu.mode==1 && dut.line_alu.count==47);
6:wait(dut.mbusy && dut.line_alu.mode==0 && dut.line_alu.count==0);
7:wait(dut.mbusy && dut.line_alu.mode==0 && dut.line_alu.count==13);
endcase
@(negedge clk);v=0;v[20:0]={10'd100,11'd200};v[41:21]={10'd500,11'd300};v[62:42]={10'd300,11'd600};rrst=1;c=1;rc=1;
@(negedge clk);c=0;rc=0;repeat(12000)@(negedge clk);
if(!ready || !rready || u || ru)$fatal(1,"mid-operation recommit readiness differs case%0d ready%0d/%0d under%0d/%0d",case_id,ready,rready,u,ru);
for(k=0;k<640;k=k+1)if(dut.state_line_mem[k]!==refdut.state_line_mem[k])$fatal(1,"mid-operation row word differs case%0d word%0d",case_id,k);
for(k=768;k<1024;k=k+1)if(dut.state_line_mem[k]!==refdut.state_line_mem[k])$fatal(1,"mid-operation edge word differs case%0d word%0d",case_id,k);
if(wait_clocks>51)$fatal(1,"arithmetic drain exceeded bounded latency");if(wait_clocks>max_wait)max_wait=wait_clocks;
cases=cases+1;$display("SERIAL_ABORT_CASE_PASS case%0d words896 wait%0d",case_id,wait_clocks);
end
if(cases!=8 || max_wait==0)$fatal(1,"arithmetic abort coverage incomplete");
$display("SERIAL_SNAPSHOT_MID_LAUNCH_RECOMMIT_PASS cases=8 words=7168 max_wait=%0d",max_wait);$finish;
end endmodule