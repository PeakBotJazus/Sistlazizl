from gen import text_mask, posts, slots, button_guides, flip_lid, OUT
from engine import *
import gen, sys

def shell(S,W,Wi,y0,y1,T,H):
    S.box(-W,W,y0,y1,0,H); S.cut(-Wi,Wi,y0+T,y1-T,T,H+1)

def posts_r(S,pc,T,H,r=2.6):
    for (x,y) in pc: S.add(ZCyl(x,y,r,T-0.1,H))
    for (x,y) in pc: S.sub(ZCyl(x,y,1.3,H-10,H+0.1))

def lid_base(L,W,Wi,y0,y1,T,zl,zt,pc):
    L.box(-W,W,y0,y1,zl,zt)
    ring=Wi-0.3
    L.box(-ring,ring,y0+T+0.3,y1-T-0.3,zl-3,zl)
    L.cut(-(ring-1.3),ring-1.3,y0+T+1.6,y1-T-1.6,zl-3.1,zl-0.0001)
    for (x,y) in pc: L.sub(ZCyl(x,y,3.4,zl-3.2,zl))
    for (x,y) in pc:
        L.sub(ZCyl(x,y,1.7,zl-0.1,zt+0.1)); L.sub(ZCyl(x,y,3.1,zt-2,zt+0.1))

def cradle_y(S,cx,cy,bx,by,T,ped_h,pcb_t,ped_w=10):
    hx=bx/2+0.2; hy=by/2+0.2; zb=T+ped_h; zt=zb+pcb_t
    S.box(cx-ped_w/2,cx+ped_w/2,cy-hy,cy+hy,T-0.1,zb)
    S.box(cx+hx,cx+hx+1.6,cy-hy-1.6,cy+hy,T-0.1,zt)
    S.box(cx-hx-1.6,cx-hx,cy-hy-1.6,cy+hy,T-0.1,zt)
    S.box(cx-hx,cx+hx,cy-hy-1.6,cy-hy,T-0.1,zt)

def standoffs(S,cx,cy,bx,by,T,h,ins=3.0):
    pts=[(cx+sx*(bx/2-ins),cy+sy*(by/2-ins)) for sx in(-1,1) for sy in(-1,1)]
    for p in pts: S.add(ZCyl(p[0],p[1],3.0,T-0.1,T+h))
    for p in pts: S.sub(ZCyl(p[0],p[1],0.9,T+h-3.5,T+h+0.1))

def receiver():
    W,Wi,T,H=35.5,33.0,2.5,30.0
    YB=82.5
    pc=[(-30.0,5.5),(-30.0,77.0),(30.0,77.0),(30.0,58.0)]
    TX,ZC=24.0,23.0
    S=Solid(); shell(S,W,Wi,0,YB,T,H); posts_r(S,pc,T,H,3.0)
    standoffs(S,0,43,50,70,T,3.0)                       # макетка 50x70, на ней же ESP32
    S.cut(-23,3,-1,3.0,8.5,17.5)                         # USB ESP32 в передней стенке
    S.sub(YCyl(TX,ZC,6.9,-1,3.0))                        # отверстие под трубку
    build('receiver_body',S,H)
    zl,zt=H,H+4.0; cy=49.5
    L=Solid(); lid_base(L,W,Wi,0,YB,T,zl,zt,pc)
    # трубка с фотодиодом висит на крышке над платой
    L.box(TX-6.5,TX+6.5,2.6,48.0,ZC,zl+0.1)
    L.add(YCyl(TX,ZC,6.5,0.5,48.0))
    L.sub(YCyl(TX,ZC,4.5,0.0,44.0))
    for y in(8.5,23.5,38.5): L.add(YCyl(TX,ZC,4.7,y-0.5,y+0.5))
    for y in(8.5,23.5,38.5): L.sub(YCyl(TX,ZC,1.0,y-1,y+1))
    L.cut(TX-1.8,TX+1.8,43.9,45.2,ZC-1.8,ZC+1.8)
    L.cut(TX-2.8,TX+2.8,45.0,49.0,ZC-2.25,ZC+2.25)
    # экран
    L.sub(Box(-18.95,18.95,cy-29.2,cy+29.2,zl,zl+3.0))
    L.sub(Box(-17.5,17.5,cy-24.5,cy+24.5,zl+2.9,zt+0.1))
    for sx in(-1,1): L.sub(ZCyl(sx*26.0,60.0,0.9,zl-0.1,zl+3.0))
    button_guides(L,-10-9,[16.0],zl,zt,16.0); button_guides(L,-10+9,[16.0],zl,zt,16.0)
    build('receiver_lid',L,zt,flip=zt)
    B=Solid(); B.box(-28,28,-3.5,3.5,0,4.0)
    for sx in(-1,1): B.sub(ZCyl(sx*26.0,0,1.1,-1,5))
    build('receiver_screen_bar',B,4.0)

def transmitter():
    W,Wi,T,H=40.5,38.0,2.5,30.0
    YB=76.5
    pc=[(sx*35.4,y) for sx in(-1,1) for y in(5.1,71.4)]
    LX,LZ=18.5,21.6
    S=Solid(); shell(S,W,Wi,0,YB,T,H); posts_r(S,pc,T,H,2.6)
    ex,ey=18.5,40.0
    cradle_y(S,ex,ey,28,64,T,3.0,1.6)
    slots(S,[(ex-18.4,44.0),(ex+18.4,44.0),(ex-18.4,62.0),(ex+18.4,62.0)],T,1.8,3.6)
    S.cut(ex-13,ex+13,YB-T-0.1,YB+1,5.5,14.0)            # USB в задней стенке
    S.sub(YCyl(LX,LZ,4.5,-1,3.0))                        # окно под лазер
    build('transmitter_body',S,H)
    zl,zt=H,H+3.0
    L=Solid(); lid_base(L,W,Wi,0,YB,T,zl,zt,pc)
    # лазер висит на крышке над платой ESP32
    L.box(9.2,10.8,2.6,36.4,15.0,zl+0.1); L.box(26.2,27.8,2.6,36.4,15.0,zl+0.1)
    L.box(9.2,27.8,2.6,36.4,15.0,17.0)
    L.box(LX-5.5,LX+5.5,2.6,16.0,LZ,zl+0.1); L.add(YCyl(LX,LZ,5.5,2.6,16.0))
    L.sub(YCyl(LX,LZ,3.1,2.0,17.5))
    L.sub(ZCyl(LX,9.0,1.3,LZ,zl+0.1)); L.sub(ZCyl(LX,9.0,1.7,zl,zt+0.1))
    # светодиоды в ряд у переднего края
    xs=(-33.0,-14.2,4.6)
    for x in xs: L.add(ZCyl(x,11.0,4.4,24.6,zl))
    for x in xs: L.sub(ZCyl(x,11.0,2.6,24.5,zt+0.1)); L.sub(ZCyl(x,11.0,3.1,24.5,26.0))
    button_guides(L,ex-9,[YB-T-2-6],zl,zt,12.0); button_guides(L,ex+9,[YB-T-2-6],zl,zt,12.0)
    for x,t in zip(xs,('ПИТАНИЕ','ТЕЛЕФОН','ПЕРЕДАЧА')):
        L.sub(text_mask(t,x,4.6,2.2,zt-0.4,zt+0.1))
    build('transmitter_lid',L,zt,flip=zt)

build=gen.build
if __name__=='__main__':
    w=sys.argv[1] if len(sys.argv)>1 else 'all'
    if w in('all','tx'): transmitter()
    if w in('all','rx'): receiver()
