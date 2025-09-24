# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.7
#   kernelspec:
#     display_name: Python [conda env:base] *
#     language: python
#     name: conda-base-py
# ---

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

# +
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def BPR_function(t_0,C,alpha,beta,N):
    t =  t_0 * (1+alpha*(N/C)**beta)
    return t

def Triangular_FD_congested(q,k_j,w):
    t = (k_j/q-1/w)*60
    return t


# +
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
# -

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
# <img src="./01_BPR/02_1_presentation_fig/VDF_review_demanddef.png" width=70%>
# - [The link to the Wu et al. (2022)](https://www.notion.so/2020-Xin-Burce-Wu-Characterization-and-calibration-of-volume-to-capacity-ratio-in-volume-delay-fun-16618fce4e52801b9e7fd9e9ec7b01b7)

# # Methodology
# ## Flow chart
# - <span style="color:red"> Q) For the raw data, I use $q$ to represent flow rates and $\bar{v}$ to denote the average velocity of vehicles. I would like to discuss its appropriateness. </span>
# - <span style="color:red"> I need to add steps for the Peak/Non-peak cases </span>
#
# <center> <img src="https://github.com/jooneui/fig_collection/blob/main/Fig1.png?raw=true", width = "70%"> </center>

# ## Data cleaning

# ### Speed threshold
# - In 5-min aggregated data, there are some avg speed over 80mph. I set this value as the threshold.
# - $$v(t) = \begin{cases}
# v^{\text{freeflow}}_{\max}, & \text{if } v(t) > v^{\text{freeflow}}_{\max} \\
# v(t), & \text{otherwise}
# \end{cases}$$
# - Why not interpolating instead of putting threshold?
#     - I observed that many over–free-flow speeds occur right before congestion builds up. If we interpolate those values, the resulting speeds fall between free-flow and congested levels, which may classify them as part of the peak period.
#     - However, when I checked the data patterns, the corresponding density and flow still reflected free-flow conditions.
#     - So instead of interpolating, I think it’s more logical to cap the speeds at a realistic free-flow maximum to preserve the free-flow state and improve the accuracy of peak-period detection
#     -  <img src='./01_BPR/02_1_presentation_fig/overfreeflowspeed.png' width=80%>    

# ### Interpolation
# - After applying the speed threshold, I perform interpolation using 5-minute interval data.
# - The original data comes in 30-second intervals, which tends to be highly variable due to the fine temporal scale—so interpolating based on those values could be problematic.
# - Instead, I chose to aggregate the data into 5-minute intervals to obtain more representative values.
# - If any 5-minute interval is missing, I apply interpolation to fill it in.

# # Data Description

# ## SR-91
# - Lane information(ex. HOT)
#     - NO HOT, but only HOV.
#     - VDS does not cover the HOV lane, but only for general-purpose lanes(4 out of 5 lanes).
#     - HOT in SR 91: SR 91 with the SR 55 Freeway (Costa Mesa Freeway) in Anaheim to its junction with I-15 in Corona(18 miles)
#     - Period: total __307__
#         - Jan. ~ Apr., Aug.~Oct. 2011,
#         - Aug., Sep., . 2012
#         - Sep., Oct., 2023
#         - Jan., 2024
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
# - Period: total __245__
#     - Jan. ~ Oct. 2011
# - <img src='./01_BPR/02_1_presentation_fig/I-5_Buenapark.png' width=80%>
# - Need to check 1205612
# - <img src='./01_BPR/02_1_presentation_fig/VDS1205583.png' width=90%>

# # Speed-Based Detection of Peak Periods and Estimation of BPR Functions

# ## Methodology

# ### Ramer–Douglas–Peucker (RDP) Algorithm

# + [markdown] editable=true slideshow={"slide_type": "subslide"}
# - **Objective:**  
#     - To simplify a curve (a sequence of connected points) by reducing the number of points while preserving the overall shape within a specified tolerance.
#
# - **Concept**
#     - The RDP algorithm identifies and retains **key points (corners or bends)** that are critical to the shape of the curve.
#     - Intermediate points that lie within a user-defined distance (**epsilon, ε**) from a straight-line approximation are discarded.

# + [markdown] editable=true slideshow={"slide_type": "skip"}
# #### RDP threshold value reference
# - Original RDP studies are was for **image processing (Ramer)** and **geography contour line(Douglas and Peuker)**
#     - Ramer (1972): approximate the curves extracted from images
#     - Douglas and Peuker (1973): digitizing geographic features (coastlines, contours)
#     - so, x-axis and y-axis have the same unit, perpendicular distance has a same unit.
#     - And their purpose was to keep the geometry/visual shape with the minmum number of points to decrease compuatational time/space.

# + [markdown] editable=true slideshow={"slide_type": "skip"}
# ##### Threshold values
# - Their approach for the threshold was a bit different from our study
#     - Their focus is not on detecting some specific characteristic, but on finding the values that can maintain the general shape with the small number of points. Because of that, most of the studies that they applies is based on the heuristic.
#     - Both studies suggest the limitation that the tolerance must be chosen manually.
#     - Ramar (1972): sensitivity analysis based on the tolerance from 1~5 gridpoints(pixel) in the image
#     - Douglas and Peuker (1973): mention the tolerance should be application-dependent
#         - map scale, positional accuracy of GPS (larger than the accuracy error to eliminate the artifacts)   
# - Many other studies' applications are mostly about the RDP visual image(maps, digitized medical images, object contours), so they used the perpendicular distance. 

# + [markdown] editable=true slideshow={"slide_type": "skip"}
# - However, in our study, we have a temporal constraint
#     - In our study, we want to segment the curve with the lines that accurate represent the curve, but the accuracy means time-dependent, not just geometric shape.
#     - We want to have an accurate values for each time between the segment and actual pattern.
#     - The vertical deviation directly measures "how wrong" the estimated travel time would be.

# + [markdown] editable=true slideshow={"slide_type": "skip"}
# - Peque et al. (2019). use the vertical distance.
#     - Travel time curve (travel time vs. time of day) as a polyline
#     - Draw linear interpolation and calculate the vertical distance from each point.
#     - The vertical distance (y-axis difference) is the natural error measure.
#         - It directly means: “how wrong is my predicted travel time at this specific time?”
#         - This matches their application: keeping travel times accurate at every time step.
# -

# #### RDP threshold in this study

# ### PELT method

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

# ### Segmentation setting

#
# <img src='./01_BPR/02_1_presentation_fig/changepoint_logic.png' width=70%>   

# #### RDP & PELT
# - **Start:** Point where the distance slope changes — congestion start at $\tau_m$.  
# - **End:** The cumulative profile is discrete, adding the next speed value at each step.  
#     - If the point after $\tau_{m+1}$ ($\tau_{m+1} + 1$) is at free-flow speed, the slope from $\tau_{m+1}$ reflects free-flow conditions.
#     - The congestion end changepoint: $\tau_{m+1}+1$

# ## Peak-period detection Result

# - Case1) Speed threshold-based
#     - peak period: A period if the speed stays below the _'speed_upper_bound'_ for at least _'min_minutes'_, allowing up to _'max_outliers'_:
#         -  speed_upper_bound=40mph, min_minutes=90min, max_outliers = 7 
# - Case2) PELT
# - Case3) RDQ
# - Case4) Derivative-based: The concept is similar to PELT, so not deploy it.

# - I explained RDP logic, and we determined to use constant parameters.
# - Compare the how congestion boundaries are similar between PELT vs RDP

# + [markdown] editable=true slideshow={"slide_type": "subslide"}
# - **Methodology**
#     - **Step1) Start with the Full Curve**: Connect the **first and last points** with a straight line.
#     - **Step2) Find the Furthest Point**: Calculate the **vertical distance** of all intermediate points to this line.
#        - Identify the point with the **maximum distance**.
#     - **Step3) Check the Distance**: If the maximum distance is **greater than the tolerance ε**, retain this point and **recursively apply RDP** to the two sub-curves:
#          - From the start to this point
#          - From this point to the end
#          - If the maximum distance is **less than or equal to ε**, remove all intermediate points between the start and end.
#      - **Step4) Repeat Until Simplified**: Continue until all points meet the distance condition.
#
# <img src="./01_BPR/02_1_presentation_fig/RDP_process.png" width=90%>
# -

# ### Parameter setting
# - RDP: 12miles
# - PELT: 2500 $(mph)^2$

# ### RDP vs PELT

# - SR-91: total __307__ days
#     - Jan. ~ Apr., Aug.~Oct. 2011,
#     - Aug., Sep., . 2012
#     - Sep., Oct., 2023
#     - Jan., 2024
# - I-5: total __245__ days
#     - Jan. ~ Oct. 2011 

# | Case | Description                          | SR-91 (VDS: 1203506)            |          | I-5 (VDS: 1205583)                |          |
# |------|--------------------------------------|---------------------|----------|---------------------|----------|
# |      |                                      | # of periods        | %        | # of periods        | %        |
# | 1    | Start and duration match exactly      | 221                | 55.0%    | 131                   | 58.7%     |
# | 2    | Start and duration differ by ≤ 30 min | 151                 | 37.6%    | 80             | 35.9%    |
# | 3    | All other cases                       | 30                | 7.5%     | 12                   | 5.4%     |
#

# - Case1: (Exact match) The two methods either detect a peak with the same start time and duration, or correctly identify days without congestion.
#     - VDS1203506: 102 (correctly identiy days without congestion)
#     - VDS1205583: 117(correctly identiy days without congestion)
# - Case 2 (Small differences, within thresholds): The two peaks don’t match exactly, but:
#     - The start times differ by ≤ 30 minutes, and
#     - The durations differ by ≤ 30 minutes.
# - Case 3 (Other / mismatched):
#     - Start time differs by more than 30 minutes, or
#     - Duration differs by more than 30 minutes, or
#     - One method detects a congested period, but the other method does not find a corresponding peak.

# ### Manual check based on random sampling

# - Many samples (days) are taken up by uncongested days.
# - Comparing PELT and RDP, RDP tends to cover a slightly wider range.
#     - Personally, I think RDP represents the peak more clearly and captures the start and end of congestion more accurately.
#     - With a smaller m in PELT, the section is captured to some extent.
#     - However, lowering m also makes PELT pick up very small fluctuations, which keeps the detected values high.
#     - Because RDP uses cumulative speed, it’s less sensitive to short fluctuations and produces more stable results overall.

# | Case | Description                          | SR-91 (VDS: 1203506)            |          | I-5 (VDS: 1205583)                |          |
# |------|--------------------------------------|---------------------|----------|---------------------|----------|
# |      |                                      | # of periods        | %        | # of periods        | %        |
# | 1a    | Both as an uncongested day      | 8                | 19.5%    | 18                  | 61.3%     |
# | 1b    | Start and duration match exactly      | 12                | 29.3%    | 3                   | 9.7%     |
# | 2    | Start and duration differ by ≤ 30 min | 15                 | 36.6%    | 7             | 19.4%    |
# | 3    | All other cases                       | 6                | 14.6%     | 2                  | 9.7%     |

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

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### Previous discussion but not valid anymore

# + [markdown] editable=true jp-MarkdownHeadingCollapsed=true slideshow={"slide_type": "subslide"}
# <div class="alert alert-danger">
# 25/09/02
#
# __RDP threshold in this study(2025/9/2)__
#
# - $\epsilon = \frac{\theta}{\bar{v}}$, where $\theta$ is costant value
#     - $\theta = 800 \text{mph}\cdot\text{miles}$
#     - normally, $\bar{v}=63 \sim 68mph$, then $\epsilon=11.76 \sim 12.7 miles$
# - Why is it inversely proportional? High average speeds mean shorter congestion periods or less severe congestion, so when speeds are higher, the threshold should be lower to detect those relatively small changes.

# + [markdown] editable=true slideshow={"slide_type": ""}
# <div class="alert alert-danger">
# 25/09/02
#
# RDP result
# - The logic is much simpler than before.
# - It generally treats one uncongested period as a single segment and detects the congested periods well.
# - Tradeoff: keeping uncongested periods whole vs detecting short-term congestion.
#     - Sometimes, uncongested periods accumulate small deviations over long durations, leading to larger vertical distances than congested periods (e.g., VDS123506: 12/8/21, 11/3/27 vs 11/3/16).
#     - We prioritize detecting short-term congestion.
#         - As a result, an off-peak period may sometimes be split into two segments. However, both segments remain sufficiently long, since splits only occur after small deviations accumulate over time.
#         - These splits are not considered congestioned period.
# - Detecting one off-peak is like having detecting stationary states. However
# -

# <div class="alert alert-danger">
#
# 25/8/19
#
# **RDP threshold in this study**
# - <img src='./01_BPR/02_1_presentation_fig/RDP_vertical_dist.png' width=40%>
# - $d_{max} = (v_f - \bar{v}) \cdot t_m $, where $v_f$ = free-flow speed speed (mph), $\bar{v}$ = average daily speed (mph), and $t_m$ = morning uncongested period length (hr).
# - The condition: $d_{max} > \epsilon$, where $\epsilon$ = tolerance (miles)
# - The way implemented in this paper
#     - $t_m = \begin{cases}
# 4, & \text{if congested periods exist} \\
# 24, & \text{if uncongested all day}
# \end{cases}$
#         - uncongsted all day $\equiv$ $\text{if total time with } v(t)<50 \text{ mph is less than 30 min}$
#         - 4 hrs comes from the night period (ends 20:00, so 4 hours left to 12AM)
#     - $v_f = \max \left\{ \overline{v}_{0\text{--}4\,\text{AM}},\; \overline{v}_{20\text{--}24\,\text{PM}} \right\}$
#         - $\quad \text{where } \overline{v}_{[a,b)} \text{ denotes the average speed over the time interval } [a,b). $
#     - $v_{avg} = \text{the average speed over the entire day}$
#     - $\epsilon = \begin{cases} (v_f - \bar{v}) \cdot t_m, & \text{if } v_f - \bar{v} > \delta \\
#       \delta \cdot t_m, & \text{if } v_f - \bar{v} \le \delta \end{cases}$
#         - $\delta = 2 \text{miles}$
#         - If $v_f - \bar{v}$ is too small, the distance profile is divided into too many segments, so set the margin.
#             - ex.) short-term congested period exist: 1hour avg speed: 30mph
#                 - $v_f-\bar{v}=70-(70*23+30*1)/24 = \frac{(70-30)*1}{24}=\frac{40}{24}=1.67$
#
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true
# ※ mentioned in DP about the previous study
# - Lang’s original procedure (1969)
#     - Start with:
#     - Anchor = first point.
#     - Floater = third point.
#     - Check whether the second point lies within tolerance of the line segment (Anchor–Floater).
#         - If yes → move Floater forward (to fourth point) and check again.
#         - If not → Anchor moves up to the point before the Floater.
#     - Problem: The point just before the Floater (e.g., P2 in Fig. 4) may not be the “best” representative.
#         - It could miss sharp corners because the choice is arbitrary and sequential, not geometric.
# -

# <div class="alert alert-danger">
#
# ##### Result and Discussion (2025/6/24)
#
#
# - using Pelt in both distance anc speed profiles
# </div>

# <div class="alert alert-danger">
#
# __The L2-Based PELT Algorithm May Not Detect the Exact Transition Point__
#
# __Cumulative of speed profile__
# - The changepoint is not explicitly aligned with the actual transition point. Instead, it appears either before or after the true transition. This issue persists regardless of the penalty size.
# - In the case of a penalty value of 100, the changepoint may align with the actual transition point. However, it doesn't seem to detect the peak period itself—instead, it tends to divide the time series into as many small segments as possible and then selects those segments where the average speed falls below the threshold.
# - <img src='./01_BPR/02_1_presentation_fig/PELT_speed_penalty_sensitivity analysis.png' width=150%>
#
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true
# <div class="alert alert-danger">
#
# __Cumulative of Speed-differential profile__
# - Instead of using the speed profile, I used the speed differential profile, which resulted in a more realistic segmentation.
#     - ex.) speed_profile = [v1, v2, v3, v4] → differential profile = [v2-v1, v3-v2, v4-v3]
# - <img src='./01_BPR/02_1_presentation_fig/PELT_speeddiff_penalty_sensitivity analysis.png' width=100%>
#
# </div>
# -

#
# <div class="alert alert-danger">
# __My opinion why speed is not working perfectly__
# - PELT detects the changepoint when slope changes. In the cumulative speed profile, the slope is speed.
# - Peak periods are not stationary states; within these periods, speeds gradually decrease and fluctuate significantly compared to off-peak times. From the PELT perspective, this volatility makes it difficult to precisely identify true transition points, as the signal lacks post-change stability.
# - In contrast, near-stationary state detection relies on segments of consistent values after changepoints, making the transition boundaries more distinct and reliable.
# - Reframing the speed profile into its first-order differential better aligns with this stationary-state detection logic, as it highlights periods of rapid change followed by relative stability.
# - Additionally, daily patterns in speed differentials more closely resemble individual speed trajectories during deceleration. When drivers maintain the same speeds and decrease with constant acceleration, using acceleration would be more straightforward to detect the changepoints.
# - <img src='./01_BPR/02_1_presentation_fig/PELT_driver_profile.png' width=30%>
#
# </div>

# <div class="alert alert-danger">
#
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
#
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### VDS_num: 1205583 (25/7/22)
# -

# - (25/7/22)
# - Peak-period detection
#     - Divide the peak period well, including the buildup/dissipation process.
#         - Unlike my previous approach, which directly selected the peak period, this method includes the buildup and dissipation phases based on whether speeds fall below a specified upper threshold. 
#     -  <img src='./01_BPR/02_1_presentation_fig/RDP_good.png' width=80%>

