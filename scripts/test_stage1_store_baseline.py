"""Refresh the two archived bank-store contracts against the adopted RTL."""
from refined_testlib import R,run
def stage1_run(name,source,modules):
    return run(name,source,modules,args=('+fixture=scripts/test_refined_store.py',
                                      '+oracle=scripts/test_refined_timing.py'))
s=(R/'scripts/test_refined_store.py').read_text(encoding='utf-8')
s=s.replace("run('store_cached_id_comparison'","run('stage1_store_cached_id_comparison'")
s=s.replace("run('refined_v4_frame_store_and_display'","run('stage1_refined_v4_frame_store_and_display'")
s=s.replace("run('","stage1_run('")
exec(compile(s,str(R/'scripts/test_refined_store.py'),'exec'),{'__name__':'__main__','__file__':__file__,'stage1_run':stage1_run})
