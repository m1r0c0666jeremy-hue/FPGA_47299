if {[catch {
import_device ph1_35p.db -package PH1P35MDG324 -speed 3
cd {D:/aaa_FPGA/region-sequence-stage1/build/stage1_four_row_probe_20261022_2151/gate_four_rows_20261022_230553}
open_project {D:/aaa_FPGA/region-sequence-stage1/build/stage1_four_row_probe_20261022_2151/gate_four_rows_20261022_230553/target_color_regions_stage1.al} -single_run
elaborate -top serial_wrapper
set_param rtl min_ripple_len 64
set_param rtl infer_fsm sequential
optimize_rtl
set_param gate map_mode area_prior
set_param gate pack_effort high
optimize_gate -packarea isolated.area
puts "PRIVATE_FOUR_ROW_GATE_PASS"
} message]} {puts stderr "PRIVATE_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
