"""Native1080 transport/display checks. Does not rewrite legacy fixtures."""
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
from refined_testlib import R, run

ap=argparse.ArgumentParser()
ap.add_argument('--suite',choices=['all','timing','ingress','video','store','geometry','recovery'],default='all')
ap.add_argument('--full',action='store_true')
ap.add_argument('--zoom',type=int)
ap.add_argument('--rotate',type=int)
ap.add_argument('--workers',type=int,default=3)
ap.add_argument('--color',action='store_true',help='Independent full-hue saturated model: every supported source mask is A=1.')
ap.add_argument('--mode',type=int,choices=range(4))
ap.add_argument('--pair',type=int,choices=(0,1))
ap.add_argument('--video-backend',choices=['iverilog','native'],default='iverilog')
a=ap.parse_args()
rtl=R/'rtl/color_regions'
inc=('-I',str(rtl))

timing=r'''`timescale 1ns/1ps
module tb;
reg clk=0,rst=0;always #6.734006734 clk=~clk;
wire vs,hs,de,user,last;
fhd_vtc dut(rst,clk,vs,hs,de,user,last);
integer h=0,v=0,n=0,active=0,starts=0,ends=0,synclines=0;
initial begin repeat(4)@(negedge clk);rst=1;
repeat(2475000)begin @(negedge clk);
if(de!==(h<1920 && v<1080) || hs!==(h>=2008 && h<2052) || vs!==(v>=1084 && v<1089))
$fatal(1,"native timing h%0d v%0d de%b hs%b vs%b",h,v,de,hs,vs);
if(user!==(h==0 && v==0) || last!==(h==1919 && v<1080))$fatal(1,"stream boundary");
active=active+de;starts=starts+user;ends=ends+last;if(vs && h==0)synclines=synclines+1;
if(h==2199)begin h=0;v=v+1;end else h=h+1;
end
if(active!=2073600 || starts!=1 || ends!=1080 || synclines!=5)$fatal(1,"timing counts");
$display("FHD_TIMING_PASS exact1920x1080/2200x1125 positive44/5 sync,88/4 front,148/36 back,2073600 pixels");$finish;
end endmodule'''

store=r'''`timescale 1ns/1ps
module tb;
reg clk=0,rst=0,beg=0,wr=0,result=0,snap=0,inv=0;always #7.5 clk=~clk;
reg [1:0] bank=3;reg [31:0] fid=123;reg [24:0] addr=21000000;reg [767:0] meta=0;
wire os,good;wire [851:0] data;
refined_frame_store #(.V4(1)) dut(clk,rst,beg,bank,fid,wr,addr,result,meta,snap,10'd15,os,data,good,32'd500,16'd7,1'b1,inv);
integer n;
task snapshot;begin @(negedge clk);snap=1;@(negedge clk);snap=0;repeat(3)@(negedge clk);end endtask
initial begin repeat(4)@(negedge clk);rst=1;@(negedge clk);beg=1;@(negedge clk);beg=0;
for(n=0;n<388799;n=n+1)begin wr=1;addr=21000000+n*8;@(negedge clk);end
wr=0;snapshot;if(data[802] || good)$fatal(1,"short1080 frame published");
wr=1;addr=24110392;@(negedge clk);wr=0;
meta[31:0]=fid;meta[255]=1;meta[247]=1;meta[244]=1;meta[242:235]=7;meta[415:413]=5;
meta[671:640]=500;meta[719:704]=7;meta[720]=1;meta[226]=1;meta[99:90]=55;
result=1;@(negedge clk);result=0;snapshot;
if(!data[802] || !good || data[801:800]!=3 || data[799:768]!=123 || data[767:0]!==meta)$fatal(1,"full388800/v5/upperY bank3 association");
wr=1;addr=24110400;@(negedge clk);wr=0;snapshot;if(data[802] || good)$fatal(1,"extra beat not rejected");
inv=1;@(negedge clk);inv=0;snapshot;if(data[802] || good)$fatal(1,"invalidation");
$display("FHD_STORE_PASS exact388800 writes,bank3 endpoint24110392,short/extra rejected,v5 Y1079 and timestamp preserved");$finish;
end endmodule'''