# - Disscussion
#     - Speeds have many ups-and-down (8/11/2011)
#     - Temporary uncongested periods between congested states: should we regard it as one peak-peak period or two? (8/8/2011, 7/18/2011)
#         - Our approach first detects off-peak periods as sustained near free-flow speeds over a certain duration. The remaining times are then classified as peak periods. This means that short uncongested intervals between two peak periods are also labeled as peak, since they likely reflect temporary dips in congestion rather than true off-peak conditions. I include these intervals as part of the peak period, considering that queues may build up or dissipate across peak periods, and point sensors might briefly register uncongested conditions even during sustained congestion.
#     - <img src='./01_BPR/02_1_presentation_fig/RDP_discussion.png' width=70%>

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### VDS: 1203506 (25/7/22)
# -

#
# - The trend is more versatile.
# - <img src='./01_BPR/02_1_presentation_fig/RDP_1203506_good.png' width=100%>

# - __(Discussion1)__ By using the cumulative profile, the temporary spark is not regarded as peak-period: I think that is logical.
# - <img src='./01_BPR/02_1_presentation_fig/RDP_123506_temporaryspark.png' width=60%>

# - __(Discussion2: Two-peaks in the afternoon)__ Some days have two peak periods in the afternooon.
# - <img src='./01_BPR/02_1_presentation_fig/RDP_123506_twopeaksinafternoon.png' width=60%>

# - __(Discussion3: Congestion at night)__
# - <img src='./01_BPR/02_1_presentation_fig/RDP_123506_congestionatnight.png' width=60%>

# - __(Discussion3: Congestion at night)__
#     - Controversial to define 16-20 as peak or off-peak: I can include them as off-peak, but their average is about 60mph, I think better to regard them as off-peak
# - <img src='./01_BPR/02_1_presentation_fig/RDP_123506_fluctuation.png' width=60%>

#
# **Last week discussion (8/12)**
# - Review the RDP original paper:
#     - how the threshold was implemented.
# - RDP threshold:
#     - Use vertical distance, instead of perpendicular distance
#     - not use a fixed value,
#         - dependent on the average daily speed
#         - Think about applying 75 percentile value (will check it til next meeting)
#     - Check if this will lead to one segment for one uncongested period. 

# + [markdown] editable=true slideshow={"slide_type": "subslide"}
# **8/18 discussion**
# - simplify the process of threshold setting
#     - engineering judgement,
#     - function of the average speed 

# + [markdown] jp-MarkdownHeadingCollapsed=true
# <div class="alert alert-danger">
#
# __(Methodology) Speed threshold-based__
#
# - Peak-period
#     - Define the peak period based on the travel speeds
#         - peak period: A period if the speed stays below the 'speed_upper_bound' for at least 'min_minutes', allowing up to 'max_outliers'.
#             - speed_upper_bound=40mph, min_minutes=90min, max_outliers = 7
#     - Travel demand: sum up the travel volumes during the peak period
#         - <img src='./01_BPR/02_1_presentation_fig/proj3_UE_v2.png' width=40%>
#     - Ideal arrival time window size($W$): Assume 120minutes(2hours)
#     - Average demand (vph): Travel demand (vehicles) / Ideal arrival window size (hours)
#         - __This determines the slope: Need to discuss with the criterion__
#         -  W=120 minutes(VDS 1203506), W=90 minutes (VDS 1205583) fit well
# - Non-peak period: The rest of the time within a day
#     - Average demand: the average traffic flow rate (vph)

# + [markdown] jp-MarkdownHeadingCollapsed=true
# <div class="alert alert-danger">
#
# __(Methodology) Derivative-based Line Segmentation__
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
# -

# ### (Code) Package install

# +
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


# + [markdown] jp-MarkdownHeadingCollapsed=true
# ### (Code) Peak period detection

# + tags=["code"]
def rawdata_setting(full_path,VDS_num,file_name,lane_num):
    """
    Upload raw-data and standardize the settings
    """
    
    rawdata = pd.read_excel("%s/%s" % (full_path,file_name))
    
    rawdata.columns = ['time'] + [f'flow_{i}' for i in lane_num] + [f'occ_{i}' for i in lane_num]

    rawdata['time'] = pd.to_datetime(rawdata['time'])
    # 'time_filter' is to convert the time to minutes.(ex. 02:30:30 -> 150.30min)
    rawdata['time_filter'] = rawdata['time'].dt.hour*60 + rawdata['time'].dt.minute + rawdata['time'].dt.second/60
    # rawdata['time_filter'] = rawdata['time'].dt.hour*100 + rawdata['time'].dt.minute
    rawdata['time_hour'] = rawdata['time'].dt.hour
    
    return rawdata


# + tags=["code"]
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
    # rawdata_gfactor = rawdata_gfactor.apply(lambda row: row.fillna(row.mean(skipna=True)),axis=1)
    
    ## change the policy, fill NA gfactor with the interpolatino of the immediate previous and next value in the same column
    rawdata_gfactor = rawdata_gfactor.interpolate(method='linear', axis=0)
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
    
    # Step 3: calculate indivdual 5-min aggregated per lane speed to calculate the CV_speed
    for lane in lane_num:
        flow_unit = np.array(rawdata_flow).transpose()[(lane-1)].flatten()
        rest_flow_df = rawdata_flow_df.drop(columns = [f'flow_{lane}'])
        speed_unit = np.array(rawdata_speed).transpose()[(lane-1)].flatten()
        density_unit = np.array(rawdata_density).transpose()[(lane-1)].flatten()
        
        # assign value 0 to the traffic flow when the density is equal to zero(= speed is equal to inf)
        # when density=0, speed becomes inf, making it impossible to calculate the average speeds(sum_flow/sumproduct(flow,1/speed))
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


# + tags=["code"]
""" Sometimes, the rawdata interval is too short to see the stable traffic pattern, so rawdata is aggregated to specific time interval.
This function address calculating traffic state variables in every pre-determined aggregated time interval.


* "This is not equal to the 'Research_BPR_function_Develop.ipynb', because of rawdata['time_slot'] is different: it used the median value
Interpolate_missing(traffic, config) is also changed.
"""

def aggregate_rawdata_for_peakdetection(rawdata, aggregate_timeframe, raw_timeframe, date, lane_num, gfactor,VDS_num):
    
    # Pre-compute time_slot for all data to avoid doing it in the loop
    rawdata['time_slot'] = (np.floor(rawdata['time_filter'] / aggregate_timeframe)) * aggregate_timeframe + aggregate_timeframe/2
    
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
    path_directory = f'./{working_f}/12 python file/{VDS_num}'
    os.makedirs(path_directory, exist_ok=True)

    with open(f'./{working_f}/12 python file/{VDS_num}/traffic_within_day_{date}_{aggregate_timeframe}aggmin_{lane_num}.p', 'wb') as file:
        pickle.dump(traffic_within_day, file)

    with open(f'./{working_f}/12 python file/{VDS_num}/plot_date_{date}_{aggregate_timeframe}aggmin.p', 'wb') as file:    
        pickle.dump(plot_date, file)
    
    return traffic_within_day, plot_date


# +
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

        print("zero_row_id", zero_row_id)
        
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


# +
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

    directory_path = f"./{working_f}/02 fig/15 Unit time_flowspeed_all/{VDS_num}"
    # Create the directory
    os.makedirs(directory_path, exist_ok=True)

    plt.savefig(f'{directory_path}/{date}_{lane_num}.png')
    plt.close()


# + jupyter={"source_hidden": true}
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

    directory_path = f"./{working_f}/02 fig/15 Unit time_densityspeed_all/{VDS_num}"
    # Create the directory
    os.makedirs(directory_path, exist_ok=True)

    plt.savefig(f'{directory_path}/{date}_{lane_num}.png')
    plt.close()


# -

# <img src='./01_BPR/02_1_presentation_fig/RDQ_tempscale_sensitivty.png' width=80%>

# ### (Code) Speed-based peak period

def PELT_plot(df, bkpts, date, VDS_num, aggregate_timeframe, peak_list, method, penalty):
    
    time_slot_hour = df['time_slot'] / 60

    # joon, pelt, RDP, derivative
    title_name = {'RDP':'RDP-Based Congested Periods Detection',
                  'RDP_v':'RDP_v_Based Congested Periods Detection',
                  'pelt': 'PELT-Based Congested Periods Detection',
                  'joon': 'Speed Threshold-Based Congested Periods Detection',
                 'pelt_directpeak': 'PELT-Based Directly Congested Periods Detection',}
    
    fig, ax1 = plt.subplots(figsize=(12, 5))

    date_v2 = f'{date[2:4]}/{date[4:6]}/20{date[0:2]}'
    # Left axis: Changepoints (as vertical lines)
    ax1.set_xlabel('Time (Hours)',fontsize=16)
    ax1.set_ylabel('Speed (mph)',fontsize=16, color = 'green')
    ax1.set_title(f'{title_name[method]}(VDS: {VDS_num}, Date: {date_v2})',fontsize=18)
    ax1.grid(True)
    ax1.set_xlim(0, 24+.1)
    ax1.set_xticks(np.arange(0, 25, 1))

    # Plot changepoints
    for bkpt in bkpts:
        # ax1.axvline(x=(time_slot_hour[bkpt]-(aggregate_timeframe/2)/60), color='black', linestyle='--', linewidth = 1.5,
        #             label='Changepoints' if bkpt == bkpts[0] else "")
        ax1.axvline(x=(time_slot_hour[bkpt]), color='black', linestyle='--', linewidth = 1.5,
            label='Changepoints' if bkpt == bkpts[0] else "")

    
    # Plot peak/off-peaks
    for element in peak_list:
        if element['idx'] > 0:
            s_hours, s_minutes = map(int, element['start'].split(':'))
            s_total_hours = s_hours + s_minutes/60
            label = 'Congested periods boundary' if element['idx'] == 1 else ''
            ax1.axvline(x=s_total_hours, color='red', linestyle='--', linewidth=2, label=label)

            e_hours, e_minutes = map(int, element['end'].split(':'))
            e_total_hours = e_hours + e_minutes/60
            # label = 'Peak-Periods' if element['idx'] == 1 else ''
            ax1.axvline(x=e_total_hours, color='red',linewidth=2, linestyle='--')
            

    # Right axis: Cumulative speed pattern
    ax1.plot(time_slot_hour, df['speed'], color='green', linewidth=1, label='Speed')
    ax1.set_ylim(0,85)
    ax1.set_yticks(np.arange(0, 85 + 1, 10))  # Ticks at 0, 20, 40, 60, 80
    # Set y-axis tick label color
    ax1.tick_params(axis='y', colors='green')
    # Set y-axis spine (axis line) color
    ax1.spines['left'].set_color('green')

    time_slot_hour_re = [0] + time_slot_hour.to_list()
    cumsum_speed_re = [0] + df['cumsum_speed'].to_list()

    ax2 = ax1.twinx()
    ax2.plot(time_slot_hour_re, cumsum_speed_re, color='blue', linewidth=1, label='Cumulative speed')
    ax2.set_ylabel('Cumulative Speed (miles)',fontsize=16, color='blue')
    ax2.set_ylim(0, 1600)
    ax2.set_yticks(np.arange(0, 1600 + 1, 200)) 
    # Set y-axis tick label color
    ax2.tick_params(axis='y', colors='blue')
    # Set y-axis spine (axis line) color
    ax2.spines['right'].set_color('blue')

    # Handle legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left',fontsize=15)

    fig.tight_layout()
    plt.savefig(f'./{working_f}/02 fig/16 PELT/{VDS_num}_{date}_{aggregate_timeframe}_{method}_{penalty}.png')
    # plt.show()  # Uncomment if you want to display the plot

# + jupyter={"source_hidden": true}
# 25/7/30 version

# # def pelt_speedbased_peak(df, column, speed_upper, model, date, VDS_num, penalty, aggregate_timeframe, min_length, method):
# import numpy as np
# import ruptures as rpt
# import pandas as pd

# def pelt_speedbased_peak(model, df, column, freeflow_speed, freeflow_speed_epsilon, 
#                          aggregate_timeframe, date, VDS_num, pelt_penalty, pelt_min_length, min_off_len, min_peak_len, method):
#     """
#     Detect peak periods using PELT on cumulative speed profile.
# `
#     Args:
#         df (DataFrame): Time-indexed traffic data with a 'speed' column.
#         column (str): Name of speed column.
#         speed_upper (float): Threshold to separate peak vs non-peak.
#         model (str): Cost model for ruptures (e.g., "rbf", "l2").
#         penalty (float): Penalty for adding a changepoint.

#     Returns:
#         DataFrame: Original df with added 'division' column.
#     """
#     df = df.copy()
    
#     # Step 1: Compute cumulative speed (helps detect changes in slope)
#     df["cumsum_" + column] = df[column].cumsum() * aggregate_timeframe / 60

#     # Step 2: Apply PELT on cumulative speed
#     signal = df[column].values
#     # bkpts = custom_pelt_l2(signal, penalty=pelt_penalty, min_size=int(min_size) if min_size else 1)

#     # algo = rpt.Pelt(model=model, jump=1).fit(signal)
#     algo = rpt.Pelt(model=model, min_size=int(pelt_min_length/aggregate_timeframe),jump=1).fit(signal)
    
# ## Breakpoints: [23, 45, 100]: Segment 1: indices 0 to 22 / Segment 2: indices 23 to 44 / Segment 3: indices 45 to 99
#     bkpts = algo.predict(pen=pelt_penalty)
#     print("Breakpoints:", bkpts)
    
#     # Step 3: Label segments
#     df["division"] = 0
#     peak_list = []
#     idx = 0
#     prev_peak_end = 0

#     for start, end in zip(bkpts[:-1], bkpts[1:]):
#         seg_mean = df[column].iloc[start:end].mean()
#         seg_len = (end - start) * aggregate_timeframe

#         if seg_len > min_off_len and seg_mean > freeflow_speed - freeflow_speed_epsilon:
#             df["division"].iloc[start:end] = 0
#         else:
#             if prev_peak_end != start:
#                 idx += 1
#             ## Based on the changepoint optimization formula, the segment is (
#             df["division"].iloc[(start:end] = idx
#             prev_peak_end = end

#     for div_idx, group in df.groupby("division"):
#         start_time = group["time_slot"].min() - aggregate_timeframe
#         end_time = group["time_slot"].max() + aggregate_timeframe
#         seg_len = end_time - start_time

#         if seg_len < min_peak_len and div_idx != 0:
#             df.loc[df['division'] == div_idx, 'division'] = -1
#             div_idx = -1

#         if div_idx != 0:
#             peak_list.append({
#                 "idx": div_idx,
#                 "start": f"{int(start_time // 60):02d}:{int(start_time % 60):02d}",
#                 "end": f"{int(end_time // 60):02d}:{int(end_time % 60):02d}",
#                 "length": seg_len
#             })

#     # If there are 100dataset, the last index in bkpts is 100. when plotting the changepoints, time_slot[100] is out of boundary, so omit the last index
#     bkpts = bkpts[:-1] 

#     PELT_plot_all(df, bkpts, date, VDS_num, aggregate_timeframe, peak_list, method)

#     return df, peak_list

# + jupyter={"source_hidden": true}
# def pelt_speedbased_directpeak(df, column, speed_upper, model, date, VDS_num, penalty, aggregate_timeframe, min_length, method):
import numpy as np
import ruptures as rpt
import pandas as pd

def pelt_speedbased_directpeak(model, df, column, freeflow_speed, freeflow_speed_epsilon, 
                         aggregate_timeframe, date, VDS_num, pelt_penalty, pelt_min_length, min_off_len, min_peak_len, method):
    
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
    df["cumsum_" + column] = df[column].cumsum() * aggregate_timeframe / 60

    # Step 2: Apply PELT on cumulative speed
    signal = df[column].values
    # bkpts = custom_pelt_l2(signal, penalty=pelt_penalty, min_size=int(min_size) if min_size else 1)

    # algo = rpt.Pelt(model=model, jump=1).fit(signal)
    algo = rpt.Pelt(model=model, min_size=int(pelt_min_length/aggregate_timeframe),jump=1).fit(signal)
    
## Breakpoints: [23, 45, 100]: Segment 1: indices 0 to 22 / Segment 2: indices 23 to 44 / Segment 3: indices 45 to 99
    bkpts = algo.predict(pen=pelt_penalty)
    # print("Breakpoints:", bkpts)

    ### In the actual PELT algorithm, a changepoint is assigned to the segment containing the preceding data points, so the index should be shifted forward by one.
    real_bkpts = [0] + [i-1 for i in bkpts]
    
    # Step 3: Label segments
    df["division"] = 0
    peak_list = []
    prev_peak_end = 0
    start = 0
    length = 0
    idx=0
    start_com = 0

    
    for end in real_bkpts:
        seg_mean_speed = df[column].iloc[(start):(end+1)].mean()

        if seg_mean_speed < (freeflow_speed - freeflow_speed_epsilon):
            if start_com == start:
                df["division"].iloc[(start):(end+1)] = idx
                
                ## Since it is hard to explain, ignore including one more point at the congested period.
                # if end+1 <= (len(df) -1) :
                #     df["division"].iloc[(end+1)] = idx
                
                # df.loc[df.index[(start):(end+1)], 'division'] = idx
                # # df.loc[df.index[(start+1):(end+1)], 'division'] = idx
                # df.loc[df.index[(start-1)], 'division'] = idx
                start_com = end
            else:
                idx +=1
                df["division"].iloc[(start):(end+1)] = idx
                
                ## Since it is hard to explain, ignore including one more point at the congested period.
                # if end+1 <= (len(df) -1) :
                #     df["division"].iloc[(end+1)] = idx
                
                # df.loc[df.index[(start):(end+1)], 'division'] = idx
                # df.loc[df.index[(start-1)], 'division'] = idx
                start_com = end
                
        start = end
    
    
    idx_lists = list(range(0,idx+1))

    if len(idx_lists)>1 :
        for idx in idx_lists[1:]:
            df_filter = df[df['division']==idx]
            start_time = df_filter['time_slot'].min() 
            end_time = df_filter['time_slot'].max()
            length = end_time - start_time
            
            peak_list.append({'idx': idx, 'start': f'{int(start_time // 60):02d}:{int(start_time % 60):02d}', 'end': f'{int(end_time // 60):02d}:{int(end_time % 60):02d}', 'length': length})
        
    PELT_plot(df, real_bkpts, date, VDS_num, aggregate_timeframe, peak_list, method)

    return df, peak_list

