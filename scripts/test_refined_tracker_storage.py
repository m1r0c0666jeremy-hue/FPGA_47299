"""Private before/after output equivalence with a held candidate transaction."""
from pathlib import Path
import argparse,sys,xml.etree.ElementTree as ET
from refined_testlib import R,run
from refined_tracker_storage import tracker_asset
ap=argparse.ArgumentParser();ap.add_argument('--build',choices=['place']);ap.add_argument('--flow',action='store_true')
ap.add_argument('--capture-contract',action='store_true')
ap.add_argument('--production',action='store_true')
ap.add_argument('--official-syn',choices=['AreaOptimizeMedium','AreaOptimizeHigh'])
ap.add_argument('--official-phy',choices=['CongestionMedium','CongestionHigh','TimingHigh','TimingUltra']);a=ap.parse_args()
out=R/'build/refined_tracker_storage_prototype';out.mkdir(exist_ok=True)
base=R/'rtl/color_regions/stable_tracker.v';candidate=out/'stable_tracker.v';reference=out/'reference.v'
baseline=R/'scripts/refined_tracker_storage_base.v.txt' if a.production else base
for path,data in ((candidate,tracker_asset(baseline.read_text(encoding='utf-8'))),(reference,baseline.read_text(encoding='utf-8').replace('module stable_tracker(','module reference_tracker('))):
    data=data.encode()
    if path.exists():assert path.read_bytes()==data
    else:path.write_bytes(data)
if a.production:
    assert not (a.capture_contract or a.flow or a.build),'Production uses the formal integration fixtures'
    assert base.read_bytes()==candidate.read_bytes(),'Production tracker differs from verified transform'
    candidate=base
if a.capture_contract:
    path=R/'scripts/test_refined_history.py';s=path.read_text(encoding='utf-8')
    old='from refined_testlib import R,run,literal_fixture';assert s.count(old)==1
    s=s.replace(old,'from refined_testlib import R,literal_fixture\nrun=private_run')
    def private_run(name,tb,modules):
        if name not in ('history_full_rgb_after','capture_diagnostics_v4'):return
        assert 'stable_capture' in tb and ' dut(' in tb
        monitor='''
reg candidate_hold_active=0;reg [1023:0] candidate_hold_value=0;integer candidate_hold_checks=0;
always @(posedge dut.clk)begin
 if(!dut.rst_n)candidate_hold_active<=0;
 else begin
  if(candidate_hold_active)begin
   if(dut.candidates!==candidate_hold_value || dut.gs)$fatal(1,"capture changed candidate bus before tracker done");
   candidate_hold_checks=candidate_hold_checks+1;
  end
  if(dut.ts)begin candidate_hold_active<=1;candidate_hold_value<=dut.candidates;end
  if(dut.td)candidate_hold_active<=0;
 end
end
final begin
 if(candidate_hold_checks==0)$fatal(1,"candidate hold contract not exercised");
 $display("CAPTURE_CANDIDATE_HOLD_PASS checked%0d source clocks",candidate_hold_checks);
end
'''
        assert tb.count('endmodule')==1
        if 'reg candidate_hold_active=' not in tb:tb=tb.replace('endmodule',monitor+'\nendmodule')
        return run('tracker_storage_'+name+'_contract',tb,[candidate if p==base else p for p in modules])
    exec(compile(s,str(path),'exec'),dict(__file__=str(path),__name__='__main__',private_run=private_run));raise SystemExit(0)
if a.flow:
    path=R/'scripts/test_refined_tracker.py';s=path.read_text(encoding='utf-8')
    old='from refined_testlib import R,run,literal_fixture';assert s.count(old)==1
    s=s.replace(old,'from refined_testlib import R,literal_fixture\nrun=private_run')
    def private_run(name,tb,modules):
        return run('tracker_storage_'+name,tb,[candidate if p==base else p for p in modules])
    exec(compile(s,str(path),'exec'),dict(__file__=str(path),__name__='__main__',private_run=private_run));raise SystemExit(0)
if a.build:
    original=R/'td_project/target_color_regions_refined.al'
    tree=ET.fromstring(original.read_text(encoding='utf-8').replace('&','&amp;').replace('::','__TD_COLON__'))
    for node in tree.findall('./Source_Files/*/File'):
        p=(original.parent/node.attrib['Path']).resolve();node.set('Path',(candidate if p.name==candidate.name else p).as_posix())
    project=out/'prototype.al';project_data=('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n').encode('utf-8')
    if project.exists():assert project.read_bytes().replace(b'\r\n',b'\n')==project_data,'Private project changed; preserve it'
    else:project.write_bytes(project_data)
    path=R/'scripts/run_refined_build.py';s=path.read_text(encoding='utf-8')
    assert s.count("project=R/'td_project/target_color_regions_refined.al'")==1
    s=s.replace("project=R/'td_project/target_color_regions_refined.al'","project=prototype_project").replace("f'refined_{a.stage}_{stamp}'","f'refined_tracker_storage_{a.stage}_{stamp}'")
    sys.argv=[str(path),'--stage','place','--map-mode','area_prior','--pack-effort','high','--checkpoint']
    for key,flag in (('official_syn','--official-syn'),('official_phy','--official-phy')):
        if getattr(a,key):sys.argv += [flag,getattr(a,key)]
    exec(compile(s,str(path),'exec'),dict(__file__=str(path),__name__='__main__',prototype_project=project));raise SystemExit(0)
