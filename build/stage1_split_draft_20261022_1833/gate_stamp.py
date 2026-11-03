"""Connected editor/render estimates only. Refuse to run beside any active TD."""
from pathlib import Path
import copy,datetime,json,os,re,subprocess,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;R=O.parents[1];P=R/'build/stage1_shared_vertex_20261022'
active=subprocess.run(['powershell','-NoProfile','-Command',
  '@(Get-Process -Name td_commands_prompt -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True,check=True)
assert active.stdout.strip()=='0','Wait for the current formal TD to finish; no parallel TD probe'
td=Path('D:/26_software/TangDynasty/bin/td_commands_prompt.exe')
env=os.environ.copy();env['PATH']=str(td.parent)+os.pathsep+env.get('PATH','')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');result={}
for label in ('split_shared_stamp',):
    out=O/('gate_'+label+'_'+stamp);out.mkdir(exist_ok=False)
    split=label!='baseline';shared=label in ('split_shared','split_shared_stamp')
    extra=',saved,draft' if split else ''
    renderer='stage1_render #(.SPLIT_DRAFT(1))' if split else 'stage1_render'
    data='saved' if split else 'draw'
    trailing=",draft,n,nd!=0" if split else ''
    wrapper=out/'serial_wrapper.v'
    wrapper.write_text('''module serial_wrapper(input clk,rst,input [7:0] data,output observe);
reg [821:0] s;always @(posedge clk or negedge rst)if(!rst)s<=0;else s<={s[813:0],data};
wire [2:0] n,expected,actual;wire [3:0] nd,closed,state,completed,occupied,ee,se;wire [15:0] revision,counts;
wire [671:0] draw,saved;wire [167:0] draft;wire muted,alarm,busy,live,mvalid;wire [1:0] trend;wire [10:0] distance;wire [19:0] dwell;
stage1_regions editor(clk,rst,s[1:0],s[2],s[3],s[4],s[5],s[6],s[7],s[8],s[9],s[10],s[18:11],s[19],s[20],s[21],s[53:22],s[821:54],
n,nd,revision,draw,counts,closed,state,completed,occupied,expected,actual,muted,alarm,trend,distance,dwell,ee,se,busy,live,mvalidEXTRA);
wire [3:0] mask;wire [23:0] color,label_color;wire label_on,ready,under;wire [7:0] glyph;wire [2:0] gx;wire [3:0] gy;
RENDER picture(clk,rst,s[20],VERTICES,counts,closed,s[1:0],s[64:54],s[74:65],s[77:75],s[78],state,completed,expected,actual,
s[89:79],s[99:90],s[100],mask,color,label_on,glyph,gx,gy,label_color,ready,underTRAILING);
assign observe=^{n,nd,revision,counts,closed,state,completed,occupied,expected,actual,muted,alarm,trend,distance,dwell,ee,se,busy,live,mvalid,
mask,color,label_on,glyph,gx,gy,label_color,ready,under};endmodule
'''.replace('EXTRA',extra).replace('RENDER',renderer).replace('VERTICES',data).replace('TRAILING',trailing),encoding='utf-8')
    root=ET.fromstring((R/'td_project/target_color_regions_stage1.al').read_text().replace('&','&amp;').replace('::','__COLON__'))
    root.set('Path',out.as_posix());template=copy.deepcopy(root.find('./Source_Files/Verilog/File'))
    for group in root.findall('./Source_Files/*'):
        for node in list(group):group.remove(node)
    mods=[wrapper]
    for n in ('stage1_arith','stage1_sequence','stage1_point','stage1_segment','stage1_validate','stage1_regions','stage1_render'):
        if n=='stage1_regions' and split:p=O/('stage1_regions_shared.v' if shared else 'stage1_regions.v')
        elif n=='stage1_render' and split:p=O/'stage1_render_stamp.v'
        elif shared and n in ('stage1_point','stage1_validate'):p=P/(n+'.v')
        else:p=R/'rtl/color_regions'/(n+'.v')
        mods.append(p)
    for i,p in enumerate(mods):
        node=copy.deepcopy(template);node.set('Path',p.as_posix());root.find('./Source_Files/Verilog').append(node)
        for a in node.findall('./FileInfo/Attr'):
            if a.get('Name')=='CompileOrder':a.set('Val',str(i))
    project=out/'target_color_regions_stage1.al'
    project.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode').replace('&amp;','&').replace('__COLON__','::'))
    script=out/'run.tcl'
    script.write_text('''if {[catch {
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
puts "PRIVATE_SPLIT_GATE_PASS"
} message]} {puts stderr "PRIVATE_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
'''.replace('OUT',out.as_posix()).replace('PROJECT',project.as_posix()))
    with (out/'td.log').open('x',encoding='utf-8') as f:
        p=subprocess.run([td,script.as_posix()],cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT)
    assert p.returncode==0,(label,out)
    text=(out/'isolated.area').read_text()
    resources={n:int(re.search(r'^\s*#'+n+r'\*?\s+(\d+)',text,re.M)[1]) for n in ('slice','lut6','reg','eram','dsp')}
    result[label]=dict(directory=out.relative_to(R).as_posix(),resources=resources)
    print('PRIVATE_SPLIT_GATE_DONE',label,resources,flush=True)
(O/'gate_stamp_comparison.json').write_text(json.dumps(dict(scope='CONNECTED EDITOR/RENDER ESTIMATES ONLY; no board candidate',outputs=result),indent=2))
