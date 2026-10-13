"""Run candidate-baseline and extracted-ingress regressions in new outputs.

The archived tests/expected results are reused unchanged. Only their output
locations change, so no old success/failure logs or previews are overwritten.
"""
from pathlib import Path
import argparse, os, subprocess, sys

R=Path(__file__).resolve().parents[1]
O=R/'build/sim/git_return/runners'
O.mkdir(parents=True,exist_ok=True)
p=argparse.ArgumentParser()
p.add_argument('--stage',choices=['unit','ingress','detection','full','video','osd','regression'],required=True)
args=p.parse_args()
name='test_robust_ingress.py' if args.stage=='ingress' else f'test_candidate_{args.stage}.py'
source=(R/'scripts'/name).read_text(encoding='utf-8')
source=source.replace('Path(__file__).resolve().parents[1]',f'Path({str(R)!r})')
source=source.replace('build/sim/candidate','build/sim/git_return')
source=source.replace('build/sim/robust','build/sim/git_return')
source=source.replace('reports/candidate_','reports/git_return_')
source=source.replace('reports/robust_ingress.log','reports/git_return_ingress.log')
runner=O/name
runner.write_text(source,encoding='utf-8',newline='\n')
env=os.environ.copy();env['PYTHONPATH']=str(R/'scripts')
flags=['--full'] if args.stage=='unit' else []
result=subprocess.run([sys.executable,str(runner),*flags],cwd=R,env=env)
if result.returncode: raise SystemExit(result.returncode)
print(f'GIT_RETURN_STAGE_PASSED {args.stage}')
