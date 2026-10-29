"""Update the native continuation index without overwriting historical evidence."""
import argparse,json,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--status',required=True);ap.add_argument('--build');ap.add_argument('--session',type=int);ap.add_argument('--software');ap.add_argument('--note',required=True);a=ap.parse_args()
 state=R/(R/'build/current_native_zoom_path.txt').read_text(encoding='utf-8').strip()/'state.json'
 d=json.loads(state.read_text(encoding='utf-8'));event={'time':datetime.datetime.now().isoformat(),'status':a.status,'note':a.note}
 if a.build:event['build']=a.build
 if a.session:event['session']=a.session
 d.setdefault('history',[]).append(event);d['status']=a.status;d['latest_event']=event
 if a.build:d['current_build']=a.build
 d['active_processes']=([{'kind':'TD','session':a.session,'directory':a.build}] if a.session else [])
 if a.software:d['current_software']=a.software
 state.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8');print(event)
