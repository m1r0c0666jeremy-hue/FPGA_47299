if {[catch {
import_device ph1_35p.db -package PH1P35MDG324 -speed 3
cd {D:/aaa_FPGA/region-sequence-stage1/build/stage1_valid_data_resetfree_20261024_0014/gate_baseline_20261024_002930}
open_project {D:/aaa_FPGA/region-sequence-stage1/build/stage1_valid_data_resetfree_20261024_0014/gate_baseline_20261024_002930/target_color_regions_stage1.al} -single_run
elaborate -top serial_wrapper
set_param rtl min_ripple_len 64
set_param rtl infer_fsm sequential
optimize_rtl
set_param gate map_mode area_prior
set_param gate pack_effort high
optimize_gate -packarea isolated.area
export_db isolated_gate.db
write_verilog isolated_netlist.v
if {[catch {report_hfn gate} e]} {puts "HFN_REPORT_UNAVAILABLE: $e"}
puts "PRIVATE_VALID_DATA_GATE_PASS"
} message]} {puts stderr "PRIVATE_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
