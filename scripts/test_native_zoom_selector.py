"""Compare production selector to its frozen pre-optimization RTL each clock."""
import ast,datetime,hashlib,json
from refined_testlib import R
from test_native_zoom_core import execute

def main():
 reference=R/'build/native_zoom_place_20261029_210805/compiled_source/rtl/color_regions/native_frame_store.v'
 raw=reference.read_bytes();assert hashlib.sha256(raw).hexdigest()=='e5986035ab67b9ec5c07e13fb47d602b59258197b43070f366dc583aa858da91'
 out=R/'build'/('native_selector_reference_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir(exist_ok=False)
 old=out/'frozen_frame_store.v';old.write_text(raw.decode('utf-8').replace('module native_frame_store #','module frozen_frame_store #'),encoding='utf-8')
 producer=R/'scripts/probe_native_frame_selector.py';tree=ast.parse(producer.read_text(encoding='utf-8'))
 tb=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='tb' for t in n.targets))
 tb=tb.replace('module tb;','module selector_case #(parameter WORDS=32)(output reg done=0);')
 tb=tb.replace('native_frame_store #','frozen_frame_store #').replace('private_frame_store #','native_frame_store #')
 tb=tb.replace('.WORDS(32)','.WORDS(WORDS)').replace('n<32','n<WORDS').replace('n==31','n==WORDS-1').replace('n==16','n==WORDS/2')
 tb=tb.replace('PRIVATE_SELECTOR_EQUIVALENCE_PASS frames3000 cycles%0d wrap/lastwrite_snapshot/meta/source/invalidate/bank_reuse; NOT_ADOPTED_NO_RESOURCE_MEASUREMENT',
   'SELECTOR_CASE_PASS frames3000 cycles%0d wrap/lastwrite_snapshot/meta/source/invalidate/bank_reuse')
 tb=tb.replace('$finish;','done=1;')
 tb+='''\nmodule tb;wire [2:0] done;
 selector_case #(.WORDS(4)) a(done[0]);selector_case #(.WORDS(8)) b(done[1]);selector_case #(.WORDS(32)) c(done[2]);
 initial begin wait(&done);$display("NATIVE_SELECTOR_EQUIVALENCE_PASS 9000frames words4/8/32 precomputed_bank_choice clock_exact");$finish;end
 endmodule\n'''
 result=execute('selector_equivalence',tb,['native_frame_store.v',str(old)],timeout=300)
 receipt=result/'native_receipt.json';d=json.loads(receipt.read_text(encoding='utf-8'))
 d['producer_inputs'][producer.relative_to(R).as_posix()]=hashlib.sha256(producer.read_bytes()).hexdigest()
 receipt.write_text(json.dumps(d,indent=2),encoding='utf-8')
if __name__=='__main__':main()
