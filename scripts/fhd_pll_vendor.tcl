# Use the installed PH1P35 calculator. The HDMI PLL is cascaded from the
# system's exact 60 MHz output, giving an integer 99/4 feedback ratio.
proc set_param {args} {}
set IP_DEVICE PH1P35MDG324
source {E:/TD 6.2.1/ip/depot/PLLF6F1D0P0_1.0/Dependency.tcl}
foreach {name fin enables frequencies} {
 system 50 {1 1 1 0 0 0 0 0} {100 24 60 100 100 100 100 100}
 hdmi 60 {1 1 0 0 0 0 0 0} {74.25 371.25 100 100 100 100 100 100}
} {
 set divs [Calc_Dividers $fin -1 NOCOMP $enables $frequencies {MHz MHz MHz MHz MHz MHz MHz MHz} {0 0 0 0 0 0 0 0} {deg deg deg deg deg deg deg deg} 0 0 -1 0]
 puts "$name dividers=$divs"
 set v [Calc_VCO_Fractional_auto $fin [lindex $divs 11] [lindex $divs 10] [lindex $divs 8] 0 $enables $frequencies {MHz MHz MHz MHz MHz MHz MHz MHz} [lrange $divs 0 7] -1 NOCOMP]
 puts "$name fraction=$v"
 puts "$name bandwidth=[Calc_BandWidth -1 [lindex $v 3] High {*}[lrange $divs 0 6]]"
 puts "$name actual=[Calc_ActualFreq [lindex $v 0] 1 [lrange $divs 0 7] [lrange $divs 0 7]]"
}
exit
