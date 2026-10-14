"""Signed tip/identity and concurrent physical grid-bank regression."""
from pathlib import Path
import os,subprocess
R=Path(__file__).resolve().parents[1];O=R/'build/sim/stable_adversarial';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','');logs=[]
def run(name,src,modules):
    tb=O/(name+'.sv');tb.write_text(src,encoding='utf-8')
    for cmd in ([iv,'-g2012','-s','tb','-o',O/(name+'.vvp'),tb,*[R/f'rtl/color_regions/{m}.v' for m in modules]], [iv.with_name('vvp.exe'),O/(name+'.vvp')]):
        p=subprocess.run(list(map(str,cmd)),cwd=R,env=env,capture_output=True,text=True,timeout=900)
        logs.append(p.stdout+p.stderr);print(logs[-1],flush=True);(R/'reports/stable_adversarial.log').write_text('\n'.join(logs),encoding='utf-8')
        if p.returncode:raise SystemExit(p.returncode)
run('tracker',r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0,complete=1;reg [31:0] id=0;reg [9:0] cmd=3;reg [15:0] rev=0;
reg [1023:0] candidates=0;wire done,valid,hv;wire [127:0] a,b;wire [10:0] tx;wire [9:0] ty;wire [3:0] reason;wire [83:0] boxes;wire [1:0] selected_state;
stable_tracker dut(clk,rst,start,id,cmd,rev,complete,candidates,done,a,b,valid,tx,ty,reason,hv,boxes,selected_state);
function [127:0] c;input integer x,y,n;begin c=0;c[120]=1;c[61:42]=n;c[72:62]=x;c[82:73]=y;c[41:0]={10'(y+8),10'(y-8),11'(x+8),11'(x-8)};end endfunction
task frame;integer cycles;begin @(negedge clk);id=id+1;start=1;@(negedge clk);start=0;cycles=0;while(!done && cycles<200)begin @(negedge clk);cycles=cycles+1;end if(!done)$fatal(1,"tracker deadline");@(negedge clk);end endtask
task reset;begin @(negedge clk);rst=0;repeat(3)@(negedge clk);rst=1;id=0;candidates=0;cmd=3;rev=0;end endtask
task tipcase;input integer ax,ay,bx,by,ex,ey;begin reset;candidates[127:0]=c(ax,ay,48);candidates[639:512]=c(bx,by,2048);
frame;if(valid)$fatal(1,"early lock1");frame;if(valid)$fatal(1,"early lock2");frame;
if(!valid || tx!=ex || ty!=ey)$fatal(1,"signed tip %0d/%0d expected%0d/%0d",tx,ty,ex,ey);end endtask
integer k;
initial begin
tipcase(640,360,541,281,690,400);tipcase(640,360,739,281,591,400);
tipcase(640,360,541,439,690,321);tipcase(640,360,739,439,591,321);
// The second, unequal-size pair is nearer the guide centre than slot zero.
reset;candidates[127:0]=c(360,200,5000);candidates[639:512]=c(390,200,5000);
candidates[255:128]=c(690,360,48);candidates[767:640]=c(590,360,4096);frame;frame;frame;
if(!valid || a[72:62]!=690 || b[72:62]!=590)$fatal(1,"central pair selection");
// A larger different pair remains a distractor after confirmation.
candidates[127:0]=c(510,380,10000);candidates[639:512]=c(410,380,10000);frame;
if(!valid || a[72:62]!=690)$fatal(1,"identity switched to larger pair");
// Direction and area discontinuities cannot recover the stored identity.
candidates=0;candidates[127:0]=c(590,360,48);candidates[639:512]=c(690,360,4096);frame;if(valid)$fatal(1,"reversed tool accepted");
candidates[127:0]=c(690,360,10000);candidates[639:512]=c(590,360,4096);frame;if(valid)$fatal(1,"area discontinuity accepted");
candidates[127:0]=c(690,360,48);frame;if(valid)$fatal(1,"early recovery1");frame;if(valid)$fatal(1,"early recovery2");frame;if(!valid)$fatal(1,"nearby recovery");
// Invalid observations must not release identity and select a central impostor.
complete=0;frame;if(valid || !hv || reason!=8 || selected_state!=2)$fatal(1,"bad frame released identity");complete=1;
candidates=0;candidates[127:0]=c(510,380,48);candidates[639:512]=c(410,380,4096);frame;frame;frame;
if(valid || !hv)$fatal(1,"bad frame auto-switched tool");
candidates[127:0]=c(690,360,48);candidates[639:512]=c(590,360,4096);frame;frame;frame;if(!valid)$fatal(1,"bad-frame nearby recovery");
// A short forward gap restarts confirmation against the existing identity.
id=id+2;frame;if(valid || !hv)$fatal(1,"short gap released identity/confirmation");frame;frame;if(!valid)$fatal(1,"gap recovery");
id=id-1;frame;if(valid || !hv)$fatal(1,"duplicate consumed/released identity");frame;frame;frame;if(!valid)$fatal(1,"duplicate recovery");
candidates[639:512]=0;for(k=0;k<15;k=k+1)begin frame;if(valid)$fatal(1,"occluded tip");end
if(reason!=6 || hv || selected_state!=3)$fatal(1,"identity expiry");candidates[639:512]=c(590,360,4096);frame;frame;frame;if(valid)$fatal(1,"expired auto reacquire");
cmd=cmd+2;frame;frame;frame;if(!valid)$fatal(1,"manual new session");
rev=rev+1;frame;if(valid)$fatal(1,"parameter version reused confirmation");frame;frame;if(!valid)$fatal(1,"version reconfirm");
id=id+15;frame;if(valid || hv || reason!=6)$fatal(1,"long raw-frame gap did not expire");frame;frame;if(valid)$fatal(1,"long gap auto reselected");
// Too-close projected marks and out-of-frame extrapolation.
reset;candidates[127:0]=c(640,360,48);candidates[639:512]=c(650,360,48);frame;frame;frame;if(valid)$fatal(1,"short projection");
reset;candidates[127:0]=c(500,360,48);candidates[639:512]=c(800,360,48);frame;frame;frame;
for(k=0;k<7;k=k+1)begin candidates[127:0]=c(500-k*70,360,48);candidates[639:512]=c(800-k*70,360,48);frame;end
if(valid || reason!=7)$fatal(1,"outside tip visible %0d reason%0d",tx,reason);
complete=0;frame;if(valid || reason!=8)$fatal(1,"invalid frame tip");
$display("STABLE_TRACKER_ADVERSARIAL_PASS four quadrants, signed odd rounding, central multi-pair, area/direction identity, recovery/expiry, version, projection and outside");$finish;end endmodule''',['stable_tracker'])
run('banks',r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,v=0,bank=0,start=0,wb=0;reg [10:0] x=0;reg [9:0] y=0;reg [3:0] ha=0,hb=0;
wire busy,done,failed;wire [1023:0] cand;wire [17:0] cycles;integer xx,yy,p,n,k,delta;reg saw_done=0;
stable_grid dut(clk,rst,v,bank,x,y,ha,hb,start,wb,1'b0,84'd0,1'b0,busy,done,failed,cand,cycles);
function hit;input integer xx,yy,c,dd;begin xx=xx-dd;yy=yy-dd;
if(c==0)hit=(xx>=640 && xx<643 && yy>=320 && yy<336)||(xx>=480 && xx<496 && yy>=256 && yy<272)||(xx>=528 && xx<544 && yy>=256 && yy<272)||(xx>=0 && xx<16 && yy>=0 && yy<16);
else hit=xx>=700 && xx<716 && yy>=320 && yy<336;end endfunction
task check;input integer d;integer j,thin,left,right,edge_ok;reg [127:0] c;begin
thin=0;left=0;right=0;edge_ok=0;
if(failed || cycles>=212000)$fatal(1,"concurrent grid deadline");
for(j=0;j<4;j=j+1)begin c=cand[j*128+:128];if(!c[120])$fatal(1,"lost fourth region");
if(c[72:62]==641+d && c[82:73]==327+d && c[61:42]==48)thin=1;
if(c[72:62]==487+d && c[82:73]==263+d && c[61:42]==256)left=1;
if(c[72:62]==535+d && c[82:73]==263+d && c[61:42]==256)right=1;
if(c[72:62]==7+d && c[82:73]==7+d && c[61:42]==256)edge_ok=1;end
if(!(thin && left && right && edge_ok) || !cand[632] || cand[584:574]!=707+d || cand[594:585]!=327+d)$fatal(1,"bank/moments/minimum/gap mismatch d%0d",d);
end endtask
always @(negedge clk)if(done && wb==0)begin check(0);saw_done=1;end
initial begin repeat(3)@(negedge clk);rst=1;
for(delta=0;delta<=16;delta=delta+16)begin
bank=delta!=0;for(yy=0;yy<720;yy=yy+1)for(xx=0;xx<1280;xx=xx+4)begin @(negedge clk);v=1;x=xx;y=yy;
for(p=0;p<4;p=p+1)begin ha[p]=hit(xx+p,yy,0,delta);hb[p]=hit(xx+p,yy,1,delta);end end
@(negedge clk);v=0;repeat(4)@(negedge clk);wb=bank;start=1;@(negedge clk);start=0;end
if(!saw_done)$fatal(1,"worker blocked by concurrent capture");n=0;while(!done && n<213000)begin @(negedge clk);n=n+1;end check(16);
$display("STABLE_GRID_BANKS_PASS simultaneous capture/worker, four candidates, 16x16 minimum, 3px band, 32px same-colour gap, exact moments and top-left edge_ok");$finish;end endmodule''',['stable_grid','regions_divide'])
run('model_boundary',r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,v=0;reg [127:0] models=0;reg [15:0] rev=0;
wire [31:0] id,drop;wire ov;wire [639:0] meta;integer n,packets=0;reg [127:0] original;
function [63:0] model;input integer lo,hi;begin model=(64'h8000000000000000)|(64'(lo)<<54)|(64'(hi)<<45)|(64'd32<<37)|(64'd16<<29)|(64'd1<<27);end endfunction
stable_capture dut(clk,rst,sof,v,1'b0,{4{24'hc82020}},1'b0,1'b1,8'd1,models,rev,24'h400400,8'd0,1'b0,1'b0,1'b1,id,ov,meta,drop);
always @(negedge clk)if(ov)begin packets=packets+1;
if(meta[31:0]==1 && (meta[543:416]!==original || meta[559:544]!=0 || !meta[247]))$fatal(1,"old frame metadata changed");
if(meta[31:0]==2 && (meta[543:416]!=0 || meta[559:544]!=1 || !meta[247] || meta[245] || meta[246]))$fatal(1,"new frame model not used");end
initial begin original={model(195,255),model(345,30)};models=original;repeat(4)@(negedge clk);rst=1;
for(n=0;n<230400;n=n+1)begin @(negedge clk);sof=n==0;v=1;if(n==230398)begin models=0;rev=1;end end
// New raw-frame parameters are already visible, but the two previous WB groups
// above still belong to frame one. They must not lose their red classification.
for(n=0;n<230400;n=n+1)begin @(negedge clk);sof=n==0;v=1;
if(n==400 && dut.grid.stats0[3599][8:0]!=256)$fatal(1,"old frame tail classified by new model: %0d",dut.grid.stats0[3599][8:0]);end
@(negedge clk);sof=1;v=0;@(negedge clk);sof=0;repeat(213000)@(negedge clk);
if(packets!=2 || drop!=0)$fatal(1,"model boundary packet loss");
$display("STABLE_CAPTURE_MODELS_PASS continuous frames, pre-WB parameter update two clocks before post-WB SOF, frozen tail, model/revision provenance");$finish;end endmodule''',['stable_capture','stable_model_lane','stable_filter4','stable_grid','regions_divide','stable_tracker'])
print('STABLE_ADVERSARIAL_PASS',flush=True)
