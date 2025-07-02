#!/usr/bin/env python
# coding: utf-8

# BPR function_hahahaha

# 
# <div class="alert alert-warning">
#     
# - Blue: notes (info) | White: slides | Green: main(success) | Red: past versions(danger)
# - Generally, the presentation follows <font size = 5> slides -> main text -> personal notes ->  code </font> in each subsection (Outline only appear at the beginning of each section, some subsections may not have personal notes or codes)
#     
# </div>
#     

# <p style="font-size: 25px;"> Weekly meeting </p>
# 
# - [weekley meeting collection](https://github.com/jooneui/BPR/blob/main/.ipynb_checkpoints/Weekly_meeting_BPR_function-checkpoint.ipynb)

# # Variable Definition 
# - Need to check it again
# - Time
#     - $\bar{t}$: Average time to move unit distance (min/mile)
#     - $t_0$: Free-flow travel time (min)
#     - $T$: Given(??) time period (hr)
# - Flow
#     - $N$: Daily Traffic volume (vpd) ($= N_0 \times l$, $l$: The number of lanes)
#     - $N_0$: Daily Traffic volume per lane (vpdpl)
#     - $C$: Road capacity (vpd) ($= C_0 \times l$)
#     - $C_0$: Road capacity per lane(vpdpl) = 32,000vpd
#     - $\bar{C}$: Pratical capacity (vpd)
#     - $q$: Flow rate per lane(vphpl)
# - Speed
#     - $\bar{v}$: Average speed(mph)
#     - $\mu$: Free-flow speed(mph)
# - Density
#     - $k$: Density(vpm)
#     - $k_c$: Critical density(vpm)
#     - $k_j$: Jam density(vpm)
# - Etc
#     - $d$: Loop detector length(m)
#     - $l$: The number of lanes

# __6/24/2025 Agenda__
# - PELT method application
# - Our research contribution
# - Fixed peak-period: non free-flow travel times in the low demand

# # Introduction

# ## The importance of Volume-Delay function(VDF)
# - VDF is a critical component of traffic assignment, quantifying travel time caused by observed volume and road capacity(Kucharski and Drabicki 2017)
# - VDF establishes the relationship between travel time, road traffic volume, and dynamic traffic state (Branston 1976; Nie and Zhang 2005; Patriksson 2015)
# - Accurate estimation and calibration of the current traffic demand and supply are crucial in identifying and addressing congested or oversaturated conditions (Yuyan Pan et al. 2023)

# ## BPR function
# - The Bureau of Public Roads (BPR), Davidson’s, Akcelik’s, and conical delay functions are the most commonly used link cost functions.
# - The BPR function has profound applications in transportation planning primarily as a result of its simple mathematical form, easily observable field inputs, and consistent performance (Mtoi and Ren, 2014; Das and Rama Chilukuri, 2020)
# - BPR function: $t=t_0(1+\alpha(\frac{N}{C})^\beta)$
#     - $\alpha$ is the scale parameter
#         - how the congestion effects change when the capacity is reached(Spiess, 1990)
#     - $\beta$ is a shape parameter

# ## Problem Statement
# 
# - ① BPR has not adequately incorporated fundamental diagrams(FD)
#     - BPR function
#         - $\bar{t}=\frac{1}{\bar{v}}=t_0[1+\alpha(\frac{N}{C})^\beta]$ ($N=qT$)
#     - Triangular F.D.
#         - $\bar{t} = \begin{cases} \frac{1}{\mu} \text{  (if  } k < k_c) \\ \frac{Tk_j}{N} - \frac{1}{\omega} \text{  (if  } k > k_c) \end{cases}$ [Appendix 1]
#     - Simply employing $N/C$ in the BPR fails to accurately depict the shape of FD

# In[1]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def BPR_function(t_0,C,alpha,beta,N):
    t =  t_0 * (1+alpha*(N/C)**beta)
    return t

def Triangular_FD_congested(q,k_j,w):
    t = (k_j/q-1/w)*60
    return t


# In[2]:


# 1. Variable Definition
# Unit: q:vph, C: vpd, k_j: vpm, mu: mph, tau: sec, w: vpm, t_0: min
q = np.linspace(0,1500,200)
q_c = np.linspace(1300,1500,200)
T = 24
N = q * T
C = 32000
k_j = 150
tau = 2 
mu = 60
w = 1/(tau * k_j)*3600
alpha = 0.15
beta = 4
t_0 = 1/mu*60

# 2. calculate the function value

t_BPR = BPR_function(t_0,C,alpha,beta,N)

t_FD_u = np.repeat(t_0,200)
t_FD_c = Triangular_FD_congested(q_c,k_j,w)

# 3. plot 
plt.plot(q,t_BPR, color='black',label = 'BPR')
plt.plot(q,t_FD_u, color='blue',label = 'FD_uncongested')
plt.plot(q_c,t_FD_c, color='blue',label = 'FD_congested')
plt.legend(fontsize = 10)
plt.xlabel('flow rate(vph)')
plt.ylabel('travel times(min)')
plt.title('BPR vs Triangular F.D.')


# - ② Discrepancy with the original paper(BPR, 1964)
#     - There are discrepancies in how variables are used between the original paper(BRP, 1964) and pratical application.
# ||BPR(1964)|Practical Usage|
# |:------:|:------------------:|-------------------------|
# |Expression|$t=t_0(1+\alpha(\frac{N}{\tilde{C}})^\beta)$|$t=t_0(1+\alpha(\frac{N}{C})^\beta)$|
# |$N$|Assigned volume(vpd)| Daily Traffic volume(??) (vpd)   |
# |$C$ or $\tilde{C}$|Practical capacity(vpd) $\approx 32,000vpd$| Road capacity(vpd)|
#     
#     - Practical capacity is much less than general road capacity, leading to a possible case of $N>C$
#         - The original paper also addressed this case as an example.
#     - However, in the measured data, it is impossible to directly observe the case where V/C is greater than 1.(Yuyan Pan et al. 2023)
# - Therefore, it is necessary to redefine the demand-supply relation($N/C$) that resolves the both drawbacks of BPR
#     - replacing the practical capacity with higher value does not resolve the first issue: The incorporation of FD into BPR
# - <span style="color:red"> Q) I would like to discuss the interpretation of practical capacity($\tilde{C}$)</span>
#     - <span style="color:red"> The practical capacity of 32,000vpd mentioned in BPR(1964) applies specifically to link 3403-3406. What if the link has only one lane? If then, the practical capacity varies based on the number of lanes in each link. For instance, a two-lane link may have a practical capacity of 64,000vp. I think this statement is more logical considering the varying road capacity depending on the number of lanes. </span>
# 
# 
# 
# 

# - __해당 부분 정리 필요!!__

# ## Objective

# 지금은 git을 위한 시간

# <div class="alert alert-danger">
# 
# - Propose advanced BPR function by newly defining traffic demand
#     - Traffic demand refers to the amount of vehicular or pedestrian traffic that is __expected or desired__ in a particular area or on a particular roadway
#         - Measure of the need for transportation infrastructure
# - Let's newly define traffic demand as $N'=q\cdot T(N)$, where $N'$ stands for desired trafffic volume and $w$ as road capacity(vph)
#     - __$T(N)$: the intensity of demand__(이거 설명 필요)
#         - 답변: T는 간단하게 congestion period를 의미함. 
#     - <span style="color:red"> Q) What about using T(k) instead of T(N) as N itself cannot distinguish between hyper- and under-congested. </span> 
#         - (ex. $T(N)=\frac{N}{q}$)
#             - $N$: Traffic volume (vpd)
#             - $q$: Annual average daily traffic (vph)
#             - $T$: Observed time period (hr)
#     - $w$: capacity(vpd?)
#         - __How can we define it? As Wished time windows need to be handled in time windows??__(이거)
# - Three cases for defining $N'$ 
#     - All-day: $T(N)$=24 & w are similar during the normal weekdays
#     - peak
#     - non-peak
#         - __Q) If $T(N)$ is a linear function of $N$, and $w$ is not function of $N$, how about plotting $N^2$ vs $\bar{z}$, and check if it follows BPR shape?__        
# - 어떻게 할 수 있을까??
#     - demand derivation 할 수 있을까?? 먼저 추세를 보자!!
# 
# 
# </div>

# ## Appendix
# 
# - 1. Triangular Fundamental Diagram
#     - $k \ge k_c$
#         - $q = \omega(k_j-k)$
#         - $k = k_j-\frac{q}{\omega}$
#         - $v = \frac{q}{k}=\frac{\omega q}{\omega k_j - q}=\frac{\omega q}{\omega \times \frac{\mu+\omega}{\mu\omega}C-q}=\frac{\omega q}{\frac{\mu+\omega}{\mu}C-q}=\frac{\mu\omega q}{\mu(C-q)+wC}$
#         - $z=\frac{1}{v}=\frac{\mu(C-q)+\omega C}{\mu \omega q}=\frac{C(\mu+\omega)}{\mu \omega q}-\frac{1}{\omega}=\frac{k_j}{q}-\frac{1}{\omega}$
#         - cf) $\bar{z}=\frac{\int_0^T z(t)q(t) dt}{\int_0^T q dt}=\frac{\int_0^T k_j-\frac{q}{\omega}dt}{\int_0^T q dt}=\frac{k_j T - \frac{\bar{q}T}{\omega}}{\bar{q}T}=\frac{k_j}{\bar{q}}-\frac{1}{\omega}=\frac{Tk_j}{N}-\frac{1}{\omega}$
#     - $k \lt k_c$
#         - $v = \mu$
#         - $z = \frac{1}{v}=\frac{1}{\mu}$
#         

# # Literature Review
# 
# - __Papers__
#     - __Yuyan Annie Pan et al., 2023__
#         - Background
#             - Exisiting VDFs have not adequately incorporated fundamental diagrams(FD)
#         - Objective
#             - An improved VDF is proposed, based on the FD by integrating the traffic flow model into the VDF.
#                 - Only using one parameter $m$, refering to maximum flow inertia coefficient
#             - The proposed VDF will be tested and validated in two cases: Beijing and LA
#                 - New model performs better than existing models with respect to RMSE and MAE
#         - [Methodology](./Yuyan_Annie_Pan_2023.ipynb)
#             - The hypercongested region of the FD experiences a left-right symmetric shift with $x=v/C=1$ as the reference point.
#             - <center> <img src="https://github.com/jooneui/fig_collection/blob/main/Fig2.png?raw=true", width = 70%>
#             - $tt= \begin{cases} t_0 \cdot [\frac{2}{1+\sqrt{1-(\frac{V}{C})^m}}]^{\frac{2}{m}}, \text{  if  } V/C \lt 1 \\  t_0 \cdot [\frac{2}{1-\sqrt{1-(2-\frac{V}{C})^m}}]^\frac{2}{m}, \text{  if  } V/C > 1 \end{cases}$
# - BPR drawbacks
#     - fails to accurately capture the dynamics of traffic flow (Pan et al., 2022) and queue evolution(Cheng et al. 2022; Zhou et al. 2022)
#     - its accuaracy decreases with higher values of $\beta$(Spiess 1990)
# - Other VDFs
#     - Davidson(1966, 1978): based on queueing theory
#     - Akcelik(1979,1991): linear extension of Davidson's function
#     - Tisato(1991): modified version Davidson's model, addressing congestion duration during oversaturated conditions
#     - Spiess(1990): canonical function
#     - Zhou et al.(2022): improved version of Spiess

