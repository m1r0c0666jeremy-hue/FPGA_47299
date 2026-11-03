"""Private four-row cache probe. Formal RTL and active TD inputs remain unchanged."""
from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
formal=json.loads((R/'build/stage1_route_20261022_205748_044232/inputs.json').read_text())
assert all(sha(R/n)==h for n,h in formal.items())
source=(R/'rtl/color_regions/stage1_render.v').read_text()
def edit(a,b):
    global source
    assert source.count(a)==1,(a,source.count(a))
    source=source.replace(a,b)
edit('Packed state RAM + eight scanlines with serial stamps.','Packed state RAM + four scanlines with serial stamps.')
edit('line_mem[0:1279]','line_mem[0:639]')
edit('reg [7:0] bank_valid;reg [9:0] bank_row[0:7]','reg [3:0] bank_valid;reg [9:0] bank_row[0:3]')
edit("wire [10:0] read_address=y[2:0]*11'd160+{3'd0,x[10:3]};", "wire [9:0] read_address=y[1:0]*10'd160+{2'd0,x[10:3]};")
edit("wire [10:0] write_address=row[2:0]*11'd160+{3'd0,word_index};", "wire [9:0] write_address=row[1:0]*10'd160+{2'd0,word_index};")
source=source.replace('bank_valid[y[2:0]]','bank_valid[y[1:0]]').replace('bank_row[y[2:0]]','bank_row[y[1:0]]')
source=source.replace('bank_valid[row[2:0]]','bank_valid[row[1:0]]').replace('bank_row[row[2:0]]','bank_row[row[1:0]]')
edit("row<7 || {1'b0,y}+11'd6>={1'b0,row}","row<3 || {1'b0,y}+11'd2>={1'b0,row}")
candidate=O/'stage1_render.v'
with candidate.open('x',encoding='utf-8',newline='\n') as f:f.write(source)
proof=json.loads((R/'reports/stage1/software_current_20261022_2123.json').read_text())
results={}
for label,marker in (
 ('stage1_render_guards','STAGE1_RENDER_GUARDS_PASS'),
 ('stage1_regions','STAGE1_EDIT_RENDER_PASS point_pixels=134400'),
 ('stage1_render_14_624','STAGE1_RENDER_PASS cases=14 pixels=11182080'),
 ('stage1_overlay','STAGE1_OVERLAY_PASS cases=8 pixels=6389760')):
    entry=proof['regression'][label]
    assert all(sha(R/n)==h for group in (entry['inputs'],entry['fixture_inputs'],entry['producer_inputs']) for n,h in group.items())
    benches=[R/n for n in entry['fixture_inputs'] if n.endswith('/tb.sv')];assert len(benches)==1
    bench=benches[0].read_text().replace('dut.bank_row[yy%8]','dut.bank_row[yy%4]')
    modules=[candidate if n=='rtl/color_regions/stage1_render.v' else R/n for n in entry['inputs']]
    out=run('private_four_row_'+label,bench,modules,timeout=1800)
    record=R/'reports/refined/regression'/(out.name+'.json');log=record.with_suffix('.log')
    assert marker in log.read_text()
    results[label]=dict(record=record.relative_to(R).as_posix(),record_sha256=sha(record),log_sha256=sha(log))
assert all(sha(R/n)==h for n,h in formal.items())
with (O/'validation.json').open('x',encoding='utf-8') as f:json.dump(dict(scope='PRIVATE FOUR ROWS ONLY; no resource or physical result; not adopted',checks=results,unchanged_formal_inputs=formal,candidate_sha256=sha(candidate)),f,indent=2)
print('PRIVATE_FOUR_ROW_ALL_PASS; NOT ADOPTED; resource and formal physical result still required',flush=True)
