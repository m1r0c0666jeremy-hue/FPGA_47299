cd {D:/aaa_FPGA/transparent-ring-stability/build/refined_checkpoint_timing_20261018_223206}
if {[catch {
 import_device ph1_35p.db -package PH1P35MDG324 -speed 3
 import_db {D:/aaa_FPGA/transparent-ring-stability/build/refined_timing_paths_place_20261018_222507/target_color_regions_placed.db}
 update_timing -mode manhattan
 report_timing_summary -file detailed.timing -ep_num 20 -path_num 1
 report_analysis manhattan -timing -max_path_num 20 -path_num_per_ep 1 -file timing_analysis.txt
 puts "READONLY_CHECKPOINT_TIMING_PASS"
} message]} {puts stderr "PROBE_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
