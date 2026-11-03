"""Compare current, bounded point and bounded render arithmetic only after the formal TD ends; no parallel TD."""
from pathlib import Path
import copy,datetime,hashlib,json,os,re,subprocess,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;R=O.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
active=subprocess.check_output(['powershell','-NoProfile','-Command','@(Get-Process -Name td_commands_prompt -ErrorAction SilentlyContinue).Count'],text=True).strip()
assert active=='0','Wait for the active formal TD; do not run a second TD'
proof=json.loads((O/'validation.json').read_text());eq=json.loads((O/'equivalence_validation.json').read_text())
assert len(proof['checks'])==7 and len(eq['checks'])==3
assert sha(O/'probe.py')==proof['producer_sha256'] and sha(O/'equivalence.py')==eq['producer_sha256']
assert all(sha(R/n)==h for n,h in proof['candidate_inputs'].items())
assert sha(O/'stage1_arith.v')==eq['candidate_sha256']
assert proof['unchanged_formal_inputs']==eq['unchanged_formal_inputs']
assert all(sha(R/n)==h for n,h in proof['unchanged_formal_inputs'].items())
render=json.loads((O/'render_validation.json').read_text())
assert len(render['checks'])==5 and sha(O/'render_probe.py')==render['producer_sha256']
assert sha(O/'stage1_render_mw14.v')==render['candidate_sha256']
assert render['other_candidates']==proof['candidate_inputs'] and render['unchanged_formal_inputs']==proof['unchanged_formal_inputs']
markers={'stage1_point':'STAGE1_POINT_PASS cases=516','stage1_validate':'STAGE1_VALIDATE_PASS cases=220',
         'stage1_regions':'STAGE1_EDIT_RENDER_PASS point_pixels=134400','stage1_render_guards':'STAGE1_RENDER_GUARDS_PASS',
         'stage1_render_14_624':'STAGE1_RENDER_PASS cases=14 pixels=11182080','stage1_overlay':'STAGE1_OVERLAY_PASS cases=8 pixels=6389760'}
for group in (proof,eq,render):
    for label,e in group['checks'].items():
        assert sha(R/e['record'])==e['record_sha256'] and sha((R/e['record']).with_suffix('.log'))==e['log_sha256']
        assert sha(R/e['bench'])==e['bench_sha256']
        assert all(sha(R/n)==h for k in ('inputs','fixtures','producers') for n,h in e.get(k,{}).items())
        if 'reference_bench' in e:assert sha(R/e['reference_bench'])==e['reference_bench_sha256']
        log=(R/e['record']).with_suffix('.log').read_text()
        if group is eq:
            mw,dw=label.split('_');marker=f'PRIVATE_BOUNDED_DEFAULT_EQ_PASS MW{mw} DW{dw} comparisons200932 resets931'
        elif label.startswith('math_'):
            _,mw,dw,*_=label.split('_');marker=f'STAGE1_ARITH_PASS width={mw} divisor={dw} cases=2049'
        else:marker=markers[label]
        assert marker in log,(label,'Missing expected private proof marker')
        if label=='stage1_regions':assert 'STAGE1_REGIONS_PASS' in log

td=Path('D:/26_software/TangDynasty/bin/td_commands_prompt.exe');env=os.environ.copy();env['PATH']=str(td.parent)+os.pathsep+env.get('PATH','')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');result={}
wrapper_source=R/'build/stage1_split_draft_20261022_1833/gate_split_shared_stamp_20261022_192541/serial_wrapper.v'
for label in ('indexed','bounded','bounded_render'):
    out=O/('gate_'+label+'_'+stamp);out.mkdir(exist_ok=False);sources=out/'sources';sources.mkdir()
    wrapper=out/'serial_wrapper.v';wrapper.write_bytes(wrapper_source.read_bytes());mods=[wrapper];inputs={}
    for name in ('stage1_arith','stage1_sequence','stage1_point','stage1_segment','stage1_validate','stage1_regions','stage1_render'):
        if name=='stage1_render' and label=='bounded_render':original=O/'stage1_render_mw14.v'
        elif name in ('stage1_arith','stage1_point') and label!='indexed':original=O/(name+'.v')
        else:original=R/'rtl/color_regions'/(name+'.v')
        frozen=sources/original.name;frozen.write_bytes(original.read_bytes());mods.append(frozen)
        inputs[original.relative_to(R).as_posix()]=sha(original)
    (out/'inputs.json').write_text(json.dumps(inputs,indent=2))
    root=ET.fromstring((R/'td_project/target_color_regions_stage1.al').read_text().replace('&','&amp;').replace('::','__COLON__'))
    root.set('Path',out.as_posix());template=copy.deepcopy(root.find('./Source_Files/Verilog/File'))
    for group in root.findall('./Source_Files/*'):
        for node in list(group):group.remove(node)
    for i,path in enumerate(mods):
        node=copy.deepcopy(template);node.set('Path',path.as_posix());root.find('./Source_Files/Verilog').append(node)
        for attr in node.findall('./FileInfo/Attr'):
            if attr.get('Name')=='CompileOrder':attr.set('Val',str(i))
    project=out/'target_color_regions_stage1.al';project.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode').replace('&amp;','&').replace('__COLON__','::'))
    script=out/'run.tcl';script.write_text('''if {[catch {
import_device ph1_35p.db -package PH1P35MDG324 -speed 3
cd {OUT}
open_project {PROJECT} -single_run
elaborate -top serial_wrapper
set_param rtl min_ripple_len 64
set_param rtl infer_fsm sequential
optimize_rtl
set_param gate map_mode area_prior
set_param gate pack_effort high
optimize_gate -packarea isolated.area
puts "PRIVATE_BOUNDED_POINT_GATE_PASS"
} message]} {puts stderr "PRIVATE_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
'''.replace('OUT',out.as_posix()).replace('PROJECT',project.as_posix()))
    with (out/'td.log').open('x',encoding='utf-8') as log:p=subprocess.run([td,script.as_posix()],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert p.returncode==0,(label,out)
    assert all(sha(R/n)==h for n,h in inputs.items())
    text=(out/'isolated.area').read_text();resources={n:int(re.search(r'^\s*#'+n+r'\*?\s+(\d+)',text,re.M)[1]) for n in ('slice','lut6','reg','eram','dsp')}
    result[label]=dict(directory=out.relative_to(R).as_posix(),inputs=inputs,resources=resources)
    print('PRIVATE_BOUNDED_POINT_GATE_DONE',label,resources,flush=True)
with (O/('gate_comparison_'+stamp+'.json')).open('x',encoding='utf-8') as f:json.dump(dict(scope='CONNECTED LOCAL ESTIMATES ONLY; NOT ADOPTED OR A WHOLE-DEVICE RESULT',outputs=result,producer_sha256=sha(Path(__file__)),wrapper_sha256=sha(wrapper_source)),f,indent=2)
