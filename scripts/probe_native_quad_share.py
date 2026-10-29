"""Private reader mux sharing; execute independent color/page oracles unchanged."""
import datetime,hashlib,json,sys
from refined_testlib import R
from test_native_zoom_core import execute
import test_native_zoom_color_modes as color_test

def main():
 out=R/'build'/('native_quad_share_probe_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir(exist_ok=False)
 core=R/'rtl/color_regions/native_line_core.v';wrapper=R/'rtl/color_regions/native_line_reader.v'
 before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (core,wrapper)}
 s=core.read_text(encoding='utf-8').replace('module native_line_core','module private_line_core')
 old=''' wire [47:0] ordered_pair=linegroup >> ((job_rotate?pair_index[2:0]:7-pair_index[2:0])*48);
 wire [47:0] pair_rgb=job_rotate?{ordered_pair[23:0],ordered_pair[47:24]}:ordered_pair;
'''
 assert old in s;s=s.replace(old,'')
 anchor=' wire [3:0] hit;stable_model_lane'
 assert anchor in s;s=s.replace(anchor," wire [47:0] pair_rgb=pair_index[0]?pixel_quad[47:0]:pixel_quad[95:48];\n"+anchor)
 candidate=out/'private_line_core.v';candidate.write_text(s,encoding='utf-8')
 w=wrapper.read_text(encoding='utf-8').replace('native_line_core core(', 'private_line_core core(')
 private_wrapper=out/'private_line_reader.v';private_wrapper.write_text(w,encoding='utf-8')
 outputs=[]
 def private_execute(name,tb,modules,**kw):
  modules=[str(candidate) if m=='native_line_core.v' else str(private_wrapper) if m=='native_line_reader.v' else m for m in modules]
  result=execute('private_quad_'+name,tb,modules,**kw);outputs.append(result.relative_to(R).as_posix());return result
 color_test.execute=private_execute
 for z in range(3):
  sys.argv=[__file__,'--zoom',str(z)];color_test.main()
 assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in before.items())
 receipt={'status':'PRIVATE_QUAD_SHARE_EQUIVALENT_PIXELS','source_hashes':{p.relative_to(R).as_posix():h for p,h in before.items()},
  'private_core_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'outputs':outputs,'cases':len(outputs),'adopted':False,'resource_measured':False,
  'scope':'Independent dense/average RGB, masks and four pages, 3zoom/2rotate/2pairs, 20480pixels each; production files untouched'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(out,receipt)
if __name__=='__main__':main()
