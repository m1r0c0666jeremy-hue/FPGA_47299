"""Preserve the existing full calibration fixtures with isolated output/logs."""
from refined_testlib import R,run
import ast,datetime,re,sys,types
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
out=R/'build/sim'/('refined_calibration_'+stamp);out.mkdir(parents=True,exist_ok=False)
def adapted(name,src,modules):
 src=re.sub(r'(stable_calibration\s+dut\([^;]+)(\);)',r'\1,,\2',src)
 old='if(dut.rx!=52+160*(dut.groups%8)+8*dut.frames || dut.ry!=17+90*(dut.groups/8)+8*((3*dut.frames)%8))'
 new='if(!(dut.rx>=636 && dut.rx<644 && dut.ry>=356 && dut.ry<364) && (dut.rx!=52+160*(dut.background_groups%8)+8*dut.frames || dut.ry!=27+120*(dut.background_groups/8)+8*((3*dut.frames)%8)))'
 src=src.replace(old,new)
 if 'task frames;' in src:
  src=src.replace('if(n>=3000000)$fatal', '$display("REFINED_CALIBRATION_STEP kind%0d status%h",kind,status);\nif(n>=3000000)$fatal')
 run('calibration_'+name,src,modules)
if '--distributions' in sys.argv:
 shim=types.ModuleType('test_ring_calibration');shim.R=R;shim.O=out;shim.P=R/'reports/refined/regression';shim.run=adapted
 sys.modules['test_ring_calibration']=shim
 script=R/'scripts/test_ring_distributions.py'
 sys.argv=[str(script),*(['--extended'] if '--extended' in sys.argv else [])]
 exec(compile(script.read_text(encoding='utf-8'),str(script),'exec'),{'__file__':str(script),'__name__':'__main__'})
else:
 script=R/'scripts/test_ring_calibration.py';scope={'__file__':str(script),'__name__':'refined_calibration_fixture'}
 tree=ast.parse(script.read_text(encoding='utf-8'))
 exec(compile(tree,str(script),'exec'),scope)
 scope.update(run=adapted,O=out,P=R/'reports/refined/regression')
 main=next(n for n in tree.body if isinstance(n,ast.If) and ast.unparse(n.test)=="__name__ == '__main__'")
 sys.argv=[str(script)]
 exec(compile(ast.fix_missing_locations(ast.Module(body=main.body,type_ignores=[])),str(script),'exec'),scope)
