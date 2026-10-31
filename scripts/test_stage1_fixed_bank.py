"""Actual adopted RTL versus fixed 802af20, at small and production lengths."""
import hashlib
from refined_testlib import R,run
from refined_store_logic import store_asset
fixture=R/'sim/fixtures/stable_fixed_bank'
reference=fixture/'reference_802af20.v'
raw=reference.read_bytes().replace(b'module reference_frame_store #',b'module refined_frame_store #')
assert hashlib.sha256(raw).hexdigest()=='cabb925ecad48ee885bc77c15f87c41256bdab5d491b0e7b61d4986ac276e2d1'
actual=R/'rtl/color_regions/refined_frame_store.v'
assert actual.read_bytes()==store_asset((R/'rtl/color_regions/stable_frame_store.v').read_text(encoding='utf-8')).encode('utf-8')
for name in ('small','production'):
    bench=fixture/(name+'.sv')
    run('stage1_fixed_bank_'+name,bench.read_text(encoding='utf-8'),[reference,actual],timeout=1800,
        args=('+fixture='+bench.relative_to(R).as_posix(),
              '+generator=scripts/refined_store_logic.py',
              '+baseline=rtl/color_regions/stable_frame_store.v'))
