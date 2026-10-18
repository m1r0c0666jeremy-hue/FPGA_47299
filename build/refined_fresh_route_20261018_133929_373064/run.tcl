set out {D:/aaa_FPGA/transparent-ring-stability/build/refined_fresh_route_20261018_133929_373064}
set probe {D:/aaa_FPGA/transparent-ring-stability/build/refined_failed_checkpoint_probe_20261018_133626}
cd $out
proc report_signature {path} {
 set f [open $path r];set data [read $f];close $f
 set lines {}
 foreach line [split [string map [list "\r" ""] $data] "\n"] {
  if {[regexp {^(Generated[ 	]+:|[|][ 	]+Date[ 	]+:|Generated (on|at)|Date:|Time:)} [string trim $line]]} {continue}
  lappend lines [string trimright $line]
 }
 return [string trim [join $lines "\n"]]
}
if {[catch {
 import_device ph1_35p.db -package PH1P35MDG324 -speed 3
 import_db failed_normal_route.db
 update_timing -mode manhattan
 report_clock_utilization -file restored_clocks.txt
 report_timing_exception -file restored_exceptions.timing
 foreach name {restored_clocks.txt restored_exceptions.timing} {
  if {[report_signature [file join $probe $name]] ne [report_signature [file join $out $name]]} {error "FAILED_CHECKPOINT_CONSTRAINT_MISMATCH: $name"}
 }
 puts "FAILED_CHECKPOINT_CONSTRAINT_ROUNDTRIP_PASS"
 set_param route effort routability
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
} message]} {puts stderr "BUILD_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
