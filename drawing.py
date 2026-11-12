import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import PathPatch, Rectangle, Circle
from matplotlib.path import Path
import numpy as np, gen3
from engine import *
cap={}
gen3.build=lambda name,S,zmax,flip=None: cap.__setitem__(name,(S,zmax))
gen3.receiver(); gen3.transmitter()
FS=7; LW=0.8
def section(ax,name,z,fc='#d9dde3'):
    S,zm=cap[name]
    for polys,z0,z1 in slice_solid(S,zm,verbose=False):
        if z0<=z<z1:
            for o,hs in polys:
                v=[];c=[]
                for r in [o]+hs:
                    v+=list(r)+[r[0]]; c+=[Path.MOVETO]+[Path.LINETO]*(len(r)-1)+[Path.CLOSEPOLY]
                ax.add_patch(PathPatch(Path(v,c),fc=fc,ec='k',lw=LW))
def dash(ax,x0,x1,y0,y1,col='#c0392b'):
    ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec=col,lw=0.7,ls=(0,(4,2))))
def dcirc(ax,x,y,r,col='#c0392b',fill=False):
    ax.add_patch(Circle((x,y),r,fill=fill,ec=col,lw=0.7,ls=(0,(4,2)) if not fill else '-',fc='#fff' if fill else 'none'))
def hdim(ax,x1,x2,y,txt,src=None,off=0):
    ax.annotate('',xy=(x1,y),xytext=(x2,y),arrowprops=dict(arrowstyle='<|-|>',lw=0.6,color='#1a5fb4',shrinkA=0,shrinkB=0,mutation_scale=6))
    if src is not None:
        for x in(x1,x2): ax.plot([x,x],[src,y+(1.5 if y>src else -1.5)],color='#1a5fb4',lw=0.4)
    ax.text((x1+x2)/2,y+(1.2 if off==0 else -3.2),txt,ha='center',fontsize=FS,color='#1a5fb4')
def vdim(ax,y1,y2,x,txt,src=None,side=1):
    ax.annotate('',xy=(x,y1),xytext=(x,y2),arrowprops=dict(arrowstyle='<|-|>',lw=0.6,color='#1a5fb4',shrinkA=0,shrinkB=0,mutation_scale=6))
    if src is not None:
        for y in(y1,y2): ax.plot([src,x+(1.5 if x>src else -1.5)],[y,y],color='#1a5fb4',lw=0.4)
    ax.text(x+side*1.5,(y1+y2)/2,txt,ha='left' if side>0 else 'right',va='center',fontsize=FS,color='#1a5fb4',rotation=90)
def note(ax,x,y,txt,**k):
    k.setdefault('fontsize',FS); ax.text(x,y,txt,**k)
def sheet(fig,title,sub,n):
    fig.text(0.03,0.955,title,fontsize=13,weight='bold')
    fig.text(0.03,0.93,sub,fontsize=8,color='#444')
    fig.add_artist(Rectangle((0.015,0.015),0.97,0.97,transform=fig.transFigure,fill=False,lw=1.2))
    fig.text(0.97,0.025,f'Лист {n}/4   Размеры в мм   Красный пунктир — детали внутри / на другой детали',ha='right',fontsize=7,color='#444')
def axes2(fig):
    a=fig.add_axes([0.04,0.07,0.44,0.83]); b=fig.add_axes([0.52,0.07,0.44,0.83])
    for x in(a,b): x.set_aspect('equal'); x.axis('off')
    return a,b
def axes1(fig):
    a=fig.add_axes([0.04,0.07,0.92,0.83]); a.set_aspect('equal'); a.axis('off'); return a

