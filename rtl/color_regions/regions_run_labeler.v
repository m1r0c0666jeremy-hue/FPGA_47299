// Bounded streaming 8-connected run labelling, one colour, all ROIs combined.
// Labels 0..127 are ALL usable. An 8-bit allocation count prevents wrap at 128.
// Stats layout: clip148, members147:146, sumq145:124, ymax123:114,
// ymin113:104, xmax103:93, xmin92:82, sy81:51, sx50:20, count19:0.
`default_nettype none
module regions_run_labeler #(parameter HEIGHT=720,LINE_LIMIT=288)(
 input wire clk,rst_n,begin_frame,input wire begin_bank,
 input wire [1:0] in_count,input wire [230:0] in_records,
 input wire in_eol,in_overflow,input wire [5:0] in_total,
 input wire [1:0] in_line_bank,input wire in_frame_bank,input wire [9:0] in_y,
 output reg [1:0] bad,output reg closed,output reg closed_bank,
 output wire [7:0] labels0,labels1,output wire [9:0] edges0,edges1,
 input wire [7:0] post_stat_addr,input wire post_stat_write,input wire [148:0] post_stat_data,
 output reg [148:0] post_stat_q,input wire [9:0] post_edge_addr,output reg [13:0] post_edge_q,
 output reg [8:0] max_line_cycles
);
 (* ram_style="block" *) reg [76:0] runs[0:127];
 (* ram_style="block" *) reg [148:0] stats[0:255];
 (* ram_style="block" *) reg [13:0] edges[0:1023];
 reg [6:0] line_labels[0:95];
 // FIFO: {frame bank, line bank, record index[5:0], run[76:0]}.
 reg [85:0] queue[0:7];reg [2:0] wp,rp;reg [3:0] used;
 reg [3:0] outstanding[0:2];reg [5:0] emitted;
 wire [85:0] head0=queue[rp];
 // Two direct write lanes sustain two events/clock. Only a third EOL event
 // enters the eight-entry spill FIFO; consume it on the next free RAM port.
 // This is one FIFO write and one FIFO read, allowing distributed RAM inference.
 wire pop=used!=0 && in_count<2;
 wire push=in_count==3 && (used<8 || pop);
 wire [5:0] second_index=emitted+1'b1,third_index=emitted+2'd2;
 wire [85:0] direct0={in_frame_bank,in_line_bank,emitted,in_records[0+:77]};
 wire [85:0] direct1={in_frame_bank,in_line_bank,second_index,in_records[77+:77]};
 wire write_a=in_count!=0 || pop;
 wire write_b=in_count>=2 || (in_count==1 && pop);
 wire [85:0] event_a=in_count!=0?direct0:head0;
 wire [85:0] event_b=in_count>=2?direct1:head0;
 wire q0_ok=event_a[82:77]<32,q1_ok=event_b[82:77]<32;
 wire [6:0] qa0={event_a[84:83],event_a[81:77]},qa1={event_b[84:83],event_b[81:77]};
 wire run_ports_free=!write_a && !write_b;
 reg [76:0] run_p,run_c;
 reg [7:0] allocated[0:1];reg [9:0] edge_count[0:1];
 assign labels0=allocated[0];assign labels1=allocated[1];
 assign edges0=edge_count[0];assign edges1=edge_count[1];
 localparam IDLE=0,READ=1,USE=2,STAT_READ=3,STAT_WRITE=4,FINISH=5;
 reg [2:0] state;
 reg pending;reg [1:0] pend_line,cur_line,prev_line;
 reg pend_bank,cur_bank;reg [9:0] pend_y,cur_y;
 reg [5:0] pend_count,ncur,nprev,pi,ci,previous_count;
 reg previous_bank;reg [9:0] previous_y;
 reg [8:0] line_cycles;
 reg assigned;reg [6:0] current_label,commit_label;
 reg commit_new;reg [76:0] commit_run;reg [148:0] stat_q;
 wire [6:0] prev_label=line_labels[{prev_line,pi[4:0]}];
 wire pvalid=pi<nprev;
 wire overlap=pvalid && ({1'b0,run_p[21:11]}+12'd1>={1'b0,run_c[10:0]}) &&
                                ({1'b0,run_p[10:0]}<={1'b0,run_c[21:11]}+12'd1);
 wire previous_left=pvalid && ({1'b0,run_p[21:11]}+12'd1<{1'b0,run_c[10:0]});
 wire advance_previous=previous_left || (overlap && {1'b0,run_p[21:11]}<{1'b0,run_c[21:11]}+12'd1);
 wire finish_current=!advance_previous;
 wire [6:0] chosen=assigned?current_label:overlap?prev_label:allocated[cur_bank][6:0];
 wire new_label=!assigned && !overlap;
 wire make_edge=state==USE && overlap && assigned && current_label!=prev_label && !bad[cur_bank] && edge_count[cur_bank]<512;
 wire [7:0] sa={cur_bank,commit_label};
 reg [148:0] merged;
 wire [11:0] run_length={1'b0,commit_run[21:11]}-{1'b0,commit_run[10:0]}+12'd1;
 always @* begin
   merged=commit_new?149'd0:stat_q;
   merged[19:0]=(commit_new?20'd0:stat_q[19:0])+run_length;
   merged[50:20]=(commit_new?31'd0:stat_q[50:20])+commit_run[41:22];
   merged[81:51]=(commit_new?31'd0:stat_q[81:51])+commit_run[61:42];
   merged[92:82]=commit_new || commit_run[10:0]<stat_q[92:82]?commit_run[10:0]:stat_q[92:82];
   merged[103:93]=commit_new || commit_run[21:11]>stat_q[103:93]?commit_run[21:11]:stat_q[103:93];
   merged[113:104]=commit_new?cur_y:stat_q[113:104];
   merged[123:114]=cur_y;
   merged[145:124]=(commit_new?22'd0:stat_q[145:124])+commit_run[73:62];
   merged[147:146]=(commit_new?2'd0:stat_q[147:146])|commit_run[76:75];
   merged[148]=(commit_new?1'b0:stat_q[148])|commit_run[74];
 end
 // Canonical true-dual-port RAM: each port has ONE shared read/write address.
 // A conditional write and an unrelated read expression inferred 9856 flip-flops
 // in TD. The scanner only consumes outputs after a pop-free READ cycle.
 wire [6:0] run_addr_a=write_a?qa0:{prev_line,pi[4:0]};
 wire [6:0] run_addr_b=write_b?qa1:{cur_line,ci[4:0]};
 always @(posedge clk)begin
   run_p<=runs[run_addr_a];
   if(write_a && q0_ok)runs[run_addr_a]<=event_a[76:0];
 end
 always @(posedge clk)begin
   run_c<=runs[run_addr_b];
   if(write_b && q1_ok)runs[run_addr_b]<=event_b[76:0];
 end
 // Per-colour component RAM: scanner port A, frame-finalizer port B.
 always @(posedge clk)begin
   stat_q<=stats[sa];
   if(state==STAT_WRITE && !bad[cur_bank])stats[sa]<=merged;
   post_stat_q<=stats[post_stat_addr];
   if(post_stat_write)stats[post_stat_addr]<=post_stat_data;
 end
 always @(posedge clk)begin
   if(make_edge)edges[{cur_bank,edge_count[cur_bank][8:0]}]<={current_label,prev_label};
   post_edge_q<=edges[post_edge_addr];
 end
 always @(posedge clk)if(push)queue[wp]<={in_frame_bank,in_line_bank,third_index,in_records[154+:77]};
 integer i;reg [4:0] pend_n;
 always @(posedge clk or negedge rst_n)begin
   if(!rst_n)begin
     wp<=0;rp<=0;used<=0;emitted<=0;bad<=0;closed<=0;closed_bank<=0;
     allocated[0]<=0;allocated[1]<=0;edge_count[0]<=0;edge_count[1]<=0;
     state<=IDLE;pending<=0;pend_line<=0;pend_bank<=0;pend_y<=0;pend_count<=0;
     cur_line<=0;prev_line<=0;cur_bank<=0;cur_y<=0;ncur<=0;nprev<=0;pi<=0;ci<=0;
     previous_count<=0;previous_bank<=0;previous_y<=0;line_cycles<=0;max_line_cycles<=0;
     assigned<=0;current_label<=0;commit_label<=0;commit_new<=0;commit_run<=0;
     for(i=0;i<3;i=i+1)outstanding[i]<=0;
   end else begin
     closed<=0;
     if(begin_frame)begin bad[begin_bank]<=0;allocated[begin_bank]<=0;edge_count[begin_bank]<=0;end
     if(in_count==3 && !push)bad[in_frame_bank]<=1;
     wp<=wp+push;rp<=rp+pop;used<=used-pop+push;
     for(i=0;i<3;i=i+1)begin
       pend_n=outstanding[i]+(in_line_bank==i && push?1:0);
       if(pop && head0[84:83]==i)pend_n=pend_n-1'b1;
       outstanding[i]<=pend_n;
     end
     if(in_eol)emitted<=0;
     else if(in_count!=0)emitted<=emitted+in_count>32?33:emitted+in_count;
     if(begin_frame)emitted<=0;
     if(in_overflow)bad[in_frame_bank]<=1;
     if(write_a && !q0_ok)bad[event_a[85]]<=1;
     if(write_b && !q1_ok)bad[event_b[85]]<=1;
     if(pending || state!=IDLE)line_cycles<=line_cycles+1'b1;
     if(in_eol)begin
       if(pending || state!=IDLE)begin bad[cur_bank]<=1;bad[in_frame_bank]<=1;state<=IDLE;end
       pending<=1;pend_line<=in_line_bank;pend_bank<=in_frame_bank;pend_y<=in_y;pend_count<=in_total;line_cycles<=0;
     end
     case(state)
       IDLE:if(pending && outstanding[pend_line]==0 && !(in_count!=0 && in_line_bank==pend_line))begin
         pending<=0;cur_line<=pend_line;prev_line<=pend_line==0?2:pend_line-1'b1;
         cur_bank<=pend_bank;cur_y<=pend_y;ncur<=pend_count;ci<=0;pi<=0;assigned<=0;
         nprev<=(pend_y!=0 && previous_bank==pend_bank && previous_y+1==pend_y)?previous_count:0;
         state<=pend_count==0?FINISH:READ;
       end
       READ:if(run_ports_free)state<=USE;
       USE:begin
         if(overlap)begin
           if(!assigned)begin current_label<=prev_label;assigned<=1;end
           else if(current_label!=prev_label)begin
             if(edge_count[cur_bank]==512)bad[cur_bank]<=1;
             else edge_count[cur_bank]<=edge_count[cur_bank]+1'b1;
           end
         end
         if(advance_previous)begin pi<=pi+1'b1;state<=READ;end
         else begin
           commit_label<=chosen;commit_new<=new_label;commit_run<=run_c;
           line_labels[{cur_line,ci[4:0]}]<=chosen;
           if(new_label)begin
             if(allocated[cur_bank]==128)bad[cur_bank]<=1;
             else allocated[cur_bank]<=allocated[cur_bank]+1'b1;
           end
           state<=STAT_READ;
         end
       end
       STAT_READ:state<=STAT_WRITE;
       STAT_WRITE:begin assigned<=0;ci<=ci+1'b1;state<=ci+1==ncur?FINISH:READ;end
       FINISH:begin
         previous_count<=ncur;previous_y<=cur_y;previous_bank<=cur_bank;
         if(line_cycles>max_line_cycles)max_line_cycles<=line_cycles;
         if(cur_y==HEIGHT-1)begin closed<=1;closed_bank<=cur_bank;end
         state<=IDLE;
       end
     endcase
     // An early EOL must override the old scanner state's next-state assignment.
     if(in_eol && (pending || state!=IDLE))begin
       state<=IDLE;previous_count<=0;pending<=1;
     end
     if((pending || state!=IDLE) && line_cycles>=LINE_LIMIT)begin
       bad[pending?pend_bank:cur_bank]<=1;
       if((pending?pend_y:cur_y)==HEIGHT-1)begin closed<=1;closed_bank<=pending?pend_bank:cur_bank;end
       pending<=0;state<=IDLE;previous_count<=0;
     end
   end
 end
endmodule
`default_nettype wire
