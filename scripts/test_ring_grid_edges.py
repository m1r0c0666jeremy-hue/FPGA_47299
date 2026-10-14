"""Fringe ownership, weak-chain isolation, shape preservation and quality order."""
from test_ring_calibration import R,O,run
from test_ring_regions import stats,blobs
def rect(x,y,w,h):return {(x+i,y+j) for j in range(h) for i in range(w)}
def support(p):return {(x,y) for x,y in p if sum((x+dx,y+dy) in p for dy in (-1,0,1) for dx in (-1,0,1) if dx or dy)>=2}
pairs=lambda x,y:{(x+i,y+j) for j in (0,4,8,12) for i in (0,1,4,5,8,9,12,13)}
cases=[('weak_chain',rect(160,160,3,16)|rect(224,160,3,16)|{(x,164) for x in (176,177,192,193,208,209)},2),
       ('shared_fringe',rect(160,160,3,16)|rect(192,160,3,16)|{(176,164),(177,164)},2),
       ('rejected_first_owner',rect(160,160,3,15)|rect(192,160,3,16)|{(176,164),(177,164)},1),
       ('four_edges',rect(0,0,3,16)|rect(1277,704,3,16)|rect(0,717,16,3)|rect(1264,0,16,3),4),
       ('thin_shapes',rect(400,240,16,16)-rect(403,243,10,10)|rect(720,240,3,64),2),
       ('weak_print_and_ring',pairs(400,240)|pairs(416,240)|rect(720,240,3,16),2),
       ('quality_top4',rect(640,352,3,16)|set().union(*(pairs(x,y)|pairs(x+16,y) for x,y in [(336,208),(512,208),(752,208),(336,448),(752,448)])),4)]
for strict in (0,4):
    for name,points,expected in cases:
        a=stats(points,support(points));vec=O/f'{name}_{strict}.hex'
        vec.write_text('\n'.join(f'{(n|sx<<9|sy<<20|q<<62):020x}' for n,sx,sy,q in a),encoding='ascii')
        if strict and name=='weak_print_and_ring':expected=1
        if strict and name=='quality_top4':expected=1
        extra=''
        if name=='weak_chain':extra='for(j=0;j<2;j=j+1)if(cand[j*128+42+:20]!=50)$fatal(1,"weak chain expanded or lost fringe");'
        if name=='shared_fringe':extra='if(cand[61:42]+cand[189:170]!=98)$fatal(1,"shared fringe duplicate");'
        if name=='rejected_first_owner':extra='if(cand[61:42]!=48)$fatal(1,"first ownership was silently reassigned");'
        if name in ('quality_top4','weak_print_and_ring'):
            extra+='if(cand[89:83]!=100 || cand[61:42]!=48)$fatal(1,"strong thin target lost top rank");'
        src=f'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;wire busy,done,failed;wire [1023:0] cand;wire [17:0] cycles;
reg [79:0] words[0:3599];integer j,n=0,c;
stable_grid #(.STRICT_SUPPORT({strict})) dut(clk,rst,1'b0,1'b0,11'd0,10'd0,8'd0,8'd0,start,1'b0,1'b0,84'd0,1'b0,busy,done,failed,cand,cycles);
initial begin $readmemh("{vec.as_posix()}",words);repeat(3)@(negedge clk);rst=1;
@(negedge clk);for(j=0;j<3600;j=j+1)dut.stats0[j]=words[j];start=1;@(negedge clk);start=0;
while(!done && n<213000)begin @(negedge clk);n=n+1;end
if(!done || failed || cycles>=212000)$fatal(1,"deadline");c=0;for(j=0;j<4;j=j+1)if(cand[j*128+120])c=c+1;
if(c!={expected})$fatal(1,"{name} strict{strict} count %0d",c);{extra}
$display("RING_GRID_EDGES_PASS {name} strict={strict} kept=%0d cycles=%0d",c,cycles);$finish;end endmodule'''
        run(f'grid_{name}_strict{strict}',src,[R/'rtl/color_regions/stable_grid.v',R/'rtl/color_regions/regions_divide.v'])
