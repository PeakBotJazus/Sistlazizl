"""Мини-CSG движок: тело = последовательность add/sub примитивов.
Нарезается на слои по 0.2 мм (как слайсер), каждый слой контуром извлекается
с сетки 0.1 мм, потом экструдируется в призмы -> бинарный STL."""
import numpy as np, struct, math
from contourpy import contour_generator, FillType

G = 0.1      # шаг сетки XY, узлы в (i+0.5)*G
LAY = 0.2    # толщина слоя
OVL = 0.0    # без нахлёста: нет z-fighting-полос в просмотрщиках

class Box:
    def __init__(s, x0,x1,y0,y1,z0,z1): s.b=(x0,x1,y0,y1); s.z=(z0,z1)
    def state(s,z): return 1 if s.z[0]<=z<s.z[1] else None
    def bbox(s,z,st): return s.b
    def g(s,z,st,X,Y):
        x0,x1,y0,y1=s.b
        return np.maximum(np.abs(X-(x0+x1)/2)-(x1-x0)/2, np.abs(Y-(y0+y1)/2)-(y1-y0)/2)
class ZCyl:
    def __init__(s,cx,cy,r,z0,z1): s.c=(cx,cy); s.r=r; s.z=(z0,z1)
    def state(s,z): return 1 if s.z[0]<=z<s.z[1] else None
    def bbox(s,z,st): return (s.c[0]-s.r,s.c[0]+s.r,s.c[1]-s.r,s.c[1]+s.r)
    def g(s,z,st,X,Y): return np.hypot(X-s.c[0],Y-s.c[1])-s.r
class YCyl:   # ось вдоль Y, центр (cx,cz)
    def __init__(s,cx,cz,r,y0,y1): s.cx=cx; s.cz=cz; s.r=r; s.y=(y0,y1)
    def state(s,z):
        d=abs(z-s.cz)
        return None if d>=s.r else round(math.sqrt(s.r**2-d*d),4)
    def bbox(s,z,w): return (s.cx-w,s.cx+w,s.y[0],s.y[1])
    def g(s,z,w,X,Y):
        return np.maximum(np.abs(X-s.cx)-w, np.abs(Y-(s.y[0]+s.y[1])/2)-(s.y[1]-s.y[0])/2)
class Mask:   # растровая маска (текст): g<0 внутри
    def __init__(s,x0,y0,arr,z0,z1): s.x0=x0; s.y0=y0; s.arr=arr; s.z=(z0,z1)
    def state(s,z): return 1 if s.z[0]<=z<s.z[1] else None
    def bbox(s,z,st):
        h,w=s.arr.shape; return (s.x0,s.x0+w*G,s.y0,s.y0+h*G)
    def g(s,z,st,X,Y): return s.arr

class XZMask:   # растровая метка на вертикальной стенке: g<0 внутри значка, по Y полоса [y0,y1]
    def __init__(s,x0,z0,arr,y0,y1): s.x0=x0; s.z0=z0; s.arr=arr; s.y=(y0,y1)
    def state(s,z):
        r=int(math.floor((z-s.z0)/LAY))
        return r if 0<=r<s.arr.shape[0] else None
    def bbox(s,z,st):
        w=s.arr.shape[1]; return (s.x0,s.x0+w*G,s.y[0],s.y[1])

class Solid:
    def __init__(s): s.ops=[]
    def add(s,p): s.ops.append(('a',p)); return s
    def sub(s,p): s.ops.append(('s',p)); return s
    def box(s,*a): return s.add(Box(*a))
    def cut(s,*a): return s.sub(Box(*a))

def ring_area(p): x,y=p[:,0],p[:,1]; return 0.5*np.sum(x*np.roll(y,-1)-np.roll(x,-1)*y)

