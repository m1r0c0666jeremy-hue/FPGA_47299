"""Compile the enabled RTL dependency set; physical vendor IP is black-boxed."""
from pathlib import Path
import re,subprocess,os,datetime,json,hashlib
from refined_testlib import R,IV,ENV
from stage1_project import _parse
from native_zoom_codegen import assets

def sources():
    root=_parse((R/'td_project/target_color_regions_native_zoom.al').read_text(encoding='utf-8'))
    result=[]
    for f in root.findall('./Source_Files/Verilog/File'):
        attrs={a.get('Name'):a.get('Val') for a in f.findall('./FileInfo/Attr')}
        if attrs.get('UsedInSyn')=='false' or attrs.get('AutoExcluded')=='true':continue
        p=(R/'td_project'/f.get('Path')).resolve()
        assert p.is_file(),p
        if '.enc.' in p.name:continue
        result.append(p)
    return result

def main():
    for name,expected in assets().items():assert (R/name).read_bytes()==expected.encode('utf-8'),name
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    out=R/'build'/('native_zoom_elaboration_'+stamp);out.mkdir()
    paths=sources()
    cmd=[str(IV),'-g2012','-i','-DNATIVE_BEHAVIORAL_RAM','-s','criticalwork_top','-o',str(out/'top.vvp'),*map(str,paths)]
    with (out/'compile.log').open('w',encoding='utf-8') as log:
        code=subprocess.run(cmd,cwd=R,env=ENV,stdout=log,stderr=subprocess.STDOUT).returncode
    record={'exit_code':code,'source_count':len(paths),'scope':'RTL elaboration only; missing physical IP black-boxed, not a functional or TD pass',
            'inputs':{p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (out/'receipt.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print((out/'compile.log').read_text(encoding='utf-8'))
    print('NATIVE_ELABORATION',code,'sources',len(paths),out)
    raise SystemExit(code)
if __name__=='__main__':main()