# # Contribution

# - Yuyan Pan et al. (2022) reviewed VDFs: and checked various definitions of demand variables for congested conditions.
# - Wu et al. (2022) used the same concept of our research (demand: the total volume during the congested period), and assume this demand is originally intended for the most peak-hour, and showed this pattern using empirical data
#     - Even if assuming $W$ as one peak hour may not be realistic, our current empirical study does not include the determination of $W$. So I'm trying to clarify what the main contribution of this study actually is.
# <img src="./02_1_presentation_fig/VDF_review_demanddef.png" width=70%>
# - [The link to the Wu et al. (2022)](https://www.notion.so/2020-Xin-Burce-Wu-Characterization-and-calibration-of-volume-to-capacity-ratio-in-volume-delay-fun-16618fce4e52801b9e7fd9e9ec7b01b7)

# # Methodology
# ## Flow chart
# - <span style="color:red"> Q) For the raw data, I use $q$ to represent flow rates and $\bar{v}$ to denote the average velocity of vehicles. I would like to discuss its appropriateness. </span>
# - <span style="color:red"> I need to add steps for the Peak/Non-peak cases </span>
# 
# <center> <img src="https://github.com/jooneui/fig_collection/blob/main/Fig1.png?raw=true", width = "70%"> </center>

# # Data Description

# ## SR-91
# - Lane information(ex. HOT)
#     - NO HOT, but only HOV.
#     - VDS does not cover the HOV lane, but only for general-purpose lanes(4 out of 5 lanes).
#     - HOT in SR 91: SR 91 with the SR 55 Freeway (Costa Mesa Freeway) in Anaheim to its junction with I-15 in Corona(18 miles)
#     - Period: Jan. ~ Apr., Aug.~Oct. 2011, 
#     <center> <img src="https://ars.els-cdn.com/content/image/1-s2.0-S0191261517311050-gr9.jpg", width = 40%> </center>
# - Check consistency with Qinglong Yan et al.(2018); critical density, free-flow speed, etc.
#     - Yan et al. 2018. 
#         - Nine months (Jan., Feb., Mar., Apr., May, July, Sept., Oct., and Nov.) in 2011 with the sample size of 273 days
#         - 30sec data
#         - Using flow-rate and occupancy
#         - Critical occ: 0.164

# ## I-5
# - VDS: 1205583
# - 1 HOT lane, 6 GP lanes
# - congested during the morning peak period
# - Period: Jan. ~ Oct. 2011
# - <img src='./02_1_presentation_fig/I-5_Buenapark.png' width=60%>
# - Need to check 1205612
# - <img src='./02_1_presentation_fig/VDS1205583.png' width=70%>

# # Results
# 

# ## (Code) BPR function calibration depending on time interval size

# In[1]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib import dates
from matplotlib.dates import DayLocator, HourLocator,DateFormatter

import xlrd
import os
from time import time
import datetime as dt
from dateutil.parser import parse
import math
import statistics
from scipy.signal import find_peaks
import scipy.stats
import pickle
import csv
from datetime import datetime

from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from sklearn import preprocessing
import itertools
from itertools import chain

import warnings
warnings.filterwarnings('ignore')


# In[2]:


def rawdata_setting(directory,VDS_num,file_name,lane_num):
    """
    Upload raw-data and standardize the settings
    """
    
    rawdata = pd.read_excel("./11 Rawdata/%s/%s/%s" % (directory,VDS_num,file_name))
    
    rawdata.columns = ['time'] + [f'flow_{i}' for i in lane_num] + [f'occ_{i}' for i in lane_num]

    rawdata['time'] = pd.to_datetime(rawdata['time'])
    # 'time_filter' is to convert the time to minutes.(ex. 02:30:30 -> 150.30min)
    rawdata['time_filter'] = rawdata['time'].dt.hour*60 + rawdata['time'].dt.minute + rawdata['time'].dt.second/60
    # rawdata['time_filter'] = rawdata['time'].dt.hour*100 + rawdata['time'].dt.minute
    rawdata['time_hour'] = rawdata['time'].dt.hour
    
    return rawdata


# In[3]:


def avg_traffic_state(rawdata, time_frame, lane_num, gfactor):
    """
    Calculate average traffic state parameters based on raw traffic data.

    Parameters:
    - raw_data: DataFrame, contains raw traffic data with columns 'flow_1', 'flow_2', 'flow_3', 'flow_4',
                'occ_1', 'occ_2', 'occ_3', 'occ_4'
    - rawdata_flow, rawdata_density, rawdata_speed are switched to np.array,
    - rawdata_flow_df is DataFrame
    - time_frame: int, time frame for the data in minutes (e.g., 5 minutes)
    - lane_num: lane number to analyze(ex. lane_num = [1,2,3,4]
    

    Returns: The average covers all lanes, not based on each lane.
    - avg_speed: float, average speed in miles per hour(mph) 
    - avg_time: float, average time in minutes per mile(min/mile)
    - avg_flow: float, average flow in vehicles per hour per lane(vph)
    - avg_density: float, average density in vehicles per mile per lane(vpm)
    """
    # Step 0: Select the lane numbers for extracting data 
    flow_variable = [f'flow_{lane}' for lane in lane_num]
    occ_variable = [f'occ_{lane}' for lane in lane_num]
    gfactor_variable = [f'Lane {lane}' for lane in lane_num]

    # Step 1: Read rawdata
    # Step 1-1: Read volume data and transfer to flow-rates (vehicles per hour)
    rawdata_flow_df = rawdata[flow_variable] * (60 / time_frame)
    rawdata_flow = np.array(rawdata_flow_df)
    
    # Step 1-2: Read occupancy data(%) and divide by 100
    rawdata_occ = np.array(rawdata[occ_variable])/100
    
    # Step 1-3: Read gfactor and dulplicate it to the total number of rows
    # gfactor['Time'] = pd.to_datetime(gfactor['Time']).dt.hour

    # Define a lambda function to format the time in the HH:MM format, recognize it as a date, and extract its hour.
    gfactor['Time'] = gfactor['Time'].apply(lambda x: f"{x:02}:00" if isinstance(x, int) else x)
    gfactor['Time'] = pd.to_datetime(gfactor['Time'], format='%H:%M').dt.hour
    
    rawdata_gfactor = pd.merge(rawdata, gfactor, how='left', left_on='time_hour', right_on='Time')[gfactor_variable]
    ## fill NA gfactor with the mean of the rest of that row
    rawdata_gfactor = rawdata_gfactor.apply(lambda row: row.fillna(row.mean(skipna=True)),axis=1)
    rawdata_gfactor = np.array(rawdata_gfactor)
    
    # Step 2: calculate individual lane's density and speed
    # Step 2-1: Calculate average density(vpm)
    rawdata_density = rawdata_occ * 5280 / rawdata_gfactor
        
    # Step 2-2: Calculate average speed(mph)
    rawdata_speed = rawdata_flow / rawdata_density

    # Step 2-3: Calculate the CV for flow rates and density
    agg_flow_per_lane = np.mean(rawdata_flow, axis=0)
    cv_flow = np.std(agg_flow_per_lane, ddof=0)/np.mean(agg_flow_per_lane)
    
    agg_density_per_lane = np.mean(rawdata_density, axis=0)
    cv_density = np.std(agg_density_per_lane, ddof=0)/np.mean(agg_density_per_lane)
    
    agg_speed_per_lane = []
    
    # Step 3: calculate indivdual 5-min aggregated per lane speed
    for lane in lane_num:
        flow_unit = np.array(rawdata_flow).transpose()[(lane-1)].flatten()
        rest_flow_df = rawdata_flow_df.drop(columns = [f'flow_{lane}'])
        speed_unit = np.array(rawdata_speed).transpose()[(lane-1)].flatten()
        density_unit = np.array(rawdata_density).transpose()[(lane-1)].flatten()
        
        # assign value 0 to the traffic flow when the density is equal to zero(= speed is equal to inf)
        # when density=0, speed becomes inf, leading to be impossible to calculate the average speeds(sum_flow/sumproduct(flow,1/speed))
        # Assigning a traffic flow of zero to this case gives it zero weight, which doesn't affect the average speed, 
        # allowing the calculation of average speeds at the same time.
        inf_indices = (speed_unit == np.inf)
        flow_unit[inf_indices] = 0
        
        avg_speed_per_lane = average_speed_calculation(flow_unit, speed_unit, density_unit, rest_flow_df, malfunc_inclusion = False)
        agg_speed_per_lane.append(avg_speed_per_lane)
        
    cv_speed = np.std(agg_speed_per_lane, ddof=0)/np.mean(agg_speed_per_lane)
    
    # Step 4: calculate aggreate density & speed & flow(not related to the CV calculation)
    # Step 4-1: Flattening the flow and speed
    rawdata_flow = np.array(rawdata_flow).flatten()
    rawdata_speed = np.array(rawdata_speed).flatten()
    
    # Step 4-2: Calculate the average speed(mph), average time(min/mile), average flow(vph), and average density(vpm), 
    avg_speed = average_speed_calculation(agg_flow_per_lane, agg_speed_per_lane, agg_density_per_lane, agg_flow_per_lane.tolist(), malfunc_inclusion = False)
    avg_time = 1/avg_speed * 60
    avg_flow = rawdata_flow.mean()
    avg_density = avg_flow / avg_speed

    return avg_speed, avg_time, avg_flow, avg_density, cv_flow, cv_density, cv_speed, agg_flow_per_lane, agg_density_per_lane, agg_speed_per_lane


# In[7]:


""" Sometimes, the rawdata interval is too short to see the stable traffic pattern, so rawdata is aggregated to specific time interval.
This function address calculating traffic state variables in every pre-determined aggregated time interval.
"""

def aggregate_rawdata(rawdata, aggregate_timeframe, raw_timeframe, date, lane_num, gfactor,VDS_num):
    
    # Pre-compute time_slot for all data to avoid doing it in the loop
    rawdata['time_slot'] = (np.floor(rawdata['time_filter'] / aggregate_timeframe) + 1) * aggregate_timeframe
    
    # Initialize list to store each row's data for final DataFrame
    traffic_within_day = pd.DataFrame()
    plot_date = []
     
    # Operate on grouped DataFrame
    for time_slot, group in rawdata.groupby('time_slot'):
        if not group.empty:
            avg_speed, avg_time, avg_flow, avg_density, cv_flow, cv_density, cv_speed, agg_flow_per_lane, agg_density_per_lane, agg_speed_per_lane = avg_traffic_state(group, raw_timeframe, lane_num, gfactor)
        
            traffic_per_lane = pd.DataFrame([list(agg_flow_per_lane)+list(agg_density_per_lane)+list(agg_speed_per_lane)])            
            traffic_per_lane.columns = [f'{metric}_{lane}' for metric in ['flow', 'density', 'speed'] for lane in lane_num]
            
            traffic_entire_lanes = pd.DataFrame({'time_slot': group['time_slot'].unique(), 'speed': avg_speed, 'time': avg_time, 'flow': avg_flow, 'density': avg_density, 'cv_flow': cv_flow, 'cv_density': cv_density, 'cv_speed': cv_speed})
