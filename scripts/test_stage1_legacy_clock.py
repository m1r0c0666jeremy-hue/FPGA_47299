"""Qualify the explicitly deferred DDR profile at its actual old clock rate.

Digital tests do not establish analog PLL lock, training, or board stability.
"""
from refined_testlib import R,run,literal_fixture
from stage1_ddr_contract import contract


def main():
    profile=contract()
    assert profile['profile']=='LEGACY_50MHZ_REFERENCE_CORRECTION_DEFERRED'
    assert profile['reference_mhz']==50 and profile['user_period_ns']==15
    assert profile['reader_timeout_us']==2000.01
    print('LEGACY_REFERENCE_RISK',profile,flush=True)
    src=r'''`timescale 1ns/1ps
module tb;
reg clk=0,rst=0,ready=0,fault=0;
always #10 clk=~clk;
wire ctrl,stream,dead;wire [15:0] epoch,count;wire [1:0] retry;wire [3:0] why;
refined_ddr_recovery #(.CYCLES_PER_MS(50000),.INIT_MS(1)) dut(clk,rst,ready,fault,ctrl,stream,epoch,count,retry,why,dead);
time asserted;
always @(negedge ctrl)asserted=$time;
initial begin #1;rst=0;repeat(4)@(negedge clk);rst=1;
wait(ctrl);wait(!ctrl);if(why!=5 || count!=1)$fatal(1,"init timeout not diagnosed");
wait(ctrl);if($time-asserted<999980 || $time-asserted>1000020)$fatal(1,"50MHz reset duration");
ready=1;wait(stream);fault=~fault;wait(!ctrl);ready=0;wait(ctrl);ready=1;wait(stream);
if(count!=2 || epoch!=2 || dead || why!=4)$fatal(1,"fault recovery identity");
#3;rst=0;#0.001;if(ctrl || stream)$fatal(1,"global assertion not immediate");
$display("STAGE1_LEGACY_DDR_REFERENCE_PASS exact-pinned-profile/reference50/supervisor50/real1ms-reset/epoch analog-unverified");$finish;end
initial begin #8000000;$fatal(1,"legacy recovery timeout");end
endmodule'''
    run('stage1_legacy_ddr_reference',src,[R/'rtl/color_regions'/n for n in
        ('stage1_top.v','stage1_memory_video_out.v','refined_ddr_recovery.v')],timeout=180)

    src=literal_fixture(R/'scripts/test_refined_recovery.py')
    assert 'always #7.5 dc=~dc;' in src
    src=src.replace('always #5 rc=~rc;','always #10 rc=~rc;')
    src=src.replace('stable_line_reader #(.JOB_TIMEOUT_CYCLES(1300),.DRAIN_TIMEOUT_CYCLES(1000)) dut','refined_line_reader dut')
    src=src.replace("2'd0,ovs,ohs,ode,rgb,mask,ok", "3'd0,ovs,ohs,ode,rgb,mask,ok")
    src=src.replace('first_due+1500','first_due+140000').replace('repeat(2100)','repeat(142000)').replace('n<4000','n<400000').replace('repeat(1800)','repeat(136000)')
    src=src.replace('integer mode=0,',r'''real job_start=0;reg started=0,checked_timeout=0;
always @(posedge dc)begin
if(dut.state==1 && !started)begin job_start=$realtime;started=1;end
if(dut.timeout_event && !checked_timeout)begin
if(!started || $realtime-job_start<1999800 || $realtime-job_start>2000200)$fatal(1,"legacy reader timeout not2ms: %f",$realtime-job_start);
checked_timeout=1;end end
integer mode=0,''')
    src=src.replace('$finish;end', '$display("STAGE1_LEGACY_DDR66_RECOVERY_PASS mode%0d nominal2ms late-drain/missing-return/fresh-identity/continuous-sync",mode);if(!checked_timeout)$fatal(1,"no actual default timeout");$finish;end')
    mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_line_reader','stable_model_lane','stable_filter4','refined_reset_bridge','refined_zoom_geometry','refined_ddr_recovery','refined_mc_to_user_interface')]
    mods += [R/'rtl/04_tracking/target_mailbox.v',R/'user_source/ip_source/w155_d512_fifo/w155_d512_fifo.v',R/'user_source/ip_source/w155_d512_fifo/soft_fifo_al_f58e8b3e1f3d.v']
    for mode in (0,1):
        run('stage1_legacy_ddr66_recovery_'+str(mode),src,mods,args=['+MODE='+str(mode)],timeout=180)


if __name__=='__main__':main()
