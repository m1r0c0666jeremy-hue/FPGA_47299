"""Actual production capture pipeline versus its immutable pre-fix source."""
from pathlib import Path
import hashlib,json,re,sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from refined_testlib import literal_fixture,run
from refined_capture_history_logic import history_asset
out=R/'build/refined_capture_history_formal';out.mkdir(exist_ok=True)
base=R/'rtl/color_regions/stable_capture.v'
original=(R/'scripts/refined_capture_history_base.v.txt').read_text(encoding='utf-8')
assert base.read_bytes()==history_asset(original).encode()
reference=original.replace('module stable_capture #','module reference_capture #').encode()
p=out/'reference.v'
if p.exists():assert p.read_bytes()==reference
else:p.write_bytes(reference)
ctx=dict(source_sha256=hashlib.sha256(base.read_bytes()).hexdigest())
tb=literal_fixture(R/'scripts/test_refined_history.py')
line=next(x for x in tb.splitlines() if x.startswith('stable_capture dut('))
gold=line.replace('stable_capture dut(', 'reference_capture gold(').replace(',id,ov,meta,drop);',',gid,gov,gmeta,gdrop);')
assert gold!=line
tb=tb.replace(line,line+'\nwire [639:0] gmeta;wire [31:0] gid,gdrop;wire gov;\n'+gold)
tb=re.sub(r'(dut\.tracker\.[^;]+;)',lambda m:m.group(1)+'\n'+m.group(1).replace('dut.tracker.','gold.tracker.'),tb)
tb=tb.replace('CHECK','').replace('LABEL','private_history_pipeline')
tb=tb.replace('endmodule',r'''
integer eq_checks=0,history_starts=0;
always @(posedge clk)begin #1;
 if({id,ov,meta,drop}!=={gid,gov,gmeta,gdrop})$fatal(1,"history pipeline output mismatch cycle%0d",eq_checks);
 eq_checks=eq_checks+1;
end
always @(posedge clk)if(rst && dut.gs)begin
 if(dut.history_for_bank!==gold.history_for_bank)$fatal(1,"history not aligned with grid start");
 history_starts=history_starts+1;
end
final begin
 if(eq_checks<230400 || history_starts==0)$fatal(1,"history pipeline coverage clocks%0d starts%0d",eq_checks,history_starts);
 $display("PRIVATE_CAPTURE_HISTORY_PIPELINE_PASS clocks%0d starts%0d exact-cycle metadata/output",eq_checks,history_starts);
end
endmodule''')
others=[R/'rtl/color_regions'/f'{n}.v' for n in ('stable_tracker','stable_model_lane','stable_filter4','stable_grid','regions_divide')]
for name,command,revision,last in [('stale_context',3,0,'0'),('matching_identity',15,1,'0'),('expired_identity',15,1,"32'hfffffff0")]:
 t=tb.replace('last_command=3;',f'last_command={command};').replace('last_revision=0;',f'last_revision={revision};').replace('last_id=0;',f'last_id={last};')
 run('capture_history_pipeline_'+name,t,[base,out/'reference.v',*others])
assert hashlib.sha256(base.read_bytes()).hexdigest()==ctx['source_sha256']
