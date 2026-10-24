"""Independent pixel geometry oracle for all sub-tile translations."""
from collections import deque
from pathlib import Path
import argparse,json
from test_ring_calibration import R,O,P,run
def stats(points,strong):
    a=[[0,0,0,0] for _ in range(3600)]
    for x,y in points:
        s=a[y//16*80+x//16];s[0]+=1;s[1]+=x%16;s[2]+=y%16;s[3]+=int((x,y) in strong)
    return a
def blobs(a,fringe):
    active=set();core=set()
    for n,s in enumerate(a):
        x=n%80;y=n//80;support=sum(a[yy*80+xx][0] for yy in range(max(0,y-1),min(45,y+2)) for xx in range(max(0,x-1),min(80,x+2)))
        if s[0]>=4 and support>=16:core.add(n)
        if s[0]>0 and support>=16:active.add(n)
    if not fringe:active=set(core)
    visited=set();result=[]
    for root in sorted(core):
        if root in visited:continue
        visited.add(root);q=deque([root]);nodes=[]
        while q:
            n=q.popleft();nodes.append(n)
            if n not in core:continue
            x=n%80;y=n//80
            for yy in range(max(0,y-1),min(45,y+2)):
                for xx in range(max(0,x-1),min(80,x+2)):
                    z=yy*80+xx
                    if z in active and z not in visited:visited.add(z);q.append(z)
        count=sum(a[n][0] for n in nodes)
        if count>=48:
            sx=sum(a[n][1]+16*(n%80)*a[n][0] for n in nodes)
            sy=sum(a[n][2]+16*(n//80)*a[n][0] for n in nodes)
            result.append((sx//count,sy//count,count))
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',action='store_true');args=p.parse_args()
    vectors=[];expected=[];lost=0
    anchors=[(320,192),(576,192),(320,448),(576,448)]
    for batch in range(64):
        pts=[set(),set()]
        for k,(ax,ay) in enumerate(anchors):
            n=batch*4+k;dx=n%16;dy=n//16
            pts[0].update((ax+dx+x,ay+dy+y) for y in range(16) for x in range(3))
            pts[1].update((ax+96+dx+x,ay+32+dy+y) for y in range(3) for x in range(16))
        aa,bb=[stats(z,z) for z in pts]
        e=[blobs(z,not args.baseline) for z in (aa,bb)];expected.append(e)
        lost+=8-len(e[0])-len(e[1])
        for a,b in zip(aa,bb):
            word=a[0]|a[1]<<9|a[2]<<20|b[0]<<31|b[1]<<40|b[2]<<51
            if not args.baseline:word|=a[3]<<62|b[3]<<71
            vectors.append(f'{word:0{16 if args.baseline else 20}x}')
    vec=O/('grid_before.hex' if args.baseline else 'grid_after.hex');vec.write_text('\n'.join(vectors),encoding='ascii')
    checks=''
    for batch,e in enumerate(expected):
        checks+=f'{batch}:begin\n'
        for c,results in enumerate(e):
            checks+=f'n=0;for(j={c*4};j<{c*4+4};j=j+1)if(cand[j*128+120])n=n+1;if(n!={len(results)})$fatal(1,"candidate count batch{batch} colour{c} %0d",n);\n'
            for x,y,count in results:
                checks+=f'n=0;for(j={c*4};j<{c*4+4};j=j+1)if(cand[j*128+120] && cand[j*128+62+:11]=={x} && cand[j*128+73+:10]=={y} && cand[j*128+42+:20]=={count})n=1;if(!n)$fatal(1,"phase/moment batch{batch} colour{c} xy{x}/{y}");\n'
        checks+='end\n'
    width=62 if args.baseline else 80
    module=R/('sim/ring_baseline/stable_grid.v' if args.baseline else 'rtl/color_regions/stable_grid.v')
    src=f'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0;wire busy,done,failed;wire [1023:0] cand;wire [17:0] cycles;
reg [{width-1}:0] words[0:230399];integer batch,j,n,total,maxcycles=0;
stable_grid dut(clk,rst,1'b0,1'b0,11'd0,10'd0,{4 if args.baseline else 8}'d0,{4 if args.baseline else 8}'d0,start,1'b0,1'b0,84'd0,1'b0,busy,done,failed,cand,cycles);
initial begin $readmemh("{vec.as_posix()}",words);repeat(3)@(negedge clk);rst=1;
for(batch=0;batch<64;batch=batch+1)begin @(negedge clk);for(j=0;j<3600;j=j+1)dut.stats0[j]=words[batch*3600+j];
start=1;@(negedge clk);start=0;total=0;while(!done && total<213000)begin @(negedge clk);total=total+1;end
if(!done || failed || cycles>=212000)$fatal(1,"grid deadline");if(cycles>maxcycles)maxcycles=cycles;
case(batch){checks}endcase end
$display("RING_GRID_PHASES_PASS baseline={int(args.baseline)} retained={512-lost}/512 maxcycles=%0d",maxcycles);$finish;end endmodule'''
    run('grid_phases_before' if args.baseline else 'grid_phases_after',src,[module,R/'rtl/color_regions/regions_divide.v'])
    (P/('grid_before.json' if args.baseline else 'grid_after.json')).write_text(json.dumps(dict(cases=512,retained=512-lost,oracle='source rectangles and independent graph traversal'),indent=2),encoding='utf-8')
if __name__=='__main__':main()
