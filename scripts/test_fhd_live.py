"""Native 1080 joint regression, derived from the independent EN source oracle.

Actual capture/classification/tracking, vendor FIFOs, DDR command adapter,
complete-frame banks, moving rational zoom, supported masks and English OSD.
The external DDR is an ordered byte oracle, not a simulation of physical pins.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from refined_testlib import R,run

# Reuse the EN test's fixture construction, not its old 720p execution/results.
code=(R/'scripts/test_refined_live.py').read_text(encoding='utf-8')
code=code[:code.index('def execute(job):')]
code=code.replace('a=ap.parse_args()',"ap.add_argument('--backend',choices=['iverilog','native'],default='native');a=ap.parse_args()")
code=code.replace('default=160','default=1295')
ns={};exec(compile(code,'EN oracle fixture','exec'),ns)
s,mods,a=ns['s'],ns['mods'],ns['a']
if a.backend=='native':
    from refined_native_testlib import run_native as run
edits={
 'always #6.667 pc':'always #6.734006734 pc',
 'integer h=0,v=725':'integer h=0,v=1084',
 'v>=725 && v<730':'v>=1084 && v<1089',
 'h>=1390 && h<1430':'h>=2008 && h<2052',
 'v<720 && h<1280':'v<1080 && h<1920',
 'wire [9:0] cy,y0':'wire [10:0] cy,y0',
 'reg [10:0] last_cx=640;reg [9:0] last_cy=360':'reg [10:0] last_cx=960;reg [10:0] last_cy=540',
 'for(y=0;y<720;y=y+1)':'for(y=0;y<1080;y=y+1)',
 'for(x=0;x<1280;x=x+4)':'for(x=0;x<1920;x=x+4)',
 'x=(b/3)%1280;y=b/3840':'x=(b/3)%1920;y=b/5760',
 'n/240>=342+2*f && n/240<366+2*f':'n/360>=504+4*f && n/360<552+4*f',
 'x>=600+4*f && x<632+4*f && y>=342+2*f && y<366+2*f':'x>=880+8*f && x<944+8*f && y>=504+4*f && y<552+4*f',
 'x>=480+4*f && x<512+4*f && y>=342+2*f && y<366+2*f':'x>=640+8*f && x<704+8*f && y>=504+4*f && y<552+4*f',
 '(ROTATE?1279-ox:ox)':'(ROTATE?1919-ox:ox)',
 '(ROTATE?623-oy:oy)':'(ROTATE?983-oy:oy)',
 'if(oy<624)':'if(oy<984)',
 'if(ox==1279)':'if(ox==1919)',
 'active[415:413]!=4':'active[415:413]!=5',
 '>24':' >48',
 'if(h==1649)':'if(h==2199)',
 'if(v==749)':'if(v==1124)',
 'if(frame==5 && v==749 && h==1600)':'if(frame==7 && v==1124 && h==2150)',
 'checked!=5*1280*624':'checked!=7*1920*984',
 'repeat(260000)':'repeat(83000)',
 '#200000000':'#700000000',
 'STABLE_LIVE_PASS':'FHD_LIVE_PASS',
}
for old,new in edits.items():
    if old not in s:raise AssertionError('EN oracle changed: '+old)
    s=s.replace(old,new)
def execute(job):
    pair,rot=job
    return run(f'fhd_live_{pair}_{rot}_g{a.line_gap}',s,mods,top='tb_stable_live',
       compile_args=['-I'+str(R/'rtl/color_regions'),f'-Ptb_stable_live.PAIR_MODE={pair}',f'-Ptb_stable_live.ROTATE={rot}'],timeout=7200)
jobs=[tuple(a.case)] if a.case else [(p,r) for p in (0,1) for r in (0,1)]
with ThreadPoolExecutor(max_workers=a.workers) as pool:list(pool.map(execute,jobs))
print('FHD_LIVE_ALL_PASS',len(jobs),'jobs',7*len(jobs),'display frames',7*len(jobs)*1920*984,'native video pixels; nominal synthetic line schedule')
