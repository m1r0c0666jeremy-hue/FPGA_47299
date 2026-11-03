module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,commit=0;reg [671:0] vertices;reg [15:0] counts;reg [3:0] closed;
reg [1:0] mode;reg [10:0] x0,x=0;reg [9:0] y0,y=0;reg [2:0] zoom;reg rotate;
reg [3:0] state,completed;reg [2:0] target,actual;reg de=0;
wire [3:0] mask;wire [23:0] color,label_color;wire label_on,ready,underrun;wire [7:0] glyph;wire [2:0] gx;wire [3:0] gy;
reg [732:0] contexts[0:14-1];reg [5119:0] expected[0:624-1];integer c,yy,h,dbg;reg [3:0] want;reg [127:0] ew;
wire [1:0] split_region=c[1:0];
wire [167:0] split_draft=vertices>>(split_region*168);
wire [671:0] split_mask={{504{1'b0}},{168{1'b1}}}<<(split_region*168);
wire [671:0] split_saved=vertices & ~split_mask;
stage1_render #(.SPLIT_DRAFT(1)) dut(clk,rst,commit,split_saved,counts,closed,mode,x0,y0,zoom,rotate,state,completed,target,actual,
x,y,de,mask,color,label_on,glyph,gx,gy,label_color,ready,underrun,split_draft,{1'b0,split_region},1'b1);
initial begin $readmemh("D:/aaa_FPGA/region-sequence-stage1/build/stage1_render_vectors/contexts.hex",contexts);repeat(3)@(negedge clk);rst=1;
for(c=0;c<14;c=c+1)begin
@(negedge clk);
{vertices,counts,closed,mode,x0,y0,zoom,rotate,state,completed,target,actual}=contexts[c];
$readmemh($sformatf("D:/aaa_FPGA/region-sequence-stage1/build/stage1_render_vectors/expected_%0d.hex",c),expected);de=0;x=0;y=0;commit=1;@(negedge clk);commit=0;
repeat(10000)@(negedge clk);if(!ready || underrun)$fatal(1,"initial row deadline state%0d",dut.state);
vertices=0;counts=0;
for(yy=0;yy<624;yy=yy+1)begin
for(h=0;h<1650;h=h+1)begin
@(negedge clk);de=h<1280;x=h<1280?h:0;y=yy;
@(posedge clk);#1;
if(de)begin want=expected[yy][h*4+:4];
if(mask!==want || underrun)begin
for(dbg=8;dbg<16;dbg=dbg+1)begin ew={dut.edge_mem[dbg*8+7],dut.edge_mem[dbg*8+6],dut.edge_mem[dbg*8+5],dut.edge_mem[dbg*8+4],dut.edge_mem[dbg*8+3],dut.edge_mem[dbg*8+2],dut.edge_mem[dbg*8+1],dut.edge_mem[dbg*8]};
$display("EDGE%0d cur%d rem%0d q%d r%0d den%0d ys%0d..%0d end%d flags%b",dbg,$signed(ew[15:0]),ew[29:16],$signed(ew[45:30]),ew[59:46],ew[73:60],ew[83:74],ew[93:84],$signed(ew[109:94]),ew[114:110]);end
$fatal(1,"render c%0d z%0d r%b xy%0d/%0d mask%h/%h state%0d row%0d ready%b bank%b tag%0d underrun%b",c,zoom,rotate,h,yy,mask,want,dut.state,dut.row,ready,dut.bank_valid,dut.bank_row[yy%8],underrun);end
end end end
de=0;$display("STAGE1_RENDER_CASE_PASS case%0d zoom%0d rotate%b rows%0d",c,zoom,rotate,624);
end
$display("STAGE1_RENDER_PASS cases=%0d pixels=%0d",14,14*624*1280);$finish;end
endmodule