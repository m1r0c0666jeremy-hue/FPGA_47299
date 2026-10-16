"""Existing physical gesture sequences plus immediate camera-fault pause."""
from refined_testlib import R,run,literal_fixture
src=literal_fixture(R/'scripts/test_ring_controls.py')
src=src.replace('reg rst=0;','reg rst=0,pause=0;').replace('rotate,diag);','rotate,diag,pause);')
src=src.replace('wire [1:0] zoom,diag;','wire [2:0] zoom;wire [1:0] diag;').replace('reg [1:0] z,d;','reg [2:0] z;reg [1:0] d;').replace('reg [1:0] zd;','reg [2:0] zd;')
src=src.replace('if(zoom!=2)$fatal(1,"zoom repeat or endpoint");','if(zoom!=3)$fatal(1,"five-step zoom repeat");')
src=src.replace('i<3;i=i+1)begin press(3','i<4;i=i+1)begin press(3').replace('diagnostic three-page cycle','diagnostic four-page cycle')
src=src.replace('integer i;reg old;', 'reg [7:0] saved_session;reg old_cancel;integer i;reg old;')
src=src.replace('$display("RING_CONTROLS_PASS', '''reset_all;press(2,60);release_all;saved_session=session;pause=1;waitms(1);pause=0;waitms(2);
if(tracking || session!=saved_session+1)$fatal(1,"camera fault did not pause tracking once");
reset_all;press(5,1020);release_all;old_cancel=cancel;pause=1;waitms(1);pause=0;waitms(2);
if(dut.cal_ui || cancel==old_cancel || tracking)$fatal(1,"camera fault did not cancel calibration");
reset_all;press(4,2600);release_all;if(zoom!=4)$fatal(1,"upper zoom endpoint");press(4,730);release_all;if(zoom!=4)$fatal(1,"zoom endpoint wrapped");
sw=0;waitms(12);press(4,2600);release_all;if(zoom!=0)$fatal(1,"reverse five-step endpoint");press(4,60);release_all;if(zoom!=0)$fatal(1,"lower zoom endpoint wrapped");
$display("REFINED_CONTROLS_PAUSE_PASS immediate capture fault pause, new session and calibration cancellation");
$display("RING_CONTROLS_PASS''')
run('controls_with_camera_pause',src.replace('stable_controls #','refined_controls #'),[R/'rtl/color_regions/refined_controls.v'])
