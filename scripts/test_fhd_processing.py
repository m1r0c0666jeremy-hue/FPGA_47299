"""Native-FHD pixel/region/protocol oracles; leaves historical evidence intact."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys
R=Path(__file__).resolve().parents[1]
V=R/'rtl/color_regions';IV=R/'tools/iverilog/ucrt64/bin/iverilog.exe'
ENV=os.environ.copy();ENV['PATH']=str(IV.parent)+os.pathsep+ENV.get('PATH','')
STAMP=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
O=R/'build/sim/fhd_processing'/STAMP;O.mkdir(parents=True,exist_ok=False)
P=R/'reports/fhd/processing';P.mkdir(parents=True,exist_ok=True)
def run(name,src,mods,timeout=600):
 tb=O/(name+'.sv');tb.write_text(src,encoding='utf-8')
 inputs=[V/(m+'.v') for m in mods]+[V/'fhd_metadata.vh']
 hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
 log=P/(STAMP+'_'+name+'.log');code=0
 for cmd in ([IV,'-g2012','-I',V,'-s','tb','-o',O/(name+'.vvp'),tb,*inputs[:-1]], [IV.with_name('vvp.exe'),O/(name+'.vvp')]):
  with log.open('a',encoding='utf-8') as f:
   p=subprocess.run(list(map(str,cmd)),cwd=R,env=ENV,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  code=p.returncode
  if code:break
 assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in ((R/n,h) for n,h in hashes.items())), 'source changed during test'
 (P/(STAMP+'_'+name+'.json')).write_text(json.dumps(dict(inputs=hashes,fixture_sha256=hashlib.sha256(tb.read_bytes()).hexdigest(),exit_code=code,output=str(O),log=str(log)),indent=2),encoding='utf-8')
 print(log.read_text(encoding='utf-8'),flush=True)
 if code:raise SystemExit(code)
COMMON=['stable_capture','stable_model_lane','stable_filter4','stable_grid','stable_tracker','regions_divide']
metadata=r'''`include "fhd_metadata.vh"
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;wire [767:0] meta;wire [31:0] fid,dropped,fus;wire [15:0] epoch;wire ov,tv;
stable_capture #(.V4(1)) dut(.I_clk(clk),.I_rst_n(rst),.I_sof(1'b0),.I_valid(1'b0),.I_fault(1'b0),.I_rgb(96'd0),
.I_pair(1'b0),.I_enable(1'b1),.I_session(8'd7),.I_models(128'd0),.I_revision(16'd2),.I_gains(24'd0),.I_cal_status(8'd0),
.I_cal_active(1'b0),.I_needs_cal(1'b0),.I_result_ready(1'b1),.O_frame_id(fid),.O_valid(ov),.O_meta(meta),.O_dropped(dropped),
.I_source_id(32'd1),.I_source_us(32'd7),.I_now_us(32'd9),.I_epoch(16'd1),.I_time_valid(1'b1),.I_model_state(2'd0),.I_quality(42'd0),
.O_frame_us(fus),.O_epoch(epoch),.O_time_valid(tv));
reg [127:0] a,b;reg [10:0] ty;wire [767:0] packet=dut.packet;
integer i,ay,by,y0,y1,n;
initial begin a=0;b=0;ty=0;repeat(3)@(negedge clk);rst=1;@(negedge clk);
force dut.a=a;force dut.b=b;force dut.ty=ty;
for(i=0;i<2000;i=i+1)begin
 ay=i%1080;by=(i*17)%1080;y0=(i*31)%1080;y1=(i*47)%1080;n=(i*10607)%2073601;
 a=0;b=0;a[75:65]=(i*13)%1920;a[86:76]=ay;b[75:65]=(i*19)%1920;b[86:76]=by;ty=(i*61)%1080;
 a[43:0]={11'(y1),11'(y0),11'd1919,11'd0};b[43:0]={11'(y0),11'(y1),11'd1799,11'd101};
 a[64:44]=n;b[64:44]=2073600-n;dut.raw_a[0]=n;dut.raw_b[0]=2073600-n;dut.filtered_a[0]=2073600;dut.filtered_b[0]=n;
 #1;
 if(`FHD_META_A_Y(packet)!==11'(ay) || `FHD_META_B_Y(packet)!==11'(by) || `FHD_META_TIP_Y(packet)!==ty)$fatal(1,"centroid/tip high bit %d",i);
 if(`FHD_META_A_BOX(packet)!==a[43:0] || `FHD_META_B_BOX(packet)!==b[43:0])$fatal(1,"box high bit %d",i);
 if(`FHD_META_A_COUNT(packet)!==21'(n) || `FHD_META_B_COUNT(packet)!==21'(2073600-n))$fatal(1,"area high bit %d",i);
 if(`FHD_META_RAW_A(packet)!==21'(n) || `FHD_META_RAW_B(packet)!==21'(2073600-n) || `FHD_META_FILTERED_A(packet)!==21'd2073600 || `FHD_META_FILTERED_B(packet)!==21'(n))$fatal(1,"pixel total high bit %d",i);
 if(packet[415:413]!=5 || packet[254] || packet[767:765])$fatal(1,"protocol version/reserved");
end
$display("FHD_METADATA_PASS 2000 independently packed coordinates/areas and 2073600-pixel totals");$finish;end
endmodule'''
grid=r'''`include "fhd_metadata.vh"
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,v=0,bank=0,start=0;reg [10:0] x=0,y=0;reg [7:0] ha=0,hb=0;
wire busy,done,failed;wire [1023:0] candidates;wire [17:0] cycles;
stable_grid dut(clk,rst,v,bank,x,y,ha,hb,start,1'b0,1'b0,88'd0,1'b0,busy,done,failed,candidates,cycles);
integer xx,yy,n,p,c,countA,countB,sumxA,sumyA,sumxB,sumyB,goodA,goodB,waited;
reg [91:0] got;reg [127:0] item;
function maskA(input integer xx,yy);maskA=(c==0) || (xx>=871 && xx<918 && yy>=1007 && yy<1078);endfunction
function maskB(input integer xx,yy);maskB=(c==0) || (xx>=1053 && xx<1110 && yy>=553 && yy<601);endfunction
task check(input integer index,expectedCount,expectedX,expectedY);begin
item=candidates[index*128+:128];
if(!item[120] || `FHD_C_COUNT(item)!=expectedCount || `FHD_C_X(item)!=expectedX || `FHD_C_Y(item)!=expectedY || `FHD_C_SUPPORT(item)!=100)$fatal(1,"candidate case%0d slot%0d count%0d centroid%0d/%0d support%0d",c,index,`FHD_C_COUNT(item),`FHD_C_X(item),`FHD_C_Y(item),`FHD_C_SUPPORT(item));end endtask
initial begin repeat(4)@(negedge clk);rst=1;
for(c=0;c<2;c=c+1)begin
 for(yy=0;yy<1080;yy=yy+1)begin for(xx=0;xx<1920;xx=xx+4)begin
 @(negedge clk);v=1;x=xx;y=yy;ha=0;hb=0;
 for(p=0;p<4;p=p+1)begin ha[p]=maskA(xx+p,yy);ha[p+4]=ha[p];hb[p]=maskB(xx+p,yy);hb[p+4]=hb[p];end
 end @(negedge clk);v=0;end
 repeat(4)@(negedge clk);
 // Python-independent arithmetic oracle for every local pixel moment.
 for(n=0;n<3600;n=n+1)begin
 countA=0;countB=0;sumxA=0;sumyA=0;sumxB=0;sumyB=0;
 for(yy=0;yy<24;yy=yy+1)for(xx=0;xx<24;xx=xx+1)begin
 if(maskA((n%80)*24+xx,(n/80)*24+yy))begin countA=countA+1;sumxA=sumxA+xx;sumyA=sumyA+yy;end
 if(maskB((n%80)*24+xx,(n/80)*24+yy))begin countB=countB+1;sumxB=sumxB+xx;sumyB=sumyB+yy;end end
 got=dut.stats0[n];
 if(got!=={10'(countB),10'(countA),13'(sumyB),13'(sumxB),10'(countB),13'(sumyA),13'(sumxA),10'(countA)})$fatal(1,"cell stats case%0d tile%0d %h",c,n,got);
 end
 start=1;@(negedge clk);start=0;waited=0;
 while(!done && waited<220000)begin @(negedge clk);waited=waited+1;end
 if(!done || failed)$fatal(1,"grid timeout/failed case%0d %0d",c,waited);
 if(c==0)begin check(0,2073600,959,539);check(4,2073600,959,539);end
 else begin check(0,3337,894,1042);check(4,2736,1081,576);end
end
$display("FHD_GRID_PASS 7200 exact 24x24 cells, max576/6624 moments, full-frame21-bit totals, highY candidates");$finish;end endmodule'''
tracker=r'''`include "fhd_metadata.vh"
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;reg [31:0] id=0;reg [1023:0] candidates=0;
wire done,tip,history;wire [127:0] a,b;wire [10:0] tx,ty;wire [3:0] reason,bounds;wire [87:0] boxes;wire [1:0] state;wire [9:0] hc;wire [15:0] hr;wire [31:0] hf;wire [4:0] loss;
stable_tracker dut(clk,rst,start,id,10'd1,16'd7,1'b1,candidates,done,a,b,tip,tx,ty,reason,history,boxes,state,hc,hr,hf,loss,bounds);
integer i,waited;reg [127:0] ca,cb;
task observe(input integer ax,ay,bx,by);begin
ca=0;cb=0;ca[120]=1;cb[120]=1;ca[75:65]=ax;ca[86:76]=ay;cb[75:65]=bx;cb[86:76]=by;
ca[64:44]=1500;cb[64:44]=1500;ca[93:87]=100;cb[93:87]=100;ca[43:0]={11'(ay+5),11'(ay-5),11'(ax+5),11'(ax-5)};cb[43:0]={11'(by+5),11'(by-5),11'(bx+5),11'(bx-5)};
candidates=0;candidates[127:0]=ca;candidates[639:512]=cb;end endtask
task frame;begin @(negedge clk);id=id+1;start=1;@(negedge clk);start=0;waited=0;while(!done && waited<500)begin @(negedge clk);waited=waited+1;end if(!done)$fatal(1,"tracker timeout");end endtask
initial begin repeat(4)@(negedge clk);rst=1;observe(1000,700,1080,700);
frame;if(tip)$fatal(1,"premature confirm1");frame;if(tip)$fatal(1,"premature confirm2");frame;if(!tip || tx!=960 || ty!=700)$fatal(1,"three-frame confirmation");
observe(1000,880,1080,880);frame;observe(1000,1040,1080,1040);frame;observe(1000,1060,1080,1060);
for(i=0;i<10;i=i+1)frame;
if(!tip || ty<1024 || boxes[43:33]!=1065 || boxes[87:77]!=1065)$fatal(1,"highY identity/tip/box truncated %d %h",ty,boxes);
candidates=0;for(i=0;i<14;i=i+1)begin frame;if(tip || state==3)$fatal(1,"missing color lifetime early %0d",i);end
frame;if(state!=3 || history)$fatal(1,"15 new-frame identity expiry state%0d loss%0d",state,loss);
$display("FHD_TRACKER_PASS three-frame confirm, 11bit highY geometry, missing-color hide and15-frame expiry");$finish;end endmodule'''
capture=r'''`include "fhd_metadata.vh"
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,v=0;reg [95:0] rgb=0;reg [31:0] source_id=0,source_us=0;
wire [767:0] meta;wire ov;wire [31:0] fid,dropped,fus;wire [15:0] epoch;wire tv;
function [63:0] model(input integer lo,hi);model={1'b1,9'(lo),9'(hi),8'd32,8'd16,2'd1,27'd0};endfunction
wire [127:0] models={model(195,255),model(345,30)};
stable_capture #(.V4(1)) dut(.I_clk(clk),.I_rst_n(rst),.I_sof(sof),.I_valid(v),.I_fault(1'b0),.I_rgb(rgb),
.I_pair(1'b0),.I_enable(1'b1),.I_session(8'd7),.I_models(models),.I_revision(16'd2),.I_gains(24'h400400),.I_cal_status(8'd0),
.I_cal_active(1'b0),.I_needs_cal(1'b0),.I_result_ready(1'b1),.O_frame_id(fid),.O_valid(ov),.O_meta(meta),.O_dropped(dropped),
.I_source_id(source_id),.I_source_us(source_us),.I_now_us(32'd1000000),.I_epoch(16'd11),.I_time_valid(1'b1),.I_model_state(2'd1),.I_quality(42'd99),
.O_frame_us(fus),.O_epoch(epoch),.O_time_valid(tv));
integer f,xx,yy,p,observed=0,waited;
function [23:0] pixel(input integer x,y);begin pixel=24'h808080;
if(x>=900 && x<948 && y>=640 && y<688)pixel=24'hd02020;
if(x>=1020 && x<1068 && y>=640 && y<688)pixel=24'h2020d0;end endfunction
always @(posedge clk)if(rst && ov)begin
observed=observed+1;
if(meta[31:0]!=observed || meta[415:413]!=5 || !meta[604] || !meta[245] || !meta[246] || !meta[247])$fatal(1,"capture identity/complete %0d meta%h",observed,meta);
if(meta[47:37]!=923 || `FHD_META_A_Y(meta)!=663 || meta[68:58]!=1043 || `FHD_META_B_Y(meta)!=663)$fatal(1,"capture exact centroid");
if(`FHD_META_A_COUNT(meta)!=2304 || `FHD_META_B_COUNT(meta)!=2304 || `FHD_META_RAW_A(meta)!=2304 || `FHD_META_FILTERED_B(meta)!=2304)$fatal(1,"capture native component totals");
if(meta[671:640]!=observed*33333 || meta[719:704]!=11 || !meta[720] || meta[764:723]!=99)$fatal(1,"capture atomic source time/profile");
if((observed<3 && meta[32]) || (observed>=3 && (!meta[32] || meta[89:79]!=863 || `FHD_META_TIP_Y(meta)!=663)))$fatal(1,"capture three-frame native tip");
end
initial begin repeat(4)@(negedge clk);rst=1;
for(f=1;f<=4;f=f+1)begin source_id=f;source_us=f*33333;
for(yy=0;yy<1080;yy=yy+1)begin for(xx=0;xx<1920;xx=xx+4)begin
@(negedge clk);sof=xx==0 && yy==0;v=1;for(p=0;p<4;p=p+1)rgb[95-p*24-:24]=pixel(xx+p,yy);end
@(negedge clk);sof=0;v=0;repeat(90)@(negedge clk);end end
@(negedge clk);source_id=5;source_us=166665;sof=1;v=0;@(negedge clk);sof=0;
waited=0;while(observed<4 && waited<220000)begin @(negedge clk);waited=waited+1;end
if(observed!=4 || dropped!=0)$fatal(1,"capture result count%0d dropped%0d",observed,dropped);
$display("FHD_CAPTURE_PASS four complete native1080 RGB frames, exact classifier/filter/grid/tracker totals, immutable v5 timing, three-frame tip");$finish;end endmodule'''
cal=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,v=0,enter=0,sample=0;reg [95:0] rgb=0;
wire [11:0] gr,gb;wire [127:0] models;wire [15:0] rev;wire active,needs,fp;wire [7:0] status,fs;wire [23:0] fg;wire [1:0] ms;wire [41:0] quality;
stable_calibration dut(clk,rst,sof,v,rgb,1'b0,enter,sample,1'b0,1'b0,gr,gb,models,rev,active,needs,status,fp,fg,fs,ms,quality);
integer f,xx,yy,n=0,stage=0,ex=0,ey=0,expectedIndex=0,white=0,bg=0;
reg [21:0] coordinates[0:511];
always @(posedge clk)if(rst && dut.sample_write)begin
 if(stage==1)begin
 if(dut.rx!=944+(n%4)*8 || dut.ry!=524+((n%64)/4)*2 || dut.sample_wraddr!=n)$fatal(1,"sparse32ROI position %0d at%0d/%0d",n,dut.rx,dut.ry);
 white=white+1;end
 if(stage==2)begin
 if({dut.rx,dut.ry}!==coordinates[n] || dut.sample_wraddr!=n)$fatal(1,"background ordering %0d at%0d/%0d expected%h",n,dut.rx,dut.ry,coordinates[n]);bg=bg+1;end
 n=n+1;end
task frames;begin
for(f=0;f<8;f=f+1)begin
 for(yy=0;yy<1080;yy=yy+1)for(xx=0;xx<1920;xx=xx+4)begin @(negedge clk);sof=xx==0 && yy==0;v=1;end
end
@(negedge clk);sof=1;v=0;@(negedge clk);sof=0;end endtask
initial begin $readmemh("COORDINATES",coordinates);repeat(4)@(negedge clk);rst=1;rgb={4{24'h808080}};
@(negedge clk);enter=1;@(negedge clk);enter=0;sample=1;@(negedge clk);sample=0;stage=1;
frames;repeat(100)@(negedge clk);
if(n!=512 || white!=512 || dut.phase!==3'd2 || status[3:0]!==4'd0 || gr!==12'd1024 || gb!==12'd1024)$fatal(1,"white8frames count%0d phase%0d status%h gain%0d/%0d",n,dut.phase,status,gr,gb);
n=0;stage=2;sample=1;@(negedge clk);sample=0;frames;
if(n!=512 || bg!=512 || dut.phase!=3 || !dut.background_valid || status[3:0]!=0)$fatal(1,"background8frames count%0d phase%0d status%h",n,dut.phase,status);
$display("FHD_CALIBRATION_PASS 16 complete1080 frames, exact256 native samples/frame,512-word white/background, unity whitegain");$finish;end endmodule'''
calibration_models=cal.replace('if(stage==1)begin','if(stage==1 || stage>=3)begin').replace(
 '$display("FHD_CALIBRATION_PASS 16 complete1080 frames, exact256 native samples/frame,512-word white/background, unity whitegain");',r'''
 n=0;stage=3;rgb={4{24'hc02020}};sample=1;@(negedge clk);sample=0;frames;
 for(ex=0;ex<512;ex=ex+1)if(dut.samples[ex]!=={4{24'hc02020}} || dut.background[ex]!=={4{24'h808080}})$fatal(1,"A/background sampleRAM %0d %h/%h",ex,dut.samples[ex],dut.background[ex]);
 expectedIndex=0;while((dut.phase!=4 || dut.state!=0) && status[3:0]==0 && expectedIndex<3000000)begin @(negedge clk);expectedIndex=expectedIndex+1;end
 if(n!=512 || dut.phase!=4 || status[3:0]!=0)$fatal(1,"A material model n%0d status%h cycles%0d peak%0d cluster%0d positive%0d negative%0d gain%0d/%0d retained%0d retention%0d sample%h bg%h",n,status,expectedIndex,dut.peak,dut.cluster,dut.positive_sum,dut.negative_sum,gr,gb,dut.retained[0],dut.retention_seen,dut.samples[0],dut.background[0]);
 n=0;stage=4;rgb={4{24'h2020c0}};sample=1;@(negedge clk);sample=0;frames;
 expectedIndex=0;while((dut.phase!=0 || dut.state!=0) && expectedIndex<3000000)begin @(negedge clk);expectedIndex=expectedIndex+1;end
 if(n!=512 || dut.phase!=0 || status[3:0]!=0 || !dut.calibrated[0])$fatal(1,"B material publication n%0d status%h cycles%0d",n,status,expectedIndex);
 @(negedge clk);sof=1;v=0;@(negedge clk);sof=0;
 if(ms!=1 || needs || models!==dut.profiles[0] || !models[63] || !models[127])$fatal(1,"learned profile not atomic at next source SOF");
 if(!(models[62:54]>models[53:45] && models[53:45]>0) || models[126:118]>240 || models[117:109]<=240)$fatal(1,"learned red/blue hue windows %h",models);
 if(models[36:29]<8 || models[100:93]<8 || gr!==12'd1024 || gb!==12'd1024)$fatal(1,"background exclusion/whitegain");
 $display("FHD_CALIBRATION_MODELS_PASS four-step32 full1080 frames, exact8frame sparse samples/step, red/blue learned and atomically published");''')
if __name__=='__main__':
 requested=set(sys.argv[1:] or ['metadata','grid','tracker','calibration_models','capture'])
 if 'metadata' in requested:run('metadata',metadata,COMMON)
 if 'grid' in requested:run('grid',grid,['stable_grid','regions_divide'])
 if 'tracker' in requested:run('tracker',tracker,['stable_tracker'])
 if 'calibration' in requested or 'calibration_models' in requested:
  points=[]
  for f in range(8):
   row=[(80+240*x+8*f,40+180*y+8*((3*f)%8)) for y in range(6) for x in range(8)]
   row +=[(x,y) for y in range(532,548,2) for x in (952,960)]
   points+=sorted(row,key=lambda p:(p[1],p[0]))
  cf=O/'background_coordinates.hex';cf.write_text('\n'.join(f'{x<<11|y:06x}' for x,y in points),encoding='ascii')
  if 'calibration' in requested:run('calibration',cal.replace('COORDINATES',cf.as_posix()),['stable_calibration','regions_divide'])
  if 'calibration_models' in requested:run('calibration_models',calibration_models.replace('COORDINATES',cf.as_posix()),['stable_calibration','regions_divide'])
 if 'capture' in requested:run('capture',capture,COMMON)
