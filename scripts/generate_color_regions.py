"""Generate only functional colour-region assets; --check never writes."""
from pathlib import Path
import argparse,json,re
from color_regions_reference import DEFAULTS
R=Path(__file__).resolve().parents[1]
def generate(check=False):
    c=json.loads((R/'rtl/03_tool_detection/target_config.json').read_text(encoding='utf-8'))
    cfg={k:c['regions_'+k] for k in DEFAULTS}
    assert all(type(v) is int for v in cfg.values())
    assert (cfg['sat_num'],cfg['sat_den'])==(3,16),'Current shift datapath implements 3/16'
    vals={k.upper():str(v) for k,v in cfg.items()}
    for k in ('red_hi','red_wrap','yellow_lo','yellow_hi','blue_lo','blue_hi','purple_lo','purple_hi'):
        assert 0<=cfg[k]<=360 and cfg[k]%15==0
        vals[k.upper()+'_Q']=str(cfg[k]//15)
    from color_regions_ui import assets as ui_assets
    assets=ui_assets()
    from color_regions_topology import assets as topology_assets
    assets.update(topology_assets(cfg))
    s=(R/'scripts/color_regions_classifier.v.txt').read_text(encoding='utf-8')
    for k,v in vals.items():s=s.replace('@'+k+'@',v)
    # Explicit shift/add constants: do not infer per-pixel DSP multipliers.
    def shift_constant(m):
        n=int(m[1]);return '('+'+'.join('dd' if b==0 else '(dd<<'+str(b)+')' for b in range(5) if n&(1<<b))+')'
    s=re.sub(r'(\d+)\*dd',shift_constant,s)
    assert not re.search(r'@[A-Z_]+@',s)
    assets['rtl/color_regions/regions_classifier.v']=s
    for name,s in assets.items():
        p=R/name;data=s.replace('\r\n','\n').encode()
        if check:assert p.is_file() and p.read_bytes()==data,name
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    print('COLOR_REGIONS_GENERATION_CHECK_PASS' if check else 'COLOR_REGIONS_GENERATED',len(assets))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');generate(ap.parse_args().check)
