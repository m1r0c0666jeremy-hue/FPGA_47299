"""Private timing prototype; never publishes or changes the formal source tree."""
from pathlib import Path
import argparse, hashlib, json, sys, xml.etree.ElementTree as ET
from refined_testlib import R, run

RELAY = r'''
`default_nettype none
module refined_camera_control_relay(
 input wire ref_clk,cam_clk,display_clk,rst_n,display_rst_n,
 input wire gain_req,gain_up,cam_gain_ack,cam_event,cam_ready,
 input wire [17:0] cam_status,
 output wire cam_req,cam_up,gain_ack,event_relay,ready_relay,
 output wire [17:0] ui_status);
 (* async_reg="true",syn_preserve=1 *) reg [1:0] reset_sync;
 wire ref_rst_n=reset_sync[1];
 always @(posedge ref_clk or negedge rst_n)
  if(!rst_n)reset_sync<=0;else reset_sync<={reset_sync[0],1'b1};
 (* async_reg="true",syn_preserve=1 *) reg [2:0] req_sync;
 (* async_reg="true",syn_preserve=1 *) reg [1:0] up_sync,ack_sync,event_sync,ready_sync;
 always @(posedge ref_clk or negedge ref_rst_n)begin
  if(!ref_rst_n)begin req_sync<=0;up_sync<=0;ack_sync<=0;event_sync<=0;ready_sync<=0;end
  else begin req_sync<={req_sync[1:0],gain_req};up_sync<={up_sync[0],gain_up};
   ack_sync<={ack_sync[0],cam_gain_ack};event_sync<={event_sync[0],cam_event};ready_sync<={ready_sync[0],cam_ready};end
 end
 assign cam_req=req_sync[2];assign cam_up=up_sync[1];assign gain_ack=ack_sync[1];
 assign event_relay=event_sync[1];assign ready_relay=ready_sync[1];
 wire [17:0] ref_status;wire cam_send_ready,ref_send_ready;
 target_mailbox #(.WIDTH(18)) cam_to_ref(.S_clk(cam_clk),.S_rst_n(rst_n),.S_send(cam_send_ready),
  .S_data(cam_status),.S_ready(cam_send_ready),.D_clk(ref_clk),.D_rst_n(ref_rst_n),.D_valid(),.D_data(ref_status));
 target_mailbox #(.WIDTH(18)) ref_to_display(.S_clk(ref_clk),.S_rst_n(ref_rst_n),.S_send(ref_send_ready),
  .S_data(ref_status),.S_ready(ref_send_ready),.D_clk(display_clk),.D_rst_n(display_rst_n),.D_valid(),.D_data(ui_status));
endmodule
`default_nettype wire
'''

ap=argparse.ArgumentParser();ap.add_argument('--place',action='store_true');a=ap.parse_args()
out=R/'build/refined_camera_relay_prototype';out.mkdir(exist_ok=True)
base=R/'rtl/color_regions/stable_top.v';old=base.read_bytes();text=old.decode('utf-8')
needle='''target_mailbox #(.WIDTH(18)) camera_ui(.S_clk(S_24m_clk),.S_rst_n(S_rst_n),.S_send(camera_ui_ready),
 .S_data({camera_ready,camera_phase,camera_fault,camera_retries,camera_gain}),.S_ready(camera_ui_ready),
 .D_clk(S_hdmi_pixel_clk),.D_rst_n(process_rst_n),.D_valid(),.D_data(camera_ui_status));'''
replacement='''wire camera_event_relay,camera_ready_relay,camera_gain_req_relay,camera_gain_up_relay,camera_gain_ack_raw;
refined_camera_control_relay camera_relay(.ref_clk(S_100m_clk),.cam_clk(S_24m_clk),.display_clk(S_hdmi_pixel_clk),
 .rst_n(S_rst_n),.display_rst_n(process_rst_n),.gain_req(gain_req),.gain_up(gain_up),.cam_gain_ack(camera_gain_ack_raw),
 .cam_event(camera_parameter_event),.cam_ready(camera_ready),
 .cam_status({camera_ready,camera_phase,camera_fault,camera_retries,camera_gain}),
 .cam_req(camera_gain_req_relay),.cam_up(camera_gain_up_relay),.gain_ack(gain_ack),
 .event_relay(camera_event_relay),.ready_relay(camera_ready_relay),.ui_status(camera_ui_status));'''
changes=[(needle,replacement),
 ('camera_event_sync<={camera_event_sync[0],camera_parameter_event}', 'camera_event_sync<={camera_event_sync[0],camera_event_relay}'),
 ('camera_ready_sync<={camera_ready_sync[0],camera_ready}', 'camera_ready_sync<={camera_ready_sync[0],camera_ready_relay}'),
 ('.I_gain_req(gain_req), .I_gain_up(gain_up), .O_gain_ack(gain_ack)', '.I_gain_req(camera_gain_req_relay), .I_gain_up(camera_gain_up_relay), .O_gain_ack(camera_gain_ack_raw)')]
for before,after in changes:
 assert text.count(before)==1,before
 text=text.replace(before,after)
candidate=text+RELAY
for path,data in ((out/'relay.v',RELAY),(out/'stable_top.v',candidate)):
 data=data.encode('utf-8')
 if path.exists():assert path.read_bytes()==data
 else:path.write_bytes(data)
assert base.read_bytes()==old
record=dict(private_not_adopted=True,source=base.relative_to(R).as_posix(),source_sha256=hashlib.sha256(old).hexdigest(),
            candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest(),constraints_changed=False,
            purpose='Retimed low-rate control only; adds latency, requires CDC and full integration verification before adoption')
