"""Private synthesis-only check of the documented per-net fanout attribute."""
from pathlib import Path
import argparse,hashlib,json,sys,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--wire',action='store_true');args=ap.parse_args()
prefix='refined_reset_wire_fanout' if args.wire else 'refined_reset_fanout'
out=R/'build'/(prefix+'_prototype');out.mkdir(exist_ok=True)
base=R/'rtl/color_regions/stable_memory_video_out.v';old=base.read_bytes()
text=old.decode('utf-8');needle='(* async_reg="true", syn_preserve=1 *) reg [1:0] capture_reset,ddr_reset;'
replacement='(* async_reg="true", syn_preserve=1, max_fanout=128 *) reg [1:0] capture_reset,ddr_reset;'
if args.wire:
 needle='wire capture_rst_n=capture_reset[1],ddr_rst_n=ddr_reset[1];'
 replacement='(* max_fanout=128 *) wire capture_rst_n=capture_reset[1],ddr_rst_n=ddr_reset[1];'
assert text.count(needle)==1
candidate=text.replace(needle,replacement).encode('utf-8')
assert candidate.decode('utf-8').replace(replacement,needle).encode('utf-8')==old
src=out/base.name
if src.exists():assert src.read_bytes()==candidate
else:src.write_bytes(candidate)
record=dict(private_not_adopted=True,only_documented_attribute_added=True,synchronizer_preserve_attributes_retained=True,original_sha256=hashlib.sha256(old).hexdigest(),candidate_sha256=hashlib.sha256(candidate).hexdigest(),original=base.relative_to(R).as_posix(),candidate=src.relative_to(R).as_posix())
p=out/'attribute_equivalence.json'
if p.exists():assert json.loads(p.read_text(encoding='utf-8'))==record
else:p.write_text(json.dumps(record,indent=2),encoding='utf-8')
project=R/'td_project/target_color_regions_refined.al'
tree=ET.fromstring(project.read_text(encoding='utf-8').replace('&','&amp;').replace('::','__TD_COLON__'))
for node in tree.findall('./Source_Files/*/File'):
 path=(project.parent/node.attrib['Path']).resolve();node.set('Path',(src if path==base else path).as_posix())
prototype=out/'prototype.al';data=('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n').encode('utf-8')
if prototype.exists():assert prototype.read_bytes().replace(b'\r\n',b'\n')==data
else:prototype.write_bytes(data)
script=R/'scripts/run_refined_build.py';s=script.read_text(encoding='utf-8')
assert s.count("project=R/'td_project/target_color_regions_refined.al'")==1
s=s.replace("project=R/'td_project/target_color_regions_refined.al'",'project=prototype_project')
s=s.replace("f'refined_{a.stage}_{stamp}'","f'{prototype_prefix}_{a.stage}_{stamp}'")
needle='    puts "REFINED_SYNTH_COMPLETED"';assert s.count(needle)==1
s=s.replace(needle,'    report_hfn gate -limit 30 -file high_fanout_gate.txt\n'+needle)
sys.argv=[str(script),'--stage','synth','--map-mode','area_prior','--pack-effort','high','--strategy','5']
exec(compile(s,str(script),'exec'),dict(__file__=str(script),__name__='__main__',prototype_project=prototype,prototype_prefix=prefix))
