"""Independent wire-level SC500 reads, publication, documented masks and failures."""
from refined_testlib import R, run

src = r'''`timescale 1ns/1ps
module tb #(parameter MODE=0,FAULT_SLOT=4);
reg clk=0,rst=0,request=0,up=1,frame=0,badframe=0;
always #5 clk=~clk;
wire ack,scl,ready,en,event_toggle;tri1 sda;
wire [3:0] fault,phase;wire [1:0] retries;wire [6:0] gain,applied;
refined_camera_config #(.CYCLES_PER_MS(MODE==7?40:1000),.CLK_DIV(7),.BOOT_MS(1),
 .TRANSACTION_MS(2),.FRAME_TIMEOUT_MS(12),.BACKOFF_MS(2)) dut(
 .clk(clk),.rst_n(rst),.gain_req(request),.gain_up(up),.frame_toggle(frame),.bad_frame_toggle(badframe),
 .gain_ack(ack),.scl(scl),.sda(sda),.ready(ready),.receiver_enable(en),.parameter_event(event_toggle),
 .fault(fault),.retries(retries),.phase(phase),.requested_gain(gain),.applied_gain(applied));
function [15:0] gain_address;input integer slot;begin
 case(slot)0:gain_address=16'h3e03;1:gain_address=16'h3e00;2:gain_address=16'h3e01;
 3:gain_address=16'h3e02;4:gain_address=16'h3e08;default:gain_address=16'h3e09;endcase
end endfunction
function [7:0] mask_at;input integer slot;begin mask_at=slot==0?8'h0f:slot==3?8'hf0:8'hff;end endfunction
// Independent piecewise decoding of the documented gain stages; no RTL table access.
function [15:0] expected_analogue;input integer value;begin
 if(value<48)expected_analogue=16'h0320+value-16;
 else if(value<80)expected_analogue=16'h0720+value-48;
 else if(value<90)expected_analogue=16'h0f20+value-80;
 else expected_analogue=16'h1f20+value-90;
end endfunction
function [7:0] expected_byte;input integer slot,value;reg [15:0] a;begin
 a=expected_analogue(value);
 case(slot)0:expected_byte=8'h0b;1:expected_byte=0;2:expected_byte=8'h7c;
 3:expected_byte=8'h60;4:expected_byte=a[15:8];default:expected_byte=a[7:0];endcase
end endfunction
wire injected;wire [31:0] writes,reads,restarts,protocol_errors;
wire [15:0] last_address;wire [7:0] last_value;
wire arm=MODE==2 || MODE==3 || MODE==4 || MODE==5 || MODE==6 || MODE==11;
wire [1:0] inject_kind=MODE==5 || MODE==11?2:MODE==6?1:3;
wire [15:0] inject_address=MODE==4?(FAULT_SLOT==0?16'h3107:16'h3108):gain_address(FAULT_SLOT);
sc500_i2c_slave_model #(.RESERVED_NOISE(MODE==1)) sensor(rst,scl,sda,arm,inject_kind,
 MODE==3 || MODE==4 || MODE==11,inject_address,FAULT_SLOT==3?8'h10:8'h01,
 injected,writes,reads,restarts,protocol_errors,last_address,last_value);
integer observed_reads=0,oracle_gain=90,slot,previous_applied=0,published_reads=0;
reg forbid_old=0;
always @(negedge clk)if(rst)begin
 if(forbid_old && (applied==91 || ack==1))$fatal(1,"superseded gain published applied%0d ack%b",applied,ack);
 if((MODE==0 || MODE==1) && reads!=observed_reads)begin
  if(reads!=observed_reads+1)$fatal(1,"read observation skipped");
  if(reads<=2)begin
   if(last_address!=(reads==1?16'h3107:16'h3108) || last_value!=(reads==1?8'hee:8'h27))$fatal(1,"sensor ID wire read");
  end else begin
   slot=(reads-3)%6;
   if(last_address!=gain_address(slot))$fatal(1,"read order %h slot%0d",last_address,slot);
   if((last_value & mask_at(slot))!=(expected_byte(slot,oracle_gain) & mask_at(slot)))
    $fatal(1,"independent gain oracle %h got%h wanted%h gain%0d",last_address,last_value,expected_byte(slot,oracle_gain),oracle_gain);
  end
  observed_reads=reads;
 end
 if((MODE==0 || MODE==1) && applied!=previous_applied)begin
  if(applied!=oracle_gain || reads-published_reads!=(previous_applied==0?8:6))$fatal(1,"publication before all reads");
  published_reads=reads;previous_applied=applied;
 end
end
task await_phase;input integer wanted;integer n;begin
 n=0;while(phase!=wanted && n<2000000)begin @(negedge clk);n=n+1;end
 if(phase!=wanted)$fatal(1,"phase timeout mode%0d want%0d got%0d fault%0d op%0d index%0d reads%0d",MODE,wanted,phase,fault,dut.operation,dut.index,reads);
end endtask
task frames;input integer count;integer j;begin
 for(j=0;j<count;j=j+1)begin repeat(10)@(negedge clk);frame=~frame;end
 repeat(10)@(negedge clk);
end endtask
task settle;begin frames(3);await_phase(7);if(!ready)$fatal(1,"ready absent");end endtask
task step_gain;input integer wanted;begin
 oracle_gain=wanted;up=wanted>applied;request=~request;
 repeat(10)@(negedge clk);if(ready)$fatal(1,"gain request did not stop camera admission");
 await_phase(6);if(applied!=wanted || ack!=request || ready)$fatal(1,"verified gain or ACK");settle;
end endtask
task goto_gain;input integer wanted;begin
 while(applied!=wanted)step_gain(applied<wanted?applied+1:applied-1);
end endtask
integer before_writes,before_reads;
initial begin
 repeat(5)@(negedge clk);rst=1;
 if(MODE==3 || MODE==4 || MODE==7 || MODE==11)begin
  await_phase(9);
  if(retries!=3 || ready || applied!=0 || ack!=0 || fault!=(MODE==4?5:MODE==7?2:MODE==11?1:4))$fatal(1,"unbounded/error publication mode%0d fault%0d",MODE,fault);
  before_writes=writes;before_reads=reads;repeat(2000)@(negedge clk);
  if(phase!=9 || writes!=before_writes || reads!=before_reads)$fatal(1,"latched failure restarted");
 end else begin
  if(MODE==2 || MODE==5 || MODE==6)begin
   await_phase(8);if(applied!=0 || ack || ready || fault!=(MODE==2?4:1) || !injected)$fatal(1,"partial apply on fault");
  end
  await_phase(6);
  if(applied!=90 || ack || ready)$fatal(1,"startup verified state");
  frames(2);if(ready)$fatal(1,"ready before three frames");
  badframe=~badframe;repeat(10)@(negedge clk);frames(2);if(ready)$fatal(1,"bad frame did not restart confirmation");
  frames(1);await_phase(7);
  if(MODE==2 || MODE==5 || MODE==6)begin if(retries!=1)$fatal(1,"recovery retry count");end
  if(MODE==0)begin goto_gain(105);goto_gain(16);goto_gain(32);goto_gain(48);goto_gain(64);goto_gain(80);goto_gain(90);end
  if(MODE==1)step_gain(91);
  if(MODE==8 || MODE==9 || MODE==10)begin
   request=1;up=1;
   while(reads<(MODE==9?14:9))@(negedge clk);
   if(applied!=90 || ack)$fatal(1,"published during pending read");
   if(MODE==10)begin
    rst=0;repeat(10)@(negedge clk);request=0;rst=1;await_phase(6);
   end else begin
    forbid_old=1;up=0;request=0;repeat(10)@(negedge clk);await_phase(6);
   end
   if(applied!=90 || ack || ready)$fatal(1,"supersession/reset result");settle;
  end
 end
 if(MODE!=7 && protocol_errors!=0)$fatal(1,"wire protocol errors %0d",protocol_errors);
 if(MODE!=7 && reads!=restarts)$fatal(1,"read/repeated-start mismatch %0d/%0d",reads,restarts);
 $display("STAGE1_CAMERA_READBACK_PASS MODE=%0d SLOT=%0d writes=%0d reads=%0d repeated_starts=%0d fault=%0d retries=%0d",MODE,FAULT_SLOT,writes,reads,restarts,fault,retries);
 $finish;
end
initial begin #100000000;$fatal(1,"wire readback watchdog");end
endmodule'''

mods = [R/'rtl/color_regions/refined_camera_config.v']
mods += [R/'user_source/hdl_source/uics500_cfg'/n for n in
         ('uics500reg_720p60.v', 'uics500regAE.v', 'SC500GainTbl.v', 'uii2c.v')]
mods += [R/'scripts/sc500_i2c_slave_model.v.txt']
cases = [('all_presets', 0, 4), ('reserved_bits', 1, 4)]
cases += [(f'mismatch_{slot}', 2, slot) for slot in range(6)]
cases += [('persistent_mismatch', 3, 4), ('id_high', 4, 0), ('id_low', 4, 1),
          ('read_nack', 5, 4), ('write_nack', 6, 4), ('timeout', 7, 4),
          ('superseded_first', 8, 4), ('superseded_last', 9, 4),
          ('reset_read', 10, 4), ('persistent_read_nack', 11, 4)]
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=[name for name, _, _ in cases])
    selected = parser.parse_args().case
    for name, mode, slot in cases:
        if selected is None or selected == name:
            run('stage1_camera_readback_'+name, src, mods,
                compile_args=[f'-Ptb.MODE={mode}', f'-Ptb.FAULT_SLOT={slot}'], timeout=600)