(out/'context.json').write_text(json.dumps(record,indent=2),encoding='utf-8')

if a.place:
 project=R/'td_project/target_color_regions_refined.al'
 tree=ET.fromstring(project.read_text(encoding='utf-8').replace('&','&amp;').replace('::','__TD_COLON__'))
 for node in tree.findall('./Source_Files/*/File'):
  p=(project.parent/node.attrib['Path']).resolve();node.set('Path',((out/'stable_top.v') if p==base else p).as_posix())
 prototype=out/'prototype.al';data=('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n').encode()
 if prototype.exists():assert prototype.read_bytes()==data
 else:prototype.write_bytes(data)
 script=R/'scripts/run_refined_build.py';s=script.read_text(encoding='utf-8')
 assert s.count("project=R/'td_project/target_color_regions_refined.al'")==1
 s=s.replace("project=R/'td_project/target_color_regions_refined.al'",'project=prototype_project')
 s=s.replace("f'refined_{a.stage}_{stamp}'","f'refined_camera_relay_{a.stage}_{stamp}'")
 sys.argv=[str(script),'--stage','place','--map-mode','area_prior','--pack-effort','high','--strategy','5','--max-fanout','128','--checkpoint']
 exec(compile(s,str(script),'exec'),dict(__file__=str(script),__name__='__main__',prototype_project=prototype))
 raise SystemExit(0)

tb=r'''`timescale 1ns/1ps
module tb;
reg rclk=0,cclk=0,dclk=0,rst=0;
always #5 rclk=~rclk;always #21 cclk=~cclk;always #6.6665 dclk=~dclk;
reg req=0,up=0,ack=0,ev=0,ready=0;reg [17:0] status=0;
wire creq,cup,gack,event_out,ready_out;wire [17:0] ui;
reg [1:0] ack_display=0,event_display=0,ready_display=0,drst=0;
wire display_rst=drst[1];
always @(posedge dclk or negedge rst)if(!rst)drst<=0;else drst<={drst[0],1'b1};
always @(posedge dclk or negedge display_rst)begin
 if(!display_rst)begin ack_display<=0;event_display<=0;ready_display<=0;end
 else begin ack_display<={ack_display[0],gack};event_display<={event_display[0],event_out};ready_display<={ready_display[0],ready_out};end
end
refined_camera_control_relay dut(rclk,cclk,dclk,rst,display_rst,req,up,ack,ev,ready,status,creq,cup,gack,event_out,ready_out,ui);
always @(negedge dclk)if(display_rst && ui!=0 && ui[17:9]!==~ui[8:0])$fatal(1,"torn status word");
// Existing camera receiver's request has one extra synchronizer stage vs direction.
reg [2:0] crsync=0;reg [1:0] cusync=0;reg seen=0;integer accepted=0,wait_ack=0;
always @(posedge cclk or negedge rst)begin
 if(!rst)begin crsync<=0;cusync<=0;seen<=0;ack<=0;wait_ack<=0;end
 else begin
  crsync<={crsync[1:0],creq};cusync<={cusync[0],cup};
  if(crsync[2]!=seen)begin
   if(cusync[1]!==up)$fatal(1,"direction overtaken by request");
   if(wait_ack!=0)$fatal(1,"request while previous transaction pending");
   seen<=crsync[2];wait_ack<=3+(accepted%11);accepted=accepted+1;
  end
  if(wait_ack>1)wait_ack<=wait_ack-1;
  if(wait_ack==1)begin wait_ack<=0;ack<=seen;end
 end
end
integer n,k,limit,prior;reg [31:0] rng=32'h47299;
task tick;begin @(negedge dclk);end endtask
initial begin
 for(k=0;k<4;k=k+1)tick();rst=1;
 for(n=0;n<512;n=n+1)begin
  if(n!=0 && n%64==0)begin rst=0;req=0;up=0;ev=0;ready=0;status=0;repeat(7)tick();rst=1;repeat(15)tick();end
  rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};repeat(1+(rng%17))tick();
  prior=accepted;up=rng[2];req=~req;ev=~ev;ready=~ready;status={n[8:0],~n[8:0]};
  limit=0;while(ack_display[1]!==req && limit<1000)begin tick();limit=limit+1;end
  if(limit==1000 || accepted!=prior+1)$fatal(1,"lost or duplicate gain transaction");
  repeat(100)tick();
  if(ui!==status || event_display[1]!==ev || ready_display[1]!==ready)$fatal(1,"relay status/event mismatch");
 end
 if(accepted!=512)$fatal(1,"transaction count");
 for(n=0;n<8;n=n+1)begin
  up=~up;req=~req;ev=~ev;status=18'h15555;repeat(1+n*2)tick();
  rst=0;req=0;up=0;ev=0;ready=0;status=0;repeat(7)tick();rst=1;repeat(200)tick();
  if(ui!==0 || ack_display!==0 || event_display!==0 || ready_display!==0)$fatal(1,"stale transaction after reset");
 end
 $display("CAMERA_RELAY_PRIVATE_PASS 512 completed gain transactions; direction, ACK, atomic 18-bit status, events, 8 idle and 8 in-flight resets; unrelated clocks");$finish;
end
initial begin #20000000;$fatal(1,"timeout");end
endmodule
'''
run('camera_relay_private',tb,[out/'relay.v',R/'rtl/04_tracking/target_mailbox.v'])
