"""Exact RGB/model-pipeline comparison and private synthesis/placement."""
from refined_testlib import R,run
from refined_shared_hue import shared_hue_asset
import argparse,sys,xml.etree.ElementTree as ET,json,zipfile
ap=argparse.ArgumentParser();ap.add_argument('--build',choices=['synth','place']);ap.add_argument('--production',action='store_true');ap.add_argument('--exhaustive-rtl',action='store_true');a=ap.parse_args()
out=R/('build/refined_shared_hue_production_retimed' if a.production else 'build/refined_shared_hue_prototype');out.mkdir(exist_ok=True)
base=R/'rtl/color_regions/stable_model_lane.v';candidate=out/base.name
protection=json.loads((R/'reports/refined/protected_inputs.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(R/protection['backup']/'sources_before.zip') as z:
 original=z.read('rtl/color_regions/stable_model_lane.v').decode('utf-8').replace('\r\n','\n')
data=shared_hue_asset(original).encode()
if a.production:
 from refined_hue_retime_logic import retime_hue_asset
 data=retime_hue_asset(data.decode('utf-8')).encode('utf-8')
if candidate.exists():assert candidate.read_bytes()==data
else:candidate.write_bytes(data)
if a.production:
 assert base.read_bytes()==data,'production lane differs from verified transform'
 candidate=base
if not a.build:
 import numpy as np
 g,b=np.indices((256,256),dtype=np.int32);count=0;peak=0
 for r in range(256):
  m=np.maximum(r,np.maximum(g,b));d=m-np.minimum(r,np.minimum(g,b))
  dr=60*(g-b);old=np.where(m==r,np.where(dr<0,dr+360*d,dr),np.where(m==g,120*d+60*(b-r),240*d+60*(r-g)))
  diff=np.where(m==r,g-b,np.where(m==g,b-r,r-g))
  offset=np.where(m==r,np.where(g<b,6*d,0),np.where(m==g,2*d,4*d))
  u=(offset+(diff&2047))&2047;new=(u<<6)-(u<<2)
  assert np.all(old==new) and np.all(u<=1530) and np.all(new>=0)
  count+=new.size;peak=max(peak,int(new.max()))
 print('HUE_ALL_RGB_EXHAUSTIVE_PASS',count,'numerator max',peak,flush=True)
 ref=out/'reference.v';b=original.replace('module stable_model_lane(', 'module reference_model_lane(').encode()
 if ref.exists():assert ref.read_bytes()==b
 else:ref.write_bytes(b)
 tb='''module tb;reg clk=0;always #5 clk=~clk;reg rst=0;reg [23:0] rgb=0;reg [127:0] models=0;
 wire [1:0] a,b;reference_model_lane gold(clk,rst,rgb,models,a);stable_model_lane dut(clk,rst,rgb,models,b);
 reg [31:0] rng=32'h47299;integer n,dual=0;
 always @(posedge clk)begin #1;if(rst && n>8)begin
 if(a!==b || gold.n!==dut.n || gold.mx!==dut.mx || gold.mn!==dut.mn)$fatal(1,"hue pipeline mismatch n%0d rgb%h n%0d/%0d hit%b/%b",n,rgb,gold.n,dut.n,a,b);
 if(a==3)dual=dual+1;end end
 initial begin repeat(4)@(negedge clk);rst=1;
 for(n=0;n<150000;n=n+1)begin @(negedge clk);
 rng=rng*1664525+1013904223;rgb=rng[23:0];
 if(n%7==0)rgb={rng[7:0],rng[7:0],rng[7:0]};
 if(n%13==0)rgb=24'hff0000;if(n%17==0)rgb=24'h0000ff;if(n%19==0)rgb=24'hffff00;
 if(n%23==0)rgb=24'hff00ff;
 rng=rng*1664525+1013904223;models[31:0]=rng;rng=rng*1664525+1013904223;models[63:32]=rng;
 rng=rng*1664525+1013904223;models[95:64]=rng;rng=rng*1664525+1013904223;models[127:96]=rng;
 if(n%3==0)begin models[63]=1;models[127]=1;models[44:37]=0;models[36:29]=1;models[108:101]=0;models[100:93]=1;end
 end
 repeat(8)@(negedge clk);$display("SHARED_HUE_RTL_PASS 150000 dynamic RGB/model cycles, unchanged four-clock masks, numerator/max/min exact; dual%0d",dual);$finish;
 end endmodule'''
 run('shared_hue_math',tb,[ref,candidate])
 if a.exhaustive_rtl:
  exhaustive='''module tb;
 wire [1:0] a,b;
 reference_model_lane gold(1'b0,1'b1,24'd0,128'd0,a);
 stable_model_lane dut(1'b0,1'b1,24'd0,128'd0,b);
 integer i;
 initial begin
 for(i=0;i<16777216;i=i+1)begin
 gold.r=i[23:16];gold.g=i[15:8];gold.b=i[7:0];
 dut.r=i[23:16];dut.g=i[15:8];dut.b=i[7:0];#1;
 if(gold.n!==dut.n || gold.mx!==dut.mx || gold.mn!==dut.mn)
 $fatal(1,"hue exhaustive mismatch rgb%h old%0d new%0d",i,gold.n,dut.n);
 end
 $display("SHARED_HUE_EXHAUSTIVE_RTL_PASS all16777216 RGB numerator/max/min exact");$finish;
 end endmodule'''
  if a.production:
   exhaustive=exhaustive.replace("stable_model_lane dut(1'b0,1'b1,24'd0,128'd0,b);", "reg [23:0] raw_rgb=24'hffffff;stable_model_lane dut(1'b0,1'b1,raw_rgb,128'd0,b);")
   # This fixture deliberately has no clock/reset. Trigger its combinational
   # input before depositing pipeline registers, including the first RGB zero.
   exhaustive=exhaustive.replace('initial begin\n for(i=0;', 'initial begin\n #1;\n for(i=0;',1)
   needle='dut.r=i[23:16];dut.g=i[15:8];dut.b=i[7:0];#1;'
   assert exhaustive.count(needle)==1
   exhaustive=exhaustive.replace(needle,'''dut.r=i[23:16];dut.g=i[15:8];dut.b=i[7:0];raw_rgb=i[23:0];#1;
dut.maximum1=dut.raw_maximum;dut.minimum1=dut.raw_minimum;
dut.chroma1=dut.raw_maximum-dut.raw_minimum;dut.difference1=dut.raw_difference;dut.sector1=dut.raw_sector;#1;''')
  run('shared_hue_exhaustive_rtl',exhaustive,[ref,candidate],timeout=1800)
 (out/'exhaustive.json').write_text(__import__('json').dumps(dict(rgb_vectors=count,numerator_max=peak,passed=True),indent=2),encoding='utf-8')
else:
 original=R/'td_project/target_color_regions_refined.al'
 tree=ET.fromstring(original.read_text(encoding='utf-8').replace('&','&amp;').replace('::','__TD_COLON__'))
 for node in tree.findall('./Source_Files/*/File'):
  p=(original.parent/node.attrib['Path']).resolve();node.set('Path',(candidate if p.name==candidate.name else p).as_posix())
 project=out/'prototype.al';project.write_bytes(('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n').encode('utf-8'))
 path=R/'scripts/run_refined_build.py';s=path.read_text(encoding='utf-8').replace("project=R/'td_project/target_color_regions_refined.al'","project=prototype_project").replace("f'refined_{a.stage}_{stamp}'","f'refined_shared_hue_{a.stage}_{stamp}'")
 sys.argv=[str(path),'--stage',a.build,'--map-mode','area_prior','--pack-effort','high','--macro-performance','macro_congestion']
 exec(compile(s,str(path),'exec'),dict(__file__=str(path),__name__='__main__',prototype_project=project))
