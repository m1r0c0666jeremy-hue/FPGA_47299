"""Reproduce review findings without changing the received RTL or build artifacts.

Exit 1 means an actual review assertion failed. The active packer and last-word
cases intentionally assert the desired behavior, not the presence of a bug.
Two existing test fixtures are copied to the ignored build directory with only
their old 'bug must exist' checks replaced by full/empty guard checks.
"""
from pathlib import Path
import os
import re
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
out=root/'build/sim/review'; out.mkdir(parents=True,exist_ok=True)
bin_dir=root/'tools/iverilog/ucrt64/bin'
env=os.environ.copy(); env['PATH']=str(bin_dir)+os.pathsep+env.get('PATH','')
hdl=root/'user_source/hdl_source'
project=(root/'td_project/criticalwork.al').read_text(encoding='utf-8')
matches=[]
for rel in re.findall(r'<File Path="([^"]+)"',project):
    p=(root/'td_project'/rel).resolve()
    if p.suffix=='.v' and re.search(r'\bmodule\s+data_96bit_to_128bit\b',p.read_text(encoding='utf-8',errors='replace')):
        matches.append(p)
assert len(matches)==1, matches
active=matches[0]

def replace_once(text, old, new):
    assert text.count(old)==1, old
    return text.replace(old,new)

memory=(root/'sim/tb_memory.sv').read_text()
memory=replace_once(memory,
    'if(dut.U_w128_d512_fifo.overflow_attempts==0) $fatal(1,"overflow scenario not exercised");',
    'if(dut.U_w128_d512_fifo.overflow_attempts!=0 || dut.S_fifo_overflow!==1) $fatal(1,"write full guard / dropped-data flag failed");')
memory=replace_once(memory,
    '$display("KNOWN_LIMITATION memory: camera keeps writing when FIFO full; no overflow recovery in reference");',
    '$display("PASS write full guard; dropped-data flag set, full-frame recovery NOT tested");')
(out/'tb_memory_guard.sv').write_text(memory)
readout=(root/'sim/tb_readout.sv').read_text()
readout=replace_once(readout,
    'if(dut.U_w128_d512_fifo.underflow_attempts==0) $fatal(1,"underflow scenario missing");',
    'if(dut.U_w128_d512_fifo.underflow_attempts!=0 || pixel!==0) $fatal(1,"empty read guard / blanking failed");')
readout=replace_once(readout,
    '$display("KNOWN_LIMITATION memory: display reads when FIFO empty; reference does not blank/recover underflow");',
    '$display("PASS empty read guard and empty black output; recovery NOT tested");')
(out/'tb_readout_guard.sv').write_text(readout)
fifo=root/'sim/fifo_model.sv'
jobs=[
    ('active_pack_reset','tb_review_pack_reset',[root/'sim/tb_review_pack_reset.sv',active]),
    ('unused_fixed_pack_reset','tb_review_pack_reset',[root/'sim/tb_review_pack_reset.sv',hdl/'data_96bit_to_128bit.v']),
    ('write_full_guard','tb_memory',[out/'tb_memory_guard.sv',fifo,hdl/'video_in.v']),
    ('read_empty_guard','tb_readout',[out/'tb_readout_guard.sv',fifo,hdl/'video_out.v']),
    ('read_last_word','tb_review_last_word',[root/'sim/tb_review_last_word.sv',fifo,hdl/'video_out.v']),
]
logs=[f'Active packer from TD project: {active.relative_to(root).as_posix()}']
failed=[]
for name,top,files in jobs:
    image=out/(name+'.vvp')
    compiled=subprocess.run([str(bin_dir/'iverilog.exe'),'-g2012','-s',top,'-o',str(image),*map(str,files)],capture_output=True,text=True,env=env,cwd=root)
    logs.append(f'=== {name}: compile exit {compiled.returncode} ===\n{compiled.stdout}{compiled.stderr}')
    if compiled.returncode: failed.append(name); continue
    run=subprocess.run([str(bin_dir/'vvp.exe'),str(image)],capture_output=True,text=True,env=env,cwd=root,timeout=30)
    logs.append(f'=== {name}: run exit {run.returncode} ===\n{run.stdout}{run.stderr}')
    if run.returncode: failed.append(name)
logs.append('FAILED ASSERTIONS: '+', '.join(failed))
text='\n'.join(logs)
(root/'reports/teammate_review_tests.log').write_text(text,encoding='utf-8')
print(text)
sys.exit(bool(failed))