# + jupyter={"source_hidden": true}
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
        
            
    PELT_plot(df, changepoints, date, VDS_num, aggregate_timeframe, method)

    return df, peak_list

# + jupyter={"source_hidden": true}
# # def rdp_segmentation_peak(df, column, epsilon, freeflow_speed, freeflow_speed_epsilon, aggregate_timeframe, date, VDS_num, min_off_len, min_peak_len, method):

# from rdp import rdp
# import numpy as np
# import pandas as pd

# def rdp_segmentation_peak(df, column, epsilon, freeflow_speed, freeflow_speed_epsilon,
#                           aggregate_timeframe, date, VDS_num, min_off_len, min_peak_len, method):
#     """
#     Segment cumulative speed using RDP and classify segments as peak/non-peak.
#     Args:
#         df (DataFrame): Input DataFrame with 'time_slot' and speed column.
#         column (str): Speed column name.
#         epsilon (float): Tolerance for RDP (controls segmentation granularity).
#         speed_upper (float): Threshold to define peak periods.
#         aggregate_timeframe (int): Seconds per row (e.g., 300).
#         date (str): For plotting.
#         VDS_num (str): For plotting.
    
#     """
#     df = df.copy()
#     df["cumsum_" + column] = df[column].cumsum() * aggregate_timeframe / 60

#     # Apply RDP
#     points = np.column_stack([df.index, df["cumsum_" + column].values])
#     rdp_indices = rdp(points, epsilon=epsilon)[:, 0].astype(int).tolist()
#     if rdp_indices[-1] != df.index[-1]:
#         rdp_indices.append(df.index[-1])

#     df["division"] = 0
#     peak_list = []
#     idx = 0
#     prev_peak_end = 0

#     for start, end in zip(rdp_indices[:-1], rdp_indices[1:]):
#         seg_mean = df[column].iloc[start:end].mean()
#         seg_len = (end - start) * aggregate_timeframe

#         if seg_len > min_off_len and abs(seg_mean - freeflow_speed) < freeflow_speed_epsilon:
#             df["division"].iloc[start:end] = 0
#         else:
#             if prev_peak_end != start:
#                 idx += 1
#             df["division"].iloc[start:end] = idx
#             prev_peak_end = end

#     for div_idx, group in df.groupby("division"):
#         # start_time = group["time_slot"].min() - aggregate_timeframe/2
#         # end_time = group["time_slot"].max() + aggregate_timeframe/2
#         start_time = group["time_slot"].min()
#         end_time = group["time_slot"].max() + aggregate_timeframe
#         seg_len = end_time - start_time

#         if seg_len < min_peak_len and div_idx != 0:
#             df.loc[df['division'] == div_idx, 'division'] = -1
#             div_idx = -1

#         if div_idx != 0:
#             peak_list.append({
#                 "idx": div_idx,
#                 "start": f"{int(start_time // 60):02d}:{int(start_time % 60):02d}",
#                 "end": f"{int(end_time // 60):02d}:{int(end_time % 60):02d}",
#                 "length": seg_len
#             })

#     PELT_plot(df, rdp_indices, date, VDS_num, aggregate_timeframe, peak_list, method)

#     return df, peak_list

# + jupyter={"source_hidden": true}
# def pelt_speedbased_peak(df, column, speed_upper, model, date, VDS_num, penalty, aggregate_timeframe, min_length, method):
import numpy as np
import ruptures as rpt
import pandas as pd

def pelt_speedbased_peak(model, df, column, freeflow_speed, freeflow_speed_epsilon, 
                         aggregate_timeframe, date, VDS_num, pelt_penalty, pelt_min_length, min_off_len, min_peak_len, method):
    """
    Detect peak periods using PELT on cumulative speed profile.
`
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
    df["cumsum_" + column] = df[column].cumsum() * aggregate_timeframe / 60

    # Step 2: Apply PELT on cumulative speed
    signal = df[column].values
    # bkpts = custom_pelt_l2(signal, penalty=pelt_penalty, min_size=int(min_size) if min_size else 1)

    # algo = rpt.Pelt(model=model, jump=1).fit(signal)
    algo = rpt.Pelt(model=model, min_size=int(pelt_min_length/aggregate_timeframe),jump=1).fit(signal)
    
## Breakpoints: [23, 45, 100]: Segment 1: indices 0 to 22 / Segment 2: indices 23 to 44 / Segment 3: indices 45 to 99
    bkpts = algo.predict(pen=pelt_penalty)
    print("PELT_Breakpoints:", bkpts)

    ### In the actual PELT algorithm, a changepoint is assigned to the segment containing the preceding data points, so the index should be shifted forward by one.
    real_bkpts = [0] + [i-1 for i in bkpts]
    
    # Step 3: Label segments
    df["division"] = 0
    peak_list = []
    idx = 0
    prev_peak_end = 0

    for start, end in zip(real_bkpts[:-1], real_bkpts[1:]):
        seg_mean = df[column].iloc[(start):(end+1)].mean()
        seg_len = (end+1 - start) * aggregate_timeframe

        print(start,seg_mean)
        if seg_len > min_off_len and seg_mean > (freeflow_speed - freeflow_speed_epsilon):
            continue
        else:
            if prev_peak_end != start:
                idx += 1
            ## Based on the changepoint optimization formula, the segment is (
            # df["division"].iloc[(start+1):(end)] = idx
            df["division"].iloc[(start):(end+1)] = idx
            
            ## Since it is hard to explain, ignore including one more point at the congested period.
            # if end+1 <= (len(df) -1) :
            #     df["division"].iloc[(end+1)] = idx
            
            prev_peak_end = end
    
    for div_idx, group in df.groupby("division"):
        start_time = group["time_slot"].min()
        end_time = group["time_slot"].max()
        seg_len = end_time - start_time

        if seg_len < min_peak_len and div_idx != 0:
            df.loc[df['division'] == div_idx, 'division'] = -1
            div_idx = -1

        if div_idx != 0:
            peak_list.append({
                "idx": div_idx,
                "start": f"{int(start_time // 60):02d}:{int(start_time % 60):02d}",
                "end": f"{int(end_time // 60):02d}:{int(end_time % 60):02d}",
                "length": seg_len
            })


    PELT_plot(df, real_bkpts, date, VDS_num, aggregate_timeframe, peak_list, method, pelt_penalty)

    return df, peak_list

# + jupyter={"source_hidden": true}
# # rdp.py
# import numpy as np

# def rdp_v(points, epsilon):
#     """
#     Ramer–Douglas–Peucker with **vertical error** (y-axis) and full recursion.
#     Returns the kept points as [[x0, y0], [x1, y1], ..., [xM, yM]] in order.

#     Parameters
#     ----------
#     points : array-like, shape (n, 2)
#         Polyline points ordered by x (e.g., time index, cumulative value).
#         Column 0 = x (index or time), Column 1 = y (cumulative/signal).
#     epsilon : float
#         Vertical tolerance (same units as y). Larger epsilon -> fewer points.

#     Returns
#     -------
#     simplified : ndarray, shape (m, 2)
#         Subset of `points` (first and last always included), preserving order.
#     """
#     P = np.asarray(points, dtype=float)
#     if P.ndim != 2 or P.shape[1] != 2:
#         raise ValueError("`points` must be a (n, 2) array-like.")

#     # Ensure sorted by x (defensive; your df.index is already increasing)
#     order = np.argsort(P[:, 0], kind="stable")
#     P = P[order]

#     return _rdp_vertical_recursive(P, float(epsilon))


# def _rdp_vertical_recursive(P, epsilon):
#     n = P.shape[0]
#     if n <= 2:
#         return P

#     x1, y1 = P[0]
#     x2, y2 = P[-1]
#     dx = x2 - x1

#     # Predicted y on the straight line at each x (vertical projection)
#     if dx == 0.0:
#         # Degenerate: identical x at ends; interpolate along param t
#         t = np.linspace(0.0, 1.0, n)
#         y_line = y1 + t * (y2 - y1)
#     else:
#         t = (P[:, 0] - x1) / dx
#         y_line = y1 + t * (y2 - y1)

#     vertical_err = np.abs(P[:, 1] - y_line)

#     # Find interior point with max vertical error
#     if n > 2:
#         idx_rel = np.argmax(vertical_err[1:-1])      # index within slice (1..n-2)
#         idx_max = idx_rel + 1                         # absolute index in P
#         dmax = vertical_err[idx_max]
#     else:
#         dmax = 0.0
#         idx_max = None

#     if dmax > epsilon:
#         # Split and recurse on both halves (full recursion)
#         left = _rdp_vertical_recursive(P[:idx_max + 1], epsilon)
#         right = _rdp_vertical_recursive(P[idx_max:], epsilon)
#         # Concatenate without duplicating the split point
#         return np.vstack((left[:-1], right))
#     else:
#         # Endpoints approximate this span within tolerance
#         return P[[0, -1]]

# + jupyter={"source_hidden": true}
# # rdp.py: with the penalty depending on the lenght of the data
# import numpy as np

# def rdp_v(points, epsilon, aggregate_timeframe):
#     """
#     Ramer–Douglas–Peucker with **vertical error** (y-axis) and full recursion.
#     Returns the kept points as [[x0, y0], [x1, y1], ..., [xM, yM]] in order.

#     Parameters
#     ----------
#     points : array-like, shape (n, 2)
#         Polyline points ordered by x (e.g., time index, cumulative value).
#         Column 0 = x (index or time), Column 1 = y (cumulative/signal).
#     epsilon : float
#         Vertical tolerance (same units as y). Larger epsilon -> fewer points.

#     Returns
#     -------
#     simplified : ndarray, shape (m, 2)
#         Subset of `points` (first and last always included), preserving order.
#     """
#     P = np.asarray(points, dtype=float)
#     if P.ndim != 2 or P.shape[1] != 2:
#         raise ValueError("`points` must be a (n, 2) array-like.")

#     # Ensure sorted by x (defensive; your df.index is already increasing)
#     order = np.argsort(P[:, 0], kind="stable")
#     P = P[order]

#     return _rdp_vertical_recursive(P, float(epsilon), aggregate_timeframe)


# def _rdp_vertical_recursive(P, epsilon, aggregate_timeframe):
#     n = P.shape[0]
#     if n <= 2:
#         return P

#     x1, y1 = P[0]
#     x2, y2 = P[-1]
#     dx = x2 - x1

#     # Predicted y on the straight line at each x (vertical projection)
#     if dx == 0.0:
#         # Degenerate: identical x at ends; interpolate along param t
#         t = np.linspace(0.0, 1.0, n)
#         y_line = y1 + t * (y2 - y1)
#     else:
#         t = (P[:, 0] - x1) / dx
#         y_line = y1 + t * (y2 - y1)

#     vertical_err = np.abs(P[:, 1] - y_line)
#     adj_epsilon = epsilon * np.log(aggregate_timeframe * n/60)

#     # Find interior point with max vertical error
#     if n > 2:
#         idx_rel = np.argmax(vertical_err[1:-1])      # index within slice (1..n-2)
#         idx_max = idx_rel + 1                         # absolute index in P
#         dmax = vertical_err[idx_max]
#         print(dmax, idx_max, n, "dmax, idx_max,n")
#     else:
#         dmax = 0.0
#         idx_max = None

#     if dmax > adj_epsilon:
#         # Split and recurse on both halves (full recursion)
#         left = _rdp_vertical_recursive(P[:idx_max + 1], epsilon, aggregate_timeframe)
#         right = _rdp_vertical_recursive(P[idx_max:], epsilon, aggregate_timeframe)
#         # Concatenate without duplicating the split point
#         return np.vstack((left[:-1], right))
#     else:
#         # Endpoints approximate this span within tolerance
#         return P[[0, -1]]

# + jupyter={"source_hidden": true}
# rdp.py
import numpy as np

def rdp_v(points, epsilon):
    """
    Ramer–Douglas–Peucker with **vertical error** (y-axis) and full recursion.
    Returns the kept points as [[x0, y0], [x1, y1], ..., [xM, yM]] in order.

    Parameters
    ----------
    points : array-like, shape (n, 2)
        Polyline points ordered by x (e.g., time index, cumulative value).
        Column 0 = x (index or time), Column 1 = y (cumulative/signal).
    epsilon : float
        Vertical tolerance (same units as y). Larger epsilon -> fewer points.

    Returns
    -------
    simplified : ndarray, shape (m, 2)
        Subset of `points` (first and last always included), preserving order.
    """
    P = np.asarray(points, dtype=float)
    if P.ndim != 2 or P.shape[1] != 2:
        raise ValueError("`points` must be a (n, 2) array-like.")

    # Ensure sorted by x (defensive; your df.index is already increasing)
    order = np.argsort(P[:, 0], kind="stable")
    P = P[order]

    return _rdp_vertical_recursive(P, float(epsilon))


def _rdp_vertical_recursive(P, epsilon):
    n = P.shape[0]
    if n <= 2:
        return P

    x1, y1 = P[0]
    x2, y2 = P[-1]
    dx = x2 - x1

    # Predicted y on the straight line at each x (vertical projection)
    if dx == 0.0:
        # Degenerate: identical x at ends; interpolate along param t
        t = np.linspace(0.0, 1.0, n)
        y_line = y1 + t * (y2 - y1)
    else:
        t = (P[:, 0] - x1) / dx
        y_line = y1 + t * (y2 - y1)

    vertical_err = np.abs(P[:, 1] - y_line)

    # Find interior point with max vertical error
    if n > 2:
        slice_err = vertical_err[1:-1]
        
        # First max
        idx_rel = np.argmax(slice_err)
        idx_max = idx_rel + 1
        dmax = vertical_err[idx_max]
        
        # Mask out first max
        slice_err[idx_rel] = -np.inf
        
        # Second max
        idx2_rel = np.argmax(slice_err)
        idx2_abs = idx2_rel + 1
        dmax2 = vertical_err[idx2_abs]
        
        # print("Largest:", dmax, "at", idx_max)
        # print("Second largest:", dmax2, "at", idx2_abs)
    
    else:
        dmax = 0.0
        idx_max = None

    if dmax > epsilon:
        # Split and recurse on both halves (full recursion)
        left = _rdp_vertical_recursive(P[:idx_max + 1], epsilon)
        right = _rdp_vertical_recursive(P[idx_max:], epsilon)
        # Concatenate without duplicating the split point
        return np.vstack((left[:-1], right))
    else:
        # Endpoints approximate this span within tolerance
        return P[[0, -1]]


# + jupyter={"source_hidden": true}
# using rdp but error metric as vertical distance

from rdp import rdp
import numpy as np
import pandas as pd

def rdp_v_segmentation_peak(df, column, epsilon, freeflow_speed, freeflow_speed_epsilon,
                          aggregate_timeframe, date, VDS_num, min_off_len, min_peak_len, method):
    """
    Segment cumulative speed using RDP and classify segments as peak/non-peak.
    Args:
        df (DataFrame): Input DataFrame with 'time_slot' and speed column.
        column (str): Speed column name.
        epsilon (float): Tolerance for RDP (controls segmentation granularity).
        speed_upper (float): Threshold to define peak periods.
        aggregate_timeframe (int): Seconds per row (e.g., 300).
        date (str): For plotting.
        VDS_num (str): For plotting.
    
    """
    df = df.copy()
    df["cumsum_" + column] = df[column].cumsum() * aggregate_timeframe / 60

    min_offpeak_hour = 4

    if (len(df[df[column] < (freeflow_speed - freeflow_speed_epsilon-5)]) / len(df[column])) < (0.5 / 24):
        min_offpeak_hour = 24

    freeflow_speed_tol = max(df[column].iloc[0:int(4*60/5)].mean(),df[column].iloc[-int(4*60/5):].mean(), 60)
    # print(freeflow_speed_tol,"speed_tol")
    max_margin = 2
    # print("avg_speed",df[column].mean())
    avg_speed = min(df[column].mean(), freeflow_speed_tol-max_margin)

    # epsilon = theta / avg_speed
    # print("avg_speed",avg_speed, epsilon)
    # k=7.1
    
    # Apply RDP
    points = np.column_stack([df.index, df["cumsum_" + column].values])
    rdp_indices = rdp_v(points, epsilon)[:, 0].astype(int).tolist()
    if rdp_indices[-1] != df.index[-1]:
        rdp_indices.append(df.index[-1])

    print("RDP_Breakpoints:", rdp_indices)
    df["division"] = 0
    peak_list = []
    idx = 0
    prev_peak_end = 0

    for start, end in zip(rdp_indices[:-1], rdp_indices[1:]):
        seg_mean = df[column].iloc[(start):(end+1)].mean()
        seg_len = (end+1 - start) * aggregate_timeframe

        if seg_len > min_off_len and abs(seg_mean - freeflow_speed) < freeflow_speed_epsilon:
            continue
        else:
            if prev_peak_end != start:
                idx += 1
            df["division"].iloc[(start):(end+1)] = idx
            # df["division"].iloc[start] = idx
            
            ## Since it is hard to explain, ignore including one more point at the congested period.
            # if end+1 <= (len(df) -1) :
            #     df["division"].iloc[(end+1)] = idx
                    
            prev_peak_end = end

    for div_idx, group in df.groupby("division"):
        # start_time = group["time_slot"].min() - aggregate_timeframe/2
        # end_time = group["time_slot"].max() + aggregate_timeframe/2
        start_time = group["time_slot"].min()
        end_time = group["time_slot"].max()
        seg_len = end_time - start_time

        if seg_len < min_peak_len and div_idx != 0:
            df.loc[df['division'] == div_idx, 'division'] = -1
            div_idx = -1

        if div_idx != 0:
            peak_list.append({
                "idx": div_idx,
                "start": f"{int(start_time // 60):02d}:{int(start_time % 60):02d}",
                "end": f"{int(end_time // 60):02d}:{int(end_time % 60):02d}",
                "length": seg_len
            })

    PELT_plot(df, rdp_indices, date, VDS_num, aggregate_timeframe, peak_list, method, epsilon)

    return df, peak_list


