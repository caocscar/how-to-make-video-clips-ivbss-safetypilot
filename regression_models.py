# -*- coding: utf-8 -*-
"""
Created on Wed May 10 14:53:26 2017

@author: caoa
"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import pyodbc
import time

cutoff = 1e6 # microseconds

#%%
server1 = 'Tri-SPDB2'
database1 = 'SpDasBsm'
connection_string1 = 'Driver={SQL Server}; Server='+server1+'; Database='+database1+'; trusted_connection=yes'   
conn1 = pyodbc.connect(connection_string1)
database2 = 'SpWsuBsm'
connection_string2 = 'Driver={SQL Server}; Server='+server1+'; Database='+database2+'; trusted_connection=yes'   
conn2 = pyodbc.connect(connection_string2)
server3 = 'Tri-SPDB1'
database3 = 'SpFot'
connection_string3 = 'Driver={SQL Server}; Server='+server3+'; Database='+database3+'; trusted_connection=yes'   
conn3 = pyodbc.connect(connection_string3)

#%%
t0 = time.time()

triplist = pd.read_csv('201303to04.csv')
coef, indexForward, BSM = [],[],[]

for i,device,trip in zip(triplist.index,triplist['Device'],triplist['Trip']):

    # Calculate formula for Gentime based on Dastime
    cols = 'Gentime, DasTime'
    dasbsm = pd.read_sql('SELECT {0} FROM BsmMD WHERE RxDevice={1} and TxDevice={1} and Trip={2} ORDER BY Gentime'.format(cols,device,trip), conn1)    
    if dasbsm.shape[0] <= 1:
        print('No DasBsm Data')
        continue
    else:
        while True:
            delta = dasbsm['Gentime'].diff(1)
            assert not (delta < 0).any()
            if delta.max() < cutoff:
                print('{} {} {} Good data {:.1f}s'.format(i,device,trip,delta.max() / cutoff))
                break
            else:
                print('{} {} BAD data {:.1f}s'.format(device,trip,delta.max() / cutoff))
                idx = delta[delta == delta.max()].index[0]
                if (delta.shape[0] - idx) > idx:
                    dasbsm = dasbsm.iloc[idx:]
                    dasbsm.reset_index(drop=True, inplace=True)
                else:
                    dasbsm = dasbsm.iloc[:idx]

    # regression calculation
    model = smf.ols('Gentime ~ DasTime', data=dasbsm)
    coefficients = model.fit().params
    beta0 = coefficients.iat[0]
    beta1 = coefficients.iat[1]
    coef.append((device,trip,beta0,beta1)) 

    def gps2das(y):
        return round((y - beta0)/beta1, 0)

    def das2gps(x):
        return round(beta0+beta1*x, 0)
        
    # Get BSM dataset
    cols = 'RxDevice as Device, FileId as Trip, Gentime'
    bsm = pd.read_sql('SELECT {0} FROM BsmP1 WHERE RxDevice={1} and TxDevice={1} and FileId={2}'.format(cols,device,trip), conn2)
    delta = bsm['Gentime'].diff(1)
    assert not (delta < 0).any()

    # Pull video index information
    cols = 'Device, Trip, ForwardSize, ForwardCount, ForwardKey, VideoTime as DasTime'
    idxfwd = pd.read_sql('SELECT {0} FROM IndexForward WHERE Device={1} and Trip={2}'.format(cols,device,trip), conn3)
    if idxfwd.empty:
        print('No index file')
        continue
    delta = idxfwd['DasTime'].diff(1)
    assert not (delta < 0).any()    
  
    def closest_videotime_wo_going_over(x):
        idx = idxfwd['DasTime'].searchsorted(x)[0]-1
        if idx < 0:
            return None
        else:
            return idxfwd.iat[idx,5]
    
    def closest_gentime_wo_going_over(x):
        idx = bsm['Gentime'].searchsorted(x)[0]-1
        if idx < 0:
            return None
        else:
            return bsm.iat[idx,2]   
        
    # gentime -> videotime
    bsm['DasTimeHat'] = bsm['Gentime'].apply(gps2das).astype(int)
    V = bsm['DasTimeHat'].apply(closest_videotime_wo_going_over)
    bsm.insert(3, 'DasTime', V)
    BSM.append(bsm)
    
    # videotime -> gentime
    idxfwd['GentimeHat'] = idxfwd['DasTime'].apply(das2gps).astype(np.int64)
    G = idxfwd['GentimeHat'].apply(closest_gentime_wo_going_over)
    idxfwd.insert(6, 'Gentime', G)
    indexForward.append(idxfwd)

#%% Close connections
conn1.close()
conn2.close()
conn3.close()

coefs = pd.DataFrame(coef, columns=['Device','Trip','beta0','beta1'])
bsm2video = pd.concat(BSM, ignore_index=True)
video2bsm = pd.concat(indexForward, ignore_index=True)

delta1 = bsm2video['DasTimeHat'] - bsm2video['DasTime']
assert delta1.min() >= 0
delta2 = video2bsm['GentimeHat'] - video2bsm['Gentime']
assert delta2.min() >= 0

coefs.to_csv('coefficients.txt', index=False)
bsm2video.to_csv('bsm2video.txt', index=False, float_format='%.0f')
video2bsm.to_csv('video2bsm.txt', index=False, float_format='%.0f')

t1 = time.time()
print('Total: {:.1f} seconds'.format((t1-t0)))
