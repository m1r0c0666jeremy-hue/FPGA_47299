// 16x16 tiles, exact pixel moments, bounded full-frame eight-neighbour traversal.
// Statistics have independent capture/worker RAM ports. No per-fragment labels.
`default_nettype none
module stable_grid #(parameter STRICT_SUPPORT=0)(input wire clk,rst_n,
 input wire valid,bank,input wire [10:0] x,input wire [9:0] y,
 input wire [7:0] ha,hb,input wire start,work_bank,
 input wire tracking,input wire [83:0] previous_boxes,input wire previous_valid,
 output reg busy,done,failed,output wire [1023:0] candidates,
 output reg [17:0] cycles);
 (* ram_style="bram" *) reg [79:0] stats0[0:4095],stats1[0:4095];
 reg [79:0] sq0,sq1;
 wire [11:0] tile_addr=(y[9:4]<<6)+(y[9:4]<<4)+x[10:4];
 wire [12:0] cap_addr={bank,tile_addr};reg [79:0] cache;
 reg cv,cb;reg [12:0] ca,last_ca;reg [7:0] ah,bh;reg [3:0] lx,ly;
 reg wb;wire [79:0] cap_q=cb?sq1:sq0;
 reg [8:0] ac,bc,asup,bsup;reg [10:0] ax,bx,ay,by;integer p;
 reg [79:0] base,next_stat;
 always @*begin
 ac=0;bc=0;asup=0;bsup=0;ax=0;bx=0;ay=0;by=0;
 for(p=0;p<4;p=p+1)begin
 if(ah[p])begin ac=ac+1'b1;ax=ax+lx+p;ay=ay+ly;end
 if(bh[p])begin bc=bc+1'b1;bx=bx+lx+p;by=by+ly;end
 if(ah[p+4] && ah[p])asup=asup+1'b1;if(bh[p+4] && bh[p])bsup=bsup+1'b1;end
 base=ly==0 && lx==0?80'd0:(ca==last_ca?cache:cap_q);
 next_stat={base[79:71]+bsup,base[70:62]+asup,base[61:51]+by,base[50:40]+bx,base[39:31]+bc,
            base[30:20]+ay,base[19:9]+ax,base[8:0]+ac};
 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin cv<=0;cb<=0;ca<=0;last_ca<=8191;cache<=0;ah<=0;bh<=0;lx<=0;ly<=0;end
 else begin cv<=valid;cb<=bank;ca<=cap_addr;ah<=ha;bh<=hb;lx<=x[3:0];ly<=y[3:0];
 if(cv)begin cache<=next_stat;last_ca<=ca;end end end
 // TD's documented directive is "bram", not the ignored "block" value.
 (* ram_style="bram" *) reg [5:0] flags[0:4095];
 (* ram_style="bram" *) reg [13:0] queue[0:4095];
 // Two row histories in a single true dual-port RAM. Each physical port has
 // one explicit address; a mux around two separately read arrays can cause
 // four inferred read ports and distributed-RAM expansion in TD.
 (* ram_style="bram" *) reg [17:0] rows[0:255];
 wire [79:0] wq=wb?sq1:sq0;reg [5:0] fq;reg [13:0] qq;reg [17:0] uq,mq;
 reg [12:0] wa;reg [11:0] fa;reg [12:0] qa;
 reg fw,qw,rw;reg [5:0] fd;reg [13:0] qd;reg [17:0] rd;
 reg [6:0] rowaddr;reg rowbank;
 (* syn_preserve=1 *) reg [11:0] queue_read_addr;
 always @(posedge clk)begin queue_read_addr<=qa[11:0];qq<=queue[queue_read_addr];end
 wire [7:0] row_a={rowbank,rowaddr},row_b={!rowbank,rowaddr};
 always @(posedge clk)begin uq<=rows[row_a];if(rw)rows[row_a]<=rd;end
 always @(posedge clk)mq<=rows[row_b];
 always @(posedge clk)begin
 sq0<=stats0[valid && !bank?tile_addr:wa[11:0]];
 sq1<=stats1[valid && bank?tile_addr:wa[11:0]];
 if(cv)begin if(ca[12])stats1[ca[11:0]]<=next_stat;else stats0[ca[11:0]]<=next_stat;end
 fq<=flags[fa];
 if(fw)flags[fa]<=fd;if(qw)queue[qa]<=qd;
 end
 localparam IDLE=0,PADDR=1,PWAIT=2,PREAD=3,PFEED=4,SCAN=5,SCGET=6,
 POP=7,WADDR=8,WWAIT=9,ADD=10,NSET=11,NGET=12,RETIRE=13,
 NEXTCOLOR=14,DSET=15,DWAIT=16,FINISH=17,POPWAIT=18;
 reg [4:0] state;reg color;reg [6:0] pc;reg [5:0] py;reg [11:0] scan;
 wire [6:0] scan_x=scan%80;wire [5:0] scan_y=scan/80;
 reg [12:0] head,tail;reg [6:0] tx;reg [5:0] ty;reg [3:0] direction;
 reg [17:0] u0,u1,m0,m1,l0,l1;wire [17:0] lower=(pc>0 && pc<81 && py>0 && py<46)?{wq[39:31],wq[8:0]}:18'd0;
 wire [11:0] support_a={3'd0,uq[8:0]}+{3'd0,u1[8:0]}+{3'd0,u0[8:0]}+
 {3'd0,mq[8:0]}+{3'd0,m1[8:0]}+{3'd0,m0[8:0]}+
 {3'd0,lower[8:0]}+{3'd0,l1[8:0]}+{3'd0,l0[8:0]};
 wire [11:0] support_b={3'd0,uq[17:9]}+{3'd0,u1[17:9]}+{3'd0,u0[17:9]}+
 {3'd0,mq[17:9]}+{3'd0,m1[17:9]}+{3'd0,m0[17:9]}+
 {3'd0,lower[17:9]}+{3'd0,l1[17:9]}+{3'd0,l0[17:9]};
 reg signed [8:0] nx;reg signed [7:0] ny;reg neighbor_ok;
 reg [19:0] count,strong_count;reg edge_only;reg [30:0] sx,sy;reg [6:0] xmin,xmax;reg [5:0] ymin,ymax;
 reg [2:0] qualified[0:1],reject_stage[0:1];reg [1:0] saw_core;
 reg [127:0] best[0:7];reg [61:0] moments[0:7];reg [127:0] item;
 // The consumer starts only after done and copies before the next start.
 // Publish the completed candidate bank directly; do not duplicate 1024 FFs.
 reg published;wire [1023:0] published_best;genvar slot_index;
 generate for(slot_index=0;slot_index<8;slot_index=slot_index+1)begin:publish_slot
 if(slot_index==0)assign published_best[127:0]={(!saw_core[0]?3'd3:reject_stage[0]),qualified[0]>4,(qualified[0]>4?3'd4:qualified[0]),best[0][120:0]};
 else if(slot_index==4)assign published_best[639:512]={(!saw_core[1]?3'd3:reject_stage[1]),qualified[1]>4,(qualified[1]>4?3'd4:qualified[1]),best[4][120:0]};
 else assign published_best[slot_index*128+:128]=best[slot_index];
 end endgenerate
 assign candidates=published && !failed?published_best:1024'd0;
 reg [61:0] item_moment;reg [19:0] supports[0:7];reg [1:0] quality_tier;reg [27:0] score;reg nearby,central;
 reg [2:0] insert_index,divide_index;reg found_insert;reg [1:0] axis;
 wire [30:0] tcx=({24'd0,tx}<<4)*(color?wq[39:31]:wq[8:0])+(color?wq[50:40]:wq[19:9]);
 wire [30:0] tcy=({25'd0,ty}<<4)*(color?wq[39:31]:wq[8:0])+(color?wq[61:51]:wq[30:20]);
 wire [41:0] oldbox=color?previous_boxes[83:42]:previous_boxes[41:0];
 wire [10:0] bx0={xmin,4'd0},bx1={xmax,4'hf};wire [9:0] by0={ymin,4'd0},by1={ymax,4'hf};
 integer z,offset;reg [12:0] capped;
 always @*begin
 nx=$signed({2'd0,tx});ny=$signed({2'd0,ty});
 case(direction)
 0:begin nx=nx-1;ny=ny-1;end 1:ny=ny-1;2:begin nx=nx+1;ny=ny-1;end
 3:nx=nx-1;4:nx=nx+1;5:begin nx=nx-1;ny=ny+1;end
 6:ny=ny+1;7:begin nx=nx+1;ny=ny+1;end endcase
 neighbor_ok=nx>=0 && nx<80 && ny>=0 && ny<45;
 wa={wb,12'd0};fa=0;qa=0;fw=0;qw=0;rw=0;fd=0;qd=0;rd=lower;rowaddr=pc;rowbank=py[0];
 if(state==PADDR || state==PWAIT || state==PREAD || state==PFEED)begin
 if(pc>0 && pc<81 && py>0 && py<46)wa={wb,12'd0}+((py-1)*80)+(pc-1);
 if(state==PFEED)begin rw=1;if(pc>=2 && py>=2)begin
 fa=((py-2)*80)+(pc-2);fw=1;fd={2'b00,(m1[17:9]>=4 && support_b>=16),(m1[8:0]>=4 && support_a>=16),
 (m1[17:9]>0 && support_b>=16),(m1[8:0]>0 && support_a>=16)};end end
 end
 if(state==SCAN || state==SCGET)begin fa=scan;
 if(state==SCGET && fq[color+2] && !fq[color+4])begin
 fw=1;fd=fq|(6'b010000<<color);qa=0;qw=1;qd={1'b0,scan_y,scan_x};end end
 if(state==POP || state==POPWAIT)qa=head;
 if(state==WADDR || state==WWAIT || state==ADD)wa={wb,12'd0}+ty*80+tx;
 if(state==NSET || state==NGET)begin
 fa=neighbor_ok?(ny*80+nx):0;
 if(state==NGET && neighbor_ok && fq[color] && !fq[color+4] && tail<3600)begin
 fw=1;fd=fq|(6'b010000<<color);qa=tail;qw=1;qd={!fq[color+2],ny[5:0],nx[6:0]};end end
 nearby=previous_valid && bx0<=oldbox[21:11]+32 && bx1+32>=oldbox[10:0] &&
 by0<=oldbox[41:32]+32 && by1+32>=oldbox[31:22];
 central=bx0+bx1>=640 && bx0+bx1<1920 && by0+by1>=360 && by0+by1<1080;
 capped=count>4096?4096:count[12:0];
 quality_tier=({2'd0,strong_count}<<2)>=({2'd0,count}+({2'd0,count}<<1))?3:
 ({2'd0,strong_count}<<1)>={2'd0,count}?2:({2'd0,strong_count}<<2)>={2'd0,count}?1:0;
 score={11'd0,(tracking && nearby),(!tracking && central),quality_tier,capped};
 item=0;item[120]=count>=48 && (STRICT_SUPPORT==0 || strong_count>=4) && bx1-bx0<960 && by1-by0<540;
 item[119:92]=score;item[91:90]=quality_tier;item[61:42]=count;item[41:0]={by1,by0,bx1,bx0};item_moment={sy,sx};
 offset=color?4:0;insert_index=0;found_insert=0;
 for(z=0;z<4;z=z+1)if(!found_insert && (!best[offset+z][120] || score>best[offset+z][119:92]))begin
 insert_index=z;found_insert=1;end
 end
 reg ds;reg [31:0] numerator,denominator;wire dbusy,ddone;wire [31:0] quotient;
 regions_divide divider(clk,rst_n,ds,numerator,denominator,dbusy,ddone,quotient);
 integer i;
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
 state<=IDLE;busy<=0;done<=0;failed<=0;published<=0;cycles<=0;wb<=0;color<=0;pc<=0;py<=0;scan<=0;
 head<=0;tail<=0;tx<=0;ty<=0;direction<=0;u0<=0;u1<=0;m0<=0;m1<=0;l0<=0;l1<=0;
 count<=0;sx<=0;sy<=0;xmin<=0;xmax<=0;ymin<=0;ymax<=0;divide_index<=0;axis<=0;ds<=0;numerator<=0;denominator<=0;
 for(i=0;i<8;i=i+1)begin best[i]<=0;moments[i]<=0;supports[i]<=0;end
 strong_count<=0;edge_only<=0;saw_core<=0;
 for(i=0;i<2;i=i+1)begin qualified[i]<=0;reject_stage[i]<=0;end end
 else begin
 done<=0;ds<=0;if(busy)cycles<=cycles+1'b1;
 if(busy && cycles>=212000)begin busy<=0;done<=1;failed<=1;published<=0;state<=IDLE;end
 else case(state)
 IDLE:if(start)begin
 busy<=1;failed<=0;published<=0;cycles<=0;wb<=work_bank;color<=0;pc<=0;py<=0;u0<=0;u1<=0;m0<=0;m1<=0;l0<=0;l1<=0;
 saw_core<=0;for(i=0;i<2;i=i+1)begin qualified[i]<=0;reject_stage[i]<=0;end
 for(i=0;i<8;i=i+1)best[i]<=0;state<=PADDR;end
 PADDR:state<=PWAIT;PWAIT:state<=PREAD;PREAD:state<=PFEED;
 PFEED:begin
 u0<=u1;u1<=uq;m0<=m1;m1<=mq;l0<=l1;l1<=lower;
 if(pc==81)begin pc<=0;u0<=0;u1<=0;m0<=0;m1<=0;l0<=0;l1<=0;
 if(py==46)begin scan<=0;state<=SCAN;end else begin py<=py+1'b1;state<=PADDR;end end
 else begin pc<=pc+1'b1;state<=PADDR;end end
 SCAN:state<=SCGET;
 SCGET:begin
 if(fq[color+2])saw_core[color]<=1;
 if(fq[color+2] && !fq[color+4])begin
 head<=0;tail<=1;count<=0;strong_count<=0;sx<=0;sy<=0;xmin<=79;xmax<=0;ymin<=44;ymax<=0;state<=POP;end
 else if(scan==3599)state<=NEXTCOLOR;else begin scan<=scan+1'b1;state<=SCAN;end end
 POP:state<=POPWAIT;
 POPWAIT:state<=WADDR;
 WADDR:begin edge_only<=qq[13];tx<=qq[6:0];ty<=qq[12:7];head<=head+1'b1;state<=WWAIT;end
 WWAIT:state<=ADD;
 ADD:begin strong_count<=strong_count+(color?wq[79:71]:wq[70:62]);count<=count+(color?wq[39:31]:wq[8:0]);sx<=sx+tcx;sy<=sy+tcy;
 if(tx<xmin)xmin<=tx;if(tx>xmax)xmax<=tx;if(ty<ymin)ymin<=ty;if(ty>ymax)ymax<=ty;
 direction<=0;state<=edge_only?(head<tail?POP:RETIRE):NSET;end
 NSET:state<=NGET;
 NGET:begin
 if(neighbor_ok && fq[color] && !fq[color+4])begin
 if(tail>=3600)begin failed<=1;state<=FINISH;end else tail<=tail+1'b1;end
 if(direction==7)begin if(head<tail || (neighbor_ok && fq[color] && !fq[color+4]))state<=POP;else state<=RETIRE;end
 else begin direction<=direction+1'b1;state<=NSET;end end
 RETIRE:begin
 if(item[120])begin if(qualified[color]<5)qualified[color]<=qualified[color]+1'b1;end
 else reject_stage[color]<=count<48?4:5;
 if(item[120] && found_insert)for(i=0;i<4;i=i+1)begin
 if(i==insert_index)begin best[offset+i]<=item;moments[offset+i]<=item_moment;supports[offset+i]<=strong_count;end
 else if(i>insert_index)begin best[offset+i]<=best[offset+i-1];moments[offset+i]<=moments[offset+i-1];supports[offset+i]<=supports[offset+i-1];end end
 if(scan==3599)state<=NEXTCOLOR;else begin scan<=scan+1'b1;state<=SCAN;end end
 NEXTCOLOR:if(!color)begin color<=1;scan<=0;state<=SCAN;end
 else begin divide_index<=0;axis<=0;state<=DSET;end
 DSET:begin
 numerator<=axis==2?(({12'd0,supports[divide_index]}<<6)+({12'd0,supports[divide_index]}<<5)+({12'd0,supports[divide_index]}<<2)):
 axis==1?{1'b0,moments[divide_index][61:31]}:{1'b0,moments[divide_index][30:0]};
 denominator<={12'd0,best[divide_index][61:42]};ds<=1;state<=DWAIT;end
 DWAIT:if(ddone)begin
 if(axis==2)best[divide_index][89:83]<=quotient[6:0];
 else if(axis==1)best[divide_index][82:73]<=quotient[9:0];else best[divide_index][72:62]<=quotient[10:0];
 if(axis!=2)begin axis<=axis+1'b1;state<=DSET;end
 else if(divide_index==7)state<=FINISH;
 else begin divide_index<=divide_index+1'b1;axis<=0;state<=DSET;end end
 FINISH:begin published<=!failed;
 busy<=0;done<=1;state<=IDLE;end
 endcase end end
endmodule
`default_nettype wire
