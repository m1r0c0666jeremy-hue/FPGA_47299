// 40x23 coarse density grid; one capture RAM port, one frozen-frame scan port.
// Both selected colours share each 22-bit word. No same-bank read/write sharing.
`default_nettype none
module regions_grid #(parameter WIDTH=1280,HEIGHT=720,TILE_MIN=4,SUPPORT_MIN=16,PADDING=64)(
 input wire clk,rst_n,begin_frame,capture_bank,valid,input wire [10:0] x,input wire [9:0] y,
 input wire [3:0] hit_a,hit_b,
 input wire start,work_bank,output reg busy,done,failed,
 output reg [1:0] ready,bad,
 output reg [167:0] boxes,output reg [3:0] boxes_valid,output reg [1:0] more
);
 localparam GW=(WIDTH+31)/32,GH=(HEIGHT+31)/32,CELLS=GW*GH;
 (* ram_style="block" *) reg [21:0] counts[0:2047];
 reg [21:0] cap_q,work_q;
 reg [10:0] segment_a,segment_b;reg [21:0] next_base;
 reg [9:0] prefetch;reg capturing;
 wire [2:0] pa={2'd0,hit_a[0]}+{2'd0,hit_a[1]}+{2'd0,hit_a[2]}+{2'd0,hit_a[3]};
 wire [2:0] pb={2'd0,hit_b[0]}+{2'd0,hit_b[1]}+{2'd0,hit_b[2]}+{2'd0,hit_b[3]};
 wire [9:0] here=(y[9:5]<<5)+(y[9:5]<<3)+x[10:5];
 wire cap_write=valid && capturing && x[4:0]==28;
 wire [10:0] cap_addr={capture_bank,(cap_write?here:prefetch)};
 always @(posedge clk)begin
   cap_q<=counts[cap_addr];
   if(cap_write)counts[cap_addr]<={segment_b+{8'd0,pb},segment_a+{8'd0,pa}};
 end
 reg [9:0] baddr;reg bank;
 reg clear_write;reg [10:0] work_addr;
 always @(posedge clk)begin
   work_q<=counts[work_addr];
   if(clear_write)counts[work_addr]<=0;
 end
 (* ram_style="block" *) reg [3:0] cells[0:1023];
 reg [9:0] cell_addr;reg [3:0] cell_q,cell_data;reg cell_we;
 (* ram_style="block" *) reg [10:0] queue[0:1023];
 reg [9:0] qrptr,qwptr,qcount,qwrite_addr;reg [10:0] queue_q,queue_data;reg queue_we;
 always @(posedge clk)begin queue_q<=queue[qrptr];if(queue_we)queue[qwrite_addr]<=queue_data;end
 localparam BOOT_CLEAR=0,IDLE=1,MASK_BEGIN=2,MASK_SCAN=3,MASK_NEXT=4,SEARCH_REQ=5,SEARCH_WAIT=6,SEARCH_GET=7,
 POP=8,POP_GET=9,VALUE_WAIT=10,VALUE_GET=11,NEIGHBOR=12,NEIGHBOR_WAIT=13,NEIGHBOR_GET=14,
 COMPONENT=15,SEARCH_NEXT=16,COLOR_NEXT=17,CLEAR=18,FINISH=19;
 reg [4:0] state;reg boot_bank;reg [9:0] clear_index,index;
 reg [5:0] scan_x,cx,nx_hold;reg [4:0] scan_y,cy,ny_hold;
 reg [3:0] ni;reg sample_pending,center_pending;
 reg [13:0] sum_a,sum_b;reg [10:0] own_a,own_b;
 reg color;reg [19:0] component_count;reg [5:0] minx,maxx;reg [4:0] miny,maxy;
 reg [62:0] best[0:3];reg [1:0] number;
 reg [16:0] elapsed;
 integer dx,dy,xx,yy,j;reg in_bounds;reg [9:0] neighbor_index;
 reg [13:0] total_a,total_b;
 reg [41:0] component_box;reg [62:0] component_item;
 reg [10:0] bx0,bx1;reg [9:0] by0,by1;
 wire [9:0] cell_read_addr=state==SEARCH_REQ?index:state==NEIGHBOR?neighbor_index:cell_addr;
 always @(posedge clk)begin cell_q<=cells[cell_read_addr];if(cell_we)cells[cell_addr]<=cell_data;end
 function [9:0] tile_address;
   input [5:0] tx;input [4:0] ty;reg [9:0] row;
   begin row={5'd0,ty};tile_address=(row<<5)+(row<<3)+tx;end
 endfunction
 function [9:0] next_pointer;input [9:0] a;begin next_pointer=a==CELLS-1?0:a+1'b1;end endfunction
 function better;input [62:0] a,b;begin better=a[62] && (!b[62] || a[61:42]>b[61:42] ||
    (a[61:42]==b[61:42] && (a[31:22]<b[31:22] || (a[31:22]==b[31:22] && a[10:0]<b[10:0]))));end endfunction
 always @*begin
   dx=0;dy=0;
   if(state==MASK_SCAN)begin
     case(ni)
      0:begin dx=-1;dy=-1;end 1:dy=-1;2:begin dx=1;dy=-1;end
      3:dx=-1;4:begin dx=0;dy=0;end 5:dx=1;
      6:begin dx=-1;dy=1;end 7:dy=1;8:begin dx=1;dy=1;end
     endcase
     xx=scan_x+dx;yy=scan_y+dy;
   end else begin
     case(ni)
      0:begin dx=-1;dy=-1;end 1:dy=-1;2:begin dx=1;dy=-1;end
      3:dx=-1;4:dx=1;5:begin dx=-1;dy=1;end 6:dy=1;7:begin dx=1;dy=1;end
     endcase
     xx=cx+dx;yy=cy+dy;
   end
   in_bounds=xx>=0 && xx<GW && yy>=0 && yy<GH && (state!=MASK_SCAN || ni<9);
   neighbor_index=in_bounds?tile_address(xx[5:0],yy[4:0]):0;
   work_addr={bank,baddr};clear_write=0;
   if(state==BOOT_CLEAR)begin work_addr={boot_bank,clear_index};clear_write=1;end
   else if(state==CLEAR)begin work_addr={bank,clear_index};clear_write=1;end
   else if(state==MASK_SCAN)work_addr={bank,neighbor_index};
   total_a=sum_a+(sample_pending?{3'd0,work_q[10:0]}:14'd0);
   total_b=sum_b+(sample_pending?{3'd0,work_q[21:11]}:14'd0);
   bx0=({5'd0,minx}<<5)>PADDING?({5'd0,minx}<<5)-PADDING:0;
   bx1=(({5'd0,maxx}+1)<<5)-1+PADDING;
   if(bx1>=WIDTH)bx1=WIDTH-1;
   by0=({5'd0,miny}<<5)>PADDING?({5'd0,miny}<<5)-PADDING:0;
   by1=(({5'd0,maxy}+1)<<5)-1+PADDING;
   if(by1>=HEIGHT)by1=HEIGHT-1;
   component_box={by1,by0,bx1,bx0};component_item={1'b1,component_count,component_box};
 end
 always @(posedge clk or negedge rst_n)begin
   if(!rst_n)begin
     capturing<=0;prefetch<=0;segment_a<=0;segment_b<=0;next_base<=0;
   end else begin
     if(begin_frame)begin capturing<=ready[capture_bank];prefetch<=0;segment_a<=0;segment_b<=0;next_base<=0;end
     if(valid && (begin_frame?ready[capture_bank]:capturing))begin
       if(x[4:0]==0)begin
         segment_a<=(begin_frame?11'd0:next_base[10:0])+pa;
         segment_b<=(begin_frame?11'd0:next_base[21:11])+pb;
       end else begin segment_a<=segment_a+pa;segment_b<=segment_b+pb;end
       if(x[4:0]==20)begin
         if(x[10:5]==GW-1)prefetch<=y==HEIGHT-1?0:tile_address(0,(y+10'd1)>>5);
         else prefetch<=tile_address(x[10:5]+1'b1,y[9:5]);
       end
       if(x[4:0]==28)next_base<=cap_q;
     end
   end
 end
 always @(posedge clk or negedge rst_n)begin
   if(!rst_n)begin
     state<=BOOT_CLEAR;boot_bank<=0;clear_index<=0;busy<=1;done<=0;failed<=0;ready<=0;bad<=0;
     boxes<=0;boxes_valid<=0;more<=0;bank<=0;baddr<=0;index<=0;scan_x<=0;scan_y<=0;cx<=0;cy<=0;
     nx_hold<=0;ny_hold<=0;ni<=0;sample_pending<=0;center_pending<=0;sum_a<=0;sum_b<=0;own_a<=0;own_b<=0;
     color<=0;component_count<=0;minx<=0;maxx<=0;miny<=0;maxy<=0;number<=0;elapsed<=0;
     cell_addr<=0;cell_data<=0;cell_we<=0;queue_we<=0;queue_data<=0;qwrite_addr<=0;qrptr<=0;qwptr<=0;qcount<=0;
     for(j=0;j<4;j=j+1)best[j]<=0;
   end else begin
     done<=0;cell_we<=0;queue_we<=0;
     if(busy && state!=BOOT_CLEAR)elapsed<=elapsed+1'b1;
     case(state)
       BOOT_CLEAR:if(clear_index==CELLS-1)begin
         ready[boot_bank]<=1;clear_index<=0;
         if(boot_bank)begin busy<=0;state<=IDLE;end else boot_bank<=1;
       end else clear_index<=clear_index+1'b1;
       IDLE:if(start)begin
         bank<=work_bank;busy<=1;failed<=bad[work_bank];elapsed<=0;index<=0;scan_x<=0;scan_y<=0;
         boxes_valid<=0;more<=0;for(j=0;j<4;j=j+1)best[j]<=0;
         if(bad[work_bank])begin clear_index<=0;state<=CLEAR;end else state<=MASK_BEGIN;
       end
       MASK_BEGIN:begin ni<=0;sum_a<=0;sum_b<=0;own_a<=0;own_b<=0;sample_pending<=0;center_pending<=0;state<=MASK_SCAN;end
       MASK_SCAN:begin
         sample_pending<=in_bounds;center_pending<=ni==4;sum_a<=total_a;sum_b<=total_b;
         if(center_pending)begin own_a<=work_q[10:0];own_b<=work_q[21:11];end
         if(ni==9)begin
           cell_addr<=index;cell_data<={2'b0,(own_b>=TILE_MIN && total_b>=SUPPORT_MIN),(own_a>=TILE_MIN && total_a>=SUPPORT_MIN)};
           cell_we<=1;state<=MASK_NEXT;
         end else ni<=ni+1'b1;
       end
       MASK_NEXT:if(index==CELLS-1)begin index<=0;scan_x<=0;scan_y<=0;color<=0;number<=0;qrptr<=0;qwptr<=0;qcount<=0;state<=SEARCH_REQ;end
         else begin index<=index+1'b1;if(scan_x==GW-1)begin scan_x<=0;scan_y<=scan_y+1'b1;end else scan_x<=scan_x+1'b1;state<=MASK_BEGIN;end
       SEARCH_REQ:begin cell_addr<=index;state<=SEARCH_GET;end
       SEARCH_WAIT:state<=SEARCH_GET;
       SEARCH_GET:if(cell_q[color] && !cell_q[2+color])begin
         cell_data<=cell_q|(4'b0100<<color);cell_we<=1;
         queue_data<={scan_y,scan_x};qwrite_addr<=qwptr;queue_we<=1;qwptr<=next_pointer(qwptr);qcount<=1;
         component_count<=0;minx<=scan_x;maxx<=scan_x;miny<=scan_y;maxy<=scan_y;state<=POP;
       end else state<=SEARCH_NEXT;
       POP:if(qcount==0)state<=COMPONENT;
         else if(!(queue_we && qwrite_addr==qrptr))state<=POP_GET;
       POP_GET:begin
         cx<=queue_q[5:0];cy<=queue_q[10:6];baddr<=tile_address(queue_q[5:0],queue_q[10:6]);
         qrptr<=next_pointer(qrptr);qcount<=qcount-1'b1;state<=VALUE_WAIT;
       end
       VALUE_WAIT:state<=VALUE_GET;
       VALUE_GET:begin
         component_count<=component_count+(color?work_q[21:11]:work_q[10:0]);
         if(cx<minx)minx<=cx;if(cx>maxx)maxx<=cx;if(cy<miny)miny<=cy;if(cy>maxy)maxy<=cy;
         ni<=0;state<=NEIGHBOR;
       end
       NEIGHBOR:if(in_bounds)begin cell_addr<=neighbor_index;nx_hold<=xx[5:0];ny_hold<=yy[4:0];state<=NEIGHBOR_GET;end
         else if(ni==7)state<=POP;else ni<=ni+1'b1;
       NEIGHBOR_WAIT:state<=NEIGHBOR_GET;
       NEIGHBOR_GET:begin
         if(cell_q[color] && !cell_q[2+color])begin
           if(qcount==CELLS)begin failed<=1;clear_index<=0;state<=CLEAR;end
           else begin
             cell_data<=cell_q|(4'b0100<<color);cell_we<=1;
             queue_data<={ny_hold,nx_hold};qwrite_addr<=qwptr;queue_we<=1;qwptr<=next_pointer(qwptr);qcount<=qcount+1'b1;
           end
         end
         if(cell_q[color] && !cell_q[2+color] && qcount==CELLS)begin
           failed<=1;clear_index<=0;state<=CLEAR;
         end else if(ni==7)state<=POP;else begin ni<=ni+1'b1;state<=NEIGHBOR;end
       end
       COMPONENT:begin
         if(number!=3)number<=number+1'b1;
         if(better(component_item,best[{color,1'b0}]))begin best[{color,1'b1}]<=best[{color,1'b0}];best[{color,1'b0}]<=component_item;end
         else if(better(component_item,best[{color,1'b1}]))best[{color,1'b1}]<=component_item;
         state<=SEARCH_NEXT;
       end
       SEARCH_NEXT:if(index==CELLS-1)state<=COLOR_NEXT;
         else begin index<=index+1'b1;if(scan_x==GW-1)begin scan_x<=0;scan_y<=scan_y+1'b1;end else scan_x<=scan_x+1'b1;state<=SEARCH_REQ;end
       COLOR_NEXT:begin
         more[color]<=number==3;
         if(!color)begin color<=1;number<=0;index<=0;scan_x<=0;scan_y<=0;qrptr<=0;qwptr<=0;qcount<=0;state<=SEARCH_REQ;end
         else begin clear_index<=0;state<=CLEAR;end
       end
       CLEAR:if(clear_index==CELLS-1)begin ready[bank]<=1;state<=FINISH;end else clear_index<=clear_index+1'b1;
       FINISH:begin
         for(j=0;j<4;j=j+1)begin boxes[42*j+:42]<=best[j][41:0];boxes_valid[j]<=best[j][62] && !failed;end
         if(failed)more<=0;
         busy<=0;done<=1;state<=IDLE;
       end
     endcase
     if(busy && state!=BOOT_CLEAR && state!=CLEAR && state!=FINISH && elapsed>=65536-CELLS-2)begin failed<=1;clear_index<=0;state<=CLEAR;end
     if(begin_frame)begin
       bad[capture_bank]<=!ready[capture_bank];
       if(ready[capture_bank])ready[capture_bank]<=0;
     end
   end
 end
endmodule
`default_nettype wire
