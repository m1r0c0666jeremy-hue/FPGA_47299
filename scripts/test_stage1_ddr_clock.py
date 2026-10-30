"""Clock/reset boundary and real reader drain at corrected133.333MHz."""
from refined_testlib import R,run,literal_fixture
from stage1_ddr_contract import contract

def main():
    print('DDR_REFERENCE_CONTRACT',contract(),flush=True)
    src=r'''`timescale 1ns/1ps
module tb;
reg refclk=0,sysclk=0,rst=0,ready=0,fault=0;
always #5 refclk=~refclk;always #10 sysclk=~sysclk;
wire ctrl,stream,dead,refreset;wire [15:0] epoch,count;wire [1:0] retry;wire [3:0] why;
refined_ddr_recovery #(.CYCLES_PER_MS(50000),.INIT_MS(1)) dut(sysclk,rst,ready,fault,ctrl,stream,epoch,count,retry,why,dead);
refined_reset_bridge bridge(refclk,ctrl,refreset);
integer edges=0,ms_count=0;reg old_ctrl=0;time asserted;
always @(negedge ctrl)begin asserted=$time;#0.001;if(refreset!==0)$fatal(1,"DDR reset assertion not immediate");end
task release_check;begin
wait(ctrl);edges=0;while(!refreset)begin @(posedge refclk);#0.001;edges=edges+1;if(edges>2)$fatal(1,"release too late");end
if(edges!=2)$fatal(1,"release not two ref edges");end endtask
initial begin #1;rst=0;repeat(4)@(negedge sysclk);rst=1;release_check;
wait(!ctrl);if(why!=5 || count!=1)$fatal(1,"init timeout not diagnosed");
wait(ctrl);if($time-asserted<999980 || $time-asserted>1000020)$fatal(1,"50MHz supervisor reset duration changed");
ready=1;release_check;wait(stream);fault=~fault;wait(!ctrl);ready=0;wait(ctrl);release_check;ready=1;wait(stream);
if(count!=2 || epoch!=2 || dead || why!=4)$fatal(1,"fault recovery identity");
#3;rst=0;#0.001;if(ctrl || stream || refreset)$fatal(1,"global assertion not immediate");
$display("STAGE1_DDR_REFERENCE_PASS reference100/supervisor50/reset2edges/real1ms-reset/epoch");$finish;end
initial begin #8000000;$fatal(1,"clock/reset test timeout");end
endmodule'''
    run('stage1_ddr_reference',src,[R/'rtl/color_regions'/x for x in ('refined_reset_bridge.v','refined_ddr_recovery.v','stage1_top.v','stage1_memory_video_out.v')],timeout=180)
    src=literal_fixture(R/'scripts/test_refined_recovery.py')
    src=src.replace('always #7.5 dc=~dc;','always #3.75 dc=~dc;').replace('always #5 rc=~rc;','always #10 rc=~rc;')
    src=src.replace('stable_line_reader #(.JOB_TIMEOUT_CYCLES(1300),.DRAIN_TIMEOUT_CYCLES(1000)) dut','refined_line_reader dut')
    src=src.replace("2'd0,ovs,ohs,ode,rgb,mask,ok", "3'd0,ovs,ohs,ode,rgb,mask,ok")
    src=src.replace('first_due+1500','first_due+140000').replace('repeat(2100)','repeat(142000)').replace('n<4000','n<400000').replace('repeat(1800)','repeat(136000)')
    src=src.replace('integer mode=0,', '''real job_start=0;reg started=0,checked_timeout=0;
always @(posedge dc)begin
if(dut.state==1 && !started)begin job_start=$realtime;started=1;end
if(dut.timeout_event && !checked_timeout)begin
if(!started || $realtime-job_start<999900 || $realtime-job_start>1000100)$fatal(1,"default reader timeout not1ms: %f",$realtime-job_start);
checked_timeout=1;end end
integer mode=0,''')
    src=src.replace('$finish;end', '$display("STAGE1_DDR133_RECOVERY_PASS mode%0d nominal1ms late-drain/missing-return/fresh-identity/continuous-sync",mode);if(!checked_timeout)$fatal(1,"no actual default timeout");$finish;end')
    mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_line_reader','stable_model_lane','stable_filter4','refined_reset_bridge','refined_zoom_geometry','refined_ddr_recovery','refined_mc_to_user_interface')]
    mods += [R/'rtl/04_tracking/target_mailbox.v',R/'user_source/ip_source/w155_d512_fifo/w155_d512_fifo.v',R/'user_source/ip_source/w155_d512_fifo/soft_fifo_al_f58e8b3e1f3d.v']
    for mode in (0,1):run('stage1_ddr133_recovery_'+str(mode),src,mods,args=['+MODE='+str(mode)],timeout=180)

if __name__=='__main__':main()
