# Run from any directory with td_commands_prompt.exe <this-file>.
set root {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261022_231917/compiled_source}
set project {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261022_231917/target_color_regions_stage1.al}
set out {D:/aaa_FPGA/region-sequence-stage1/build/stage1_place_20261022_231917}
file mkdir $out
cd $out
if {[catch {
    import_device ph1_35p.db -package PH1P35MDG324 -speed 3
    cd [file dirname $project]
    open_project $project -single_run
    elaborate -top criticalwork_top
    cd $out
    read_adc [file join $root td_project stage1_pins.adc]
    read_ip_adc -ip ddr2 -file [file join $root user_source hdl_source ph1p35_ddr ddr2 src adc ddr2.adc]
    read_sdc [file join $root td_project target_lock.sdc]
    read_sdc -ip ddr2 [file join $root user_source hdl_source ph1p35_ddr ddr2 src sdc ddr2.sdc]
    read_sdc -ip w128_d512_fifo [file join $root user_source ip_source w128_d512_fifo w128_d512_fifo.tcl]
    set_param rtl min_ripple_len 64
    set_param rtl infer_fsm sequential
    optimize_rtl
    set_param gate map_mode area_prior
    set_param gate pack_effort high
    optimize_gate -packarea target_color_regions_gate.area
    set_param place opt_timing high
    set_param place ofv 70
    set_param place opt_max_density 50
    set_param place target_density 0.7
    set_param place target_density_pp 0.75
    set_param place aggressive_opt 20
    set_param place enhanced_beeline_opt 2
    set_param place enhanced_gp on
    set_param place non_crit_opt on
    set_param place post_place_opt high
    set_param route post_route_opt high
    set_param place pr_strategy 4
    set_param route effort normal
    set_param place pack_mode more_lut_pair
    set_param place max_fanout 128
    legalize_phy_inst
    export_db target_color_regions_gate.db
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