# + jupyter={"source_hidden": true}
# def rdp_segmentation_peak(df, column, epsilon, freeflow_speed, freeflow_speed_epsilon, aggregate_timeframe, date, VDS_num, min_off_len, min_peak_len, method):

from rdp import rdp
import numpy as np
import pandas as pd

def rdp_segmentation_peak(df, column, epsilon, freeflow_speed, freeflow_speed_epsilon,
                          aggregate_timeframe, date, VDS_num, min_off_len, min_peak_len, method):
    """
    Segment cumulative speed using RDP and classify segments as peak/non-peak.
    Args:
        df (DataFrame): Input DataFrame with 'time_slot' and speed column.
        column (str): Speed column name.
        epsilon (float): Tolerance for RDP (controls segmentation granularity).
        speed_upper (float): Threshold to define peak periods.
        aggregate_timeframe (int): Seconds per row (e.g., 300).
        date (str): For plotting.
        VDS_num (str): For plotting.
    
    """
    df = df.copy()
    df["cumsum_" + column] = df[column].cumsum() * aggregate_timeframe / 60

    # Apply RDP
    points = np.column_stack([df.index, df["cumsum_" + column].values])
    
    rdp_indices = rdp(points, epsilon=epsilon)[:, 0].astype(int).tolist()
    if rdp_indices[-1] != df.index[-1]:
        rdp_indices.append(df.index[-1])

    print("RDP_Breakpoints:", rdp_indices)
    df["division"] = 0
    peak_list = []
    idx = 0
    prev_peak_end = 0

    for start, end in zip(rdp_indices[:-1], rdp_indices[1:]):
        seg_mean = df[column].iloc[(start):(end+1)].mean()
        seg_len = (end+1 - start) * aggregate_timeframe

        if seg_len > min_off_len and abs(seg_mean - freeflow_speed) < freeflow_speed_epsilon:
            continue
        else:
            if prev_peak_end != start:
                idx += 1
            df["division"].iloc[(start):(end+1)] = idx
            # df["division"].iloc[start] = idx
            ## Since it is hard to explain, ignore including one more point at the congested period.
            # if end+1 <= (len(df) -1) :
            #     df["division"].iloc[(end+1)] = idx
                    
            prev_peak_end = end

    for div_idx, group in df.groupby("division"):
        # start_time = group["time_slot"].min() - aggregate_timeframe/2
        # end_time = group["time_slot"].max() + aggregate_timeframe/2
        start_time = group["time_slot"].min()
        end_time = group["time_slot"].max()
        seg_len = end_time - start_time

        if seg_len < min_peak_len and div_idx != 0:
            df.loc[df['division'] == div_idx, 'division'] = -1
            div_idx = -1

        if div_idx != 0:
            peak_list.append({
                "idx": div_idx,
                "start": f"{int(start_time // 60):02d}:{int(start_time % 60):02d}",
                "end": f"{int(end_time // 60):02d}:{int(end_time % 60):02d}",
                "length": seg_len
            })

    PELT_plot(df, rdp_indices, date, VDS_num, aggregate_timeframe, peak_list, method)

    return df, peak_list


# + jupyter={"source_hidden": true}
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
                df['division'].iloc[start:i] = idx
                print("uniqueslot",df.loc[df['division'] == idx,"time_slot"].unique())
                start_time = df.iloc[start]["time_slot"] - aggregate_timeframe/2
                end_time = df.iloc[i-1]["time_slot"] + aggregate_timeframe/2
                
                length = end_time - start_time
                
                peak_list.append({
                    "idx": idx,
                    "start": f"{int(start_time // 60):02d}:{int(start_time % 60):02d}",
                    "end": f"{int((end_time) // 60):02d}:{int((end_time) % 60):02d}",
                    "length": length
                })
                changepoints.append(start)
                changepoints.append(i)

                idx += 1
                
            start = i
            outliers = 0
            prev = i

    # Plot with RDP breakpoints
    PELT_plot(df, changepoints, date, VDS_num, aggregate_timeframe, peak_list, method)
    
    return df, peak_list


# + jupyter={"source_hidden": true}
# =====================
# Utility Functions
# =====================

def load_raw(file_name, config):
    """
    Load and standardize raw traffic data and gfactor for a given date file.
    Returns: rawdata (DataFrame), gfactor (DataFrame), date (str)
    """
    date = file_name[-11:-5]
    gfile = f"{config['path']}/11 Rawdata/gfactor/{config['VDS_num']}/gfactor_{date}.xlsx"
    gfactor = pd.read_excel(gfile)
    rawdata = rawdata_setting(
        full_path=f"{config['path']}/11 Rawdata/{config['dir']}/{config['VDS_num']}",
        VDS_num=config['VDS_num'],
        file_name = file_name,
        lane_num=config['lane_num']
    )
    return rawdata, gfactor, date


def load_or_aggregate(rawdata, date, config):
    """
    Aggregate and cache daily traffic if not already saved.
    Returns: traffic_within_day (DataFrame), plot_date (list)
    """
    agg = config['aggregate_timeframe']
    cache_dir = f"./{working_f}/12 python file/{config['VDS_num']}"
    traffic_file = os.path.join(cache_dir, f"traffic_within_day_{date}_{agg}aggmin_{config["lane_num"]}.p")
    plot_file = os.path.join(cache_dir, f"plot_date_{date}_{agg}aggmin.p")

    if os.path.exists(traffic_file):
        with open(traffic_file, 'rb') as f:
            traffic = pickle.load(f)
        with open(plot_file, 'rb') as f:
            plot_date = pickle.load(f)
    else:
        traffic, plot_date = aggregate_rawdata_for_peakdetection(
            rawdata, agg, config['raw_timeframe'], date,
            config['lane_num'], gfactor, config['VDS_num']
        )
        os.makedirs(cache_dir, exist_ok=True)
        with open(traffic_file, 'wb') as f: pickle.dump(traffic, f)
        with open(plot_file, 'wb') as f: pickle.dump(plot_date, f)

    return traffic, plot_date


# + jupyter={"source_hidden": true}
def skip_if_missing(rawdata, config):
    """
    Check if rawdata exceeds missing_ratio threshold; skip if too many missing slots.
    """
    total_expected = (24 * 60) / config['raw_timeframe']
    return len(rawdata) < (1 - config['missing_ratio']) * total_expected
    

def highfreeflowspeed_conversion(traffic, config):
    threshold = config['freeflow_speed_thre']
    traffic.loc[(traffic['speed']>threshold),'speed'] = threshold

    return traffic

    
def interpolate_missing(traffic, config):
    """
    Linearly interpolate missing time slots in the aggregated traffic DataFrame.
    """
    traffic = traffic.copy()
    a_tf = config['aggregate_timeframe']
    ## x+a_tf/2 is only applicable for the two-peak detection. otherwise, use {x for x in range(1,24*60+a_tf, a_tf)}
    all_slots = {x + a_tf / 2 for x in range(0, 24 * 60, a_tf)}
    present = set(traffic['time_slot'])
    missing = sorted(all_slots - present)

    for t in missing:
        if t == min(all_slots) or t == max(all_slots):
            continue
        prev_t = max(s for s in present if s < t)
        next_t = min(s for s in present if s > t)
        row_prev = traffic[traffic.time_slot == prev_t].iloc[0].astype(float)
        row_next = traffic[traffic.time_slot == next_t].iloc[0].astype(float)
        weight = (t - prev_t) / (next_t - prev_t)
        new_row = row_prev * (1 - weight) + row_next * weight
        new_row['time_slot'] = t
        traffic = pd.concat([traffic, new_row.to_frame().T], ignore_index=True)

    return traffic.sort_values('time_slot').reset_index(drop=True)



# + jupyter={"source_hidden": true}
def assign_fixedtime_peaks(traffic, config):
    """
    Label each time slot into divisions based on temporal_scale.
    This function does not apply when temporal_scale is 'speedbasedpeak'
    """
    ts = traffic.copy()
    scale = config['temporal_scale']
    if scale == 'hour':
        ts['division'] = ts.time_slot // 60

    elif scale == 'peak':
        ts['division'] = 0
        m, M = config['peak_periods']['morning']
        a, A = config['peak_periods']['afternoon']
        ts.loc[ts.time_slot.between(m, M), 'division'] = 1
        ts.loc[ts.time_slot.between(a, A), 'division'] = 2

    elif scale == 'entireday':
        ts['division'] = 0

    return ts


# -

def compute_metrics(group, division_idx, config, group_num):
    """
    Compute travel time, total demand, and period label for a traffic division.
    """
    flows = group[[f'flow_{i}' for i in config['lane_num']]].values.flatten()
    speeds = group[[f'speed_{i}' for i in config['lane_num']]].values.flatten()
    mask = ~np.isnan(speeds)
    flow_good, speed_good = flows[mask], speeds[mask]
    
    if config['temporal_scale'] in ('speedbasedpeak', 'peak') and division_idx != 0:
        # len(group)-1 reason: 
        # if congested period is detected as 8:00:30 ~ 8:55:30 then, the division==1 ranges will be 8:00:00 to 9:00:00. 
        # so, we need to "-1" to eliminate each side of 2:30 min.
        time_duration = (len(group)-1) * config['aggregate_timeframe']

        # demand means total volumes during the congested period
        flow_good[0] = flow_good[0]/2
        flow_good[(len(flow_good)-1)] = flow_good[(len(flow_good)-1)]/2

        sum_flow = flow_good.sum()
        demand = sum_flow * (config['aggregate_timeframe']/60) / len(config['lane_num'])
        avg_flow = flow_good.mean() * len(group) / (len(group)-1)
        t0 = group.time_slot.min()

        sum_prod = (flow_good / speed_good).sum()
        traveltime = sum_prod / sum_flow * 60
        
        m, M = config['peak_periods']['morning']
        a, A = config['peak_periods']['afternoon']

        # start time
        if m < t0 < M:
            period = 'morning-peak'
        elif a < t0 < A:
            period = 'afternoon-peak'
        else:
            period = 'off-peak'
    else:
        sum_flow = flow_good.sum()
        
        demand = sum_flow * (config['aggregate_timeframe']/60) / len(config['lane_num'])
        avg_flow = flow_good.mean()
        
        time_duration = (len(group)+group_num-1) * config['aggregate_timeframe']
        period = 'off-peak'

        ## Actually, it needs to be revised, beacause it does not include the first/last half of the congested period part.
        sum_prod = (flow_good / speed_good).sum()
        traveltime = sum_prod / sum_flow * 60

    return traveltime, demand, avg_flow, division_idx, period, time_duration


# #### (code) implementation

# +
# Parameters for handling the data
# raw_timeframe: Defines the timeframe unit in minutes for the input raw data 
# (e.g., 30 seconds is represented as 0.5 minutes).
raw_timeframe = 0.5

# path: The base directory path where the raw data files are stored.
working_f = '01_BPR'
path = '/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/11 Rawdata'

# directory: The subdirectory name under the main path where the data files are located.
directory = '30sec'

# VDS_num: The subdirectory name under the main path where the data files are located.
# VDS_num = '1205583'
# VDS_num = '1203506'
VDS_num = '1214006'

c_lane_num = {'1205583':[1,2,3,4,5,6], '1203506':[1,2,3,4],'1214006':[1,2,3,4]}
lane_num = c_lane_num[VDS_num]

# Constructs the full path to the directory containing the data files.
full_path = os.path.join(path, directory, VDS_num)

# Retrieves a list of all files in the specified directory.
# This list will be used to iterate over or reference the data files for processing.
file_list = sorted(os.listdir(full_path))
if '.DS_Store' in file_list:
    file_list.remove('.DS_Store')

# lane_num: Specifies the range of lane numbers to be analyzed.
# This is used to filter or segment the data based on lane information.

Day_list = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

# Printing the list of files found in the specified directory.
print("Files in the specified directory:", file_list, len(file_list))



# +
import os
import pickle
import numpy as np
import pandas as pd

# =====================
# Configuration Section
# =====================
config = {
    # Temporal granularity: 'hour', 'peak', 'entireday', 'speedbasedpeak'
    'temporal_scale': 'speedbasedpeak',

    # File paths and identifiers
    'path': './01_BPR',           # base data directory
    'dir': directory,
    'VDS_num': VDS_num,         # detector ID
    'lane_num': lane_num,       # list of lane indices
    'file_list': file_list,     # list of raw data filenames

    # Data quality thresholds
    'missing_ratio': 0.05,      # max allowed missing fraction
    'freeflow_speed_thre': 80,  # cap for speed values (units)

    # Time parameters (minutes)
    'raw_timeframe': raw_timeframe,
    'aggregate_timeframe': 5,

    # Peak window definitions (minutes from midnight)
    'peak_periods': {
        'morning': (6 * 60, 10 * 60),
        'afternoon': (12.5 * 60, 20 * 60)
    },

    # Speed-based peak |detection parameters
    'speedbased_params': {
        ## joon, pelt, RDP_v, derivative, pelt_directpeak
        'method': 'RDP_v',
        'pelt_min_length': 5,
        'min_off_len': 60,
        'min_peak_len': 0,
        'speed_upper': 60,
        'freeflow_speed':70,
        'freeflow_speed_epsilon':20
    }
}


# -

def detect_speed_peaks(traffic, date, config):
    """
    Identify peak periods based on speed using chosen method (pelt, derivative, RDP, etc.).
    Returns updated DataFrame and list of peak intervals.
    """
    params = config['speedbased_params']
    if params['method'] == 'RDP':
        return rdp_segmentation_peak(
            df = traffic, column='speed',
            epsilon=1.5, freeflow_speed=params['freeflow_speed'],
            freeflow_speed_epsilon=params['freeflow_speed_epsilon'],
            aggregate_timeframe=config['aggregate_timeframe'],
            date=date, VDS_num=config['VDS_num'],
            min_off_len=params['min_off_len'],
            min_peak_len=params['min_peak_len'],
            method=params['method']
        )
    elif params['method'] == 'RDP_v':
        return rdp_v_segmentation_peak(
            df = traffic, column='speed',
            epsilon=12, freeflow_speed=params['freeflow_speed'],
            freeflow_speed_epsilon=params['freeflow_speed_epsilon'],
            aggregate_timeframe=config['aggregate_timeframe'],
            date=date, VDS_num=config['VDS_num'],
            min_off_len=params['min_off_len'],
            min_peak_len=params['min_peak_len'],
            method=params['method']
        )
    elif params['method'] == 'pelt':
        return pelt_speedbased_peak(
            model = "l2",
            df = traffic, column='speed', 
            freeflow_speed=params['freeflow_speed'],
            freeflow_speed_epsilon=params['freeflow_speed_epsilon'],
            aggregate_timeframe=config['aggregate_timeframe'],
            date=date, VDS_num=config['VDS_num'],
            # pelt_penalty = 320, # (previous value in TRB)
            pelt_penalty = 2500,
            pelt_min_length = params['pelt_min_length'],
            min_off_len=params['min_off_len'],
            min_peak_len=params['min_peak_len'],
            method=params['method']
        )
    elif params['method'] == 'pelt_directpeak':
        return pelt_speedbased_directpeak(
            model = "l2",
            df = traffic, column='speed', 
            freeflow_speed=params['freeflow_speed'],
            freeflow_speed_epsilon=params['freeflow_speed_epsilon'],
            aggregate_timeframe=config['aggregate_timeframe'],
            date=date, VDS_num=config['VDS_num'],
            pelt_penalty = 320,
            pelt_min_length = params['pelt_min_length'],
            min_off_len=params['min_off_len'],
            min_peak_len=params['min_peak_len'],
            method=params['method']
        )
    elif params['method'] == 'derivative':
        return derivative_based_segmentation(
            df = traffic, column='speed', 
            slope_threshold=80, window=15, min_gap=10, speed_upper=speed_upper, 
            aggregate_timeframe=config['aggregate_timeframe'], 
            min_length = params['min_length'], 
            method = params['method'])
            # traffic_within_day_intpol, peak_list = derivative_based_segmentation(traffic_within_day_intpol, column='speed', slope_threshold=15, window=60, min_gap=10, speed_upper=55, aggregate_timeframe=aggregate_timeframe, min_length= min_length, method = method)
    elif params['method'] == 'joon':
         return speedbasedpeak(
             df = traffic, column='speed', 
             speed_upper = params['speed_upper'], min_minutes = params['min_peak_len'], 
             max_outliers = 0, aggregate_timeframe = config['aggregate_timeframe'], 
             method = params['method'])