def dp(pts,tol):
    n=len(pts)
    if n<4: return pts
    # замкнутый контур: разбиваем по двум дальним точкам
    i0=0; d=np.hypot(*(pts-pts[0]).T); i1=int(d.argmax())
    def rec(a,b):  # открытый участок a..b (индексы в pts, b может = n)
        P=pts[a],pts[b%n]
        keep=np.zeros(n+1,bool); keep[a]=keep[b]=True
        stack=[(a,b)]
        while stack:
            s,e=stack.pop()
            if e-s<2: continue
            A=pts[s]; B=pts[e%n]; seg=pts[s+1:e]
            ab=B-A; L=np.hypot(*ab)
            if L<1e-9: dist=np.hypot(*(seg-A).T)
            else: dist=np.abs(ab[0]*(seg[:,1]-A[1])-ab[1]*(seg[:,0]-A[0]))/L
            k=int(dist.argmax())
            if dist[k]>tol:
                m=s+1+k; keep[m]=True; stack.append((s,m)); stack.append((m,e))
        return keep
    k1=rec(0,i1); k2=rec(i1,n)
    keep=(k1|k2)[:n]
    return pts[keep]

def triangulate(outer,holes):
    pts=[tuple(p) for p in outer]
    poly=list(range(len(outer)))
    P=np.array(outer,float)
    allp=list(map(tuple,outer))
    hl=[]
    for h in holes:
        base=len(allp); allp.extend(map(tuple,h)); hl.append(list(range(base,base+len(h))))
    A=np.array(allp)
    hl.sort(key=lambda r:-A[r][:,0].max())
    for h in hl:
        hm=max(h,key=lambda i:A[i][0]); M=A[hm]
        best=None;bx=1e18
        n=len(poly)
        for k in range(n):
            a=poly[k]; b=poly[(k+1)%n]; ya=A[a][1]; yb=A[b][1]
            if (ya<=M[1]<=yb or yb<=M[1]<=ya) and ya!=yb:
                t=(M[1]-ya)/(yb-ya); xi=A[a][0]+t*(A[b][0]-A[a][0])
                if xi>=M[0]-1e-12 and xi<bx: bx=xi; best=k
        if best is None: raise RuntimeError('no bridge')
        a=poly[best]; b=poly[(best+1)%n]
        pk=best if A[a][0]>A[b][0] else (best+1)%n
        I=np.array([bx,M[1]]); Pp=A[poly[pk]]
        # проверка вершин внутри треугольника M,I,P
        cand=None;cang=1e18
        for k in range(n):
            v=A[poly[k]]
            if k==pk: continue
            if v[0]<M[0]: continue
            if _intri(M,I,Pp,v):
                ang=abs(v[1]-M[1])/max(v[0]-M[0],1e-12)
                if ang<cang: cang=ang; cand=k
        if cand is not None: pk=cand
        hi=h.index(hm); hr=h[hi:]+h[:hi]
        poly=poly[:pk+1]+hr+[hm]+[poly[pk]]+poly[pk+1:]
    return _earclip(A,poly)

