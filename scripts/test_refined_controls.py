"""Existing physical gesture sequences plus immediate camera-fault pause."""
from refined_testlib import R,run,literal_fixture
src=literal_fixture(R/'scripts/test_ring_controls.py')
src=src.replace('reg rst=0;','reg rst=0,pause=0;').replace('rotate,diag);','rotate,diag,pause);')
src=src.replace('integer i;reg old;', 'reg [7:0] saved_session;reg old_cancel;integer i;reg old;')
src=src.replace('$display("RING_CONTROLS_PASS', '''reset_all;press(2,60);release_all;saved_session=session;pause=1;waitms(1);pause=0;waitms(2);
if(tracking || session!=saved_session+1)$fatal(1,"camera fault did not pause tracking once");
reset_all;press(5,1020);release_all;old_cancel=cancel;pause=1;waitms(1);pause=0;waitms(2);
if(dut.cal_ui || cancel==old_cancel || tracking)$fatal(1,"camera fault did not cancel calibration");
$display("REFINED_CONTROLS_PAUSE_PASS immediate capture fault pause, new session and calibration cancellation");
$display("RING_CONTROLS_PASS''')
run('controls_with_camera_pause',src,[R/'rtl/color_regions/stable_controls.v'])
