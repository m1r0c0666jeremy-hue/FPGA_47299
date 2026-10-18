cd {D:/aaa_FPGA/transparent-ring-stability/build/refined_detailed_timing_probe_20261018_193123}
if {[catch {
 import_device ph1_35p.db -package PH1P35MDG324 -speed 3
 import_db {D:/aaa_FPGA/transparent-ring-stability/build/refined_full_20261018_183727/target_color_regions_placed.db}
 update_timing -mode manhattan
 report_timing_summary -file detailed.timing -ep_num 20 -path_num 1
 report_timing_path -file camera_event.timing -through [get_nets {u_camera/u_config/parameter_event}]
 puts "READONLY_DETAILED_TIMING_PASS"
} message]} {puts stderr "PROBE_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
