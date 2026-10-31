"""Refresh only the twelve inherited checks whose display inputs changed."""
import argparse,runpy,sys
from refined_testlib import R
import refined_testlib
from audit_stage1 import timing_baseline_specs

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('script');ap.add_argument('args',nargs=argparse.REMAINDER);a=ap.parse_args()
    allowed={'test_refined_fault_v4.py','test_refined_arbitration.py','test_refined_geometry.py',
             'test_osd_memory_ui.py','test_osd_memory_overlay.py','test_osd_packed_program.py'}
    assert a.script in allowed,a.script
    original=refined_testlib.run
    selected=set(timing_baseline_specs())
    def run(name,*args,**kwargs):
        if name in selected:return original('stage1_baseline_'+name,*args,**kwargs)
        print('UNCHANGED_BASELINE_NOT_RERUN',name,flush=True)
    refined_testlib.run=run
    sys.argv=[str(R/'scripts'/a.script),*a.args]
    runpy.run_path(sys.argv[0],run_name='__main__')
