cd {D:/aaa_FPGA/region-sequence-stage1/build/stage1_floorplan_diagnostic_20261023_0242}
import_device ph1_35p.db -package PH1P35MDG324 -speed 3
import_db {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261023_012438/target_color_regions_placed.db}
foreach cmd {create_bound add_cells_to_bound report_cells report_hierarchy_stats report_nets report_wirelength export_adc} {puts "SYNTAX $cmd";catch {$cmd -help} msg;puts $msg}
foreach pat {area_controller* *region_render*} {
 puts "PATTERN $pat"
 set cells [get_cells -hier $pat]; puts "COUNT [llength $cells] FIRST [lrange $cells 0 2]"
 foreach c [lrange $cells 0 0] {puts "PROPERTIES";puts [list_property $c];report_property $c}
}
report_hierarchy_stats -list
exit
