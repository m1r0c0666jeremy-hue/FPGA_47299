"""Reject unsafe project changes while retaining the reviewed user's TD save."""
from refined_testlib import R,run
import stage1_project,generate_stage1,datetime,hashlib,json

def main():
    p=R/'td_project/target_color_regions_stage1.al';before=p.read_bytes();expected=[]
    original=stage1_project.check_project
    def capture(path,wanted):expected.append(wanted);return original(path,wanted)
    stage1_project.check_project=capture
    try:generate_stage1.assets()
    finally:stage1_project.check_project=original
    text=before.decode('utf-8');folder=R/'build'/('stage1_project_cases_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'));folder.mkdir()
    cases={
        'device':text.replace('PH1P35MDG324','PH1P25MDG324'),
        'top':text.replace('criticalwork_top','wrong_top'),
        'constraint':text.replace('target_lock.sdc','wrong.sdc'),
        'dependency':text.replace('stage1_regions.v','missing_regions.v'),
        'enabled':text.replace('Name="UsedInSyn" Val="true"','Name="UsedInSyn" Val="false"',1),
        'exclusion':text.replace('Name="AutoExcluded" Val="true"','Name="AutoExcluded" Val="false"',1),
    }
    for name,value in cases.items():
        assert value!=text,name
        q=folder/(name+'.al');q.write_text(value,encoding='utf-8')
        try:original(q,expected[0])
        except AssertionError:pass
        else:raise AssertionError('Unsafe project accepted '+name)
    q=folder/'formatting.al';q.write_text(text.replace('    ','  '),encoding='utf-8');original(q,expected[0])
    assert p.read_bytes()==before,'User project overwritten'
    out=run('stage1_project_guards','module tb;initial begin $display("STAGE1_PROJECT_GUARDS_PASS six-negative/formatting/user-bytes-preserved");$finish;end endmodule',[],timeout=120)
    report=R/'reports/refined/regression'/(out.name+'.json');d=json.loads(report.read_text())
    for n in ('scripts/stage1_project.py','scripts/generate_stage1.py','scripts/stage1_behavior_ui.py','td_project/target_color_regions_stage1.al'):
        d['fixture_inputs'][n]=hashlib.sha256((R/n).read_bytes()).hexdigest()
    for f in folder.iterdir():d['fixture_inputs'][f.relative_to(R).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
    report.write_text(json.dumps(d,indent=2),encoding='utf-8')

if __name__=='__main__':main()
