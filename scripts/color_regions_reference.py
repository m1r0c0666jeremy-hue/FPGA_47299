"""Independent pixel flood-fill oracle for the functional colour-region design.

No RTL run labels/equivalence table are used here. Coordinates are source pixels.
Engineering defaults are not measured camera calibration.
"""
from collections import deque
from fractions import Fraction
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
DEFAULTS=dict(min_value=24,min_chroma=8,sat_num=3,sat_den=16,
              red_lo=0,red_hi=30,red_wrap=345,yellow_lo=45,yellow_hi=75,
              blue_lo=195,blue_hi=255,purple_lo=255,purple_hi=330,
              tile_min=4,support_min=16,area_min=16,padding=64,confirm=3,max_step=96)
def configuration():
    c=json.loads((R/'rtl/03_tool_detection/target_config.json').read_text(encoding='utf-8'))
    return {k:c.get('regions_'+k,v) for k,v in DEFAULTS.items()}
def classify(rgb,c=None):
    c=c or DEFAULTS;r,g,b=map(int,rgb);m=max(r,g,b);d=m-min(r,g,b)
    if m<c['min_value'] or d<c['min_chroma'] or c['sat_den']*d<c['sat_num']*m:return 0,0
    if m==r:h=Fraction(60*(g-b),d)%360
    elif m==g:h=120+Fraction(60*(b-r),d)
    else:h=240+Fraction(60*(r-g),d)
    hits=[h<c['red_hi'] or h>=c['red_wrap'],c['blue_lo']<=h<c['blue_hi'],
          c['yellow_lo']<=h<c['yellow_hi'],c['purple_lo']<=h<c['purple_hi']]
    if sum(hits)!=1:return 0,0
    return 1<<hits.index(True),sum((4*d>=m,2*d>=m,4*d>=3*m))
def components(mask,quality=None):
    """Unbounded 8-neighbour BFS: independent truth, not the hardware capacity policy."""
    h=len(mask);w=len(mask[0]);seen=set();out=[]
    for y in range(h):
        for x in range(w):
            if not mask[y][x] or (x,y) in seen:continue
            q=deque([(x,y)]);seen.add((x,y));pixels=[]
            while q:
                px,py=q.popleft();pixels.append((px,py))
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        nx,ny=px+dx,py+dy
                        if 0<=nx<w and 0<=ny<h and mask[ny][nx] and (nx,ny) not in seen:
                            seen.add((nx,ny));q.append((nx,ny))
            xs,ys=zip(*pixels);n=len(pixels);box=(min(xs),max(xs),min(ys),max(ys))
            fill=100*n//((box[1]-box[0]+1)*(box[3]-box[2]+1))
            qs=sum(int(quality[y0][x0]) for x0,y0 in pixels) if quality is not None else 0
            out.append(dict(box=box,count=n,sx=sum(xs),sy=sum(ys),cx=sum(xs)//n,cy=sum(ys)//n,
                            fill=fill,sumq=qs,score=n*(64+fill)+4*qs))
    return out
def grid_regions(mask,c=None):
    c=c or DEFAULTS;h=len(mask);w=len(mask[0]);gw=(w+31)//32;gh=(h+31)//32
    counts=[[0]*gw for _ in range(gh)]
    for y,row in enumerate(mask):
        for x,v in enumerate(row):counts[y//32][x//32]+=bool(v)
    active=[[counts[y][x]>=c['tile_min'] and sum(counts[yy][xx]
             for yy in range(max(0,y-1),min(gh,y+2)) for xx in range(max(0,x-1),min(gw,x+2)))>=c['support_min']
             for x in range(gw)] for y in range(gh)]
    # Flood fill using a copy carrying each cell's original pixel count.
    seen=set();out=[]
    for y in range(gh):
        for x in range(gw):
            if not active[y][x] or (x,y) in seen:continue
            q=deque([(x,y)]);seen.add((x,y));cells=[]
            while q:
                xx,yy=q.popleft();cells.append((xx,yy))
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        nx,ny=xx+dx,yy+dy
                        if 0<=nx<gw and 0<=ny<gh and active[ny][nx] and (nx,ny) not in seen:
                            seen.add((nx,ny));q.append((nx,ny))
            xs,ys=zip(*cells);out.append(dict(count=sum(counts[yy][xx] for xx,yy in cells),
                box=(max(0,32*min(xs)-c['padding']),min(w-1,32*(max(xs)+1)-1+c['padding']),
                     max(0,32*min(ys)-c['padding']),min(h-1,32*(max(ys)+1)-1+c['padding']))))
    out.sort(key=lambda a:(-a['count'],a['box'][2],a['box'][0]))
    return out[:2],len(out)>2
