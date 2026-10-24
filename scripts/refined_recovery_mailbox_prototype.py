"""Private telemetry ACK sampling change, retaining bundled-data handshakes."""
import argparse,hashlib,json,sys,xml.etree.ElementTree as ET
from refined_testlib import R,run

ap=argparse.ArgumentParser();ap.add_argument('--combined-place',action='store_true');args=ap.parse_args()
out=R/'build/refined_recovery_mailbox_prototype';out.mkdir(exist_ok=True)
source=(R/'rtl/04_tracking/target_mailbox.v').read_text(encoding='utf-8')
changes=[('module target_mailbox #','module refined_recovery_mailbox #'),
 ('reg ack1,ack2,req1,req2,req3;','reg ack1,ack_mid,ack2,req1,req2,req3;'),
 ('request<=0;payload<=0;ack1<=0;ack2<=0;','request<=0;payload<=0;'),
 ('            ack1<=ack;ack2<=ack1;',''),
 ('    assign S_ready=request==ack2;', '''    // Two full source-clock periods resolve ACK metastability before use.
    // First two samples use falling edges; final rising-edge stage preserves
    // source-side payload/request updates and prevents an opposite-edge hold path.
    always @(negedge S_clk or negedge S_rst_n)begin
        if(!S_rst_n)begin ack1<=0;ack_mid<=0;end
        else begin ack1<=ack;ack_mid<=ack1;end
    end
    always @(posedge S_clk or negedge S_rst_n)
        if(!S_rst_n)ack2<=0;else ack2<=ack_mid;
    assign S_ready=request==ack2;''')]
candidate=source
for before,after in changes:
 assert candidate.count(before)==1,before
 candidate=candidate.replace(before,after)
# ack1->ack_mid is one complete 20ns period at the actual 50MHz source.
# ack_mid->ack2 is an additional 10ns; request/payload remain rising-edge.
candidate=candidate.replace('Two full source-clock periods resolve ACK metastability before use.',
 'A full source-clock period plus a half period resolve ACK before use.')
base=R/'rtl/color_regions/stable_memory_video_out.v';memory=base.read_text(encoding='utf-8')
needle='target_mailbox #(.WIDTH(39)) recovery_telemetry';assert memory.count(needle)==1
memory=memory.replace(needle,'refined_recovery_mailbox #(.WIDTH(39)) recovery_telemetry')+ '\n'+candidate
for path,data in ((out/'recovery_mailbox.v',candidate),(out/'stable_memory_video_out.v',memory)):
 data=data.encode('utf-8')
 if path.exists():assert path.read_bytes()==data
 else:path.write_bytes(data)
(out/'context.json').write_text(json.dumps(dict(private_not_adopted=True,original_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),mailbox_sha256=hashlib.sha256(candidate.encode()).hexdigest(),candidate_sha256=hashlib.sha256(memory.encode()).hexdigest(),constraints_changed=False),indent=2),encoding='utf-8')

if args.combined_place:
 replacements={base:out/'stable_memory_video_out.v',R/'rtl/color_regions/stable_top.v':R/'build/refined_camera_relay_prototype/stable_top.v',R/'rtl/color_regions/stable_model_lane.v':R/'build/refined_hue_retime_prototype/stable_model_lane.v'}
 for path in replacements.values():assert path.is_file(),path
 project=R/'td_project/target_color_regions_refined.al'
 tree=ET.fromstring(project.read_text(encoding='utf-8').replace('&','&amp;').replace('::','__TD_COLON__'))
 for node in tree.findall('./Source_Files/*/File'):
  p=(project.parent/node.attrib['Path']).resolve();node.set('Path',replacements.get(p,p).as_posix())
 prototype=out/'combined_prototype.al';data=('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n').encode()
 if prototype.exists():assert prototype.read_bytes()==data
 else:prototype.write_bytes(data)
 script=R/'scripts/run_refined_build.py';s=script.read_text(encoding='utf-8').replace("project=R/'td_project/target_color_regions_refined.al'",'project=prototype_project').replace("f'refined_{a.stage}_{stamp}'","f'refined_timing_paths_{a.stage}_{stamp}'")
 sys.argv=[str(script),'--stage','place','--map-mode','area_prior','--pack-effort','high','--strategy','5','--max-fanout','128','--checkpoint']
 exec(compile(s,str(script),'exec'),dict(__file__=str(script),__name__='__main__',prototype_project=prototype));raise SystemExit(0)

