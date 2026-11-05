"""Breadboard layout for the car I/O circuits (park-lamp, ignition/latch, dimmer, buzzer).
65-column board, rows a-e / f-j, a rail pair top and bottom. Output: docs/bench/breadboard_car_io.png"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
ROWY = dict(a=12,b=11,c=10,d=9,e=8,f=6,g=5,h=4,i=3,j=2)
RAIL = {"T+":13.6,"T-":14.4,"B+":0.8,"B-":0.0}
def P(c,r): return (c, ROWY[r] if r in ROWY else RAIL[r])
fig,ax = plt.subplots(figsize=(26,13)); ax.set_xlim(-14,72); ax.set_ylim(-9,22); ax.set_aspect("equal"); ax.axis("off")
ax.add_patch(FancyBboxPatch((-0.5,-0.8),66,16,boxstyle="round,pad=0.3",fc="#f4f1e8",ec="#999"))
ax.add_patch(Rectangle((-0.5,6.7),66,0.6,fc="#ddd8c8",ec="none"))
for c in range(1,66):
    for r in ROWY: ax.add_patch(Circle(P(c,r),0.13,fc="#555",ec="none"))
    for r in RAIL: ax.add_patch(Circle(P(c,r),0.11,fc="#777",ec="none"))
    if c%5==0 or c==1:
        ax.text(c,15.25,str(c),ha="center",fontsize=8,color="#444"); ax.text(c,-1.1,str(c),ha="center",fontsize=8,color="#444")
for r,y in ROWY.items(): ax.text(0.2,y,r,ha="center",va="center",fontsize=8,color="#444"); ax.text(65.8,y,r,ha="center",va="center",fontsize=8,color="#444")
lab={"T+":("3.3 V (top +)","#c0392b"),"T-":("GND (top -)","#2c3e9e"),"B+":("12 V (bottom +)","#c0392b"),"B-":("GND (bottom -)","#2c3e9e")}
for k,y in RAIL.items():
    ax.plot([0.5,65.5],[y+0.3 if k in("T-","B+") else y-0.3]*2,color=lab[k][1],lw=1.5)
    ax.text(-0.8,y,lab[k][0],ha="right",va="center",fontsize=10,color=lab[k][1],weight="bold")
def wire(a,b,col,lw=2.6):
    (x1,y1),(x2,y2)=P(*a),P(*b); ax.plot([x1,x2],[y1,y2],color=col,lw=lw,solid_capstyle="round",zorder=3)
    for x,y in((x1,y1),(x2,y2)): ax.add_patch(Circle((x,y),0.2,fc=col,ec="k",lw=.5,zorder=4))
def res(a,b,txt):
    (x1,y1),(x2,y2)=P(*a),P(*b); ax.plot([x1,x2],[y1,y2],color="#888",lw=1.5,zorder=3)
    mx,my=(x1+x2)/2,(y1+y2)/2; w=1.6 if y1==y2 else 0.55; h=0.5 if y1==y2 else 0.9
    ax.add_patch(FancyBboxPatch((mx-w/2,my-h/2),w,h,boxstyle="round,pad=0.05",fc="#d9b77e",ec="k",lw=.6,zorder=4))
    ax.text(mx+(0 if y1==y2 else 0.5),my+(0.45 if y1==y2 else 0),txt,ha="center" if y1==y2 else "left",va="bottom" if y1==y2 else "center",fontsize=8.5,weight="bold",zorder=5)
    for x,y in((x1,y1),(x2,y2)): ax.add_patch(Circle((x,y),0.16,fc="#888",ec="k",lw=.4,zorder=4))
def diode(a,k,txt):
    (x1,y1),(x2,y2)=P(*a),P(*k); ax.plot([x1,x2],[y1,y2],color="#888",lw=1.5,zorder=3)
    mx=(x1+x2)/2; ax.add_patch(Rectangle((mx-0.8,y1-0.22),1.6,0.44,fc="#e67e22",ec="k",lw=.6,zorder=4))
    ax.add_patch(Rectangle((mx+0.45,y1-0.22),0.25,0.44,fc="k",zorder=5))
    ax.text(mx,y1-0.35,txt,ha="center",va="top",fontsize=8,zorder=5)
    for x,y in((x1,y1),(x2,y2)): ax.add_patch(Circle((x,y),0.16,fc="#888",ec="k",lw=.4,zorder=4))
def npn(c,r,txt):
    x,y=P(c,r); ax.add_patch(FancyBboxPatch((x-0.45,y-0.35),2.9,0.7,boxstyle="round,pad=0.1",fc="#bbb",ec="k",lw=.7,zorder=4))
    for i,l in enumerate("EBC"): ax.text(x+i,y,l,ha="center",va="center",fontsize=9,weight="bold",zorder=5)
    ax.text(x+1,y+0.75,txt,ha="center",va="bottom",fontsize=8,weight="bold",zorder=5)
def opto(c,txt):
    ax.add_patch(Rectangle((c-0.45,7.6),1.9,-1.95,fc="#222",ec="k",zorder=4)); ax.add_patch(Circle((c-0.15,6.35),0.12,fc="#eee",zorder=5))
    for (cc,r,n) in((c,"f","1"),(c+1,"f","2"),(c+1,"e","3"),(c,"e","4")):
        x,y=P(cc,r); ax.add_patch(Circle((x,y),0.17,fc="silver",ec="k",zorder=5)); ax.text(x,y+(-0.45 if r=="f" else 0.45),n,ha="center",va="center",fontsize=7.5,color="k",zorder=6)
    ax.text(c+0.5,6.85,txt,ha="center",va="center",fontsize=7,color="w",weight="bold",zorder=6)
def tag(c,r,txt,col="#222",dy=0.55,fs=8.5):
    x,y=P(c,r); ax.text(x,y+dy,txt,ha="center",va="bottom" if dy>0 else "top",fontsize=fs,color=col,weight="bold",zorder=6)
def off(xy,txt,fc,w=7,h=1.8):
    ax.add_patch(FancyBboxPatch((xy[0]-w/2,xy[1]-h/2),w,h,boxstyle="round,pad=0.2",fc=fc,ec="k",zorder=2)); ax.text(*xy,txt,ha="center",va="center",fontsize=9,weight="bold",zorder=3)
def lead(xy,b,col,txt=None):
    x2,y2=P(*b); ax.plot([xy[0],x2],[xy[1],y2],color=col,lw=2.2,ls="--",zorder=3); ax.add_patch(Circle((x2,y2),0.2,fc=col,ec="k",lw=.5,zorder=4))
    if txt: ax.text((xy[0]+x2)/2+0.3,(xy[1]+y2)/2,txt,fontsize=8,color=col,weight="bold",zorder=5)
RED,BLK,YEL,GRN,BLU,ORG,PUR="#d62728","#111","#d4a017","#2ca02c","#1f77b4","#ff7f0e","#9467bd"
# power module
ax.add_patch(FancyBboxPatch((0.55,-0.6),4.9,15.3,boxstyle="round,pad=0.1",fc="#2e7d32",ec="k",alpha=.85,zorder=2))
ax.text(3.0,10.5,"VUPN7191\npower\nmodule",ha="center",va="center",color="w",fontsize=10,weight="bold",zorder=3)
ax.text(3.0,12.9,"TOP jumper\n3.3 V\n(stage 2: OFF)",ha="center",va="center",color="#ffeb3b",fontsize=8,weight="bold",zorder=3)
ax.text(3.0,2.2,"BOTTOM jumper\nOFF\n(meter-check!)",ha="center",va="center",color="#ffeb3b",fontsize=8,weight="bold",zorder=3)
ax.text(3.0,6.2,"USB or\nbarrel in",ha="center",va="center",color="w",fontsize=8,zorder=3)
# ground tie between rails
wire((64,"T-"),(64,"B-"),BLK,2); tag(62.6,"e","GND\ntie",BLK,dy=-0.9)
# ---- park-lamp sense
opto(10,"NTE3222"); res((7,"h"),(10,"h"),"2.2k"); wire((7,"j"),(7,"B+"),YEL); tag(7.6,"i","PARK",YEL,dy=0)
wire((11,"j"),(11,"B-"),BLK); wire((11,"a"),(11,"T-"),BLK); res((10,"a"),(10,"T+"),"10k"); tag(10,"c","GPIO2",BLU,dy=-0.25)
ax.text(10.5,16.6,"PARK-LAMP SENSE\nU1 NTE3222",ha="center",fontsize=10,weight="bold")
# ---- ignition sense
opto(20,"NTE3222"); res((16,"h"),(20,"h"),"2.2k"); wire((16,"j"),(16,"B+"),GRN); tag(16.8,"i","IGN",GRN,dy=0)
wire((21,"j"),(21,"B-"),BLK); wire((21,"a"),(21,"T-"),BLK); res((20,"a"),(20,"T+"),"10k"); tag(20,"c","GPIO7",BLU,dy=-0.25)
wire((16,"g"),(40,"g"),GRN,2)
ax.text(20.5,16.6,"IGNITION SENSE\nU2 NTE3222",ha="center",fontsize=10,weight="bold")
# ---- dimmer
lx,ly=P(26,"d"); wire((26,"d"),(26,"B+"),ORG,2); tag(26.9,"i","DIM",ORG,dy=0)
res((26,"c"),(30,"c"),"47k"); res((30,"a"),(30,"T-"),"10k")
ax.add_patch(Rectangle((29.7,8.75),1.6,0.5,fc="#1a5276",ec="k",zorder=4)); ax.text(30.5,9.0,"1uF",color="w",ha="center",va="center",fontsize=7.5,zorder=5)
tag(29.6,"d","+",RED,dy=-0.75); tag(31.4,"d","-",BLK,dy=-0.75)
for cc in(30,31): ax.add_patch(Circle(P(cc,"d"),0.16,fc="#888",ec="k",zorder=5))
wire((31,"a"),(31,"T-"),BLK); tag(30,"e","GPIO1",BLU,dy=-0.25)
ax.text(29,16.6,"DIMMER INPUT",ha="center",fontsize=10,weight="bold")
# ---- buzzer driver
npn(31,"h","Q3 2N2222"); wire((31,"j"),(31,"B-"),BLK); res((28,"i"),(32,"i"),"1k"); tag(28,"f","GPIO6",BLU,dy=0.35)
diode((33,"i"),(35,"i"),"1N4148"); wire((35,"j"),(35,"B+"),RED)
off((34,-5.5),"TMX-12S buzzer",ORG,w=6.5,h=1.6); lead((33,-4.7),(33,"f"),PUR,"-"); lead((35,-4.7),(35,"f"),RED,"+")
ax.text(32,16.6,"",ha="center")
ax.text(32.5,-2.6,"BUZZER DRIVER",ha="center",fontsize=10,weight="bold")
# ---- power latch
res((40,"h"),(45,"h"),"10k"); npn(44,"g","Q1 2N2222"); wire((44,"j"),(44,"B-"),BLK)
npn(50,"g","Q2 2N2222"); wire((50,"j"),(50,"B-"),BLK); res((48,"h"),(51,"h"),"1k"); tag(48,"f","GPIO21",BLU,dy=0.35)
wire((46,"i"),(52,"i"),PUR,2); diode((52,"h"),(56,"h"),"1N4148"); wire((56,"j"),(56,"B+"),RED)
off((54,-6.2),"Relay CES-SPDT40P\n(off-board)",  "#aed6f1",w=9,h=2.0)
lead((51,-5.2),(52,"f"),PUR,"85"); lead((55,-5.2),(56,"f"),RED,"86"); lead((57,-5.2),(58,"B+"),RED,"30"); lead((58.5,-5.4),(60,"f"),"#8e44ad","87")
tag(60,"f","CLUSTER\n12V OUT",PUR,dy=0.35)
ax.text(51,16.6,"POWER LATCH",ha="center",fontsize=10,weight="bold")
# ---- 12 V in
off((68.5,-4.2),"12 V supply",  "#f5b7b1",w=5.5,h=1.5); off((68.5,-1.6),"5 A ATM fuse\nCES-FHM12",  "#fdebd0",w=5.5,h=1.6)
ax.plot([68.5,68.5],[-3.45,-2.4],color=RED,lw=2.5); lead((68.5,-0.8),(63,"B+"),RED,"+12")
lead((66.5,-4.2),(65,"B-"),BLK,"-")
# ---- hub
off((40,19.8),"ESP32-S3 hub (off-board, USB). GPIO1 -> 30e   GPIO2 -> 10c   GPIO7 -> 20c   GPIO6 -> 28f   GPIO21 -> 48f   GND -> top -   (stage 2: 3V3 -> top +)","#d6eaf8",w=64,h=1.4)
ax.text(-13.5,-8.6,"Bench stand-ins: insert the PARK / IGN / DIM wire into the 12 V rail = lamps on / key on / dimmer at full.  Pull it out = off.   "
 "Transistor E-B-C order differs between parts: check your part's datasheet and rotate it so E, B and C land in the columns shown.\n"
 "Opto pin 1 = dot.   Diode stripe = cathode (toward 12 V).   Capacitor stripe (-) to col 31.   Neon digital gauges, rev 2026-11-04.",fontsize=9.5,va="bottom")
ax.text(36,21.4,"Car I/O breadboard layout - 65 x 10 board",ha="center",fontsize=16,weight="bold")
plt.savefig("docs/bench/breadboard_car_io.png",dpi=110,bbox_inches="tight"); print("ok")
