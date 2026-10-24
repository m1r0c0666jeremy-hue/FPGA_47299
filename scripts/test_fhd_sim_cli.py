"""A timed-out verification command must leave a rejection record, never a pass."""
import json, subprocess, sys
from refined_testlib import R

report=R/'reports/refined/regression'
before=set(report.glob('fhd_cli_timeout_*.json'))
source='module tb; initial begin $display("fixture started"); forever #1; end endmodule'
command=f"from refined_testlib import run;run('fhd_cli_timeout',{source!r},[],timeout=1,expected_failure=True)"
result=subprocess.run([sys.executable,'-c',command],cwd=R/'scripts',capture_output=True,text=True,timeout=15)
records=set(report.glob('fhd_cli_timeout_*.json'))-before
assert len(records)==1, 'timeout lost structured verification record'
record=json.loads(records.pop().read_text(encoding='utf-8'))
assert result.returncode!=0 and record['timed_out'] and not record['passed'], 'timeout accepted as expected functional failure'
assert record['stage']=='simulate' and record['fixture_sha256'], 'missing timeout provenance'
print('FHD_SIM_CLI_PASS: timeout rejects with provenance even when a functional failure was expected')
