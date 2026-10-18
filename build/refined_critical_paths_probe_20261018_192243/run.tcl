cd {D:/aaa_FPGA/transparent-ring-stability/build/refined_critical_paths_probe_20261018_192243}
if {[catch {
 import_device ph1_35p.db -package PH1P35MDG324 -speed 3
 import_db {D:/aaa_FPGA/transparent-ring-stability/build/refined_full_20261018_183727/target_color_regions_placed.db}
 update_timing -mode manhattan
 report_analysis manhattan -timing -max_path_num 20 -path_num_per_ep 1 -file timing_analysis.txt
 puts "READONLY_CRITICAL_PATHS_PASS"
} message]} {puts stderr "PROBE_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
