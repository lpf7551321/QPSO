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
from scipy import stats

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
load=[]
power_net=[]
energy_net=[]
pv_out=solargene.pv_out
wind_out=windgene.wind_out
load=loadgene.load_

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
ren=[3,70]  #01 wind pv

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
    sum_=0
    annual=pos_[0]*WINDS_PRICE_MAINT+pos_[1]*PV_PRICE_MAINT+counts[0]*BAT_PRICE_MAINT+counts[1]*ELE_PRICE_MAINT+counts[2]*TANK_PRICE_MAINT+counts[3]*FC_PRICE_MAINT
    for year in range(20):
        sum_+=(annual/(I+1)**year)
    return sum_
    
def cost_reset(pos_,counts):
    sum_=0
    annual=counts[0]*BAT_PRICE_RESET+counts[3]*FC_PRICE_RESET
    for count in range(3):
        sum_+=(annual/(I+1)**(count*6))
    return sum_
    
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

def goaltotal(pos_,cycleCounts_,Qnet,Pnet):
    install=cost_config(pos_,Qnet,Pnet,cycleCounts_)
    return install+cost_maintain(pos_,cycleCounts_)+cost_reset(pos_,cycleCounts_)+cost_risk(Qnet)+cost_outage(Pnet)

#powerNetGene(power_net,ren)
#powerRenGene(power_ren,ren)
#energyNetGene(energy_net,power_net)  
#print 'payment install : %f'%cost_config(ren,energy_net,power_net,cycle_counts)
#print 'tank max volumn : %f'%max_tank_Volumn[0]
#print 'payment maintain: %f'%cost_maintain(ren,cycle_counts)
#print 'payment reset   : %f'%cost_reset(ren,cycle_counts)
#print 'payment risk    : %f'%cost_risk(energy_net)
#print 'payment outage  : %f'%cost_outage(power_net)
#print '!!payment total goal: %f'%goaltotal(ren,cycle_counts,energy_net,power_net)


#my QPSO  Algorithn
sudu=[]#[T]generate [N]particle size :tn--id[2]dimenssion
cycle_counts=[] # [T][N][4]0123:ele  fc tank |bat=[] #0123:ele  fc tank |bat
xPOS=[]  #[T]generate [N]particle size :tn--id[2]dimenssion
xPOS_local_best=[]  #[N]particle size [2]dimenssion
xPOS_global_best=[] #[T][2] dimenssion
results=[] # goalfunc(pos) to get result:[T][N][1]
def inti_population(pos_,v_,cycleCount_,gen_,size_,local_,global_,goalfunc_,res_,Qnet,Pnet):
    rlist=[]
    for igen in range(gen_):
        pos_.append([])
        v_.append([])
        cycleCount_.append([])
        res_.append([])
        global_.append([])
        for isize in range(size_): 
            pos_[igen].append([])
            v_[igen].append([])
            cycleCount_[igen].append([])
            res_[igen].append([])
    for item in range(size_):
        local_.append([])
        pos_[0][item].append(np.random.randint(1,50))
        pos_[0][item].append(np.random.randint(1,200))
        v_[0][item].append(np.random.randint(1,30))
        v_[0][item].append(np.random.randint(1,30))
    #初始化种群的各个粒子的pos以及 速度
    for item in range(size_):
        powerNetGene(Pnet,pos_[0][item])
       # powerRenGene(Rnet,pos_[0][item])
        energyNetGene(Qnet,Pnet)
        rlist.append(goalfunc_(pos_[0][item],cycleCount_[0][item],Qnet,Pnet))   
        temp=pos_[0][item][0]
        local_[item].append(temp)
        temp=pos_[0][item][1]
        local_[item].append(temp)
    #print rlist
    index=rlist.index(min(rlist))
    for item in range(size_):
        res_[0][item].append(rlist[item])
    #print res_
    print 'init min value index: %d'%index
    temp=pos_[0][index][0]
    global_[0].append(temp)
    temp=pos_[0][index][1]
    global_[0].append(temp)

    
def get_potential_center(local_,global_,r):
    Pd=[]
    Pd.append(local_[0]*r+global_[0]*(1-r))
    Pd.append(local_[1]*r+global_[1]*(1-r))
    return Pd
    
def get_particle_best_ave(local_):
    mbest=[]
    x1=0
    x2=0
    for item in range(len(local_)):
        x1+=local_[item][0]
        x2+=local_[item][1]
    mbest.append(x1/len(local_))
    mbest.append(x2/len(local_))
    #print 'best ave:[%f,%f]'%(mbest[0],mbest[1])
    return mbest
    