ports=[('done',1),('a',128),('b',128),('tip_valid',1),('tip_x',11),('tip_y',10),('reason',4),('history_valid',1),('history_boxes',84),('selection_state',2),('history_command',10),('history_revision',16),('history_frame',32),('history_loss',5),('tip_bounds',4)]
def inst(module,name,bus):
    fields=['.clk(clk)','.rst_n(rst)','.start(start)','.frame_id(id)','.command(command)','.revision(revision)','.complete(complete)','.candidates(candidates)'];offset=0
    for port,width in ports:
        fields.append(f'.{port}({bus}[{offset+width-1}:{offset}])');offset+=width
    assert offset==437
    return module+' '+name+'('+','.join(fields)+');'
tb=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0,complete=1;
reg [31:0] id=0,rng=32'h47299;reg [9:0] command=3;reg [15:0] revision=0;
reg [1023:0] candidates=0;wire [436:0] g,d;integer f,j,k,n,tips=0,checks=0;reg [15:0] reasons=0;
INSTANCES
task tick;begin @(negedge clk);if(g!==d)$fatal(1,"tracker storage output mismatch f%0d gstate%0d dstate%0d pair%0d/%0d g%h d%h",f,gold.state,dut.state,gold.pair_index,dut.pair_index,g,d);checks=checks+1;end endtask
function [31:0] random32;begin rng=rng*1664525+1013904223;random32=rng;end endfunction
function [127:0] object(input integer x,y);reg [127:0] v;begin
v={random32(),random32(),random32(),random32()};v[120]=1;v[61:42]=48+(rng%4000);v[89:83]=rng%101;
v[72:62]=x;v[82:73]=y;v[41:0]={10'd600,10'd32,11'd1000,11'd64};object=v;end endfunction
initial begin repeat(4)tick;rst=1;
for(f=0;f<3000;f=f+1)begin
 if(f>100 && f%137==0)begin rst=0;repeat(3)tick;rst=1;end
 if(f==200)begin rst=0;repeat(2)tick;rst=1;id=32'hfffffffe;end
 if(f<=100 || f%11!=0)id=id+1;
 if(f>100 && f%23==0)id=id+20;
 if(f>100 && f%31==0)id=id-2;
 if(f>100 && f%157==0)revision=revision+1;
 command=(f>100 && f%43==0)?0:3;complete=!(f>100 && f%47==0);
 candidates=0;
 for(j=0;j<8;j=j+1)begin
  candidates[j*128+:128]=object(random32()%1280,random32()%720);
  candidates[j*128+120]=(f>100 && (rng%3)!=0);
 end
 candidates[((f/7)%4)*128+:128]=object(600+(f%16),300);
 candidates[(4+(f/11)%4)*128+:128]=object(700+(f%16),400);
 if(f>100 && f%53==0)for(j=0;j<4;j=j+1)candidates[j*128+120]=0;
 if(f>100 && f%59==0)for(j=4;j<8;j=j+1)candidates[j*128+120]=0;
 start=1;tick;start=0;n=0;
 while(!gold.done && n<150)begin tick;n=n+1;end
 if(!gold.done)$fatal(1,"tracker storage completion timeout");
 if(gold.tip_valid)tips=tips+1;reasons[gold.reason]=1;tick;
end
if(tips<10 || !reasons[8])$fatal(1,"insufficient transaction coverage tips%0d reasons%h",tips,reasons);
$display("TRACKER_STORAGE_PRIVATE_PASS 3000 held-input transactions, %0d cycles all437 external bits equal, tips%0d reasons%h; not production",checks,tips,reasons);$finish;
end endmodule'''.replace('INSTANCES',inst('reference_tracker','gold','g')+'\n'+inst('stable_tracker','dut','d'))
if a.production:tb=tb.replace('TRACKER_STORAGE_PRIVATE_PASS','TRACKER_STORAGE_EQUIVALENCE_PASS').replace('; not production','; canonical production with held candidate input')
run('tracker_storage_equivalence' if a.production else 'tracker_storage_private',tb,[reference,candidate])
