"""Private four-cycle hue retiming, with no model or output latency changes."""
import argparse,hashlib,json,sys,xml.etree.ElementTree as ET
from refined_testlib import R,run

ap=argparse.ArgumentParser();ap.add_argument('--place',action='store_true');args=ap.parse_args()
out=R/'build/refined_hue_retime_prototype';out.mkdir(exist_ok=True)
base=R/'rtl/color_regions/stable_model_lane.v';original=base.read_text(encoding='utf-8')
start=original.index(' reg [7:0] hue_a,hue_b,hue_chroma;')
end=original.index(' always @(posedge clk',start)
new=r''' // Compute channel selection/chroma on the input-register stage.
 // Keep the original four-clock hit/model alignment; no extra pixel delay.
 reg [7:0] maximum1,minimum1,chroma1;
 reg signed [8:0] difference1;
 reg [1:0] sector1;
 reg [7:0] raw_maximum,raw_minimum,raw_a,raw_b;
 reg signed [8:0] raw_difference;
 reg [1:0] raw_sector;
 reg [10:0] hue_offset,hue_units;
 always @*begin
 raw_maximum=rgb[23:16]>rgb[15:8]?(rgb[23:16]>rgb[7:0]?rgb[23:16]:rgb[7:0]):(rgb[15:8]>rgb[7:0]?rgb[15:8]:rgb[7:0]);
 raw_minimum=rgb[23:16]<rgb[15:8]?(rgb[23:16]<rgb[7:0]?rgb[23:16]:rgb[7:0]):(rgb[15:8]<rgb[7:0]?rgb[15:8]:rgb[7:0]);
 if(raw_maximum==rgb[23:16])begin raw_a=rgb[15:8];raw_b=rgb[7:0];raw_sector=rgb[15:8]<rgb[7:0]?3:0;end
 else if(raw_maximum==rgb[15:8])begin raw_a=rgb[7:0];raw_b=rgb[23:16];raw_sector=1;end
 else begin raw_a=rgb[23:16];raw_b=rgb[15:8];raw_sector=2;end
 raw_difference=$signed({1'b0,raw_a})-$signed({1'b0,raw_b});
 mx=maximum1;mn=minimum1;
 case(sector1)
 0:hue_offset=0;
 1:hue_offset={3'd0,chroma1}<<1;
 2:hue_offset={3'd0,chroma1}<<2;
 3:hue_offset=({3'd0,chroma1}<<2)+({3'd0,chroma1}<<1);
 endcase
 hue_units=hue_offset+{{2{difference1[8]}},difference1};
 n=({7'd0,hue_units}<<6)-({7'd0,hue_units}<<2);
 end
'''
candidate=original[:start]+new+original[end:]
candidate=candidate.replace('r<=0;g<=0;b<=0;', 'r<=0;g<=0;b<=0;maximum1<=0;minimum1<=0;chroma1<=0;difference1<=0;sector1<=0;',1)
candidate=candidate.replace('r<=rgb[23:16];g<=rgb[15:8];b<=rgb[7:0];c0<=models;',
 'r<=rgb[23:16];g<=rgb[15:8];b<=rgb[7:0];c0<=models;\n maximum1<=raw_maximum;minimum1<=raw_minimum;chroma1<=raw_maximum-raw_minimum;difference1<=raw_difference;sector1<=raw_sector;',1)
candidate=candidate.replace('m<=mx;d<=mx-mn;hn<=n[16:0];','m<=mx;d<=chroma1;hn<=n[16:0];',1)
for name,data in (('stable_model_lane.v',candidate),('reference.v',original.replace('module stable_model_lane(', 'module reference_model_lane('))):
 p=out/name;data=data.encode('utf-8')
 if p.exists():assert p.read_bytes()==data
 else:p.write_bytes(data)
(out/'context.json').write_text(json.dumps(dict(private_not_adopted=True,original_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest(),pipeline_cycles=4,model_thresholds_changed=False),indent=2),encoding='utf-8')

if args.place:
 project=R/'td_project/target_color_regions_refined.al'
 tree=ET.fromstring(project.read_text(encoding='utf-8').replace('&','&amp;').replace('::','__TD_COLON__'))
 for node in tree.findall('./Source_Files/*/File'):
  p=(project.parent/node.attrib['Path']).resolve();node.set('Path',((out/'stable_model_lane.v') if p==base else p).as_posix())
 prototype=out/'prototype.al';data=('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n').encode()
 if prototype.exists():assert prototype.read_bytes()==data
 else:prototype.write_bytes(data)
 script=R/'scripts/run_refined_build.py';s=script.read_text(encoding='utf-8').replace("project=R/'td_project/target_color_regions_refined.al'",'project=prototype_project').replace("f'refined_{a.stage}_{stamp}'","f'refined_hue_retime_{a.stage}_{stamp}'")
 sys.argv=[str(script),'--stage','place','--map-mode','area_prior','--pack-effort','high','--strategy','5','--max-fanout','128','--checkpoint']
 exec(compile(s,str(script),'exec'),dict(__file__=str(script),__name__='__main__',prototype_project=prototype));raise SystemExit(0)

tb=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [23:0] rgb=0;reg [127:0] models=0;
wire [1:0] g,d;reference_model_lane gold(clk,rst,rgb,models,g);stable_model_lane dut(clk,rst,rgb,models,d);
reg [31:0] rng=32'h47299;integer i,j,checks=0;
always @(posedge clk)begin #1;
 if(g!==d || gold.n!==dut.n || gold.mx!==dut.mx || gold.mn!==dut.mn || gold.hn!==dut.hn || gold.m!==dut.m || gold.d!==dut.d)
 $fatal(1,"retime mismatch i%0d rgb%h hits%b/%b n%0d/%0d",i,rgb,g,d,gold.n,dut.n);
 checks=checks+1;
end
initial begin repeat(4)@(negedge clk);rst=1;
for(i=0;i<300000;i=i+1)begin @(negedge clk);
 rng=rng*1664525+1013904223;rgb=rng[23:0];
 if(i%7==0)rgb={rng[7:0],rng[7:0],rng[7:0]};
 if(i%13==0)rgb=24'hff0000;if(i%17==0)rgb=24'h0000ff;if(i%19==0)rgb=24'hffff00;if(i%23==0)rgb=24'hff00ff;
 for(j=0;j<4;j=j+1)begin rng=rng*1664525+1013904223;models[j*32+:32]=rng;end
 if(i%3==0)begin models[63]=1;models[127]=1;models[44:37]=0;models[36:29]=1;models[108:101]=0;models[100:93]=1;end
 if(i%16384==16380)rst=0;if(i%16384==16383)rst=1;
end
repeat(8)@(negedge clk);$display("HUE_RETIME_PRIVATE_PASS 300000 dynamic RGB/model clocks, reset, numerator/max/min and registered outputs equal; four-cycle latency unchanged; checks%0d",checks);$finish;
end endmodule'''
run('hue_retime_private',tb,[out/'reference.v',out/'stable_model_lane.v'])