geometry=r'''`timescale 1ns/1ps
module tb;
reg clk=0,rst=0,commit=0,rot=0;always #5 clk=~clk;reg [2:0] z=0;
reg [639:0] meta=0;reg [10:0] x0=0,y0=96;
wire [10:0] w,h;wire [2:0] p,q,px,py;wire ready;wire [251:0] points;
refined_zoom_geometry view(z,rot,w,h,p,q,px,py);
refined_overlay_geometry map(clk,rst,commit,meta,x0,y0,z,rot,ready,points);
integer i,j,pp,qq,ww,hh,expected,observed,tipx,tipy;
initial begin repeat(3)@(negedge clk);rst=1;
for(i=0;i<5;i=i+1)for(j=0;j<2;j=j+1)begin
z=i;rot=j;#1;pp=(i==1 || i==3)?3:i==2?2:i==4?4:1;qq=i==1?2:1;
ww=(1919*qq)/pp+1;hh=(983*qq)/pp+1;
if(w!=ww || h!=hh || p!=pp || q!=qq)$fatal(1,"zoom extents");
for(tipx=0;tipx<1920;tipx=tipx+1)begin
expected=((j?1919-tipx:tipx)*qq)/pp;
observed=j?ww-1-(tipx*qq+px)/pp:(tipx*qq+px)/pp;
if(observed!=expected)$fatal(1,"reflected xDDA");end
for(tipy=0;tipy<984;tipy=tipy+1)begin
expected=((j?983-tipy:tipy)*qq)/pp;
observed=j?hh-1-(tipy*qq+py)/pp:(tipy*qq+py)/pp;
if(observed!=expected)$fatal(1,"reflected yDDA");end
end
z=0;rot=0;meta[226]=1;meta[99:90]=55;meta[89:79]=1919;
meta[110:100]=1800;meta[121:111]=1919;meta[227]=1;meta[131:122]=0;meta[228]=1;meta[141:132]=55;
commit=1;@(negedge clk);commit=0;repeat(22)@(negedge clk);
if(!ready || $signed(points[224+:14])!=1919 || $signed(points[238+:14])!=983)$fatal(1,"tip1079 truncation");
if($signed(points[28+:14])!=928 || $signed(points[42+:14])!=983)$fatal(1,"bbox1024/1079 truncation");
if($signed(points[168+:14])!=944 || $signed(points[182+:14])!=975 || $signed(points[196+:14])!=428 || $signed(points[210+:14])!=459)$fatal(1,"green32x32 center frame");
$display("FHD_GEOMETRY_PASS all5 zooms/all0/180DDA samples,tipY1079,32x32 center sample");$finish;
end endmodule'''

recovery=r'''`timescale 1ns/1ps
module tb;
reg pc=0,dc=0,rst=0,stream=1,commit=0,vs=0,unexpected=0;always #6.734006734 pc=~pc;always #7.5 dc=~dc;
wire busy,rd,svs,shs,sde,ok,fault;wire [24:0] addr;wire [23:0] rgb;wire [1:0] mask;wire [127:0] dd,pd;
refined_line_reader #(.JOB_TIMEOUT_CYCLES(64),.DRAIN_TIMEOUT_CYCLES(64)) dut(commit,1'b1,rst,dc,1'b1,1'b0,2'd3,32'd1,128'd0,
1'b1,1'b0,128'd0,busy,rd,addr,pc,vs,1'b1,1'b0,11'd0,11'd96,3'd0,svs,shs,sde,rgb,mask,ok,1'b0,stream,fault,dd,pd,32'd0,unexpected);
integer n;
initial begin repeat(10)@(negedge pc);rst=1;repeat(8)@(negedge pc);commit=1;@(negedge pc);commit=0;
n=0;while(!fault && n<2000)begin @(negedge dc);n=n+1;end
if(!fault || dd[75:72]!=6 || !busy)$fatal(1,"bounded unavailableDDR timeout/broken failover");
stream=0;vs=1;repeat(8)@(negedge pc);if(!fault || !svs || rgb!=0 || ok)$fatal(1,"stream recovery interrupted free-running sync/fault persistence");
vs=0;stream=1;repeat(12)@(negedge dc);unexpected=1;@(negedge dc);unexpected=0;repeat(4)@(negedge dc);
if(fault || dd[75:72]!=8)$fatal(1,"unexpected return recovery/fault toggle");
rst=0;repeat(4)@(negedge dc);if(fault || dd!=0)$fatal(1,"global reset diagnostic clearing");
$display("FHD_RECOVERY_PASS bounded3failures,coordinatedstreamreset retainsfault,synccontinues,unexpectedreturns trigger,newglobalresetclears");$finish;
end endmodule'''

