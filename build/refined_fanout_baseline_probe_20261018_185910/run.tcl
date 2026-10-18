cd {D:/aaa_FPGA/transparent-ring-stability/build/refined_fanout_baseline_probe_20261018_185910}
if {[catch {
 import_device ph1_35p.db -package PH1P35MDG324 -speed 3
 import_db {D:/aaa_FPGA/transparent-ring-stability/build/refined_full_20261018_170526/target_color_regions_placed.db}
 update_timing -mode manhattan
 report_hfn place -limit 30 -timing -file high_fanout.txt
 report_param -detail -stage place -file place_parameters.txt
 puts "READONLY_FANOUT_BASELINE_PASS"
} message]} {puts stderr "PROBE_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
