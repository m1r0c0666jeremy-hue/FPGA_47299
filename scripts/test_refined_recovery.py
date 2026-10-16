"""Late returns must drain before reuse; missing returns require shared reset."""
from refined_testlib import R,run
src=r'''`timescale 1ns/1ps
module tb;
reg pc=0,dc=0,rc=0;always #6.667 pc=~pc;always #7.5 dc=~dc;always #5 rc=~rc;
reg rst=0,commit=0;wire ctrl,stream,failed,fault_toggle;wire [15:0] epoch,recoveries;wire [1:0] retries;wire [3:0] reason;
refined_ddr_recovery #(.CYCLES_PER_MS(10),.INIT_MS(50)) supervisor(rc,rst,ctrl,fault_toggle,ctrl,stream,epoch,recoveries,retries,reason,failed);
wire [127:0] dd,pd;wire rd,busy;wire [24:0] addr;reg returned=0;reg [127:0] rddata=0;wire dready,dvalid;wire [127:0] dout;
wire en,wen,wend;wire [24:0] aa;wire [2:0] cmd;wire [127:0] wd;wire [15:0] wm;wire [9:0] outstanding;wire unexpected;wire [31:0] accepted;
refined_mc_to_user_interface adapter(.I_clk(dc),.I_rst_n(stream),.I_ddr_user_wr_en(1'b0),.I_ddr_user_rd_en(rd),.I_ddr_user_addr(addr),.I_ddr_user_wr_data(128'd0),
.O_ddr_user_ready(dready),.O_ddr_user_rd_valid(dvalid),.O_ddr_user_rd_data(dout),.O_mc_app_en(en),.O_mc_app_addr(aa),.O_mc_app_cmd(cmd),.I_mc_app_rdy(1'b1),
.O_mc_app_wdf_wren(wen),.O_mc_app_wdf_data(wd),.O_mc_app_wdf_end(wend),.O_mc_app_wdf_mask(wm),.I_mc_app_wdf_rdy(1'b1),
.I_mc_app_rd_data(rddata),.I_mc_app_rd_data_end(returned),.I_mc_app_rd_data_valid(returned),.O_write_commit(),.O_write_addr(),
.O_outstanding_reads(outstanding),.O_unexpected_return(unexpected),.O_accepted_reads(accepted));
reg vs=0,hs=0,de=0;wire ovs,ohs,ode,ok;wire [23:0] rgb;wire [1:0] mask;
stable_line_reader #(.JOB_TIMEOUT_CYCLES(1300),.DRAIN_TIMEOUT_CYCLES(1000)) dut(commit,1'b1,rst,dc,1'b0,1'b0,2'd0,32'd9,128'd0,
dready,dvalid,dout,busy,rd,addr,pc,vs,hs,de,11'd0,10'd48,2'd0,ovs,ohs,ode,rgb,mask,ok,1'b0,stream,fault_toggle,dd,pd,accepted,unexpected);
integer mode=0,cycle=0,tail=0,head=0,commands=0,returns=0,first_due=0,n=0,checks=0;
integer due[0:2047];reg drop_used=0;reg [1:0] vs_pipe=0,hs_pipe=0,de_pipe=0;integer pcycle=0;
always @(posedge pc)begin
 vs_pipe<={vs_pipe[0],vs};hs_pipe<={hs_pipe[0],hs};de_pipe<={de_pipe[0],de};pcycle=pcycle+1;
end
always @(negedge pc)begin
 if(rst && pcycle>20)begin if({ovs,ohs,ode}!={vs_pipe[1],hs_pipe[1],de_pipe[1]})$fatal(1,"HDMI sync interrupted by stream recovery");checks=checks+1;end
 vs=pcycle%31==0;hs=pcycle%7==0;de=pcycle%3==0;
end
always @(posedge dc)if(stream && en && cmd[0])begin
 if(commands==0)first_due=cycle;
 due[tail]=(commands==239 && !drop_used)?(mode==0?first_due+1500:1000000):cycle+37;
 if(commands==239)drop_used=1;
 tail=tail+1;commands=commands+1;
end
always @(negedge dc)begin
 cycle=cycle+1;returned=0;
 if(!ctrl)begin head=0;tail=0;commands=0;end
 else if(head<tail && due[head]<=cycle)begin returned=1;rddata=0;head=head+1;returns=returns+1;end
end
task newframe;begin @(negedge pc);commit=1;@(negedge pc);commit=0;end endtask
initial begin if(!$value$plusargs("MODE=%d",mode))mode=0;
 repeat(6)@(negedge rc);rst=1;wait(stream);repeat(8)@(negedge pc);newframe;
 if(mode==0)begin repeat(2100)@(negedge dc);
 if(recoveries!=0 || returns!=240 || outstanding!=0 || dd[87:76]!=1 || dut.state!=0)$fatal(1,"late return not safely drained rec%0d ret%0d out%0d state%0d diag%h",recoveries,returns,outstanding,dut.state,dd);
 $display("REFINED_DRAIN_PASS finite late final beat drained; no new task or reset reused outstanding data");
 end else begin
 n=0;while(recoveries==0 && n<4000)begin @(negedge dc);n=n+1;end
 if(recoveries!=1 || epoch!=1 || dd[75:72]!=4 || dd[71:63]!=239)$fatal(1,"missing beat recovery not diagnosed %h rec%0d",dd,recoveries);
 wait(stream);repeat(12)@(negedge pc);newframe;repeat(1800)@(negedge dc);
 if(recoveries!=1 || failed || outstanding!=0 || returns!=479)$fatal(1,"fresh task contaminated rec%0d out%0d ret%0d",recoveries,outstanding,returns);
 if(dd[87:76]<2 || checks<1000)$fatal(1,"fault disappeared across reset/sync coverage");
 $display("REFINED_RECOVERY_PASS permanent missing return, coordinated FIFO/controller reset, old queue discarded, fresh 240 words and continuous HDMI sync");end
 $finish;end
endmodule'''
mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('stable_line_reader','stable_model_lane','stable_filter4','refined_reset_bridge','refined_ddr_recovery','refined_mc_to_user_interface')]+[R/'rtl/04_tracking/target_mailbox.v',R/'user_source/ip_source/w155_d512_fifo/w155_d512_fifo.v',R/'user_source/ip_source/w155_d512_fifo/soft_fifo_al_f58e8b3e1f3d.v']
for mode in (0,1):run(f'video_recovery_{mode}',src,mods,args=[f'+MODE={mode}'])
budget=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,init=0,fault=0;wire ctrl,stream,dead;wire [15:0] epoch,count;wire [1:0] retry;wire [3:0] why;
refined_ddr_recovery #(.CYCLES_PER_MS(2),.INIT_MS(8)) dut(clk,rst,init,fault,ctrl,stream,epoch,count,retry,why,dead);
integer n,k;
initial begin repeat(5)@(negedge clk);rst=1;repeat(25)@(negedge clk);
if(count!=1 || why!=5)$fatal(1,"init timeout");init=1;wait(stream);
repeat(4)@(negedge clk);fault=~fault;wait(!ctrl);init=0;wait(ctrl);init=1;wait(stream);
repeat(4)@(negedge clk);fault=~fault;wait(!ctrl);init=0;wait(ctrl);init=1;wait(stream);
repeat(4)@(negedge clk);fault=~fault;wait(dead);
@(negedge clk);if(count!=4 || retry!=3 || stream || ctrl)$fatal(1,"retry budget count%0d retry%0d stream%b ctrl%b",count,retry,stream,ctrl);
repeat(30)@(negedge clk);if(!dead)$fatal(1,"failure not held");
$display("REFINED_RECOVERY_BUDGET_PASS initial timeout, three restarts then latched failure; reference clock stays alive");$finish;end
initial begin #100000;$fatal(1,"budget test stuck");end endmodule'''
run('recovery_budget',budget,[R/'rtl/color_regions/refined_ddr_recovery.v'])
