"""Private only; replay saved independent math and compare every visible ALU output."""
from pathlib import Path
import hashlib,json,sys,subprocess
O=Path(__file__).resolve().parent;R=O.parents[1]
sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
from test_stage1_arith import BENCH
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=json.loads((R/'build/stage1_place_20261022_231917/inputs.json').read_text())
assert all(sha(R/n)==h for n,h in inputs.items())
baseline=O/'baseline_arith.v'
baseline.write_bytes((R/'rtl/color_regions/stage1_arith.v').read_bytes().replace(b'module stage1_arith #',b'module baseline_arith #',1))
checks={}
def execute(name,source,mods):
 out=run('stage1_private_resetfree_'+name,source,mods,timeout=300)
 record=R/'reports/refined/regression'/(out.name+'.json');d=json.loads(record.read_text())
 assert d['exit_code']==0
 checks[name]=dict(record=record.relative_to(R).as_posix(),record_sha256=sha(record),log_sha256=sha(record.with_suffix('.log')),
   bench=(out/'tb.sv').relative_to(R).as_posix(),bench_sha256=sha(out/'tb.sv'),inputs=d['inputs'],fixtures=d['fixture_inputs'],producers=d['producer_inputs'])
for mw,dw in ((12,48),(21,23),(24,14)):
 path=R/f'build/stage1_arith_vectors/math_{mw}_{dw}.hex';assert len(path.read_text().splitlines())==2049
 source=BENCH.replace('WIDTH',str(mw)).replace('DIVISOR',str(dw)).replace('COUNT','2049').replace('FILE',path.as_posix())
 execute(f'math_{mw}_{dw}',source,[O/'stage1_arith.v'])
 source=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;reg [1:0] op=0;reg [47:0] a=0,b=0;
wire bo,do_,bn,dn;wire [47:0] ro,rmo,rn,rmn;
baseline_arith #(.MW(MW_VALUE),.DW(DW_VALUE)) old(clk,rst,start,op,a,b,bo,do_,ro,rmo);
stage1_arith #(.MW(MW_VALUE),.DW(DW_VALUE)) candidate(clk,rst,start,op,a,b,bn,dn,rn,rmn);
reg [63:0] random_state=64'h1054a8c1329f607d;integer i,checks=0,resets=0;
task compare;begin
 if({bo,do_,ro,rmo}!=={bn,dn,rn,rmn})$fatal(1,"reset-free mismatch cycle%0d reset%b start%b op%0d old%b/%b/%h/%h new%b/%b/%h/%h",i,rst,start,op,bo,do_,ro,rmo,bn,dn,rn,rmn);
 checks=checks+1;end endtask
always @(posedge clk)begin #1;compare;end
always @(negedge rst)begin #1;compare;end
initial begin repeat(3)@(negedge clk);
for(i=0;i<200000;i=i+1)begin
 random_state=random_state^(random_state<<13);random_state=random_state^(random_state>>7);random_state=random_state^(random_state<<17);
 a=random_state[47:0];b={random_state[31:0],random_state[63:48]};op=random_state[49:48];start=random_state[50];
 if(i%257==0)begin rst=0;resets=resets+1;end else rst=1;
 if(i%1319==0)begin #2;rst=0;resets=resets+1;#2;rst=1;end
 @(negedge clk);
end
$display("PRIVATE_RESETFREE_EQ_PASS MW%0d DW%0d comparisons%0d resets%0d",MW_VALUE,DW_VALUE,checks,resets);$finish;end endmodule'''
 source=source.replace('MW_VALUE',str(mw)).replace('DW_VALUE',str(dw))
 execute(f'equivalence_{mw}_{dw}',source,[baseline,O/'stage1_arith.v'])
assert all(sha(R/n)==h for n,h in inputs.items())
proof=dict(status='PRIVATE_RESETFREE_ARITH_VALIDATED_NOT_ADOPTED',scope='No resource estimate or current formal credit',
 candidate_sha256=sha(O/'stage1_arith.v'),producer_sha256=sha(Path(__file__)),baseline_sha256=sha(baseline),checks=checks,unchanged_formal_inputs=inputs)
with (O/'validation.json').open('x',encoding='utf-8') as f:json.dump(proof,f,indent=2)
print('PRIVATE_RESETFREE_ALL_PASS',len(checks),flush=True)
