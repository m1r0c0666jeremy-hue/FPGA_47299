"""Native-rate classifier sharing against frozen four-lane capture and geometry."""
import argparse,hashlib,json
from refined_testlib import R
from test_native_zoom_core import execute

REFERENCE_SHA='0f4134435dc26f31720566e514fa101749ce5a6644b61e810dbc76d0a94260a3'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--case',choices=('masks','full','fault','reducer'),required=True);a=ap.parse_args()
 fixture=R/'scripts/native_zoom_fixtures'/('capture_shared_'+a.case+'.sv')
 source=fixture.read_text(encoding='utf-8')
 modules=['native_memory_video_out.v','stable_model_lane.v']
 if a.case in ('full','fault'):
  reference=R/'vendor_reference/native_capture_2720936.v'
  assert hashlib.sha256(reference.read_bytes()).hexdigest()==REFERENCE_SHA
  modules += [str(reference),'stable_filter4.v','stable_grid.v','regions_divide.v']
 if a.case=='reducer':modules+=['native_downsample2.v','native_line_ram.v']
 out=execute('capture_shared_'+a.case,source,modules,timeout=1800)
 p=out/'native_receipt.json';d=json.loads(p.read_text(encoding='utf-8'))
 d['producer_inputs'][fixture.relative_to(R).as_posix()]=hashlib.sha256(fixture.read_bytes()).hexdigest()
 p.write_text(json.dumps(d,indent=2),encoding='utf-8')

if __name__=='__main__':main()
