# Run from any directory with td_commands_prompt.exe <this-file>.
set root [file normalize [file join [file dirname [info script]] ..]]
set project [file join $root td_project target_lock_candidates.al]
set out [file join $root build target_lock_candidates]
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
    optimize_rtl
    optimize_gate -packarea target_lock_candidates_gate.area
    legalize_phy_inst
    place
    route
    report_area -io_info -file target_lock_candidates_phy.area
    update_timing -mode final
    report_timing_status -file target_lock_candidates_phy.ts
    report_timing_summary -file target_lock_candidates_pr.timing
    report_timing_exception -file target_lock_candidates_exception.timing
    report_clock_utilization -file target_lock_candidates_clocks.txt
    bitgen -bit target_lock_candidates.bit
    puts "TARGET_LOCK_CANDIDATES_BUILD_COMPLETED"
} message]} {
    puts stderr "BUILD_FAILED: $message"
    puts stderr $::errorInfo
    exit 1
}
exit
