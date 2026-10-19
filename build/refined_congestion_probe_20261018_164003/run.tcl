cd {D:/aaa_FPGA/transparent-ring-stability/build/refined_congestion_probe_20261018_164003}
if {[catch {
 import_device ph1_35p.db -package PH1P35MDG324 -speed 3
 import_db {D:/aaa_FPGA/transparent-ring-stability/build/refined_tracker_storage_place_20261018_131844/target_color_regions_placed.db}
 update_timing -mode manhattan
 report_hfn place -limit 50 -timing -file high_fanout.txt
 report_analysis manhattan -congestion -file congestion.txt
 report_param -detail -stage route -file route_parameters.txt
 puts "READONLY_CONGESTION_PROBE_PASS"
} message]} {puts stderr "PROBE_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
