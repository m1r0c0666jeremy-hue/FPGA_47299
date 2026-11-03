cd {D:/aaa_FPGA/region-sequence-stage1/build/stage1_floorplan_diagnostic_20261023_0242}
import_device ph1_35p.db -package PH1P35MDG324 -speed 3
import_db {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261023_012438/target_color_regions_placed.db}
set f [open positions.tsv w];puts $f "module	cell	col	row	type"
foreach pat {area_controller* *region_render*} {
 set cells [get_cells -hier -quiet $pat]
 foreach c $cells {puts $f "$pat	$c	[get_property -quiet PLACED_COL $c]	[get_property -quiet PLACED_ROW $c]	[get_property -quiet REF_NAME $c]"}
}
close $f
set nets [get_nets -hier -quiet *vertices*]; puts "NETCOUNT [llength $nets] FIRST [lrange $nets 0 2]"
report_nets [lrange $nets 0 1] -connection -pin_display_limit 5
report_bounds -all
exit
