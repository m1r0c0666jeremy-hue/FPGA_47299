"""Compare private arithmetic against production and measure physical area."""
from refined_testlib import R,run
from refined_calibration_arithmetic import calibration_asset
import argparse,sys,xml.etree.ElementTree as ET
ap=argparse.ArgumentParser();ap.add_argument('--build',choices=['synth','place']);ap.add_argument('--flow',choices=['acquisition','distributions','extended']);a=ap.parse_args()
out=R/'build/refined_cal_math_prototype';out.mkdir(exist_ok=True)
candidate=out/'stable_calibration.v';base=R/'rtl/color_regions/stable_calibration.v'
data=calibration_asset(base.read_text(encoding='utf-8')).encode()
if candidate.exists():assert candidate.read_bytes()==data
else:candidate.write_bytes(data)
if a.flow:
 path=R/'scripts/test_refined_calibration.py';script=path.read_text(encoding='utf-8')
 old=" run('calibration_'+name,src,modules)"
 assert old in script
 script=script.replace(old," run('cal_math_calibration_'+name,src,[candidate if p.name=='stable_calibration.v' else p for p in modules])")
 sys.argv=[str(path),*(['--distributions'] if a.flow!='acquisition' else []),*(['--extended'] if a.flow=='extended' else [])]
 exec(compile(script,str(path),'exec'),dict(__file__=str(path),__name__='__main__',candidate=candidate))
 raise SystemExit(0)
if not a.build:
 ref=out/'reference.v';data=base.read_text(encoding='utf-8').replace('module stable_calibration(','module reference_calibration(').encode()
 if ref.exists():assert ref.read_bytes()==data
 else:ref.write_bytes(data)
 fields={'r':255,'g':255,'b':255,'m':255,'d':255,'mlow':255,'dlow':255,'slow':31,'peak':511,'hue':511,'hlo':63,'hhi':63,'cp':1,'option_s':3,'option_m':3,'option_d':3,'option_narrow':1,'positive_sum':4095,'cluster':4095,'eligible':4095,'staged_r':4095,'staged_b':4095,'pi':3}
 drive=''
 for name,mask in fields.items():drive+=f'rng=rng*1664525+1013904223;gold.{name}=rng & {mask};dut.{name}=gold.{name};\n'
 for name in ('frame_samples','frame_eligible','retained'):
  drive+=f'for(j=0;j<8;j=j+1)begin rng=rng*1664525+1013904223;gold.{name}[j]=rng[8:0];dut.{name}[j]=rng[8:0];end\n'
 for part in range(3):drive+=f'rng=rng*1664525+1013904223;gold.sample_q[{part*32}+:32]=rng;dut.sample_q[{part*32}+:32]=rng;\n'
 compare=' || '.join(f'gold.{n}!==dut.{n}' for n in ('hn','mx','mn','min_d','sat_code','all_frames','retention_ok','staged_model','option_model','option_hit','option_cost'))
 tb='''module tb;
 reference_calibration gold(.clk(1'b0),.rst_n(1'b1),.sof(1'b0),.valid(1'b0),.rgb(96'd0),.pair(1'b0),.enter(1'b0),.sample(1'b0),.cancel(1'b0),.gain_changed(1'b0));
 stable_calibration dut(.clk(1'b0),.rst_n(1'b1),.sof(1'b0),.valid(1'b0),.rgb(96'd0),.pair(1'b0),.enter(1'b0),.sample(1'b0),.cancel(1'b0),.gain_changed(1'b0));
 reg [31:0] rng=32'h47299;integer k,j;reg [19:0] expected;
 initial begin gold.negative=0;dut.negative=0;
 for(k=0;k<200000;k=k+1)begin
 DRIVE
 gold.phase=3+k%2;dut.phase=gold.phase;gold.state=8+k%2;dut.state=gold.state;
 #1;expected=gold.state==8?gold.pixel[23:16]*gold.staged_r:gold.pixel[7:0]*gold.staged_b;
 if(COMPARE || dut.wb_product!==expected)$fatal(1,"cal arithmetic mismatch at%0d hn%0d/%0d gain%0d/%0d",k,gold.hn,dut.hn,expected,dut.wb_product);
 end
 $display("CAL_ARITHMETIC_PRIVATE_PASS 200000 RGB/quantile/count/frame arrays, selected gain products, unchanged state scheduling");$finish;end endmodule'''.replace('DRIVE',drive).replace('COMPARE',compare)
 run('cal_arithmetic_private',tb,[ref,candidate,R/'rtl/color_regions/regions_divide.v'])
else:
 original=R/'td_project/target_color_regions_refined.al'
 tree=ET.fromstring(original.read_text(encoding='utf-8').replace('&','&amp;').replace('::','__TD_COLON__'))
 for node in tree.findall('./Source_Files/*/File'):
  p=(original.parent/node.attrib['Path']).resolve();node.set('Path',(candidate if p.name==candidate.name else p).as_posix())
 project=out/'prototype.al';project.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n',encoding='utf-8')
 path=R/'scripts/run_refined_build.py';s=path.read_text(encoding='utf-8').replace("project=R/'td_project/target_color_regions_refined.al'","project=prototype_project").replace("f'refined_{a.stage}_{stamp}'","f'refined_cal_math_{a.stage}_{stamp}'")
 sys.argv=[str(path),'--stage',a.build,'--map-mode','area_prior','--pack-effort','high']
 exec(compile(s,str(path),'exec'),dict(__file__=str(path),__name__='__main__',prototype_project=project))
