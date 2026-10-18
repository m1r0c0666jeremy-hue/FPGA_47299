"""Route a verified placed TD checkpoint in a fresh, immutable attempt.

The parent must have completed synthesis/placement from the current sources.
Clock and exception reports must survive import byte-for-byte (path metadata
normalized) before routing is allowed. No ADC/SDC constraints are edited.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,shutil,subprocess
from refined_build_report import assess
R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--parent',required=True);ap.add_argument('--route-effort',choices=['normal','routability'],default='normal')
ap.add_argument('--replace-strategy',type=int,choices=range(1,12));a=ap.parse_args()
branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
assert branch=='release/transparent-ring-stability-20261015'
subprocess.run(['git','merge-base','--is-ancestor','2f79847f8443fb18f3896a6b88ae9b75c06c9ff8','HEAD'],cwd=R,check=True)
parent=(R/a.parent).resolve();assert parent.is_relative_to(R/'build') and re.fullmatch(r'[A-Za-z0-9_]+',parent.name)
s=json.loads((parent/'summary.json').read_text(encoding='utf-8'))
assert s['stage']=='place' and s['exit_code']==0 and s['resource_pass'] and s['inputs_unchanged'],s
checkpoint=parent/'target_color_regions_placed.db'
assert s['checkpoints'][checkpoint.name]==sha(checkpoint)
assert 'REFINED_PLACED_CHECKPOINT_READY' in (parent/'td.log').read_text(encoding='utf-8')
before=json.loads((parent/'inputs.json').read_text(encoding='utf-8'))
assert before==json.loads((parent/'inputs_after.json').read_text(encoding='utf-8'))
context=json.loads((parent/'source_context.json').read_text(encoding='utf-8'))
assert context['input_count']==len(before) and context['inputs_sha256']==sha(parent/'inputs.json')
assert all(sha(parent/'compiled_source'/name)==v and sha(R/name)==v for name,v in before.items()),'Parent/current sources differ'
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
out=R/'build'/f'refined_route_{stamp}';out.mkdir(exist_ok=False)
for name in ('inputs.json','compiled_inputs.zip','flow_options.json','official_strategy_ph1.json','official_strategy_context.json'):
 if (parent/name).is_file():shutil.copy2(parent/name,out/name)
frozen=out/'compiled_source';frozen.mkdir()
for name,v in before.items():
 p=frozen/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((parent/'compiled_source'/name).read_bytes());assert sha(p)==v
shutil.copy2(checkpoint,out/checkpoint.name)
proof=dict(parent=parent.relative_to(R).as_posix(),checkpoint_name=checkpoint.name,checkpoint_sha256=sha(checkpoint),parent_summary_sha256=sha(parent/'summary.json'),parent_context_sha256=sha(parent/'source_context.json'),parent_inputs_sha256=sha(parent/'inputs.json'))
(out/'checkpoint_provenance.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
context.update(creation_time=stamp,placed_checkpoint=proof,replaced_strategy=a.replace_strategy)
(out/'source_context.json').write_text(json.dumps(context,indent=2),encoding='utf-8')
t=f'''set out {{{out.as_posix()}}}
set parent {{{parent.as_posix()}}}
cd $out
proc report_signature {{path parent out}} {{
 set f [open $path r];set data [read $f];close $f
 set data [string map [list "\\r" "" $parent "<ATTEMPT>" $out "<ATTEMPT>"] $data]
 set lines {{}}
 foreach line [split $data "\\n"] {{
  if {{[regexp {{^(Generated[ \t]+:|[|][ \t]+Date[ \t]+:|Generated (on|at)|Date:|Time:)}} [string trim $line]]}} {{continue}}
  lappend lines [string trimright $line]
 }}
 return [string trim [join $lines "\\n"]]
}}
if {{[catch {{
 import_device ph1_35p.db -package PH1P35MDG324 -speed 3
 import_db target_color_regions_placed.db
 update_timing -mode manhattan
 report_clock_utilization -file placed_clocks.txt
 report_timing_exception -file placed_exceptions.timing
 foreach name {{placed_clocks.txt placed_exceptions.timing}} {{
  if {{[report_signature [file join $parent $name] $parent $out] ne [report_signature [file join $out $name] $parent $out]}} {{error "CHECKPOINT_CONSTRAINT_MISMATCH: $name"}}
 }}
 puts "CHECKPOINT_CONSTRAINT_ROUNDTRIP_PASS"
 set_param route effort {a.route_effort}
'''
if s.get('official_strategy'):
 for definition in s['official_strategy']['selected'].values():
  for item in definition['params']:
   if item['step']=='route':
    key,value=item['param'],str(item['val']);assert re.fullmatch(r'[A-Za-z0-9_]+',key) and re.fullmatch(r'[A-Za-z0-9_.-]+',value)
    t+=f' set_param route {key} {value}\n'
if a.replace_strategy is not None:
 if s.get('official_strategy'):
  for definition in s['official_strategy']['selected'].values():
   for item in definition['params']:
    if item['step']=='place':
     key,value=item['param'],str(item['val']);assert re.fullmatch(r'[A-Za-z0-9_]+',key) and re.fullmatch(r'[A-Za-z0-9_.-]+',value)
     t+=f' set_param place {key} {value}\n'
 t+=f' set_param place pr_strategy {a.replace_strategy}\n place\n report_area -io_info -file replacement_place.area\n puts "REFINED_REPLACEMENT_PLACE_COMPLETED"\n'
t+=''' route
 report_area -io_info -file target_color_regions_phy.area
 update_timing -mode final
 report_timing_status -file target_color_regions_phy.ts
 report_timing_summary -file target_color_regions_pr.timing
 report_timing_exception -file target_color_regions_exception.timing
 report_clock_utilization -file target_color_regions_clocks.txt
 bitgen -bit target_color_regions.bit
 puts "REFINED_CHECKPOINT_FULL_COMPLETED"
} message]} {puts stderr "BUILD_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
'''
(out/'run.tcl').write_text(t,encoding='utf-8')
td=Path('D:/26_software/TangDynasty/bin/td_commands_prompt.exe');env=os.environ.copy();env['PATH']=str(td.parent)+os.pathsep+env.get('PATH','')
print('REFINED_ROUTE_ATTEMPT',out,flush=True)
with (out/'td.log').open('w',encoding='utf-8') as log:p=subprocess.run([str(td),(out/'run.tcl').as_posix()],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
after={name:sha(frozen/name) for name in before};(out/'inputs_after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
summary={k:v for k,v in s.items() if k not in ('resources','resource_pass','placement_required','gate_estimate','checkpoints')}
summary.update(stage='full',head=context['compiled_source_commit'],head_after=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),route_effort=a.route_effort,exit_code=p.returncode,inputs_unchanged=before==after,working_tree_matches=all(sha(R/name)==v for name,v in before.items()),checkpoint_provenance=proof,checkpoint_unchanged=sha(checkpoint)==proof['checkpoint_sha256']==sha(out/checkpoint.name))
summary['replaced_strategy']=a.replace_strategy
if a.replace_strategy is not None:summary['placement_strategy']=a.replace_strategy
if p.returncode==0:summary.update(assess(out,'full'))
(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('REFINED_ROUTE_RESULT',json.dumps(summary),flush=True)
if p.returncode or not summary.get('resource_pass') or not summary.get('timing_pass') or not summary['checkpoint_unchanged'] or not summary['inputs_unchanged']:raise SystemExit(p.returncode or 3)
