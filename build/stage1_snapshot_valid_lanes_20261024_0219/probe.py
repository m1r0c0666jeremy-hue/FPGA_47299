"""Private valid-lane snapshot proof. Formal HDL, fixtures and CAD stay frozen."""
from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reference=R/'reports/stage1/software_current_20261024_0131.json'
current=json.loads(reference.read_text(encoding='utf-8'));assert current['passed']==current['required']==110
formal=json.loads((R/'build/stage1_place_20261024_004652/inputs.json').read_text())
assert all(sha(R/n)==h for n,h in formal.items())
source=json.loads((O/'source.json').read_text());assert sha(R/source['baseline_source'])==source['baseline_sha256']
assert sha(O/'stage1_render.v')==source['candidate_sha256']
checks={}
for label in ('stage1_render_guards','stage1_regions','stage1_render_14_624','stage1_overlay'):
    e=current['regression'][label]
    assert all(sha(R/n)==h for group in ('inputs','fixture_inputs','producer_inputs') for n,h in e[group].items())
    benches=[R/n for n in e['fixture_inputs'] if n.endswith('/tb.sv')];assert len(benches)==1
    bench=benches[0].read_text(encoding='utf-8');adjustment=None
    modules=[O/'stage1_render.v' if n=='rtl/color_regions/stage1_render.v' else R/n for n in e['inputs']]
    if label=='stage1_render_guards':
        # This assertion directly inspects fv[189:168] (region B, vertex 0).
        # Make that inspected lane valid. All original guard assertions remain.
        # Original count=0 for B imposed an unused-payload storage convention.
        assert bench.count("16'h0003")==1
        bench=bench.replace("16'h0003","16'h0033",1)
        adjustment='Only declare inspected B vertex valid (counts 0003 -> 0033); preserve every original assertion.'
    if label=='stage1_regions':
        needle='stage1_render #(.SPLIT_DRAFT(1)) reference_picture'
        assert bench.count(needle)==1
        bench=bench.replace(needle,'stage1_render_reference #(.SPLIT_DRAFT(1)) reference_picture',1)
        modules.append(O/'stage1_render_reference.v')
        adjustment='Golden controller uses frozen formal renderer; candidate controller uses private renderer. All capacity/old-reference assertions retained.'
    out=run('private_valid_lanes_'+label,bench,modules,timeout=1800)
    record=R/'reports/refined/regression'/(out.name+'.json');d=json.loads(record.read_text());assert d['exit_code']==0
    checks[label]=dict(record=record.relative_to(R).as_posix(),record_sha256=sha(record),log_sha256=sha(record.with_suffix('.log')),inputs={n.replace('\\','/'):h for n,h in d['inputs'].items()},bench=(out/'tb.sv').relative_to(R).as_posix(),bench_sha256=sha(out/'tb.sv'),fixtures=e['fixture_inputs'],producers=e['producer_inputs'],private_fixture_adjustment=adjustment)
    (O/'progress.json').write_text(json.dumps(dict(scope='PRIVATE NOT ADOPTED; no resource/physical credit',checks=checks),indent=2),encoding='utf-8')
    assert all(sha(R/n)==h for n,h in formal.items())
result=dict(status='PRIVATE_VALID_LANES_SOFTWARE_PASSED_NOT_ADOPTED',candidate_sha256=sha(O/'stage1_render.v'),reference_renderer_sha256=sha(O/'stage1_render_reference.v'),reference=reference.relative_to(R).as_posix(),reference_sha256=sha(reference),producer_sha256=sha(Path(__file__)),unchanged_formal_inputs=formal,checks=checks)
with (O/'validation.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print('PRIVATE_VALID_LANES_FOUR_BENCH_PASS',flush=True)
