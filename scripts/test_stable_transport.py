"""Real v2 banks/mailboxes/viewports/first requests, plus moving-window guards."""
from pathlib import Path
import os,subprocess
R=Path(__file__).resolve().parents[1];O=R/'build/sim/stable_transport';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','');logs=[]
def transform(s):
    s=s.replace('tb_color_regions_','tb_stable_')
    for a,b in [('regions_frame_store','stable_frame_store'),('regions_display','stable_display'),('regions_line_reader','stable_line_reader'),
                ('[450:0]','[674:0]'),('[449:448]','[673:672]'),('[447:416]','[671:640]'),('[450]','[674]'),('[415:0]','[639:0]'),
                ("416'd0","640'd0"),('.WIDTH(416)','.WIDTH(640)'),('.WIDTH(451)','.WIDTH(675)'),('[415:413]=1','[415:413]=2')]:s=s.replace(a,b)
    return s.replace('tb_color_regions_','tb_stable_')
for name in ['frame_store','display','association']:
    s=transform((R/f'sim/tb_color_regions_{name}.sv').read_text(encoding='utf-8'))
    if name=='display':
        s=s.replace('$display("PASS display', '''live=1;tracking=1;session=3;pair=0;zoom=2;packet(13,1,1,1);data[32]=1;data[89:79]=900;data[99:90]=500;blank;
if(cx!=664 || cy!=384)$fatal(1,"window max step");
packet(14,1,1,1);data[32]=1;data[89:79]=900;data[99:90]=500;blank;if(cx!=688 || cy!=408)$fatal(1,"second window step");
blank;if(cx!=688 || cy!=408)$fatal(1,"duplicate frame moved viewport");
packet(15,1,1,1);data[32]=1;data[89:79]=691;data[99:90]=411;blank;if(cx!=688 || cy!=408)$fatal(1,"deadzone");
packet(16,1,1,1);blank;if(cx!=688 || cy!=408)$fatal(1,"loss did not freeze");
tracking=0;session=4;mode=3;packet(17,1,0,0);data[567:566]=1;blank;
if(cx!=640 || cy!=360 || x0!=0 || y0!=48 || oz!=0 || om!=0)$fatal(1,"calibration guide off-screen");
packet(18,1,0,0);blank;if(oz!=2 || om!=3 || cx!=640 || cy!=360)$fatal(1,"requested page/zoom not restored after calibration");
$display("PASS stable moving display: 24px max-step, 4px deadzone, missing tip freeze, duplicate suppression");
$display("PASS display''')
    if name=='association':
        s=s.replace("ob,oi,1'b1,rdvalid","ob,oi,active[543:416],1'b1,rdvalid").replace('ode,rgb,ok);','ode,rgb,,ok);')
        s=s.replace('reader.frame_id_d','reader.image_id').replace('base(b)+48*1920','base(b)+47*1920').replace('repeat(1000)','repeat(10000)')
        s=s.replace('416/451-bit','640/675-bit')
    file=O/(name+'.sv');file.write_text(s,encoding='utf-8');exe=O/(name+'.vvp')
    files=[R/f'rtl/color_regions/{n}.v' for n in ('stable_frame_store','stable_display','stable_line_reader','stable_model_lane','stable_filter4')]+[R/'rtl/04_tracking/target_mailbox.v']
    for cmd in ([iv,'-g2012','-s','tb_stable_'+name,'-o',exe,file,*files],[iv.with_name('vvp.exe'),exe]):
        q=subprocess.run(list(map(str,cmd)),cwd=R,env=env,capture_output=True,text=True,timeout=180);logs.append(q.stdout+q.stderr);print(logs[-1],flush=True)
        (R/'reports/transparent_ring/regression/stable_transport.log').write_text('\n'.join(logs),encoding='utf-8')
        if q.returncode:raise SystemExit(q.returncode)
print('STABLE_TRANSPORT_ALL_PASS',flush=True)
