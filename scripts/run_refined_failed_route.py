"""Continue a verified failed normal checkpoint in a fresh TD process."""
from pathlib import Path
import argparse,datetime,json,os,shutil,subprocess
from audit_refined import R,sha,canonical_build_inputs,checkpoint_report_signature
from refined_failed_checkpoint import verify_source
from refined_build_report import assess
ap=argparse.ArgumentParser();ap.add_argument('--source-attempt',required=True);ap.add_argument('--probe',required=True)
ap.add_argument('--route-effort',choices=['normal','routability'],default='routability');a=ap.parse_args()
assert subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()=='release/transparent-ring-stability-20261015'
subprocess.run(['git','merge-base','--is-ancestor','2f79847f8443fb18f3896a6b88ae9b75c06c9ff8','HEAD'],cwd=R,check=True)
source=(R/a.source_attempt).resolve();probe=(R/a.probe).resolve()
proof,before,ctx,ps,parent=verify_source(R,source,probe,canonical_build_inputs,checkpoint_report_signature)
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f');out=R/'build'/f'refined_fresh_route_{stamp}';out.mkdir(exist_ok=False)
for name in ('inputs.json','compiled_inputs.zip'):
    shutil.copy2(source/name,out/name)
frozen=out/'compiled_source';frozen.mkdir()
for name,value in before.items():
    p=frozen/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/'compiled_source'/name,p);assert sha(p)==value
shutil.copy2(source/'failed_normal_route.db',out/'failed_normal_route.db')
(out/'failed_checkpoint_provenance.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
ctx.update(creation_time=stamp,failed_checkpoint_provenance=proof)
(out/'source_context.json').write_text(json.dumps(ctx,indent=2),encoding='utf-8')
t=f'''set out {{{out.as_posix()}}}
set probe {{{probe.as_posix()}}}
cd $out
proc report_signature {{path}} {{
 set f [open $path r];set data [read $f];close $f
 set lines {{}}
 foreach line [split [string map [list "\\r" ""] $data] "\\n"] {{
  if {{[regexp {{^(Generated[ \t]+:|[|][ \t]+Date[ \t]+:|Generated (on|at)|Date:|Time:)}} [string trim $line]]}} {{continue}}
  lappend lines [string trimright $line]
 }}
 return [string trim [join $lines "\\n"]]
}}
if {{[catch {{
 import_device ph1_35p.db -package PH1P35MDG324 -speed 3
 import_db failed_normal_route.db
 update_timing -mode manhattan
 report_clock_utilization -file restored_clocks.txt
 report_timing_exception -file restored_exceptions.timing
 foreach name {{restored_clocks.txt restored_exceptions.timing}} {{
  if {{[report_signature [file join $probe $name]] ne [report_signature [file join $out $name]]}} {{error "FAILED_CHECKPOINT_CONSTRAINT_MISMATCH: $name"}}
 }}
 puts "FAILED_CHECKPOINT_CONSTRAINT_ROUNDTRIP_PASS"
 set_param route effort {a.route_effort}
 route
 export_db target_color_regions_routed.db
 report_area -io_info -file target_color_regions_phy.area
 update_timing -mode final
 report_timing_status -file target_color_regions_phy.ts
 report_timing_summary -file target_color_regions_pr.timing
 report_timing_exception -file target_color_regions_exception.timing
 report_clock_utilization -file target_color_regions_clocks.txt
 bitgen -bit target_color_regions.bit
 puts "REFINED_FRESH_FAILED_ROUTE_COMPLETED"
}} message]}} {{puts stderr "BUILD_FAILED: $message";puts stderr $::errorInfo;exit 1}}
exit
'''
(out/'run.tcl').write_text(t,encoding='utf-8')
td=Path('D:/26_software/TangDynasty/bin/td_commands_prompt.exe');env=os.environ.copy();env['PATH']=str(td.parent)+os.pathsep+env.get('PATH','')
print('REFINED_FRESH_FAILED_ROUTE_ATTEMPT',out,flush=True)
with (out/'td.log').open('w',encoding='utf-8') as log:p=subprocess.run([str(td),(out/'run.tcl').as_posix()],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
after={name:sha(frozen/name) for name in before};(out/'inputs_after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
s={k:v for k,v in ps.items() if k not in ('resources','resource_pass','placement_required','gate_estimate','checkpoints')}
s.update(stage='full',head=ctx['compiled_source_commit'],head_after=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),exit_code=p.returncode,route_effort=a.route_effort,inputs_unchanged=before==after,working_tree_matches=all(sha(R/name)==value for name,value in before.items()),official_strategy=None,recovery_method='fresh_process_from_failed_normal_route',failed_checkpoint_provenance=proof,failed_checkpoint_unchanged=sha(out/'failed_normal_route.db')==proof['checkpoint_sha256'],route_checkpoints={name:sha(out/name) for name in ('target_color_regions_routed.db',) if (out/name).is_file()})
if p.returncode==0:s.update(assess(out,'full'))
(out/'summary.json').write_text(json.dumps(s,indent=2),encoding='utf-8');print('REFINED_FRESH_FAILED_ROUTE_RESULT',json.dumps(s),flush=True)
if p.returncode or not s.get('resource_pass') or not s.get('timing_pass') or not s['failed_checkpoint_unchanged'] or not s['inputs_unchanged']:raise SystemExit(p.returncode or 3)