# , 'time_hour': group['time_hour'].unique()
            traffic_within_day = pd.concat([traffic_within_day, pd.concat([traffic_per_lane, traffic_entire_lanes], axis=1)], ignore_index=True)
            plot_date.append(time_slot)
                
    # Assuming avg_traffic_state is a function that computes the averages and cv correctly
    # Note: Ensure avg_traffic_state function is optimized and correctly utilizes vectorized operations
    
    # Save the data
    path_directory = f'./12 python file/{VDS_num}'
    os.makedirs(path_directory, exist_ok=True)
    
    with open(f'./12 python file/{VDS_num}/traffic_within_day_{date}_{aggregate_timeframe}aggmin_{lane_num}.p', 'wb') as file:
        pickle.dump(traffic_within_day, file)

    with open(f'./12 python file/{VDS_num}/plot_date_{date}_{aggregate_timeframe}aggmin.p', 'wb') as file:    
        pickle.dump(plot_date, file)
    
    return traffic_within_day, plot_date


# In[9]:


"""
flow_unit, speed_unit, density_unit: the type of the input must be "np.array"
rest_flow_df : dataframe time interval as row, lane_id as each column, so it contains values of flow rates in other lanes. 
malfunc_inclusion: 'malfunc_inclusion = True' means containing cells having malfunctioning values(flow<24vph, density<0.4). 
In that case, the flow rate needs to be changed to the average values from other lanes at same time interval, so as to prevent the weight of that cell becomes zero.
The speed value is updated to 1, as this cell refers value from malfunctioning sensors.
"""