display=r'''`timescale 1ns/1ps
module tb;
reg clk=0,rst=0,vs=0,snapshot=0;always #5 clk=~clk;
reg [851:0] data=0;wire commit,valid;wire [10:0] cx,cy,x0,y0;wire [767:0] meta;
stable_display #(.V4(1)) dut(.I_clk(clk),.I_rst_n(rst),.I_vs(vs),.I_de(1'b0),.I_snapshot(snapshot),.I_data(data),
.I_tracking(1'b1),.I_show(1'b1),.I_conflict(1'b0),.I_live(1'b1),.I_session(8'd7),.I_zoom(3'd4),.I_mode(2'd0),.I_pair(1'b0),
.O_commit(commit),.O_cx(cx),.O_cy(cy),.O_x0(x0),.O_y0(y0),.O_meta(meta),.O_detection_valid(valid),.I_rotate(1'b0));
task show;begin @(negedge clk);vs=1;@(negedge clk);vs=0;@(negedge clk);snapshot=1;@(negedge clk);snapshot=0;end endtask
initial begin repeat(4)@(negedge clk);rst=1;
data[802]=1;data[799:768]=1;data[31:0]=1;data[255]=1;data[247]=1;data[244]=1;data[242:235]=7;data[415:413]=5;
data[719:704]=7;data[835+:16]=7;data[851]=1;data[32]=1;data[89:79]=1900;data[226]=1;data[99:90]=55;
show;#1;if(!valid || cx!=1008 || cy!=588 || x0!=768 || y0!=465 || meta[226]!=1)$fatal(1,"v5 tipY1079 viewport %0d/%0d",cx,cy);
data[799:768]=2;data[31:0]=2;data[415:413]=4;show;#1;if(valid || meta!=0)$fatal(1,"v4 metadata admitted");
$display("FHD_DISPLAY_PASS v5 upperY1079,8pixel deadband48pixel step,viewport bounds,legacyv4 rejected");$finish;
end endmodule'''

