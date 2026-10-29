"""Negative branch/source/project gates without altering live files."""
import json,datetime
from native_zoom_policy import R,compiler_paths,canonical_build_inputs,sha
from native_zoom_codegen import assets
from stage1_project import check_project

if __name__=='__main__':
 out=R/'build'/('native_zoom_guard_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir(exist_ok=False)
 original={p.relative_to(R).as_posix():sha(p) for p in compiler_paths()};canonical_build_inputs(original)
 rejected=[]
 def reject(name,action):
  try:action()
  except (AssertionError,KeyError,ValueError):rejected.append(name)
  else:raise AssertionError('Guard accepted '+name)
 for name in ('rtl/color_regions/native_read_adapter.v','rtl/color_regions/native_downsample2.v','rtl/color_regions/native_top.v','td_project/native_zoom.sdc','vendor_reference/sc500cs_native_2592.json'):
  d=original.copy();d[name]='0'*64;reject('hash_'+name,lambda:canonical_build_inputs(d))
 d=original.copy();d.pop('rtl/color_regions/native_top.v');reject('missing_compiler_source',lambda:canonical_build_inputs(d))
 expected=assets()['td_project/target_color_regions_native_zoom.al']
 variants={'top':expected.replace('criticalwork_top','wrong_top'),'device':expected.replace('PH1P35MDG324','PH1P35MDG256'),
  'constraint':expected.replace('native_zoom.sdc','target_lock.sdc'),
  'dependency':expected.replace('native_read_adapter.v','wrong_read_adapter.v'),
  'enabled':expected.replace('Path="../rtl/color_regions/native_read_adapter.v"><FileInfo><Attr Name="UsedInSyn" Val="true"','Path="../rtl/color_regions/native_read_adapter.v"><FileInfo><Attr Name="UsedInSyn" Val="false"')}
 for name,text in variants.items():
  assert text!=expected,name
  p=out/(name+'.al');p.write_text(text,encoding='utf-8');reject('project_'+name,lambda:check_project(p,expected))
 assert original=={p.relative_to(R).as_posix():sha(p) for p in compiler_paths()}
 record={'status':'NATIVE_GUARDS_PASS','rejected':rejected,'case_count':len(rejected),'no_live_input_mutation':True,
 'inputs':original,'producer_sha256':sha(__file__),'policy_sha256':sha(R/'scripts/native_zoom_policy.py')}
 (out/'receipt.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print({k:v for k,v in record.items() if k!='inputs'})
