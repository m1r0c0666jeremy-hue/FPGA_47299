from pathlib import Path
import ast,hashlib,json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((O/'source.json').read_text());assert all(sha(O/n)==h for n,h in source['candidates'].items());assert all(sha(R/n)==h for n,h in source['unchanged_formal_inputs'].items())
old=R/'build/stage1_serial_snapshot_20261024_0723/abort_probe.py';tree=ast.parse(old.read_text(encoding='utf-8-sig'));constants=[n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='bench' for t in n.targets) and isinstance(n.value,ast.Constant)];assert len(constants)==1
header=constants[0][:constants[0].index('integer k;')];needle="11'd0,10'd0,3'd0,1'b0";assert header.count(needle)==2;header=header.replace(needle,"11'd0,10'd200,3'd0,1'b0")
clone=O/'stage1_render_clean_reference.v';assert not clone.exists();clone.write_bytes((O/'stage1_render.v').read_bytes().replace(b'module stage1_render #',b'module stage1_render_clean_reference #',1))
body=r'''
integer k,cases=0,case_id,wait_clocks=0,max_wait=0;
always @(posedge clk)if(!rst)wait_clocks=0;else if(dut.state==22 && dut.mbusy)wait_clocks=wait_clocks+1;
initial begin
for(case_id=0;case_id<8;case_id=case_id+1)begin
@(negedge clk);rst=0;rrst=0;c=0;rc=0;v=0;
v[20:0]={10'd100,11'd100};v[41:21]={10'd200,11'd600};v[62:42]={10'd500,11'd200};
repeat(3)@(negedge clk);rst=1;c=1;@(negedge clk);c=0;
case(case_id)
0:wait(dut.mstart && dut.mop==1 && !dut.mbusy);
1:wait(dut.mbusy && dut.line_alu.mode==1 && dut.line_alu.count==0);
2:wait(dut.mbusy && dut.line_alu.mode==1 && dut.line_alu.count==1);
3:wait(dut.mbusy && dut.line_alu.mode==1 && dut.line_alu.count==23);
4:wait(dut.mbusy && dut.line_alu.mode==1 && dut.line_alu.count==46);
5:wait(dut.mbusy && dut.line_alu.mode==1 && dut.line_alu.count==47);
6:wait(dut.mbusy && dut.line_alu.mode==0 && dut.line_alu.count==0);
7:wait(dut.mbusy && dut.line_alu.mode==0 && dut.line_alu.count==13);
endcase
@(negedge clk);v=0;v[20:0]={10'd100,11'd200};v[41:21]={10'd500,11'd300};v[62:42]={10'd300,11'd600};rrst=1;c=1;rc=1;
@(negedge clk);c=0;rc=0;repeat(12000)@(negedge clk);
if(!ready || !rready || u || ru)$fatal(1,"mid-operation recommit readiness differs case%0d ready%0d/%0d under%0d/%0d",case_id,ready,rready,u,ru);
for(k=0;k<640;k=k+1)if(dut.state_line_mem[k]!==refdut.state_line_mem[k])$fatal(1,"mid-operation row word differs case%0d word%0d",case_id,k);
for(k=768;k<1024;k=k+1)if(dut.state_line_mem[k]!==refdut.state_line_mem[k])$fatal(1,"mid-operation edge word differs case%0d word%0d",case_id,k);
if(wait_clocks>51)$fatal(1,"arithmetic drain exceeded bounded latency");if(wait_clocks>max_wait)max_wait=wait_clocks;
cases=cases+1;$display("SERIAL_ABORT_CASE_PASS case%0d words896 wait%0d",case_id,wait_clocks);
end
if(cases!=8 || max_wait==0)$fatal(1,"arithmetic abort coverage incomplete");
$display("SERIAL_SNAPSHOT_MID_LAUNCH_RECOMMIT_PASS cases=8 words=7168 max_wait=%0d",max_wait);$finish;
end endmodule'''
out=run('private_serial_snapshot_safe_mid_launch',header+body,[R/'rtl/color_regions/stage1_arith.v',O/'stage1_render.v',clone],timeout=60)
rp=R/'reports/refined/regression'/(out.name+'.json');d=json.loads(rp.read_text());assert d['exit_code']==0
assert all(sha(R/n)==h for n,h in source['unchanged_formal_inputs'].items())
with (O/'abort_validation.json').open('x',encoding='utf-8') as f:json.dump(dict(status='PRIVATE_EIGHT_MID_OPERATION_RECOMMIT_CASES_PASSED_NOT_ADOPTED',record=rp.relative_to(R).as_posix(),record_sha256=sha(rp),log_sha256=sha(rp.with_suffix('.log')),inputs={n.replace('\\','/'):h for n,h in d['inputs'].items()},bench=(out/'tb.sv').relative_to(R).as_posix(),bench_sha256=sha(out/'tb.sv'),fixtures={old.relative_to(R).as_posix():sha(old)},producers={Path(__file__).relative_to(R).as_posix():sha(Path(__file__)),'scripts/refined_testlib.py':sha(R/'scripts/refined_testlib.py')},producer_sha256=sha(Path(__file__)),scope='Latest snapshot matches fresh clean instance across8 divider/multiplier launch/mid/end offsets and7168 cache/edge words. Copy is unchanged; mapping waits for old arithmetic idle with bounded drain. No formal/resource/physical credit.'),f,indent=2)
print('PRIVATE_SAFE_SNAPSHOT_ABORT_PROOF_PASS')
