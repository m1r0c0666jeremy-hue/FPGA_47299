"""Cycle comparison including interrupted RAM transfers and resets; private only."""
from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=O/'stage1_render.v';renamed=O/'stage1_render_resetfree_compare.v'
with renamed.open('x',encoding='utf8') as f:f.write(source.read_text().replace('module stage1_render #','module stage1_render_resetfree_compare #',1))
bench=r"""module tb;
reg clk=0;always #5 clk=~clk;
reg rst=0,commit=0,de=0,rotate=0,visible=0;reg[671:0] vertices=0;reg[167:0] draft=0;
reg[15:0] counts=0;reg[3:0] closed=0,run_state=0,completed=0;reg[1:0] mode=0;
reg[10:0] x=0,x0=0;reg[9:0] y=0,y0=0;reg[2:0] zoom=0,target=0,actual=0,region=0;
wire[3:0] mask0,mask1;wire[23:0] color0,color1,lc0,lc1;wire lo0,lo1,ready0,ready1,u0,u1;wire[7:0] gl0,gl1;wire[2:0] gx0,gx1;wire[3:0] gy0,gy1;
stage1_render #(.SPLIT_DRAFT(1)) base(clk,rst,commit,vertices,counts,closed,mode,x0,y0,zoom,rotate,run_state,completed,target,actual,x,y,de,mask0,color0,lo0,gl0,gx0,gy0,lc0,ready0,u0,draft,region,visible);
stage1_render_resetfree_compare #(.SPLIT_DRAFT(1)) cand(clk,rst,commit,vertices,counts,closed,mode,x0,y0,zoom,rotate,run_state,completed,target,actual,x,y,de,mask1,color1,lo1,gl1,gx1,gy1,lc1,ready1,u1,draft,region,visible);
reg[31:0] rng=32'hf00d2345;integer cycle=0,checks=0,writes=0,commits=0,resets=0,i,j;
reg[10:0] vx;reg[9:0] vy;
always @(posedge clk) if(rst)begin
 if({base.state,base.field,base.edge_id,base.row,base.word_index,base.bank_valid}!=={cand.state,cand.field,cand.edge_id,cand.row,cand.word_index,cand.bank_valid})$fatal(1,"control mismatch cycle %0d",cycle);
 if(base.state==9)begin
 if(base.work[base.field*16+:16]!==cand.work[cand.field*16+:16])$fatal(1,"edge RAM write differs cycle %0d edge %0d field %0d",cycle,base.edge_id,base.field);writes=writes+1;end
end
initial begin
 repeat(3)@(negedge clk);rst=1;
 for(cycle=0;cycle<300000;cycle=cycle+1)begin
  @(negedge clk);
  if({mask0,color0,lo0,gl0,gx0,gy0,lc0,ready0,u0}!=={mask1,color1,lo1,gl1,gx1,gy1,lc1,ready1,u1})$fatal(1,"external output differs cycle %0d",cycle);
  checks=checks+1;rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
  rst=(cycle%19001!=18998 && cycle%19001!=18999);if(!rst)resets=resets+1;
  commit=(cycle%20000==0 || cycle%20000==13 || cycle%20000==1000 || cycle%20000==3300 || !rst);if(commit)begin
   commits=commits+1;zoom=(cycle/20000)%5;rotate=rng[0];mode=rng[3:2];closed=rng[7:4];run_state=rng[11:8]%8;completed=rng[15:12];target=rng[18:16]%4;actual=rng[21:19]%5;
   x0=rng[10:0]%1280;y0=rng[20:11]%720;region=rng[24:22]%4;visible=rng[25];
   for(i=0;i<4;i=i+1)begin counts[i*4+:4]=3+(rng>>(i*3))%6;
    for(j=0;j<8;j=j+1)begin vx=(rng+37*i+89*j)%1280;vy=((rng>>8)+31*i+67*j)%720;vertices[(i*8+j)*21+:21]={vy,vx};end end
   draft=vertices[167:0];
  end else begin vertices[20:0]=rng[20:0];draft[20:0]=rng[23:3];end
  de=cycle%20000>=12000;if(!de)begin x=0;y=624;end else begin if(x==1599)begin x=0;y=y>=623?0:y+1'b1;end else x=x+1'b1;end
 end
 if(writes<1000 || commits<40 || resets<20)$fatal(1,"coverage short writes%0d commits%0d resets%0d",writes,commits,resets);
 $display("PRIVATE_SNAPSHOT_RESETFREE_EQUIVALENCE_PASS checks=%0d writes=%0d commits=%0d reset_cycles=%0d",checks,writes,commits,resets);$finish;
end
endmodule"""
inputs=[R/'rtl/color_regions/stage1_arith.v',R/'rtl/color_regions/stage1_render.v',renamed]
formal=json.loads((R/'build/stage1_place_20261023_200045/inputs.json').read_text());assert all(sha(R/n)==h for n,h in formal.items())
out=run('private_snapshot_resetfree_equivalence',bench,inputs,timeout=300)
record=R/'reports/refined/regression'/(out.name+'.json');assert 'PRIVATE_SNAPSHOT_RESETFREE_EQUIVALENCE_PASS' in record.with_suffix('.log').read_text()
result={'scope':'PRIVATE NOT ADOPTED','record':record.relative_to(R).as_posix(),'record_sha256':sha(record),'log_sha256':sha(record.with_suffix('.log')),'bench':(out/'tb.sv').relative_to(R).as_posix(),'bench_sha256':sha(out/'tb.sv'),'inputs':{n.relative_to(R).as_posix():sha(n) for n in inputs},'candidate_sha256':sha(source),'producer_sha256':sha(Path(__file__)),'unchanged_formal_inputs':formal}
assert all(sha(R/n)==h for n,h in formal.items())
with (O/'equivalence_validation.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
