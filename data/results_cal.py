# -*- coding: utf-8 -*-
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import math
import loadgene
import windgene
import solargene
import recyclemodule
import copy
import tempgene
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from scipy import stats

#pos :wind pv bat ele-tank-fc :
WINDS_COUNTS=3
PV_COUNTS=40
BAT_COUNTS=0
ELE_COUNTS=0
TANK_COUNTS=0
FC_COUNTS=0
# price all kinds of dvice
I=0.03

WINDS_PRICE_DEVICE=9702 #3KW
WINDS_PRICE_MAINT=40
WINDS_PV_CONTROLLER=2500  #CHANGE 
WINDS_LIFESPAN=18

PV_PRICE_BAT1=450 #100W
PV_PRICE_BAT2=1280 #250W
PV_PRICE_MAINT=20
PV_LIFESPAN=18

BAT_PRICE_DEVICE=1050 #200AH 
BAT_PRICE_RESET=850
BAT_PRICE_MAINT=24
BAT_LIFESPAN=6
BAT_CHDH_COUNTS=500
 
DA_PRICE_DEVICE=2500  #2KW
DA_PRICE_MAINT=25
DA_LIFESPAN=218

ELE_PRICE_DEVICE=12760 #1KW
ELE_PRICE_MAINT=160  #1KW
ELE_LIFSPAN=18

TANK_PRICE_DEVICE=1800
TANK_PRICE_MAINT=10
TANK_LIFESPAN=18

FC_PRICE_DEVICE=19140 #1KW
FC_PRICE_MAINT=1110
FC_PRICE_RESET=15900
FC_LIFESPAN=6

#parameter assembly :
#bat:
BAT_CAP=200 #a.h
BAT_CHARGE_=0.3   #0.8-0.5
BAT_DISCHARGE_=0.3#0.5-0.2
BAT_VOL=49
#cycle:
RATED_ELE=1 #KW
RATED_FC=2  #KW
TANk_CAP=200#L


RATIO_RISK=200000000
RATIO_OUTAGE=10000


#total power
pv_out=[]
wind_out=[]
load=[]
power_net=[]
power_ren=[]
energy_net=[]
pv_out=solargene.pv_out
wind_out=windgene.wind_out
load=loadgene.load_

def powerRenGene(p_ren,pos_):
    del p_ren[:]
    for day in range(364):
        for hour in range(24):
            p_ren.append(windgene.wind_out[day*24+hour]*pos_[0]+solargene.pv_out[day*24+hour]*pos_[1])

def powerNetGene(p_net,pos_):
    del p_net[:]
    for day in range(364):
        for hour in range(24):
            p_net.append(windgene.wind_out[day*24+hour]*pos_[0]+solargene.pv_out[day*24+hour]*pos_[1]-load[day*24+hour]) 


def energyNetGene(egy_net,p_net):
    del egy_net[:]
    for day in range(364):
        for hour in range(24):
            if day==0 and hour==0:
                 egy_net.append(p_net[day*24+hour]*1)
            else:
                 egy_net.append(egy_net[day*24+hour-1]+p_net[day*24+hour]*1)



#GOAL FUNC:  
max_tank_Volumn=0
cycle_counts=[] #0123:ele  fc tank |bat
ren=[0,1]  #01 wind pv
#goal=config cost + reset cost + maintain cost + outage cost +risk cost
def cost_config(pos_,Qnet,Pnet,cycleCounts_):
    pri_wind=pos_[0]*WINDS_PRICE_DEVICE
    pri_pv=pos_[1]*PV_PRICE_BAT1
    #cycclecont:1bat,2ele,3tank,4fc
    cycleCounts_.append(max(int(abs(max(Pnet)/(BAT_CAP*BAT_CHARGE_*BAT_VOL/1000.0))),int(abs(min(Pnet)/(BAT_CAP*BAT_DISCHARGE_*BAT_VOL/1000.0)))))
    cycleCounts_.append(int(max(Pnet)/recyclemodule.RATIO_POWER2GAS))
    #print 'max pnet :%f'%max(Pnet)
    #print 'Qmin:%f   '%Qmin
    max_tank_Volumn=recyclemodule.tank_svgas(recyclemodule.ele_mkgas(max(Qnet)))
    #print 'maxVol :%f'%max_tank_Volumn
    # 30:氢气的压缩率
    cycleCounts_.append(max_tank_Volumn/(100))
    #3kw bat power    
    q=(max(Qnet)/3)*BAT_PRICE_DEVICE
    if abs(q)>ELE_PRICE_DEVICE+TANK_PRICE_DEVICE+FC_PRICE_DEVICE:
        cycleCounts_.append(int(max(Pnet)/RATED_FC))            
        pri_cycle=ELE_PRICE_DEVICE*cycleCounts_[1]+TANK_PRICE_DEVICE*cycleCounts_[2]+FC_PRICE_DEVICE*cycleCounts_[3]
      
        #print 'cycle price :%f'%p_cycle
        #print 'bat   price :%f'%p_bat
    else:
        cycleCounts_.append(0.0)
        pri_cycle=0
        #print 'cycle not use'
        #print q
        
    #print 'bat: %d ele : %d tank : %d fc : %d'%(cycleCounts_[0],cycleCounts_[1],cycleCounts_[2],cycleCounts_[3])      
    pri_bat=cycleCounts_[3]*BAT_PRICE_DEVICE
    return pri_wind+pri_pv+pri_bat+pri_cycle
    