# +
# =====================
# Main Processing Loop
# =====================
c_daily_flow = []
c_daily_traveltimes = []
c_date = []
c_division = []
c_period = []
c_dayofweek = []
c_totaldemand = []
c_avgflow = []
c_duration = []
set_peak_period = pd.DataFrame(columns=["date", "peak_list"])
Day_list = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

# 'wholeday', 'peak'
temporal_scope = 'peak'


for file_name in config['file_list']:
    print(file_name)
    rawdata, gfactor, date = load_raw(file_name, config)
    if skip_if_missing(rawdata, config):
        continue

    traffic, plot_date = load_or_aggregate(rawdata, date, config)

    traffic = highfreeflowspeed_conversion(traffic, config)
    traffic = interpolate_missing(traffic, config)
    traffic = assign_fixedtime_peaks(traffic, config)

    traffic.to_csv(f"./traffic_{VDS_num}_{file_name}.csv")

    if temporal_scope == 'wholeday':
        traffic['division'] = 0
        group_num = len(traffic['division'].unique())
        
        tt, demand, avg_flow, div, period, time_duration = compute_metrics(traffic, 0, config, group_num)
        c_daily_traveltimes.append(tt); c_totaldemand.append(demand); c_avgflow.append(avg_flow)
        c_date.append(date); c_division.append(div); c_period.append(period)
        c_dayofweek.append(Day_list[int(rawdata.loc[0, 'time'].weekday())]); c_duration.append(time_duration)

    elif temporal_scope == 'peak':
        # Speed-based peak detection
        if config['temporal_scale'] == 'speedbasedpeak':
            traffic, peaks = detect_speed_peaks(traffic, date, config)
            set_peak_period = pd.concat([set_peak_period, pd.DataFrame([{'date': date, 'peak_list': peaks}])], ignore_index=True)
    
        # Compute metrics per division
        group_num = len(traffic['division'].unique())
        
        for division_idx, group in traffic.groupby('division'):
            tt, demand, avg_flow, div, period, time_duration = compute_metrics(group, division_idx, config, group_num)
            c_daily_traveltimes.append(tt); c_totaldemand.append(demand); c_avgflow.append(avg_flow)
            c_date.append(date); c_division.append(div); c_period.append(period)
            c_dayofweek.append(Day_list[int(rawdata.loc[0, 'time'].weekday())]); c_duration.append(time_duration)
# -

print(set_peak_period)
set_peak_period.to_csv(f"./{working_f}/set_peak_period_{config['VDS_num']}_{config['aggregate_timeframe']}_{config['speedbased_params']['method']}.csv")

# +
c_daily_traffic = pd.DataFrame({'traveltimes': c_daily_traveltimes, 'totaldemand': c_totaldemand, 'avg_flow': c_avgflow, 'date': c_date, 'dayofweek': c_dayofweek, 'period':c_period, 'duration':c_duration, 'division': c_division })

c_daily_traffic['year'] = c_daily_traffic['date'].astype(int)//10000 + 2000
c_daily_traffic.to_csv(f"./{working_f}/c_daily_traffic_{config['VDS_num']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config['speedbased_params']['method']}_{temporal_scope}.csv")

# +
### eliminate days with more than same periods having more than two.
c_daily_traffic = pd.read_csv(f"./{working_f}/c_daily_traffic_{config['VDS_num']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config['speedbased_params']['method']}_{temporal_scope}.csv")
c_daily_traffic.head()

# Find dates with duplicate periods
dup_dates = (
    c_daily_traffic.groupby("date")["period"]
    .apply(lambda x: x.duplicated().any())
)

print(dup_dates[dup_dates == True])

# Keep only dates without duplicate periods
valid_dates = dup_dates[~dup_dates].index
c_daily_traffic_filtered = c_daily_traffic[c_daily_traffic["date"].isin(valid_dates)]



print("Before:", c_daily_traffic.shape)
print("After :", c_daily_traffic_filtered.shape)

c_daily_traffic_filtered.to_csv(f"./{working_f}/c_daily_traffic_{config['VDS_num']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config['speedbased_params']['method']}_{temporal_scope}_filtered.csv")
# -

# ### (Code) Result & Analysis: Congestion-based Peak period result

# +
import pandas as pd
import ast

temporal_scale = 'speedbasedpeak'
# VDS: 1203506, 1205583
VDS_num = '1203506'
# VDS_num = '1205583'
# VDS_num = '1214006'

aggregate_timeframe = 5
#pelt, RDP, joon
methods = ['RDP','pelt','pelt_directpeak','RDP_v']

for method in methods:
    file_path_setpeakperiod = f"./{working_f}/set_peak_period_{VDS_num}_{aggregate_timeframe}_{method}.csv"
    set_peak_period = pd.read_csv(file_path_setpeakperiod)
    
    # Convert 'peak_list' string to list of dictionaries
    set_peak_period['peak_list'] = set_peak_period['peak_list'].apply(ast.literal_eval)
      
    with open(f"./{working_f}/set_peak_period_{VDS_num}_{aggregate_timeframe}_{method}.p",'wb') as file:
        pickle.dump(set_peak_period, file)

# +
import pandas as pd
from datetime import datetime


# Load the DataFrames
pelt_df = pd.read_pickle(f"./{working_f}/set_peak_period_{VDS_num}_5_pelt.p")
rdp_df  = pd.read_pickle(f"./{working_f}/set_peak_period_{VDS_num}_5_RDP_v.p")
peltdirect_df  = pd.read_pickle(f"./{working_f}/set_peak_period_{VDS_num}_5_pelt_directpeak.p")

# case: "peltrdp" or "peltpelt"
case = "peltrdp"

if case == "peltrdp":
    df2 = rdp_df
elif case == "peltpelt":
    df2 = peltdirect_df

# Helper to convert "hh:mm" to minutes since midnight
def time_to_minutes(t):
    h, m = map(int, t.split(':'))
    return h*60 + m

case_counts = {1: 0, 2: 0, 3: 0}
start_diff_threshold = 30
len_diff_threshold = 30
max_threshold = 120

set_case3 =[]

# for each day
for i in range(len(pelt_df)):
    # print(pelt_df.iloc[i]['date'])
    
    list1 = pelt_df.iloc[i]['peak_list']
    list2 = df2.iloc[i]['peak_list']

    # when both of them detect did not detect congested period during a day
    if len(list1)==0  and len(list2) ==0:
        # continue
        case_counts[1] += 1  # Case 1: exact match
    # when at least one of the methods detect congested periods
    else:
        # If the detected congested periods are within 'max_threshold'(e.g., 2hours) between the methods, regard them as the potential same congested period.
        # Matching logic (simple summary)
        # 1) Always iterate over the longer list to avoid double-counting when one
        #    long congested segment is split into two shorter ones by the other method.
        # 2) For each long segment, consider only short segments whose starts are within
        #    `max_threshold` minutes of the long segment’s start.
        # 3) Use `checked_idx` to ensure each short segment is matched at most once per long segment.
        # 4) Classification:
        #    - Case 1: start AND length are exactly equal.
        #    - Case 2: start and length differences are within thresholds (`start_diff_threshold`, `len_diff_threshold`).
        #    - Case 3: otherwise (record as mismatch and log the date).
        if len(list1) >= len(list2):
            list_longs = list1
            list_shorts = list2
        else:
            list_longs = list2
            list_shorts = list1

        checked_idx = []

        # for every peak_period in the long_lists of each day
        for list_me in list_longs:    

            for list_other in list_shorts:
                diff_start = abs(time_to_minutes(list_me['start']) - time_to_minutes(list_other['start']))
                    
                # find another peak_period from the other method within the common period to compare
                if diff_start <= max_threshold:
                    # check if the period is already compared in the previous iterations. if then, we dont need to compare it again. 
                    # (ensure each short segment is matched at most once per long segment.)
                    if list_other['idx'] in checked_idx:
                        
                        continue
                    else:
                        checked_idx.append(list_other['idx'])
                        
                        if list_me['start'] == list_other['start'] and list_me['length'] == list_other['length']:
                            case_counts[1] += 1  # Case 1: exact match
                        else:
                            diff_len  = abs(list_me['length'] - list_other['length'])
                            
                            if diff_start <= start_diff_threshold and diff_len <= len_diff_threshold:
                                case_counts[2] += 1  # Case 2: both differences within ±20 minutes
                            else:
                                case_counts[3] += 1  # Case 3: everything else
                                set_case3.append(pelt_df.loc[i,'date'])


# Display summary
summary_df = pd.DataFrame({
    'Case': ['Case 1', 'Case 2', 'Case 3'],
    'Description': [
        'start and length match exactly',
        'start and length differ but both within ±20 minutes',
        'all other cases (no match or beyond threshold)'
    ],
    'Count': [case_counts[1], case_counts[2], case_counts[3]]
})
print("VDS_num",VDS_num)
print(summary_df)
print(set_case3)
# -

# #### (Code) Comparison plot

# +
import random
# Set the seed
random.seed(42)  # You can pick any number here


# VDS_num: The subdirectory name under the main path where the data files are located.
# VDS_num_analyze = '1205583'
VDS_num_analyze = '1203506'
# 
c_lane_num = {'1205583':[1,2,3,4,5,6], '1203506':[1,2,3,4]}
lane_num = c_lane_num[VDS_num_analyze]

sample_size = 30
purpose = 'RDP'

# Constructs the full path to the directory containing the data files.
full_path = os.path.join(path, directory, VDS_num_analyze)
file_list = sorted(os.listdir(full_path))
if '.DS_Store' in file_list:
    file_list.remove('.DS_Store')

# Select 20 random samples
samples_file_list = random.sample(file_list, sample_size)

# file_list = ['Rawdata_240123.xlsx', 'Rawdata_120817.xlsx', 'Rawdata_120823.xlsx', 'Rawdata_110213.xlsx', 'Rawdata_110315.xlsx', 'Rawdata_110307.xlsx']
print(samples_file_list)
# -

# =====================
# Configuration Section
# =====================
config_v2 = {
    # Temporal granularity: 'hour', 'peak', 'entireday', 'speedbasedpeak'
    'temporal_scale': 'speedbasedpeak',

    # File paths and identifiers
    'path': './01_BPR',           # base data directory
    'dir': directory,
    'VDS_num': VDS_num_analyze,         # detector ID
    'lane_num': lane_num,       # list of lane indices
    'file_list': file_list,     # list of raw data filenames

    # Data quality thresholds
    'missing_ratio': 0.05,      # max allowed missing fraction
    'freeflow_speed_thre': 80,  # cap for speed values (units)

    # Time parameters (minutes)
    'raw_timeframe': raw_timeframe,
    'aggregate_timeframe': 5,

    # Peak window definitions (minutes from midnight)
    'peak_periods': {
        'morning': (6 * 60, 10 * 60),
        'afternoon': (15 * 60, 19 * 60)
    }}


def PELT_plot_all(df, date, VDS_num, aggregate_timeframe, peak_list_PELT, peak_list_RDP, peak_list_PELT_direct, purpose):
# def PELT_plot_all(df, bkpts, date, VDS_num, aggregate_timeframe, peak_list_PELT, method):
    
    time_slot_hour = df['time_slot'] / 60
    date_v2 = f'{date[2:4]}/{date[4:6]}/20{date[0:2]}'
    
    # joon, pelt, RDP, derivative
    title_name = {'RDP':f'Congestion Period Detection from PELT and RDP (VDS: {VDS_num}, Date: {date_v2})', 
                  'PELT_direct': f'Comparison of Proposed and Previous Approaches (VDS: {VDS_num}, Date: {date_v2})'}

    label_name = {'RDP':['PELT-detected congestion boundaries', 'RDP-detected congestion boundaries'],
                  'PELT_direct': ['Proposed method: congested period boundary','Previous method: congested period boundary']}
    
    fig, ax1 = plt.subplots(figsize=(12, 5))

    
    # Left axis: Changepoints (as vertical lines)
    ax1.set_xlabel('Time (Hours)',fontsize=16)
    ax1.set_ylabel('Speed (mph)',fontsize=16, color = 'green')
    ax1.set_title(title_name[purpose],fontsize=18)
    ax1.grid(True)
    ax1.set_xlim(0, 24+.1)
    ax1.set_xticks(np.arange(0, 25, 1))

    # Plot peak/off-peaks
    select_date_PELT = peak_list_PELT.loc[(peak_list_PELT['date'] == int(date)),'peak_list'].iloc[0]
    select_date_RDP = peak_list_RDP.loc[(peak_list_RDP['date'] == int(date)),'peak_list'].iloc[0]
    # select_date_PELT_direct = peak_list_PELT_direct.loc[(peak_list_PELT_direct['date'] == int(date)),'peak_list'].iloc[0]

    if purpose == 'RDP':
        select_date_purpose = select_date_RDP
    elif purpose == 'PELT_direct':
        select_date_purpose = select_date_PELT_direct

    
    for element in select_date_PELT:
        if len(element) == 0:
            continue
        
        if element['idx'] > 0:
            s_hours, s_minutes = map(int, element['start'].split(':'))
            s_total_hours = s_hours + s_minutes/60
            # label = 'PELT congested boundary' if element['idx'] == 1 else ''
            label = label_name[purpose][0] if element['idx'] == 1 else ''
            ax1.axvline(x=s_total_hours, color='red', linewidth=2.5, linestyle='-', label=label)

            e_hours, e_minutes = map(int, element['end'].split(':'))
            e_total_hours = e_hours + e_minutes/60
            # label = 'Peak-Periods' if element['idx'] == 1 else ''
            ax1.axvline(x=e_total_hours, color='red', linewidth=2.5, linestyle='-')
            
    
    for element in select_date_purpose:    
        if len(element) == 0:
            continue
        
        if element['idx'] > 0:
            s_hours, s_minutes = map(int, element['start'].split(':'))
            s_total_hours = s_hours + s_minutes/60
            label = label_name[purpose][1] if element['idx'] == 1 else ''
            ax1.axvline(x=s_total_hours, color='purple', linewidth=2.5, linestyle='--', label=label)

            e_hours, e_minutes = map(int, element['end'].split(':'))
            e_total_hours = e_hours + e_minutes/60
            # label = 'Peak-Periods' if element['idx'] == 1 else ''
            ax1.axvline(x=e_total_hours, color='purple', linewidth=2.5, linestyle='--')
            

    # Right axis: Cumulative speed pattern
    ax1.plot(time_slot_hour, df['speed'], color='green', linewidth=1, label='Speed')
    ax1.set_ylim(0,85)
    ax1.set_yticks(np.arange(0, 85 + 1, 10))  # Ticks at 0, 20, 40, 60, 80
    # Set y-axis tick label color
    ax1.tick_params(axis='y', colors='black')
    # Set y-axis spine (axis line) color
    ax1.spines['left'].set_color('green')

    time_slot_hour_re = [0] + time_slot_hour.to_list()
    cumsum_speed_re = [0] + df['cumsum_speed'].to_list()

    ax2 = ax1.twinx()
    ax2.plot(time_slot_hour_re, cumsum_speed_re, color='blue', linewidth=1, label='Cumulative speed')
    ax2.set_ylabel('Cumulative Speed (miles)',fontsize=16, color='blue')
    ax2.set_ylim(0, 1600)
    ax2.set_yticks(np.arange(0, 1600 + 1, 200)) 
    # Set y-axis tick label color
    ax2.tick_params(axis='y', colors='blue')
    # Set y-axis spine (axis line) color
    ax2.spines['right'].set_color('blue')

    # Handle legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left',fontsize=15)

    fig.tight_layout()
    plt.savefig(f'./{working_f}/02 fig/16 PELT/All_{purpose}_{VDS_num}_{date}_{aggregate_timeframe}.png')
    # plt.show()  # Uncomment if you want to display the plot

# +
with open(f"./{working_f}/set_peak_period_{VDS_num_analyze}_{aggregate_timeframe}_pelt.p",'rb') as file:
        peak_list_PELT = pickle.load(file)

with open(f"./{working_f}/set_peak_period_{VDS_num_analyze}_{aggregate_timeframe}_RDP_v.p",'rb') as file:
    peak_list_RDP = pickle.load(file)

with open(f"./{working_f}/set_peak_period_{VDS_num_analyze}_{aggregate_timeframe}_pelt_directpeak.p",'rb') as file:
    peak_list_PELT_direct = pickle.load(file)


for i,file_name in enumerate(samples_file_list):
    date = samples_file_list[i].split('_')[1].split('.')[0]
    
    rawdata, gfactor, date = load_raw(file_name, config_v2)
    
    if skip_if_missing(rawdata, config_v2):
        continue

    traffic, plot_date = load_or_aggregate(rawdata, date, config_v2)
    
    traffic = highfreeflowspeed_conversion(traffic, config_v2)
    traffic = interpolate_missing(traffic, config_v2)
    traffic = assign_fixedtime_peaks(traffic, config_v2)
    traffic["cumsum_speed"] = traffic['speed'].cumsum() * aggregate_timeframe / 60

    peak_list_PELT.columns = ['idx','date','peak_list']
    peak_list_RDP.columns = ['idx','date','peak_list']
    peak_list_PELT_direct.columns = ['idx','date','peak_list']

    PELT_plot_all(traffic, date, VDS_num_analyze, aggregate_timeframe, peak_list_PELT, peak_list_RDP, peak_list_PELT_direct, purpose)
