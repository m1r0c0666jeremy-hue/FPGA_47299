`timescale 1ns/1ps
// Real AWB/packing/writer/capture/CDC/store/view/reader/pages/OSD modules.
// DDR physical pins are replaced by an ordered memory response model. Every
// written byte is checked against the independently generated source image.
module tb_stable_live #(parameter PAIR_MODE=0);
reg cc=0,dc=0,pc=0,rst=0;always #8.334 cc=~cc;always #7.5 dc=~dc;always #6.667 pc=~pc;
reg rawsof=0,rawv=0;reg [95:0] raw=0;wire asf,av,al;wire [95:0] ar;
stable_awb awb(cc,rst,1'b0,rawsof,rawv,raw,12'd1024,12'd1024,al,asf,av,ar);
wire psf,pv;wire [127:0] packed_rgb;
stable_packer packer(cc,rst,asf,av,ar,psf,pv,packed_rgb);
reg [127:0] models;wire cv,crready;wire [31:0] cfid,dropped;wire [639:0] cm,dm;wire dr;
wire overflow,beginf,wr,wrbusy;wire [1:0] bank,rp;wire [31:0] write_id;wire [24:0] wa;wire [127:0] wd;
wire rbusy,re;wire [24:0] ra;reg ready=1,rdvalid=0;reg [127:0] rddata=0;
video_in writer(rst,cc,psf,cfid,beginf,bank,write_id,overflow,pv,packed_rgb,1'b0,dc,1'b0,rbusy,wrbusy,rp,wr,wa,wd,ready);
reg [15:0] revision=0;
stable_capture capture(cc,rst,asf,av,overflow,ar,1'(PAIR_MODE),1'b1,8'd1,models,revision,24'h400400,8'd0,1'b0,1'b0,crready,cfid,cv,cm,dropped);
target_mailbox #(.WIDTH(640)) results(cc,rst,cv,cm,crready,dc,rst,dr,dm);
integer h=0,v=725,frame=0;reg primed=0;
wire vs=primed && v>=725 && v<730,hs=primed && h>=1390 && h<1430,de=primed && v<720 && h<1280;
reg vs_old=0;wire request=vs && !vs_old;wire reqready,request_d;wire [9:0] command_d;
always @(posedge pc)vs_old<=vs;
target_mailbox #(.WIDTH(10)) requests(pc,rst,request && reqready,10'(3+512*PAIR_MODE),reqready,dc,rst,request_d,command_d);
wire ss,sready,sg,ps;wire [674:0] sd,pd;
stable_frame_store store(dc,rst,beginf,bank,write_id,wr,wa,dr,dm,request_d && sready,command_d,ss,sd,sg);
target_mailbox #(.WIDTH(675)) snapshots(dc,rst,ss,sd,sready,pc,rst,ps,pd);
wire commit;wire [1:0] selected,zoom,mode;wire [31:0] selected_id;wire [10:0] cx,x0;wire [9:0] cy,y0;
wire [639:0] active;wire shown,pair,detection,sample,video_ok;wire [2:0] state;
reg [1:0] requested_zoom=1,requested_mode=0;
stable_display view(pc,rst,vs,de,ps,pd,1'b1,1'b1,1'b0,video_ok,8'd1,requested_zoom,requested_mode,1'(PAIR_MODE),commit,selected,selected_id,cx,x0,cy,y0,zoom,mode,active,shown,pair,detection,sample,state);
wire rvs,rhs,rde;wire [23:0] rgb;wire [1:0] mask;
stable_line_reader reader(commit,sg,rst,dc,wrbusy,wr,selected,selected_id,active[543:416],ready,rdvalid,rddata,rbusy,re,ra,pc,vs,hs,de,x0,y0,zoom,rvs,rhs,rde,rgb,mask,video_ok);
wire pvs,phs,pde,ovs,ohs,ode;wire [23:0] prgb,orgb;wire [1:0] actual_mode;
stable_preprocess preprocess(pc,rst,mode,pair,rvs,rhs,rde,rgb,mask,pvs,phs,pde,prgb,actual_mode);
stable_osd osd(pc,rst,pvs,phs,pde,prgb,active,x0,y0,zoom,actual_mode,state,1'b1,shown,video_ok,pair,detection,sample,ovs,ohs,ode,orgb);
function [23:0] pixel(input integer f,x,y);
begin
pixel=24'h303030;
if(x>=600+4*f && x<632+4*f && y>=342+2*f && y<366+2*f)pixel=PAIR_MODE?24'hc8c820:24'hc82020;
if(f!=7 && x>=480+4*f && x<512+4*f && y>=342+2*f && y<366+2*f)pixel=PAIR_MODE?24'hb420c8:24'h2020c8;
end endfunction
function [127:0] word(input integer f,n);
integer j,b,x,y,c;reg [23:0] p;begin
for(j=0;j<16;j=j+1)begin b=n*16+j;x=(b/3)%1280;y=b/3840;c=b%3;p=pixel(f,x,y);word[127-j*8-:8]=p>>(16-c*8);end
end endfunction
reg [31:0] bank_ids[0:3];integer beat=0,write_frame=0,write_bank=0,written=0;
integer qaddr[0:4095],qframe[0:4095],due[0:4095],head=0,tail=0,dc_cycle=0,rbank,rword;
always @(posedge dc)if(rst)begin
if(beginf)begin bank_ids[bank]=write_id;write_frame=write_id;write_bank=bank;beat=0;end
if(wr)begin
if(wa!==write_bank*7000000+beat*8 || wd!==word(write_frame,beat))$fatal(1,"real DDR write corrupt f%0d beat%0d",write_frame,beat);
beat=beat+1;written=written+1;
end
if(re)begin
if(wrbusy || wr)$fatal(1,"DDR arbitration collision");rbank=ra/7000000;rword=(ra%7000000)/8;
qaddr[tail]=rword;qframe[tail]=bank_ids[rbank];due[tail]=dc_cycle+37;tail=(tail+1)%4096;if(head==tail)$fatal(1,"response queue overflow");end
end
always @(negedge dc)begin
dc_cycle=dc_cycle+1;ready=dc_cycle%19!=0 && dc_cycle%23!=0;rdvalid=0;
if(head!=tail && due[head]<=dc_cycle)begin rdvalid=1;rddata=word(qframe[head],qaddr[head]);head=(head+1)%4096;end
end
integer f,x,y,i,checked=0,ox=0,oy=0,transactions=0,valid_tips=0;reg changed_version_seen=0;reg old_rvs=0;reg [10:0] last_cx=640;reg [9:0] last_cy=360;
reg [1:0] last_zoom=1;reg [3:0] seen_modes=0;reg [2:0] seen_zooms=0;
reg [23:0] expected_pixel;reg [1:0] expected_mask;
always @(negedge pc)if(rst && primed)begin
if(rvs && !old_rvs)begin ox=0;oy=0;end old_rvs=rvs;
if(rde)begin
if(oy<624)begin
if(!video_ok)$fatal(1,"live video underrun frame%0d xy%0d/%0d",frame,ox,oy);
if(rgb!==pixel(selected_id,x0+(ox>>zoom),y0+(oy>>zoom)))$fatal(1,"image/metadata/window mismatch frame%0d sourceid%0d xy%0d/%0d got%h",frame,selected_id,ox,oy,rgb);
expected_pixel=pixel(selected_id,x0+(ox>>zoom),y0+(oy>>zoom));expected_mask=expected_pixel==(PAIR_MODE?24'hc8c820:24'hc82020)?1:expected_pixel==(PAIR_MODE?24'hb420c8:24'h2020c8)?2:0;
if(mask!==expected_mask)$fatal(1,"live supported source mask/frame model mismatch");
seen_modes[mode]=1;seen_zooms[zoom]=1;
checked=checked+1;end
if(ox==1279)begin ox=0;oy=oy+1;end else ox=ox+1;end
if(commit)begin
if(active[31:0]!==selected_id || active[415:413]!=3 || active[543:416]!==models_for(selected_id) || active[559:544]!=(selected_id>=8?1:0))$fatal(1,"live snapshot provenance");
if(active[603:595]!=(2+PAIR_MODE) || (active[32] && active[594:593]!=2))$fatal(1,"selected tool identity/status CDC mismatch");
if(selected_id>=8)changed_version_seen=1;
if(zoom==last_zoom)begin
if(!active[32] && (cx!=last_cx || cy!=last_cy))$fatal(1,"loss moved window");
if($signed({1'b0,cx})-$signed({1'b0,last_cx})>24 || $signed({1'b0,last_cx})-$signed({1'b0,cx})>24)$fatal(1,"live max step");end
transactions=transactions+1;if(active[32])valid_tips=valid_tips+1;last_cx=cx;last_cy=cy;last_zoom=zoom;
end
if(h==1649)begin h=0;if(v==749)begin v=0;frame=frame+1;requested_mode=frame%4;requested_zoom=(frame+1)%3;end else v=v+1;end else h=h+1;
if(frame==5 && v==749 && h==1600)begin
if(checked!=5*1280*624 || transactions<5 || valid_tips<3 || dropped!=0 || !changed_version_seen || seen_modes!=15 || seen_zooms!=7)$fatal(1,"live coverage %0d %0d %0d %0d",checked,transactions,valid_tips,cx);
$display("STABLE_LIVE_PASS pair%0d real capture->DDR->640/675 CDC->moving viewport->source masks->OSD: four pages, three zooms, parameter switch, %0d pixels, %0d snapshots, %0d tip snapshots, %0d written words",PAIR_MODE,checked,transactions,valid_tips,written);$finish;end
end
always @(posedge cc)if(cv && cm[31:0]==3)primed<=1;
function [63:0] model(input integer lo,hi);begin model=(64'h8000000000000000)|(64'(lo)<<54)|(64'(hi)<<45)|(64'd32<<37)|(64'd16<<29)|(64'd1<<27);end endfunction
function [127:0] models_for(input integer f);begin models_for=PAIR_MODE?(f>=8?{model(285,302),model(52,69)}:{model(255,330),model(45,75)}):(f>=8?{model(232,249),model(352,9)}:{model(195,255),model(345,30)});end endfunction
initial begin
models=models_for(0);for(i=0;i<4;i=i+1)bank_ids[i]=0;
repeat(12)@(negedge cc);rst=1;repeat(12)@(negedge cc);
for(f=1;f<=12;f=f+1)begin
models=models_for(f);revision=f>=8?1:0;
for(y=0;y<720;y=y+1)for(x=0;x<1280;x=x+4)begin
@(negedge cc);rawsof=x==0 && y==0;rawv=1;for(i=0;i<4;i=i+1)raw[95-i*24-:24]=pixel(f,x+i,y);end
@(negedge cc);rawv=0;rawsof=0;repeat(260000)@(negedge cc);
end
@(negedge cc);rawsof=1;rawv=0;@(negedge cc);rawsof=0;
end
initial begin #200000000;$fatal(1,"live timeout");end
endmodule
