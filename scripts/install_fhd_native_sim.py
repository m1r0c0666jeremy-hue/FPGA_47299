"""Install hash-pinned MSYS2 compiler/simulator locally; no system PATH edits."""
from pathlib import Path
import concurrent.futures,hashlib,json,re,subprocess,urllib.request
from refined_testlib import R

index=R/'build/tool_index'
packages={}
for path in index.glob('*/desc'):
    fields=re.split(r'%([A-Z0-9]+)%\n',path.read_text(encoding='utf-8'))
    info={fields[i]:fields[i+1].strip().splitlines() for i in range(1,len(fields),2)}
    packages[info['NAME'][0]]=info
selected={}
def include(name):
    name=re.split(r'[<>=]',name)[0]
    if name=='perl':return # Invoke the native verilator_bin directly.
    if name in selected:return
    info=packages[name];selected[name]=info
    for dep in info.get('DEPENDS',[]):include(dep)
for name in ('gcc','verilator'):include('mingw-w64-ucrt-x86_64-'+name)
target=R/'tools/native_sim';target.mkdir(exist_ok=True)
def download(item):
    name,info=item;filename=info['FILENAME'][0];path=target/filename
    url='https://mirror.msys2.org/mingw/ucrt64/'+filename
    if not path.exists():urllib.request.urlretrieve(url,path)
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    assert sha==info['SHA256SUM'][0],filename+' SHA mismatch'
    members=subprocess.check_output(['tar','-tf',str(path)],text=True).splitlines()
    assert all(not p.startswith(('/','\\')) and '..' not in Path(p).parts and ':' not in p for p in members)
    subprocess.run(['tar','-xf',str(path),'-C',str(target)],check=True)
    print('LOCAL_SIM_PACKAGE',name,flush=True)
    return dict(name=name,url=url,sha256=sha)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    manifest=list(pool.map(download,selected.items()))
(target/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('LOCAL_SIM_READY',target)
