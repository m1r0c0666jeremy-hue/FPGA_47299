"""Debounced chord ordering, suppression, partial release and reset defaults."""
from test_ring_calibration import R,run
src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [2:0] keys=7;reg [1:0] sw=1;reg [7:0] cal=0;
wire req,up,tracking,show,conflict,pair,enter,sample,cancel,rotate;wire [1:0] zoom,diag;wire [7:0] session;
stable_controls #(.CYCLES_PER_MS(1),.DEBOUNCE_MS(2),.LONG_PRESS_MS(1000)) dut(clk,rst,keys,sw,req,cal,req,up,zoom,tracking,show,session,conflict,pair,enter,sample,cancel,rotate,diag);
task waitms(input integer n);repeat(n)@(negedge clk);endtask
task press(input [2:0] v,input integer n);begin keys=~v;waitms(n);end endtask
task release_all;begin press(0,12);end endtask
task reset_all;begin rst=0;keys=7;cal=0;waitms(4);rst=1;waitms(12);end endtask
task chord_test(input [2:0] v,input [2:0] first);
reg rq,en,sa,ca,tr,sh,rot;reg [1:0] z,d;reg [7:0] ss;
begin reset_all;rq=req;en=enter;sa=sample;ca=cancel;tr=tracking;sh=show;rot=rotate;z=zoom;d=diag;ss=session;
press(first,40);press(v,1020);
if(req!=rq || sample!=sa || cancel!=ca || tracking!=tr || show!=sh || zoom!=z)$fatal(1,"chord leaked single action %d/%d",v,first);
if(v==5 && (enter==en || session!=ss+1))$fatal(1,"calibration chord");
if(v==6 && rotate==rot)$fatal(1,"rotation chord");
if(v==3 && diag!=d+1)$fatal(1,"diagnostic chord");
rq=req;en=enter;rot=rotate;d=diag;ss=session;
press(first,1250);if(req!=rq || enter!=en || rotate!=rot || diag!=d || session!=ss || show!=sh || zoom!=z || tracking!=tr)$fatal(1,"partial release repeats/leaks");
release_all;if(req!=rq || enter!=en || rotate!=rot || diag!=d || show!=sh || zoom!=z || tracking!=tr)$fatal(1,"release leaked short action");end endtask
integer i;reg old;reg [1:0] zd;
initial begin reset_all;if(!rotate || diag!=0 || zoom!=0 || tracking || !show)$fatal(1,"reset defaults");
chord_test(5,1);chord_test(5,4);chord_test(6,2);chord_test(6,4);chord_test(3,1);chord_test(3,2);
reset_all;for(i=0;i<3;i=i+1)begin press(3,1020);release_all;end if(diag!=0)$fatal(1,"diagnostic three-page cycle");
reset_all;old=rotate;press(6,500);release_all;if(rotate!=old || tracking || zoom!=0)$fatal(1,"short chord");
reset_all;press(7,1020);release_all;if(!rotate || diag!=0 || enter || req || tracking || zoom!=0 || !show)$fatal(1,"triple-key action");
reset_all;press(4,130);zd=zoom;press(6,1020);release_all;if(!rotate || zoom!=zd || tracking || !show)$fatal(1,"late chord promoted");
reset_all;press(4,60);release_all;if(zoom!=1)$fatal(1,"short zoom");press(4,730);release_all;if(zoom!=2)$fatal(1,"zoom repeat or endpoint");
reset_all;press(2,60);release_all;if(!tracking)$fatal(1,"short selection");old=show;press(2,1020);release_all;if(show==old || !tracking)$fatal(1,"long show leaked selection");
reset_all;press(5,1020);release_all;cal=8'h20;waitms(8);old=sample;press(2,60);release_all;if(sample==old || tracking)$fatal(1,"white confirm");
cal=8'h40;waitms(8);old=sample;press(2,60);release_all;if(sample==old)$fatal(1,"background confirm");
cal=8'h60;waitms(8);old=sample;press(2,60);release_all;if(sample==old)$fatal(1,"A confirm");
cal=8'h80;waitms(8);old=sample;press(2,60);release_all;if(sample==old)$fatal(1,"B confirm");
old=cancel;press(1,60);release_all;if(cancel==old || req)$fatal(1,"calibration cancel leaked gain");
reset_all;press(5,1020);release_all;cal=8'h20;waitms(8);cal=0;waitms(8);press(2,60);release_all;if(!tracking)$fatal(1,"calibration completion not released");
reset_all;if(!rotate || diag!=0)$fatal(1,"reset after changes");
$display("RING_CONTROLS_PASS both chord orders, 100ms window/late key, short/long, repeat, all-release suppression, triple keys, four calibration steps and reset");$finish;end endmodule'''
run('controls_chords',src,[R/'rtl/color_regions/stable_controls.v'])