video=r'''`timescale 1ns/1ps
module tb;
reg pc=0,dc=0,rst=0;always #6.734006734 pc=~pc;always #7.5 dc=~dc;
integer h=0,v=1084,frames=0,zarg=0,rarg=0,marg=0,parg=0,cycle=0;
wire vs=v>=1084 && v<1089,hs=h>=2008 && h<2052,de=v<1080 && h<1920;
reg commit=0,vsold=0;integer countdown=0;
always @(posedge pc)begin vsold<=vs;commit<=0;if(vs&&!vsold)countdown<=20;
else if(countdown>0)begin countdown<=countdown-1;if(countdown==1)commit<=1;end end
reg [10:0] x0=0,y0=96;reg [2:0] zoom=0;reg [1:0] mode=0;
wire busy,rd,svs,shs,sde,ok;wire [24:0] addr;wire [23:0] rgb;wire [1:0] mask;
reg valid=0,ready=1,wrbusy=0,wren=0;reg [127:0] data=0;reg [31:0] accepted=0;
wire fault;wire [127:0] dd,pd;
refined_line_reader dut(commit,1'b1,rst,dc,wrbusy,wren,2'd3,32'd123,128'd0,ready,valid,data,busy,rd,addr,
pc,vs,hs,de,x0,y0,zoom,svs,shs,sde,rgb,mask,ok,1'(rarg),1'b1,fault,dd,pd,accepted,1'b0);
wire pvs,phs,pde,ovs,ohs,ode;wire [23:0] prgb,orgb;wire [1:0] actual;
stable_preprocess process(pc,rst,mode,1'(parg),svs,shs,sde,rgb,mask,pvs,phs,pde,prgb,actual);
refined_osd osd(.I_clk(pc),.I_rst_n(rst),.I_vs(pvs),.I_hs(phs),.I_de(pde),.I_rgb(prgb),
.I_meta(768'd0),.I_x0(x0),.I_y0(y0),.I_zoom(zoom),.I_mode(actual),.I_state(3'd0),.I_tracking(1'b0),
.I_show(1'b0),.I_video_ok(ok),.I_pair(1'(parg)),.I_detection_valid(1'b0),.I_sample_valid(1'b0),
.I_rotate(1'(rarg)),.I_diag(2'd0),.I_image_id(32'd123),.I_geometry_commit(commit),
.I_latency_valid(1'b1),.I_latency_us(32'd4321),.I_frame_age(32'd2),.I_ddr_diag(dd),.I_pixel_diag(pd),.I_recovery(39'd0),.I_camera(18'd0),
.O_vs(ovs),.O_hs(ohs),.O_de(ode),.O_rgb(orgb));
function [23:0] pixel(input integer xx,yy);pixel={8'(xx),8'(yy),8'((xx>>8)*64+(yy>>8)*16+((xx^yy)&15))};endfunction
function integer pp(input integer z);pp=z==1||z==3?3:z==2?2:z==4?4:1;endfunction
function integer qq(input integer z);qq=z==1?2:1;endfunction
function integer sx(input integer xx);sx=x0+((rarg?1919-xx:xx)*qq(zarg))/pp(zarg);endfunction
function integer sy(input integer yy);sy=y0+((rarg?983-yy:yy)*qq(zarg))/pp(zarg);endfunction
function [127:0] word_at(input integer aa);integer j,bp,xx,yy,ch;reg [23:0] p;begin
for(j=0;j<16;j=j+1)begin bp=((aa-21000000)/8)*16+j;xx=(bp/3)%1920;yy=bp/5760;ch=bp%3;p=pixel(xx,yy);word_at[127-j*8-:8]=p>>(16-ch*8);end end endfunction
function [23:0] page(input [23:0] p,input integer m);integer g;begin g=(p[23:16]+2*p[15:8]+p[7:0]+2)/4;
case(m)0:page=p;1:page={8'(g/4),8'(g/4),8'(g/4)};2:page={8'(g),8'(g),8'(g)};default:page=0;endcase end endfunction
integer qa[0:4095],due[0:4095],head=0,tail=0,dc_cycle=0,wc=0,transactions=0,lastrow=-1,maxrow=0;
always @(negedge dc)begin dc_cycle=dc_cycle+1;ready=dc_cycle%19!=0 && dc_cycle%23!=0;valid=0;
if(head!=tail && due[head]<=dc_cycle)begin valid=1;data=word_at(qa[head]);head=(head+1)%4096;end end
always @(posedge dc)begin
if(!rst)begin wrbusy<=0;wren<=0;wc<=0;accepted<=0;end
else begin wren<=wrbusy && ready;if(wrbusy && ready && wc==239)wrbusy<=0;else if(!busy)wrbusy<=1;
if(wrbusy)begin if(ready)wc<=wc+1;end else wc<=0;
if(rd)begin
if(wrbusy||wren)$fatal(1,"DDRownership");if(addr<21000000 || addr>=24110400 || addr%8!=0)$fatal(1,"DDRbounds %0d",addr);
if((addr-21000000)/2880>maxrow)maxrow=(addr-21000000)/2880;
qa[tail]=addr;due[tail]=dc_cycle+37;tail=(tail+1)%4096;if(tail==head)$fatal(1,"queueoverflow");transactions=transactions+1;accepted<=accepted+1;end
end end
integer x=0,y=0,ox=0,oy=0,checked=0,outchecked=0,foot=0,highrows=0;reg so=0,oo=0;
reg [23:0] exp;reg [4:0] vd=0,hd=0,ded=0;
always @(posedge pc)if(!rst)begin vd<=0;hd<=0;ded<=0;end else begin vd<={vd[3:0],vs};hd<={hd[3:0],hs};ded<={ded[3:0],de};end
always @(negedge pc)if(rst)begin
if(cycle>20 && {ovs,ohs,ode}!=={vd[4],hd[4],ded[4]})$fatal(1,"syncpipeline");
if(svs&&!so)begin x=0;y=0;end so=svs;
if(sde)begin
if(y<984)begin exp=pixel(sx(x),sy(y));if(!ok || rgb!==exp || mask!==0)$fatal(1,"nativeRGB z%0d r%0d xy%0d/%0d src%0d/%0d got%h expected%h ok%b state%0d",zarg,rarg,x,y,sx(x),sy(y),rgb,exp,ok,dut.state);
checked=checked+1;if(sy(y)>=1024)highrows=highrows+1;end else if(rgb!==0)$fatal(1,"footerread");
if(x==1919)begin x=0;y=y+1;end else x=x+1;end
if(ovs&&!oo)begin ox=0;oy=0;end oo=ovs;
if(ode)begin
if(oy<984)begin exp=page(pixel(sx(ox),sy(oy)),marg);if(orgb!==exp)$fatal(1,"page mismatch m%0d xy%0d/%0d got%h exp%h",marg,ox,oy,orgb,exp);outchecked=outchecked+1;end
else begin foot=foot+1;if(oy==984 && orgb!==24'h101824)$fatal(1,"footerorigin");end
if(ox==1919)begin ox=0;oy=oy+1;end else ox=ox+1;end
if(h==2199)begin h=0;if(v==1124)begin v=0;frames=frames+1;end else v=v+1;end else h=h+1;
cycle=cycle+1;
if(frames==1 && v==1124 && h==2150)begin
if(checked!=1889280 || outchecked!=1889280 || foot!=184320 || highrows==0 || maxrow!=1079 || fault)$fatal(1,"coverage counts %0d %0d %0d high%0d maxrow%0d fault%b",checked,outchecked,foot,highrows,maxrow,fault);
if(!osd.footer_ready || osd.flatency!=4321 || osd.fage!=2)$fatal(1,"row985 footer latency snapshot");
$display("FHD_VIDEO_PASS pair%0d z%0d rot%0d page%0d RGB/masks1889280/footer184320 maxrow1079 incl1024+/independentDDRstalls/concurrent240wordwrites",parg,zarg,rarg,marg);$finish;end
end
initial begin
if($value$plusargs("ZOOM=%d",zarg))begin end if($value$plusargs("ROTATE=%d",rarg))begin end if($value$plusargs("MODE=%d",marg))begin end
if($value$plusargs("PAIR=%d",parg))begin end
zoom=zarg;mode=marg;x0=1920-((1919*qq(zarg))/pp(zarg)+1);y0=1080-((983*qq(zarg))/pp(zarg)+1);
repeat(12)@(negedge pc);rst=1;end
initial begin #100000000;$fatal(1,"videotimeout");end
endmodule'''

