if {[catch {
import_device ph1_35p.db -package PH1P35MDG324 -speed 3
cd {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_review_20261024_0913/inspection_20261024_092143}
import_db {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261024_090145/target_color_regions_placed.db}
report_param -detail -stage place -file inherited_place.txt
report_param -detail -stage route -file inherited_route.txt
report_param -detail -stage flow -file inherited_flow.txt

if {[catch {report_hfn place} e]} {puts "HFN_REPORT_UNAVAILABLE: $e"}
puts "CHECKPOINT_STRUCTURE_REPORT_ONLY_DONE"
} message]} {puts stderr "PARAM_REPORT_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
