# Run from any directory with td_commands_prompt.exe <this-file>.
set root {D:/aaa_FPGA/transparent-ring-stability/build/refined_full_20261018_000704/compiled_source}
set project {D:/aaa_FPGA/transparent-ring-stability/build/refined_full_20261018_000704/target_color_regions_refined.al}
set out {D:/aaa_FPGA/transparent-ring-stability/build/refined_full_20261018_000704}
file mkdir $out
cd $out
if {[catch {
    import_device ph1_35p.db -package PH1P35MDG324 -speed 3
    cd [file dirname $project]
    open_project $project -single_run
    elaborate -top criticalwork_top
    cd $out
    read_adc [file join $root td_project target_lock.adc]
    read_ip_adc -ip ddr2 -file [file join $root user_source hdl_source ph1p35_ddr ddr2 src adc ddr2.adc]
    read_sdc [file join $root td_project target_lock.sdc]
    read_sdc -ip ddr2 [file join $root user_source hdl_source ph1p35_ddr ddr2 src sdc ddr2.sdc]
    read_sdc -ip w128_d512_fifo [file join $root user_source ip_source w128_d512_fifo w128_d512_fifo.tcl]
    set_param rtl resource_sharing auto
    set_param rtl shifter_style shifter_reg
    optimize_rtl
    set_param gate add_map_lut_struct high
    set_param gate map_mode area_prior
    set_param gate multi_thread_mapping partition
    set_param gate map_mode area_prior
    set_param gate pack_effort high
    optimize_gate -packarea target_color_regions_gate.area
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
    set_param place pr_strategy 1
    set_param route effort routability
    legalize_phy_inst
    place
    report_area -io_info -file target_color_regions_place.area
    route
    report_area -io_info -file target_color_regions_phy.area
    update_timing -mode final
    report_timing_status -file target_color_regions_phy.ts
    report_timing_summary -file target_color_regions_pr.timing
    report_timing_exception -file target_color_regions_exception.timing
    report_clock_utilization -file target_color_regions_clocks.txt
    bitgen -bit target_color_regions.bit
    puts "TARGET_COLOR_REGIONS_BUILD_COMPLETED"
} message]} {
    puts stderr "BUILD_FAILED: $message"
    puts stderr $::errorInfo
    exit 1
}
exit
