"""Exercise the exact generated retry Tcl with namespaced command stubs."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
candidate=R/'build/refined_route_20261018_115500_912935/run.tcl'
source=candidate.read_text(encoding='utf-8')
fragment=source[source.index(' if {[catch {route} normal_error]}'):source.index(' report_area -io_info')]
assert fragment.count('set_param route effort routability')==1
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
out=R/'build'/f'refined_retry_control_{stamp}';out.mkdir(exist_ok=False)
script='''foreach mode {direct recovered doublefail savefail} {
 set ns ::case_$mode
 namespace eval $ns {
  variable calls 0;variable files {};variable messages {};variable effort normal
  proc route {} {
   variable calls;variable mode;incr calls
   if {$mode eq "direct" || ($calls==2 && $mode ne "doublefail")} {return}
   error "INJECTED_ROUTE_FAILURE"
  }
  proc export_db {name} {
   variable files;variable mode;lappend files $name
   if {$name eq "failed_normal_route.db" && $mode eq "savefail"} {error "INJECTED_CHECKPOINT_SAVE_FAILURE"}
  }
  proc set_param {step key value} {
   variable effort
   if {$step ne "route" || $key ne "effort" || $value ne "routability"} {error "BAD_RETRY_SETTING"}
   set effort $value
  }
  proc puts {message} {variable messages;lappend messages $message}
 }
 namespace eval $ns [list variable mode $mode]
 set status [catch {namespace eval $ns {
FRAGMENT
 }} error_message]
 set calls [set ${ns}::calls];set files [set ${ns}::files];set effort [set ${ns}::effort]
 if {$mode eq "direct"} {
  if {$status!=0 || $calls!=1 || $effort ne "normal" || $files ne "target_color_regions_routed.db"} {error "DIRECT_ROUTE_CONTROL_FAILED"}
 } elseif {$mode eq "doublefail"} {
  if {$status!=1 || $calls!=2 || [lsearch -exact $files target_color_regions_routed.db]>=0} {error "SECOND_FAILURE_WAS_HIDDEN"}
 } else {
  if {$status!=0 || $calls!=2 || $effort ne "routability" || [lsearch -exact $files target_color_regions_routed.db]<0} {error "RECOVERY_CONTROL_FAILED"}
 }
 puts "ROUTE_RETRY_CONTROL_CASE_PASS $mode calls=$calls status=$status effort=$effort"
}
puts "ROUTE_RETRY_CONTROL_PASS four cases; finite retry and second error propagated; command stubs only, not physical routing"
exit
'''.replace('FRAGMENT',fragment)
# A top-level catch prevents TD's interactive console from hiding a Tcl error.
script='if {[catch {\n'+script.removesuffix('exit\n')+'} message]} {puts stderr $message;puts stderr $::errorInfo;exit 1}\nexit\n'
fixture=out/'run.tcl';fixture.write_text(script,encoding='utf-8')
td=Path('D:/26_software/TangDynasty/bin/td_commands_prompt.exe');env=os.environ.copy();env['PATH']=str(td.parent)+os.pathsep+env.get('PATH','')
p=subprocess.run([str(td),fixture.as_posix()],cwd=out,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
log=p.stdout+p.stderr
record=R/'reports/refined'/f'route_retry_control_{stamp}'
record.with_suffix('.log').write_text(log,encoding='utf-8')
passed=p.returncode==0 and 'ROUTE_RETRY_CONTROL_PASS four cases' in log
record.with_suffix('.json').write_text(json.dumps(dict(passed=passed,exit_code=p.returncode,physical_routing=False,inputs={path.relative_to(R).as_posix():sha(path) for path in (candidate,fixture,R/'scripts/run_refined_route.py',Path(__file__))}),indent=2),encoding='utf-8')
assert passed,log
print('ROUTE_RETRY_CONTROL_PASS',record.relative_to(R))
