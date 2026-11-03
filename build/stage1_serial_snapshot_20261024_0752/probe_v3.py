"""Private original pixel/capacity oracles; never counted as formal evidence."""
from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((O/'source.json').read_text());reference=R/s['baseline'];assert sha(reference)==s['baseline_sha256']
full=json.loads(reference.read_text());assert full['passed']==full['required']==110 and not full['missing']
assert all(sha(R/n)==h for n,h in s['unchanged_formal_inputs'].items())
assert all(sha(O/n)==h for n,h in s['candidates'].items())
checks={}
for label in ('stage1_render_guards','stage1_regions','stage1_render_14_624','stage1_overlay'):
 e=full['regression'][label]
 assert all(sha(R/n)==h for k in ('inputs','fixture_inputs','producer_inputs') for n,h in e[k].items())
 benches=[R/n for n in e['fixture_inputs'] if n.endswith('/tb.sv')];assert len(benches)==1;bench=benches[0].read_text();adjustment=None
 modules=[O/Path(n).name if n in ('rtl/color_regions/stage1_regions.v','rtl/color_regions/stage1_render.v') else R/n for n in e['inputs']]
 if label=='stage1_render_guards':
  assert bench.count('dut.fv[189:168]')==1 and bench.count('dut.fd[20:0]')==1
  bench=bench.replace('dut.fv[189:168]',"{dut.state_line_mem[649][0],dut.state_line_mem[648][20:0]}").replace('dut.fd[20:0]','dut.state_line_mem[672][20:0]')
  adjustment='Exact same22-bit frozen B coordinate spans snapshot RAM words648/649;21-bit draft point is word672. All existing assertions, commits, resets and deadlines retained.'
 if label=='stage1_regions':
  needle='stage1_render #(.SPLIT_DRAFT(1)) reference_picture';assert bench.count(needle)==1
  bench=bench.replace(needle,'stage1_render_reference #(.SPLIT_DRAFT(1)) reference_picture',1);modules.append(O/'stage1_render_reference.v')
  needle='if({pmask,pcolor,lon,glyph,gx,gy,lcolor,rready,under}!==';assert bench.count(needle)==1
  bench=bench.replace(needle,'if(rde && {pmask,pcolor,lon,glyph,gx,gy,lcolor,rready,under}!==',1)
  adjustment='Golden old-controller/F renderer vs private G. All controller cycle/coordinate/capacity and original editor assertions retained. Coupled display comparison covers every active pixel; blanking-only ready/preparation may differ by40 copy clocks plus1 fetch/edge. Existing10000-clock readiness deadlines remain; extra adversarial deferral/recommit proof is mandatory.' 
 out=run('private_serial_snapshot_safe_'+label,bench,modules,timeout=1800)
 record=R/'reports/refined/regression'/(out.name+'.json');d=json.loads(record.read_text());assert d['exit_code']==0
 checks[label]=dict(record=record.relative_to(R).as_posix(),record_sha256=sha(record),log_sha256=sha(record.with_suffix('.log')),inputs={n.replace('\\','/'):h for n,h in d['inputs'].items()},bench=(out/'tb.sv').relative_to(R).as_posix(),bench_sha256=sha(out/'tb.sv'),fixtures=e['fixture_inputs'],producers=e['producer_inputs'],private_fixture_adjustment=adjustment)
 (O/'progress_v3.json').write_text(json.dumps(dict(status='PRIVATE_NOT_ADOPTED_NOT_FORMAL_NO_RESOURCE_CREDIT',checks=checks),indent=2))
 assert all(sha(R/n)==h for n,h in s['unchanged_formal_inputs'].items())
with (O/'selected_validation_v3.json').open('x',encoding='utf-8') as f:json.dump(dict(status='ONLY_SELECTED_FOUR_PASSED; ADDITIONAL_DEFERRED_EDIT_PROOF_REQUIRED_BEFORE_GATE_OR_ADOPTION',checks=checks,candidates=s['candidates'],source_sha256=sha(O/'source.json'),producer_sha256=sha(Path(__file__)),formal_inputs_unchanged=True),f,indent=2)
print('PRIVATE_SERIAL_SNAPSHOT_SELECTED_FOUR_PASS; still require adversarial deferral/reset/recommit proof',flush=True)
