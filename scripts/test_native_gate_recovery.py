"""Reject mismatched/corrupt crash recovery records using private copies."""
import datetime,hashlib,json,struct
from pathlib import Path
from refined_testlib import R
from native_gate_recovery import gate_recovery_proof

def main():
 parent=R/'build/native_zoom_place_20261029_223152';summary=json.loads((parent/'summary.json').read_text(encoding='utf-8'))
 log=(parent/'td.log').read_text(encoding='utf-8');positive=gate_recovery_proof(parent,summary['exit_code'],log)
 assert positive['exception_code']=='0xe06d7363'
 dump=(parent/positive['dump_name']).read_bytes();out=R/'build'/('native_gate_recovery_guard_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir(exist_ok=False)
 def patched(offset,value):
  b=bytearray(dump);struct.pack_into('<I',b,offset,value);return bytes(b)
 count,directory=struct.unpack_from('<II',dump,8)
 entry=next(directory+12*i for i in range(count) if struct.unpack_from('<I',dump,directory+12*i)[0]==6)
 _,size,offset=struct.unpack_from('<III',dump,entry)
 variants={
  'unsupported_exit':(dump,17,log),
  'mismatched_exception':(dump,3221225477,log),
  'missing_export':(dump,summary['exit_code'],log.replace('finish command "export_db target_color_regions_gate.db"','incomplete export')),
  'missing_crash_log':(dump,summary['exit_code'],log.replace('Oops! coredump','unrelated dump')),
  'unsafe_dump_path':(dump,summary['exit_code'],log.replace(positive['dump_name'],'../'+positive['dump_name'])),
  'missing_dump':(None,summary['exit_code'],log),
  'bad_signature':(b'BAD!'+dump[4:],summary['exit_code'],log),
  'short_header':(dump[:16],summary['exit_code'],log),
  'bad_directory':(patched(12,len(dump)),summary['exit_code'],log),
  'missing_exception':(patched(entry,7),summary['exit_code'],log),
  'bad_exception_bounds':(patched(entry+8,len(dump)),summary['exit_code'],log),
  'forged_exception':(patched(offset+8,3221225477),summary['exit_code'],log)}
 rejected=[]
 for name,(data,code,text) in variants.items():
  folder=out/name;folder.mkdir()
  if data is not None:(folder/positive['dump_name']).write_bytes(data)
  try:gate_recovery_proof(folder,code,text)
  except AssertionError:rejected.append(name)
  else:raise AssertionError('Recovery accepted '+name)
 assert (parent/positive['dump_name']).read_bytes()==dump
 result={'status':'NATIVE_GATE_RECOVERY_GUARDS_PASS','positive':positive,'rejected':rejected,'case_count':len(rejected),
  'original_unchanged':True,'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  'guard_sha256':hashlib.sha256((R/'scripts/native_gate_recovery.py').read_bytes()).hexdigest()}
 (out/'receipt.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(out,result)
if __name__=='__main__':main()
