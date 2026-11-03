"""New preset scheduler through the actual three-clock relay, supervisor and I2C."""
from refined_testlib import R,run

src=r'''`timescale 1ns/1ps
module tb #(parameter INJECT_NACK=0);
reg pc=0,refclk=0,cc=0,rst=0;always #6.667 pc=~pc;always #5 refclk=~refclk;always #21 cc=~cc;
reg [2:0] keys=7;wire request,up,ack,cam_req,cam_up,cam_ack,event_cam,ready_cam,event_ref,ready_ref;
wire [17:0] ui;wire [3:0] phase,fault;wire [1:0] retries;wire [6:0] requested,applied;
wire scl,receiver_enable;tri1 sda;reg frame_toggle=0;integer fc=0;
always @(posedge cc)if(rst)begin if(fc==3199)begin fc=0;frame_toggle<=~frame_toggle;end else fc=fc+1;end
reg [1:0] es=0;reg ep=0;wire pause=es[1]!=ep;
always @(posedge pc or negedge rst)if(!rst)begin es<=0;ep<=0;end else begin es<={es[0],event_ref};ep<=es[1];end
refined_camera_control_relay relay(refclk,cc,pc,rst,rst,request,up,cam_ack,event_cam,ready_cam,
 {ready_cam,phase,fault,retries,applied},cam_req,cam_up,ack,event_ref,ready_ref,ui);
wire [2:0] zoom,slot;wire tracking,show,conflict,pair,ce,cs,cl,rotate,down,k2,k3,k4,cancel,gb,gf;
wire [7:0] session;wire [1:0] diag,mode;
stage1_controls #(.CYCLES_PER_MS(1000)) controls(.I_clk(pc),.I_rst_n(rst),.I_keys_n(keys),.I_ui_switch(2'd0),
.I_gain_ack(ack),.I_cal_status(8'd0),.I_pause(pause),.I_camera(ui),.O_gain_req(request),.O_gain_up(up),
.O_zoom(zoom),.O_tracking(tracking),.O_show(show),.O_session(session),.O_conflict(conflict),.O_pair(pair),
.O_cal_enter(ce),.O_cal_sample(cs),.O_cal_cancel(cl),.O_rotate(rotate),.O_diag(diag),.O_ui_mode(mode),
.O_down2(down),.O_click2(k2),.O_click3(k3),.O_click4(k4),.O_cancel(cancel),.O_gain_busy(gb),.O_gain_failed(gf),.O_gain_slot(slot));
refined_camera_config #(.CYCLES_PER_MS(320),.CLK_DIV(23),.BOOT_MS(1),.TRANSACTION_MS(10),.FRAME_TIMEOUT_MS(100)) camera(
.clk(cc),.rst_n(rst),.gain_req(cam_req),.gain_up(cam_up),.frame_toggle(frame_toggle),.bad_frame_toggle(1'b0),
.gain_ack(cam_ack),.scl(scl),.sda(sda),.ready(ready_cam),.receiver_enable(receiver_enable),.parameter_event(event_cam),
.fault(fault),.retries(retries),.phase(phase),.requested_gain(requested),.applied_gain(applied));
wire used_nack;wire [31:0] sensor_writes,sensor_reads,sensor_restarts,sensor_errors;
wire [15:0] sensor_address;wire [7:0] sensor_value;
sc500_i2c_slave_model sensor(rst,scl,sda,INJECT_NACK && gb,2'd1,1'b0,16'h3e02,8'h01,
used_nack,sensor_writes,sensor_reads,sensor_restarts,sensor_errors,sensor_address,sensor_value);
integer acknowledgements=0;reg previous_ack=0;reg [6:0] previous_applied=0;
always @(negedge cc)if(rst)begin
if(cam_ack!=previous_ack)begin acknowledgements=acknowledgements+1;previous_ack=cam_ack;end
if(applied!=previous_applied)begin
if(previous_applied!=0 && applied!=previous_applied+1 && applied+1!=previous_applied)$fatal(1,"gain jumped without single steps");
previous_applied=applied;end end
task ms;input integer n;begin repeat(1000*n)@(negedge pc);end endtask
task await_gain;input integer wanted,wanted_slot;integer n;begin n=0;
while((ui[6:0]!=wanted || slot!=wanted_slot || gb || !ui[17]) && n<5000000)begin @(negedge pc);n=n+1;end
if(n==5000000 || gf)$fatal(1,"preset did not complete gain%0d/%0d slot%0d phase%0d fault%0d req%b ack%b waiting%b",ui[6:0],wanted,slot,phase,fault,request,ack,controls.gain_wait);
end endtask
task brightness;begin keys=6;ms(30);keys=7;ms(30);end endtask
initial begin repeat(5)@(negedge pc);rst=1;await_gain(90,5);
brightness;await_gain(105,6);if(acknowledgements!=15)$fatal(1,"105 ACK count %0d",acknowledgements);
brightness;await_gain(16,0);if(acknowledgements!=104)$fatal(1,"wrap ACK count %0d",acknowledgements);
if(INJECT_NACK && !used_nack)$fatal(1,"NACK not exercised");
if(sensor_errors!=0 || sensor_reads!=sensor_restarts)$fatal(1,"I2C wire protocol");
$display("STAGE1_CAMERA_PASS real-I2C/relay/presets90-105-16/104-complete-ACKs/parameter-events NACK=%0d retries=%0d",INJECT_NACK,retries);$finish;end
initial begin #150000000;$fatal(1,"camera test timeout");end
endmodule'''
mods=[R/'rtl/color_regions'/n for n in ('stage1_controls.v','stage1_top.v','refined_camera_config.v')]
mods += [R/'rtl/04_tracking/target_mailbox.v']
mods += [R/'user_source/hdl_source/uics500_cfg'/n for n in ('uics500reg_720p60.v','uics500regAE.v','SC500GainTbl.v','uii2c.v')]
mods += [R/'scripts/sc500_i2c_slave_model.v.txt']
for nack in (0,1):run('stage1_camera_'+str(nack),src,mods,compile_args=['-Ptb.INJECT_NACK='+str(nack)],timeout=600)
