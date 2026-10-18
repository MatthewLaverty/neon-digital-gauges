"""Bench PoC wiring diagram (rev 2026-10-16): PC + USB-CAN adapter as fake Haltech; hub (ESP32-S3-DevKitC-1) with
4x4 membrane keypad (all keys, owner 2026-10-16), dimmer pot, headlamp switch; Blink PKP-2300-SI deferred (optional);
no VSS loopback: speed and distance now come from the Haltech (0x370, 0x6F6); 2.8C tach at the far end."""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
C=dict(h='#e0b000',l='#2e9e44',g='#222222',v3='#d62728',v12='#ff7f0e',sig='#1f77b4',usb='#8a8a8a')
fig,ax=plt.subplots(figsize=(18,12.5),dpi=110); ax.set_xlim(0,183); ax.set_ylim(0,125); ax.axis('off')
LH=3.1
def box(x,y,w,title,lines=(),fc='#f4f4f4'):
    h=6.5+LH*len(lines)+1.0
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.3,rounding_size=1.0',fc=fc,ec='#444',lw=1.2,zorder=2))
    ax.text(x+w/2,y+h-1.6,title,ha='center',va='top',fontsize=10.5,weight='bold',zorder=4)
    for i,t in enumerate(lines): ax.text(x+1.0,y+h-6.2-i*LH,t,ha='left',va='top',fontsize=8.4,family='monospace',zorder=4)
    return y+h
def wire(pts,c,lw=2.2,ls='-'):
    xs,ys=zip(*pts); ax.plot(xs,ys,c=c,lw=lw,ls=ls,solid_capstyle='round',zorder=1)
def dot(x,y,c): ax.plot(x,y,'o',c=c,ms=5.5,zorder=3)
def lab(x,y,t,c='#333',**k):
    k.setdefault('fontsize',8.2); ax.text(x,y,t,color=c,zorder=4,**k)
ax.text(90,124,'Neon gauges: bench proof-of-concept wiring (rev 2026-10-16)',ha='center',va='top',fontsize=14,weight='bold')
ax.text(90,120.3,'CAN bus at 1 Mbit/s. Terminate ONLY the two ends (USB-CAN adapter and CAN board #2). With power off, expect about 60 ohm between CAN H and CAN L.',ha='center',va='top',fontsize=9.5)
# CAN trunk
YH,YL,YG=48,44,40; X0,X1=21,172
wire([(X0,YH),(X1,YH)],C['h'],3.2); wire([(X0,YL),(X1,YL)],C['l'],3.2); wire([(X0,YG),(X1,YG)],C['g'],2,'--')
lab(23,YH+0.9,'CAN H',C['h'],weight='bold'); lab(23,YL+0.9,'CAN L',C['l'],weight='bold'); lab(23,YG+0.9,'GND reference',C['g'])
# PC + adapter
box(2,70,18,'PC',('python-can','fake_haltech.py','SavvyCAN'),'#e8eef7')
box(1,34,20,'USB-CAN adapter',('Jhoinrch RH-02 PLUS','CANable 2.0, slcan','terminal H/GND/L','120R switch: ON'),'#e8eef7')
wire([(11,70),(11,54.5)],C['usb'],3); lab(12,61,'USB',C['usb'])
# USB to hub and tach
wire([(8,87.3),(8,114.5),(50,114.5),(50,110.2)],C['usb'],3); lab(10,115.2,'USB-C: power + programming (native USB port on each board)',C['usb'])
# hub
top=box(28,70,50,'HUB: ESP32-S3-DevKitC-1 N16R8',(
 'GPIO4   TWAI TX -> CAN board #1 CTX','GPIO5   TWAI RX <- CAN board #1 CRX','3V3,GND         -> CAN board #1',
 'GPIO1   ADC     <- dimmer pot wiper','GPIO2   input   <- headlamp switch','GPIO6,7  free (no VSS: speed and',
 '         distance come from the Haltech)','GPIO8-11  -> keypad rows R1-R4','GPIO12-15 <- keypad cols C1-C4','           (internal pull-ups)'),'#eef7ee')
# CAN board 1
box(32,52,26,'CAN board #1',('SN65HVD230, 3.3 V','mid-bus: NO 120R'),'#fff8e1')
for x,c,t in ((36,'v3','3V3'),(41,'sig','CTX'),(46,'sig','CRX'),(51,'g','GND')):
    wire([(x,70),(x,66.4)],C[c],2); lab(x+0.4,67.3,t,C[c])
