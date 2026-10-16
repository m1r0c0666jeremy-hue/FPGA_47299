"""Real vendor command FIFO plus real wrapper, independently stalled PAXI ports."""
from refined_testlib import R,run
vendor=[R/'user_source/ip_source/w155_d512_fifo/w155_d512_fifo.v',R/'user_source/ip_source/w155_d512_fifo/soft_fifo_al_f58e8b3e1f3d.v']
src=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg wr=0,rd=0;reg [24:0] addr=0;reg [127:0] data=0;
wire ready,rv,en,wren,wend,ar,dr;wire [24:0] ma;wire [2:0] cmd;wire [127:0] wd,rdata,md;
wire [15:0] mask;wire rend,mv,commit;wire [24:0] committed;wire [9:0] outstanding;wire unexpected;
refined_mc_to_user_interface dut(.I_clk(clk),.I_rst_n(rst),.I_ddr_user_wr_en(wr),.I_ddr_user_rd_en(rd),.I_ddr_user_addr(addr),.I_ddr_user_wr_data(data),
.O_ddr_user_ready(ready),.O_ddr_user_rd_valid(rv),.O_ddr_user_rd_data(rdata),.O_mc_app_en(en),.O_mc_app_addr(ma),.O_mc_app_cmd(cmd),.I_mc_app_rdy(ar),
.O_mc_app_wdf_wren(wren),.O_mc_app_wdf_data(wd),.O_mc_app_wdf_end(wend),.O_mc_app_wdf_mask(mask),.I_mc_app_wdf_rdy(dr),
.I_mc_app_rd_data(md),.I_mc_app_rd_data_end(rend),.I_mc_app_rd_data_valid(mv),.O_write_commit(commit),.O_write_addr(committed),.O_outstanding_reads(outstanding),.O_unexpected_return(unexpected));
refined_ph1p35_ddr_wrapper ctl(.I_sys_clk(clk),.I_sys_rst_n(rst),.I_mc_app_addr(ma),.I_mc_app_cmd(cmd),.I_mc_app_en(en),
.I_mc_app_wdf_data(wd),.I_mc_app_wdf_end(wend),.I_mc_app_wdf_mask(mask),.I_mc_app_wdf_wren(wren),.O_mc_app_rd_data(md),
.O_mc_app_rd_data_end(rend),.O_mc_app_rd_data_valid(mv),.O_mc_app_rdy(ar),.O_mc_app_wdf_rdy(dr));
integer emitted=0,reads=0,writes=0,returns=0,cycles=0;
always @(posedge clk)if(rst)begin
 cycles=cycles+1;
 if(commit)begin if(committed%24==8)$fatal(1,"read marked committed write");writes=writes+1;end
 if(rv)begin
  if(rdata!==128'(24*returns+8))$fatal(1,"read return order %0d got%h",returns,rdata);
  returns=returns+1;
 end
 if(unexpected)$fatal(1,"unexpected return");
end
initial begin repeat(5)@(negedge clk);rst=1;repeat(8)@(negedge clk);
 while(emitted<1800)begin
  @(negedge clk);wr=0;rd=0;
  if(ready)begin addr=emitted*8;data={4{32'(emitted*8)}};rd=emitted%3==1;wr=!rd;emitted=emitted+1;end
 end
 @(negedge clk);wr=0;rd=0;
 while((returns<600 || writes<1200 || outstanding!=0) && cycles<30000)@(negedge clk);
 if(returns!=600 || writes!=1200 || ctl.u_ddr2.arcount!=600 || ctl.u_ddr2.awcount!=1200 || ctl.u_ddr2.wcount!=1200)$fatal(1,"lost/duplicate commands %0d/%0d AR%0d AW%0d W%0d",returns,writes,ctl.u_ddr2.arcount,ctl.u_ddr2.awcount,ctl.u_ddr2.wcount);
 $display("REFINED_DDR_PASS 1800 FIFO commands, 1200 independent AW/W commits, 600 ordered reads; split ready, stable payload and full queue pressure");$finish;end
endmodule
module ddr2(input ref_clk,sys_rst_n,apb_pclk,apb_prst_n,output dhi_clk,ddrphy_rdy,cfg_clk,ddrphy_rst_n,
input [24:0] paxi_awaddr,input paxi_awvalid,output paxi_awready,input [127:0] paxi_wdata,input [15:0] paxi_wstrb,input paxi_wvalid,paxi_wlast,output paxi_wready,
input [24:0] paxi_araddr,input paxi_arvalid,output paxi_arready,output reg [127:0] paxi_rdata,output paxi_rlast,output reg paxi_rvalid,input paxi_rready,
output [12:0] ddr_addr,output [1:0] ddr_ba,output ddr_cke,ddr_odt,ddr_cs_n,ddr_ras_n,ddr_cas_n,ddr_we_n,ddr_ck_p,ddr_ck_n,inout [1:0] ddr_dm,inout [15:0] ddr_dq,inout [1:0] ddr_dqs_p,ddr_dqs_n);
assign dhi_clk=ref_clk;assign ddrphy_rdy=sys_rst_n;
integer cycle=0,arcount=0,awcount=0,wcount=0,head=0,tail=0,k;
integer queue[0:2047],due[0:2047];reg [15:0] lfsr=16'h5237;
assign paxi_arready=sys_rst_n && cycle>=75 && lfsr[0];
assign paxi_awready=sys_rst_n && (cycle<75 || lfsr[2]);
assign paxi_wready=sys_rst_n && cycle>=105 && lfsr[4];
assign paxi_rlast=paxi_rvalid;
reg held_ar=0,held_aw=0,held_w=0;reg [24:0] old_ar,old_aw;reg [127:0] old_w;
always @(posedge ref_clk)if(sys_rst_n)begin
 cycle=cycle+1;
 if(held_ar && (!paxi_arvalid || paxi_araddr!==old_ar))$fatal(1,"AR not held");
 if(held_aw && (!paxi_awvalid || paxi_awaddr!==old_aw))$fatal(1,"AW not held");
 if(held_w && (!paxi_wvalid || paxi_wdata!==old_w))$fatal(1,"W not held");
 held_ar=paxi_arvalid && !paxi_arready;held_aw=paxi_awvalid && !paxi_awready;held_w=paxi_wvalid && !paxi_wready;
 old_ar=paxi_araddr;old_aw=paxi_awaddr;old_w=paxi_wdata;
 if(paxi_arvalid && paxi_arready)begin
  if(paxi_araddr!=24*arcount+8)$fatal(1,"read address lost %0d got%0d",arcount,paxi_araddr);
  queue[tail]=paxi_araddr;due[tail]=cycle+11+(arcount%17);tail=tail+1;arcount=arcount+1;
 end
 if(paxi_awvalid && paxi_awready)begin
  k=awcount+(awcount+1)/2;
  if(paxi_awaddr!=k*8)$fatal(1,"write address order %0d got%0d expected%0d",awcount,paxi_awaddr,k*8);awcount=awcount+1;
 end
 if(paxi_wvalid && paxi_wready)begin
  k=wcount+(wcount+1)/2;
  if(paxi_wdata!=={4{32'(k*8)}} || paxi_wstrb!=0 || !paxi_wlast)$fatal(1,"write data/mask %0d",wcount);wcount=wcount+1;
 end
end
always @(negedge ref_clk)begin
 lfsr<={lfsr[14:0],lfsr[15]^lfsr[13]^lfsr[12]^lfsr[10]};paxi_rvalid=0;
 if(sys_rst_n && head<tail && due[head]<=cycle && lfsr[7])begin paxi_rvalid=1;paxi_rdata=queue[head];head=head+1;end
end
endmodule'''
run('ddr_handshake',src,[R/'rtl/color_regions/refined_mc_to_user_interface.v',R/'rtl/color_regions/refined_ph1p35_ddr_wrapper.v',*vendor])

counterexample=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,rd=0,arready=0;wire ready,en,wren,wend;wire [24:0] addr;wire [2:0] cmd;wire [127:0] data;wire [31:0] mask;integer accepted=0;
wire appready=READY_EXPR;
ADAPTER dut(.I_clk(clk),.I_rst_n(rst),.I_ddr_user_wr_en(1'b0),.I_ddr_user_rd_en(rd),.I_ddr_user_addr(25'd1232),.I_ddr_user_wr_data(128'd0),
.O_ddr_user_ready(ready),.O_ddr_user_rd_valid(),.O_ddr_user_rd_data(),.O_mc_app_en(en),.O_mc_app_addr(addr),.O_mc_app_cmd(cmd),.I_mc_app_rdy(appready),
.O_mc_app_wdf_wren(wren),.O_mc_app_wdf_data(data),.O_mc_app_wdf_end(wend),.O_mc_app_wdf_mask(mask),.I_mc_app_wdf_rdy(1'b1),
.I_mc_app_rd_data(128'd0),.I_mc_app_rd_data_end(1'b0),.I_mc_app_rd_data_valid(1'b0));
always @(posedge clk)if(rst && en && cmd[0] && arready)begin if(addr!=1232)$fatal(1,"payload");accepted=accepted+1;end
initial begin repeat(5)@(negedge clk);rst=1;repeat(8)@(negedge clk);rd=1;@(negedge clk);rd=0;
repeat(20)@(negedge clk);arready=1;repeat(20)@(negedge clk);
if(accepted!=EXPECTED)$fatal(1,"counterexample accepted %0d",accepted);
$display("COUNTEREXAMPLE_PASS LABEL accepted%0d with AWREADY=1 ARREADY=0 then released",accepted);$finish;end endmodule'''
for before in (True,False):
    name='mc_to_user_interface' if before else 'refined_mc_to_user_interface'
    code=counterexample.replace('ADAPTER',name).replace('READY_EXPR',"1'b1" if before else "cmd[0]?arready:1'b1").replace('EXPECTED','0' if before else '1').replace('LABEL','baseline_loses_read' if before else 'refined_preserves_read')
    module=R/'user_source/hdl_source/mc_to_user_interface.v' if before else R/'rtl/color_regions/refined_mc_to_user_interface.v'
    run('ddr_counterexample_before' if before else 'ddr_counterexample_after',code,[module,*vendor])

bank=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,beginf=0,write=0,snapshot=0;reg [1:0] bank=0;reg [31:0] id=10;reg [24:0] addr=0;
wire snap,good;wire [674:0] data;
stable_frame_store #(.WORDS(3)) dut(clk,rst,beginf,bank,id,write,addr,1'b0,640'd0,snapshot,10'd0,snap,data,good);
task begin_bank(input [1:0] b,input [31:0] n);begin @(negedge clk);bank=b;id=n;beginf=1;@(negedge clk);beginf=0;end endtask
task beat(input [24:0] a);begin @(negedge clk);addr=a;write=1;@(negedge clk);write=0;end endtask
task view;begin @(negedge clk);snapshot=1;@(negedge clk);snapshot=0;@(negedge clk);end endtask
initial begin repeat(4)@(negedge clk);rst=1;
begin_bank(0,10);beat(0);beat(8);view;if(data[674])$fatal(1,"incomplete bank published");
begin_bank(1,11);beat(16);view;if(!good || data[673:672]!=0 || data[671:640]!=10)$fatal(1,"late previous bank commit lost");
beat(7000000);beat(7000008);beat(7000016);view;if(!good || data[673:672]!=1 || data[671:640]!=11)$fatal(1,"new bank incomplete");
begin_bank(1,12);if(good)$fatal(1,"reuse not invalidated");beat(7000000);beat(7000016);beat(7000008);view;
if(data[673:672]==1)$fatal(1,"bad address frame published");
$display("REFINED_BANK_COMMIT_PASS pending frame tail survives next bank begin; incomplete, reused and out-of-order banks rejected");$finish;end endmodule'''
run('bank_actual_commit',bank,[R/'rtl/color_regions/stable_frame_store.v'])
