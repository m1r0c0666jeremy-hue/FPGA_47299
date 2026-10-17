"""Private arithmetic/RTL equivalence and independent TD resource experiment."""
from refined_testlib import R,run
from refined_reciprocal_lane import reciprocal_asset,one_logic_asset
import argparse,json,sys,xml.etree.ElementTree as ET
ap=argparse.ArgumentParser();ap.add_argument('--build',choices=['synth','place']);ap.add_argument('--logic-lane',action='store_true');a=ap.parse_args()
variant='reciprocal_one_logic' if a.logic_lane else 'reciprocal'
out=R/f'build/refined_{variant}_prototype';out.mkdir(exist_ok=True)
candidate=out/'stable_model_lane.v';text=reciprocal_asset((R/'rtl/color_regions/stable_model_lane.v').read_text(encoding='utf-8'))
if a.logic_lane:text=one_logic_asset(text)
data=text.encode()
if candidate.exists():assert candidate.read_bytes()==data
else:candidate.write_bytes(data)
capture=None
if a.logic_lane:
 capture=out/'stable_capture.v'
 data=(R/'rtl/color_regions/stable_capture.v').read_text(encoding='utf-8')
 assert 'stable_model_lane u_lane(' in data
 data=data.replace('stable_model_lane u_lane(','stable_model_lane #(.LOGIC_TRIAL(lane==3)) u_lane(').encode()
 if capture.exists():assert capture.read_bytes()==data
 else:capture.write_bytes(data)
if not a.build:
 import numpy as np
 count=0
 for d in range(1,256):
  n=np.arange(360*d,dtype=np.int64);q0=(n*((131072+d-1)//d))>>17
  q=q0-(q0*d>n)
  assert np.all(q==n//d) and np.all(q0<=360)
  count+=len(n)
 print('RECIPROCAL_INTEGER_EXHAUSTIVE_PASS',count,'all 0<=n<360*d, d1..255',flush=True)
 ref=out/'reference.v';data=(R/'rtl/color_regions/stable_model_lane.v').read_text(encoding='utf-8').replace('module stable_model_lane(','module reference_model_lane(').encode()
 if ref.exists():assert ref.read_bytes()==data
 else:ref.write_bytes(data)
 # The immutable benchmark exercises arbitrary valid/wrapped/overlapping
 # models and back-to-back parameter changes, with the exact four-clock port.
 tb=(R/'build/sim/refined/shared_hue_math_20261017_224607_217265/tb.sv').read_text(encoding='utf-8')
 tb=tb.replace('SHARED_HUE_RTL_PASS','RECIPROCAL_FOUR_CLOCK_RTL_PASS')
 if a.logic_lane:tb=tb.replace('stable_model_lane dut(','stable_model_lane #(.LOGIC_TRIAL(1)) dut(')
 run(variant+'_private_math',tb,[ref,candidate])
 (out/'integer_exhaustive.json').write_text(json.dumps(dict(passed=True,vectors=count,q_bits=17),indent=2),encoding='utf-8')
else:
 original=R/'td_project/target_color_regions_refined.al'
 tree=ET.fromstring(original.read_text(encoding='utf-8').replace('&','&amp;').replace('::','__TD_COLON__'))
 for node in tree.findall('./Source_Files/*/File'):
  p=(original.parent/node.attrib['Path']).resolve();node.set('Path',(candidate if p.name==candidate.name else capture if capture and p.name==capture.name else p).as_posix())
 project=out/'prototype.al';project.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n',encoding='utf-8')
 path=R/'scripts/run_refined_build.py';s=path.read_text(encoding='utf-8').replace("project=R/'td_project/target_color_regions_refined.al'","project=prototype_project").replace("f'refined_{a.stage}_{stamp}'","f'refined_"+variant+"_{a.stage}_{stamp}'")
 sys.argv=[str(path),'--stage',a.build,'--map-mode','area_prior','--pack-effort','high']
 exec(compile(s,str(path),'exec'),dict(__file__=str(path),__name__='__main__',prototype_project=project))
