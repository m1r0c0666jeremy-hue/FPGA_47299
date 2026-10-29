"""Qualify an exported gate after a documented native placement failure."""
import hashlib,re,struct
from pathlib import Path

CRASH_CODES=(3221225477,3765269347)

def gate_recovery_proof(parent,exit_code,log):
 parent=Path(parent)
 assert 'finish command "export_db target_color_regions_gate.db"' in log,'Gate export did not finish'
 if exit_code==0:
  assert 'REFINED_PLACED_CHECKPOINT_READY' in log
  return {'status':'PLACEMENT_COMPLETED','exit_code':0}
 if exit_code==1:
  assert "PHY-9053 ERROR: Design's slice number" in log
  return {'status':'PLACEMENT_RESOURCE_FAILURE_LEGAL_GATE','exit_code':1}
 assert exit_code in CRASH_CODES,'Unrecognized native failure'
 names=re.findall(r'Oops! coredump ([^\s]+)',log)
 assert len(names)==1,'Missing or ambiguous native crash dump'
 name=names[0];assert re.fullmatch(r'[A-Za-z0-9_.-]+\.dmp',name),'Unsafe dump path'
 path=parent/name;assert path.is_file(),'Missing native dump'
 data=path.read_bytes();assert len(data)>=32 and data[:4]==b'MDMP','Invalid minidump header'
 count,directory=struct.unpack_from('<II',data,8)
 assert 0<count<=64 and directory+12*count<=len(data),'Invalid minidump directory'
 streams=[struct.unpack_from('<III',data,directory+12*i) for i in range(count)]
 exception=[(size,offset) for kind,size,offset in streams if kind==6]
 assert len(exception)==1,'Missing or ambiguous exception stream'
 size,offset=exception[0];assert size>=168 and offset+size<=len(data),'Invalid exception stream'
 thread,=struct.unpack_from('<I',data,offset)
 code,=struct.unpack_from('<I',data,offset+8)
 assert code==exit_code,'Minidump exception does not match native exit'
 return {'status':'NATIVE_PLACEMENT_CRASH_WITH_MATCHING_DUMP','exit_code':exit_code,'exception_code':f'0x{code:08x}',
  'dump_name':name,'dump_sha256':hashlib.sha256(data).hexdigest(),'thread_id':thread,'log_sha256':hashlib.sha256((parent/'td.log').read_bytes()).hexdigest()}
