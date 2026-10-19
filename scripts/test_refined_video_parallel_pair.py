"""Add pair-1 workers using an existing, current-source frozen video fixture.

Never regenerates shared oracle files while the main video matrix is running.
The main runner's --reuse-current skips cases completed here.
"""
from pathlib import Path
import argparse,datetime,hashlib,json
from concurrent.futures import ThreadPoolExecutor
from refined_testlib import R,run,literal_fixture

ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
assert 1<=a.workers<=8
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
template=None
for path in sorted((R/'reports/refined/regression').glob('refined_video_0_0_0_0_f0_n1_*.json'),reverse=True):
    record=json.loads(path.read_text(encoding='utf-8'))
    bench=Path(record.get('output',''))/'tb.sv'
    if record.get('exit_code')==0 and bench.is_file() and all(sha(R/name)==value for name,value in record['inputs'].items()):
        template=(path,record,bench);break
assert template,'A passing current-source matrix case is required first'
path,record,bench=template;source=bench.read_text(encoding='utf-8')
modules=[R/name for name in record['inputs']]
oracle=R/'build/sim/refined_video_refined'
oracles={name:sha(oracle/name) for name in ('masks_0.hex','masks_1.hex')}
origins=literal_fixture(R/'scripts/test_refined_video.py','origins')
context=R/'reports/refined'/('video_parallel_resume_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.json')
context.write_bytes(json.dumps(dict(template=path.relative_to(R).as_posix(),template_sha256=sha(path),
 bench_sha256=sha(bench),inputs=record['inputs'],oracle_directory=oracle.relative_to(R).as_posix(),
 oracles=oracles,jobs='pair1 all5 zooms x4 pages x2 directions, reverse order',shared_oracles_written=False),indent=2).encode('utf-8'))

def execute(job):
    z,page,rot=job;name=f'refined_video_1_{z}_{page}_{rot}_f0_n1'
    for old in sorted((R/'reports/refined/regression').glob(name+'_*.json'),reverse=True):
        item=json.loads(old.read_text(encoding='utf-8'));old_bench=Path(item.get('output',''))/'tb.sv'
        if item.get('exit_code')==0 and item.get('inputs')==record['inputs'] and old_bench.is_file() and old_bench.read_text(encoding='utf-8')==source:
            print('REFINED_VIDEO_PARALLEL_REUSE',name,flush=True);return
    x,y=origins[z]
    run(name,source,modules,top='tb_stable_video',args=['+PAIR=1',f'+ZOOM={z}',f'+MODE={page}',f'+ROTATE={rot}',
        f'+X={x}',f'+Y={y}','+FAULT=0','+FRAMES=1',f'+MASK={(oracle/"masks_1.hex").as_posix()}'],timeout=1800)

with ThreadPoolExecutor(max_workers=a.workers) as pool:
    list(pool.map(execute,list(reversed([(z,p,r) for z in range(5) for p in range(4) for r in (0,1)]))))
assert all(sha(oracle/name)==value for name,value in oracles.items()),'Shared oracle changed during matrix simulation'
print('REFINED_VIDEO_PARALLEL_PAIR_PASS 40 cases completed or reused, shared oracle hashes unchanged',flush=True)
