if {[catch {
import_device ph1_35p.db -package PH1P35MDG324 -speed 3
cd {D:/aaa_FPGA/region-sequence-stage1/build/stage1_gate_param_check_20261023_2204/inspection_20261023_222318}
import_db {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261023_200045/target_color_regions_gate.db}
report_param -detail -stage place -file inherited_place.txt
report_param -detail -stage route -file inherited_route.txt
report_param -detail -stage flow -file inherited_flow.txt
puts "CHECKPOINT_PARAMETER_REPORT_ONLY_DONE"
} message]} {puts stderr "PARAM_REPORT_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
