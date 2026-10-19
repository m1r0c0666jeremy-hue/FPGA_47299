"""Verify the immutable provenance of a failed formal routing checkpoint."""
from pathlib import Path
import hashlib,json,re
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def clock_periods(path):
    pairs=set();columns=None
    for line in path.read_text(encoding='utf-8').splitlines():
        if '|' not in line:continue
        cells=[v.strip() for v in line.split('|')]
        if 'Clock Period' in cells and 'Clock' in cells:
            columns=cells.index('Clock Period'),cells.index('Clock');continue
        if columns and len(cells)>max(columns):
            period,name=cells[columns[0]],cells[columns[1]]
            if re.fullmatch(r'\d+\.\d+',period) and name:pairs.add((name,period))
    return pairs

def verify_source(root,source,probe,canonical,signature):
    source=source.resolve();probe=probe.resolve()
    assert source.is_relative_to(root/'build') and probe.is_relative_to(root/'build')
    before=json.loads((source/'inputs.json').read_text(encoding='utf-8'));canonical(before)
    assert all(sha(root/name)==value and sha(source/'compiled_source'/name)==value for name,value in before.items())
    ctx=json.loads((source/'source_context.json').read_text(encoding='utf-8'))
    assert ctx['input_count']==len(before) and ctx['inputs_sha256']==sha(source/'inputs.json')
    saved=json.loads((source/'normal_failure_checkpoint.json').read_text(encoding='utf-8'))
    assert saved['stage']=='NORMAL_ROUTE_FAILED_CHECKPOINT_NOT_A_DELIVERABLE'
    assert saved['compiled_source_commit']==ctx['compiled_source_commit'] and saved['frozen_input_count']==len(before)
    assert saved['inputs_sha256']==sha(source/'inputs.json') and saved['source_context_sha256']==sha(source/'source_context.json')
    assert saved['parent_provenance_sha256']==sha(source/'checkpoint_provenance.json')
    prefix=(source/'normal_failure_prefix.log').read_bytes()
    assert hashlib.sha256(prefix).hexdigest()==saved['prefix_sha256']
    assert (source/'td.log').read_bytes().startswith(prefix)
    assert b'PHY-8080 ERROR' in prefix and b'ROUTE_NORMAL_FAILED_RETRY_ROUTABILITY' in prefix
    assert b'finish command "export_db failed_normal_route.db"' in prefix and b'FAILED_NORMAL_DB_SAVE_FAILED' not in prefix
    assert sha(source/'failed_normal_route.db')==saved['checkpoint_sha256'],'Failed routing checkpoint SHA mismatch'
    initial=json.loads((source/'checkpoint_provenance.json').read_text(encoding='utf-8'))
    parent=(root/initial['parent']).resolve();assert parent.is_relative_to(root/'build')
    ps=json.loads((parent/'summary.json').read_text(encoding='utf-8'))
    assert ps['stage']=='place' and ps['exit_code']==0 and ps['resource_pass'] and ps['inputs_unchanged']
    assert ps.get('official_strategy') is None,'Fresh continuation currently verified for the plain strategy parent only'
    assert sha(parent/'summary.json')==initial['parent_summary_sha256']
    assert sha(parent/'source_context.json')==initial['parent_context_sha256']
    assert sha(parent/'inputs.json')==initial['parent_inputs_sha256']==sha(source/'inputs.json')
    assert sha(parent/initial['checkpoint_name'])==initial['checkpoint_sha256']==ps['checkpoints'][initial['checkpoint_name']]
    assert before==json.loads((parent/'inputs.json').read_text())==json.loads((parent/'inputs_after.json').read_text())
    assert all(sha(parent/'compiled_source'/name)==value for name,value in before.items())
    assert ctx['compiled_source_commit']==json.loads((parent/'source_context.json').read_text())['compiled_source_commit']
    assert 'CHECKPOINT_CONSTRAINT_ROUNDTRIP_PASS' in prefix.decode('utf-8')
    for name in ('placed_clocks.txt','placed_exceptions.timing'):
        assert signature(source/name,parent,source)==signature(parent/name,parent,source)
    probe_summary=json.loads((probe/'summary.json').read_text(encoding='utf-8'))
    assert probe_summary['probe_only'] and probe_summary['exit_code']==0 and probe_summary['checkpoint_unchanged']
    assert probe_summary['checkpoint_sha256']==saved['checkpoint_sha256']
    assert probe_summary['source_attempt']==source.relative_to(root).as_posix()
    assert f'import_db {{{(source/"failed_normal_route.db").as_posix()}}}' in (probe/'run.tcl').read_text(encoding='utf-8')
    assert 'FAILED_CHECKPOINT_READONLY_PROBE_PASS' in (probe/'td.log').read_text(encoding='utf-8')
    periods=clock_periods(source/'placed_clocks.txt');restored=clock_periods(probe/'restored_clocks.txt')
    assert len(periods)>=8 and periods==restored,'Saved checkpoint clock periods differ'
    assert signature(source/'placed_exceptions.timing',source,probe)==signature(probe/'restored_exceptions.timing',source,probe),'Saved checkpoint exceptions differ'
    proof=dict(source_attempt=source.relative_to(root).as_posix(),probe=probe.relative_to(root).as_posix(),checkpoint_sha256=saved['checkpoint_sha256'],source_context_sha256=sha(source/'source_context.json'),source_inputs_sha256=sha(source/'inputs.json'),source_saved_proof_sha256=sha(source/'normal_failure_checkpoint.json'),source_prefix_sha256=sha(source/'normal_failure_prefix.log'),initial_provenance_sha256=sha(source/'checkpoint_provenance.json'),probe_summary_sha256=sha(probe/'summary.json'),probe_clocks_sha256=sha(probe/'restored_clocks.txt'),probe_exceptions_sha256=sha(probe/'restored_exceptions.timing'),clock_periods=[list(v) for v in sorted(periods)])
    return proof,before,ctx,ps,parent