# -

# ## BPR calibration result

# **Discussion 9/9**
# - We have talked about RDP shows more consistent results
# - I also compared the groundtruth result based on my personal view
# - BPR calibration 

# ### Version1: natural log of average flow-rate

# - $z(r)=\zeta(1+\alpha r^\beta)$
#     - $\zeta$: free-flow traveltimes (min/mile)
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} q^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC/T)^\beta}$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(q)$
# - $y_n = ln(\tilde{\alpha})+\beta x_n$
#     - $y_n = ln(\frac{z(r)}{\zeta}-1)$
#     - $x_n = ln(q)$

# <img src='./01_BPR/02_1_presentation_fig/BPR_calibration_v1.png' width=60%>

# - The shape is not what we have expected: invervse relationship.
# - As average flow increases, travel time decreases.
# - The parameter $\beta$ takes a negative value.
#     - $q=\frac{D}{LT}$ where $D$ is the total travel distance (miles) and $L$ is lane-miles, and $T$ is peak period length.
#     - It is reasonable to assume that the peak period length $T$ increases with the demand level.
#         - Higher demand level could lead to a lower average flow-rate 
#     - Therefore, $q$ cannot be used to represent the demand level.

# <img src='./01_BPR/02_1_presentation_fig/BPR_variable_distribution.png' width=60%>

# - As the congestion period gets longer, the average flow rate decreases, while the average travel time increases.
# - The buildup and dissipation durations remain roughly the same, regardless of how long the total congestion lasts.
# - This means that the core of the peak period—the most congested part—becomes longer as the congestion extends.
# - As a result, average travel times rise, and average flow rates fall.

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### fitting method: 
# -

# Minimize the **Sum of Squared Residuals (SSR)**:
# $SSR(b_0, b_1) = \sum_{i=1}^{n} \left[ y_i - (b_0 + b_1 x_i) \right]^2$
#
# - Step 1: Compute Means: $\bar{x} = \frac{1}{n} \sum_{i=1}^n x_i, \quad \bar{y} = \frac{1}{n} \sum_{i=1}^n y_i$
# - Step 2: Minimize SSR by Partial Derivatives
#     - **Partial w.r.t. $b_0$:** $\sum_{i=1}^n (y_i - b_0 - b_1 x_i) = 0 \Rightarrow b_0 = \bar{y} - b_1 \bar{x}$
#     - **Partial w.r.t. $b_1$:** $\sum_{i=1}^n x_i (y_i - b_0 - b_1 x_i) = 0$
#     - Substitute $b_0 = \bar{y} - b_1 \bar{x}$, expand and simplify:
# - Step 3: Define Variance Terms:
#     - $S_{xy} = \sum (x_i - \bar{x})(y_i - \bar{y}) = \sum x_i y_i - n \bar{x} \bar{y}$
#     - $S_{xx} = \sum (x_i - \bar{x})^2 = \sum x_i^2 - n \bar{x}^2$
# - Final OLS Estimates
#     - $b_1 = \frac{S_{xy}}{S_{xx}}, \quad b_0 = \bar{y} - b_1 \bar{x}$

# **Parameter Estimation Method: Levenberg–Marquardt Algorithm**
# - The model parameters $a,b$ are estimated by **nonlinear least squares** using the Levenberg–Marquardt (LM) algorithm.
#     - LM minimizes the sum of squared residuals: $S(\theta) = \sum_{i=1}^{n} \big[y_i - f(x_i;\theta)\big]^2$
# - At each iteration $k$, the parameter update is:$(J^\top J + \lambda I)\Delta\theta = J^\top r, \quad \theta_{k+1} = \theta_k + \Delta\theta$
#     - where $r = y - f(x;\theta_k)$ is the residual vector, $J$ is the Jacobian, and $\lambda$ is a damping factor.  
# - LM interpolates between **gradient descent** (large $\lambda$) and **Gauss–Newton** (small $\lambda$), ensuring both stability and fast convergence.
#

# + [markdown] jp-MarkdownHeadingCollapsed=true
# ### Version2: natural log of total demand
# -

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} (Tq)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tq$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - $y_n = ln(\tilde{\alpha})+\beta x_n$

# - $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}= \frac{0.15}{(2*2200)^4}=3.4*10^{-5}$
#     - $\alpha=0.15, W=2 \text{hours}, C=2200\text{vphpl}, \beta=4$
# - it is hard to calibrate the $\alpha$, having a positive value.

# <img src='./01_BPR/02_1_presentation_fig/BPR_calibration_v2.png' width=70%>

# ### Version3: inverse natural log of total demand

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} (Tq)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tq$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - $-ln(\frac{z(r)}{\zeta}-1)=-ln(\tilde{\alpha})-\beta ln(N)$
# - $ln((\frac{z(r)}{\zeta}-1)^{-1})=ln(\frac{1}{\tilde{\alpha}})  -\beta ln(N)$

# - Calibration result
#     - $\zeta = 1min/mile (60mph)$
#     - W=1.5hours
#     - C=2200vphpl
#
# |            | SR-91 Morning | SR-91 Afternoon | I-5 Morning (1205583) |
# |------------|---------------|-----------------|-------------|
# | alpha'_hat | 0.60          | 2.54            | 3.81        |
# | beta_hat   | 0.12          | 0.33            | 0.63        |
# | alpha_hat  | 1.46          | 1.13            | 3.70        |

# #### Previous note

# <div class="alert alert-danger">
#
# **BPR function fitting (2025/9/15 이전)**
# - VDS: 1205583 (I-5)
# - <img src='./01_BPR/02_1_presentation_fig/BPR_VDS1205583.png' width=10%>
# - VDS: 1203506 (SR-91)
# - <img src='./01_BPR/02_1_presentation_fig/BPR_VDS1203506_bothperiods.png' width=10%>
# - <img src='./01_BPR/02_1_presentation_fig/BPR_VDS1203506_mor.png' width=10%>

# + [markdown] jp-MarkdownHeadingCollapsed=true
#
# <div class="alert alert-danger">
# - *I need to eliminate the off-peak data
# - Case 1 (speed-threshold-based) shows the most typical BPR curve shape.
# - We need to consider the reason behind this difference.
#     - One possible explanation is that during the peak period, speed drops sharply unlike the theoretical triangular shape of congestion cost.
#     - As a result, there's little incentive to shift arrival times within the peak period, since congestion levels remain similarly high.
#     - Therefore, some individuals whose preferred arrival time falls within the peak period (W) tend to avoid it altogether and travel right next to the speed drop. In this case, it's important to fully capture the peak period—up until speeds return to free-flow conditions
# - If Case 1 is found to be more meaningful, we should develop a method using Cases 2, 3, and 4 that captures a similarly broad range—
#     - since Cases 2, 3, and 4 are methodologically more robust.
#     - Case 2,3,4 shows simliar to entire-day case.

# + [markdown] jp-MarkdownHeadingCollapsed=true
# <img src='./01_BPR/02_1_presentation_fig/Speedbased_method_BPR_comparison.png' width=10%>
# -

# <img src='./01_BPR/02_1_presentation_fig/BPR_calibration_v3.png' width=90%>

# <img src='./01_BPR/02_1_presentation_fig/BPR_calibration_v4.png' width=30%>

# ### Trials for model fitting improvment (e.g., R-squared)

# #### Measures for model fitting

# **Coefficient of determination($R^2$)**: $R^2=\frac{\mathrm{SSR}}{\mathrm{SST}}=\frac{\sum(\hat y_i-\bar y)^2}{\sum(y_i-\bar y)^2} =\frac{\sum(\hat\beta_1(x_i-\bar x))^2}{\sum(y_i-\bar y)^2}=\hat\beta_1^{\,2}\frac{\,S_{xx}}{S_{yy}}$, where $\hat\beta_1=\frac{S_{xy}}{S_{xx}}$
# - this is about explanatory power 
# - measures the proportion of variance in y that is explained by the regression model (compared to just using $\bar{y}$). 
# - In our case, the beta is near to zero, so the impact of x ($ln(N)$) to y($ln((\frac{z(r)}{\zeta}-1)^{-1})$) is low.
# - For the predictive fit(How close are my predictions to reality), error-based metric such as RMSE can be used.
#     - $\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2}$
#     - $\text{MAPE} = \frac{100}{n} \sum_{i=1}^n |\frac{y_i - \hat{y_i}}{y_i}|$

# + [markdown] jp-MarkdownHeadingCollapsed=true
# **Derivation of the OLS Intercept**
# -

# - $\hat\beta_0 = \bar y - \hat\beta_1 \bar x.$x
#
# $\text{SSE} = \sum_{i=1}^n (y_i - \hat y_i)^2
# = \sum_{i=1}^n (y_i - \hat\beta_0 - \hat\beta_1 x_i)^2.$
#
# ---
# $\frac{\partial \text{SSE}}{\partial \hat\beta_0} = -2 \sum (y_i - \hat\beta_0 - \hat\beta_1 x_i) = 0$
# $\frac{\partial \text{SSE}}{\partial \hat\beta_1} = -2 \sum x_i (y_i - \hat\beta_0 - \hat\beta_1 x_i) = 0.$
#
# This gives two **normal equations**:
# $\sum (y_i - \hat\beta_0 - \hat\beta_1 x_i) = 0 \quad \tag{Eq. 1}$
# $\sum x_i (y_i - \hat\beta_0 - \hat\beta_1 x_i) = 0 \quad \tag{Eq. 2}$
#

# #### How to increase model fitting

# ##### 1) Removing days with multiple congested periods within one fixed-time congested window
# - The number of dates before and after filtering
# - |            | SR-91  | I-5 |
# |------------|---------------|-----------------|
# | before_filter |   300       |     230      |
# | after_filter   | 266          | 230           |
# | \|before-after\|  | 34        | 0          |

# - RMSE: small more fit ⟷ R-squared: small less fit
# <img src='./01_BPR/02_1_presentation_fig/BPR_calibration_v3_beforeafter.png' width=100%>

# |            | SR-91 Morning | SR-91 Afternoon | I-5 Morning (1205583) |
# |------------|---------------|-----------------|-------------|
# | alpha_hat  | 1.45          | 1.12            | 3.61        |
# | beta_hat   | 0.07          | 0.22            | 0.63        |
#
# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} (Tq)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tq$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - $-ln(\frac{z(r)}{\zeta}-1)=-ln(\tilde{\alpha})-\beta ln(N)$
# - $ln((\frac{z(r)}{\zeta}-1)^{-1})=ln(\frac{1}{\tilde{\alpha}})  -\beta ln(N)$

# ##### 2) Free-flow speeds adjustment
# - both of them median value is 67mph.
#     - apply fixed value as 70mph
#     - Apply day-dependent freeflowspeed: $ln((\frac{z(r)}{\zeta(r)}-1)^{-1})=ln(\frac{1}{\tilde{\alpha}})  -\beta ln(N)$, but no significant difference 

# <img src='./01_BPR/02_1_presentation_fig/Freeflow_speed_dist.png' width=90%>

# ### daily-basis BPR function estimate

# #### daily average flowrate

# <img src='./01_BPR/02_1_presentation_fig/BPR_daily average flow.png' width=80%>

# #### Jin (2025): weighted average of ideal arrival time window

# - $z/\zeta = 1+\alpha (\frac{N}{lC\tilde{W}})^\beta$
#     - $\xi_j=\frac{D_j}{D}$, where $D=\sum_{j=1}^J D_j$
#     - $z = \sum_{j=1}^J \xi_j z_j$
#     - $\sum_{j=1}^J \frac{\xi_j^{\beta+1}}{W_j^\beta}=\frac{1}{\tilde{W}^\beta}$
#         - $\tilde{W}=(\frac{1}{\sum_{j=1}^J \frac{\xi_j^{\beta+1}}{W_j^\beta}})^{1/\beta}$ 

# - $W_1=W_2=1\text{hours}$, $W_3=\infty$
# - $\beta = 4$

# - higher R-sqaured
# <img src='./01_BPR/02_1_presentation_fig/BPR_daily_jin_2025.png' width=100%>

# ### Add location

# - VDS1214006: Next to VDS: 1205883 (I-5)
#     - 2011.Jan~2011.June
#     - having days with congested period: 
# - <img src='./01_BPR/02_1_presentation_fig/VDS1205583.png' width=90%>

# <img src='./01_BPR/02_1_presentation_fig/BPR_1214006.png' width=40%>

# |            | SR-91 Morning | SR-91 Afternoon | I-5 Morning (1205583) | I-5 Morning(1214006)|
# |------------|---------------|-----------------|-------------|-------------|
# | alpha_hat  | 1.45          | 1.12            | 3.61        |4.91 |
# | beta_hat   | 0.07          | 0.22            | 0.63        |0.61 |
#
#
#
# - The parameter value shows near known BPR parameter

# ### (Code) BPR fitting

# #### (Version1) ln(Avgflow)-ln(traveltimes)

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} q^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC/T)^\beta}$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(q)$
# - $y_n = ln(\tilde{\alpha})+\beta x_n$
#

# +
import math

# Step 0: Input!!!
free_traveltime =  60*1/70
# 1203506, 1205583
VDS_num = 1203506
# VDS_num = 1205583
method = 'RDP_v'
version = 'filtered'

# 'wholeday', 'peak'
temporal_scope = 'wholeday'

## "entireday", "peak" "hour" "speedbasedpeak"
file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}_{temporal_scope}_{version}.csv"
### 'dayofweek', 'year', 'period'
label_criterion = 'period'

## write down not inclue values
dayofweek_notinclude = []
month_notinclude = []
year_notinclude = []

period_include = ['afternoon-peak']
# 'morning-peak', 'afternoon-peak'

# Step 1: data read
c_daily_traffic = pd.read_csv(file_path)
c_daily_traffic['date'] = c_daily_traffic['date'].astype(str)
c_daily_traffic['month'] = c_daily_traffic['date'].str.slice(0, 4)

# Step 3: column add
c_daily_traffic['ln_avg_flow'] = np.log(c_daily_traffic['avg_flow'])

c_daily_traffic['ln_t_tau'] = np.log(c_daily_traffic['traveltimes'] / free_traveltime - 1)
c_daily_traffic['inv_ln_t_tau'] = np.log(1/(c_daily_traffic['traveltimes'] / free_traveltime - 1))

# c_daily_traffic.to_csv(f"./{working_f}/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}.csv")

# Step 4: data filtering
## Step 3-1: off-/peak- period
c_daily_traffic = c_daily_traffic[c_daily_traffic['division'] != -1]

## Step 4-2: notinclude
c_daily_traffic = c_daily_traffic[~c_daily_traffic['dayofweek'].isin(dayofweek_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['month'].isin(month_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['year'].isin(year_notinclude)]

c_daily_traffic = c_daily_traffic[c_daily_traffic['period'].isin(period_include)]

# +
# Ensure day is categorical with ordered days
day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
c_daily_traffic['dayofweek'] = pd.Categorical(c_daily_traffic['dayofweek'], categories=day_order, ordered=True)
c_daily_traffic_day = c_daily_traffic.groupby(label_criterion)

# Step 3: Create a scatter plot for 'flow' vs 'time'
fig, ax = plt.subplots(1, 1, figsize=(7.5, 5))
plt.legend()

for name, group in c_daily_traffic_day:

    ax.plot(group["ln_avg_flow"], group["ln_t_tau"] , marker="o", linestyle="", label=f"{name}")

    x = group["ln_avg_flow"].to_numpy()
    y = group["ln_t_tau"].to_numpy()

    # Fit: y = b0 + b1*x
    b1, b0 = np.polyfit(x, y, 1)  # returns slope, intercept

    # Make a smooth line across the observed range
    x_line = np.linspace(x.min(), x.max(), 200)
    y_line = b0 + b1 * x_line
    ax.plot(x_line, y_line, linewidth=2, label=f"Fit: y = {b0:.3f} + {b1:.3f}x")

    # Optional: show R² in the legend
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    ax.legend(title=f"R² = {r2:.3f}")


# ax.scatter(c_daily_traffic["flow"], c_daily_traffic["traveltimes"])
ax.set_title(f'BPR parameter calibration at VDS {VDS_num} ({method} congestion detection)')
ax.set_ylabel(r'$ln\left(\frac{z(r)}{\zeta}-1\right)$', fontsize=13)
ax.set_xlabel(r'$ln(q)$: Natural log of average flow-rate in congested period', fontsize=13)
ax.grid(True)
# ax.set_xlim(, 7.5)
# ax.set_ylim(0,2.4)
# ax.legend(title=f'{label_criterion}')

# Save and Display the plot
plt.savefig(f'./{working_f}/02 fig/12 Daily BPR/BPR_calibration_v1_{VDS_num})_labeled by_{label_criterion}_with_{year_notinclude}{period_include}_{method}.png')
# plt.show()
# -

# #### (Version2) ln(traveldemand)-ln(traveltimes)

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} (Tq)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tq$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - $y_n = ln(\tilde{\alpha})+\beta x_n$

# +
import math

# Step 0: Input!!!
free_traveltime =  60*1/70
# 1203506, 1205583
VDS_num = 1203506
# VDS_num = 1205583
method = 'RDP_v'
version = 'filtered'

# 'wholeday', 'peak'
temporal_scope = 'wholeday'

## "entireday", "peak" "hour" "speedbasedpeak"
file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}_{temporal_scope}_{version}.csv"

### 'dayofweek', 'year', 'period'
label_criterion = 'period'

## write down not inclue values
dayofweek_notinclude = []
year_notinclude = []
month_notinclude = []

period_include = ['afternoon-peak']
# 'morning-peak', 'afternoon-peak'

