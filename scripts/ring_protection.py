"""Record/check historical artifacts and the user's other working copies."""
from pathlib import Path
import hashlib,json,subprocess,argparse
R=Path(__file__).resolve().parents[1]
P=R/'reports/transparent_ring/protected_inputs.json'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
    paths=list(R.rglob('*.bit'))+list(R.rglob('*.zip'))
    paths += [Path('D:/aaa_FPGA/color-regions-env-issues/td_project/target_color_regions.al'),
              Path('D:/aaa_FPGA/criticalwork/td_project/target_color_regions.al')]
    paths += [R/'td_project/target_lock.adc',R/'td_project/target_lock.sdc',R/'user_source/hdl_source/video_in.v']
    return {str(p.resolve()):digest(p) for p in paths if p.is_file()}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--record',action='store_true');args=a.parse_args()
    if args.record:
        if P.exists():raise SystemExit('Protection record already exists')
        P.parent.mkdir(parents=True,exist_ok=True)
        P.write_text(json.dumps(inputs(),ensure_ascii=False,indent=2),encoding='utf-8')
    else:
        saved=json.loads(P.read_text(encoding='utf-8'))
        changed=[p for p,h in saved.items() if not Path(p).is_file() or digest(Path(p))!=h]
        if changed:raise SystemExit('Protected input changed: '+str(changed))
        print('RING_PROTECTION_PASS',len(saved),'historical/user files')
