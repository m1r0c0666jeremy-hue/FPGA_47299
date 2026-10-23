"""Quantify the private data-reset candidate after formal TD ends; no parallel TD."""
from pathlib import Path
import copy,datetime,hashlib,json,os,re,subprocess,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;R=O.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
active=subprocess.check_output(['powershell','-NoProfile','-Command','@(Get-Process -Name td_commands_prompt -ErrorAction SilentlyContinue).Count'],text=True).strip()
assert active=='0','Wait for the active formal TD; do not run a second TD'
proof=json.loads((O/'validation.json').read_text());assert len(proof['checks'])==4
assert sha(O/'probe.py')==proof['producer_sha256'] and sha(O/'stage1_render.v')==proof['candidate_sha256']
assert all(sha(R/n)==h for n,h in proof['unchanged_formal_inputs'].items())
markers={'math_14_14':'STAGE1_ARITH_PASS width=14 divisor=14 cases=2049','stage1_regions':'STAGE1_EDIT_RENDER_PASS point_pixels=134400',
         'stage1_render_guards':'STAGE1_RENDER_GUARDS_PASS','stage1_render_14_624':'STAGE1_RENDER_PASS cases=14 pixels=11182080',
         'stage1_overlay':'STAGE1_OVERLAY_PASS cases=8 pixels=6389760'}
for label,e in proof['checks'].items():
    assert sha(R/e['record'])==e['record_sha256'] and sha((R/e['record']).with_suffix('.log'))==e['log_sha256']
    assert sha(R/e['bench'])==e['bench_sha256']
    assert all(sha(R/n)==h for k in ('inputs','fixtures','producers') for n,h in e.get(k,{}).items())
    log=(R/e['record']).with_suffix('.log').read_text();assert markers[label] in log
    if label=='stage1_regions':assert 'STAGE1_REGIONS_PASS' in log
# Compare the exact controller and valid coordinates including reset interruptions.
equivalence=O/'equivalence_validation.json';eq=json.loads(equivalence.read_text())
assert sha(O/'compare.py')==eq['producer_sha256']
assert sha(R/eq['record'])==eq['record_sha256'] and sha((R/eq['record']).with_suffix('.log'))==eq['log_sha256']
assert sha(R/eq['bench'])==eq['bench_sha256']
assert all(sha(R/n)==h for n,h in eq['inputs'].items())
assert all(sha(R/n)==h for g in ('fixtures','producers') for n,h in eq[g].items())
assert 'PRIVATE_VALID_DATA_CONTROL_EQUIVALENCE_PASS' in (R/eq['record']).with_suffix('.log').read_text()
assert sha(O/'stage1_regions.v')==proof['regions_candidate_sha256']

td=Path('D:/26_software/TangDynasty/bin/td_commands_prompt.exe');env=os.environ.copy();env['PATH']=str(td.parent)+os.pathsep+env.get('PATH','')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
A=R/'build/stage1_valid_data_resetfree_20261024_0014'
prior_files=list(A.glob('gate_comparison_*.json'));assert len(prior_files)==1
prior_file=prior_files[0];prior=json.loads(prior_file.read_text());base=prior['outputs']['baseline'];bd=R/base['directory']
assert all(sha(R/n)==v for n,v in base['inputs'].items())
assert sha(bd/'isolated_netlist.v')==base['netlist_sha256'] and sha(bd/'isolated_gate.db')==base['checkpoint_sha256']
assert sha(bd/'td.log')==base['log_sha256']
result={'baseline':base}

wrapper_source=R/'build/stage1_split_draft_20261022_1833/gate_split_shared_stamp_20261022_192541/serial_wrapper.v'
assert sha(wrapper_source)=='604def53b2d9c23070b2d820bea3fef9061a8b33a782103b61ddf55dd620b670'
for label in ('valid_storage',):
    out=O/('gate_'+label+'_'+stamp);out.mkdir(exist_ok=False);sources=out/'sources';sources.mkdir()
    wrapper=out/'serial_wrapper.v';wrapper.write_bytes(wrapper_source.read_bytes());mods=[wrapper];inputs={}
    for name in ('stage1_arith','stage1_sequence','stage1_point','stage1_segment','stage1_validate','stage1_regions','stage1_render'):
        original=O/(name+'.v') if label=='valid_storage' and name in ('stage1_render','stage1_regions') else R/'rtl/color_regions'/(name+'.v')
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
export_db isolated_gate.db
write_verilog isolated_netlist.v
if {[catch {report_hfn gate} e]} {puts "HFN_REPORT_UNAVAILABLE: $e"}
puts "PRIVATE_VALID_DATA_GATE_PASS"
} message]} {puts stderr "PRIVATE_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
'''.replace('OUT',out.as_posix()).replace('PROJECT',project.as_posix()))
    with (out/'td.log').open('x',encoding='utf-8') as log:p=subprocess.run([td,script.as_posix()],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert p.returncode==0,(label,out)
    assert all(sha(R/n)==h for n,h in inputs.items())
    text=(out/'isolated.area').read_text();resources={n:int(re.search(r'^\s*#'+n+r'\*?\s+(\d+)',text,re.M)[1]) for n in ('slice','lut6','reg','eram','dsp')}
    result[label]=dict(directory=out.relative_to(R).as_posix(),inputs=inputs,resources=resources,netlist_sha256=sha(out/'isolated_netlist.v'),checkpoint_sha256=sha(out/'isolated_gate.db'),log_sha256=sha(out/'td.log'))
    print('PRIVATE_VALID_DATA_GATE_DONE',label,resources,flush=True)
with (O/('gate_comparison_'+stamp+'.json')).open('x',encoding='utf-8') as f:json.dump(dict(scope='CONNECTED LOCAL ESTIMATES ONLY; NOT ADOPTED OR A WHOLE-DEVICE RESULT',outputs=result,baseline_comparison=prior_file.relative_to(R).as_posix(),baseline_comparison_sha256=sha(prior_file),producer_sha256=sha(Path(__file__)),wrapper_sha256=sha(wrapper_source),validation_sha256=sha(O/'validation.json'),equivalence_sha256=sha(equivalence),reference=proof['reference'],reference_sha256=proof['reference_sha256']),f,indent=2)
