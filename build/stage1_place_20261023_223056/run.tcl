# Run from any directory with td_commands_prompt.exe <this-file>.
set root {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261023_223056/compiled_source}
set project {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261023_223056/target_color_regions_stage1.al}
set out {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261023_223056}
file mkdir $out
cd $out
if {[catch {
    import_device ph1_35p.db -package PH1P35MDG324 -speed 3
    import_db {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261023_223056/input_gate.db}
    set_param place opt_timing high
    set_param place ofv 70
    set_param place opt_max_density 50
    set_param place target_density 0.6
    set_param place target_density_pp 0.7
    set_param place aggressive_opt 20
    set_param place enhanced_beeline_opt 2
    set_param place enhanced_gp on
    set_param place non_crit_opt on
    set_param place post_place_opt high
    set_param place enable_congestion_recovery on
    set_param route post_route_opt high
    set_param place pr_strategy 2
    set_param route effort normal
    set_param place macro_performance macro_congestion
    set_param place max_fanout 999999
    export_db target_color_regions_gate.db
    puts "STAGE1_VERIFIED_GATE_REUSE"
    report_param -detail -stage place -file effective_place.txt
    report_param -detail -stage route -file effective_route.txt
    place
    report_area -io_info -file target_color_regions_place.area
    report_clock_utilization -file placed_clocks.txt
    report_timing_exception -file placed_exceptions.timing
    export_db target_color_regions_placed.db
    puts "REFINED_PLACED_CHECKPOINT_READY"
    report_area -io_info -file target_color_regions_phy.area
    puts "REFINED_PLACE_COMPLETED"
} message]} {puts stderr "BUILD_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