def average_speed_calculation(flow_unit, speed_unit, density_unit, rest_flow_df, malfunc_inclusion):
    
    flow_unit = np.array(flow_unit)
    speed_unit = np.array(speed_unit)
    density_unit = np.array(density_unit)
    
    if (malfunc_inclusion == True):
        # Safely compute the multiplication, avoiding division by zero and handling NaN values
        # "set" makes it possible to remove overlapping row ids.
        flow_bound = 24
        density_bound = 0.4
        
        zero_row_id = list(set(chain(
            (idx for idx, value in enumerate(flow_unit) if value < flow_bound),
            (idx for idx, value in enumerate(density_unit) if value < density_bound))))

        if (len(zero_row_id)>0):
            # the case when calculating avg speed of a lane. so, the follwoing code is to update flow and speed value of a lane. In this case, the length of flow unit is equal to the row of the rest_flow_df
            if (len(flow_unit) == rest_flow_df.shape[0]):
                flow_unit[zero_row_id] = rest_flow_df.iloc[zero_row_id].mean(axis=1)
                speed_unit[zero_row_id] = 1

            # To calculate the average speed for a day across all lanes, the flow_unit list contains all flow values, and rest_flow_df is its DataFrame equivalent.
            # Therefore, the length of flow_unit equals the number of rows times the number of columns in rest_flow_df. 
            # To update the flow and speed values in case of a malfunction, 
            # rest_flow_df removes the current lane's data and calculates the average flow for the same time interval using the other lanes.
            elif (len(flow_unit) > rest_flow_df.shape[0]):
                zero_idx_list = [(idx // rest_flow_df.shape[0], idx % rest_flow_df.shape[0]) for idx in zero_row_id]

                for idx, (col_idx, row_idx) in enumerate(zero_idx_list):
                    flow_unit[zero_row_id[idx]] = rest_flow_df.drop(columns=[f'flow_{col_idx + 1}']).iloc[row_idx].mean()
                    speed_unit[zero_row_id[idx]] = 1

    with np.errstate(divide='ignore', invalid='ignore'):
        multiply = np.multiply(flow_unit, 1/speed_unit)
    # Sum the non-NaN results directly  (속도 0일 때 어떻게 할 지 논의해보기!!)
    
    sum_flow = flow_unit.sum()
    sum_product = np.nansum(multiply)
       
    avg_speed = sum_flow / sum_product
    
    return avg_speed


# In[11]:


"""
This is the plot of average flow and speed over time for every day.
"""

def plot_within_flowspeed_day(traffic_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num):
    # 1st Plot: Time vs Traffic Flow and Avg Speed
    fig, ax = plt.subplots(1,1, figsize=(9,6))
    fig.suptitle(f'Traffic State within a Day using {directory} data(Date: {file_name[8:-5]}({Day}))',fontsize=18)
    ax.plot(plot_date, traffic_day['flow'], color='tab:blue')
    
    # Configure x-axis ticks and labels
    x_ticks = range(0, 1500, 60)
    x_labels = range(0, 25, 1)
    ax.set_xticks(ticks=x_ticks, labels=x_labels, fontsize=10)
    ax.locator_params(axis='x', nbins=25)
    
    # Set plot title and labels
    ax.set_title(f'Average Flow and Speed over time (aggregated by every {aggregate_timeframe} min)',fontsize=13)
    ax.set_ylabel('Flow rates (vphpl)', color='tab:blue', fontsize=12)
    ax.tick_params(axis='y',labelcolor='tab:blue')
    ax.set_xlabel('Time (hr)', fontsize=12)
    ax.set_ylim(0,2500)
    ax.set_yticks(range(0,2600,200))
    
    # Create a twinx axis for the second line plot on the same subplot
    ax2 = ax.twinx()
    ax2.plot(plot_date, traffic_day['speed'], color='tab:red')
    ax2.set_ylabel('Average Speed (mph)', color='tab:red', fontsize=12)
    ax2.tick_params(axis='y',labelcolor='tab:red')
    ax2.set_ylim(0,120)
    ax2.set_yticks(range(0,130,10))

    ax.grid(True)

    directory_path = f"./02 fig/15 Unit time_flowspeed_all/{VDS_num}"
    # Create the directory
    os.makedirs(directory_path, exist_ok=True)

    plt.savefig(f'{directory_path}/{date}_{lane_num}.png')
    plt.close()


# In[13]:


"""
This is the plot of average flow and speed over time for every day.
"""

def plot_within_densityspeed_day(traffic_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num):
    # 1st Plot: Time vs Traffic Flow and Avg Speed
    fig, ax = plt.subplots(1,1, figsize=(9,6))
    fig.suptitle(f'Traffic State within a Day using {directory} data(Date: {file_name[8:-5]}({Day}))',fontsize=18)
    ax.plot(plot_date, traffic_day['density'], color='tab:blue')
    
    # Configure x-axis ticks and labels
    x_ticks = range(0, 1500, 60)
    x_labels = range(0, 25, 1)
    ax.set_xticks(ticks=x_ticks, labels=x_labels, fontsize=10)
    ax.locator_params(axis='x', nbins=25)
    
    # Set plot title and labels
    ax.set_title(f'Average Flow and Speed over time (aggregated by every {aggregate_timeframe} min)',fontsize=13)
    ax.set_ylabel('Densities (vpmpl)', color='tab:blue', fontsize=12)
    ax.tick_params(axis='y',labelcolor='tab:blue')
    ax.set_xlabel('Time (hr)', fontsize=12)
    ax.set_ylim(0,80)
    ax.set_yticks(range(0,85,5))
    
    # Create a twinx axis for the second line plot on the same subplot
    ax2 = ax.twinx()
    ax2.plot(plot_date, traffic_day['speed'], color='tab:red')
    ax2.set_ylabel('Average Speed (mph)', color='tab:red', fontsize=12)
    ax2.tick_params(axis='y',labelcolor='tab:red')
    ax2.set_ylim(0,120)
    ax2.set_yticks(range(0,130,10))

    ax.grid(True)

    directory_path = f"./02 fig/15 Unit time_densityspeed_all/{VDS_num}"
    # Create the directory
    os.makedirs(directory_path, exist_ok=True)

    plt.savefig(f'{directory_path}/{date}_{lane_num}.png')
    plt.close()


# ## Case 1) Speed-based peak-period

# __6/24/2025 Discussion__
# - Discussed PELT method
# - Apply simple line-segmentation method, and compare the methods: peak-periods, BPR fitting
# - Interpolation between the missing points

# ### Methodology: Speed based peak-period detection

# #### Speed threshold-based
# - Peak-period
#     - Define the peak period based on the travel speeds
#         - peak period: A period if the speed stays below the 'speed_upper_bound' for at least 'min_minutes', allowing up to 'max_outliers'.
#             - speed_upper_bound=40mph, min_minutes=90min, max_outliers = 7
#     - Travel demand: sum up the travel volumes during the peak period
#         - <img src='./02_1_presentation_fig/proj3_UE_v2.png' width=40%>
#     - Ideal arrival time window size($W$): Assume 120minutes(2hours)
#     - Average demand (vph): Travel demand (vehicles) / Ideal arrival window size (hours)
#         - __This determines the slope: Need to discuss with the criterion__
#         -  W=120 minutes(VDS 1203506), W=90 minutes (VDS 1205583) fit well
# - Non-peak period: The rest of the time within a day
#     - Average demand: the average traffic flow rate (vph)

# #### Derivative-based Line Segmentation

# - __Concept__
#     - To segment a cumulative signal (e.g., cumulative speed) into linear components by **detecting points where the slope (first derivative) changes significantly**.
#     - Changepoints can be identified **where the derivative exhibits significant shifts**, indicating transitions between segments.
# - __Methodology__
#     - **Step1) Compute First Derivative**: Approximate the slope by: $s_t = \frac{y_t - y_{t-1}}{\Delta t}$
#         - Here, $y_t$ is the cumulative value (e.g., cumulative speed) at time $t$.
#     -  **Step2) Smooth the Derivative**
#         - Apply a **moving average** to reduce noise and highlight underlying trends: $\hat{s}_t = \frac{1}{w} \sum_{i=t-w+1}^{t} s_i$
#             - Where $w$ is the smoothing window size.
#     - **Step3) Detect Slope Shifts**: Compute the **absolute difference** between consecutive smoothed slopes: $|\hat{s}_t - \hat{s}_{t-1}|$
#        - Flag $t$ as a **changepoint** if this difference exceeds a user-defined **threshold** $\delta$.

# #### Ramer–Douglas–Peucker (RDP) Algorithm

# - **Objective:**  
#     - To simplify a curve (a sequence of connected points) by reducing the number of points while preserving the overall shape within a specified tolerance.
# 
# - **Concept**
#     - The RDP algorithm identifies and retains **key points (corners or bends)** that are critical to the shape of the curve.
#     - Intermediate points that lie within a user-defined distance (**epsilon, ε**) from a straight-line approximation are discarded.
# - **Methodology**
#     - **Step1) Start with the Full Curve**: Connect the **first and last points** with a straight line.
#     - **Step2) Find the Furthest Point**: Calculate the **perpendicular distance** of all intermediate points to this line.
#        - Identify the point with the **maximum distance**.
#     - **Step3) Check the Distance**: If the maximum distance is **greater than the tolerance ε**, retain this point and **recursively apply RDP** to the two sub-curves:
#          - From the start to this point
#          - From this point to the end
#          - If the maximum distance is **less than or equal to ε**, remove all intermediate points between the start and end.
#      - **Step4) Repeat Until Simplified**: Continue until all points meet the distance condition.
# 

# #### PELT method

# ##### General definition
# - __objective function(L2 cost)__
#     - Let the time series be $y_1, y_2, \dots, y_T$, and let the set of changepoints be $\{\tau_1, \tau_2, \dots, \tau_m\}$, where:
# $$\tau_0 = 0, \quad \tau_{m+1} = T$$
#     - Each segment is defined over the interval \( (\tau_i, \tau_{i+1}] \). The objective function minimized by PELT is: $\min_{\{\tau_1, \dots, \tau_m\}} \left\{ \sum_{i=0}^{m} \sum_{t = \tau_i + 1}^{\tau_{i+1}} \left( y_t - \bar{y}_{(\tau_i+1):\tau_{i+1}} \right)^2 + \beta m \right\}
# $
#     - where:
#         - $\bar{y}_{(\tau_i+1):\tau_{i+1}}$ is the mean of the segment from $\tau_i + 1$ to $\tau_{i+1}$,
#         - $\beta$ is a fixed penalty for each changepoint,
#         - The inner sum $\sum (y_t - \bar{y})^2$ represents the L2 cost (sum of squared deviations from the segment mean).

# ##### Speed-based PELT
# - __Setting__
#     - To identify peak periods from traffic speed time series, we implemented the Pruned Exact Linear Time (PELT) algorithm using a change-point detection framework based on segment-level shifts in average speed. The segmentation aims to detect intervals where speed patterns deviate from free-flow conditions.
#     - Penalty: penalty = 100000
#     - Minimum Segment Length: 5min
#         - This ensures that each detected segment spans at least the minimum duration for what we consider a meaningful peak period.
#     - cumulative speed profile 
# - __Segment Classification and Output__
#     - After segmentation, the average speed of each segment is calculated.
#     - Segments with an average speed below 50 mph are labeled as peak periods; all others are labeled as off-peak.
#     - If multiple peak segments are adjacent, they are grouped together under the same label.
#     - For each peak period, the start time and duration are recorded for further analysis.

# ### Peak-period detection result

# #### Temporal scale of data
# - RDP: Divide each off-peak period into a single piece from 30-minute time intervals.
# - Time temporal matters to peak-period.
#     - 5-min: [{'start': '06:50', end: '08:30', 'length': 100}]
#     - 30-min: [{'start': '06:30', end: '08:30', 'length': 120}]
#     - 60-min: [{'start': '06:00', end: '09:00', 'length': 180}]
# - In some cases, 60-min interval has significantly decreased peak-period size
# - A 60-minute interval can be too coarse to capture detailed patterns.
#     - whereas I think a 30-minute interval offers a better balance between resolution and stability.

# <img src='./02_1_presentation_fig/RDQ_tempscale_sensitivty.png' width=80%>

# #### Methodology comparison

# - Case1) Speed threshold-based
#     - peak period: A period if the speed stays below the _'speed_upper_bound'_ for at least _'min_minutes'_, allowing up to _'max_outliers'_:
#         -  speed_upper_bound=40mph, min_minutes=90min, max_outliers = 7 
# - Case2) PELT
# - Case3) RDQ
# - Case4) Derivative-based

# ##### Result
# - The results are almost the same, but slightly different.
# - The speed-based method tends to cover the entire peak period, often with a broader range.
#     - The RDP method is closer to line segmentation:
#         - It uses the cumulative curve and identifies key points that preserve the overall shape.
#         - Because of that, the RDP cannot capture the period of congestion dissipation in overall.
#     - The PELT and derivative-based methods are more similar to point segmentation: They detect changepoints when sudden drops occur.
#         - The derivative method identifies sharp changes in slope, which indicate speed drops.
#         - PELT detects changes based on the overall speed pattern.
#         - Because of that, they cannot capture the period of congestion formation in overall.

# <img src='./02_1_presentation_fig/Speedbased_method_comparison.png' width=100%>

# ##### BPR function fitting
# - *I need to eliminate the off-peak data
# - Case 1 (speed-threshold-based) shows the most typical BPR curve shape.
# - We need to consider the reason behind this difference.
#     - One possible explanation is that during the peak period, speed drops sharply unlike the theoretical triangular shape of congestion cost.
#     - As a result, there's little incentive to shift arrival times within the peak period, since congestion levels remain similarly high.
#     - Therefore, some individuals whose preferred arrival time falls within the peak period (W) tend to avoid it altogether and travel right next to the speed drop. In this case, it's important to fully capture the peak period—up until speeds return to free-flow conditions
# - If Case 1 is found to be more meaningful, we should develop a method using Cases 2, 3, and 4 that captures a similarly broad range—
#     - since Cases 2, 3, and 4 are methodologically more robust.
#     - Case 2,3,4 shows simliar to entire-day case.

# <img src='./02_1_presentation_fig/Speedbased_method_BPR_comparison.png' width=100%>

# ##### Result and Discussion (2025/6/24)

# __The L2-Based PELT Algorithm May Not Detect the Exact Transition Point__
# 
# __Cumulative of speed profile__
# - The changepoint is not explicitly aligned with the actual transition point. Instead, it appears either before or after the true transition. This issue persists regardless of the penalty size.
# - In the case of a penalty value of 100, the changepoint may align with the actual transition point. However, it doesn't seem to detect the peak period itself—instead, it tends to divide the time series into as many small segments as possible and then selects those segments where the average speed falls below the threshold.
# - <img src='./02_1_presentation_fig/PELT_speed_penalty_sensitivity analysis.png' width=150%>

# __Cumulative of Speed-differential profile__
# - Instead of using the speed profile, I used the speed differential profile, which resulted in a more realistic segmentation.
#     - ex.) speed_profile = [v1, v2, v3, v4] → differential profile = [v2-v1, v3-v2, v4-v3]
# - <img src='./02_1_presentation_fig/PELT_speeddiff_penalty_sensitivity analysis.png' width=100%>

# __My opinion why speed is not working perfectly__
# - PELT detects the changepoint when slope changes. In the cumulative speed profile, the slope is speed.
# - Peak periods are not stationary states; within these periods, speeds gradually decrease and fluctuate significantly compared to off-peak times. From the PELT perspective, this volatility makes it difficult to precisely identify true transition points, as the signal lacks post-change stability.
# - In contrast, near-stationary state detection relies on segments of consistent values after changepoints, making the transition boundaries more distinct and reliable.
# - Reframing the speed profile into its first-order differential better aligns with this stationary-state detection logic, as it highlights periods of rapid change followed by relative stability.
# - Additionally, daily patterns in speed differentials more closely resemble individual speed trajectories during deceleration. When drivers maintain the same speeds and decrease with constant acceleration, using acceleration would be more straightforward to detect the changepoints.
# - <img src='./02_1_presentation_fig/PELT_driver_profile.png' width=30%>

# - The limitation of Speed-based PELT
#     - may Not Detect the Exact Transition Point
#     - [70, 70, 70, 55, 40, 35, 35, 35]
#     - We evaluate possible changepoints at:
# 
# __✅ Case 1: Split at `t = 3`__ (**True transition point**)__
# - **Segment 1**: \([70, 70, 70]\)  
#   Mean: 70  
#   Cost:  
#   \[
#   (70 - 70)^2 + (70 - 70)^2 + (70 - 70)^2 = 0
#   \]
# 
# - **Segment 2**: \([55, 40, 35, 35, 35]\)  
#   Mean: 40  
#   Cost:  
#   \[
#   (55 - 40)^2 + (40 - 40)^2 + 3 \times (35 - 40)^2 = 225 + 0 + 75 = 300
#   \]
# 
# **Total Cost: 0 + 300 = 300**
# 
# ---
# 
# __✅ Case 2: Split at `t = 4` 
# 
# - **Segment 1**: \([70, 70, 70, 55]\)  
#   Mean: 66.25  
#   Cost:  
#   \[
#   3 \times (70 - 66.25)^2 + (55 - 66.25)^2 = 42.19 + 126.56 = 168.75
#   \]
# 
# - **Segment 2**: \([40, 35, 35, 35]\)  
#   Mean: 36.25  
#   Cost:  
#   \[
#   (40 - 36.25)^2 + 3 \times (35 - 36.25)^2 = 14.06 + 4.69 = 18.75
#   \]
# 
# **Total Cost: 168.75 + 18.75 = 187.5**

# ### (Code) Speed-based peak period

# In[371]:


def PELT_plot(df, bkpts, date, VDS_num, aggregate_timeframe, method):
    time_slot_hour = df['time_slot'] / 60
    
    fig, ax1 = plt.subplots(figsize=(12, 5))

    # Left axis: Changepoints (as vertical lines)
    ax1.set_xlabel('Time Interval (Hours)')
    ax1.set_ylabel('Speed Diff')
    ax1.set_title('Cumulative Speed with Detected Peak Periods')
    ax1.grid(True)
    ax1.set_xlim(0, 25)
    ax1.set_xticks(np.arange(0, 25, 1))

    # Plot changepoints
    for bkpt in bkpts:
        ax1.axvline(x=time_slot_hour[bkpt], color='red', linestyle='--',
                    label='Changepoint' if bkpt == bkpts[0] else "")

    # Right axis: Cumulative speed pattern
    ax1.plot(time_slot_hour, df['speed'], color='green', linewidth=1, label='Speed')
    ax1.set_ylim(0,80)


    time_slot_hour_re = [0] + time_slot_hour.to_list()
    cumsum_speed_re = [0] + df['cumsum_speed'].to_list()

    ax2 = ax1.twinx()
    ax2.plot(time_slot_hour_re, cumsum_speed_re, color='blue', linewidth=1, label='Cumulative Speed Diff')
    ax2.set_ylabel('Cumulative Speed Diff')
    ax2.set_ylim(0, max(cumsum_speed_re))

    # Handle legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    fig.tight_layout()
    plt.savefig(f'./02 fig/16 PELT/{VDS_num}_{date}_{aggregate_timeframe}_{method}.png')
    # plt.show()  # Uncomment if you want to display the plot


# In[373]:


# "Instead of using PELT libary, this is the custom Pelt method"

# def custom_pelt_l2(signal, penalty, min_size=1):
#     """
#     Handwritten PELT algorithm using L2 cost (mean shift).
    
#     Parameters:
#         signal (np.ndarray): 1D array of cumulative values (e.g., cumulative speed).
#         penalty (float): Penalty to control number of changepoints.
#         min_size (int): Minimum samples per segment.
    
#     Returns:
#         List[int]: Indices where changepoints are detected.
#     """
#     n = len(signal)
#     cost = np.full(n + 1, np.inf)
#     cost[0] = 0
#     cp = [[] for _ in range(n + 1)]

#     for t in range(min_size, n + 1):
#         for s in range(max(0, t - 500), t - min_size + 1):  # optional window limit
#             segment = signal[s:t]
#             mean = np.mean(segment)
#             seg_cost = np.sum((segment - mean) ** 2)
#             total_cost = cost[s] + seg_cost + penalty
#             if total_cost < cost[t]:
#                 cost[t] = total_cost
#                 cp[t] = cp[s] + [t]

#     return cp[n]


# In[375]:


# def pelt_speedbased_peak(df, column, speed_upper, model, date, VDS_num, penalty, aggregate_timeframe, min_length, method):
import numpy as np
import ruptures as rpt
import pandas as pd

def pelt_speedbased_peak(df, column, speed_upper, model, date, VDS_num, penalty, aggregate_timeframe, min_length, method):
    """
    Detect peak periods using PELT on cumulative speed profile.

    Args:
        df (DataFrame): Time-indexed traffic data with a 'speed' column.
        column (str): Name of speed column.
        speed_upper (float): Threshold to separate peak vs non-peak.
        model (str): Cost model for ruptures (e.g., "rbf", "l2").
        penalty (float): Penalty for adding a changepoint.

    Returns:
        DataFrame: Original df with added 'division' column.
    """
    df = df.copy()
    
    # Step 1: Compute cumulative speed (helps detect changes in slope)
    df["cumsum_" + column] = df[column].cumsum()

    # Step 2: Apply PELT on cumulative speed
    signal = df[column].values
    # bkpts = custom_pelt_l2(signal, penalty=penalty, min_size=int(min_size) if min_size else 1)

    
    algo = rpt.Pelt(model=model, jump=1).fit(signal)
    # algo = rpt.Pelt(model=model, min_size=min_size,jump=1).fit(signal)

    
## Breakpoints: [23, 45, 100]: Segment 1: indices 0 to 22 / Segment 2: indices 23 to 44 / Segment 3: indices 45 to 99
    bkpts = algo.predict(pen=penalty)
    print("Breakpoints:", bkpts)
    
    # Step 3: Label segments
    df['division'] = 0
    idx = 0
    start = 0
    prev_peak = False  # Track whether previous segment was a peak
    length = 0
    
    peak_list = []
    
    for end in bkpts:
        seg_mean_speed = df[column].iloc[start:end].mean()
        
        if seg_mean_speed < speed_upper:
            if prev_peak:
                # Continue same peak period (same idx)
                length += end-start
                df.loc[start:(end), 'division'] = idx
            else:
                # Start new peak period
                idx += 1
                df.loc[start:(end), 'division'] = idx
                prev_peak = True
                
                start_time = df.iloc[start]['time_slot']
                peak_list.append({'idx': idx, 'start': f'{int(start_time // 60):02d}:{int(start_time % 60):02d}', 'length': length * aggregate_timeframe})
                
                # when 1st peak-period is detected (from non-peak in the early morning to first peak-period is detected)
                if peak_list[-1]['idx'] == 1:
                    length = end-start
                    # implement the 'length' "multiply 5" means to convert to 'minutes' unit.
                    peak_list[-1]['length'] = length * aggregate_timeframe    
                # from when 2nd peak-period is detected. (need to implement the previous peak-period time length and initialize the length= end-start)
                elif peak_list[-1]['idx'] > 1:
                    # "multiply 5" means to convert to 'minutes' unit.
                    peak_list[-2]['length'] = length * aggregate_timeframe
                    length = 0
                    length += end-start
                    
                start=end
                
            print(bkpts, end, idx)
        else:
            prev_peak = False  # Reset if non-peak
            

        start = end

    if len(peak_list) >= 1:    
        peak_list[-1]['length'] = length * aggregate_timeframe

    for i, length in enumerate(peak_list):
        length = peak_list[i]['length']
        print(length,"len")
        if length < min_length:
            idx_f = peak_list[i]["idx"]
            print("dix_f",idx_f)
            df.loc[df['division']==idx_f,"division"] = 0
            print(df['division'].unique())

    # If there are 100dataset, the last index in bkpts is 100. when plotting the changepoints, time_slot[100] is out of boundary, so omit the last index
    bkpts = bkpts[:-1] 
    print(df.loc[df['division']==1,'time_slot'])

    PELT_plot(df, bkpts, date, VDS_num, aggregate_timeframe, method)

    return df, peak_list


# In[377]:


# def derivative_based_segmentation(df, column, slope_threshold, window, min_gap, speed_upper, aggregate_timeframe, min_length, method):
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def derivative_based_segmentation(df, column, slope_threshold, window, min_gap, speed_upper, aggregate_timeframe, min_length, method):
    """
    Detect changepoints based on first derivative of cumulative speed.

    Args:
        df (DataFrame): Must include 'cumsum_speed' or any cumulative variable.
        column (str): Column name for cumulative value.
        slope_threshold (float): Threshold to detect slope changes (in derivative units).
        window (int): Window size for moving average smoothing.
        min_gap (int): Minimum distance between changepoints (in rows).

    Returns:
        List[int]: List of changepoint indices.
    """
    df = df.copy()

    df['cumsum_'+column] = df[column].cumsum()
    # 1. First derivative
    df['slope'] = df['cumsum_'+column].diff() / (aggregate_timeframe/60)

    # 2. Smooth the slope
    df['slope_smooth'] = df['slope'].rolling(window=int(window/aggregate_timeframe), center=False).mean()

    # 3. Compute slope difference between adjacent windows
    slope_diff = df['slope_smooth'].diff().abs()

    # 4. Detect changepoints where slope changes sharply
    changepoints = slope_diff[slope_diff > slope_threshold].index.tolist()

    # Step 3: Label segments
    df['division'] = 0
    idx = 0
    start = 0
    prev_peak = False  # Track whether previous segment was a peak
    length = 0
    
    peak_list = []
    
    for end in changepoints:
        seg_mean_speed = df[column].iloc[start:end].mean()
        
        if seg_mean_speed < speed_upper:
            if prev_peak:
                # Continue same peak period (same idx)
                length += end-start
                df.loc[start:(end), 'division'] = idx
            else:
                # Start new peak period
                idx += 1
                df.loc[start:(end), 'division'] = idx
                prev_peak = True
                
                start_time = df.iloc[start]['time_slot']
                peak_list.append({'idx': idx, 'start': f'{int(start_time // 60):02d}:{int(start_time % 60):02d}', 'length': length * 5})
                
                # when 1st peak-period is detected (from non-peak in the early morning to first peak-period is detected)
                if peak_list[-1]['idx'] == 1:
                    length = end-start
                    # implement the 'length' "multiply 5" means to convert to 'minutes' unit.
                    peak_list[-1]['length'] = length * aggregate_timeframe
                # from when 2nd peak-period is detected. (need to implement the previous peak-period time length and initialize the length= end-start)
                elif peak_list[-1]['idx'] > 1:
                    # "multiply 5" means to convert to 'minutes' unit.
                    peak_list[-2]['length'] = length * aggregate_timeframe
                    length = 0
                    length += end-start
                    
                start=end
                
            print(changepoints, end, idx)
        else:
            prev_peak = False  # Reset if non-peak
            

        start = end

    if len(peak_list) >= 1:    
        peak_list[-1]['length'] = length * aggregate_timeframe

    for i, length in enumerate(peak_list):
        length = peak_list[i]['length']
        print(length,"len")
        if length < min_length:
            idx_f = peak_list[i]["idx"]
            print("dix_f",idx_f)
            df.loc[df['division']==idx_f,"division"] = 0
            print(df['division'].unique())
            
    PELT_plot(df, changepoints, date, VDS_num, aggregate_timeframe, method)

    return df, peak_list


# In[379]:


# def rdp_segmentation_peak(df, column, epsilon, speed_upper, aggregate_timeframe, date, VDS_num, min_length, method):
from rdp import rdp
import numpy as np
import pandas as pd

def rdp_segmentation_peak(df, column, epsilon, speed_upper, aggregate_timeframe, date, VDS_num, min_length, method):
    """
    Segment cumulative speed using true RDP and classify segments as peak/non-peak.

    Args:
        df (DataFrame): Input DataFrame with 'time_slot' and speed column.
        column (str): Speed column name.
        epsilon (float): Tolerance for RDP (controls segmentation granularity).
        speed_upper (float): Threshold to define peak periods.
        aggregate_timeframe (int): Seconds per row (e.g., 300).
        date (str): For plotting.
        VDS_num (str): For plotting.

    Returns:
        Tuple: (df with division labels, peak_list summary)
    """
    df = df.copy()
    df["cumsum_" + column] = df[column].cumsum()

    # 1. Apply RDP on (row index, cumsum_speed)
    points = np.column_stack([df.index, df["cumsum_" + column].values])
    rdp_points = rdp(points, epsilon=epsilon)
    
    # 2. Directly extract row indices from RDP output
    rdp_indices = rdp_points[:, 0].astype(int).tolist()
    print("rdp_indices",rdp_indices)
    
    # 3. Ensure last row is included
    if rdp_indices[-1] != df.index[-1]:
        rdp_indices.append(df.index[-1])

    # 4. Label segments + detect peak periods
    df["division"] = 0
    idx = 0
    start = 0
    prev_peak = False
    length = 0
    peak_list = []

    for end in rdp_indices[1:]:  # skip first (start = 0)
        print(start,end)
        seg_mean_speed = df[column].iloc[start:end].mean()

        if seg_mean_speed < speed_upper:
            if prev_peak:
                length += end - start
                print(start,end,"step1")
                df.loc[start:(end), "division"] = idx
            else:
                print(start,end,"step2")
                idx += 1
                df.loc[start:(end), "division"] = idx
                prev_peak = True

                start_time = df.iloc[start]["time_slot"]
                peak_list.append({
                    "idx": idx,
                    "start": f"{int(start_time // 60):02d}:{int(start_time % 60):02d}",
                    "length": length * aggregate_timeframe 
                })

                if idx == 1:
                    length = end - start
                    peak_list[-1]["length"] = length * aggregate_timeframe
                else:
                    peak_list[-2]["length"] = length * aggregate_timeframe
                    length = end - start

            start = end
        else:
            prev_peak = False
            start = end

    if len(peak_list) >= 1:
        peak_list[-1]["length"] = length * aggregate_timeframe 

    print(peak_list)
    for i, length in enumerate(peak_list):
        length = peak_list[i]['length']
        print(length,"len")
        if length < min_length:
            idx_f = peak_list[i]["idx"]
            print("dix_f",idx_f)
            df.loc[df['division']==idx_f,"division"] = 0
            print(df['division'].unique())

    # Plot with RDP breakpoints
    PELT_plot(df, rdp_indices, date, VDS_num, aggregate_timeframe, method)

    return df, peak_list


# In[381]:


# def speedbasedpeak(df, column, speed_upper, min_minutes, max_outliers, aggregate_timeframe, method):
def speedbasedpeak(df, column, speed_upper, min_minutes, max_outliers, aggregate_timeframe, method):
    start = 0
    outliers = 0
    idx = 1

    prev = 0
    continuity = 0
    peak_list = []
    changepoints = []

    df = df.copy()
    df["cumsum_" + column] = df[column].cumsum()
    
    df['division'] = 0
    interval_size = df['time_slot'][1] - df['time_slot'][0]
    
    for i in range(len(df)):
        if df[column][i] >= speed_upper:
            outliers += 1

            # prev == i-1
            if prev == (i-1):
                continuity +=1
                prev = i
            else:
                continuity = 0

            if continuity > max_outliers/3: 
                outliers = 0
                continuity = 0
                start = i

        if outliers > max_outliers:
            if (i - start) * interval_size > min_minutes:
                df.loc[start:i,'division'] = idx

                start_time = df.iloc[start]["time_slot"]
                length = i - start
                
                peak_list.append({
                    "idx": idx,
                    "start": f"{int(start_time // 60):02d}:{int(start_time % 60):02d}",
                    "length": length * aggregate_timeframe
                })
                changepoints.append(start)
                changepoints.append(i)

                idx += 1
                
            start = i
            outliers = 0
            prev = i

    # Plot with RDP breakpoints
    PELT_plot(df, changepoints, date, VDS_num, aggregate_timeframe, method)
    
    return df, peak_list


# In[383]:


# Parameters for handling the data
# raw_timeframe: Defines the timeframe unit in minutes for the input raw data 
# (e.g., 30 seconds is represented as 0.5 minutes).
raw_timeframe = 0.5

# path: The base directory path where the raw data files are stored.
path = '/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/11 Rawdata'

# directory: The subdirectory name under the main path where the data files are located.
directory = '30sec'

# VDS_num: The subdirectory name under the main path where the data files are located.
VDS_num = '1205583'
# VDS_num = '1203506'

# total_lane_raw = 4
lane_num = [1,2,3,4,5,6]
# lane_num = [1,2,3,4] 

# Constructs the full path to the directory containing the data files.
full_path = os.path.join(path, directory, VDS_num)

# Retrieves a list of all files in the specified directory.
# This list will be used to iterate over or reference the data files for processing.
file_list = sorted(os.listdir(full_path))
if '.DS_Store' in file_list:
    file_list.remove('.DS_Store')


# total_lane_raw: Total number of lanes at the rawdata
# lane_num: Specifies the range of lane numbers to be analyzed.
# This is used to filter or segment the data based on lane information.

Day_list = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

# Printing the list of files found in the specified directory.
# print("Files in the specified directory:", file_list)


# In[966]:


# Divide the traffic_analysis depending on the time_scale

c_daily_flow = []
c_daily_traveltimes = []
c_date = []
c_period = []
c_dayofweek = []
c_totaldemand = []

## "entireday", "peak" "hour" 'speedbasedpeak'
temporal_scale = 'speedbasedpeak'
set_peak_period = pd.DataFrame(columns=["date", "peak_list"])

aggregate_timeframe = 5
num_frame = aggregate_timeframe/raw_timeframe

#speedbasedpeakmethod: pelt, derivative, RDP, joon
method = 'RDP'
min_length= 30

aggregate_time_list = list(range(0, 60*24, aggregate_timeframe)[1:])

for i, file_name in enumerate(file_list):
    
    # Step 0: uploading data and unifying rawdata's format
    date = file_name[-11:-5]
    gfactor = pd.read_excel(f'{path}/gfactor/{VDS_num}/gfactor_{date}.xlsx')
    rawdata = rawdata_setting(directory,VDS_num,file_name,lane_num)

    # Step 0: Filter our the day with more than 'missing_ratio" 
    print(file_name)
    missing_ratio = 0.05
    ## if there are missing data more than missing_ratio, then skip this iteration!
    if len(rawdata) < (1-missing_ratio) * (24*60) / raw_timeframe:
        continue
        
    print(file_name)
    # Step 1: Load data for each day and process it
    # Load raw data from csv file
    year = f'20{date[0:2]}'
    Day_list = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    Day = Day_list[int(rawdata.loc[0,'time'].weekday())]
    
    python_file_path = f'./12 python file/{VDS_num}/traffic_within_day_{date}_{aggregate_timeframe}aggmin_{lane_num}.p'
    

    if not  os.path.exists(python_file_path):
        Day = Day_list[int(rawdata.loc[0,'time'].weekday())]
    #     # Step 1: aggregate data to plot or calculate the data
        traffic_within_day, plot_date = aggregate_rawdata(rawdata, aggregate_timeframe, raw_timeframe, date, lane_num, gfactor, VDS_num)

        with open(python_file_path, 'wb') as file:
            pickle.dump(traffic_within_day, file)

        with open(f'./12 python file/{VDS_num}/plot_date_{date}_{aggregate_timeframe}aggmin.p', 'wb') as file:    
            pickle.dump(plot_date, file)
    else: 
        # Step 1-1: upload saved file
        with open(python_file_path, 'rb') as file:
            traffic_within_day = pickle.load(file)

        with open(f'./12 python file/{VDS_num}/plot_date_{date}_{aggregate_timeframe}aggmin.p', 'rb') as file:
            plot_date = pickle.load(file)

    # plot_within_flowspeed_day(traffic_within_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num)
    # plot_within_densityspeed_day(traffic_within_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num)

    ## step 2: interpolate the missing data
    notin_timeslot = sorted([x for x in aggregate_time_list if x not in traffic_within_day['time_slot'].to_list()])
    traffic_within_day_intpol = traffic_within_day
    print("notin",notin_timeslot)

    for time in notin_timeslot:
        nearest_prev_time = int(traffic_within_day['time_slot'][traffic_within_day['time_slot'] < time].max())
        nearest_after_time = int(traffic_within_day['time_slot'][traffic_within_day['time_slot'] > time].min())

        gap_size = nearest_after_time - nearest_prev_time

        row_prev = traffic_within_day[traffic_within_day['time_slot'] == nearest_prev_time].copy()
        row_after = traffic_within_day[traffic_within_day['time_slot'] == nearest_after_time].copy()
        
        # Ensure all values are numeric
        row_prev = row_prev.apply(pd.to_numeric, errors='coerce')
        row_after = row_after.apply(pd.to_numeric, errors='coerce')

        row_prev = row_prev.iloc[0].astype(float)
        row_after = row_after.iloc[0].astype(float)

        # Perform interpolation
        weight_prev = (nearest_after_time - time) / gap_size
        weight_after = (time - nearest_prev_time) / gap_size
        
        new_row = row_prev * weight_prev + row_after * weight_after
        new_row["time_slot"] = time  # ensure time_slot is correctly inserted

        traffic_within_day_intpol = pd.concat([traffic_within_day_intpol, new_row.to_frame().T], ignore_index=True)

    traffic_within_day_intpol = traffic_within_day_intpol.sort_values(by="time_slot").reset_index(drop=True)
    
    # print(len(traffic_within_day_intpol), "time_final")
    traffic_within_day.to_csv(f"traffic_within_day_{file_name}.csv")
    traffic_within_day_intpol.to_csv(f"traffic_within_day_intpol_{file_name}.csv")

    ## step3: time-period filtering
    if temporal_scale == 'hour':
        time_unit = 90
        traffic_within_day_intpol['division'] = traffic_within_day_intpol['time_slot'] // 60

    elif temporal_scale == 'peak':
        morning_peak = [4,10]
        # afternoon_peak = [16,22]
        afternoon_peak = [14,20]

        traffic_within_day['division'] = 0
        # morning peak-perid: 1 afternoon-peak period: 2
        traffic_within_day_intpol.loc[(traffic_within_day_intpol['time_slot'] >= morning_peak[0] * 60) &(traffic_within_day_intpol['time_slot'] <= morning_peak[1] * 60), 'division'] = 1
        traffic_within_day_intpol.loc[(traffic_within_day_intpol['time_slot'] >= afternoon_peak[0] * 60) &(traffic_within_day_intpol['time_slot'] <= afternoon_peak[1] * 60),'division'] = 2

    elif temporal_scale == 'entireday':
        traffic_within_day_intpol['division'] = 0

    elif temporal_scale == 'speedbasedpeak':
        # non-peak period: 0 peak-period: larger than or equal to 1
        # traffic_within_day = speedbasedpeak(traffic_within_day, column='speed', speed_upper=40, min_minutes=90, max_outliers = 7)
        # "60min"
        # min_peak_len = 60
        
        if  method == 'pelt':
            traffic_within_day_intpol, peak_list = pelt_speedbased_peak(traffic_within_day_intpol, column='speed', speed_upper=50, model="l2", date=date, VDS_num=VDS_num, penalty=1000, aggregate_timeframe=aggregate_timeframe, min_length= min_length, method = method)
        elif method == 'derivative':
            traffic_within_day_intpol, peak_list = derivative_based_segmentation(traffic_within_day_intpol, column='speed', slope_threshold=80, window=15, min_gap=10, speed_upper=55, aggregate_timeframe=aggregate_timeframe, min_length= min_length, method = method)
            # traffic_within_day_intpol, peak_list = derivative_based_segmentation(traffic_within_day_intpol, column='speed', slope_threshold=15, window=60, min_gap=10, speed_upper=55, aggregate_timeframe=aggregate_timeframe, min_length= min_length, method = method)
        elif method == 'RDP':
            traffic_within_day_intpol, peak_list = rdp_segmentation_peak(traffic_within_day_intpol, column='speed', epsilon=1.5, speed_upper=50, aggregate_timeframe=aggregate_timeframe, date=date, VDS_num=VDS_num, min_length= min_length, method = method)
        elif method == 'joon':
            traffic_within_day_intpol, peak_list = speedbasedpeak(traffic_within_day_intpol, column='speed', speed_upper = 50, min_minutes = min_length, max_outliers = 2, aggregate_timeframe = aggregate_timeframe, method = method)
            # traffic_within_day_intpol, peak_list = speedbasedpeak(traffic_within_day_intpol, column='speed', speed_upper = 50, min_minutes = min_length, max_outliers = 3, aggregate_timeframe = aggregate_timeframe, method = method)

        set_peak_period.loc[len(set_peak_period)] = [date, str(peak_list)]
    
    traffic_divisions = traffic_within_day_intpol.groupby('division')
    
    for traffic_division in traffic_divisions:

        # step2: Daily traffic pattern calculation
        flow_collection = traffic_division[1][[f'flow_{i}' for i in lane_num]].values.flatten().tolist()
        speed_collection = traffic_division[1][[f'speed_{i}' for i in lane_num]].values.flatten().tolist()
        
        # Ensure both collections are NumPy arrays
        flow_collection = np.array(flow_collection)
        speed_collection = np.array(speed_collection)
    
        flow_collection_nan = flow_collection[~np.isnan(speed_collection)]
        speed_collection_nan = speed_collection[~np.isnan(speed_collection)]
    
        with np.errstate(divide='ignore', invalid='ignore'):
            multiply = np.multiply(flow_collection_nan, 1/speed_collection_nan)
        # Sum the non-NaN results directly  (속도 0일 때 어떻게 할 지 논의해보기!!)
        sum_flow = flow_collection_nan.sum()
        sum_product = np.nansum(multiply)
           
        daily_traveltimes = sum_product / sum_flow * 60
        
        if temporal_scale in ['speedbasedpeak', 'peak']:
            if traffic_division[0] != 0:
                # daily_flow = flow_collection.sum()*(interval_size/60) /len(lane_num) / (heart_peakperiod/60)
                daily_totaldemand = flow_collection.sum()*(aggregate_timeframe/60) /len(lane_num)
            else:
                daily_totaldemand = flow_collection.mean()
        else:
            daily_totaldemand = flow_collection.mean()
    
        c_daily_traveltimes.append(daily_traveltimes)
        c_totaldemand.append(daily_totaldemand)
        c_date.append(date)
        c_period.append(traffic_division[1]['division'].unique()[0])
        c_dayofweek.append(Day)


# In[967]:


print(set_peak_period)
set_peak_period.to_csv(f"./set_peak_period_{VDS_num}_{aggregate_timeframe}_{method}.csv")


# In[968]:


c_daily_traffic = pd.DataFrame({'traveltimes': c_daily_traveltimes, 'totaldemand': c_totaldemand, 'date': c_date, 'dayofweek': c_dayofweek, 'division': c_period})

c_daily_traffic['year'] = c_daily_traffic['date'].astype(int)//10000 + 2000
c_daily_traffic.to_csv(f"./c_daily_traffic_{VDS_num}_{temporal_scale}_{aggregate_timeframe}_{method}.csv")


# In[969]:


temporal_scale = 'speedbasedpeak'
file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/c_daily_traffic_{VDS_num}_{temporal_scale}_{aggregate_timeframe}_{method}.csv"
c_daily_traffic = pd.read_csv(file_path)

# total demand from peak period to the average flow depending on the size of 'heart of peak period'
# heart of peak period(W): minutes
heart_peakperiod = 40

c_daily_traffic.loc[(c_daily_traffic['division'] == 0),'flow'] = c_daily_traffic.loc[(c_daily_traffic['division'] == 0),'totaldemand']
c_daily_traffic.loc[(c_daily_traffic['division'] != 0),'flow'] = c_daily_traffic.loc[(c_daily_traffic['division'] != 0),'totaldemand'] / (heart_peakperiod/60)

c_daily_traffic.to_csv(f"./c_daily_traffic_{VDS_num}_{temporal_scale}_{aggregate_timeframe}_{method}.csv")


# In[970]:


print(c_daily_traffic.head())


# ### BPR patterns

# In[972]:


## "entireday", "peak" "hour" "speedbasedpeak"
# VDS_num = 1203506
VDS_num = '1205583'
temporal_scale = "speedbasedpeak"
# aggregate_timeframe = 5
# joon, pelt, RDP, derivative
# method = 'derivative'
file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/c_daily_traffic_{VDS_num}_{temporal_scale}_{aggregate_timeframe}_{method}.csv"
label_criterion = 'dayofweek'


year_notinclude = []
dayofweek_notinclude = []
month_notinclude = []

# Step 1: data read
c_daily_traffic = pd.read_csv(file_path)
c_daily_traffic['date'] = c_daily_traffic['date'].astype(str)
c_daily_traffic['month'] = c_daily_traffic['date'].str.slice(0, 4)

print(len(c_daily_traffic))

# Step 2: data filtering
c_daily_traffic = c_daily_traffic[~c_daily_traffic['year'].isin(year_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['dayofweek'].isin(dayofweek_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['month'].isin(month_notinclude)]


# In[973]:


## write down not inclue values
dayofweek_notinclude = []
year_notinclude = []
month_notinclude = []

c_daily_traffic_day = c_daily_traffic.groupby(label_criterion)

# Step 3: Create a scatter plot for 'flow' vs 'time'
fig, ax = plt.subplots(1, 1, figsize=(9, 6))

for name, group in c_daily_traffic_day:
    ax.plot(group["flow"], group["traveltimes"], marker="o", linestyle="", label=f"{name}")
    
# ax.scatter(c_daily_traffic["flow"], c_daily_traffic["traveltimes"])
plt.legend()
ax.set_title(f'Demand and Travel Times at VDS {VDS_num} ({aggregate_timeframe}min, {method} method)')
ax.set_ylabel('Traveling Time (min/mile)', fontsize=13)
ax.set_xlabel('Flow Rates(vphpl)', fontsize=13)
ax.grid(True)
ax.set_xlim(0, 3500)
ax.set_ylim(0.5,6)
# ax.legend(title=f'{label_criterion}')

# Save and Display the plot
plt.savefig(f'./02 fig/12 Daily/Daily_flow_vs_time_{temporal_scale}_{VDS_num})_labeled by_{label_criterion}_without_{year_notinclude}{dayofweek_notinclude}_{aggregate_timeframe}_{method}.png')
plt.show()


# In[676]:


temporal_scale = 'speedbasedpeak'
file_path = f"./c_daily_traffic_{VDS_num}_{temporal_scale}_{aggregate_timeframe}_{method}.csv"
c_daily_traffic = pd.read_csv(file_path)

# c_daily_traffic[(c_daily_traffic['date']== 111012)].sort_values(by='date', ascending=True)
c_daily_traffic[(c_daily_traffic['flow']>2500) ].sort_values(by='date', ascending=True)
# c_daily_traffic[(c_daily_traffic['flow']>1200) & (c_daily_traffic['traveltimes']<2)].sort_values(by='date', ascending=True)
# c_daily_traffic[(c_daily_traffic['traveltimes']<1.0) & (c_daily_traffic['flow']>1100) ].sort_values(by='date', ascending=True)


# ### BPR fitting

# - Capacity ($c$): Chosen as the upper limit of the free-flow speed segment
#     - While the congested segment may vary depending on the size of $W$, the free-flow segment remains consistent.
#     - The end of the free-flow segment can be interpreted as the onset of congestion.
#         - VDS_num=1205583: c= 900
#         - VDS_num=1203506: c = 1200    
# - Fitting result (t=t_0 * (1 + a * (x / c) ** b))
#     - VDS_num=1205583: t=t_0 * (1 + 0.86 * (x / 900) ** 1.9), R^2 = 0.832
#     - VDS_num=1205583: t=t_0 * (1 + 0.54 * (x / 1200) ** 1.13), R^2 = 0.573
# - A detailed discussion is needed on how to define capacity and interpret the associated parameters.

# In[513]:


from scipy.optimize import curve_fit
import numpy as np
import random

# Step 2. Flatten all x and y values into single arrays for fitting
x_all = c_daily_traffic["flow"].values
y_all = c_daily_traffic["traveltimes"].values

capacity_part_x = x_all[x_all>1250]
capacity_part_y = y_all[x_all>1250]

random_seed = random.choices(range(len(capacity_part_x)), k=len(x_all) - 2 * len(capacity_part_x))

x_all_random = capacity_part_x[random_seed]
y_all_random = capacity_part_y[random_seed]

x_all_extra = np.concatenate((x_all, x_all_random))
y_all_extra = np.concatenate((y_all, y_all_random))


# In[517]:


# Step 3. Fit the function to the data
# Step 1. Define the function to fit

c_fixed = 1200 # fixed value
label_criterion = 'dayofweek'

c_daily_traffic_day = c_daily_traffic.groupby(label_criterion)

def model_func(x, a, b, c):
    t_0 = 6 / 7
    return t_0 * (1 + a * (x / c) ** b)

# Fix c = 1000 using a lambda
model_fixed_c = lambda x, a, b: model_func(x, a, b, c=c_fixed)

params, _ = curve_fit(model_fixed_c, x_all, y_all, p0=[1, 1], maxfev=10000)
a_fit, b_fit = params

# Step 4. Generate smooth x-values and compute corresponding y-values
x_fit = np.linspace(0, 3000, 500)
y_fit = model_func(x_fit, a_fit, b_fit, c_fixed)

# Predict y-values using the fitted model
y_pred = model_func(x_all, a_fit, b_fit, c_fixed)

# Calculate R-squared
y_true = y_all
ss_res = np.sum((y_true - y_pred) ** 2)
ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
r_squared = 1 - (ss_res / ss_tot)


# Step 5. Plot everything as before
fig, ax = plt.subplots(1, 1, figsize=(9, 6))

for name, group in c_daily_traffic_day:
    ax.plot(group["flow"], group["traveltimes"], marker="o", linestyle="", label=f"{name}")

# Plot fitted curve
ax.plot(
    x_fit, y_fit, color="black", linewidth=2,
    label=f"Fitted: y = t₀·(1 + {a_fit:.2f}·(x/{c_fixed:.0f})^{b_fit:.2f}), R² = {r_squared:.3f}")

# Labels and formatting
ax.set_ylabel('Traveling Time (min/mile)', fontsize=13)
ax.set_xlabel('Flow Rates (vphpl)', fontsize=13)
ax.grid(True)
ax.set_xlim(0, 3000)
ax.set_ylim(0, 6)
plt.legend()
plt.savefig(f'./02 fig/12 Daily/Daily_flow_vs_time_{temporal_scale}_{VDS_num})_labeled by_{label_criterion}_without_{year_notinclude}{dayofweek_notinclude}.png')
plt.show()


# ## Case 2) Daily traffic

# - Entire day
#     - Does not explicitly fit with the F.D. There are many values with the same daily volumes
#     - Why? Daily volume alone is not enough to capture traffic patterns, especially how demand is concentrated during peak periods.
#         - Example: Two days may have the same daily volume but different demand distributions throughout the day.
#         - <img src="./02_1_presentation_fig/Daily_BPR_concept.png" width=50%>
#     - Using daily demand size doesn’t directly correspond to average travel times.
#         - Because demand fluctuates over time, the total volume alone does not provide explicit insight into observed travel times.
#     - Identifying near-stationary states may help reveal patterns, but I doubt this process can shape the BPR function.
#         - Different sets of week-to-week stationary states can have the same daily volumes despite having different traffic patterns.
#         - However, if we focus only on the peak period, the volume more closely aligns with travel times, since the peak period is not fixed but varies with the severity of congestion.
#     - 교수님 논문에서 전체 day에서는 w 어떻게 정의했는지 확인해보기!!
#     - 같은 demand라도 다른 값을 가져도 되는게, 그렇기 때문에 BPR을 다른 상황마다 parameter estimation하는게 아닌가?? 

# In[515]:


## "entireday", "peak" "hour" "speedbasedpeak"
VDS_num = 1203506
# VDS_num = '1205583'
temporal_scale = "entireday"
file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/BPR/c_daily_traffic_{VDS_num}_{temporal_scale}.csv"

c_daily_traffic = pd.read_csv(file_path)

print(c_daily_traffic[(c_daily_traffic['flow']<25240/24) & (c_daily_traffic['flow']>25000/24)].sort_values(by='date', ascending=True))


# In[1144]:


## "entireday", "peak" "hour" "speedbasedpeak"
VDS_num = 1203506
# VDS_num = '1205583'
temporal_scale = "entireday"
file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/c_daily_traffic_{VDS_num}_{temporal_scale}.csv"
label_criterion = 'dayofweek'


## write down not inclue values
dayofweek_notinclude = []
year_notinclude = []
month_notinclude = []


# Step 1: data read
c_daily_traffic = pd.read_csv(file_path)
c_daily_traffic['date'] = c_daily_traffic['date'].astype(str)
c_daily_traffic['month'] = c_daily_traffic['date'].str.slice(0, 4)

print(len(c_daily_traffic))

# Step 2: data filtering
c_daily_traffic = c_daily_traffic[~c_daily_traffic['year'].isin(year_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['dayofweek'].isin(dayofweek_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['month'].isin(month_notinclude)]


c_daily_traffic_day = c_daily_traffic.groupby(label_criterion)

# Step 3: Create a scatter plot for 'flow' vs 'time'
fig, ax = plt.subplots(1, 1, figsize=(9, 6))

for name, group in c_daily_traffic_day:
    ax.plot(group["flow"]*24, group["traveltimes"], marker="o", linestyle="", label=f"{name}")
    
# ax.scatter(c_daily_traffic["flow"], c_daily_traffic["traveltimes"])
plt.legend()
# ax.set_title(f'Relationship between Daily Flow and Traveling Time at {lane_range} during {dataset_days}')
ax.set_ylabel('Traveling Time (min/mile)', fontsize=13)
ax.set_xlabel('Daily Volume (vpdpl)', fontsize=13)
ax.grid(True)
ax.set_xlim(10000, 40000)
ax.set_ylim(0.75,2)
# ax.legend(title=f'{label_criterion}')

# Save and Display the plot
plt.savefig(f'./02 fig/12 Daily/Daily_flow_vs_time_{temporal_scale}_{VDS_num})_labeled by_{label_criterion}_without_{year_notinclude}{dayofweek_notinclude}.png')
plt.show()


# ## Case 3) Fixed Time-period
# - On 6/2, we discussed testing fixed-time peak periods:
#     - Morning peak: 4:00–10:00
#     - Afternoon peak: 16:00–22:00
#     - During these peak periods, apply a fixed __waiting time of 3 hours__.
# - __For VDS: 1205306__, the original afternoon peak was set to 16:00–22:00. However, traffic often starts peaking from 15:00, resulting in many __non–free-flow travel times during low demand periods__. This could be improved by redefining the peak periods.
# - <img src='./02_1_presentation_fig/fixedtime_peak_16-22.png' width=80%>
# - Still, even with adjusted peak times, the morning and afternoon peaks diverge: the morning peak has __lower hourly demand__, while the __afternoon peak sees higher demand__.
# - this pattern roughly follow an F.D. shape, but they may shift toward a BPR-like shape if we filter for stationary states.
# - <img src='./02_1_presentation_fig/fixedtime_peak_14-20.png' width=80%>
# - __For VDS: 1205583__, traffic patterns appear more consistent and show a clearer trend, but resemble more of a fundamental diagram (F.D.) shape.
# - __this pattern shows somewhat clear FD shape, not sure how to interpret this result__
# - <img src='./02_1_presentation_fig/Daily_flow_vs_time_peak_1205583.png' width=60%>
# 
# 

# <div class="alert alert-danger">
# 
# <6/17/2025>
# - Unlike speed-based peak-period, It did not show the BPR shape.
#     - why?) Because the congestion period alone doesn’t capture distributional information—like the full-day volume—which is critical for explaining travel times.
#     - fixed와 unfixed가 근본적인 차이같어. 이와 관련한 이유를 제시해야할 것 같은데?

# In[1152]:


## "entireday", "peak" "hour" "speedbasedpeak"
# VDS_num = 1203506
VDS_num = '1205583'
temporal_scale = "peak"
file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/c_daily_traffic_{VDS_num}_{temporal_scale}_heart_peakperiod.csv"
label_criterion = 'dayofweek'


## write down not inclue values
dayofweek_notinclude = []
year_notinclude = []
month_notinclude = []


# Step 1: data read
c_daily_traffic = pd.read_csv(file_path)
c_daily_traffic['date'] = c_daily_traffic['date'].astype(str)
c_daily_traffic['month'] = c_daily_traffic['date'].str.slice(0, 4)

print(len(c_daily_traffic))
print(c_daily_traffic.head())

# Step 2: data filtering
c_daily_traffic = c_daily_traffic[~c_daily_traffic['year'].isin(year_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['dayofweek'].isin(dayofweek_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['month'].isin(month_notinclude)]


c_daily_traffic_day = c_daily_traffic.groupby(label_criterion)

# Step 3: Create a scatter plot for 'flow' vs 'time'
fig, ax = plt.subplots(1, 1, figsize=(9, 6))

for name, group in c_daily_traffic_day:
    ax.plot(group["flow"], group["traveltimes"], marker="o", linestyle="", label=f"{name}")
    
# ax.scatter(c_daily_traffic["flow"], c_daily_traffic["traveltimes"])
plt.legend()
# ax.set_title(f'Relationship between Daily Flow and Traveling Time at {lane_range} during {dataset_days}')
ax.set_ylabel('Traveling Time (min/mile)', fontsize=13)
ax.set_xlabel('Hourly Demand (vphpl)', fontsize=13)
ax.grid(True)
# ax.set_xlim(0, 2500)
ax.set_ylim(0.5,4)
ax.set_title(f"VDS: {VDS_num}_Fixedpeak_perid_{afternoon_peak}",fontsize=18)
# ax.legend(title=f'{label_criterion}')

# Save and Display the plot
# plt.savefig(f'./02 fig/12 Daily/Daily_flow_vs_time_{temporal_scale}_{VDS_num})_labeled by_{label_criterion}_without_{year_notinclude}{dayofweek_notinclude}.png')
plt.show()


# <div class='alert alert-danger'>
# 
# - __All-day case__
#     - The current outcome doesn't exhibit a clear pattern and doesn't appear to resemble the shape of a BPR function. 
# To grasp the overall shape of the results, additional data with a different rang is required
# - __Plan to analysis__
#     - ①  The datasets from August 2019, September 2019, October 2023, and November 2023 exhibit minimal variance
#          - The Average Annual Daily Traffic (AADT) from 2019 to 2023 remains stable
#         - It is essential to include datasets from a different time frame, specifically the 2014-2015 dataset: Nope. This is because of malfunctions
#         - Comparatively, the demand during 2014-2015 was significantly higher than that of 2019-2023
#     - ② The rawdata with different timeframe(15min, 1hour) needs to be applied.
#     
# - <center> <img src="https://github.com/jooneui/fig_collection/blob/main/AADT_2013-2024.png?raw=true", width = 40%> </center>
# </div>

# - <img src='./proj2_Qinlong_2018.png' width=50%>
# - Figure: Yan et al. (2018)

# In[2]:


def detect_twopeak(time_frame_peak, time_frame, rawdata, lane_num, gfactor, height, width):
    
    num_frame = time_frame_peak/time_frame
    traffic_day = pd.DataFrame({'speed':[],'time':[],'flow':[],'density':[]})
    
    # Step 0: uploading data and unifying rawdata's format
    plot_date = []

    # Step 1: variable setting(time_frame: min, lane_num: range of lanes for analysis)
    for hour in range(0, 24):
        for minute in range(0, int(60/time_frame_peak)):
            start_time = hour*100 + minute*time_frame_peak
            end_time = start_time + time_frame_peak
            # Filter rawdata for the current time slot
            mask = (rawdata['time_filter'] >= start_time) & (rawdata['time_filter'] < end_time)
            rawdata_filter = rawdata[mask]
    
            if not rawdata_filter.empty:
                # Compute average traffic state and append to traffic_day
                avg_speed, avg_time, avg_flow, avg_density = avg_traffic_state(rawdata_filter, time_frame, lane_num, gfactor)
                traffic_day.loc[len(traffic_day)] = [avg_speed, avg_time, avg_flow, avg_density]
    
    peaks, _ = find_peaks(traffic_day['flow'], height=height, width=width)  # Adjust `height` and `prominence` as needed
    # print(peaks)
    return len(peaks)


# In[ ]:


# Detect if the data has two peaks
two_peak_dates = []

for i, file_name in enumerate(file_list):
    # 15min
    time_frame_peak = 30
    num_frame = time_frame_peak/raw_timeframe
    
    traffic_day = pd.DataFrame({'speed':[],'time':[],'flow':[],'density':[]})
    height = 1500; distance = 8
    # Step 0: uploading data and unifying rawdata's format
    date = file_name[-11:]
    rawdata = rawdata_setting(directory,file_name)
    gfactor = pd.read_excel(f'{path}/gfactor/gfactor_{date}')
    
    peak_len = detect_twopeak(time_frame_peak, raw_timeframe, rawdata, lane_num, gfactor, height, distance)
    if peak_len >= 2:
        two_peak_dates.append(file_name)


# In[6]:


# Check the relationship between flow and time for the entire period

# Step 0: Create an empty DataFrame to store daily traffic data and set basic variables
# traffic_day = pd.DataFrame({'speed': [], 'time': [], 'flow': [], 'density': [],'year':[],'day':[]})

# option: 'two-peak_days', 'entire days', ;filterd days"
dataset_days = 'filtered days'
# label_criterion: 'year', 'day'
label_criterion = 'day'
# lane range: 'all lanes' '1,2 lanes'
lane_range = 'all lanes'
year_range = ['2011','2014','2015','2024']

if (dataset_days == 'entire days'):
    Dataset = file_list
elif(dataset_days == 'two-peak days'):
    Dataset = two_peak_dates
else:
    Dataset = filtered_dates
    
for i, file_name in enumerate(Dataset):
    # Step 1: Load data for each day and process it
    # Load raw data from csv file
    rawdata = rawdata_setting(directory,file_name,total_lane_raw)
    date = file_name[-11:]
    year = f'20{date[0:2]}'
    Day_list = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    Day = Day_list[int(rawdata.loc[0,'time'].weekday())]
    
#     gfactor = pd.read_excel(f'{path}/gfactor/gfactor_{date}')

#     # Step 2: Calculate the average traffic state for the day
#     avg_speed, avg_time, avg_flow, avg_density = avg_traffic_state(rawdata, raw_timeframe, lane_num, gfactor)

#     # Append daily traffic state to the DataFrame
#     traffic_day.loc[i] = [avg_speed, avg_time, avg_flow, avg_density, year, Day]

# with open(f'traffic_day_{dataset_days}_{lane_range}.p', 'wb') as file:  
#     pickle.dump(traffic_day, file)

with open(f'traffic_day_{dataset_days}_{lane_range}.p', 'rb') as file:
    traffic_day = pickle.load(file)
    
traffic_day = traffic_day.iloc[np.where(traffic_day['year'].isin(year_range))]
print(traffic_day)   

traffic_day = traffic_day.iloc[np.where(traffic_day['day'].isin(['Sat','Sun','Fri']))]

# Step 3: Create a scatter plot for 'flow' vs 'time'
fig, ax = plt.subplots(1, 1, figsize=(9, 6))

traffic_day.loc[traffic_day['day'].isin(['Tue','Wed','Thu']), 'day'] = 'Tue~Thu'
traffic_day = traffic_day.groupby(label_criterion)

for name, group in traffic_day:
    ax.plot(group["flow"], group["time"], marker="o", linestyle="", label=f"{name}")
    
plt.legend()

ax.set_title(f'Relationship between Daily Flow and Traveling Time at {lane_range} during {dataset_days}')
ax.set_ylabel('Traveling Time (min/mile)', fontsize=13)
ax.set_xlabel('Flow Rates(vphpl)', fontsize=13)
ax.grid(True)
ax.set_xlim([600,1800])
ax.set_ylim([0,2])
ax.legend(title=f'{label_criterion}')

# Save and Display the plot
# plt.savefig(f'./02 fig/12 Daily/Daily_flow_vs_time_{lane_range}_{dataset_days}({year_range})_labeled by_{label_criterion}.png')
plt.show()


# In[ ]:


x = [0, 1.6, 1.7, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 5, 5, 6, 7]
# peaks, properties = find_peaks(x, distance=5, plateau_size=2)

peaks, properties = find_peaks(x,height=2,distance=1)
# , width=5
print(peaks)
print(properties)

