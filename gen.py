from engine import *
import sys, os
from PIL import Image, ImageDraw, ImageFont
import matplotlib
OUT='/mnt/user-data/outputs'
FONT=os.path.join(os.path.dirname(matplotlib.__file__),'mpl-data/fonts/ttf/DejaVuSans-Bold.ttf')

def text_mask(txt,cx,cy,cap_h,z0,z1):
    SS=5; px=G/SS
    fs=int(cap_h/px*1.38)
    font=ImageFont.truetype(FONT,fs)
    tmp=Image.new('L',(10,10)); d=ImageDraw.Draw(tmp)
    l,t,r,b=d.textbbox((0,0),txt,font=font)
    w=r-l; h=b-t
    nx=int(math.ceil(w/SS))+6; ny=int(math.ceil(h/SS))+6
    img=Image.new('L',(nx*SS,ny*SS),0); d=ImageDraw.Draw(img)
    d.text(((nx*SS-w)//2-l,(ny*SS-h)//2-t),txt,font=font,fill=255)
    a=np.asarray(img,np.float32)/255.0
    cov=a.reshape(ny,SS,nx,SS).mean((1,3))[::-1]   # y вверх
    x0=round((cx-nx*G/2)/G)*G; y0=round((cy-ny*G/2)/G)*G
    return Mask(x0,y0,(0.5-cov).astype(np.float32),z0,z1)

def shell(S,W,Wi,y0,y1,T,H):
    S.box(-W,W,y0,y1,0,H)
    S.cut(-Wi,Wi,y0+T,y1-T,T,H+1)

def posts(S,pc,T,H):
    for (x,y) in pc:
        S.add(ZCyl(x,y,3.0,T-0.1,H)); 
    for (x,y) in pc:
        S.sub(ZCyl(x,y,1.3,H-10,H+0.1))

def standoffs(S,cx,cy,bx,by,T,h,ins=3.0):
    pts=[(cx+sx*(bx/2-ins),cy+sy*(by/2-ins)) for sx in(-1,1) for sy in(-1,1)]
    for p in pts: S.add(ZCyl(p[0],p[1],3.0,T-0.1,T+h))
    for p in pts: S.sub(ZCyl(p[0],p[1],0.9,T+h-4,T+h+0.1))

def cradle(S,cx,cy,bx,by,T,ped_h,pcb_t,stop,ped_w):
    """гнездо под плату без отверстий: подиум, боковые рёбра, упор. stop: '-x','+y'"""
    hx=bx/2+0.2; hy=by/2+0.2; zb=T+ped_h; zt=zb+pcb_t
    if stop in('-x','+x'):
        S.box(cx-hx,cx+hx,cy-ped_w/2,cy+ped_w/2,T-0.1,zb)
        S.box(cx-hx-1.6,cx+hx,cy+hy,cy+hy+1.6,T-0.1,zt)
        S.box(cx-hx-1.6,cx+hx,cy-hy-1.6,cy-hy,T-0.1,zt)
        if stop=='-x': S.box(cx-hx-1.6,cx-hx,cy-hy,cy+hy,T-0.1,zt)
    else:
        S.box(cx-ped_w/2,cx+ped_w/2,cy-hy,cy+hy,T-0.1,zb)
        S.box(cx+hx,cx+hx+1.6,cy-hy-0,cy+hy+1.6,T-0.1,zt)
        S.box(cx-hx-1.6,cx-hx,cy-hy,cy+hy+1.6,T-0.1,zt)
        S.box(cx-hx,cx+hx,cy+hy,cy+hy+1.6,T-0.1,zt)

def slots(S,lst,T,sx,sy):
    for (x,y) in lst: S.cut(x-sx/2,x+sx/2,y-sy/2,y+sy/2,-1,T+0.2)

def lid_common(L,W,y0,y1,zl,zt,pc,lipI,Wi,T):
    L.box(-W,W,y0,y1,zl,zt)
    ring=Wi-0.3
    L.box(-ring,ring,y0+T+0.3,y1-T-0.3,zl-3,zl)
    L.cut(-(ring-1.3),ring-1.3,y0+T+1.6,y1-T-1.6,zl-3.1,zl-0.0001)
    for (x,y) in pc: L.sub(ZCyl(x,y,3.5,zl-3.2,zl))
    for (x,y) in pc:
        L.sub(ZCyl(x,y,1.7,zl-0.1,zt+0.1)); L.sub(ZCyl(x,y,3.1,zt-2,zt+0.1))

def button_guides(L,bx,by_list,zl,zt,zbot):
    for y in by_list: L.add(ZCyl(bx,y,3.2,zbot,zl))
    for y in by_list: L.sub(ZCyl(bx,y,1.7,zbot-0.1,zt+0.1))

def flip_lid(T,zt,ymid=0):
    return transform(T,lambda P: np.c_[P[:,0],-P[:,1],zt-P[:,2]])

def build(name,S,zmax,flip=None):
    print(name,end=' ',flush=True)
    m=slice_solid(S,zmax); T=mesh_tris(m)
    if flip is not None: T=flip_lid(T,flip)
    write_stl(f'{OUT}/{name}.stl',T)

# ===================== ПРИЁМНИК =====================
def receiver():
    W,Wi,T,H=42.5,40.0,2.5,26.0
    YF,YB=50.0,150.5; YBi=YB-T
    pc=[(sx*37.0,y) for sx in(-1,1) for y in(55.5,145.0)]
    S=Solid(); shell(S,W,Wi,YF,YB,T,H); posts(S,pc,T,H)
    zc=10.0
    # трубка (на «санях» для печати без поддержек)
    S.box(-7,7,0,YF+0.1,0,zc); S.add(YCyl(0,zc,7,0,YF+0.1))
    S.sub(YCyl(0,zc,4.5,-1,46.0))
    for y in(8.0,23.0,38.0): S.add(YCyl(0,zc,4.7,y-0.5,y+0.5))
    for y in(8.0,23.0,38.0): S.sub(YCyl(0,zc,1.0,y-1,y+1))
    S.cut(-1.8,1.8,45.9,47.2,zc-1.8,zc+1.8)      # окно 3.6x3.6 перед активной зоной
    S.cut(-2.8,2.8,47.0,YF+T+0.5,zc-2.25,zc+2.25) # карман BPW34 5.6x4.5
    # плата усилителя 70x50 на 4 стойках
    standoffs(S,0,85,70,50,T,5.0)
    # плата ESP32-S3 64x28, USB к правой стенке
    ey=127.0; ex=Wi-0.4-32.0
    cradle(S,ex,ey,64,28,T,3.5,1.6,'-x',10)
    slots(S,[(ex-18,ey-18.6),(ex-18,ey+18.6),(ex+14,ey-18.6),(ex+14,ey+18.6)],T,3.6,1.8)
    S.cut(Wi-0.1,W+1,ey-13,ey+13,5.5,14.0)       # USB
    build('receiver_body',S,H)
    # ---- крышка (печатается лицом вниз)
    zl,zt=H,H+4.0
    L=Solid(); lid_common(L,W,YF,YB,zl,zt,pc,None,Wi,T)
    cy=85.0
    L.sub(Box(-29.2,29.2,cy-18.95,cy+18.95,zl-0.1,zl+3.0))      # карман модуля 58.4x37.9
    L.sub(Box(-24.5,24.5,cy-17.5,cy+17.5,zl+2.9,zt+0.1))        # окно 49x35
    for sx in(-1,1): L.sub(ZCyl(sx*34.5,cy,0.9,zl-0.1,zl+3.0))  # под винты планки
    button_guides(L,ex+24,[ey-9,ey+9],zl,zt,13.0)
    build('receiver_lid',L,zt,flip=zt)
    # ---- планка крепления экрана
    B=Solid(); B.box(-37.5,37.5,-3.5,3.5,0,4.0)
    for sx in(-1,1): B.sub(ZCyl(sx*34.5,0,1.1,-1,5))
    build('receiver_screen_bar',B,4.0)

# ===================== ПЕРЕДАТЧИК =====================
def transmitter():
    W,Wi,T,H=40.5,38.0,2.5,24.0
    YF,YB=0.0,75.5
    pc=[(sx*35.0,y) for sx in(-1,1) for y in(5.5,70.0)]
    S=Solid(); shell(S,W,Wi,YF,YB,T,H); posts(S,pc,T,H)
    zl=9.0
    S.box(-7,7,0,16,0,zl); S.add(YCyl(0,zl,7,0,16))
    S.sub(YCyl(0,zl,3.1,-1,17.0))                  # окно под лазер d6.2, длина канала 16 мм
    S.sub(ZCyl(0,8.0,1.3,zl,17.0))                 # M3 стопорный винт сверху
    # плата лазера 15x18.5
    cradle(S,0,26.5,15,18.5,T,2.0,1.6,'+y',10)
    slots(S,[(-11.5,26.5),(11.5,26.5)],T,1.8,3.6)
    # ESP32-S3
    ey=52.0; ex=Wi-0.4-32.0
    cradle(S,ex,ey,64,28,T,3.5,1.6,'-x',10)
    slots(S,[(ex-18,ey-18.6),(ex-18,ey+18.6),(ex+14,ey-18.6),(ex+14,ey+18.6)],T,3.6,1.8)
    S.cut(Wi-0.1,W+1,ey-13,ey+13,5.5,14.0)
    build('transmitter_body',S,H)
    zl2,zt=H,H+3.0
    L=Solid(); lid_common(L,W,YF,YB,zl2,zt,pc,None,Wi,T)
    for x in(-24,0,24):                              # светодиоды 5 мм
        L.add(ZCyl(x,28.0,4.4,19.0,zl2))
    for x in(-24,0,24):
        L.sub(ZCyl(x,28.0,2.6,18.9,zt+0.1)); L.sub(ZCyl(x,28.0,3.1,18.9,20.4))
    L.sub(ZCyl(0,8.0,2.3,zl2-0.1,zt+0.1))            # доступ к стопорному винту
    button_guides(L,ex+24,[ey-9,ey+9],zl2,zt,13.0)
    for x,t in((-24,'ПИТАНИЕ'),(0,'ТЕЛЕФОН'),(24,'ПЕРЕДАЧА')):
        L.sub(text_mask(t,x,20.5,2.6,zt-0.4,zt+0.1))
    build('transmitter_lid',L,zt,flip=zt)

if __name__=='__main__':
    which=sys.argv[1] if len(sys.argv)>1 else 'all'
    if which in('all','tx'): transmitter()
    if which in('all','rx'): receiver()
