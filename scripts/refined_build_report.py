"""Distinguish gate estimates from physically placed resources."""
from pathlib import Path
import re
def assess(out,stage):
    text=(Path(out)/('target_color_regions_gate.area' if stage=='synth' else 'target_color_regions_phy.area')).read_text(encoding='utf-8')
    resources={}
    for key in ('slice','lut6','reg','eram','dsp'):
        match=re.search(r'^\s*#'+key+r'\*?\s+(\d+)',text,re.M)
        if not match:raise ValueError(f'Missing {key} in area report')
        resources[key]=int(match[1])
    result=dict(resources=resources,gate_estimate=stage=='synth')
    limits={'slice':21216,'lut6':21216,'reg':42432,'eram':108,'dsp':40}
    checked=('reg','eram','dsp') if stage=='synth' else tuple(limits)
    result['resource_pass']=all(resources[k]<=limits[k] for k in checked)
    result['placement_required']=stage=='synth' and resources['slice']>limits['slice']
    if stage=='full':
        timing=(Path(out)/'target_color_regions_phy.ts').read_text(encoding='utf-8')
        result['slack_ns']={k:float(re.search(k+r':\s*([-\d.]+)ns',timing)[1]) for k in ('SWNS','HWNS')}
        result['timing_pass']=min(result['slack_ns'].values())>=0
    return result