for x,y,c in ((38,YH,'h'),(44,YL,'l'),(50,YG,'g')): wire([(x,52),(x,y)],C[c],2.6); dot(x,y,C[c])
# hub peripherals
yb=box(84,92.5,28,'Dimmer pot, 10k linear',('end A  -> 3V3','wiper  -> GPIO1','end B  -> GND'),'#fdf0f0')
box(84,75,28,'Headlamp switch',('toggle or jumper','GPIO2 -> switch -> GND','closed = lights on'),'#fdf0f0')
wire([(78,101),(84,101)],C['sig'],2); wire([(78,83.5),(84,83.5)],C['sig'],2)
mtop=box(118,74,34,'4x4 membrane keypad',('DIYables, ribbon L to R:','R1 R2 R3 R4 C1 C2 C3 C4',' 8  9 10 11 12 13 14 15  <- GPIO','(8 Dupont M-F jumpers)','key map (membrane only for now):','1  temp: coolant / oil','2  fuel: level / ethanol','3  speedo data, hold: rotate','A  tap ODO/TRIP, hold: reset','B  tach: rpm / boost'),'#f3eefa')
wire([(72,110.2),(72,112.3),(135,112.3),(135,mtop)],C['sig'],2.4)
# tach
ttop=box(154,62,28,'TACH: Waveshare 2.8C',('ESP32-S3, 480x480','SH1.0 UART header:','TXD GPIO43 -> CTX','RXD GPIO44 <- CRX','3V3, GND'),'#eef7ee')
wire([(50,114.5),(176,114.5),(176,ttop)],C['usb'],3)
box(155,50.5,22,'CAN board #2',(),'#fff8e1'); lab(156,51.3,'SN65HVD230, END: 120R')
for x,c,t in ((158,'v3','3V3'),(163,'sig','CTX'),(168,'sig','CRX'),(173,'g','GND')): wire([(x,62),(x,57.3)],C[c],2); lab(x+0.4,58.6,t,C[c],fontsize=7.2)
for x,y,c in ((160,YH,'h'),(165,YL,'l'),(170,YG,'g')): wire([(x,50.5),(x,y)],C[c],2.6); dot(x,y,C[c])
# Blink keypad
btop=box(62,1,46,'Blink PKP-2300-SI (DEFERRED, optional)',('AT04-4P socket, mate AT06-4S plug:','pin 1  blue   CAN L','pin 2  white  CAN H','pin 3  black  GND (battery -)','pin 4  red    +12 to 24 V',
 'Set up first, alone on the adapter:',' bit rate 1 Mbit/s (object 2010h)',' default 125 kbit/s, node 15h',' key PDO 195h, LED 215h (node 15h)'),'#f3eefa')
for x,y,c in ((76,YH,'h'),(82,YL,'l'),(88,YG,'g')): wire([(x,btop),(x,y)],C[c],2.6); dot(x,y,C[c])
box(114,12,26,'12 V bench supply',('+12 V -> pin 4','GND -> pin 3 AND','bus GND'),'#fff1e0')
wire([(114,25),(108,25)],C['v12'],2.8); lab(108.6,25.8,'+12 V',C['v12'])
wire([(127,29.2),(127,YG)],C['g'],2,'--'); dot(127,YG,C['g'])
# legend + rules
for i,(k,t) in enumerate((('h','CAN H (twist with CAN L)'),('l','CAN L'),('g','ground / reference'),('v3','3.3 V'),('v12','12 V, keypad only'),('sig','logic signal'),('usb','USB'))):
    y=29-i*3.2; wire([(2,y),(7,y)],C[k],3); lab(8,y-0.8,t)
ax.text(144,36,'Rules',fontsize=10,weight='bold',va='top')
ax.text(144,32.5,'- 12 V goes ONLY to the Blink keypad;\n  ESP32 pins are 3.3 V only.\n- ESP32 TX -> CTX, RX -> CRX (not crossed).\n- Short stubs; twist CAN H with CAN L.\n- Mid-bus board with a fixed 120R:\n  remove it (measure ~60 ohm total).\n- Avoid GPIO0/3/45/46 (strapping),\n  19/20 (USB), 26-37 (flash/PSRAM),\n  38/48 (RGB LED).',fontsize=8.3,va='top',linespacing=1.35)
fig.savefig('docs/bench/poc_wiring.png',bbox_inches='tight',facecolor='white'); print('ok')
