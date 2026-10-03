"""Import the supplied Lab1 without running its scripts or copying old build results."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = Path(r'D:\BaiduNetdiskDownload\HX1P35A_Contest_202606\7_lab_ex_2026_nosoft\lab_ex1_mipi_hdmi_SC500_720P.zip')
PREFIX = 'lab_ex1_mipi_hdmi_SC500_720P/lab_ex1_mipi_hdmi/'
manifest = []
with zipfile.ZipFile(ARCHIVE) as archive:
    for entry in archive.infolist():
        if entry.is_dir() or not entry.filename.startswith(PREFIX):
            continue
        relative = entry.filename[len(PREFIX):]
        if not (relative.startswith('user_source/') or relative in (
            'td_project/camera_to_dsi_display.al', 'td_project/camera_to_dsi_display.sdc')):
            continue
        if '..' in Path(relative).parts:
            raise ValueError(relative)
        data = archive.read(entry)
        destinations = [ROOT / 'vendor_reference' / 'lab1' / relative]
        if relative.startswith('user_source/'):
            destinations.append(ROOT / relative)
        for destination in destinations:
            if destination.exists():
                raise FileExistsError(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        manifest.append({'path': relative, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
(ROOT / 'reports').mkdir(exist_ok=True)
(ROOT / 'reports' / 'source_manifest.json').write_text(json.dumps({
    'archive': str(ARCHIVE), 'archive_sha256': hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
    'files': manifest}, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Imported {len(manifest)} files; old build outputs were not imported.')
