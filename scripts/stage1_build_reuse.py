"""Deterministic stage-one gate-checkpoint extension to the inherited build wrapper.

Exact anchors fail closed if the inherited generator changes. The generated build
retains the verified checkpoint/source lineage checks used by the release audit.
"""

REPLACEMENTS = (("ap.add_argument('--checkpoint',action='store_true')\n",
  "ap.add_argument('--checkpoint',action='store_true')\n"
  "ap.add_argument('--gate-parent',help='Reuse a verified, legalized gate checkpoint with identical current "
  "inputs; place only')\n"),
 ('canonical_build_inputs(before)\n',
  'canonical_build_inputs(before)\n'
  'gate_proof=None\n'
  'if a.gate_parent:\n'
  " assert a.stage=='place' and a.checkpoint,'Gate reuse requires --stage place --checkpoint'\n"
  " assert not a.official_syn,'Gate reuse cannot apply synthesis presets'\n"
  " parent=(R/a.gate_parent).resolve();assert parent.is_relative_to(R/'build')\n"
  " prior=json.loads((parent/'summary.json').read_text(encoding='utf-8'))\n"
  " context=json.loads((parent/'source_context.json').read_text(encoding='utf-8'))\n"
  " checkpoint=parent/'target_color_regions_gate.db'\n"
  " assert prior['stage']=='place' and prior['exit_code']==0 and prior['inputs_unchanged']\n"
  " for key in ('map_mode','pack_effort','infer_fsm','min_ripple_len','map_strategy'):\n"
  "  assert getattr(a,key)==prior[key],f'Gate reuse cannot change synthesis option {key}'\n"
  " assert prior['checkpoints'][checkpoint.name]==sha(checkpoint)\n"
  ' assert '
  "before==json.loads((parent/'inputs.json').read_text(encoding='utf-8'))==json.loads((parent/'inputs_after.json').read_text(encoding='utf-8'))\n"
  " assert context['input_count']==len(before) and context['inputs_sha256']==sha(parent/'inputs.json')\n"
  " assert all(sha(parent/'compiled_source'/name)==value for name,value in before.items())\n"
  " parent_tcl=(parent/'run.tcl').read_text(encoding='utf-8')\n"
  " assert parent_tcl.index('legalize_phy_inst')<parent_tcl.index('export_db target_color_regions_gate.db')\n"
  " assert 'REFINED_PLACED_CHECKPOINT_READY' in (parent/'td.log').read_text(encoding='utf-8')\n"
  ' '
  "gate_proof=dict(parent=parent.relative_to(R).as_posix(),checkpoint_sha256=sha(checkpoint),parent_summary_sha256=sha(parent/'summary.json'),parent_context_sha256=sha(parent/'source_context.json'),parent_inputs_sha256=sha(parent/'inputs.json'),placement_created_commit=created_head)\n"
  " (out/'input_gate.db').write_bytes(checkpoint.read_bytes())\n"
  " assert sha(out/'input_gate.db')==gate_proof['checkpoint_sha256']\n"
  " # The netlist was compiled from this parent's commit; retain that identity.\n"
  " created_head=context['compiled_source_commit']\n"
  " subprocess.run(['git','merge-base','--is-ancestor',created_head,'HEAD'],cwd=R,check=True)\n"
  ' for name,value in before.items():\n'
  "  raw=subprocess.check_output(['git','show',created_head+':'+name],cwd=R)\n"
  "  assert hashlib.sha256(raw).hexdigest()==value,'Gate compilation commit differs: '+name\n"
  " gate_proof['git_blob_inputs_verified']=len(before)\n"),
 ("(out/'source_context.json').write_text(json.dumps(dict(compiled_source_commit=created_head,creation_time=stamp,input_count=len(before),inputs_sha256=sha(out/'inputs.json')),indent=2),encoding='utf-8')\n",
  "(out/'source_context.json').write_text(json.dumps(dict(compiled_source_commit=created_head,creation_time=stamp,input_count=len(before),inputs_sha256=sha(out/'inputs.json'),reused_gate=gate_proof),indent=2),encoding='utf-8')\n"),
 ("t=t.replace('td_project target_lock.adc','td_project stage1_pins.adc')\n",
  "t=t.replace('td_project target_lock.adc','td_project stage1_pins.adc')\n"
  'if gate_proof:\n'
  ' # The parent exports this DB after legalize_phy_inst. Import its constraints\n'
  ' # and legalized netlist, then apply only the new physical settings.\n'
  " start=t.index('    import_device ');end=t.index('    set_param place ',start)\n"
  " t=t[:start]+f'    import_device ph1_35p.db -package PH1P35MDG324 -speed 3\\n    import_db "
  '{{{(out/"input_gate.db").as_posix()}}}\\n\'+t[end:]\n'
  " t=t.replace('    legalize_phy_inst\\n','',1)\n"
  ' t=t.replace(\'    place\\n\',\'    puts "STAGE1_VERIFIED_GATE_REUSE"\\n    place\\n\',1)\n'),
 ("summary['official_strategy']=official\n",
  "summary['official_strategy']=official\n"
  "summary['reused_gate']=gate_proof\n"
  'if gate_proof:\n'
  ' '
  "summary['gate_input_unchanged']=sha(out/'input_gate.db')==gate_proof['checkpoint_sha256']==sha(parent/'target_color_regions_gate.db')\n"
  " assert summary['gate_input_unchanged']\n"))


def add_gate_reuse(source):
    for old,new in REPLACEMENTS:
        assert source.count(old)==1, 'Stage-one gate reuse generator anchor changed: '+old[:80]
        source=source.replace(old,new,1)
    return source