if a.suite in ('all','timing'):
    run('fhd_timing',timing,[rtl/'fhd_vtc.v'],compile_args=inc)
if a.suite in ('all','store'):
    run('fhd_store',store,[rtl/'refined_frame_store.v'],compile_args=inc)
if a.suite in ('all','geometry'):
    run('fhd_geometry',geometry,[rtl/'refined_overlay_geometry.v',rtl/'refined_zoom_geometry.v'],compile_args=inc)
    run('fhd_display',display,[rtl/'stable_display.v',rtl/'refined_zoom_geometry.v'],compile_args=inc)
if a.suite in ('all','recovery'):
    mods=[rtl/f'{n}.v' for n in ('refined_line_reader','stable_model_lane','stable_filter4','refined_zoom_geometry','refined_reset_bridge')]
    run('fhd_recovery',recovery,[*mods,R/'rtl/04_tracking/target_mailbox.v'],compile_args=inc)
if a.suite in ('all','ingress'):
    s=(R/'sim/tb_robust_ingress.sv').read_text(encoding='utf-8').replace('video_in dut','refined_video_in dut')
    s=s.replace('172800','388800').replace('target_frame_store full_store','target_frame_store #(.WORDS(388800)) full_store')
    modules=[rtl/'refined_video_in.v',rtl/'refined_reset_bridge.v',R/'rtl/04_tracking/target_frame_store.v',
        R/'user_source/ip_source/w128_d512_fifo/w128_d512_fifo.v',R/'user_source/ip_source/w128_d512_fifo/soft_fifo_al_4057d6b76aa6.v']
    for cp,dp in ([(8,7),(5,11),(11,5)] if a.full else [(8,7)]):
        run(f'fhd_ingress_{cp}_{dp}',s,modules,top='tb_robust_ingress',compile_args=[*inc,f'-Ptb_robust_ingress.CP={cp}',f'-Ptb_robust_ingress.DP={dp}'])