def cost_maintain(pos_,counts):
    sum_wind=0
    sum_pv=0
    sum_bat=0
    sum_ele=0
    sum_tank=0
    sum_fc=0
    ann_wind=pos_[0]*WINDS_PRICE_MAINT
    ann_pv=pos_[1]*PV_PRICE_MAINT
    ann_bat=counts[0]*BAT_PRICE_MAINT
    ann_ele=counts[1]*ELE_PRICE_MAINT
    ann_tank=counts[2]*TANK_PRICE_MAINT
    ann_fc=counts[3]*FC_PRICE_MAINT
    
    for year in range(20):
        sum_wind+=(ann_wind/(I+1)**year)
        sum_pv+=(ann_pv/(I+1)**year)
        sum_bat+=(ann_bat/(I+1)**year)
        sum_ele+=(ann_ele/(I+1)**year)
        sum_tank+=(ann_tank/(I+1)**year)
        sum_fc+=(ann_fc/(I+1)**year)
    #print "main :%f,%f,%f,%f,%f,%f"%(sum_wind,sum_pv,sum_bat,sum_ele,sum_tank,sum_fc)
    return sum_wind+sum_pv+sum_bat+sum_ele+sum_tank+sum_fc
    
def cost_reset(pos_,counts):
    sum_bat=0
    sum_fc=0
    ann_bat=counts[0]*BAT_PRICE_RESET
    ann_fc=counts[3]*FC_PRICE_RESET
    for count in range(3):
        sum_bat+=(ann_bat/(I+1)**(count*6))
        sum_fc+=(ann_fc/(I+1)**(count*6))
    #print 'reset: %f,%f'%(sum_bat,sum_fc)
    return sum_bat+sum_fc
    
def cost_risk(Qnet):
    count=0
    #print 'Qnet LAST %f'%Qnet[364*24-1]
    if Qnet[364*24-1]<0:
        count=1
    return count*RATIO_RISK
    
def cost_outage(Pnet):
    sum_=0
    for item in range(364*24):
        if Pnet[item]>abs(min(Pnet)):
            sum_+=1
    return sum_*RATIO_OUTAGE

def goaltotal(pos_,counts,Qnet,Pnet):
    mcounts=[]
    install=cost_config(pos_,Qnet,Pnet,mcounts)
    #print cost_reset(pos_,mcounts)
    #print mcounts
    return install+cost_maintain(pos_,mcounts)+cost_reset(pos_,mcounts)+cost_risk(Qnet)+cost_outage(Pnet)

powerNetGene(power_net,ren)
#powerRenGene(power_ren,ren)
energyNetGene(energy_net,power_net)  
print 'payment install : %f'%cost_config(ren,energy_net,power_net,cycle_counts)
print 'tank max volumn : %f'%max_tank_Volumn
print 'payment maintain: %f'%cost_maintain(ren,cycle_counts)
print 'payment reset   : %f'%cost_reset(ren,cycle_counts)
print 'payment risk    : %f'%cost_risk(energy_net)
print 'payment outage  : %f'%cost_outage(power_net)
print '!!payment total goal: %f'%goaltotal(ren,cycle_counts,energy_net,power_net)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
x=[]
y=[]
z=[]
for i in range(10000):
   x.append(i/200)
   
for i in range(50):
    for j in range(200):
        y.append(j)
for i in range(50):
    for j in range(200):
        powerNetGene(power_net,[i,j])
        energyNetGene(energy_net,power_net) 
        z.append(goaltotal([i,j],cycle_counts,energy_net,power_net))
    
ax.plot_trisurf(x, y, z)
plt.show()
