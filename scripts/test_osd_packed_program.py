"""Packed vs fixed-stride English program: every pixel and formatter cycle."""
from refined_testlib import R,run,literal_fixture
import hashlib,json,zipfile
b=json.loads((R/'reports/refined/osd_memory_english_baseline.json').read_text())
out=R/'build/sim/osd_memory_packed';out.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(R/b['archive']) as z:
    data={n:z.read(n) for n in b['inputs']}
assert all(hashlib.sha256(data[n]).hexdigest()==h for n,h in b['inputs'].items())
assert not json.loads(data['assets/osd/anlogic/english_ui_manifest.json'])['packed_program']
original=data['rtl/color_regions/refined_osd.v'].decode().replace('module refined_osd(', 'module english_unpacked(').replace('refined_footer_program_rom','unpacked_program_rom')
old=out/'english_unpacked.v';old.write_text(original,encoding='utf-8')
program=out/'unpacked_program_rom.v';program.write_bytes(data['rtl/color_regions/refined_footer_program_rom.v'].replace(b'refined_footer_program_rom',b'unpacked_program_rom'))
src=literal_fixture(R/'scripts/test_osd_shared_chinese.py').replace('chinese_original original','english_unpacked original').replace('chinese_shared candidate','refined_osd candidate')
src=src.replace('integer f,x,y,n=0;',"integer f,x,y,n=0,k,t;reg [31:0] rng=32'h47299;")
src=src.replace('$display("OSD_SHARED_CHINESE_PASS', '''checking=0;de=0;
for(t=0;t<240;t=t+1)begin
@(negedge clk);for(k=0;k<24;k=k+1)begin rng=rng*1664525+1013904223;meta[k*32+:32]=rng;end
meta[567:565]=t%5;meta[563:560]=t%13;
original.x=0;original.y=625;candidate.x=0;candidate.y=625;de=1;
@(negedge clk);de=0;
repeat(2400)begin @(negedge clk);
if(original.format_state!==candidate.format_state || original.footer_ready!==candidate.footer_ready)$fatal(1,"packed formatter timing changed");end
for(k=0;k<128;k=k+1)if(original.characters[k]!==candidate.characters[k])$fatal(1,"packed text differs context%0d char%0d",t,k);
end
$display("OSD_PACKED_PROGRAM_PASS 240 contexts, 30720 characters and original formatter timing;''')
mods=[old,program]+[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_osd','refined_english_font_rom','refined_english_text_rom','refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry')]
run('osd_packed_program_equivalence',src,mods,timeout=1800)