pp=PdfPages('/mnt/user-data/outputs/drawings.pdf')
# ================= лист 1: приёмник, вид сверху =================
fig=plt.figure(figsize=(11.69,8.27)); sheet(fig,'Приёмник — вид сверху','Слева корпус (сечение на высоте 12 мм), справа крышка (вид сверху, как на собранном устройстве)',1)
a,b=axes2(fig)
section(a,'receiver_body',12.0)
for sx in(-1,1):
    for sy in(-1,1): dcirc(a,sx*20,43+sy*30,3.0)
dash(a,-25,25,8,78,'#c0392b'); dash(a,-24,4,8,72,'#8e44ad')
dash(a,17.5,30.5,0.5,48,'#e67e22')
note(a,-24,10,'ESP32-S3 64×28',color='#8e44ad'); note(a,-24,75,'макетная плата 50×70',color='#c0392b')
note(a,19,20,'труба\n(на крышке)',color='#e67e22'); note(a,-22,50,'4 площадки Ø6 h3\nпод скотч',color='#c0392b')
hdim(a,-35.5,35.5,-9,'71',src=0); hdim(a,-33,33,-15,'66 (внутр.)',src=2.5)
vdim(a,0,82.5,43,'82,5',src=35.5); vdim(a,2.5,80,-41,'77 (внутр.)',src=-33,side=-1)
hdim(a,-23.7,-11.3,-3.5,'12,4'); hdim(a,-8.7,3.7,-3.5,'12,4'); hdim(a,-11.3,-8.7,-6.2,'2,6')
note(a,-10,-11.8,'2 × USB-C: порты 10×3, шаг 15; окна z 9,4…16,2; значки над окнами',ha='center',color='#222')
note(a,24,-5,'Ø13,8',ha='center',color='#222'); a.plot([24,24],[-3,0],color='k',lw=0.5)
note(a,0,86,'Стенка 2,5   Высота корпуса 36   Выемки под палец 14×3 на боковых стенках',ha='center',color='#222')
a.set_xlim(-48,52); a.set_ylim(-18,92)
section(b,'receiver_lid',38.0)
dash(b,-18.95,18.95,20.3,78.7,'#2c7a2c')
dash(b,17.5,30.5,0.5,48,'#e67e22'); dash(b,-28,28,56.5,63.5,'#c0392b')
for sx in(-1,1): dcirc(b,sx*26,60,0.9,'#c0392b')
note(b,-17,44,'ЭКРАН\n48×35',ha='left',color='#222'); note(b,19,25,'труба Ø13',color='#e67e22'); note(b,-27,53.5,'планка 56×7, 2×M2',color='#c0392b')
note(b,-18.5,16.5,'гнездо модуля 58,4×37,9 (глуб. 3)',color='#2c7a2c')
hdim(b,-17.5,17.5,80,'35',src=73.5); vdim(b,25.5,73.5,-22,'48',src=-17.5,side=-1)
vdim(b,0,25.5,-29,'25,5',src=-17.5,side=-1); hdim(b,-35.5,35.5,-9,'71',src=0); vdim(b,0,82.5,43,'82,5',src=35.5)
hdim(b,-26,26,70,'52',src=63.5)
note(b,0,86,'Толщина крышки 4,  выступ-фиксатор высотой 3 (зазор 0,1 на сторону)',ha='center',color='#222')
b.set_xlim(-48,52); b.set_ylim(-18,92)
pp.savefig(fig); plt.close(fig)
# ================= лист 2: приёмник, разрез =================
fig=plt.figure(figsize=(11.69,8.27)); sheet(fig,'Приёмник — разрез вдоль оси трубки (x = 24)','Перед корпуса слева',2)
a=axes1(fig)
G='#d9dde3'
def R(y0,y1,z0,z1,fc=G,ec='k',ls='-'): a.add_patch(Rectangle((y0,z0),y1-y0,z1-z0,fc=fc,ec=ec,lw=LW,ls=ls))
R(0,82.5,0,2.5); R(0,2.5,0,36); R(80,82.5,0,36); R(0,82.5,36,40)
R(2.6,80,33,36,fc='#eef0f3')           # фиксатор крышки
R(0.5,48,22.5,35.5,fc='#e8d9f5'); R(2.6,48,29,36,fc='#e8d9f5')   # труба + подвес
R(0,44,24.5,33.5,fc='white')           # канал
for y in(8.5,23.5,38.5): R(y-0.5,y+0.5,24.5,33.5,fc='#8e44ad'); R(y-0.5,y+0.5,28,30,fc='white')
R(44,45,27.2,30.8,fc='white'); R(45,49,26.75,31.25,fc='#cfe3ff')
R(8,78,5.5,7.1,fc='#c0392b'); 
for y in(13,73): R(y-3,y+3,2.5,5.5,fc='#f1c0bb')
R(8,72,9.6,17.6,fc='none',ec='#8e44ad',ls=(0,(4,2)))
R(-0.1,2.6,9.4,16.2,fc='white')
R(20.3,78.7,36,39,fc='#cfe3ff'); R(25.5,73.5,39,40,fc='white')
vdim(a,0,40,-6,'40 всего',src=0); vdim(a,0,36,-12,'36 корпус',src=0); vdim(a,2.5,36,-18,'33,5 внутр.',src=0)
vdim(a,36,40,86,'4 крышка',src=82.5)
vdim(a,22.5,35.5,52,'Ø13',src=48); vdim(a,24.5,33.5,56,'Ø9',src=48)
vdim(a,0,29,61,'ось трубки z=29',src=48)
vdim(a,7.1,22.5,66,'15,4 свободно под трубкой',src=48,side=1)
hdim(a,0.5,48,43,'длина трубки 47,5',src=35.5); hdim(a,8.5,23.5,20,'15'); hdim(a,23.5,38.5,20,'15')
note(a,8.5,41.3,'диафрагмы Ø2, 3 шт',ha='left',color='#8e44ad'); note(a,50,41.3,'BPW34, окно 3,6×3,6',ha='left',color='#2b6cb0')
note(a,0,-3,'отв. Ø13,8 в стенке',ha='left'); note(a,30,12,'ESP32 на макетной плате (скотч)',color='#c0392b')
note(a,60,32,'гнездо экрана 58,4 (глуб. 3)\nокно 48',color='#2b6cb0'); note(a,-2,12,'USB ×2',ha='right')
a.set_xlim(-24,90); a.set_ylim(-8,46)
pp.savefig(fig); plt.close(fig)
# ================= лист 3: передатчик, вид сверху =================
fig=plt.figure(figsize=(11.69,8.27)); sheet(fig,'Передатчик — вид сверху','Слева корпус (сечение на высоте 6,5 мм), справа крышка (вид сверху, как на собранном устройстве)',3)
a,b=axes2(fig)
section(a,'transmitter_body',6.5)
dash(a,4.5,32.5,8,72,'#8e44ad'); note(a,6,40,'ESP32-S3\n64×28\nна скотч',color='#8e44ad')
dcirc(a,18.5,0,4.5)
hdim(a,-40.5,40.5,-9,'81',src=0); vdim(a,0,76.5,45,'76,5',src=40.5); hdim(a,-38,38,-15,'76 (внутр.)',src=2.5)
hdim(a,4.8,17.2,80,'12,4',src=76.5); hdim(a,19.8,32.2,80,'12,4',src=76.5); hdim(a,17.2,19.8,85,'2,6',src=76.5)
note(a,18.5,89,'2 × USB-C: порты 10×3, шаг 15; окна z 5,4…12; значки над окнами',ha='center',color='#222')
note(a,-30,25,'пластина-подиум под\nскотч 14 мм',color='#8e44ad')
note(a,0,-20,'Стенка 2,5; высота 30; выемки под палец 14×3 по бокам',ha='center',color='#222')
a.set_xlim(-48,52); a.set_ylim(-24,94)
section(b,'transmitter_lid',32.0)
dash(b,9.2,27.8,2.6,36.4,'#c0392b'); dcirc(b,18.5,9,5.5,'#c0392b')
for xm in(-22,-4): dash(b,xm-0.6,xm+0.6,3,19,'#e67e22')
for x in(-31,-13,5): dcirc(b,x,11,4.4,'#2c7a2c')
for x,t in zip((-31,-13,5),('ПИТАНИЕ','ТЕЛЕФОН','ПЕРЕДАЧА')): note(b,x,3.2,t,ha='center',color='#222')
hdim(b,-31,-13,26,'18',src=11); hdim(b,-13,5,26,'18',src=11); note(b,-31,15.5,'Ø5,2',ha='center',color='#222')
note(b,18.5,25,'лоток лазера\n(на крышке)',ha='center',color='#c0392b'); note(b,-24,22,'перегородки\nмежду светодиодами',ha='center',color='#e67e22')
note(b,18.5,5.2,'M3',ha='center',color='#222',fontsize=6)
hdim(b,-40.5,40.5,-9,'81',src=0); vdim(b,0,76.5,45,'76,5',src=40.5); vdim(b,0,11,-44,'11',src=-31,side=-1)
note(b,0,60,'Крышка снимается без винтов:\nвыступ-фиксатор, зазор 0,1 на сторону',ha='center',color='#222')
b.set_xlim(-48,52); b.set_ylim(-24,94)
pp.savefig(fig); plt.close(fig)
# ================= лист 4: передатчик, разрез =================
fig=plt.figure(figsize=(11.69,8.27)); sheet(fig,'Передатчик — разрез вдоль оси лазера (x = 18,5)','Перед корпуса слева',4)
a=axes1(fig)
R(0,76.5,0,2.5); R(0,2.5,0,30); R(74,76.5,0,30); R(0,76.5,30,33)
R(2.6,74,27,30,fc='#eef0f3')
R(8,72,2.5,5.5,fc='#f1c0bb'); R(8,72,5.5,13.5,fc='none',ec='#8e44ad',ls=(0,(4,2)))
R(74-0.1,76.6,5.4,12.0,fc='white')
R(2.6,36.4,15,17,fc='#e8d9f5'); R(2.6,16,16.1,27.1,fc='#e8d9f5'); R(2.6,16,21.6,30,fc='#e8d9f5')
R(2.0,17.5,18.5,24.7,fc='white')
R(17,35.5,17,18.6,fc='#c8e6c9'); R(6,17,18.6,24.6,fc='#f5c6c6')
a.plot([-12,6],[21.6,21.6],color='#c0392b',lw=1.6); a.annotate('',xy=(-12,21.6),xytext=(-4,21.6),arrowprops=dict(arrowstyle='-|>',color='#c0392b'))
R(-0.1,2.6,17.1,26.1,fc='white')
vdim(a,0,33,-8,'33 всего',src=0); vdim(a,0,30,-14,'30 корпус',src=0); vdim(a,2.5,30,-20,'27,5 внутр.',src=0)
vdim(a,0,21.6,82,'ось лазера z=21,6',src=76.5); vdim(a,0,15,88,'низ лотка 15',src=76.5)
vdim(a,5.5,13.5,94,'ESP32 5,5…13,5',src=76.5)
hdim(a,2.6,16,35,'канал 13,4',src=27.1); hdim(a,16.8,35.5,12,'плата KY-008 18,5',src=17)
note(a,-2,21.6+5.2,'отв. Ø9 в стенке',ha='right'); note(a,10,28.8,'Ø6,2\nстопор M3 сверху',ha='center',fontsize=6)
note(a,45,10,'ESP32-S3 на скотч',color='#8e44ad'); note(a,76,3,'USB ×2',ha='right')
a.set_xlim(-28,100); a.set_ylim(-8,40)
pp.savefig(fig); plt.close(fig)
pp.close()
print('ok')
