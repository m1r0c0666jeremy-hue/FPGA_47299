"""Isolated area estimate of the complete editor/point/validation/sequence block."""
from pathlib import Path
import datetime,json,os,subprocess,copy,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;R=O.parents[1]
wrapper=O/'serial_wrapper.v'
wrapper.write_text('''module serial_wrapper(input clk,rst,input [7:0] data,output observe);
reg [821:0] s;always @(posedge clk or negedge rst)if(!rst)s<=0;else s<={s[813:0],data};
wire [2:0] n,expected,actual;wire [3:0] nd,closed,state,completed,occupied,ee,se;wire [15:0] revision,counts;
wire [671:0] vertices;wire muted,alarm,busy,live,mvalid;wire [1:0] trend;wire [10:0] distance;wire [19:0] dwell;
stage1_regions dut(clk,rst,s[1:0],s[2],s[3],s[4],s[5],s[6],s[7],s[8],s[9],s[10],s[18:11],s[19],s[20],s[21],s[53:22],s[821:54],
n,nd,revision,vertices,counts,closed,state,completed,occupied,expected,actual,muted,alarm,trend,distance,dwell,ee,se,busy,live,mvalid);
assign observe=^{n,nd,revision,vertices,counts,closed,state,completed,occupied,expected,actual,muted,alarm,trend,distance,dwell,ee,se,busy,live,mvalid};endmodule
''')
td=Path('D:/26_software/TangDynasty/bin/td_commands_prompt.exe');env=os.environ.copy();env['PATH']=str(td.parent)+os.pathsep+env.get('PATH','')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');result={}
for label in ('baseline','shared'):
    out=O/('gate_'+label+'_'+stamp);out.mkdir(exist_ok=False)
    root=ET.fromstring((R/'td_project/target_color_regions_stage1.al').read_text().replace('&','&amp;').replace('::','__COLON__'))
    root.set('Path',out.as_posix());template=copy.deepcopy(root.find('./Source_Files/Verilog/File'))
    for group in root.findall('./Source_Files/*'):
        for node in list(group):group.remove(node)
    mods=[wrapper]
    for n in ('stage1_arith','stage1_sequence','stage1_point','stage1_segment','stage1_validate','stage1_regions'):
        p=O/(n+'.v') if label=='shared' and (O/(n+'.v')).is_file() else R/'rtl/color_regions'/(n+'.v')
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
puts "PRIVATE_SHARED_GATE_PASS"
} message]} {puts stderr "PRIVATE_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
'''.replace('OUT',out.as_posix()).replace('PROJECT',project.as_posix()))
    with (out/'td.log').open('x',encoding='utf-8') as f:r=subprocess.run([td,script.as_posix()],cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT)
    assert r.returncode==0,label
    result[label]=out.relative_to(R).as_posix();print('PRIVATE_SHARED_GATE_DONE',label,flush=True)
(O/'gate_comparison.json').write_text(json.dumps(dict(scope='ISOLATED ESTIMATES ONLY; no board candidate',outputs=result),indent=2))