if a.suite in ('all','video'):
    video_run=run
    if a.video_backend=='native':
        from refined_native_testlib import run_native as video_run
    modules=[rtl/f'{n}.v' for n in ('refined_line_reader','stable_model_lane','stable_filter4','stable_preprocess','refined_osd',
        'refined_footer_program_rom','refined_english_font_rom','refined_english_text_rom','refined_overlay_geometry','refined_zoom_geometry','refined_reset_bridge','refined_logo_rom')]
    modules += [R/'rtl/04_tracking/target_mailbox.v']
    pairs=(0,1) if a.full else (0,)
    if a.pair is not None:pairs=(a.pair,)
    jobs=[(pair,z,r,m) for pair in pairs for z in range(5) for r in (0,1) for m in range(4)] if a.full else [(pair,z,r,(z+r)%4) for pair in pairs for z in range(5) for r in (0,1)]
    if a.zoom is not None:jobs=[j for j in jobs if j[1]==a.zoom]
    if a.rotate is not None:jobs=[j for j in jobs if j[2]==a.rotate]
    if a.mode is not None:jobs=list(dict.fromkeys((pair,z,r,a.mode) for pair,z,r,m in jobs))
    if a.color:
        # G=0 and R>=128 guarantee nonzero chroma and full saturation. An
        # independently specified valid hue interval[0,360) must accept A.
        video=video.replace('32\'d123,128\'d0,ready',"32'd123,128'h0000000000000000802d000000000000,ready")
        video=video.replace("pixel={8'(xx),8'(yy),8'((xx>>8)*64+(yy>>8)*16+((xx^yy)&15))}",
            "pixel={8'(128+((xx^yy^(xx>>7)^(yy>>8))&127)),8'd0,8'((xx>>3)+yy*31)}")
        video=video.replace('mask!==0','mask!==1').replace("1:page={8'(g/4),8'(g/4),8'(g/4)}", "1:page=parg?24'hffff40:24'hff6060").replace('default:page=0',"default:page=24'hffffff")
    def execute(job):
        pair,z,r,m=job
        video_run(f'fhd_{"color_" if a.color else ""}video_p{pair}_{z}_{r}_{m}',video,modules,args=[f'+PAIR={pair}',f'+ZOOM={z}',f'+ROTATE={r}',f'+MODE={m}'],compile_args=inc)
    with ThreadPoolExecutor(max_workers=a.workers) as pool:list(pool.map(execute,jobs))
print('FHD_TRANSPORT_SUITE_PASS',a.suite,flush=True)
