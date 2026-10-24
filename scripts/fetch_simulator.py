"""Fetch MSYS2's Icarus runtime into this workspace; no installer/PATH changes.

Reads the HTTPS package index and verifies every archive against its SHA256.
Only runtime dependencies are fetched; package install scripts are not executed.
"""
from pathlib import Path
import hashlib
import io
import json
import re
import subprocess
import tarfile
import urllib.request

root = Path(__file__).resolve().parents[1] / 'tools' / 'iverilog'
root.mkdir(parents=True, exist_ok=True)
base = 'https://mirror.msys2.org/mingw/ucrt64/'
request = urllib.request.Request(base + 'ucrt64.db', headers={'User-Agent': 'criticalwork-local-test/1.0'})
index = urllib.request.urlopen(request, timeout=30).read()
index_path = root / 'ucrt64.db'
index_path.write_bytes(index)
packages = {}
descriptions = subprocess.check_output(['tar', '-xOf', str(index_path), '--include=*/desc']).decode()
for content in re.split(r'(?=%FILENAME%\n)', descriptions):
    if not content.strip(): continue
    fields = re.split(r'%([A-Z0-9]+)%\n', content)
    record = {fields[i]: fields[i+1].strip().splitlines() for i in range(1,len(fields),2)}
    packages[record['NAME'][0]] = record
pending = ['mingw-w64-ucrt-x86_64-iverilog']
chosen = {}
while pending:
    name = re.split('[<>=]', pending.pop())[0]
    if name in chosen: continue
    record = packages[name]
    chosen[name] = record
    pending.extend(record.get('DEPENDS', []))
size = sum(int(p['CSIZE'][0]) for p in chosen.values())
if size > 50_000_000: raise RuntimeError(f'Unexpected runtime download size: {size}')
manifest = []
for name, record in chosen.items():
    filename = record['FILENAME'][0]
    expected = record['SHA256SUM'][0]
    path = root / filename
    data = path.read_bytes() if path.exists() else urllib.request.urlopen(base+filename, timeout=45).read()
    if hashlib.sha256(data).hexdigest() != expected: raise RuntimeError('Hash mismatch: '+filename)
    if not path.exists(): path.write_bytes(data)
    members = subprocess.check_output(['tar', '-tf', str(path)], text=True).splitlines()
    safe = [m for m in members if m.startswith('ucrt64/') and '..' not in Path(m).parts]
    # No .INSTALL scripts; only the package's runtime tree.
    if safe:
        subprocess.run(['tar', '-xf', str(path), '-C', str(root), 'ucrt64'], check=True)
    manifest.append({'name':name, 'url':base+filename, 'sha256':expected})
    print(name, flush=True)
(root / 'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(f'Prepared {len(chosen)} runtime packages ({size} download bytes).')
