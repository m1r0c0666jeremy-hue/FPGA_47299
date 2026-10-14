"""Production support filter, calibration, controls and real capture-chain tests."""
from pathlib import Path
import os,subprocess,argparse
R=Path(__file__).resolve().parents[1];O=R/'build/sim/stable_pipeline';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
p=argparse.ArgumentParser();p.add_argument('--stage',choices=['filter','calibration','capture','controls','packer','all'],default='all');a=p.parse_args()
def run(name,source,modules):
    tb=O/(name+'.sv');tb.write_text(source,encoding='utf-8');logs=[]
    for cmd in ([str(iv),'-g2012','-s','tb','-o',str(O/(name+'.vvp')),str(tb),*[str(R/'rtl/color_regions'/m) for m in modules]],
                [str(iv.with_name('vvp.exe')),str(O/(name+'.vvp'))]):
        q=subprocess.run(cmd,cwd=R,env=env,capture_output=True,text=True,timeout=1200)
        logs.append(q.stdout+q.stderr);print(logs[-1],flush=True)
        (R/f'reports/transparent_ring/regression/stable_{name}.log').write_text('\n'.join(logs),encoding='utf-8')
        if q.returncode:raise SystemExit(q.returncode)
if a.stage in ('all','filter'):
    def point(x,y,c,f):
        if not(0<=x<1280 and 0<=y<720):return False
        if c==0:return (100<=x<116 and 100<=y<116 and (x<103 or x>=113 or y<103 or y>=113)) or (y==0 and x<20) or (x==1279 and y>700) or (x==35+f and y==40)
        return (x==640 and 300<=y<360) or (x==50 and y==719) or (x==51 and y==719) or (x==76 and y==60+f)
    with (O/'filter.hex').open('w') as output:
        for f in range(2):
            for y in range(720):
                for x in range(0,1280,4):
                    mask=0
                    for lane in range(4):
                        for c in range(2):
                            yes=point(x+lane,y,c,f) and any(point(x+lane+dx,y+dy,c,f) for dy in (-1,0,1) for dx in (-1,0,1) if dx or dy)
                            mask|=int(yes)<<(lane*2+c)
                    output.write(f'{mask:02x}\n')
    run('filter',f'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,v=0;reg [10:0] x=0;reg [9:0] y=0;reg [1:0] bank=2;reg [7:0] mask=0;
wire ov;wire [1:0] ob;wire [10:0] ox;wire [9:0] oy;wire [3:0] ha,hb;reg [7:0] expected[0:460799];integer f,xx,yy,i,n=0;reg [7:0] got;
stable_filter4 dut(clk,rst,v,x,y,bank,mask,ov,ob,ox,oy,ha,hb);
function px;input integer xx,yy,cc,ff;begin
if(cc==0)px=(xx>=100 && xx<116 && yy>=100 && yy<116 && (xx<103 || xx>=113 || yy<103 || yy>=113)) || (yy==0 && xx<20) || (xx==1279 && yy>700) || (xx==35+ff && yy==40);
else px=(xx==640 && yy>=300 && yy<360) || ((xx==50 || xx==51) && yy==719) || (xx==76 && yy==60+ff);end endfunction
always @(posedge clk)begin #1;if(rst && ov)begin
if(ox!==(n%320)*4 || oy!==((n/320)%720) || ob!==(2+(n/230400)))$fatal(1,"filter coordinates n%0d xy%0d/%0d bank%0d",n,ox,oy,ob);
for(i=0;i<4;i=i+1)begin got[i*2]=ha[i];got[i*2+1]=hb[i];end
if(got!==expected[n])$fatal(1,"filter pixels n%0d %h != %h",n,got,expected[n]);n=n+1;end end
initial begin $readmemh("{(O/'filter.hex').as_posix()}",expected);repeat(3)@(negedge clk);rst=1;
for(f=0;f<2;f=f+1)for(yy=0;yy<720;yy=yy+1)for(xx=0;xx<1280;xx=xx+4)begin
@(negedge clk);v=1;x=xx;y=yy;bank=2+f;for(i=0;i<4;i=i+1)begin mask[i*2]=px(xx+i,yy,0,f);mask[i*2+1]=px(xx+i,yy,1,f);end end
@(negedge clk);v=0;repeat(340)@(negedge clk);if(n!=460800)$fatal(1,"filter lost groups %0d",n);
$display("STABLE_FILTER_PASS two continuous full frames, thin ring, one-pixel line, all edges, isolated noise");$finish;end endmodule''',['stable_filter4.v'])
if a.stage in ('all','calibration'):
    import sys
    subprocess.run([sys.executable,str(R/'scripts/test_ring_calibration.py')],cwd=R,check=True)
if a.stage in ('all','capture'):
    run('capture','''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,v=0,fault=0,pair=0,enable=1,ready=1;reg [95:0] rgb=0;wire [31:0] fid,dropped;wire ov;wire [639:0] meta;
reg [127:0] models;integer f,x,y,i,n,count=0;reg [23:0] pixel;
function [63:0] model;input integer lo,hi;begin model=(64'h8000000000000000)|(64'(lo)<<54)|(64'(hi)<<45)|(64'd32<<37)|(64'd16<<29)|(64'd1<<27);end endfunction
stable_capture dut(clk,rst,sof,v,fault,rgb,pair,enable,8'd1,models,16'd0,24'h400400,8'd0,1'b0,1'b0,ready,fid,ov,meta,dropped);
always @(posedge clk)begin #1;if(ov)begin count=count+1;
if(meta[415:413]!=2 || meta[543:416]!==models || !meta[247])$fatal(1,"capture identity/incomplete");
if(meta[31:0]==3 && (!meta[32] || meta[89:79]!=694 || meta[99:90]!=364))$fatal(1,"third-frame tip %0d/%0d valid%0d",meta[89:79],meta[99:90],meta[32]);
if(meta[31:0]==6 && meta[32])$fatal(1,"missing blue stale tip");
if(meta[31:0]==9 && !meta[32])$fatal(1,"short loss not recovered");
if(meta[31:0]>=24 && (meta[32] || meta[36:33]!=6))$fatal(1,"long loss not expired frame%0d reason%0d",meta[31:0],meta[36:33]);
end end
initial begin models={model(195,255),model(345,30)};repeat(3)@(negedge clk);rst=1;
for(f=1;f<=25;f=f+1)for(y=0;y<720;y=y+1)for(x=0;x<1280;x=x+4)begin
@(negedge clk);v=1;sof=x==0 && y==0;
for(i=0;i<4;i=i+1)begin pixel=24'h302430;
if(f<10 && x+i>=600 && x+i<640 && y>=350 && y<380)pixel=24'hc81e1e;
if(f<10 && f!=6 && x+i>=450 && x+i<490 && y>=350 && y<380)pixel=24'h1e28c8;
rgb[95-i*24-:24]=pixel;end end
@(negedge clk);v=0;sof=1;@(negedge clk);sof=0;repeat(213000)@(negedge clk);
if(count!=25 || dropped!=0)$fatal(1,"capture lost packets %0d dropped%0d",count,dropped);
$display("STABLE_CAPTURE_PASS 25 full frames, real classification/filter/grid/tool/tip, short and long loss");$finish;end endmodule''',['stable_capture.v','stable_model_lane.v','stable_filter4.v','stable_grid.v','regions_divide.v','stable_tracker.v'])
if a.stage in ('all','packer'):
    run('packer','''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,v=0;reg [95:0] rgb=0;wire os,ov;wire [127:0] out;reg [7:0] expected[0:30719];integer group,n=0,j,offset;
stable_packer dut(clk,rst,sof,v,rgb,os,ov,out);
always @(posedge clk)begin #1;if(ov)begin for(j=0;j<16;j=j+1)if(out[127-j*8-:8]!==expected[n*16+j])$fatal(1,"pack mismatch word%0d byte%0d",n,j);n=n+1;end end
initial begin for(j=0;j<30720;j=j+1)expected[j]=(j*37+11)%256;
repeat(3)@(negedge clk);rst=1;
for(group=0;group<1280;group=group+1)begin
@(negedge clk);sof=group==0;v=1;for(j=0;j<12;j=j+1)rgb[95-j*8-:8]=expected[group*12+j];
if(group%17==3)begin @(negedge clk);sof=0;v=0;repeat(3)@(negedge clk);end end
@(negedge clk);sof=0;v=0;repeat(3)@(negedge clk);if(n!=960)$fatal(1,"pack words%0d",n);
$display("STABLE_PACKER_PASS 960 exact words with valid gaps");$finish;end endmodule''',['stable_packer.v'])
if a.stage in ('all','controls'):
    run('controls','''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [2:0] keys=7;reg [1:0] sw=0;reg ack=0;reg [7:0] status=0;
wire req,up,tracking,show,pair,conflict,enter,sample,cancel;wire [1:0] zoom;wire [7:0] session;
stable_controls #(.CYCLES_PER_MS(2),.DEBOUNCE_MS(2),.LONG_PRESS_MS(20)) dut(clk,rst,keys,sw,ack,status,req,up,zoom,tracking,show,session,conflict,pair,enter,sample,cancel);
task hold;input [2:0] k;input integer ticks;begin @(negedge clk);keys=k;repeat(ticks*2+10)@(negedge clk);keys=7;repeat(16)@(negedge clk);end endtask
initial begin repeat(3)@(negedge clk);rst=1;repeat(16)@(negedge clk);
hold(2,25);if(!enter || req || zoom!=0 || tracking)$fatal(1,"calibration chord leaked single actions");
status=8'h40;repeat(4)@(negedge clk);hold(5,5);if(!sample || tracking)$fatal(1,"KEY3 not sample");
status=0;repeat(8)@(negedge clk);hold(5,5);if(!tracking)$fatal(1,"normal short key");
hold(5,25);if(show)$fatal(1,"long hide");if(!tracking)$fatal(1,"long gesture toggled tracking");
hold(6,5);if(!req || tracking)$fatal(1,"gain did not pause tracking");
$display("STABLE_CONTROLS_PASS chord, calibration sample, normal gestures, gain pause");$finish;end endmodule''',['stable_controls.v'])