# Step 1: data read
c_daily_traffic = pd.read_csv(file_path)
c_daily_traffic['date'] = c_daily_traffic['date'].astype(str)
c_daily_traffic['month'] = c_daily_traffic['date'].str.slice(0, 4)

# Step 1-2: filtering ununusual pattern
last_col = c_daily_traffic.columns[-1]
c_daily_traffic = c_daily_traffic[c_daily_traffic[last_col] != False]

# Step 2: column add
c_daily_traffic['ln_avg_flow'] = np.log(c_daily_traffic['avg_flow'])

c_daily_traffic['ln_totaldemand'] = np.log(c_daily_traffic['totaldemand']) 
c_daily_traffic['inv_ln_totaldemand'] = np.log(1/c_daily_traffic['totaldemand']) 

c_daily_traffic['ln_t_tau'] = np.log(c_daily_traffic['traveltimes'] / free_traveltime - 1)
c_daily_traffic['inv_ln_t_tau'] = np.log(1/(c_daily_traffic['traveltimes'] / free_traveltime - 1))

# c_daily_traffic.to_csv(f"./{working_f}/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}.csv")

# Step 3: data filtering
## Step 3-1: off-/peak- period
c_daily_traffic = c_daily_traffic[c_daily_traffic['division'] != -1]

## Step 3-2: notinclude
c_daily_traffic = c_daily_traffic[~c_daily_traffic['year'].isin(year_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['dayofweek'].isin(dayofweek_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['month'].isin(month_notinclude)]

c_daily_traffic = c_daily_traffic[c_daily_traffic['period'].isin(period_include)]

# +
# Ensure day is categorical with ordered days
day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
c_daily_traffic['dayofweek'] = pd.Categorical(c_daily_traffic['dayofweek'], categories=day_order, ordered=True)
c_daily_traffic_day = c_daily_traffic.groupby(label_criterion)

# Step 3: Create a scatter plot for 'flow' vs 'time'
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
plt.legend()

for name, group in c_daily_traffic_day:

    ax.plot(group["ln_totaldemand"], group["ln_t_tau"] , marker="o", linestyle="", label=f"{name}")
    # ax.plot(group["ln_totaldemand"], group["ln_t_tau"] , marker="o", linestyle="", label=f"{name}")

    x = group["ln_totaldemand"].to_numpy()
    y = group["ln_t_tau"].to_numpy()

    # Fit: y = b0 + b1*x
    b1, b0 = np.polyfit(x, y, 1)  # returns slope, intercept

    # Make a smooth line across the observed range
    x_line = np.linspace(x.min(), x.max(), 200)
    y_line = b0 + b1 * x_line
    ax.plot(x_line, y_line, linewidth=2, label=f"Fit: y = {b0:.3f} + {b1:.3f}x")

    # Optional: show R² in the legend
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    ax.legend(title=f"R² = {r2:.3f}")


# ax.scatter(c_daily_traffic["flow"], c_daily_traffic["traveltimes"])
ax.set_title(f'BPR parameter calibration at VDS {VDS_num} ({method} congestion detection)')
ax.set_ylabel(r'$ln\left(\frac{z(r)}{\zeta}-1\right)$', fontsize=13)
ax.set_xlabel(r'$ln(Tq)$: Natural log of total volume in congested period', fontsize=13)
ax.grid(True)
# ax.set_xlim(6, 8.5)
# ax.set_ylim(0,2.4)
# ax.legend(title=f'{label_criterion}')

# Save and Display the plot
plt.savefig(f'./{working_f}/02 fig/12 Daily BPR/BPR_calibration_v2_{VDS_num})_labeled by_{label_criterion}_with_{year_notinclude}{period_include}.png')

# plt.show()

# +
## "entireday", "peak" "hour" "speedbasedpeak"
f_period = period_include[0]
c_daily_traffic_filter = c_daily_traffic[c_daily_traffic['period']==f_period]

fig, ax = plt.subplots(1,3,figsize=(18,4))
# ax.plot(c_daily_traffic_filter['duration'],c_daily_traffic_filter['avg_flow'], marker="o", linestyle="", label=f"{f_period}")
ax[0].hist(c_daily_traffic_filter['duration']/60, bins=20, edgecolor='black')
ax[1].plot(c_daily_traffic_filter['duration']/60,c_daily_traffic_filter['avg_flow'], marker="o", linestyle="", label=f"{f_period}")
ax[2].plot(c_daily_traffic_filter['duration']/60,c_daily_traffic_filter['traveltimes'], marker="o", linestyle="", label=f"{f_period}")


fig.suptitle(f'Variable distributions at VDS {VDS_num} during {period_include[0]} ({method})', fontsize=15)

for i in range(0,3):
    ax[i].set_xlabel('Congested period duration (hour)', fontsize=13)
    ax[i].set_xlim(0, c_daily_traffic_filter['duration'].max()/60)
    ax[i].set_xticks(range(0, int(c_daily_traffic_filter['duration'].max()/60)+1, 1))

ax[0].set_ylabel('Frequency', fontsize=13)
ax[1].set_ylabel(r'Avg flow rate ($q$, vphpl)', fontsize=13)
ax[2].set_ylabel(r'Avg travel time ($z(r)$, min/mile)', fontsize=13)

plt.savefig(f'./{working_f}/02 fig/12 Daily BPR/Variable distributions at VDS {VDS_num} during {period_include[0]}({method}).png')

plt.show()

# +
# Ensure day is categorical with ordered days
day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
c_daily_traffic['dayofweek'] = pd.Categorical(c_daily_traffic['dayofweek'], categories=day_order, ordered=True)

c_daily_traffic_day = c_daily_traffic.groupby(label_criterion)

# Step 3: Create a scatter plot for 'flow' vs 'time'
fig, ax = plt.subplots(1, 1, figsize=(9, 6))

for name, group in c_daily_traffic_day:
    ax.plot(group["totaldemand"], group["avg_flow"] , marker="o", linestyle="", label=f"{name}")
    
# ax.scatter(c_daily_traffic["flow"], c_daily_traffic["traveltimes"])
plt.legend()
ax.set_title(f'Demand and Travel Times at VDS {VDS_num} ({config['aggregate_timeframe']}min, {method} method)')
ax.set_ylabel('Average flow (vph)', fontsize=13)
ax.set_xlabel('total_demand (Vehs)', fontsize=13)
ax.grid(True)
# ax.set_xlim(0, 1700)
# ax.set_ylim(0,1300)
# ax.legend(title=f'{label_criterion}')
# -

# #### (Version3) Inverse ln(Avgdemand) vs ln(traveltimes)

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} (Tq)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tq$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - $-ln(\frac{z(r)}{\zeta}-1)=-ln(\tilde{\alpha})-\beta ln(N)$
# - $ln((\frac{z(r)}{\zeta}-1)^{-1})=ln(\frac{1}{\tilde{\alpha}})  -\beta ln(N)$

# +
import math

# Step 0: Input!!!
free_traveltime =  60*1/70
# 1203506, 1205583
# VDS_num = 1203506
VDS_num = 1205583
# VDS_num = 1214006
method = 'RDP_v'
# version = '_filtered'
version = ''

# 'wholeday', 'peak'
temporal_scope = 'peak'

## "entireday", "peak" "hour" "speedbasedpeak"
file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}_{temporal_scope}{version}.csv"
### 'dayofweek', 'year', 'period'
label_criterion = 'period'

## write down not inclue values
dayofweek_notinclude = []
year_notinclude = []
month_notinclude = []

period_include = ['morning-peak']
# 'morning-peak', 'afternoon-peak'

# Step 1: data read
c_daily_traffic = pd.read_csv(file_path)
c_daily_traffic['date'] = c_daily_traffic['date'].astype(str)
c_daily_traffic['month'] = c_daily_traffic['date'].str.slice(0, 4)

# Step 1-2: filtering ununusual pattern
last_col = c_daily_traffic.columns[-1]
c_daily_traffic = c_daily_traffic[c_daily_traffic[last_col] != False]

# Step 2: column add
c_daily_traffic['ln_avg_flow'] = np.log(c_daily_traffic['avg_flow'])

c_daily_traffic['ln_totaldemand'] = np.log(c_daily_traffic['totaldemand']) 
c_daily_traffic['inv_ln_totaldemand'] = np.log(1/c_daily_traffic['totaldemand']) 

c_daily_traffic['ln_t_tau'] = np.log(c_daily_traffic['traveltimes'] / free_traveltime - 1)
c_daily_traffic['inv_ln_t_tau'] = np.log(1/(c_daily_traffic['traveltimes'] / free_traveltime - 1))

# c_daily_traffic.to_csv(f"./{working_f}/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}.csv")

# Step 3: data filtering
## Step 3-1: off-/peak- period
c_daily_traffic = c_daily_traffic[c_daily_traffic['division'] != -1]

## Step 3-2: notinclude
c_daily_traffic = c_daily_traffic[~c_daily_traffic['year'].isin(year_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['dayofweek'].isin(dayofweek_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['month'].isin(month_notinclude)]

c_daily_traffic = c_daily_traffic[c_daily_traffic['period'].isin(period_include)]

# +
# Ensure day is categorical with ordered days
day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
c_daily_traffic['dayofweek'] = pd.Categorical(c_daily_traffic['dayofweek'], categories=day_order, ordered=True)
c_daily_traffic_day = c_daily_traffic.groupby(label_criterion)

# Step 3: Create a scatter plot for 'flow' vs 'time'
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
plt.legend()

for name, group in c_daily_traffic_day:

    ax.plot(group["ln_totaldemand"], group["inv_ln_t_tau"] , marker="o", linestyle="", label=f"{name}")
    # ax.plot(group["ln_totaldemand"], group["ln_t_tau"] , marker="o", linestyle="", label=f"{name}")

    x = group["ln_totaldemand"].to_numpy()
    y = group["inv_ln_t_tau"].to_numpy()

    # Fit: y = b0 + b1*x
    b1, b0 = np.polyfit(x, y, 1)  # returns slope, intercept

    # Make a smooth line across the observed range
    x_line = np.linspace(x.min(), x.max(), 200)
    y_line = b0 + b1 * x_line

    # Optional: show R² in the legend
    # Predictions for the observed x
    y_hat = b0 + b1 * x

    # --- RMSE calculation ---
    rmse = np.sqrt(np.mean((y - y_hat) ** 2))
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    
    ax.plot(x_line, y_line, linewidth=2, label=f"Fit: y = {b0:.3f} + {b1:.3f}x (R^2: {r2:.2f}, RMSE: {rmse:.2f})")
    ax.legend()

    
# ax.scatter(c_daily_traffic["flow"], c_daily_traffic["traveltimes"])
ax.set_title(f'BPR parameter calibration at VDS {VDS_num} ({method} congestion detection)')
ax.set_ylabel( r'$ln\left(\frac{z(r)}{\zeta}-1\right)^{-1}$', fontsize=13)
ax.set_xlabel(r'$ln(Tq)$: Natural log of total volume in congested period', fontsize=13)
ax.grid(True)

ax.set_xlim(6.25, 8.25)
# ax.set_xlim(6.25, 8.25)
ax.set_ylim(-2,1.5)
# ax.legend(title=f'{label_criterion}')

# Save and Display the plot
plt.savefig(f'./{working_f}/02 fig/12 Daily BPR/BPR_calibration_v3_{VDS_num})_labeled by_{label_criterion}_with_{year_notinclude}{period_include}{version}.png')
# plt.show()

# +
temporal_scale = 'speedbasedpeak'
# c_daily_traffic = pd.read_csv(file_path)

# c_daily_traffic[(c_daily_traffic['date']== 111012)].sort_values(by='date', ascending=True)
# c_daily_traffic[(c_daily_traffic['flow']>2500)].sort_values(by='date', ascending=True)
# c_daily_traffic[(c_daily_traffic['totaldemand']>1200) & (c_daily_traffic['traveltimes']<1.5)].sort_values(by='date', ascending=True)
# c_daily_traffic[(c_daily_traffic['period']== 'afternoon-peak')].sort_values(by='date', ascending=True)

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### (version4) speed dependent 
# -

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} (Tq)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tq$
# - $ln(\frac{z(r)}{\zeta(r)}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - $-ln(\frac{z(r)}{\zeta(r)}-1)=-ln(\tilde{\alpha})-\beta ln(N)$
# - $ln((\frac{z(r)}{\zeta(r)}-1)^{-1})=ln(\frac{1}{\tilde{\alpha}})  -\beta ln(N)$

# +
import math

# Step 0: Input!!!
free_traveltime =  60*1/70
# 1203506, 1205583
# VDS_num = 1203506
# VDS_num = 1205583
VDS_num = 1214006

method = 'RDP_v'
version = 'filtered'

# 'wholeday', 'peak'
temporal_scope = 'peak'

## "entireday", "peak" "hour" "speedbasedpeak"
file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}_{temporal_scope}_{version}.csv"
### 'dayofweek', 'year', 'period'
label_criterion = 'period'

## write down not inclue values
dayofweek_notinclude = []
year_notinclude = []
month_notinclude = []

period_include = ['morning-peak']
# 'morning-peak', 'afternoon-peak'

# Step 1: data read
c_daily_traffic = pd.read_csv(file_path)
c_daily_traffic['date'] = c_daily_traffic['date'].astype(str)
c_daily_traffic['month'] = c_daily_traffic['date'].str.slice(0, 4)

# +
# Build a dictionary of {date: traveltime at off-peak}
free_tt_map = (
    c_daily_traffic[c_daily_traffic['period'] == 'off-peak']
    .set_index('date')['traveltimes']
    .to_dict()
)

# Map it back to all rows by date
c_daily_traffic['free_traveltime'] = c_daily_traffic['date'].map(free_tt_map)


# Step 2: column add
c_daily_traffic['ln_avg_flow'] = np.log(c_daily_traffic['avg_flow'])

c_daily_traffic['ln_totaldemand'] = np.log(c_daily_traffic['totaldemand']) 
c_daily_traffic['inv_ln_totaldemand'] = np.log(1/c_daily_traffic['totaldemand']) 

c_daily_traffic['ln_t_tau'] = np.log(c_daily_traffic['traveltimes'] / c_daily_traffic['free_traveltime'] - 1)
c_daily_traffic['inv_ln_t_tau'] = np.log(1/(c_daily_traffic['traveltimes'] / c_daily_traffic['free_traveltime'] - 1))

# c_daily_traffic.to_csv(f"./{working_f}/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}.csv")

# Step 3: data filtering
## Step 3-1: off-/peak- period
c_daily_traffic = c_daily_traffic[c_daily_traffic['division'] != -1]

