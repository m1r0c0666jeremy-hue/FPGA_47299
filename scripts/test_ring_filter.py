"""Pixel oracle verifies unchanged masks and separate >=2-neighbour statistics."""
from test_ring_calibration import R,O,run
def points(f,c):
    if c==0:
        return {(x,y) for y in range(100,116) for x in range(100,116) if x<103 or x>=113 or y<103 or y>=113}|{(x,0) for x in range(20)}|{(1279,y) for y in range(701,720)}|{(35+f,40)}
    return {(640,y) for y in range(300,360)}|{(50,719),(51,719),(76,60+f)}
hexfile=O/'strong_filter.hex'
with hexfile.open('w',encoding='ascii') as out:
    for f in range(2):
        pp=[points(f,c) for c in range(2)]
        masks=[{},{}]
        for c in range(2):
            for x,y in pp[c]:
                n=sum((x+dx,y+dy) in pp[c] for dy in (-1,0,1) for dx in (-1,0,1) if dx or dy)
                masks[c][(x,y)]=(int(n>=1),int(n>=2))
        for y in range(720):
            for x in range(0,1280,4):
                m=0
                for i in range(4):
                    for c in range(2):
                        a,b=masks[c].get((x+i,y),(0,0));m|=a<<(i*2+c);m|=b<<(i*2+c+8)
                out.write(f'{m:04x}\n')
t=(R/'scripts/test_stable_pipeline.py').read_text(encoding='utf-8')
src='module tb;'+t.split("run('filter',f'''module tb;",1)[1].split("''',['stable_filter4.v'])",1)[0]
src=src.replace("{(O/'filter.hex').as_posix()}",hexfile.as_posix()).replace('[3:0] ha,hb','[7:0] ha,hb').replace('reg [7:0] expected','reg [15:0] expected').replace('reg [7:0] got','reg [15:0] got')
src=src.replace('got[i*2+1]=hb[i];end','got[i*2+1]=hb[i];got[i*2+8]=ha[i+4];got[i*2+9]=hb[i+4];end')
src=src.replace('STABLE_FILTER_PASS','RING_FILTER_PASS').replace('two continuous full frames','two continuous full frames, original and strong masks')
run('strong_filter',src,[R/'rtl/color_regions/stable_filter4.v'])
