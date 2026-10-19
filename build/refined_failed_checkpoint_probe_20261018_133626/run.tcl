cd {D:/aaa_FPGA/transparent-ring-stability/build/refined_failed_checkpoint_probe_20261018_133626}
if {[catch {
 import_device ph1_35p.db -package PH1P35MDG324 -speed 3
 import_db {D:/aaa_FPGA/transparent-ring-stability/build/refined_route_20261018_115500_912935/failed_normal_route.db}
 update_timing -mode manhattan
 report_clock_utilization -file restored_clocks.txt
 report_timing_exception -file restored_exceptions.timing
 report_area -io_info -file restored.area
 puts "FAILED_CHECKPOINT_READONLY_PROBE_PASS"
} message]} {puts stderr $message;puts stderr $::errorInfo;exit 1}
exit
