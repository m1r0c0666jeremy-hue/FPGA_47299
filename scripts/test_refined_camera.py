"""Configuration ACK, partial-gain failure, bounded retries and real I2C edges."""
from refined_testlib import R
from sc500_test_evidence import run
tables=[R/'user_source/hdl_source/uics500_cfg'/n for n in ('uics500reg_720p60.v','uics500regAE.v','SC500GainTbl.v')]
src=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,request=0,up=1,frame=0,badframe=0;
wire ack,scl,ready,en,event_toggle;tri1 sda;wire [3:0] fault,phase;wire [1:0] retries;wire [6:0] gain,applied;
refined_camera_config #(.CYCLES_PER_MS(CPM),.CLK_DIV(DIV),.BOOT_MS(1),.TRANSACTION_MS(2),.FRAME_TIMEOUT_MS(12),.BACKOFF_MS(2)) dut(
.clk(clk),.rst_n(rst),.gain_req(request),.gain_up(up),.frame_toggle(frame),.bad_frame_toggle(badframe),.gain_ack(ack),.scl(scl),.sda(sda),
.ready(ready),.receiver_enable(en),.parameter_event(event_toggle),.fault(fault),.retries(retries),.phase(phase),.requested_gain(gain),.applied_gain(applied));
integer mode=0,n=0,k=0,total=0;
ACK_DRIVER
task frames(input integer count);integer j;begin for(j=0;j<count;j=j+1)begin repeat(8)@(negedge clk);frame=~frame;end repeat(8)@(negedge clk);end endtask
task await_phase(input integer p);begin n=0;while(phase!=p && n<2000000)begin @(negedge clk);n=n+1;end if(phase!=p)$fatal(1,"phase timeout expected%0d got%0d index%0d fault%0d",p,phase,dut.index,fault);end endtask
initial begin if(!$value$plusargs("MODE=%d",mode))mode=0;repeat(5)@(negedge clk);rst=1;
 if(mode==0 || mode==5)begin
 await_phase(6);if(ready || ack!=0 || applied!=90)$fatal(1,"ready before frames or incomplete initial gain");frames(2);if(ready)$fatal(1,"two frames ready");
 badframe=~badframe;repeat(8)@(negedge clk);frames(2);if(ready)$fatal(1,"bad frame did not reset streak");frames(1);await_phase(7);
 request=1;repeat(8)@(negedge clk);if(ack || gain!=91 || ready || applied!=90)$fatal(1,"gain acknowledged before all writes");
 if(mode==5)begin await_phase(8);if(applied!=90 || ack || ready || fault!=1)$fatal(1,"partial gain NACK counted as applied");end
 await_phase(6);if(!ack || dut.gain_for_table!=91 || applied!=91)$fatal(1,"gain apply missing");frames(3);await_phase(7);
 if(!ready || retries!=(mode==5?1:0))$fatal(1,"normal result");
 $display("REFINED_CAMERA_PASS startup, ACK-complete gain, bad-frame confirmation reset, reapply and real framing");
 end else if(mode==1)begin
 await_phase(8);if(fault!=1 || retries!=1 || en)$fatal(1,"NACK retry");await_phase(6);frames(3);await_phase(7);
 if(!event_toggle || retries!=1)$fatal(1,"recovery did not invalidate model");
 $display("REFINED_CAMERA_NACK_PASS transient byte NACK, full soft-reset replay, stored gain and three-frame recovery");
 end else begin await_phase(9);
 if(retries!=3 || ready || en || fault!=(mode==4?3:2))$fatal(1,"unbounded retries mode%0d retries%0d fault%0d",mode,retries,fault);
 repeat(500)@(negedge clk);if(phase!=9)$fatal(1,"permanent failure restarted");
 $display("REFINED_CAMERA_FAILURE_PASS mode%0d initial+3 retries then latched failure",mode);end
 $finish;end
endmodule
STUB'''
stub=r'''module uii2c #(parameter WMEN_LEN=4,RMEN_LEN=1,CLK_DIV=1)(
 input I_clk,I_rstn,output O_iic_scl,inout IO_iic_sda,input [WMEN_LEN*8-1:0] I_wr_data,input [7:0] I_wr_cnt,
output reg [RMEN_LEN*8-1:0] O_rd_data=0,input [7:0] I_rd_cnt,input I_iic_req,I_iic_mode,output reg O_iic_busy=0,O_iic_bus_error=0,output IO_iic_sda_dg);
integer step=0,j;reg used_nack=0,transaction_failed=0;reg [7:0] registers[0:65535];
wire [15:0] address={I_wr_data[15:8],I_wr_data[23:16]};
assign O_iic_scl=1;assign IO_iic_sda=1'bz;
initial begin for(j=0;j<65536;j=j+1)registers[j]=0;registers[16'h3107]=8'hee;registers[16'h3108]=8'h27;end
always @(posedge I_clk or negedge I_rstn)begin
 if(!I_rstn)begin O_iic_busy<=0;O_iic_bus_error<=0;step<=0;transaction_failed<=0;end
 else begin
 O_iic_bus_error<=0;
 if(tb.mode!=2 && I_iic_req && !O_iic_busy)begin O_iic_busy<=1;step<=0;transaction_failed<=0;end
 if(O_iic_busy)begin
 step<=step+1;
 if(tb.mode==1 && !used_nack && step==2)begin O_iic_bus_error<=1;used_nack<=1;transaction_failed<=1;end
 if(tb.mode==5 && !used_nack && tb.request && tb.dut.gain_table && tb.dut.index==3 && step==2)begin O_iic_bus_error<=1;used_nack<=1;transaction_failed<=1;end
 if(tb.mode!=3 && step==6)begin
  O_iic_busy<=0;
  if(!transaction_failed)begin
   if(I_rd_cnt==1 && I_wr_cnt==3 && I_iic_mode)O_rd_data<=registers[address];
   else if(I_rd_cnt==0 && I_wr_cnt==4)registers[address]<=I_wr_data[31:24];
   else $fatal(1,"unexpected I2C transaction shape");
  end
 end
 end end end
endmodule'''
mods=[R/'rtl/color_regions/refined_camera_config.v',*tables]
for mode in range(6):
 code=src.replace('(CPM)','(10)').replace('(DIV)','(1)').replace('ACK_DRIVER','').replace('STUB',stub)
 run(f'camera_supervisor_{mode}',code,mods,args=[f'+MODE={mode}'])
# Actual I2C RTL plus a slave that receives and responds only through the pins.
wire_driver=r'''wire sensor_injected;wire [31:0] sensor_writes,sensor_reads,sensor_restarts,sensor_errors;
wire [15:0] sensor_address;wire [7:0] sensor_value;
sc500_i2c_slave_model sensor(rst,scl,sda,(mode==1 || (mode==5 && request)),2'd1,1'b0,
 mode==1?16'h0103:16'h3e02,8'h01,sensor_injected,sensor_writes,sensor_reads,sensor_restarts,sensor_errors,sensor_address,sensor_value);'''
code=src.replace('(CPM)','(24000)').replace('(DIV)','(239)').replace('STUB','').replace('ACK_DRIVER',wire_driver)
run('camera_real_i2c',code,[*mods,R/'user_source/hdl_source/uics500_cfg/uii2c.v',R/'scripts/sc500_i2c_slave_model.v.txt'],args=['+MODE=0'])
