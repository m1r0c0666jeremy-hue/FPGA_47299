"""Camera supervisor through the private relay, including actual I2C RTL."""
import argparse
from refined_testlib import R, literal_fixture
from sc500_test_evidence import run

ap=argparse.ArgumentParser();ap.add_argument('--production',action='store_true');args=ap.parse_args()
relay=R/'rtl/color_regions/stable_top.v' if args.production else R/'build/refined_camera_relay_prototype/relay.v'
assert 'module refined_camera_control_relay(' in relay.read_text(encoding='utf-8')
source=literal_fixture(R/'scripts/test_refined_camera.py','src')
stub=literal_fixture(R/'scripts/test_refined_camera.py','stub')
wire_driver=literal_fixture(R/'scripts/test_refined_camera.py','wire_driver')
source=source.replace('always #5 clk=~clk','always #21 clk=~clk')
for before,after in (('.gain_req(request)','.gain_req(camera_req)'),('.gain_up(up)','.gain_up(camera_up)'),('.gain_ack(ack)','.gain_ack(camera_ack)')):
    assert source.count(before)==1
    source=source.replace(before,after)
extra='''
reg ref_clk=0,display_clk=0;always #5 ref_clk=~ref_clk;always #6.6665 display_clk=~display_clk;
reg [1:0] drst=0;wire display_rst=drst[1];
always @(posedge display_clk or negedge rst)if(!rst)drst<=0;else drst<={drst[0],1'b1};
wire camera_req,camera_up,camera_ack,event_ref,ready_ref;wire [17:0] ui;
refined_camera_control_relay relay(ref_clk,clk,display_clk,rst,display_rst,
 request,up,camera_ack,event_toggle,ready,{ready,phase,fault,retries,gain},
 camera_req,camera_up,ack,event_ref,ready_ref,ui);
'''
source=source.replace('refined_camera_config #',extra+'\nrefined_camera_config #',1)
source=source.replace('$finish;end', '''repeat(100)@(negedge display_clk);
 if(ui!=={ready,phase,fault,retries,gain} || event_ref!==event_toggle || ready_ref!==ready)
  $fatal(1,"camera supervisor relay feedback mismatch");
 $display("CAMERA_RELAY_SUPERVISOR_PASS mode%0d gain ACK, event invalidation, ready and diagnostic feedback",mode);
 $finish;end''',1)
tables=[R/'user_source/hdl_source/uics500_cfg'/name for name in ('uics500reg_720p60.v','uics500regAE.v','SC500GainTbl.v')]
modules=[relay,R/'rtl/04_tracking/target_mailbox.v',R/'rtl/color_regions/refined_camera_config.v',*tables]
prefix='camera_relay_production' if args.production else 'camera_relay_private_integration'
for mode in range(6):
    tb=source.replace('(CPM)','(10)').replace('(DIV)','(1)').replace('ACK_DRIVER','').replace('STUB',stub)
    run(prefix+'_'+str(mode),tb,modules,args=['+MODE='+str(mode)])
tb=source.replace('(CPM)','(24000)').replace('(DIV)','(239)').replace('STUB','').replace('ACK_DRIVER',wire_driver)
run(prefix+'_real_i2c',tb,[*modules,R/'user_source/hdl_source/uics500_cfg/uii2c.v',R/'scripts/sc500_i2c_slave_model.v.txt'],args=['+MODE=0'])