## Step 3-2: notinclude
c_daily_traffic = c_daily_traffic[~c_daily_traffic['year'].isin(year_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['dayofweek'].isin(dayofweek_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['month'].isin(month_notinclude)]

c_daily_traffic = c_daily_traffic[c_daily_traffic['period'].isin(period_include)]

# +
# Ensure day is categorical with ordered days
day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
c_daily_traffic['dayofweek'] = pd.Categorical(c_daily_traffic['dayofweek'], categories=day_order, ordered=True)
c_daily_traffic_day = c_daily_traffic.groupby(label_criterion)

# Step 3: Create a scatter plot for 'flow' vs 'time'
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
plt.legend()

for name, group in c_daily_traffic_day:

    ax.plot(group["ln_totaldemand"], group["inv_ln_t_tau"] , marker="o", linestyle="", label=f"{name}")
    # ax.plot(group["ln_totaldemand"], group["ln_t_tau"] , marker="o", linestyle="", label=f"{name}")

    x = group["ln_totaldemand"].to_numpy()
    y = group["inv_ln_t_tau"].to_numpy()

    # Fit: y = b0 + b1*x
    b1, b0 = np.polyfit(x, y, 1)  # returns slope, intercept

    # Make a smooth line across the observed range
    x_line = np.linspace(x.min(), x.max(), 200)
    y_line = b0 + b1 * x_line
    ax.plot(x_line, y_line, linewidth=2, label=f"Fit: y = {b0:.3f} + {b1:.3f}x")

    # Optional: show R² in the legend
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    ax.legend(title=f"R² = {r2:.3f}")


# ax.scatter(c_daily_traffic["flow"], c_daily_traffic["traveltimes"])
ax.set_title(f'BPR parameter calibration at VDS {VDS_num} ({method} congestion detection)')
ax.set_ylabel( r'$ln\left(\frac{z(r)}{\zeta}-1\right)^{-1}$', fontsize=13)
ax.set_xlabel(r'$ln(Tq)$: Natural log of total volume in congested period', fontsize=13)
ax.grid(True)
# ax.set_xlim(6, 8.5)
# ax.set_ylim(0,2.4)
# ax.legend(title=f'{label_criterion}')

# Save and Display the plot
plt.savefig(f'./{working_f}/02 fig/12 Daily BPR/BPR_calibration_v4_{VDS_num})_labeled by_{label_criterion}_with_{year_notinclude}{period_include}.png')
# plt.show()

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### (Version5) total demand with time-window size
# -

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $r=\frac{N}{lCW}=\frac{N/l}{CW}$

# +
temporal_scale = 'speedbasedpeak'
# VDS_num = 1205583
VDS_num = 1203506
# VDS_num = 1214006

method = 'RDP_v'
version = 'filtered'
# 'wholeday', 'peak'
temporal_scope = 'wholeday'

file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}_{temporal_scope}_{version}.csv"

# +
## write down not inclue values
dayofweek_notinclude = []
year_notinclude = []
month_notinclude = []

period_include = ['afternoon-peak']
# 'morning-peak', 'afternoon-peak'

c_fixed = 2200 # fixed value
W = 120/60

# Step 1: data read
c_daily_traffic = pd.read_csv(file_path)


### new column
c_daily_traffic['date'] = c_daily_traffic['date'].astype(str)
c_daily_traffic['month'] = c_daily_traffic['date'].str.slice(0, 4)
# Step 2: column
# total demand from peak period to the average flow depending on the size of 'heart of peak period'
# heart of peak period(W): minutes

c_daily_traffic.loc[(c_daily_traffic['division'] == 0),'avgdemand'] = c_daily_traffic.loc[(c_daily_traffic['division'] == 0),'totaldemand']
c_daily_traffic.loc[(c_daily_traffic['division'] != 0),'avgdemand'] = c_daily_traffic.loc[(c_daily_traffic['division'] != 0),'totaldemand'] / (W)

# c_daily_traffic.to_csv(f"./{working_f}/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}.csv")

# Step 3: data filtering
## Step 3-1: off-/peak- period
c_daily_traffic = c_daily_traffic[c_daily_traffic['division'] != -1]

## Step 3-2: notinclude
c_daily_traffic = c_daily_traffic[~c_daily_traffic['year'].isin(year_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['dayofweek'].isin(dayofweek_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['month'].isin(month_notinclude)]

c_daily_traffic = c_daily_traffic[c_daily_traffic['period'].isin(period_include)]

print(c_daily_traffic.head())

# +
from scipy.optimize import curve_fit  
# Ensure day is categorical with ordered days

day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
c_daily_traffic['dayofweek'] = pd.Categorical(c_daily_traffic['dayofweek'], categories=day_order, ordered=True)
c_daily_traffic_day = c_daily_traffic.groupby(label_criterion)

def model_func(x, a, b, c, w):
    t_0 = 1/70 * 60 
    return t_0 * (1 + a * (x / (c*w)) ** b)

def calculate_R_squared(y_true, y_pred):
    # Calculate R-squared
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    return 1 - (ss_res / ss_tot)

# Step 5. Plot everything as before
fig, ax = plt.subplots(1, 1, figsize=(9, 6))

for name, group in c_daily_traffic_day:
    # Step 5-1. plot flow traveltimes functions
    ax.plot(group["avgdemand"], group["traveltimes"], marker="o", linestyle="", label=f"{name}")
    # ax.plot(group["avg_flow"], group["traveltimes"], marker="o", linestyle="", label=f"{name}")

    # Step 5-2. plot fitted curve
    # Fix c = 1000 using a lambda
    x = group["avgdemand"].values 
    # x = group["avg_flow"].values 
    y = group["traveltimes"].values
    
    model_fixed_c = lambda x, a, b: model_func(x, a, b, c=c_fixed, w=W)
    params, _ = curve_fit(model_fixed_c, x, y, p0=[1, 1], maxfev=10000)
    a_fit, b_fit = params
    
    
    # Step 4. Generate smooth x-values and compute corresponding y-values
    x_fit = np.linspace(0, max(x), 500)
    y_fit = model_func(x_fit, a_fit, b_fit, c_fixed, w=W)
    
    # Predict y-values using the fitted model
    y_pred = model_func(x, a_fit, b_fit, c_fixed, w=W)
    
    # Calculate R-squared
    r_squared = calculate_R_squared(y, y_pred)
    
    # Plot fitted curve
    ax.plot(
        x_fit, y_fit, color="black", linewidth=2,
        label=f"Fitted: y = t₀·(1 + {a_fit:.2f}·(x/({c_fixed:.0f}*{W:.0f}))^{b_fit:.2f}), R² = {r_squared:.3f}")
    plt.legend()

# ax.scatter(c_daily_traffic["flow"], c_daily_traffic["traveltimes"])
ax.set_title(f'BPR parameter calibration at VDS {VDS_num} ({method} congestion detection)')
ax.set_ylabel('Average travel time (min/mile)', fontsize=13)
ax.set_xlabel(r'$N/(W \cdot l)$: Average demand per lane during defined time windows (vphpl)', fontsize=13)
# ax.set_xlabel(r'Average flowrate per lane (vphpl)', fontsize=13)
ax.grid(True)
# ax.set_xlim(0, 2000)
# ax.set_ylim(1,4)
# ax.legend(title=f'{label_criterion}')

# Save and Display the plot
plt.savefig(f'./{working_f}/02 fig/12 Daily BPR/BPR_calibration_v4_{VDS_num})_labeled by_{label_criterion}_with_{year_notinclude}{period_include}_{temporal_scope}.png')
# plt.show()

# + [markdown] jp-MarkdownHeadingCollapsed=true
# - Capacity ($c$): Chosen as the upper limit of the free-flow speed segment
#     - While the congested segment may vary depending on the size of $W$, the free-flow segment remains consistent.
#     - The end of the free-flow segment can be interpreted as the onset of congestion.
#         - VDS_num=1205583: c= 900
#         - VDS_num=1203506: c = 1200    
# - Fitting result (t=t_0 * (1 + a * (x / c) ** b))
#     - VDS_num=1205583: t=t_0 * (1 + 0.86 * (x / 900) ** 1.9), R^2 = 0.832
#     - VDS_num=1205583: t=t_0 * (1 + 0.54 * (x / 1200) ** 1.13), R^2 = 0.573
# - A detailed discussion is needed on how to define capacity and interpret the associated parameters.

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### (Version6) Wholeday

# +
temporal_scale = 'speedbasedpeak'
VDS_num = 1205583
# VDS_num = 1203506
# VDS_num = 1214006

method = 'RDP_v'
version= 'filtered'
# version = ''
# 'wholeday', 'peak'
temporal_scope = 'peak'

file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}_{temporal_scope}_{version}.csv"

# +
## write down not inclue values
dayofweek_notinclude = []
year_notinclude = []
month_notinclude = []

period_include = ['off-peak','morning-peak','afternoon-peak']
# 'morning-peak', 'afternoon-peak'

# Step 1: data read
c_daily_traffic = pd.read_csv(file_path)

### new column
c_daily_traffic['date'] = c_daily_traffic['date'].astype(str)
c_daily_traffic['month'] = c_daily_traffic['date'].str.slice(0, 4)
# Step 2: column
# total demand from peak period to the average flow depending on the size of 'heart of peak period'
# heart of peak period(W): minutes

c_daily_traffic.loc[(c_daily_traffic['division'] == 0),'avgdemand'] = c_daily_traffic.loc[(c_daily_traffic['division'] == 0),'totaldemand']
c_daily_traffic.loc[(c_daily_traffic['division'] != 0),'avgdemand'] = c_daily_traffic.loc[(c_daily_traffic['division'] != 0),'totaldemand'] / (W)

# c_daily_traffic.to_csv(f"./{working_f}/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}.csv")

# Step 3: data filtering
## Step 3-1: off-/peak- period
c_daily_traffic = c_daily_traffic[c_daily_traffic['division'] != -1]

## Step 3-2: notinclude
c_daily_traffic = c_daily_traffic[~c_daily_traffic['year'].isin(year_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['dayofweek'].isin(dayofweek_notinclude)]
c_daily_traffic = c_daily_traffic[~c_daily_traffic['month'].isin(month_notinclude)]

c_daily_traffic = c_daily_traffic[c_daily_traffic['period'].isin(period_include)]

# +
### data handling
# Define weights
w_dict = {
    'off-peak': float('inf'),
    'morning-peak': 1,
    'afternoon-peak': 1
}
cap = 2200
beta = 4

g_c_daily_traffic = c_daily_traffic.groupby('date')


l_wratio = []
l_wtilde = []
l_avgtraveltimes = []


# Example within the loop
for date, group in g_c_daily_traffic:
    period_list = group['period'].tolist()   # e.g. ['off-peak', 'morning-peak', 'afternoon-peak']
    # print(period_list)
    
    # Convert to corresponding weights
    c_w = [w_dict[p] for p in period_list]
    # print(c_w)
    epsilon = group['totaldemand'] / group['totaldemand'].sum()
    avg_traveltimes = (group['traveltimes'] * epsilon).sum()
    
    epsilon = np.asarray(epsilon, dtype=float)
    c_w = np.asarray(c_w, dtype = float)
    w_tilde = (1 / ( (epsilon ** (beta + 1) / (c_w ** beta)).sum() )) ** (1 / beta)
    
    w0 = group['totaldemand'].sum() / cap

    w_ratio = w0/w_tilde
    # print(w_tilde, w0, w_ratio)

    l_wtilde.append(w_tilde)
    l_wratio.append(w_ratio)
    l_avgtraveltimes.append(avg_traveltimes)

# +
finite_vals = [v for v in l_wtilde if np.isfinite(v)]

fig, ax = plt.subplots(1, 1, figsize=(6, 6))
ax.hist(finite_vals, bins=20, edgecolor='black')

plt.show()

# +
from scipy.optimize import curve_fit  
# Ensure day is categorical with ordered days

def model_func(w_ratio, a, b):
    # t_0 (min/mile) = 1/v_0 (mph) * 60   
    t_0 = 1 / 70 * 60
    return t_0 * (1 + a * (w_ratio) ** b)

def calculate_R_squared(y_true, y_pred):
    # Calculate R-squared
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    return 1 - (ss_res / ss_tot)

# Step 5. Plot everything as before
fig, ax = plt.subplots(1, 1, figsize=(9, 6))


ax.plot(l_wratio, l_avgtraveltimes, marker="o", linestyle="")

# Step 5-2. plot fitted curve
# Fix c = 1000 using a lambda
x = l_wratio
y = l_avgtraveltimes

model_fixed_c = lambda w_ratio, a, b: model_func(w_ratio, a, b)
params, _ = curve_fit(model_fixed_c, x, y, p0=[1, 1], maxfev=10000)
a_fit, b_fit = params

# Step 4. Generate smooth x-values and compute corresponding y-values
x_fit = np.linspace(0, max(x), 500)
y_fit = model_func(x_fit, a_fit, b_fit)

# Predict y-values using the fitted model
y_pred = model_func(l_wratio, a_fit, b_fit)

# Calculate R-squared
r_squared = calculate_R_squared(y, y_pred)

# Plot fitted curve
ax.plot(
    x_fit, y_fit, color="black", linewidth=2,
    label=rf"Fitted: y = t₀·(1 + {a_fit:.2f}·(N/(lC$\tilde{{W}}$))^{b_fit:.2f}), R² = {r_squared:.3f}")
plt.legend()

# ax.scatter(c_daily_traffic["flow"], c_daily_traffic["traveltimes"])
ax.set_title(f'BPR parameter calibration at VDS {VDS_num} ({method} congestion detection)')
ax.set_ylabel('Average travel time (min/mile)', fontsize=13)
ax.set_xlabel(r'$\frac{N}{lC\tilde{W}}$ ', fontsize=13)
ax.grid(True)
# ax.set_xlim(0, 1500)
# ax.set_ylim(1,4)
# ax.legend(title=f'{label_criterion}')

# Save and Display the plot
plt.savefig(f'./{working_f}/02 fig/12 Daily BPR/BPR_calibration_v6_{VDS_num})_labeled by_{label_criterion}_with_{year_notinclude}{period_include}.png')
# plt.show()

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### free-flow speed distribution (off-peak)

# +
temporal_scale = 'speedbasedpeak'
VDS_num = 1205583
# VDS_num = 1203506
method = 'RDP_v'
version= 'filtered'
# version = ''
# 'wholeday', 'peak'
temporal_scope = 'peak'

file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/c_daily_traffic_{VDS_num}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{method}_{temporal_scope}_{version}.csv"

# +
## write down not inclue values
period_include = ['off-peak']
# 'morning-peak', 'afternoon-peak'

# Step 1: data read
c_daily_traffic = pd.read_csv(file_path)

# Step 1-2: filtering
last_col = c_daily_traffic.columns[-1]
c_daily_traffic = c_daily_traffic[c_daily_traffic[last_col] != False]

### new column
c_daily_traffic['date'] = c_daily_traffic['date'].astype(str)
c_daily_traffic['month'] = c_daily_traffic['date'].str.slice(0, 4)

# Step 3: data filtering
## Step 3-1: off-/peak- period
c_daily_traffic = c_daily_traffic[c_daily_traffic['division'] != -1]

## Step 3-2: notinclud
c_daily_traffic = c_daily_traffic[c_daily_traffic['period'].isin(period_include)]



# +
values = (1 / c_daily_traffic['traveltimes']) * 60

values.median()

# +
import matplotlib.pyplot as plt

# Compute transformed values


# Plot histogram as density
plt.figure(figsize=(8, 6))
plt.hist(values, bins=30, edgecolor='black', density=True)
plt.xlabel("Average speed (mph)")
plt.ylabel("Density")
plt.title(f"Density Histogram of Average Speed during Uncongested Period(VDS: {VDS_num})")
plt.grid(True, linestyle="--", alpha=0.6)


# Save and Display the plot
plt.savefig(f'./{working_f}/02 fig/12 Daily BPR/Freeflow_speed_dist_{VDS_num}{version}.png')
plt.show()
# -

# # BPR calibration based on different temporal scales

# ## Case 1) Entire Day

# - Entire day
#     - Does not explicitly fit with the F.D. There are many values with the same daily volumes
#     - Why? Daily volume alone is not enough to capture traffic patterns, especially how demand is concentrated during peak periods.
#         - Example: Two days may have the same daily volume but different demand distributions throughout the day.
#         - <img src="./01_BPR/02_1_presentation_fig/Daily_BPR_concept.png" width=50%>
#     - Using daily demand size doesn’t directly correspond to average travel times.
#         - Because demand fluctuates over time, the total volume alone does not provide explicit insight into observed travel times.
#     - Identifying near-stationary states may help reveal patterns, but I doubt this process can shape the BPR function.
#         - Different sets of week-to-week stationary states can have the same daily volumes despite having different traffic patterns.
#         - However, if we focus only on the peak period, the volume more closely aligns with travel times, since the peak period is not fixed but varies with the severity of congestion.
#     - 교수님 논문에서 전체 day에서는 w 어떻게 정의했는지 확인해보기!!
#     - 같은 demand라도 다른 값을 가져도 되는게, 그렇기 때문에 BPR을 다른 상황마다 parameter estimation하는게 아닌가?? 

# +
## "entireday", "peak" "hour" "speedbasedpeak"
VDS_num = 1203506
# VDS_num = '1205583'
temporal_scale = "peak"
file_path = f"/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/BPR/c_daily_traffic_{VDS_num}_{temporal_scale}_filtered.csv"

c_daily_traffic = pd.read_csv(file_path)

print(c_daily_traffic[(c_daily_traffic['flow']<25240/24) & (c_daily_traffic['flow']>25000/24)].sort_values(by='date', ascending=True))

# + jupyter={"outputs_hidden": true}
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
plt.savefig(f'./{working_f}/02 fig/12 Daily/Daily_flow_vs_time_{temporal_scale}_{VDS_num})_labeled by_{label_criterion}_without_{year_notinclude}{dayofweek_notinclude}.png')
plt.show()
# -

# ## Case 2) Fixed Time-period
#
#

# - On 6/2, we discussed testing fixed-time peak periods:
#     - Morning peak: 4:00–10:00
#     - Afternoon peak: 16:00–22:00
#     - During these peak periods, apply a fixed __waiting time of 3 hours__.
# - __For VDS: 1205306__, the original afternoon peak was set to 16:00–22:00. However, traffic often starts peaking from 15:00, resulting in many __non–free-flow travel times during low demand periods__. This could be improved by redefining the peak periods.
# - <img src='./01_BPR/02_1_presentation_fig/fixedtime_peak_16-22.png' width=80%>
# - Still, even with adjusted peak times, the morning and afternoon peaks diverge: the morning peak has __lower hourly demand__, while the __afternoon peak sees higher demand__.
# - this pattern roughly follow an F.D. shape, but they may shift toward a BPR-like shape if we filter for stationary states.
# - <img src='./01_BPR/02_1_presentation_fig/fixedtime_peak_14-20.png' width=80%>
# - __For VDS: 1205583__, traffic patterns appear more consistent and show a clearer trend, but resemble more of a fundamental diagram (F.D.) shape.
# - __this pattern shows somewhat clear FD shape, not sure how to interpret this result__
# - <img src='./01_BPR/02_1_presentation_fig/Daily_flow_vs_time_peak_1205583.png' width=60%>
#

# <div class="alert alert-danger">
#
# <6/17/2025>
# - Unlike speed-based peak-period, It did not show the BPR shape.
#     - why?) Because the congestion period alone doesn’t capture distributional information—like the full-day volume—which is critical for explaining travel times.
#     - fixed와 unfixed가 근본적인 차이같어. 이와 관련한 이유를 제시해야할 것 같은데?

# + jupyter={"outputs_hidden": true}
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


# -

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

# - <img src='./01_BPR/proj2_Qinlong_2018.png' width=50%>
# - Figure: Yan et al. (2018)

# + jupyter={"outputs_hidden": true}
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


# + jupyter={"outputs_hidden": true}
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

# + jupyter={"outputs_hidden": true}
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
# plt.savefig(f'./{working_f}/02 fig/12 Daily/Daily_flow_vs_time_{lane_range}_{dataset_days}({year_range})_labeled by_{label_criterion}.png')
plt.show()

# + jupyter={"outputs_hidden": true}
x = [0, 1.6, 1.7, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 5, 5, 6, 7]
# peaks, properties = find_peaks(x, distance=5, plateau_size=2)

peaks, properties = find_peaks(x,height=2,distance=1)
# , width=5
print(peaks)
print(properties)
