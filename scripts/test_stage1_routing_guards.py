"""Check the delivery routing gate against a real completed log and damaged copies."""
from pathlib import Path
import datetime,json,re,zipfile
from audit_stage1 import R,ARCHIVE,routing_audit,sha


def main():
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    root=R/'build'/('stage1_routing_guards_'+stamp);root.mkdir(exist_ok=False)
    assert sha(ARCHIVE)=='9ec0eb66550b2c67db809c6ce4e5cc69258b0187d89d891bf0f99f6469ead9d3'
    member='build/refined_route_20261019_232845_179508/td.log'
    original=root/'known_completed.log'
    with zipfile.ZipFile(ARCHIVE) as z:original.write_bytes(z.read(member))
    text=original.read_text(encoding='utf-8')
    accepted=routing_audit(original)
    last=list(re.finditer(r'over cnt = 0\(0%\), over = 0, worst = 0',text))[-1]
    copies={
      'late_conflict':text[:last.start()]+text[last.start():last.end()].replace('over cnt = 0','over cnt = 1').replace('over = 0','over = 1').replace('worst = 0','worst = 1')+text[last.end():],
      'missing_drc':text[:text.index('PHY-1001 : Stage 5 | Routing DRC')],
      'multi_drive':text.replace('No multi-drive.','Multi-drive found.'),
      'abnormal_path':text.replace('No abnormal timing path.','Abnormal timing path found.'),
      'bound_failed':text.replace('Check Pass.','Check Failed.'),
      'incomplete_build':text.replace('REFINED_CHECKPOINT_FULL_COMPLETED','INCOMPLETE'),
    }
    outcomes={};fixtures={original.relative_to(R).as_posix():sha(original)}
    for label,damaged in copies.items():
        path=root/(label+'.log');path.write_text(damaged,encoding='utf-8')
        try:routing_audit(path)
        except AssertionError:outcomes[label]='REJECTED'
        else:raise AssertionError('Unsafe routing log accepted: '+label)
        fixtures[path.relative_to(R).as_posix()]=sha(path)
    current=R/'build/stage1_route_20261024_125519_122210/td.log'
    current_text=current.read_text(encoding='utf8')
    current_accepted=routing_audit(current)
    last=list(re.finditer(r'over cnt = 0\(0%\), over = 0, worst = 0',current_text))[-1]
    candidate_copies={
      'late_conflict':current_text[:last.start()]+current_text[last.start():last.end()].replace('over cnt = 0','over cnt = 1').replace('over = 0','over = 1').replace('worst = 0','worst = 1')+current_text[last.end():],
      'missing_drc':current_text[:current_text.index('PHY-1001 : Stage 11 | Routing DRC')],
      'multi_drive':current_text.replace('No multi-drive.','Multi-drive found.'),
      'abnormal_path':current_text.replace('No abnormal timing path.','Abnormal timing path found.'),
      'bound_failed':current_text.replace('Check Pass.','Check Failed.'),
      'incomplete_build':current_text.replace('REFINED_CHECKPOINT_FULL_COMPLETED','INCOMPLETE'),
      'wrong_drc_end':current_text.replace('End Stage 11 | Routing DRC;','End Stage 5 | Routing DRC;'),
      'wrong_bound_stage':current_text.replace('Stage 11.6 | Bound Check','Stage 5.6 | Bound Check'),
    }
    current_outcomes={}
    for label,damaged in candidate_copies.items():
        path=root/('current_'+label+'.log');path.write_text(damaged,encoding='utf8')
        try:routing_audit(path)
        except AssertionError:current_outcomes[label]='REJECTED'
        else:raise AssertionError('Unsafe current routing log accepted: '+label)
        fixtures[path.relative_to(R).as_posix()]=sha(path)
    fixtures[current.relative_to(R).as_posix()]=sha(current)
    result=dict(status='ROUTING_GUARDS_PASS',archive=ARCHIVE.relative_to(R).as_posix(),archive_member=member,
                auditor_sha256=sha(R/'scripts/audit_stage1.py'),producer_sha256=sha(Path(__file__)),
                known_completed_log=original.relative_to(R).as_posix(),known_completed_log_sha256=sha(original),
                accepted=accepted,checks=outcomes,fixtures=fixtures,
                current_candidate=current.relative_to(R).as_posix(),current_accepted=current_accepted,current_checks=current_outcomes,
                scope='Artificial damaged log copies only; not current candidate or functional evidence')
    report=R/'reports/stage1'/('routing_guards_'+stamp+'.json')
    report.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('STAGE1_ROUTING_GUARDS_PASS',report.relative_to(R),outcomes)


if __name__=='__main__':main()