tb=r'''`timescale 1ns/1ps
module tb;
reg sclk=0,dclk=0,rst=0,traffic=0;integer phase=0;
initial begin if(!$value$plusargs("PHASE=%d",phase))phase=0;#(phase);forever #10 sclk=~sclk;end
always #6.6665 dclk=~dclk;
reg [1:0] drst=0;wire display_rst=drst[1];
always @(posedge dclk or negedge rst)if(!rst)drst<=0;else drst<={drst[0],1'b1};
wire gr,nr,gv,nv;wire [38:0] gd,nd;integer gs=0,ns=0,cycles=0,gd_count=0,nd_count=0;
function [38:0] word;input integer n;begin word={n[18:0],~n[18:0],1'b1};end endfunction
wire gsend=traffic && gs<1024 && cycles%7!=2;
wire nsend=traffic && ns<1024 && cycles%7!=2;
target_mailbox #(.WIDTH(39)) gold(sclk,rst,gsend,word(gs),gr,dclk,display_rst,gv,gd);
refined_recovery_mailbox #(.WIDTH(39)) dut(sclk,rst,nsend,word(ns),nr,dclk,display_rst,nv,nd);
always @(posedge sclk or negedge rst)begin
 if(!rst)begin gs<=0;ns<=0;cycles<=0;end
 else begin cycles<=cycles+1;if(gsend && gr)gs<=gs+1;if(nsend && nr)ns<=ns+1;end
end
always @(posedge dclk or negedge rst)begin
 if(!rst)begin gd_count=0;nd_count=0;end
 else begin #1;
  if(gv)begin if(gd!==word(gd_count))$fatal(1,"gold ordered word mismatch");gd_count=gd_count+1;end
  if(nv)begin if(nd!==word(nd_count))$fatal(1,"candidate ordered word mismatch");nd_count=nd_count+1;end
 end
end
integer i,limit;
task reset_idle;begin
 traffic=0;rst=0;repeat(6)@(negedge sclk);rst=1;repeat(20)@(negedge dclk);
 if(gv || nv || gd!==0 || nd!==0 || !gr || !nr)$fatal(1,"reset did not flush mailbox");
end endtask
initial begin
 reset_idle;traffic=1;limit=0;
 while((gd_count<1024 || nd_count<1024) && limit<40000)begin @(negedge dclk);limit=limit+1;end
 if(limit==40000 || gs!=1024 || ns!=1024)$fatal(1,"mailbox timeout or lost words");traffic=0;
 for(i=0;i<8;i=i+1)begin
  reset_idle;traffic=1;repeat(1+i*3)@(negedge sclk);#3;rst=0;traffic=0;repeat(8)@(negedge sclk);
  rst=1;repeat(20)@(negedge dclk);
  if(gv || nv || gd!==0 || nd!==0 || !gr || !nr)$fatal(1,"in-flight reset replayed stale payload");
 end
 $display("RECOVERY_MAILBOX_PRIVATE_PASS phase%0d 1024 ordered39-bit messages, burst gaps and 8 in-flight resets; extra ACK settling preserved",phase);$finish;
end
initial begin #10000000;$fatal(1,"timeout");end
endmodule'''
for phase in (0,1,4,9):run('recovery_mailbox_private_'+str(phase),tb,[R/'rtl/04_tracking/target_mailbox.v',out/'recovery_mailbox.v'],args=['+PHASE='+str(phase)])
