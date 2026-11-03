"""Crowded/clipped labels keep the exact pre-sharing placement and pixels."""
from refined_testlib import R
import hashlib
task=R/(R/'build/current_display_shared_path.txt').read_text(encoding='utf-8')
assert hashlib.sha256((task/'reference/stage1_render.v').read_bytes()).hexdigest()=='7f442aad1036d8b863c11411cd5509c63f0ceb1f2632af1997569e2600daca99'
wrapper=(R/'scripts/test_stage1_render_equivalence.py').read_text(encoding='utf-8')
extra=r"""
s=s.replace('cases=[(z,r,2,0) for z in range(5) for r in range(2)]',
 'cases=[(z,r,1,kind) for kind in (4,5) for z in range(5) for r in range(2)]')
s=s.replace('else:cases +=[(0,0,1,0),(0,0,2,1),(1,0,1,2),(0,0,1,3)]','else:pass')
s=s.replace('        verts=sizes=0', '''        if kind==4:active=[[(80+j*10,80),(86+j*10,86)] for j in range(4)]
        elif kind==5:active=[[(1240,570+j*9),(1279,576+j*9)] for j in range(4)]
        verts=sizes=0''')
s=s.replace("'stage1_render_equivalence'", "'stage1_render_labels'")
s=s.replace('STAGE1_RENDER_EQUIVALENCE_PASS', 'STAGE1_RENDER_LABELS_PASS')
s=s.replace('ROWS);', 'ROWS);$fflush();')
"""
at=wrapper.index('exec(compile(')
exec(compile(wrapper[:at]+extra+wrapper[at:],str(R/'scripts/test_stage1_render_equivalence.py'),'exec'),{'__name__':'__main__','__file__':__file__})