def get_beta_particle(itera_count):
    # x-1 nonlinear reduce  0.5--->0.1
    if itera_count%10==0:
        return 0.5
    else:
        return 0.5
        #return 1.0/(itera_count%10+1)
w=0.8
r1=0.6
r2=0.4
c1=c2=2
temp_counts=[]
temp_values=[]

def update_sudu(pos_,sudu_,curgen_,local_,global_):
    for i in range(len(global_)):
        print 'update sudu %d'%i
        print 'curgen_ %d'%(curgen_)
        sudu_[curgen_][i].append(w*sudu_[curgen_-1][i][0]+r1*c1*(pos_[curgen_-1][i][0]-local_[i][0])+r2*c2*(pos_[curgen_-1][i][0]-global_[curgen_-1][0]))
        sudu_[curgen_][i].append(w*sudu_[curgen_-1][i][1]+r1*c1*(pos_[curgen_-1][i][1]-local_[i][1])+r2*c2*(pos_[curgen_-1][i][1]-global_[curgen_-1][1]))

def update_pos(pos_,sudu_,curgen_):
    pos_x=0
    pos_y=0
    for i in range(len(pos_[curgen_])):
        print 'update pos  %d'%i
        pos_x=pos_[curgen_-1][i][0]+sudu_[curgen_][i][0]
        pos_y=pos_[curgen_-1][i][1]+sudu_[curgen_][i][1]
    if pos_x>0 and pos_y>0:
        pos_[curgen_][i].append(pos_x)
        pos_[curgen_][i].append(pos_y)
    else:
        pos_[curgen_][i].append(pos_[curgen_-1][i][0])
        pos_[curgen_][i].append(pos_[curgen_-1][i][1])
        
def update_population(pos_,sudu_,cycleCounts_,curgen_,local_,global_,goalfunc_,res_,Qnet,Pnet): 
    del temp_values[:]   
    del temp_counts[:]  
    rlist=[]
    print '----------------'
    print 'gen is %d'%curgen_
    print '----------------'
    update_sudu(pos_,sudu_,curgen_,local_,global_)
    update_pos(pos_,sudu_,curgen_)
    #计算更新后的粒子的适应值
    for item in range(len(pos_[curgen_])):
        powerNetGene(Pnet,pos_[curgen_][item])
        energyNetGene(Qnet,Pnet)
        rlist.append(goalfunc_(pos_[curgen_][item],cycleCounts_[curgen_][item],Qnet,Pnet))
    index=rlist.index(min(rlist))
    
    #record the fitness value of new pos  
    for item in range(len(pos_[curgen_])):
        res_[curgen_][item].append(rlist[item])
    
    #calculate local fitness: whatever  chaos to update global or not chaos to update new local
    for item in range(len(pos_[curgen_])):
        powerNetGene(Pnet,local_[item])
        energyNetGene(Qnet,Pnet)
        temp_values.append(goalfunc_(local_[item],temp_counts,Qnet,Pnet))
    #update particle pos , rlist is current result ,temp_value is local best result 
   
    for item in range(len(pos_[curgen_])):
        if temp_values[item]>rlist[item]:
            print '%d gen the %d had changed'%(curgen_,item)
            print 'local best: %f'%temp_values[item]
            print 'curent    : %f'%rlist[item]
            print 'has change local from [%f,%f] to [%f,%f]'%(local_[item][0],local_[item][1],pos_[curgen_][item][0],pos_[curgen_][item][1])
            local_[item]=copy.deepcopy(pos_[curgen_][item])
        else:
            print 'local best: %f'%temp_values[item]
            print 'curent    : %f'%rlist[item]
                    

    #update global best ,it is the best in local and histoty:
    #update global pos

    gb_index=temp_values.index(min(temp_values))
    temp=copy.deepcopy(min(temp_values))
    powerNetGene(Pnet,global_[curgen_-1])
    energyNetGene(Qnet,Pnet)
    if temp<goalfunc_(global_[curgen_-1],temp_counts,Qnet,Pnet):
        global_[curgen_]=copy.deepcopy(local_[gb_index])
    else:
        global_[curgen_]=copy.deepcopy(global_[curgen_-1])


global_best_record=[0,0]
GEN_MAX=100
inti_population(xPOS,sudu,cycle_counts,GEN_MAX,100,xPOS_local_best,xPOS_global_best,goaltotal,results,energy_net,power_net)

while True:    
    for genitem in range(1,GEN_MAX+1):
        update_population(xPOS,sudu,cycle_counts,genitem,xPOS_local_best,xPOS_global_best,goaltotal,results,energy_net,power_net)
        global_best_record[0]=xPOS_global_best[genitem]