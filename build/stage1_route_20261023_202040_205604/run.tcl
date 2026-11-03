set out {D:/aaa_FPGA/region-sequence-stage1/build/stage1_route_20261023_202040_205604}
set parent {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261023_200045}
cd $out
proc report_signature {path parent out} {
 set f [open $path r];set data [read $f];close $f
 set data [string map [list "\r" "" $parent "<ATTEMPT>" $out "<ATTEMPT>"] $data]
 set lines {}
 foreach line [split $data "\n"] {
  if {[regexp {^(Generated[ 	]+:|[|][ 	]+Date[ 	]+:|Generated (on|at)|Date:|Time:)} [string trim $line]]} {continue}
  lappend lines [string trimright $line]
 }
 return [string trim [join $lines "\n"]]
}
if {[catch {
 import_device ph1_35p.db -package PH1P35MDG324 -speed 3
 import_db target_color_regions_placed.db
 update_timing -mode manhattan
 report_clock_utilization -file placed_clocks.txt
 report_timing_exception -file placed_exceptions.timing
 foreach name {placed_clocks.txt placed_exceptions.timing} {
  if {[report_signature [file join $parent $name] $parent $out] ne [report_signature [file join $out $name] $parent $out]} {error "CHECKPOINT_CONSTRAINT_MISMATCH: $name"}
 }
 puts "CHECKPOINT_CONSTRAINT_ROUNDTRIP_PASS"
 set_param route effort normal
 set_param flow thread 16
 report_param -stage flow -file effective_flow.txt
 set_param route post_route_opt high
 if {[catch {route} normal_error]} {
  puts "ROUTE_NORMAL_FAILED_RETRY_ROUTABILITY"
  if {[catch {export_db failed_normal_route.db} save_error]} {puts "FAILED_NORMAL_DB_SAVE_FAILED: $save_error"}
  set_param route effort routability
  route
 }
 export_db target_color_regions_routed.db
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
