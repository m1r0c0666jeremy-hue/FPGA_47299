"""Independent frame-statistics oracle, including invalid-frame precedence."""
def candidate_meta(groups,w,h,seq,session,pair,enabled,pixels,fault):
 def put(low,width,v):
  nonlocal n
  n|=(int(v)&((1<<width)-1))<<low
 n=0;put(0,32,seq);put(235,8,session);put(243,1,pair);put(244,1,enabled)
 frame_ok=pixels==w*h and not fault;put(247,1,frame_ok)
 areas=[];filled=[]
 for j,pts in enumerate(groups):
  area=len(pts);areas.append(area)
  xs=[x for x,y in pts];ys=[y for x,y in pts]
  box=[min(xs,default=w-1),max(xs,default=0),min(ys,default=h-1),max(ys,default=0)]
  bbox=(box[1]-box[0]+1)*(box[3]-box[2]+1)
  fill=100*area//bbox if area else 0
  filled.append(area>0 and 100*area>=30*bbox)
  for lo,wi,v in zip([100,111,122,132] if not j else [142,153,164,174],[11,11,10,10],box):put(lo,wi,v)
  put(184+j*20,20,area);put(224 if not j else 248,7,fill)
  put(245+j,1,frame_ok and 64<=area<=20000 and filled[-1])
  put(37+j*21,11,sum(xs)//area if area else 0);put(48+j*21,10,sum(ys)//area if area else 0)
 reason=8 if fault else 1 if not frame_ok else 2 if min(areas)==0 else 3 if min(areas)<64 or max(areas)>20000 else 4 if not all(filled) else 0
 put(32,1,reason==0);put(33,4,reason)
 return n
