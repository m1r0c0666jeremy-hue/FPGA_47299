if {[catch {
foreach mode {direct recovered doublefail savefail} {
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
 if {[catch {route} normal_error]} {
  puts "ROUTE_NORMAL_FAILED_RETRY_ROUTABILITY"
  if {[catch {export_db failed_normal_route.db} save_error]} {puts "FAILED_NORMAL_DB_SAVE_FAILED: $save_error"}
  set_param route effort routability
  route
 }
 export_db target_color_regions_routed.db

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
} message]} {puts stderr $message;puts stderr $::errorInfo;exit 1}
exit
