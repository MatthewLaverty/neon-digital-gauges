#include "../park_lamp.h"
#include <cstdio>
int main(){ParkLamp p;int f=0; auto ck=[&](bool c,const char*m){if(!c){printf("FAIL %s\n",m);f++;}};
ck(!p.update(true,0)&&!p.night,"no change before debounce"); ck(!p.update(true,299),"299"); ck(p.update(true,300)&&p.night,"on at 300");
ck(!p.update(false,400),"flicker start"); ck(!p.update(true,500)&&p.night,"flicker ignored"); ck(!p.update(false,600),"off start");
ck(p.update(false,900)&&!p.night,"off at 900"); printf(f?"FAILED\n":"park_lamp: 7 checks pass\n"); return f;}
