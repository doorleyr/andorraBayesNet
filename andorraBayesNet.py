#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 13:23:37 2017

@author: doorleyr
"""
import pickle
import numpy as np
from scipy import spatial
import pandas as pd
import networkx as nx

numStochPaths=10
covSP=0.5
covDist=0.5
thetaR=3
vot=20
fixedTripCost=0.1
#odSF=1
maxEps=0.0005
maxEps2=2
dates=['2016-09-01']
periodsPerDay=13


def driveProbLogit(distance, beta):
    pDrive=1/(1+np.exp(-(-3+beta*(distance/1000))))
    return pDrive 
          
def calculate_link_costs(link_flows, link_capacities, link_free_flow_times, alpha, Beta):
    congestion=np.divide(link_flows,link_capacities)
    costs=np.multiply(link_free_flow_times,(1 + alpha*(np.power(congestion,Beta))))
    return costs, congestion
 
def simplifyNetwork(net, nodeIDs, odNodes, nodesLonLatD):
    newNet=net.copy()
    newLinkRef=np.asarray([newNet.index.values,newNet.index.values])
    for node in nodeIDs:
        #netAB=newNet.as_matrix(columns=['aNodes','bNodes', 'distances'])
        upStreamLinks=newNet.index[newNet.loc[:,'bNodes'] == node]
        upStream=newNet.loc[upStreamLinks]['aNodes']
        downStreamLinks=newNet.index[newNet.loc[:,'aNodes'] == node]
        downStream=newNet.loc[downStreamLinks]['bNodes']
        dsList=list(downStream)
        usList=list(upStream)
        nList=usList+dsList
        neighbours=list(set(nList))
        if len(neighbours)==2 and node not in odNodes:
            if neighbours[0] in usList and neighbours[1] in dsList:
                existingLink=newNet.index[(newNet.loc[:,'aNodes'] ==neighbours[0])& (newNet.loc[:,'bNodes'] ==neighbours[1])]
                if len(existingLink)==0:
                    oldLink1=newNet.index[(newNet.loc[:,'aNodes'] ==neighbours[0])& (newNet.loc[:,'bNodes'] ==node)]
                    oldLink2=newNet.index[(newNet.loc[:,'aNodes'] ==node)& (newNet.loc[:,'bNodes'] ==neighbours[1])]
                    newDistance=newNet.loc[oldLink1]['distances'].values + newNet.loc[oldLink2]['distances'].values
                    newTff=newNet.loc[oldLink1]['tff'].values + newNet.loc[oldLink2]['tff'].values
                    newCapacity=min(newNet.loc[oldLink1]['capacity'].values, newNet.loc[oldLink2]['capacity'].values)
                    # change the link from neighbours[0] to the current node to be from neighbours[0] to neighbours[1] with this new distance
                    # then delete the second link
                    newNet.set_value(oldLink1, 'distances', newDistance)
                    newNet.set_value(oldLink1, 'tff', newTff)
                    newNet.set_value(oldLink1, 'capacity', newCapacity)
                    newNet.set_value(oldLink1,'bNodes',neighbours[1])
                    newLinkRef[1,np.where(newLinkRef[1,:]==oldLink2.values[0])]=oldLink1.values[0]
                    newNet=newNet.drop(oldLink2.values[0])            
            if neighbours[1] in usList and neighbours[0] in dsList:
                existingLink=newNet.index[(newNet.loc[:,'aNodes'] ==neighbours[1])& (newNet.loc[:,'bNodes'] ==neighbours[0])]
                if len(existingLink)==0:
                    oldLink1=newNet.index[(newNet.loc[:,'aNodes'] ==neighbours[1])& (newNet.loc[:,'bNodes'] ==node)]
                    oldLink2=newNet.index[(newNet.loc[:,'aNodes'] ==node)& (newNet.loc[:,'bNodes'] ==neighbours[0])]
                    newDistance=newNet.loc[oldLink1]['distances'].values + newNet.loc[oldLink2]['distances'].values
                    newTff=newNet.loc[oldLink1]['tff'].values + newNet.loc[oldLink2]['tff'].values
                    newCapacity=min(newNet.loc[oldLink1]['capacity'].values , newNet.loc[oldLink2]['capacity'].values)
                    # change the link from neighbours[0] to the current node to be from neighbours[0] to neighbours[1] with this new distance
                    # then delete the second link
                    newNet.set_value(oldLink1, 'distances', newDistance)
                    newNet.set_value(oldLink1, 'tff', newTff)
                    newNet.set_value(oldLink1, 'capacity', newCapacity)
                    newNet.set_value(oldLink1,'bNodes',neighbours[0])
                    newLinkRef[1,np.where(newLinkRef[1,:]==oldLink2.values[0])]=oldLink1.values[0]
                    newNet=newNet.drop(oldLink2.values[0])
    for index, row in newNet.iterrows():
        aN,bN=row['aNodes'],row['bNodes']
        alon,blon,alat,blat=nodesLonLatD[aN,0],nodesLonLatD[bN,0], nodesLonLatD[aN,1],nodesLonLatD[bN,1]
        newNet.set_value(index,'aNodeLon',alon)
        newNet.set_value(index,'bNodeLon',blon)
        newNet.set_value(index,'aNodeLat',alat)
        newNet.set_value(index,'bNodeLat',blat)
    return newNet, newLinkRef
                
def shortestPath(odNodes, odDf, nodeIDs,netAB, costs):
    G=nx.DiGraph()
    odCost=np.zeros(len(odDf))
    for i in range(len(netAB)):
        G.add_edge(netAB[i,0], netAB[i,1], weight=costs[i])
    pathLinks=np.zeros((len(odDf),len(netAB)))
    for w in range(len(odDf)):
        o=int(odDf.iloc[w]['o'])
        d=int(odDf.iloc[w]['d'])
        if not (o==d) and (odDf.iloc[w]['flow']>0):
            oNode=odNodesD[o]
            dNode=odNodesD[d]
            nodesOnPath=nx.dijkstra_path(G, oNode, dNode)
            for n in range(len(nodesOnPath)-1):
                linkNum=np.where((netAB[:,0]==nodesOnPath[n]) & (netAB[:,1]==nodesOnPath[n+1]))[0][0]
                pathLinks[w,linkNum]=1
                odCost[w]+=costs[linkNum]
    return pathLinks, odCost
                                   
def stochShortestPath(odNodes, odDf, nodeIDs,netAB, costs, num, cov):
    print('Finding all stochastic shortest paths')
    perturbations=np.random.normal(loc=0.0, scale=1.0, size=[len(costs), num])
    stdev=np.transpose(np.matlib.repmat(cov*costs, num,1))
    costsStoch=np.transpose(np.matlib.repmat(costs, num,1))+np.multiply(stdev, perturbations)
    costsStoch=np.column_stack((costsStoch, costs))
    costsStochPos=np.clip(costsStoch, 0, np.inf)
    pathLinksStoch=np.empty([len(odDf)*(num+1), len(netAB)])
    odCostStoch=np.empty([len(odDf)* (num+1)])
    for n in range(num+1):
        print(n)
        pathLinksStoch[n*len(odDf):(n+1)*len(odDf),:], odCostStoch[n*len(odDf):(n+1)*len(odDf)]=shortestPath(odNodes, odDf, nodeIDs,netAB, costsStochPos[:,n])
    delta_wp=np.matlib.repmat(np.identity(len(odDf)),1,(num+1))
    return np.transpose(pathLinksStoch), delta_wp
        
def findPathDuplicates(delta_ap, delta_wp,numChoices):
    numPaths=delta_ap.shape[1]
    numODs=delta_wp.shape[0]
    duplicatePaths=np.zeros(numPaths)
    odNums=np.tile(range(numODs),numChoices)
    isSame=0
    notSame=0
    for odn in range(numODs):   
        for choice in range(numChoices-1):
            for alt in range(choice+1,numChoices):
                if np.array_equal(delta_ap[:,odn+choice*numODs],delta_ap[:,odn+alt*numODs]):
                    isSame=isSame+1
                    duplicatePaths[odn+alt*numODs]=1
                else:
                    notSame=notSame+1    
    odNums=odNums[np.where(duplicatePaths==0)]  
    temp, counts=np.unique(odNums, return_counts=True)
    numPathsByOd=dict(zip(temp, [int(c) for c in counts]))
    return duplicatePaths, numPathsByOd

def msaSolve(sameOD, maxEps, delta_wp_D, delta_ap_D, thetaR, od, K, tffDNew):
    k=0
    eps=np.inf
    
    xD=np.zeros(delta_ap_D.shape[0])    
    #initialise solution
    cD=vot*calculate_link_costs(xD, K, tffDNew, 0.15, 4)[0] 
    CD=np.dot(np.transpose(delta_ap_D), cD)+fixedTripCost

    topline=np.exp(-thetaR*(CD))
    bottomLine=[sum(topline[sameOD[path]]) for path in range(len(CD))]
    Pp=np.divide(topline, bottomLine)
    
    h=np.multiply(Pp,np.dot(np.transpose(delta_wp_D),od))

    xD=np.dot(delta_ap_D, h)
    k+=1
    while eps>maxEps:
        cD=vot*calculate_link_costs(xD, K, tffDNew, 0.15, 4)[0]
        CD=np.dot(np.transpose(delta_ap_D), cD)+fixedTripCost
        
        topline=np.exp(-thetaR*(CD))
        bottomLine=[sum(topline[sameOD[path]]) for path in range(len(CD))]
        Pp=np.divide(topline, bottomLine) 
        
        hAux=np.multiply(Pp,np.dot(np.transpose(delta_wp_D),od))        
        lastH=h
        h=lastH+(hAux-lastH)/(k+1)
        xD=np.dot(delta_ap_D, h)
        eps=np.sum(np.abs(h-lastH))/np.sum(lastH)
        k+=1
    return xD, Pp

    
    
#Get network data
netD=pickle.load( open( "data/network/netDriveJun18.p", "rb" ) )
nodeIDsD=pickle.load( open( "data/network//nodeIDsDriveJun18.p", "rb" ) )
nodesXYD=pickle.load( open( "data/network//nodesXYDriveJun18.p", "rb" ) )
nodesLonLatD=pickle.load( open( "data/network//nodesLonLatDriveJun18.p", "rb" ) )
nodeNumDict=pickle.load( open( "data/network//nodeNumDictDriveJun18.p", "rb" ) )
nodeNumDictRev={v:k for k,v in nodeNumDict.items()}

#get the estimated O-D matrix based on RNC data 
numPeriods=len(dates)*periodsPerDay

odXY=pickle.load( open( "data/od/ODxy_Oct17.p", "rb" ) )
numTaz=len(odXY)

#odAndorran=np.empty([numTaz,numTaz,numPeriods])
#odSpanish=np.empty([numTaz,numTaz,numPeriods])
#odFrench=np.empty([numTaz,numTaz,numPeriods])
#odOther=np.empty([numTaz,numTaz,numPeriods])
odAll=np.empty([numTaz,numTaz,numPeriods])
tripWindows=[]

#for dd in range(len(trainDates)):
for dd in range(len(dates)):
    #d=trainDates[dd]
    d=dates[dd]
    odfile='data/od/ODbyNation_CEST_halfDay_Oct17_'+d+'.p'
    winfile='data/od/tWin_CEST_halfDay_Oct17_'+d+'.p'
    od_d=pickle.load( open( odfile, "rb" ) )
    tripWindows_d=pickle.load( open(winfile, "rb"))
    tripWindows.extend(tripWindows_d)
#    odAndorran[:,:,dd*periodsPerDay:(dd+1)*periodsPerDay]=od_d['Andorran']
#    odSpanish[:,:,dd*periodsPerDay:(dd+1)*periodsPerDay]=od_d['Spanish']
#    odFrench[:,:,dd*periodsPerDay:(dd+1)*periodsPerDay]=od_d['French']
#    odOther[:,:,dd*periodsPerDay:(dd+1)*periodsPerDay]=od_d['Other']
    odAll[:,:,dd*periodsPerDay:(dd+1)*periodsPerDay]=od_d['All']

#find closest node to each TAZ
netABD=netD.as_matrix(columns=['aNodes','bNodes'])
odNodesD=[spatial.KDTree(nodesXYD).query(xy)[1] for xy in odXY]
    
# Get ground truth traffic data
xl = pd.ExcelFile('data/traffic/trafficFileLookup.xlsx')
testDf = xl.parse(xl.sheet_names[0])
testDf=testDf.set_index('datafile')
np.random.seed(0)
trainInd=np.random.choice(len(testDf), int(len(testDf)*4/5))
testDf['Train'] = [(i in trainInd) for i in range(len(testDf))]

realXDict=pickle.load( open( "data/traffic/realXDict.p", "rb" ) )


#simplify the network by removing redundant nodes
newNetD, newLinkRefD=simplifyNetwork(netD, nodeIDsD, odNodesD, nodesLonLatD)
newNetABD=newNetD.as_matrix(columns=['aNodes','bNodes'])
newNetIndex=list(newNetD.index)
linkNumDict=dict(zip(newLinkRefD[0,:], newLinkRefD[1,:]))
tffDNew=newNetD['tff'].values
capacities=newNetD['capacity'].values

#get the link ID of the test links in the simplified network
testDf['newNetLink']=""
testDf['netLink']=""
testDf['newNetNumInd']=""
for ind, row in testDf.iterrows():
    osmAnode=str(row['aNode'])
    osmBnode=str(row['bNode'])
    netAnode=nodeNumDict[osmAnode]
    netBnode=nodeNumDict[osmBnode]
    netIdI=np.where((netABD[:,0]==netAnode) & (netABD[:,1]==netBnode))[0][0]
    netId=netD.index[netIdI]
    newNetId=newLinkRefD[1,netId]
    testDf.set_value(ind, 'newNetLink', newNetId)
    testDf.set_value(ind, 'netLink', netId)
    testDf.set_value(ind, 'newNetNumInd', newNetD.index.get_loc(newNetId))

#get ALL the stochastic shortest paths for driving
odDf_Fake=[]
for o in range(numTaz):
    for d in range(numTaz):
        odDf_Fake.append({'o':int(o), 'd':int(d), 'flow':1})
odDf_Fake=pd.DataFrame(odDf_Fake)

cD0=vot*calculate_link_costs(np.zeros(len(newNetABD)), capacities, tffDNew, 0.15, 4)[0]
delta_ap_D_Dup, delta_wp_D_Dup=stochShortestPath(odNodesD, odDf_Fake, nodeIDsD,newNetABD, cD0, numStochPaths, covSP)
duplicatePaths, numPathsByOD=findPathDuplicates(delta_ap_D_Dup, delta_wp_D_Dup,numStochPaths+1)
##delete duplicate paths, zero-demand ODs
delta_ap_D=delta_ap_D_Dup[:,np.where(duplicatePaths==0)[0]]
delta_wp_D=delta_wp_D_Dup[:,np.where(duplicatePaths==0)[0]]

#find the competing paths for every path- used in equilibration algorithm
sameOD=[]
for path in range(delta_wp_D.shape[1]):
    w=np.where(delta_wp_D[:,path]==1)[0][0]
    sameOD.append(list(np.where(delta_wp_D[w,:]==1)[0]))

xObsTest=[]
xPredictTest=[]
outPut={}

# Start the calibration
# for each time period, use the Gaussian Bayes Network (a type of Probalistic Graphical Model) appraoch to calibrate the OD matrix using the traffic counts
# Starts with the RNC-based O-D matrix as a prior (naive) solution
# Iterates between solving for network equilibrium and updating the OD-matrix based on the evidence (traffic counts)
print('Starting calibration of O-D matrices using traffic data')
for p in range(odAll.shape[2]):
    print('Period: ' + str(p))
    od=odAll[:, :, p] 
    odDf=[]
    for o in range(len(od)):
        for d in range(len(od)):
            odDf.append({'o':int(o), 'd':int(d), 'flow':od[o,d]})
            
    odDf=pd.DataFrame(odDf)    
    odFlat=list(odDf['flow'])
    
    eps2=np.inf 
    #Castillo paper
    #Step 0: Select a set of initial beta_ai of route choice proportions (columns: OD pairs, rows: links)
    x, Pp=msaSolve(sameOD, maxEps, delta_wp_D, delta_ap_D, thetaR, odFlat, capacities, tffDNew)
    
    bayesCount=0
    # Bayes updating loop
    while eps2>maxEps2:
        bayesCount+=1
        print('Normalised Error: '+str(eps2))
        beta_ai=np.dot(delta_ap_D, np.dot(np.diag(Pp),np.transpose(delta_wp_D)))
        U=np.sum(odFlat)
        K=np.array([f/U for f in odFlat])
                
        Dn=np.diag(np.power(np.multiply(covDist,np.array(odFlat)),2))
        sigmaU=U #very uncertain to allow for U to become larger
        
        sigmaTT=np.multiply(np.power(sigmaU,2) , np.outer(K, K)) + Dn
        sigmaTV=np.dot(sigmaTT, np.transpose(beta_ai))
        sigmaVT=np.dot(beta_ai, sigmaTT)
        D_eps=np.zeros((len(x), len(x)))
        sigmaVV=np.dot(np.dot(beta_ai, sigmaTT), np.transpose(beta_ai)) + D_eps
        
        sigmaAll=np.concatenate((np.concatenate((sigmaTT, sigmaTV), axis=1), np.concatenate((sigmaVT, sigmaVV), axis=1)), axis=0)
        
        mu=np.concatenate((np.array(odFlat), x))
                
        #update incrementally, one node at a time
        for link in testDf.index: 
            #Only update distributions using the training nodes
            if testDf.loc[link]['Train']==True:
                x_obs=realXDict[link][p]
                linkNum=testDf.loc[link]['newNetNumInd']
                index=linkNum+len(odFlat)
                sigmaYZ=sigmaAll[:,index]
                sigmaZY=sigmaAll[index,:]
                sigmaZZInv=1/sigmaAll[index,index]
                diff=x_obs-mu[index]
                mu=mu+np.dot(np.dot(sigmaYZ, sigmaZZInv), diff)
                sigmaAll=sigmaAll-np.outer(np.dot(sigmaYZ, (1/(sigmaAll[index,index]))), sigmaZY)
            
        odFlat=mu[0:len(odFlat)]
        x=mu[len(odFlat):len(mu)]
        
        x, PpAux=msaSolve(sameOD, maxEps, delta_wp_D, delta_ap_D, thetaR, odFlat, capacities, tffDNew)    
        eps2=np.sum([np.power(PpAux[pp] - Pp[pp],2) for pp in range(len(Pp))])        
        Pp=Pp+(PpAux-Pp)/(bayesCount+1)
    #After convergence, test the accuracy of the remaining test links 
    for link in testDf.index: 
        if testDf.loc[link]['Train']==False:
            x_obs=realXDict[link][p]
            linkNum=testDf.loc[link]['newNetNumInd']
            index=linkNum+len(odFlat)
            x_predict=mu[index]
            xObsTest.extend([x_obs])
            xPredictTest.extend([x_predict])
    newNetD['x']=x
    newNetD['beta']=list(beta_ai)
    outPut[tripWindows[p][0]]={'OD': [int(odFlat[ii]) for ii in range(len(odFlat))], 'Traffic': list([int(newNetD.loc[linkNumDict[i]]['x']) for i in range(len(netD))]),
          #'Beta': list([int(newNetD.loc[linkNumDict[i]]['beta']) for i in range(len(netD))])
          }

APE=[100*np.abs((xPredictTest[i]-xObsTest[i])/xObsTest[i])for i in range(len(xPredictTest))]
np.mean(APE)
print('Mean Average % Error: '+str(int(np.mean(APE)))+'%')

pickle.dump( outPut, open( "data/results/andorraBayesSolution.p", "wb" ))

