from gen import text_mask
from PIL import Image, ImageDraw, ImageOps
from engine import *
import gen, gen2, sys
from gen2 import shell, cradle_y, lid_base
OUT=gen.OUT
build=gen.build

def pads(S,cx,cy,bx,by,T,h,ins=5.0):
    for sx in(-1,1):
        for sy in(-1,1):
            S.add(ZCyl(cx+sx*(bx/2-ins),cy+sy*(by/2-ins),3.0,T-0.1,T+h))

def usb_pair(S,cx,y0,y1,z0,z1,axis):
    """два окна USB-C по 11 мм с зазором 5 мм между краями"""
    for a,b in((cx-13.5,cx-2.5),(cx+2.5,cx+13.5)):
        S.cut(a,b,y0,y1,z0,z1)

def usb_ports(S,cx,y0,y1,zc):
    """порты 10x3, зазор между краями 5 (шаг 15); окна под штекер 12,4 x 6,6 по центрам портов"""
    for dx in(-7.5,7.5): S.cut(cx+dx-6.2,cx+dx+6.2,y0,y1,zc-3.3,zc+3.3)

def icon_mask(kind,cx,zc,y0,y1,mirror=False,size=6.4):
    P=50  # px/мм
    n=int(size*P); im=Image.new('L',(n,n),0); d=ImageDraw.Draw(im)
    u=lambda a,b:(a*n,b*n)
    if kind=='bolt':
        d.polygon([u(.60,0),u(.20,.54),u(.46,.54),u(.36,1),u(.82,.42),u(.56,.42),u(.72,0)],fill=255)
    else:  # жук = отладка
        w=int(0.075*n)
        d.ellipse([*u(.30,.34),*u(.70,.96)],fill=255); d.ellipse([*u(.38,.12),*u(.62,.36)],fill=255)
        for sx in(1,-1):
            f=lambda a:(a if sx==1 else 1-a)
            d.line([u(f(.40),.14),u(f(.30),.02)],fill=255,width=w)
            for ya,yb,xa in((.50,.40,.08),(.65,.66,.05),(.80,.92,.10)):
                d.line([u(f(.32),ya),u(f(xa),yb)],fill=255,width=w)
    if mirror: im=ImageOps.mirror(im)
    nx=int(math.ceil(size/G))+2; nz=int(math.ceil(size/LAY))+2
    SX,SZ=int(G*P),int(LAY*P)
    can=Image.new('L',(nx*SX,nz*SZ),0); can.paste(im,((nx*SX-n)//2,(nz*SZ-n)//2))
    a=np.asarray(can,np.float32)/255.0
    cov=a.reshape(nz,SZ,nx,SX).mean((1,3))[::-1]
    x0=round((cx-nx*G/2)/G)*G; z0=round((zc-nz*LAY/2)/LAY)*LAY
    return XZMask(x0,z0,(0.5-cov).astype(np.float32),y0,y1)

def finger_notches(S,Wi,W,yc,H):
    for sx in(-1,1):
        x0,x1=(Wi-0.05,W+1) if sx>0 else (-W-1,-Wi+0.05)
        S.cut(x0,x1,yc-7,yc+7,H-3.0,H+1)

def lid_ring(L,W,Wi,y0,y1,T,zl,zt):
    L.box(-W,W,y0,y1,zl,zt)
    r=Wi-0.1
    L.box(-r,r,y0+T+0.1,y1-T-0.1,zl-3,zl)
    L.cut(-(r-1.3),r-1.3,y0+T+1.4,y1-T-1.4,zl-3.1,zl-0.0001)

def receiver():
    W,Wi,T,H=35.5,33.0,2.5,36.0
    YB=82.5
    TX,ZC=24.0,H-7.0
    S=Solid(); shell(S,W,Wi,0,YB,T,H)
    pads(S,0,43,50,70,T,3.0)                              # площадки под скотч для макетки
    usb_ports(S,-10,-1,3.0,12.8)                          # 2 × USB-C в передней стенке
    S.sub(icon_mask('bolt',-17.5,21.4,-0.1,0.6)); S.sub(icon_mask('bug',-2.5,21.4,-0.1,0.6))
    S.sub(YCyl(TX,ZC,6.9,-1,3.0))
    finger_notches(S,Wi,W,41,H)
    build('receiver_body',S,H)
    zl,zt=H,H+4.0; cy=49.5
    L=Solid(); lid_ring(L,W,Wi,0,YB,T,zl,zt)
    L.box(TX-6.5,TX+6.5,2.6,48.0,ZC,zl+0.1)
    L.add(YCyl(TX,ZC,6.5,0.5,48.0))
    L.sub(YCyl(TX,ZC,4.5,0.0,44.0))
    for y in(8.5,23.5,38.5): L.add(YCyl(TX,ZC,4.7,y-0.5,y+0.5))
    for y in(8.5,23.5,38.5): L.sub(YCyl(TX,ZC,1.0,y-1,y+1))
    L.cut(TX-1.8,TX+1.8,43.9,45.2,ZC-1.8,ZC+1.8)
    L.cut(TX-2.8,TX+2.8,45.0,49.0,ZC-2.25,ZC+2.25)
    L.sub(Box(-18.95,18.95,cy-29.2,cy+29.2,zl,zl+3.0))     # гнездо модуля
    L.sub(Box(-17.5,17.5,cy-24.0,cy+24.0,zl+2.9,zt+0.1))    # окно 48 x 35
    for sx in(-1,1): L.sub(ZCyl(sx*26.0,60.0,0.9,zl-0.1,zl+3.0))
    build('receiver_lid',L,zt,flip=zt)
    B=Solid(); B.box(-28,28,-3.5,3.5,0,4.0)
    for sx in(-1,1): B.sub(ZCyl(sx*26.0,0,1.1,-1,5))
    build('receiver_screen_bar',B,4.0)

def transmitter():
    W,Wi,T,H=40.5,38.0,2.5,30.0
    YB=76.5
    LX,LZ=18.5,21.6
    S=Solid(); shell(S,W,Wi,0,YB,T,H)
    ex,ey=18.5,40.0
    cradle_y(S,ex,ey,28,64,T,3.0,1.6,14)
    usb_ports(S,ex,YB-T-0.1,YB+1,8.7)                         # 2 × USB-C в задней стенке
    S.sub(icon_mask('bolt',ex+7.5,17.5,YB-0.6,YB+0.1,True)); S.sub(icon_mask('bug',ex-7.5,17.5,YB-0.6,YB+0.1,True))
    S.sub(YCyl(LX,LZ,4.5,-1,3.0))
    finger_notches(S,Wi,W,38,H)
    build('transmitter_body',S,H)
    zl,zt=H,H+3.0
    L=Solid(); lid_ring(L,W,Wi,0,YB,T,zl,zt)
    L.box(9.2,10.8,2.6,36.4,15.0,zl+0.1); L.box(26.2,27.8,2.6,36.4,15.0,zl+0.1)
    L.box(9.2,27.8,2.6,36.4,15.0,17.0)
    L.box(LX-5.5,LX+5.5,2.6,16.0,LZ,zl+0.1); L.add(YCyl(LX,LZ,5.5,2.6,16.0))
    L.sub(YCyl(LX,LZ,3.1,2.0,17.5))
    L.sub(ZCyl(LX,9.0,1.3,LZ,zl+0.1)); L.sub(ZCyl(LX,9.0,1.7,zl,zt+0.1))
    xs=(-31.0,-13.0,5.0)
    for x in xs: L.add(ZCyl(x,11.0,4.4,24.6,zl))
    for xm in((xs[0]+xs[1])/2,(xs[1]+xs[2])/2):               # светоизолирующие перегородки
        L.box(xm-0.6,xm+0.6,3.0,19.0,21.0,zl+0.1)
    for x in xs: L.sub(ZCyl(x,11.0,2.6,24.5,zt+0.1)); L.sub(ZCyl(x,11.0,3.1,24.5,26.0))
    for x,t,dx in zip(xs,('ПИТАНИЕ','ТЕЛЕФОН','ПЕРЕДАЧА'),(0.0,0.0,2.5)):
        L.sub(text_mask(t,x+dx,4.8,2.2,zt-0.6,zt+0.1))
    build('transmitter_lid',L,zt,flip=zt)

if __name__=='__main__':
    w=sys.argv[1] if len(sys.argv)>1 else 'all'
    if w in('all','tx'): transmitter()
    if w in('all','rx'): receiver()
