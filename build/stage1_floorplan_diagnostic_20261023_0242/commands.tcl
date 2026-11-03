cd {D:/aaa_FPGA/region-sequence-stage1/build/stage1_floorplan_diagnostic_20261023_0242}
import_device ph1_35p.db -package PH1P35MDG324 -speed 3
import_db {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261023_012438/target_color_regions_placed.db}
foreach pattern {*bound* *region* *group* *cell* *inst* *prop* *net* *location* *attribute* *collection* *help*} {puts "COMMANDS $pattern [lsort [info commands $pattern]]"}
if {[llength [info commands help]]} {foreach cmd {get_cells get_property get_attribute get_nets get_insts report_property create_bound set_bound report_bound get_bounds report_net report_inst} {if {[llength [info commands $cmd]]} {puts "HELP $cmd";catch {help $cmd} msg;puts $msg}}}
exit