def _intri(a,b,c,p):
    d1=(p[0]-b[0])*(a[1]-b[1])-(a[0]-b[0])*(p[1]-b[1])
    d2=(p[0]-c[0])*(b[1]-c[1])-(b[0]-c[0])*(p[1]-c[1])
    d3=(p[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(p[1]-a[1])
    return not (((d1<0) or (d2<0) or (d3<0)) and ((d1>0) or (d2>0) or (d3>0)))

def _earclip(A,poly):
    tris=[]; poly=list(poly)
    guard=0
    while len(poly)>3 and guard<200000:
        guard+=1
        n=len(poly); idx=np.array(poly); V=A[idx]
        prev=np.roll(V,1,0); nxt=np.roll(V,-1,0)
        cr=(V[:,0]-prev[:,0])*(nxt[:,1]-prev[:,1])-(V[:,1]-prev[:,1])*(nxt[:,0]-prev[:,0])
        found=False
        order=np.argsort(-cr)  # сначала самые "острые" выпуклые
        for k in order:
            if cr[k]<=1e-12: break
            a=prev[k];b=V[k];c=nxt[k]
            # вершины внутри (не совпадающие с a,b,c)
            d1=(V[:,0]-b[0])*(a[1]-b[1])-(a[0]-b[0])*(V[:,1]-b[1])
            d2=(V[:,0]-c[0])*(b[1]-c[1])-(b[0]-c[0])*(V[:,1]-c[1])
            d3=(V[:,0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(V[:,1]-a[1])
            inside=(d1>=-1e-12)&(d2>=-1e-12)&(d3>=-1e-12)
            same=((np.abs(V-a).sum(1)<1e-12)|(np.abs(V-b).sum(1)<1e-12)|(np.abs(V-c).sum(1)<1e-12))
            if not np.any(inside&~same&(cr<=1e-9)):
                tris.append((poly[(k-1)%n],poly[k],poly[(k+1)%n])); poly.pop(k); found=True; break
        if not found:
            # убрать вырожденные (нулевая площадь) вершины
            k=int(np.argmin(np.abs(cr)))
            if abs(cr[k])<1e-9: poly.pop(k)
            else:
                k=int(np.argmax(cr)); tris.append((poly[(k-1)%n],poly[k],poly[(k+1)%n])); poly.pop(k)
    if len(poly)==3: tris.append(tuple(poly))
    return A,tris

def slice_solid(S, zmax, tol=0.025, verbose=True):
    ops=S.ops
    # границы сетки
    bx=[];by=[]
    for _,p in ops:
        if isinstance(p,YCyl): bb=(p.cx-p.r,p.cx+p.r,p.y[0],p.y[1])
        else: bb=p.bbox(0,None) if not isinstance(p,(YCyl,)) else None
        bx+=[bb[0],bb[1]]; by+=[bb[2],bb[3]]
    i0=int(math.floor(min(bx)/G))-3; i1=int(math.ceil(max(bx)/G))+3
    j0=int(math.floor(min(by)/G))-3; j1=int(math.ceil(max(by)/G))+3
    xs=(np.arange(i0,i1+1)+0.5)*G; ys=(np.arange(j0,j1+1)+0.5)*G
    nl=int(round(zmax/LAY))
    runs=[]; prev=None
    for k in range(nl):
        zm=(k+0.5)*LAY
        sig=tuple(p.state(zm) for _,p in ops)
        if prev is not None and sig==prev[0]: prev[2]=k+1
        else:
            prev=[sig,k,k+1,zm]; runs.append(prev)
    if verbose: print('  runs',len(runs),end=' ',flush=True)
    meshes=[]
    for ri,(sig,ka,kb,zm) in enumerate(runs):
        f=np.full((len(ys),len(xs)),10.0,np.float32)
        for (kind,p),st in zip(ops,sig):
            if st is None: continue
            x0,x1,y0,y1=p.bbox(zm,st)
            a=max(int(math.floor(x0/G-0.5))-1-i0,0); b=min(int(math.ceil(x1/G-0.5))+2-i0,len(xs))
            c=max(int(math.floor(y0/G-0.5))-1-j0,0); d=min(int(math.ceil(y1/G-0.5))+2-j0,len(ys))
            if isinstance(p,XZMask):
                gi=int(round(p.x0/G))-i0; w=p.arr.shape[1]
                a,b=gi,gi+w
                c=max(int(math.floor(y0/G-0.5))-1-j0,0); d=min(int(math.ceil(y1/G-0.5))+2-j0,len(ys))
                Y=ys[c:d,None]
                g=np.maximum(p.arr[st][None,:],np.abs(Y-(p.y[0]+p.y[1])/2)-(p.y[1]-p.y[0])/2)
            elif isinstance(p,Mask):
                gi=int(round(p.x0/G))-i0; gj=int(round(p.y0/G))-j0
                h,w=p.arr.shape; a,b,c,d=gi,gi+w,gj,gj+h
                g=p.arr
            else:
                g=p.g(zm,st,xs[None,a:b],ys[c:d,None])
            if kind=='a': f[c:d,a:b]=np.minimum(f[c:d,a:b],g)
            else: f[c:d,a:b]=np.maximum(f[c:d,a:b],-g)
        if not (f<0).any(): continue
        cg=contour_generator(xs,ys,f,fill_type=FillType.OuterOffset)
        pl,of=cg.filled(-1e9,0.0)
        polys=[]
        for pts,off in zip(pl,of):
            rings=[]
            for a,b in zip(off[:-1],off[1:]):
                r=np.asarray(pts[a:b],float)
                if np.allclose(r[0],r[-1]): r=r[:-1]
                rings.append(r)
            if not rings or abs(ring_area(rings[0]))<0.02: continue
            outer=dp(rings[0],tol)
            if ring_area(outer)<0: outer=outer[::-1]
            holes=[]
            for h in rings[1:]:
                if abs(ring_area(h))<0.005: continue
                h=dp(h,tol)
                if ring_area(h)>0: h=h[::-1]
                holes.append(h)
            polys.append((outer,holes))
        z0=ka*LAY; z1=kb*LAY+(OVL if kb<nl else 0)
        meshes.append((polys,z0,z1))
    return meshes

def _split_ring(ring,xs):
    out=[]; n=len(ring)
    for i in range(n):
        p=ring[i]; q=ring[(i+1)%n]; out.append((float(p[0]),float(p[1])))
        x0,x1=p[0],q[0]
        if abs(x1-x0)<1e-9: continue
        lo,hi=(x0,x1) if x0<x1 else (x1,x0)
        i0=np.searchsorted(xs,lo+1e-7); i1=np.searchsorted(xs,hi-1e-7)
        if i1<=i0: continue
        seq=xs[i0:i1]
        if x1<x0: seq=seq[::-1]
        for x in seq:
            t=(x-x0)/(x1-x0); out.append((float(x),float(p[1]+t*(q[1]-p[1]))))
    return out

def poly_tris(outer,holes,z0,z1,T):
    rings=[np.round(np.asarray(r,float),5) for r in [outer]+list(holes)]
    xs=np.unique(np.concatenate([r[:,0] for r in rings]))
    sr=[_split_ring(r,xs) for r in rings]
    slabs={}
    for ring in sr:
        n=len(ring)
        for i in range(n):
            a=ring[i]; b=ring[(i+1)%n]
            T.append(((a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1)))
            T.append(((a[0],a[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)))
            if abs(a[0]-b[0])<1e-9: continue
            l,r=(a,b) if a[0]<b[0] else (b,a)
            k=int(np.searchsorted(xs,l[0]-1e-6))
            slabs.setdefault(k,[]).append((l,r))
    for k,pcs in slabs.items():
        xl=xs[k]; xr=xs[k+1] if k+1<len(xs) else None
        pcs.sort(key=lambda p:p[0][1]+p[1][1])
        for j in range(0,len(pcs)-1,2):
            (l0,r0),(l1,r1)=pcs[j],pcs[j+1]
            P=[(l0[0],l0[1]),(r0[0],r0[1]),(r1[0],r1[1]),(l1[0],l1[1])]
            for tri in ((P[0],P[1],P[2]),(P[0],P[2],P[3])):
                ar=(tri[1][0]-tri[0][0])*(tri[2][1]-tri[0][1])-(tri[1][1]-tri[0][1])*(tri[2][0]-tri[0][0])
                if abs(ar)<1e-12: continue
                a,b,c=tri
                T.append(((a[0],a[1],z1),(b[0],b[1],z1),(c[0],c[1],z1)))
                T.append(((a[0],a[1],z0),(c[0],c[1],z0),(b[0],b[1],z0)))

def mesh_tris(meshes, xf=None):
    T=[]
    for polys,z0,z1 in meshes:
        for outer,holes in polys: poly_tris(outer,holes,z0,z1,T)
    return np.array(T,np.float32)

def write_stl(path,T):
    n=len(T)
    v1=T[:,1]-T[:,0]; v2=T[:,2]-T[:,0]
    nm=np.cross(v1,v2); l=np.linalg.norm(nm,axis=1,keepdims=True); l[l==0]=1; nm/=l
    rec=np.zeros(n,dtype=[('n','<f4',3),('v','<f4',(3,3)),('a','<u2')])
    rec['n']=nm; rec['v']=T
    with open(path,'wb') as f:
        f.write(b'generated'.ljust(80,b' ')); f.write(struct.pack('<I',n)); f.write(rec.tobytes())
    vol=np.sum(np.einsum('ij,ij->i',T[:,0],np.cross(T[:,1],T[:,2])))/6/1000
    print(f'{path}: {n} tris, vol~{vol:.1f} cm3, bbox {T.reshape(-1,3).min(0).round(1)}..{T.reshape(-1,3).max(0).round(1)}')

def transform(T,fn): 
    return fn(T.reshape(-1,3)).reshape(T.shape).astype(np.float32)
