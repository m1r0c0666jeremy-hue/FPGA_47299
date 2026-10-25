module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,pause=0;reg [2:0] keys=7;reg [1:0] sw=1;reg [7:0] cal=0;
wire req,up,tracking,show,conflict,pair,enter,sample,cancel,rotate;wire [2:0] zoom;wire [1:0] diag;wire [7:0] session;
refined_controls #(.CYCLES_PER_MS(1),.DEBOUNCE_MS(2),.LONG_PRESS_MS(1000)) dut(clk,rst,keys,sw,req,cal,req,up,zoom,tracking,show,session,conflict,pair,enter,sample,cancel,rotate,diag,pause);
task waitms(input integer n);repeat(n)@(negedge clk);endtask
task press(input [2:0] v,input integer n);begin keys=~v;waitms(n);end endtask
task release_all;begin press(0,12);end endtask
task reset_all;begin rst=0;keys=7;cal=0;waitms(4);rst=1;waitms(12);end endtask
task chord_test(input [2:0] v,input [2:0] first);
reg rq,en,sa,ca,tr,sh,rot;reg [2:0] z;reg [1:0] d;reg [7:0] ss;
begin reset_all;rq=req;en=enter;sa=sample;ca=cancel;tr=tracking;sh=show;rot=rotate;z=zoom;d=diag;ss=session;
press(first,40);press(v,1020);
if(req!=rq || sample!=sa || cancel!=ca || tracking!=tr || show!=sh || zoom!=z)$fatal(1,"chord leaked single action %d/%d",v,first);
if(v==5 && (enter==en || session!=ss+1))$fatal(1,"calibration chord");
if(v==6 && rotate==rot)$fatal(1,"rotation chord");
if(v==3 && diag!=0)$fatal(1,"disabled diagnostic chord");
rq=req;en=enter;rot=rotate;d=diag;ss=session;
press(first,1250);if(req!=rq || enter!=en || rotate!=rot || diag!=d || session!=ss || show!=sh || zoom!=z || tracking!=tr)$fatal(1,"partial release repeats/leaks");
release_all;if(req!=rq || enter!=en || rotate!=rot || diag!=d || show!=sh || zoom!=z || tracking!=tr)$fatal(1,"release leaked short action");end endtask
reg [7:0] saved_session;reg old_cancel;integer i;reg old;reg [2:0] zd;
initial begin reset_all;if(!rotate || diag!=0 || zoom!=0 || tracking || !show)$fatal(1,"reset defaults");
chord_test(5,1);chord_test(5,4);chord_test(6,2);chord_test(6,4);chord_test(3,1);chord_test(3,2);
reset_all;for(i=0;i<4;i=i+1)begin press(3,1020);release_all;end if(diag!=0)$fatal(1,"diagnostic four-page cycle");
reset_all;old=rotate;press(6,500);release_all;if(rotate!=old || tracking || zoom!=0)$fatal(1,"short chord");
reset_all;press(7,1020);release_all;if(!rotate || diag!=0 || enter || req || tracking || zoom!=0 || !show)$fatal(1,"triple-key action");
reset_all;press(4,130);zd=zoom;press(6,1020);release_all;if(!rotate || zoom!=zd || tracking || !show)$fatal(1,"late chord promoted");
reset_all;press(4,60);release_all;if(zoom!=1)$fatal(1,"short zoom");press(4,730);release_all;if(zoom!=3)$fatal(1,"five-step zoom repeat");
reset_all;press(2,60);release_all;if(!tracking)$fatal(1,"short selection");old=show;press(2,1020);release_all;if(show==old || !tracking)$fatal(1,"long show leaked selection");
reset_all;press(5,1020);release_all;cal=8'h20;waitms(8);old=sample;press(2,60);release_all;if(sample==old || tracking)$fatal(1,"white confirm");
cal=8'h40;waitms(8);old=sample;press(2,60);release_all;if(sample==old)$fatal(1,"background confirm");
cal=8'h60;waitms(8);old=sample;press(2,60);release_all;if(sample==old)$fatal(1,"A confirm");
cal=8'h80;waitms(8);old=sample;press(2,60);release_all;if(sample==old)$fatal(1,"B confirm");
old=cancel;press(1,60);release_all;if(cancel==old || req)$fatal(1,"calibration cancel leaked gain");
reset_all;press(5,1020);release_all;cal=8'h20;waitms(8);cal=0;waitms(8);press(2,60);release_all;if(!tracking)$fatal(1,"calibration completion not released");
reset_all;if(!rotate || diag!=0)$fatal(1,"reset after changes");
reset_all;press(2,60);release_all;saved_session=session;pause=1;waitms(1);pause=0;waitms(2);
if(tracking || session!=saved_session+1)$fatal(1,"camera fault did not pause tracking once");
reset_all;press(5,1020);release_all;old_cancel=cancel;pause=1;waitms(1);pause=0;waitms(2);
if(dut.cal_ui || cancel==old_cancel || tracking)$fatal(1,"camera fault did not cancel calibration");
reset_all;press(4,2600);release_all;if(zoom!=4)$fatal(1,"upper zoom endpoint");press(4,730);release_all;if(zoom!=4)$fatal(1,"zoom endpoint wrapped");
sw=0;waitms(12);press(4,2600);release_all;if(zoom!=0)$fatal(1,"reverse five-step endpoint");press(4,60);release_all;if(zoom!=0)$fatal(1,"lower zoom endpoint wrapped");
$display("REFINED_CONTROLS_PAUSE_PASS immediate capture fault pause, new session and calibration cancellation");
$display("RING_CONTROLS_PASS both chord orders, 100ms window/late key, short/long, repeat, all-release suppression, triple keys, four calibration steps and reset");$finish;end endmodule