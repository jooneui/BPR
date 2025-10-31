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

# ## Pipeline

# - The API(clearhouse) provides rawdata, but g-factor is not provided.
# - The rawdata includes flowrate and speed, so I calculate the density by flowrate/speed

# <center> <img src='./01_BPR/02_1_presentation_fig/1_pipeline.png' width = "70%"> </center>

# <div class="alert alert-info">
#
# __Data Pre-processing__
#
# This study employs the California Performance Measurement System (PeMS) as the primary data source. PeMS provides loop-detector data at several temporal resolutions (30 s, 5 min, 15 min, and 1 h). Among them, the 5-minute interval is used in this study because it balances representativeness and temporal precision. The 30-second data are too short to capture stable traffic states due to high variability in vehicle arrivals, while 15-minute or longer aggregations might be too coarse to identify the precise start and end of congestion. Therefore, the 5-minute aggregation is adopted to represent typical near-stationary traffic conditions while preserving the temporal resolution required for detecting congestion transitions.
#
# PeMS provides lane-level flow $(q_{k,l})$ and speed $(v_{k,l})$ for each 5-minute interval $k$ and lane $l$. The density $(k_{k,l})$ is then derived from the definitional relationship  
# $$
# q = k v \quad \Rightarrow \quad k = \frac{q}{v}.
# $$
#
# Lane-to-lane average traffic states are calculated as the arithmetic mean based on Edie’s generalized definition (Edie, 1963; Cassidy and Coifman, 1997), since all lanes share the same spatial and temporal domain size at each station:
# $$
# \bar{q}_k = \frac{1}{L}\sum_{l=1}^{L} q_{k,l}, 
# \qquad 
# \bar{k}_k = \frac{1}{L}\sum_{l=1}^{L} k_{k,l}.
# $$
# The corresponding station-level average speed is obtained as  
# $$
# \bar{v}_k = \frac{\bar{q}_k}{\bar{k}_k},
# $$
# which is equivalent to the harmonic mean of lane-level speeds weighted by their respective flow rates:
# $$
# \bar{v}_k = \frac{\sum_l q_{k,l}}{\sum_l q_{k,l}/v_{k,l}}.
# $$
#
# The 5-minute aggregated speeds are concatenated to form daily speed profiles, which are then segmented into piecewise-homogeneous intervals using either the Pruned Exact Linear Time (PELT) or the Ramer–Douglas–Peucker (RDP) algorithm. Each algorithm independently detects uncongested intervals characterized by sustained near–free-flow conditions, from which the remaining intervals are inferred as congested. After segmentation, consecutive intervals of the same traffic state are merged to form continuous periods.  
#
# For each resulting period $p$, mean traffic states are computed as  
# $$
# \bar{q}_p = \frac{1}{N_p}\sum_{k\in p}\bar{q}_k, \qquad
# \bar{k}_p = \frac{1}{N_p}\sum_{k\in p}\bar{k}_k, \qquad
# \bar{v}_p = \frac{\bar{q}_p}{\bar{k}_p},
# $$
# where $N_p$ is the number of 5-minute intervals within the period.  
#
# Through this process, the raw lane-level PeMS data are systematically transformed into temporally segmented and physically consistent traffic states, forming the foundation for subsequent analyses of congestion patterns and travel time–flow relationships.

# <div class="alert alert-info">
#
# __Line-based Segmentation__
#
# In this study, we aim to detect uncongested periods by segmenting daily speed or distance profiles into linear intervals. To perform the segmentation, we apply two widely used algorithms in parallel: PELT (Pruned Exact Linear Time) and RDP (Ramer–Douglas–Peucker). This subsection describes how each method is used to segment the daily profiles.
#
# - RDP and PELT explanation is in TRB2026 paper

# <div class="alert alert-info">
#
# __Uncongsted Period Selection__
#
# After applying PELT and RDP-based segmentation to the speed time series, we proceed to identify and classify traffic periods based on characteristics of uncongested conditions. This process consists of two main phases: segment classification and adjacent-segment merging.
#
# __Segment Classification__
#
# Given the changepoints $\tau_0 = 0, \tau_1, \ldots, \tau_m, \tau_{m+1} = n$ identified by the segmentation algorithms, we define a set of segments $S_i = [\tau_{i-1} + 1, \tau_i]$ for $i \in \{1, \ldots, m+1\}$. Each segment represents a time interval with relatively homogeneous traffic behavior.
#
# For each segment $S_i$, we compute the average speed $v_i$ as follows:
# $$
# v_i = \frac{S(\tau_i) - S(\tau_{i-1})}{(\tau_i - \tau_{i-1}) \Delta t}
# $$
# where $S(\tau_i)$ denotes the cumulative distance at time $\tau_i$, and $\Delta t$ is the sampling interval.
#
# To formalize our concept that "uncongested period is a sustained period of near-free-flow speeds," we define two measurable conditions for each segment. 
# - __Condition A (Sustained)__: the duration of the segment is at least $T$ ($D_i \ge T=90 \text{minutes}$)
# - __Condition B (Near-free-flow)__: the mean speed of the segment is at least $v_1$ ($ v_i \geq v_1 = 45 \text{mph} $)
#
# A segment that satifies both conditions is considered uncongested, while all remaining segments are treated as congested by definition. Formally,
#
# $$
# \phi(S_i) = 
# \begin{cases}
#   1 & \text{if } A \cap B \\
#   2 & \text{otherwise}
# \end{cases}
# $$
#
# Here, $\phi(S_i) = 1$ indicates an uncongested period, while $\phi(S_i) = 2$ denotes a congested period. This rule ensures that segments are only classified as uncongested if they exhibit both sufficiently high speed and a minimum duration threshold, providing robustness against transient fluctuations.
#
# These two conditions ($A$ and $B$) together define four possible traffic states. 
# - 1. Uncongested ($A\wedge B$): the segment is both long enough and fast enough to represent a sustained near-free-flow period.
# - 2. Congested ($A\wedge \neg B$): the duration is long, but the average speed is low, indicating a stable, persistent queue.
# - 3. Congested ($\neg A \wedge \neg B$): the segment is short and slow, clearly reflecting congested traffic.
# - 4. Congested ($B \wedge \neg A$): the segment is short but has relatively high mean speed. These short, high-speed periods occur near the start or end of congestion, or between two congested periods or between two free-flow plateaus.

# <center> <img src='./01_BPR/02_1_presentation_fig/2_Period_def.png' width = "50%"> </center>

# <div class="alert alert-info">
#
# Although $(B \wedge \neg A)$ satisfies the definition of a congested period (as it fails the duration condition $A$), in practice, this category includes both congested and uncongested behaviors depending on the parameter settings of segmentation algorithms like Ramer–Douglas–Peucker (RDP) and PELT. Their tolerance (or penalty) parameters control sensitivity to changes in the speed profile, but do not inherently correspond to physical traffic dynamics such as queue formation or dissipation. As a result, it is difficult to perfectly delineate the boundary between the uncongested regime ($A \wedge B$) and this short, high-speed category ($\neg A \wedge B$), leading to interpretive ambiguity.
#
# As previously discussed, the ambiguous set includes three types of short, high-speed segments:
#
# - Case 1) Congestion transitions – segments where speed changes rapidly due to the formation or clearance of a queue.
# - Case 2) Free-flow transitions – short, low-variance segments representing slight speed drifts between two uncongested plateaus.
# - Case 3) Temporary speed recoveries – brief local clearings that occur within otherwise congested periods.
#
# Among these, the second case—free flow transitions—should be classified as part of the uncongested regime, while the other two reflect congestion-related behavior. However, in practice, RDP and PELT cannot reliably distinguish between them, as both Case 1 and Case 2 are short in duration and exhibit relatively high mean speeds.
#
# When the RDP or PELT parameter is set too coarse, the algorithm smooths over moderate fluctuations and merges nearby changes into a single, extended segment. This can cause transition segments—where speeds drop or recover rapidly—to appear as part of a free-flow plateau. As a result, some genuinely congested transitions are incorrectly absorbed into the uncongested region, leading to false positive labels: segments that meet the duration and speed thresholds but actually contain the start or end of a queue.
#
# Conversely, when the parameter is set too fine, the algorithm becomes overly sensitive to minor speed variations. Smooth free-flow plateaus may be fragmented into several short segments, and calm bridges (Case 2) may be misclassified as transitions simply due to minor drifts. This over-segmentation inflates the number of ambiguous short, high-speed segments, making it harder to distinguish between genuine queue edges and gentle free-flow drifts.
#
# In summary, the RDP and PELT parameters shape how the algorithm interprets the speed profile but do not necessarily align with the physical boundaries between traffic regimes. Optimally tuning these parameters to distinguish all cases—such as queue edges, calm bridges, and embedded short plateaus—is challenging, as the ideal sensitivity can vary by location, day, and even time of day.
#
# To ensure consistency, we adopt relatively fine-grained parameter settings, allowing potentially mixed or transitional cases to fall into the ambiguous category. These ambiguous segments are then interpreted using additional traffic-relevant indicators.
#
# </div>

# <center> <img src='./01_BPR/02_1_presentation_fig/2_uncongested_ambiguous_cases.png' width = "40%"> </center>
#

# <div class="alert alert-info">
#
# To interpret these ambiguous cases in a traffic-meaningful way, we examine two simple physical indicators:
# - Intensity ($I(s)$), which measures the range of speeds within the segment and thus reflects how abrupt the internal change is;
# - Neighboring states, which identify whether the segment connects to uncongested regions or lies between congested ones.
#
# These two indicators allow us to refine the boundaries drawn by RDP without changing the fundamental definition of an uncongested period.
# The refinement follows two simple rules.
#
# - Rule 1 — Free-flow transition merge. When a short segment has a small intensity ($I(s)<15 \text{mph}$) and is adjacent to an uncongested neighbor, it is merged with that neighbor.
# This pattern corresponds to a gradual drift in speeds—what we call a “free-flow transition”—that connects two uncongested plateaus.
# Because the speeds remain stable and there is no sign of queue formation, it should reasonably be treated as part of the uncongested regime.
# - Rule 2 — Congestion transition or Temporary speed recovery. If the segment instead shows a large internal speed change ($I(s) \ge 15\text{mph}$), it represents a sharp transition in traffic conditions, such as the onset or recovery of congestion (Case 1). These segments are kept within the congested regime because they capture the boundary where flow breaks down or recovers. Alternatively, if the segment has low intensity but is surrounded by congested neighbors on both sides, it represents a brief local clearing within a broader congested episode (Case 3).
# Even though its mean speed is relatively high, this “temporary speed recovery” does not signal a true regime change and is therefore also retained as congested.
#
# Through these two rules, the ambiguous set $\neg A \cap B$ is resolved using physical reasoning rather than geometric sensitivity. Short, calm drifts are absorbed into the uncongested periods, while sharp transitions and embedded clearings remain part of congestion. This approach refines the segment boundaries to better match real traffic dynamics while keeping the original definition—uncongested equals a sustained period of near-free-flow speeds—fully intact.
#
#
# |                         | Congestion Transitions (Case 1)  | Free-Flow Transitions (Case 2) | Temporary Speed Recoveries (Case 3) |
# |-------------------------|:--------------------------------:|:------------------------------:|:-----------------------------------:|
# | **Intensity**           | $$I(s) \geq 15\,\text{mph}$$     | $$I(s) < 15\,\text{mph}$$      | $$I(s) < 15\,\text{mph}$$        |
# | **Neighbors**           | At least one congested neighbor  | Both uncongested               | Both congested                      |
# | **Actual State**           | Congested period  | Uncongested period        | Congested period                    |
#
#

# # Data Description

# ## I-5

# - \2024. Jan. 1st ~ Aug.27th
# - <img src='./01_BPR/02_1_presentation_fig/3_VDS_location.png' width=80%>
# - Roughly 1.1mile

# ### Speed patterns

# - From right to left, the VDSs are numbered 1 to 5.
#     - VDS 1 is the least congested.
#     - VDS 2 and 3 experience the heaviest congestion.
#     - When congestion becomes severe, the queue extends into VDS 4 and 5.
#         - VDS 4 and 5 generally have shorter congested periods and smaller speed drops than VDS 2 and 3, forming a triangular pattern.
#         - However, under very severe congestion, VDS 5 shows a larger speed drop despite a shorter congestion duration.
#         - My interpretation is that in a 4-lane section (compared to a 6-lane one), VDS 5 is more prone to collapse once congestion occurs.

# - <img src='./01_BPR/02_1_presentation_fig/I-5_Buenapark.png' width=60%>
# - Period: total __245__
#     - Jan. ~ Oct. 2011

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

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### RDP threshold in this study
# -

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


# -

# ### (Code) Peak period detection

# #### (Code) Data process

# + tags=["code"] jupyter={"source_hidden": true}
def rawdata_setting(full_path,VDS_num,file_name,lane_num):
    """
    Upload raw-data and standardize the settings
    """
    
    rawdata = pd.read_excel("%s/%s" % (full_path,file_name))
    
    rawdata.columns = ['time'] + [f'flow_{i}' for i in lane_num] + [f'speed_{i}' for i in lane_num]+ [f'occ_{i}' for i in lane_num] + ['length']
    # rawdata.columns = ['time'] + [f'flow_{i}' for i in lane_num] + [f'occ_{i}' for i in lane_num]

    rawdata['time'] = pd.to_datetime(rawdata['time'])
    # 'time_filter' is to convert the time to minutes.(ex. 02:30:30 -> 150.30min)
    rawdata['time_filter'] = rawdata['time'].dt.hour*60 + rawdata['time'].dt.minute + rawdata['time'].dt.second/60
    # rawdata['time_filter'] = rawdata['time'].dt.hour*100 + rawdata['time'].dt.minute
    rawdata['time_hour'] = rawdata['time'].dt.hour
    
    return rawdata


# +
""" Sometimes, the rawdata interval is too short to see the stable traffic pattern, so rawdata is aggregated to specific time interval.
This function address calculating traffic state variables in every pre-determined aggregated time interval.


* "This is not equal to the 'Research_BPR_function_Develop.ipynb', because of rawdata['time_slot'] is different: it used the median value
Interpolate_missing(traffic, config) is also changed.
"""

def aggregate_rawdata_5min(rawdata, raw_timeframe, date, lane_num, VDS_num):
    
    # Pre-compute time_slot for all data to avoid doing it in the loop
    rawdata['time_slot'] = (np.floor(rawdata['time_filter'] / raw_timeframe)) * raw_timeframe + raw_timeframe/2
    
    # Initialize list to store each row's data for final DataFrame
    traffic_within_day = pd.DataFrame()
    plot_date = []
     
    # Operate on grouped DataFrame
    flow_set = [f'flow_{i}' for i in range(1,lane_num[-1]+1,1)]
    density_set = [f'density_{i}' for i in range(1,lane_num[-1]+1,1)]
    occ_set = [f'occ_{i}' for i in range(1,lane_num[-1]+1,1)]
    speed_set = [f'speed_{i}' for i in range(1,lane_num[-1]+1,1)]
    
    rawdata[flow_set] *= 60/raw_timeframe
    # Compute densities with shape alignment, then rename columns to density_*
    speeds = rawdata[speed_set].replace(0, np.nan)
    dens_values = rawdata[flow_set].to_numpy() / speeds.to_numpy()
    dens = pd.DataFrame(dens_values, index=rawdata.index, columns=density_set)
    
    # 4) Assign (now lengths match)
    rawdata[density_set] = dens

    rawdata['flow'] = rawdata[flow_set].mean(axis=1)
    rawdata['density'] = rawdata[density_set].mean(axis=1)
    rawdata['occ'] = rawdata[occ_set].mean(axis=1)
    rawdata['speed'] = rawdata['flow'] /  rawdata['density']
    rawdata['traveltime'] = 1/rawdata['speed'] * 60 

    traffic_within_day = rawdata
    plot_date = traffic_within_day['time_slot']
    
    # Save the data
    path_directory = f'./{working_f}/12 python file/{VDS_num}'
    os.makedirs(path_directory, exist_ok=True)

    with open(f'./{working_f}/12 python file/{VDS_num}/traffic_within_day_{date}_raw{raw_timeframe}min_{lane_num}.p', 'wb') as file:
        pickle.dump(traffic_within_day, file)

    with open(f'./{working_f}/12 python file/{VDS_num}/plot_date_{date}_raw{raw_timeframe}min.p', 'wb') as file:    
        pickle.dump(plot_date, file)
    
    return traffic_within_day, plot_date


# +
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
    # gfactor = pd.read_excel(gfile)
    rawdata = rawdata_setting(
        full_path=f"{config['path']}/11 Rawdata/{config['dir']}/{config['VDS_num']}",
        VDS_num=config['VDS_num'],
        file_name = file_name,
        lane_num=config['lane_num']
    )
    # return rawdata, gfactor, date
    return rawdata, date



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
        traffic, plot_date = aggregate_rawdata_5min(
            rawdata, config['raw_timeframe'], date,
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
        
        ## for the speed in each lane and the average, recalculate based on the interpolated flow and density
        speed_cols   = [f"speed_{i}"   for i in config['lane_num']]
        flow_cols    = [f"flow_{i}"    for i in config['lane_num']]
        density_cols = [f"density_{i}" for i in config['lane_num']]
        
        new_row[speed_cols] = (
            new_row[flow_cols].to_numpy() /
            new_row[density_cols].replace(0, np.nan).to_numpy())
        new_row["speed"] = new_row["flow"] / new_row["density"]
        
        traffic = pd.concat([traffic, new_row.to_frame().T], ignore_index=True)

    return traffic.sort_values('time_slot').reset_index(drop=True)


# -

# #### (code)__Data process for multi_VDS__

# + jupyter={"source_hidden": true}
import re
from functools import reduce
from datetime import datetime as _dt

def _extract_date_from_filename(fn: str) -> str:
    """Match your existing logic: last 11..-5 slice already used elsewhere."""
    # Fallback to slice if pattern stable in your folders
    return fn[-11:-5]   # e.g., '250915' for YYMMDD

def _index_files_by_date(base_path: str) -> dict:
    """
    Return {date_str: filename} for a given VDS directory.
    base_path = f"{config['path']}/11 Rawdata/{config['dir']}/{VDS}"
    """
    files = sorted(os.listdir(base_path))
    files = [f for f in files if not f.startswith('.')]
    out = {}
    for f in files:
        try:
            d = _extract_date_from_filename(f)
            out[d] = f
        except Exception:
            continue
    return out

def _common_dates_and_files(config) -> tuple[list, dict]:
    """
    For config['VDS_list'], compute intersection of dates and map to filenames.
    Returns:
      dates_common (sorted list of 'YYMMDD'),
      date_to_files: {date: {vds: filename}}
    """
    date_maps = {}
    for vds in config['VDS_list']:
        base = os.path.join(config['path'], '11 Rawdata', config['dir'], vds)
        date_maps[vds] = _index_files_by_date(base)

    # intersection of date keys
    sets = [set(dmap.keys()) for dmap in date_maps.values()]
    dates_common = sorted(set.intersection(*sets))

    date_to_files = {d: {vds: date_maps[vds][d] for vds in config['VDS_list']} for d in dates_common}
    return dates_common, date_to_files

def _dow_from_yymmdd(d: str) -> str:
    """Return weekday string using your Day_list mapping."""
    Day_list = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    dt = _dt.strptime('20' + d, '%Y%m%d')
    return Day_list[dt.weekday()]


# + jupyter={"source_hidden": true}
def _make_vds_config(config, vds: str):
    """Shallow clone with per-VDS fields."""
    cfg = dict(config)
    cfg['VDS_num']  = vds
    cfg['lane_num'] = config['lane_map'][vds]
    return cfg

def _build_traffic_for_vds(date: str, filename: str, cfg_vds, vds):
    """Reuses your existing functions to get a per-VDS day traffic frame."""
    # load raw + gfactor
    rawdata, date  = load_raw(filename, cfg_vds)
    if skip_if_missing(rawdata, cfg_vds) :
        return None  # skip this day for this VDS 

    # aggregate or load cached
    lane_num = c_lane_num[vds]
    coverage_length = rawdata['length'].iloc[0]
    
    traffic, plot_date = aggregate_rawdata_5min(rawdata, raw_timeframe, date, lane_num, VDS_num)
    # traffic, plot_date = load_or_aggregate(rawdata, date, cfg_vds)

    # # same cleaning as your main loop
    # traffic = highfreeflowspeed_conversion(traffic, cfg_vds)
    # traffic = interpolate_missing(traffic, cfg_vds)
    # traffic = assign_fixedtime_peaks(traffic, cfg_vds)  # no-op for 'speedbasedpeak'

    return traffic, coverage_length


# + jupyter={"source_hidden": true}
def _combine_vds_traffic(traffic_list: list[pd.DataFrame], agg_min: int, c_coverage_length: list) -> pd.DataFrame:
    """
    Given multiple per-VDS daily DataFrames (already interpolated to identical
    time_slot grids), return a single DataFrame with:
        ['time_slot','speed','time','flow','density']
    computed as simple arithmetic means across VDS for each time_slot.
    """
    # keep only columns we can consistently average
    keep = ['time_slot', 'speed', 'flow', 'density']
    stacked = []
    for t in traffic_list:
        if t is not None:
            stacked.append(t[keep].copy())

    if not stacked:
        return None

    # Concatenate with keys and average by time_slot
    # combo = (pd.concat(stacked, keys=range(len(stacked)))
    #            .groupby('time_slot', as_index=False)[['flow','density']].mean())

    combo =  (pd.concat(stacked, keys=range(len(stacked)))
               .groupby('time_slot', as_index=False).apply(lambda g: pd.Series({
             'flow': np.average(g['flow'], weights=c_coverage_length),
             'density': np.average(g['density'], weights=c_coverage_length)
         })).reset_index())

    # recompute time (min/mile) from averaged speed
    combo['speed'] = combo['flow'] / combo['density']
    combo['time'] = 60.0 / combo['speed']

    # ensure standard ordering like your per-day frames
    combo = combo[['time_slot','speed','time','flow','density']].sort_values('time_slot').reset_index(drop=True)
    return combo
# #### (Code) plot codes


# -

# #### (Code) Plot

# + jupyter={"source_hidden": true}
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
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right',fontsize=15)

    fig.tight_layout()
    plt.savefig(f'./{working_f}/02 fig/16 PELT/{VDS_num}_{date}_{aggregate_timeframe}_{method}_{penalty}.png')
    # plt.show()  # Uncomment if you want to display the plot

# + jupyter={"source_hidden": true}


def speedprofile_plot(df, raw_timeframe, config, date):
    
    time_slot_hour = range(raw_timeframe, int(60*24/raw_timeframe) +1, raw_timeframe)
    
    # joon, pelt, RDP, derivative
    title_name = [f'Daily speed profile from multiple VDS (Date:{date})']   
    
    fig, ax1 = plt.subplots(figsize=(12, 5))

    ax1.set_xlabel('Time (Hours)',fontsize=16)
    ax1.set_ylabel('Speed (mph)',fontsize=16)
    ax1.set_title(title_name[0],fontsize=18)
    ax1.grid(True)
    ax1.set_xlim(0, 24+.1)
    ax1.set_xticks(np.arange(0, 25, 1))

    ax1.set_ylim(0,85)
    ax1.set_yticks(np.arange(0, 85 + 1, 10))  # Ticks at 0, 20, 40, 60, 80
    # Set y-axis tick label color
    # ax1.tick_params(axis='y', colors='green')
    # Set y-axis spine (axis line) color
    # ax1.spines['left'].set_color('green')

    colors = ['red','orange','green','blue','purple']
    
    for i, VDS  in enumerate(config['VDS_list']):
        df_per_VDS = df[i]
        df_per_VDS['time_slot_hour'] = df_per_VDS['time_slot'] / 60
        ax1.plot(df_per_VDS['time_slot_hour'], df_per_VDS['speed'], color=colors[i], linewidth=1.5, label=f'{i+1}th: {VDS}')
        ax1.legend(title="VDS", fontsize=10, loc="upper right")  # add legend inside plo
        
    fig.tight_layout()
    plt.savefig(f'./{working_f}/02 fig/17 Speedprofile/{config['VDS_list']}_{date}.png')
    # plt.show()  # Uncomment if you want to display the plot
# -

# ### (Code) Speed-based peak period

# +
# # def pelt_speedbased_directpeak(df, column, speed_upper, model, date, VDS_num, penalty, aggregate_timeframe, min_length, method):
# # This is the version of the previous studies focusing on the directly detect the peak periods

# import numpy as np
# import ruptures as rpt
# import pandas as pd

# def pelt_speedbased_directpeak(model, df, column, freeflow_speed, freeflow_speed_epsilon, 
#                          aggregate_timeframe, date, VDS_num, pelt_penalty, pelt_min_length, min_off_len, min_peak_len, method):
    
#     """
#     Detect peak periods using PELT on cumulative speed profile.

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
#     # print("Breakpoints:", bkpts)

#     ### In the actual PELT algorithm, a changepoint is assigned to the segment containing the preceding data points, so the index should be shifted forward by one.
#     real_bkpts = [0] + [i-1 for i in bkpts]
    
#     # Step 3: Label segments
#     df["division"] = 0
#     peak_list = []
#     prev_peak_end = 0
#     start = 0
#     length = 0
#     idx=0
#     start_com = 0

    
#     for end in real_bkpts:
#         seg_mean_speed = df[column].iloc[(start):(end+1)].mean()

#         if seg_mean_speed < (freeflow_speed - freeflow_speed_epsilon):
#             if start_com == start:
#                 df["division"].iloc[(start):(end+1)] = idx
                
#                 ## Since it is hard to explain, ignore including one more point at the congested period.
#                 # if end+1 <= (len(df) -1) :
#                 #     df["division"].iloc[(end+1)] = idx
                
#                 # df.loc[df.index[(start):(end+1)], 'division'] = idx
#                 # # df.loc[df.index[(start+1):(end+1)], 'division'] = idx
#                 # df.loc[df.index[(start-1)], 'division'] = idx
#                 start_com = end
#             else:
#                 idx +=1
#                 df["division"].iloc[(start):(end+1)] = idx
                
#                 ## Since it is hard to explain, ignore including one more point at the congested period.
#                 # if end+1 <= (len(df) -1) :
#                 #     df["division"].iloc[(end+1)] = idx
                
#                 # df.loc[df.index[(start):(end+1)], 'division'] = idx
#                 # df.loc[df.index[(start-1)], 'division'] = idx
#                 start_com = end
                
#         start = end
    
    
#     idx_lists = list(range(0,idx+1))

#     if len(idx_lists)>1 :
#         for idx in idx_lists[1:]:
#             df_filter = df[df['division']==idx]
#             start_time = df_filter['time_slot'].min() - aggregate_timeframe/2
#             end_time = df_filter['time_slot'].max() + aggregate_timeframe/2
#             length = end_time - start_time
            
#             peak_list.append({'idx': idx, 'start': f'{int(start_time // 60):02d}:{int(start_time % 60):02d}', 'end': f'{int(end_time // 60):02d}:{int(end_time % 60):02d}', 'length': length})
        
#     PELT_plot(df, real_bkpts, date, VDS_num, aggregate_timeframe, peak_list, method)

#     return df, peak_list

# + jupyter={"source_hidden": true}
import numpy as np
import pandas as pd
import ruptures as rpt

def pelt_speedbased_peak(
    model,
    df,
    column,
    offpeak_ff_speed_threshold,
    speed_gap_threshold,
    aggregate_timeframe,
    date,
    VDS_num,
    pelt_penalty,
    pelt_min_length,
    min_off_len,
    min_peak_len,
    method,
):
    """
    Detect peak periods using PELT on the (raw) speed series, then classify and post-process
    exactly like the optimized RDP pipeline:
      1) Segment via PELT
      2) Classify segments as off-peak vs peak (long&fast => off-peak; else => peak)
      3) Collapse adjacent peak rows into contiguous division IDs (1..K; off-peak=0)
      4) Drop 'island' divisions (small gap, high mean, isolated by off-peak)
      5) Renumber divisions to be consecutive
      6) Apply min_peak_len filter
      7) Build peak_list for plotting/reporting

    Notes:
      - Ruptures' PELT returns breakpoints as *end indices* (with the last one equal to n).
        We convert to standard half-open segments [start:end) using: starts = [0] + bkpts[:-1], ends = bkpts.
      - The function uses vectorized groupby/agg and cumsum tricks to avoid per-group loops.

    Returns
    -------
    df_out : DataFrame
        Original df with added 'segment' and 'division' columns.
    peak_list : list[dict]
        [{'idx': k, 'start': 'HH:MM', 'end': 'HH:MM', 'length': seconds}, ...]
    """
    df = df.copy()

    # 1) (Optional) cumulative curve if you prefer; kept for parity with RDP version
    cs_name = f"cumsum_{column}"
    df[cs_name] = df[column].cumsum() * aggregate_timeframe / 60.0  # minutes

    # 2) PELT segmentation over the raw speed series (works well for level/slope shifts)
    signal = df[column].to_numpy()
    n = len(df)
    # min_size is in samples; pelt_min_length is in seconds ⇒ convert
    min_size = max(1, int(pelt_min_length / aggregate_timeframe))
    algo = rpt.Pelt(model=model, min_size=min_size, jump=1).fit(signal)

    bkpts = algo.predict(pen=pelt_penalty)  # list of end indices; last should be n
    # Safety: ensure last point included
    if bkpts[-1] != n:
        bkpts.append(n)

    # Build half-open segment bounds [start:end)
    starts = [0] + bkpts[:-1]
    ends   = bkpts

    # 3) Assign segment IDs (1..S) using positions; avoid chained assignment
    seg_id = np.zeros(n, dtype=np.int32)
    seg = 1
    for s, e in zip(starts, ends):
        if e > s:                       # ignore degenerate pieces
            seg_id[s:e] = seg
            seg += 1
    df["segment"] = seg_id

    # 4) Per-segment stats (vectorized)
    seg_stats = (
        df.groupby("segment")[column]
          .agg(seg_mean="mean", seg_min="min", seg_max="max", seg_size="size")
          .reset_index()
    )
    seg_stats["seg_len_sec"] = seg_stats["seg_size"] * aggregate_timeframe

    # 5) Off-peak vs peak for each segment (your rule)
    is_offpeak_seg = (seg_stats["seg_len_sec"] >= min_off_len) & \
                     (seg_stats["seg_mean"] >= offpeak_ff_speed_threshold)
    seg_stats["is_peak_seg"] = ~is_offpeak_seg

    # Map segment-level labels back to each row (one boolean per row)
    is_peak = (
        seg_stats
        .set_index("segment")["is_peak_seg"]
        .reindex(df["segment"])
        .to_numpy()
    )

    # 6) Collapse adjacent peak rows into block ids: 0 for off-peak, 1..K for peaks
    starts_flag = (is_peak) & (~pd.Series(is_peak).shift(fill_value=False).to_numpy())
    peak_block_id = starts_flag.cumsum()
    peak_block_id[~is_peak] = 0
    df["division"] = peak_block_id.astype(np.int32)

    # 7) Remove "short high-speed islands" (isolated peak blocks that look like free-flow)
    #    Division-level stats
    if df["division"].max() > 0:
        div_stats = (
            df.loc[df["division"] > 0]
              .groupby("division")[column]
              .agg(avg_speed="mean", vmin="min", vmax="max", size="size")
              .reset_index()
        )
        div_stats["speed_gap"] = div_stats["vmax"] - div_stats["vmin"]
        div_stats["len_sec"]   = div_stats["size"] * aggregate_timeframe

        # Division bounds (first/last indices) in a vectorized way
        first_idx = (
            df.loc[df["division"] > 0]
              .groupby("division")
              .head(1)
              .groupby("division")
              .apply(lambda g: g.index[0])
        )
        last_idx = (
            df.loc[df["division"] > 0]
              .groupby("division")
              .tail(1)
              .groupby("division")
              .apply(lambda g: g.index[0])
        )
        div_bounds = pd.DataFrame(
            {"division": first_idx.index, "first": first_idx.values, "last": last_idx.values}
        )
        div_all = div_stats.merge(div_bounds, on="division", how="left")

        div_arr = df["division"].to_numpy()
        first_arr = div_all["first"].to_numpy()
        last_arr  = div_all["last"].to_numpy()

        prev_div_vals = np.where(first_arr > 0, div_arr[first_arr - 1], 0)
        next_div_vals = np.where(last_arr  < n - 1, div_arr[last_arr + 1], 0)

        island_mask = (
            (div_all["speed_gap"] <= speed_gap_threshold) &
            (div_all["avg_speed"] >  offpeak_ff_speed_threshold) &
            (prev_div_vals == 0) &
            (next_div_vals == 0)
        )
        islands = set(div_all.loc[island_mask, "division"].to_numpy())
        if islands:
            df.loc[df["division"].isin(islands), "division"] = 0

            # Rebuild contiguous division IDs after island removal
            is_peak2 = df["division"].to_numpy() > 0
            starts2  = (is_peak2) & (~pd.Series(is_peak2).shift(fill_value=False).to_numpy())
            peak_block_id2 = starts2.cumsum()
            peak_block_id2[~is_peak2] = 0
            df["division"] = peak_block_id2.astype(np.int32)

    # 8) Apply min_peak_len filter (drop very short peaks), then renumber again
    if df["division"].max() > 0 and (min_peak_len is not None) and (min_peak_len > 0):
        bounds_tmp = (
            df.loc[df["division"] > 0]
              .groupby("division")["time_slot"]
              .agg(["min", "max"])
              .reset_index()
        )
        # Use ± half bin to get inclusive duration
        bounds_tmp["start_time"] = bounds_tmp["min"] - aggregate_timeframe / 2
        bounds_tmp["end_time"]   = bounds_tmp["max"] + aggregate_timeframe / 2
        bounds_tmp["length"]     = bounds_tmp["end_time"] - bounds_tmp["start_time"]

        short_divs = set(bounds_tmp.loc[bounds_tmp["length"] < min_peak_len, "division"].to_numpy())
        if short_divs:
            df.loc[df["division"].isin(short_divs), "division"] = 0
            # Renumber after removal
            is_peak3 = df["division"].to_numpy() > 0
            starts3  = (is_peak3) & (~pd.Series(is_peak3).shift(fill_value=False).to_numpy())
            peak_block_id3 = starts3.cumsum()
            peak_block_id3[~is_peak3] = 0
            df["division"] = peak_block_id3.astype(np.int32)

    # 9) Build peak_list (vectorized)
    if df["division"].max() > 0:
        bounds = (
            df.loc[df["division"] > 0]
              .groupby("division")["time_slot"]
              .agg(["min", "max"])
              .reset_index()
        )
        bounds["start_time"] = bounds["min"] - aggregate_timeframe / 2
        bounds["end_time"]   = bounds["max"] + aggregate_timeframe / 2
        bounds["length"]     = bounds["end_time"] - bounds["start_time"]

        peak_list = [
            {
                "idx": int(row["division"]),
                "start": f"{int(row['start_time'] // 60):02d}:{int(row['start_time'] % 60):02d}",
                "end":   f"{int(row['end_time']   // 60):02d}:{int(row['end_time']   % 60):02d}",
                "length": float(row["length"]),
            }
            for _, row in bounds.iterrows()
        ]
    else:
        peak_list = []

    # Optional: visualize (uses your existing function)
    # For plotting consistency with your RDP plotter, pass 'bkpts' (end indices)
    PELT_plot(df, bkpts, date, VDS_num, aggregate_timeframe, peak_list, method, pelt_penalty)

    return df, peak_list


# + jupyter={"source_hidden": true}
# # def pelt_speedbased_peak(df, column, speed_upper, model, date, VDS_num, penalty, aggregate_timeframe, min_length, method):
# import numpy as np
# import ruptures as rpt
# import pandas as pd

# def pelt_speedbased_peak(model, df, column, offpeak_ff_speed_threshold, speed_gap_threshold,
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
#     print("PELT_Breakpoints:", bkpts)

#     ### In the actual PELT algorithm, a changepoint is assigned to the segment containing the preceding data points, so the index should be shifted forward by one.
#     real_bkpts = [0] + [i-1 for i in bkpts]
    
#     # Step 3: Label segments
#     df["division"] = 0
#     peak_list = []
#     idx = 0
#     prev_peak_end = 0

#     for start, end in zip(real_bkpts[:-1], real_bkpts[1:]):
#         seg_mean = df[column].iloc[(start):(end+1)].mean()
#         seg_len = (end+1 - start) * aggregate_timeframe

#         if seg_len > min_off_len and seg_mean > offpeak_ff_speed_threshold:
#             continue
#         else:
#             # if prev_peak_end != start:
#             idx += 1
#             ## Based on the changepoint optimization formula, the segment is (
#             # df["division"].iloc[(start+1):(end)] = idx
#             df["division"].iloc[(start):(end+1)] = idx
    
    
#     for div_idx, group in df.groupby("division"):

#         if div_idx == 0:
#             continue
#         else:
#             speed_gap = group["speed"].max() -  group["speed"].min()
#             avg_speed = group["speed"].mean()
            

#             first_idx = df.index[df['division'] == div_idx][0]  # index of the first matching row
#             last_idx = df.index[df['division'] == div_idx][-1]  # index of the first matching row
            
#             # previous division (if out of range → treat as 0)
#             prev_div = df.loc[first_idx - 1, 'division'] if first_idx > df.index[0] else 3            
#             # next division (if out of range → treat as 0)
#             next_div = df.loc[last_idx + 1, 'division'] if last_idx < df.index[-1] else 3
        
#             if speed_gap <= speed_gap_threshold and avg_speed > offpeak_ff_speed_threshold and prev_div==0 and next_div==0:
#                 df.loc[df['division'] == div_idx, 'division'] = 0
#                 # df.loc[df['division'] > div_idx, 'division'] -= 1

#     # # make division labels consecutive: e.g., [0,1,3] -> [0,1,2]
        
#     idx_f = 0
#     for div_idx, group in df.groupby("division"):
        
#         if div_idx != 0:
#             start = df.index[df['division'] == div_idx][0]  # index of the first matching row
#             prev_peak_temp = df.index[df['division'] == div_idx][-1]+1  # index of the first maxching row    
            
#             if prev_peak_end == start:
#                 df.loc[df['division']==div_idx,'division'] = idx_f
#             else:
#                 idx_f +=1
#                 df.loc[df['division']==div_idx,'division'] = idx_f
#             prev_peak_end = prev_peak_temp
    
#     for div_idx, group in df.groupby("division"):
#         start_time = group["time_slot"].min()
#         end_time = group["time_slot"].max()
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


#     PELT_plot(df, real_bkpts, date, VDS_num, aggregate_timeframe, peak_list, method, pelt_penalty)

#     return df, peak_list

# + jupyter={"source_hidden": true}
# # def pelt_speedbased_peak(df, column, speed_upper, model, date, VDS_num, penalty, aggregate_timeframe, min_length, method):
# import numpy as np
# import ruptures as rpt
# import pandas as pd

# def pelt_speedbased_peak(model, df, column, offpeak_ff_speed_threshold,
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
#     print("PELT_Breakpoints:", bkpts)

#     ### In the actual PELT algorithm, a changepoint is assigned to the segment containing the preceding data points, so the index should be shifted forward by one.
#     real_bkpts = [0] + [i-1 for i in bkpts]
    
#     # Step 3: Label segments
#     df["division"] = 0
#     peak_list = []
#     idx = 0
#     prev_peak_end = 0

#     for start, end in zip(real_bkpts[:-1], real_bkpts[1:]):
#         seg_mean = df[column].iloc[(start):(end+1)].mean()
#         seg_len = (end+1 - start) * aggregate_timeframe

#         print(start,seg_mean)
#         if seg_len > min_off_len and seg_mean > offpeak_ff_speed_threshold:
#             continue
#         else:
#             if prev_peak_end != start:
#                 idx += 1
#             ## Based on the changepoint optimization formula, the segment is (
#             # df["division"].iloc[(start+1):(end)] = idx
#             df["division"].iloc[(start):(end+1)] = idx
            
#             ## Since it is hard to explain, ignore including one more point at the congested period.
#             # if end+1 <= (len(df) -1) :
#             #     df["division"].iloc[(end+1)] = idx
            
#             prev_peak_end = end
    
#     for div_idx, group in df.groupby("division"):
#         start_time = group["time_slot"].min()
#         end_time = group["time_slot"].max()
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


#     PELT_plot(df, real_bkpts, date, VDS_num, aggregate_timeframe, peak_list, method, pelt_penalty)

#     return df, peak_list

# +
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
# -



# +
import numpy as np
import pandas as pd

def _compute_seg_stats(df, value_col, aggregate_timeframe):
    """
    Returns per-segment stats: mean/min/max/size and length in seconds.
    Expects df['segment'] already assigned.
    """
    seg_stats = (
        df.groupby("segment")[value_col]
          .agg(seg_mean="mean", seg_min="min", seg_max="max", seg_size="size")
          .reset_index()
    )
    seg_stats["seg_len_sec"] = seg_stats["seg_size"] * aggregate_timeframe
    
    return seg_stats

def _divisions_from_segment_mask(df, is_peak_seg_bool):
    """
    Map a per-segment boolean (True=peak) to per-row 'division' labels:
    0 for off-peak rows; 1..K for contiguous peak blocks.
    """
    is_peak_rows = (
        pd.Series(is_peak_seg_bool, index=is_peak_seg_bool.index)
          .reindex(df["segment"])
          .to_numpy()
    )
    starts = (is_peak_rows) & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())

    div = starts.cumsum()
    
    div[~is_peak_rows] = 0
    return div.astype(np.int32)

def _renumber_by_contiguity(div):
    """
    Renumber any positive divisions to 1..K by contiguity; zeros stay zero.
    """
    is_peak = div > 0
    starts  = (is_peak) & (~pd.Series(is_peak).shift(fill_value=False).to_numpy())
    new_ids = starts.cumsum()
    new_ids[~is_peak] = 0
    return new_ids.astype(np.int32)

def _build_peak_list(df, aggregate_timeframe):
    """
    Build [{'idx', 'start','end','length'}] from df['division'] and df['time_slot'] (seconds).
    Uses ± half-bin convention for boundaries.
    """
    if df["division"].max() <= 0:
        return []
    bounds = (
        df.loc[df["division"] > 0]
          .groupby("division")["time_slot"]
          .agg(["min", "max"])
          .reset_index()
    )
    bounds["start_time"] = bounds["min"] - aggregate_timeframe / 2
    bounds["end_time"]   = bounds["max"] + aggregate_timeframe / 2
    bounds["length"]     = bounds["end_time"] - bounds["start_time"]
    return [
        {
            "idx": int(row["division"]),
            "start": f"{int(row['start_time'] // 60):02d}:{int(row['start_time'] % 60):02d}",
            "end":   f"{int(row['end_time']   // 60):02d}:{int(row['end_time']   % 60):02d}",
            "length": float(row["length"]),
        }
        for _, row in bounds.iterrows()
    ]



# -

def label_divisions_speed(
    df,
    column,
    aggregate_timeframe,
    min_off_len,
    offpeak_ff_speed_threshold,
    speed_gap_threshold
):
    """
    1) Off-peak vs peak per segment by speed & duration.
    2) Collapse to contiguous peak blocks -> df['division'].
    3) Remove 'islands' (small gap, high mean, isolated by off-peak neighbors).
    4) Renumber by contiguity.
    Returns: df with 'division' updated (np.int32)
    """
    # --- 1) Per-segment stats (already computed above) ---
    # seg_stats has: columns ['segment','seg_mean','seg_min','seg_max','seg_size','seg_len_sec']
    seg_stats = _compute_seg_stats(df, column, aggregate_timeframe)
    
    # --- 2) Initial classification (your baseline rule) ---
    is_offpeak_seg = (seg_stats["seg_len_sec"] >= min_off_len) & \
                     (seg_stats["seg_mean"]    >= offpeak_ff_speed_threshold)
    
    is_peak_seg = ~is_offpeak_seg
    
    # --- 5) Demote peaks that are NOT isolated-offpeak but look free-flow ---
    # “firstly detected as congested” = is_peak_seg
    # Need to convert to uncongested if (~isolated_offpeak & looks_freeflow)
    is_peak_seg_final = is_peak_seg
    
    # Re-index by segment id for mapping to rows
    is_peak_seg_final.index = seg_stats["segment"]
    
    # --- 6) Map to rows and collapse to contiguous divisions ---
    is_peak_rows = (
        pd.Series(is_peak_seg_final, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy()
    )
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    df["division"] = div.astype(np.int32)

    return df



def label_divisions_speedgap_islands(
    df,
    column,
    aggregate_timeframe,
    min_off_len,
    offpeak_ff_speed_threshold,
    speed_gap_threshold
):
    """
    1) Off-peak vs peak per segment by speed & duration.
    2) Collapse to contiguous peak blocks -> df['division'].
    3) Remove 'islands' (small gap, high mean, isolated by off-peak neighbors).
    4) Renumber by contiguity.
    Returns: df with 'division' updated (np.int32)
    """
    # --- 1) Per-segment stats (already computed above) ---
    # seg_stats has: columns ['segment','seg_mean','seg_min','seg_max','seg_size','seg_len_sec']
    seg_stats = _compute_seg_stats(df, column, aggregate_timeframe)
    seg_stats["speed_gap"] = seg_stats["seg_max"] - seg_stats["seg_min"]
    
    # --- 2) Initial classification (your baseline rule) ---
    is_offpeak_seg = (seg_stats["seg_len_sec"] >= min_off_len) & \
                     (seg_stats["seg_mean"]    >= offpeak_ff_speed_threshold)
    is_peak_amb_seg = (seg_stats["seg_len_sec"] < min_off_len) & \
                     (seg_stats["seg_mean"]    >= offpeak_ff_speed_threshold)
    
    is_peak_seg = ~is_offpeak_seg
    
    # (Optional) edge handling: treat ends as their own neighbor to avoid edge artifacts
    prev_is_peak = is_peak_seg.shift(1)
    next_is_peak = is_peak_seg.shift(-1)
    if not is_peak_seg.empty:
        prev_is_peak.iloc[0]  = is_peak_seg.iloc[0]
        next_is_peak.iloc[-1] = is_peak_seg.iloc[-1]
    
    # --- 3) Isolated OFF-PEAK: off-peak segment between two peak segments ---
    isolated_peak = is_peak_amb_seg & prev_is_peak & next_is_peak
    
    # --- 4) "Looks free-flow" (flat & fast) ---
    looks_freeflow = (seg_stats["speed_gap"] < speed_gap_threshold)
    
    # --- 5) Demote peaks that are NOT isolated-offpeak but look free-flow ---
    # “firstly detected as congested” = is_peak_seg
    # Need to convert to uncongested if (~isolated_offpeak & looks_freeflow)
    demote_mask = is_peak_amb_seg & (~isolated_peak) & looks_freeflow
    is_peak_seg_final = is_peak_seg & (~demote_mask)
    
    # Re-index by segment id for mapping to rows
    is_peak_seg_final.index = seg_stats["segment"]
    
    # --- 6) Map to rows and collapse to contiguous divisions ---
    is_peak_rows = (
        pd.Series(is_peak_seg_final, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy()
    )
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    df["division"] = div.astype(np.int32)

    return df




# + jupyter={"source_hidden": true}
# def label_divisions_speedgap_islands(
#     df,
#     column,
#     aggregate_timeframe,
#     min_off_len,
#     offpeak_ff_speed_threshold,
#     speed_gap_threshold
# ):
#     """
#     1) Off-peak vs peak per segment by speed & duration.
#     2) Collapse to contiguous peak blocks -> df['division'].
#     3) Remove 'islands' (small gap, high mean, isolated by off-peak neighbors).
#     4) Renumber by contiguity.
#     Returns: df with 'division' updated (np.int32)
#     """
#     # Per-segment stats on the speed column
#     seg_stats = _compute_seg_stats(df, column, aggregate_timeframe)

#     # Rule: off-peak if long enough AND fast enough
#     is_offpeak_seg = (seg_stats["seg_len_sec"] >= min_off_len) & \
#                      (seg_stats["seg_mean"]    >= offpeak_ff_speed_threshold)
#     is_peak_seg = ~is_offpeak_seg
#     is_peak_seg.index = seg_stats["segment"]  # ensure index=segment ids

#     # Map to rows and build divisions
#     div = _divisions_from_segment_mask(df, is_peak_seg)
#     df = df.copy()

#     df["division"] = div

#     # Division-level stats for island detection
#     if df["division"].max() > 0:
#         div_stats = (
#             df.loc[df["division"] > 0]
#               .groupby("division")[column]
#               .agg(avg_speed="mean", vmin="min", vmax="max", size="size")
#               .reset_index()
#         )
#         div_stats["speed_gap"] = div_stats["vmax"] - div_stats["vmin"]
#         div_stats["len_sec"]   = div_stats["size"] * aggregate_timeframe

#         # First/last indices per division (vectorized)
#         first_idx = (
#             df.loc[df["division"] > 0]
#               .groupby("division").head(1)
#               .groupby("division").apply(lambda g: g.index[0])
#         )
#         last_idx = (
#             df.loc[df["division"] > 0]
#               .groupby("division").tail(1)
#               .groupby("division").apply(lambda g: g.index[0])
#         )
#         div_bounds = pd.DataFrame(
#             {"division": first_idx.index, "first": first_idx.values, "last": last_idx.values}
#         )
#         div_all = div_stats.merge(div_bounds, on="division", how="left")


#         # Neighbor divisions (0 if OOB)
#         n = len(df)
#         div_arr   = df["division"].to_numpy()
#         first_arr = div_all["first"].to_numpy()
#         last_arr  = div_all["last"].to_numpy()
        
#         prev_div = np.take(div_arr, first_arr - 1, mode="clip")
#         prev_div[first_arr <= 0] = 0
        
#         next_div = np.take(div_arr, last_arr + 1, mode="clip")
#         next_div[last_arr >= n - 1] = 0


#         # Island mask: small gap + high mean + surrounded by off-peak
#         island_mask = (
#             (div_all["speed_gap"] <= speed_gap_threshold) &
#             (div_all["avg_speed"] >  offpeak_ff_speed_threshold) &
#             (prev_div == 0) & (next_div == 0)
#         )
#         islands = set(div_all.loc[island_mask, "division"].to_numpy())
#         if islands:
#             df.loc[df["division"].isin(islands), "division"] = 0
#             df["division"] = _renumber_by_contiguity(df["division"].to_numpy())

#     return df

# -

def label_divisions_occupancy(
    df,
    column,
    aggregate_timeframe,
    min_off_len,
    offpeak_ff_speed_threshold,
    speed_gap_threshold,
    occ_threshold
):
    """
    1) Off-peak vs peak per segment by speed & duration.
    2) Collapse to contiguous peak blocks -> df['division'].
    3) Remove 'islands' (small gap, high mean, isolated by off-peak neighbors).
    4) Renumber by contiguity.
    Returns: df with 'division' updated (np.int32)
    """
    # Per-segment stats on the speed column
    seg_stats_speed = _compute_seg_stats(df, 'speed', aggregate_timeframe)
    seg_stats_occ = _compute_seg_stats(df, 'occ', aggregate_timeframe)
    
    # --- 2) Initial classification (your baseline rule) ---
    is_offpeak_seg = (seg_stats_speed["seg_len_sec"] >= min_off_len) & \
                     (seg_stats_speed["seg_mean"]    >= offpeak_ff_speed_threshold)
    
    is_peak_seg = ~is_offpeak_seg

    looks_freeflow = (seg_stats_occ["seg_mean"] < occ_threshold)

    # --- 5) Demote peaks that are NOT isolated-offpeak but look free-flow ---
    # “firstly detected as congested” = is_peak_seg
    # Need to convert to uncongested if (~isolated_offpeak & looks_freeflow)
    demote_mask = is_peak_seg & looks_freeflow
    is_peak_seg_final = is_peak_seg & (~demote_mask)
    
    # Re-index by segment id for mapping to rows
    is_peak_seg_final.index = seg_stats["segment"]
    
    # --- 6) Map to rows and collapse to contiguous divisions ---
    is_peak_rows = (
        pd.Series(is_peak_seg_final, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy()
    )
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    df["division"] = div.astype(np.int32)

    return df


def label_soley_occupancy(
    df,
    column,
    aggregate_timeframe,
    min_off_len,
    offpeak_ff_speed_threshold,
    speed_gap_threshold,
    occ_threshold
):
    """
    1) Off-peak vs peak per segment by speed & duration.
    2) Collapse to contiguous peak blocks -> df['division'].
    3) Remove 'islands' (small gap, high mean, isolated by off-peak neighbors).
    4) Renumber by contiguity.
    Returns: df with 'division' updated (np.int32)
    """
    # Per-segment stats on the speed column
    seg_stats_occ = _compute_seg_stats(df, 'occ', aggregate_timeframe)
    
    # --- 2) Initial classification (your baseline rule) ---
    is_offpeak_seg = (seg_stats_speed["seg_len_sec"] >= min_off_len) & \
                     (seg_stats_speed["seg_mean"]    < occ_threshold)
    
    is_peak_seg = ~is_offpeak_seg
    is_peak_seg_final = is_peak_seg
    
    # Re-index by segment id for mapping to rows
    is_peak_seg_final.index = seg_stats["segment"]
    
    # --- 6) Map to rows and collapse to contiguous divisions ---
    is_peak_rows = (
        pd.Series(is_peak_seg_final, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy()
    )
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    df["division"] = div.astype(np.int32)

    return df



# +
from rdp import rdp
import numpy as np
import pandas as pd

def rdp_v_segmentation_peak(
    df, column, epsilon, offpeak_ff_speed_threshold, speed_gap_threshold,
    aggregate_timeframe, date, VDS_num, min_off_len, min_peak_len, method, congest_method, occ_threshold
):
    df = df.copy()

    # 1) cumulative curve (minutes)
    cs_name = f"cumsum_{column}"
    df[cs_name] = df[column].cumsum() * aggregate_timeframe / 60.0

    # 2) RDP on (pos, cumsum)
    pos = np.arange(len(df))
    pts = np.column_stack([pos, df[cs_name].to_numpy()])
    bp = rdp_v(pts, epsilon)[:, 0].astype(int)  # vertical-distance RDP
    if bp[-1] != pos[-1]:
        bp = np.append(bp, pos[-1])

    # 3) Assign segment ids via slices (fast, no chained assignment)
    seg_id = np.zeros(len(df), dtype=np.int32)
    seg = 0
    for s, e in zip(bp[:-1], bp[1:]):
        seg += 1
        seg_id[s:e] = seg
        
    seg_id[-1] = seg  # last point (to mirror your original behavior)
    df["segment"] = seg_id

    
    if congest_method == 'speedgap_neighbor':
        # Strategy A: speed gap + neighbor isolation
        df = label_divisions_speedgap_islands(
            df=df, column="speed", aggregate_timeframe=aggregate_timeframe,min_off_len=min_off_len,
            offpeak_ff_speed_threshold=offpeak_ff_speed_threshold,
            speed_gap_threshold=speed_gap_threshold)
        peak_list = _build_peak_list(df, aggregate_timeframe)
    
    elif congest_method == 'occ':
        # Strategy B: occupancy-based (no islands)
        df = label_divisions_occupancy(
            df=df, occ_column="occ",          # e.g., your occupancy column name
            aggregate_timeframe=aggregate_timeframe, min_off_len=min_off_len, occ_threshold=occ_threshold)     # e.g., 0.10 (10%) or whatever scale you use)
        peak_list = _build_peak_list(df, aggregate_timeframe)

    # 9) Plot + return (reuse your existing plotter)
    PELT_plot(df, bp.tolist(), date, VDS_num, aggregate_timeframe, peak_list, method, epsilon)
    return df, peak_list

# -



# + jupyter={"source_hidden": true}
# # 4) Per-segment stats (vectorized)
#     seg_stats = df.groupby("segment")[column].agg(
#         seg_mean="mean", seg_min="min", seg_max="max", seg_size="size"
#     ).reset_index()
#     seg_stats["seg_len_sec"] = seg_stats["seg_size"] * aggregate_timeframe

#     # 5) Off-peak vs peak for each segment (your rule)
#     # Off-peak if (long enough) AND (fast enough); otherwise peak
#     is_offpeak_seg = (seg_stats["seg_len_sec"] >= min_off_len) & \
#                      (seg_stats["seg_mean"] >= offpeak_ff_speed_threshold)
#     ## True where segment is peak)
#     seg_stats["is_peak_seg"] = ~is_offpeak_seg

#     # Map back to rows
#     # So (is_peak) & (~shifted) is True only when: The current row is peak and The previous row was not peak
#     is_peak = seg_stats.set_index("segment")["is_peak_seg"].reindex(df["segment"]).to_numpy()

#     # 6) Collapse adjacent peak rows into block ids: 0 for off-peak, 1..K for peaks
#     #    This: every time we hit a peak True preceded by False, create a new block id.
#     #  Detect where new “peak blocks” begin: [0, 0, 1, 1, 0, 2, 2, 2, 0]
#     starts = (is_peak) & (~pd.Series(is_peak).shift(fill_value=False).to_numpy())
#     peak_block_id = starts.cumsum() # peak_block_id = [0, 0, 1, 1, 1, 2, 2, 2, 2] 
#     peak_block_id[~is_peak] = 0  # off-peak -> 0 # [0, 0, 1, 1, 0, 2, 2, 2, 0]
#     df["division"] = peak_block_id.astype(np.int32)

#     # 7) Remove “short high-speed islands” that are isolated (surrounded by off-peak)
#     #    Precompute per-division stats once
#     #    (Ignore division==0)
#     div_stats = df.loc[df["division"] > 0].groupby("division")[column].agg(
#         avg_speed="mean", vmin="min", vmax="max", size="size"
#     ).reset_index()
#     div_stats["speed_gap"] = div_stats["vmax"] - div_stats["vmin"]
#     div_stats["len_sec"] = div_stats["size"] * aggregate_timeframe

#     # Build fast lookup arrays for division first/last indices
#     # (no df.index[df['division']==k] calls)
#     # Compute each division’s first and last indices (once, efficiently)
#     first_idx = df.loc[df["division"] > 0].groupby("division").head(1).groupby("division").apply(lambda g: g.index[0])
#     last_idx  = df.loc[df["division"] > 0].groupby("division").tail(1).groupby("division").apply(lambda g: g.index[0])
#     div_bounds = pd.DataFrame({"division": first_idx.index, "first": first_idx.values, "last": last_idx.values})

#     div_all = div_stats.merge(div_bounds, on="division", how="left")

#     # Check neighbors are off-peak (0) without out-of-bounds branching
#     # Use np.where with bounds checks once
#     n = len(df)
#     prev_div_vals = np.where(div_all["first"].to_numpy() > 0,
#                              df["division"].to_numpy()[div_all["first"].to_numpy() - 1],
#                              0)
#     next_div_vals = np.where(div_all["last"].to_numpy() < (n - 1),
#                              df["division"].to_numpy()[div_all["last"].to_numpy() + 1],
#                              0)

#     # Islands to clear: small gap + high mean + isolated
#     island_mask = (div_all["speed_gap"] <= speed_gap_threshold) & \
#                   (div_all["avg_speed"] > offpeak_ff_speed_threshold) & \
#                   (prev_div_vals == 0) & (next_div_vals == 0)

#     islands = set(div_all.loc[island_mask, "division"].to_numpy())
#     if islands:
#         df.loc[df["division"].isin(islands), "division"] = 0

#         # Renumber remaining positive divisions to be consecutive by contiguous blocks
#         is_peak2 = df["division"].to_numpy() > 0
#         starts2 = (is_peak2) & (~pd.Series(is_peak2).shift(fill_value=False).to_numpy())
#         peak_block_id2 = starts2.cumsum()
#         peak_block_id2[~is_peak2] = 0
#         df["division"] = peak_block_id2.astype(np.int32)
# -





# +
# # using rdp but error metric as vertical distance

# from rdp import rdp
# import numpy as np
# import pandas as pd

# def rdp_v_segmentation_peak(df, column, epsilon, offpeak_ff_speed_threshold, speed_gap_threshold,
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

#     # min_offpeak_hour = 4

#     # if (len(df[df[column] < (freeflow_speed - freeflow_speed_epsilon-5)]) / len(df[column])) < (0.5 / 24):
#     #     min_offpeak_hour = 24

#     freeflow_speed_tol = max(df[column].iloc[0:int(4*60/5)].mean(),df[column].iloc[-int(4*60/5):].mean(), 60)
#     max_margin = 2
#     avg_speed = min(df[column].mean(), freeflow_speed_tol-max_margin)

#     # epsilon = theta / avg_speed
#     # print("avg_speed",avg_speed, epsilon)
#     # k=7.1
    
#     # Apply RDP
#     points = np.column_stack([df.index, df["cumsum_" + column].values])
#     rdp_indices = rdp_v(points, epsilon)[:, 0].astype(int).tolist()
#     if rdp_indices[-1] != df.index[-1]:
#         rdp_indices.append(df.index[-1])

#     print("RDP_Breakpoints:", rdp_indices)
#     df["division"] = 0
#     df["segment"] = 0
#     peak_list = []
    
#     idx = 0
#     idx_seg = 1
#     prev_peak_end = 0

#     print("rdp_indices",rdp_indices)

#     for start, end in zip(rdp_indices[:-1], rdp_indices[1:]):
#         seg_mean = df[column].iloc[(start):(end)].mean()
#         seg_len = (end - start) * aggregate_timeframe

#         df["segment"].iloc[start:end] = idx_seg
#         idx_seg += 1
        
#         # detect off-peak period first(length, speed)
#         if seg_len >= min_off_len and seg_mean >= offpeak_ff_speed_threshold:
#             continue
#         else:
#             print(start,end)
#             idx += 1
#             df["division"].iloc[start:end] = idx
#             # df["division"].iloc[start] = idx
#     df["segment"].iloc[-1] = idx_seg
            
#             ## Since it is hard to explain, ignore including one more point at the congested period.
#             # if end+1 <= (len(df) -1) :
#             #     df["division"].iloc[(end+1)] = idx
                    
        
#     for div_idx, group in df.groupby("division"):

#         if div_idx == 0:
#             continue
#         else:
#             speed_gap = group["speed"].max() -  group["speed"].min()
#             avg_speed = group["speed"].mean()
#             print(speed_gap,"gap")

#             first_idx = df.index[df['division'] == div_idx][0]  # index of the first matching row
#             last_idx = df.index[df['division'] == div_idx][-1]  # index of the first matching row
            
#             # previous division (if out of range → treat as 0)
#             prev_div = df.loc[first_idx - 1, 'division'] if first_idx > df.index[0] else 3            
#             # next division (if out of range → treat as 0)
#             next_div = df.loc[last_idx + 1, 'division'] if last_idx < df.index[-1] else 3
        
#             if speed_gap <= speed_gap_threshold and avg_speed > offpeak_ff_speed_threshold and prev_div==0 and next_div==0:
#                 df.loc[df['division'] == div_idx, 'division'] = 0
#                 # df.loc[df['division'] > div_idx, 'division'] -= 1

#     # # make division labels consecutive: e.g., [0,1,3] -> [0,1,2]
        
#     idx_f = 0
#     for div_idx, group in df.groupby("division"):
        
#         if div_idx != 0:
#             start = df.index[df['division'] == div_idx][0]  # index of the first matching row
#             prev_peak_temp = df.index[df['division'] == div_idx][-1]+1  # index of the first maxching row    
            
#             if prev_peak_end == start:
#                 df.loc[df['division']==div_idx,'division'] = idx_f
#             else:
#                 idx_f +=1
#                 df.loc[df['division']==div_idx,'division'] = idx_f
#             prev_peak_end = prev_peak_temp

#     # uniq = sorted(v for v in df['division'].unique() if v != 0)
#     # mapping = {0: 0, **{old: new for new, old in enumerate(uniq, start=1)}}
#     # df['division'] = df['division'].map(mapping).astype(int)
    
#     print("unique after", df['division'].unique())

#     for div_idx, group in df.groupby("division"):    
#             start_time = group["time_slot"].min() - aggregate_timeframe/2
#             end_time = group["time_slot"].max() + aggregate_timeframe/2
#             # start_time = group["time_slot"].min() 
#             # end_time = group["time_slot"].max()
#             seg_len = end_time - start_time
    
#             # if seg_len < min_peak_len and div_idx != 0:
#             #     df.loc[df['division'] == div_idx, 'division'] = -1
#             #     div_idx = -1
    
#             if div_idx != 0:
#                 peak_list.append({
#                     "idx": div_idx,
#                     "start": f"{int(start_time // 60):02d}:{int(start_time % 60):02d}",
#                     "end": f"{int(end_time // 60):02d}:{int(end_time % 60):02d}",
#                     "length": seg_len
#                 })

#     PELT_plot(df, rdp_indices, date, VDS_num, aggregate_timeframe, peak_list, method, epsilon)

#     return df, peak_list

# + jupyter={"source_hidden": true}
# # using rdp but error metric as vertical distance

# from rdp import rdp
# import numpy as np
# import pandas as pd

# def rdp_v_segmentation_peak(df, column, epsilon, offpeak_ff_speed_threshold, speed_gap_threshold,
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

#     # min_offpeak_hour = 4

#     # if (len(df[df[column] < (freeflow_speed - freeflow_speed_epsilon-5)]) / len(df[column])) < (0.5 / 24):
#     #     min_offpeak_hour = 24

#     freeflow_speed_tol = max(df[column].iloc[0:int(4*60/5)].mean(),df[column].iloc[-int(4*60/5):].mean(), 60)
#     # print(freeflow_speed_tol,"speed_tol")
#     max_margin = 2
#     # print("avg_speed",df[column].mean())
#     avg_speed = min(df[column].mean(), freeflow_speed_tol-max_margin)

#     # epsilon = theta / avg_speed
#     # print("avg_speed",avg_speed, epsilon)
#     # k=7.1
    
#     # Apply RDP
#     points = np.column_stack([df.index, df["cumsum_" + column].values])
#     rdp_indices = rdp_v(points, epsilon)[:, 0].astype(int).tolist()
#     if rdp_indices[-1] != df.index[-1]:
#         rdp_indices.append(df.index[-1])

#     print("RDP_Breakpoints:", rdp_indices)
#     df["division"] = 0
#     peak_list = []
#     idx = 0
#     prev_peak_end = 0

#     for start, end in zip(rdp_indices[:-1], rdp_indices[1:]):
#         seg_mean = df[column].iloc[(start):(end+1)].mean()
#         seg_len = (end+1 - start) * aggregate_timeframe

#         # detect off-peak period first(length, speed)
#         if seg_len > min_off_len and seg_mean > offpeak_ff_speed_threshold:
#             continue
#         else:
#             print(start,end)
#             idx += 1
#             df["division"].iloc[(start):(end+1)] = idx
#             # df["division"].iloc[start] = idx
            
#             ## Since it is hard to explain, ignore including one more point at the congested period.
#             # if end+1 <= (len(df) -1) :
#             #     df["division"].iloc[(end+1)] = idx
                    

#     print(df['division'].unique())


#     # if prev_peak_end != start:
#     #             idx += 1
#     # prev_peak_end = end
        
#     for div_idx, group in df.groupby("division"):

#         if div_idx == 0:
#             continue
#         else:
#             # speed_gap = group["speed"].max() -  group["speed"].min()
#             avg_speed = group["speed"].mean()
#             # print(speed_gap,"gap")

#             first_idx = df.index[df['division'] == div_idx][0]  # index of the first matching row
#             last_idx = df.index[df['division'] == div_idx][-1]  # index of the first matching row
            
#             # previous division (if out of range → treat as 0)
#             prev_div = df.loc[first_idx - 1, 'division'] if first_idx > df.index[0] else 3            
#             # next division (if out of range → treat as 0)
#             next_div = df.loc[last_idx + 1, 'division'] if last_idx < df.index[-1] else 3
        
#             if avg_speed > offpeak_ff_speed_threshold and prev_div==0 and next_div==0:
#                 df.loc[df['division'] == div_idx, 'division'] = 0
#                 # df.loc[df['division'] > div_idx, 'division'] -= 1

#     # # make division labels consecutive: e.g., [0,1,3] -> [0,1,2]
#     # uniq = sorted(v for v in df['division'].unique() if v != 0)
#     # mapping = {0: 0, **{old: new for new, old in enumerate(uniq, start=1)}}
#     # df['division'] = df['division'].map(mapping).astype(int)
        
#     idx_f = 1
#     for div_idx, group in df.groupby("division"):

#         start = df.index[df['division'] == div_idx][0]  # index of the first matching row
        
#         if div_idx != 0:
#             prev_peak_end = df.index[df['division'] == div_idx][-1]+1  # index of the first maxching row    
#             if prev_peak_end == start:
#                 df.loc[df['division']==div_idx,'division'] = idx_f
#             else:
#                 idx_f +=1
#                 df.loc[df['division']==div_idx,'division'] = idx_f
            
    
#     print("unique after", df['division'].unique())

#     for div_idx, group in df.groupby("division"):    
#             start_time = group["time_slot"].min() - aggregate_timeframe/2
#             end_time = group["time_slot"].max() + aggregate_timeframe/2
#             # start_time = group["time_slot"].min() 
#             # end_time = group["time_slot"].max()
#             seg_len = end_time - start_time
    
#             if seg_len < min_peak_len and div_idx != 0:
#                 df.loc[df['division'] == div_idx, 'division'] = -1
#                 div_idx = -1
    
#             if div_idx != 0:
#                 peak_list.append({
#                     "idx": div_idx,
#                     "start": f"{int(start_time // 60):02d}:{int(start_time % 60):02d}",
#                     "end": f"{int(end_time // 60):02d}:{int(end_time % 60):02d}",
#                     "length": seg_len
#                 })

#     PELT_plot(df, rdp_indices, date, VDS_num, aggregate_timeframe, peak_list, method, epsilon)

#     return df, peak_list

# +
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

# + jupyter={"source_hidden": true}
# # flow_good[0],len(group) is not true : lane_num consider!!!!


# def compute_metrics(group, division_idx, config, group_num):
#     """
#     Compute travel time, total demand, and period label for a traffic division.
#     """
#     flows = group[[f'flow_{i}' for i in config['lane_num']]].values.flatten()
#     speeds = group[[f'speed_{i}' for i in config['lane_num']]].values.flatten()
#     # I dont use the mask(because, speeds nan occurs when flow=density=0, when no vehicle passes, 
#     # but we have to consider this value for the average flow because it represents 0 vehicles pass throught this time interval
    
#     mask = ~np.isnan(speeds)
#     flow_good, speed_good = flows[mask], speeds[mask]
    
    
#     print("len",len(flow_good))
    
#     if config['temporal_scale'] in ('speedbasedpeak', 'peak') and division_idx != 0:
#         # len(group)-1 reason: 
#         # if congested period is detected as 8:00:30 ~ 8:55:30 then, the division==1 ranges will be 8:00:00 to 9:00:00. 
#         # so, we need to "-1" to eliminate each side of 2:30 min.
#         # time_duration = (len(group)-1) * config['aggregate_timeframe']
#         time_duration = (len(group)) * config['aggregate_timeframe']

#         # demand means total volumes during the congested period
#         # flow_good[0] = flow_good[0]/2
#         # flow_good[(len(flow_good)-1)] = flow_good[(len(flow_good)-1)]/2

#         sum_flow = flows.sum()
#         demand = sum_flow * (config['aggregate_timeframe']/60) / len(config['lane_num'])
#         # avg_flow = flow_good.mean() * len(group) / (len(group)-1)
#         avg_flow =  flows.mean()
#         t0 = group.time_slot.min()

#         sum_prod = (flow_good / speed_good).sum()
#         traveltime = sum_prod / sum_flow * 60
        
#         m, M = config['peak_periods']['morning']
#         a, A = config['peak_periods']['afternoon']

#         # start time
#         if m < t0 < M:
#             period = 'morning-peak'
#         elif a < t0 < A:
#             period = 'afternoon-peak'
#         else:
#             period = 'off-peak'
#     else:
#         sum_flow = flows.sum()
#         demand = sum_flow * (config['aggregate_timeframe']/60) / len(config['lane_num'])
#         avg_flow = flows.mean()
        
#         print("demand, avg_flow", demand/24, avg_flow)
#         print(len(flow_good))
        
#         # time_duration = (len(group)+group_num-1) * config['aggregate_timeframe']
#         time_duration = (len(group)) * config['aggregate_timeframe']
#         period = 'off-peak'

#         ## Actually, it needs to be revised, beacause it does not include the first/last half of the congested period part.
#         sum_prod = (flow_good / speed_good).sum()
#         traveltime = sum_prod / sum_flow * 60

#     return traveltime, demand, avg_flow, division_idx, period, time_duration

# +
## This is the version based on the entire lanes' average (flow, density)

def compute_metrics(group, division_idx, config, group_num, criterion):
    """
    Compute travel time, total demand, and period label for a traffic division.
    """
    flows = group['flow'].values.flatten()
    speeds = group['speed'].values.flatten()
    occs = group['occ'].values.flatten()
    
    mask = ~np.isnan(speeds)
    flow_good, speed_good, occ_good = flows[mask], speeds[mask], occs[mask]
    
    
    if config['temporal_scale'] in ('speedbasedpeak', 'peak') and division_idx != 0:
        # len(group)-1 reason: 
        # if congested period is detected as 8:00:30 ~ 8:55:30 then, the division==1 ranges will be 8:00:00 to 9:00:00. 
        # so, we need to "-1" to eliminate each side of 2:30 min.
        time_duration = (len(group)) * config['aggregate_timeframe']

        # demand means total volumes during the congested period
        # flow_good[0] = flow_good[0]/2
        # flow_good[(len(flow_good)-1)] = flow_good[(len(flow_good)-1)]/2

        sum_flow = flows.sum()
        demand = sum_flow * (config['aggregate_timeframe']/60)        
        avg_flow = flows.mean() 
        avg_occ = occs.mean()
        # avg_flow = flow_good.mean() * len(group) / (len(group)-1)
        
        t0 = group.time_slot.min()

        sum_prod = (flow_good / speed_good).sum()
        traveltime = sum_prod / sum_flow * 60
        speed = 1/traveltime * 60
        density = avg_flow / speed
        
        m, M = config['peak_periods']['morning']
        a, A = config['peak_periods']['afternoon']

        if criterion == "division":
            # start time
            if m < t0 < M:
                period = 'morning-peak'
            elif a < t0 < A:
                period = 'afternoon-peak'
            else:
                period = 'peak-in-offpeak'
                # period = 'off-peak'
        elif criterion == "segment":
            if (speed > config['speedbased_params']['offpeak_ff_speed_threshold']) and (time_duration > config['speedbased_params']['min_off_len']):
                period = 'uncongested'
            else:
                period = 'congested'

            
    else:
        sum_flow = flows.sum()
        
        demand = sum_flow * (config['aggregate_timeframe']/60) 
        avg_flow = flows.mean()
        avg_occ = occs.mean()
        
        # time_duration = (len(group)+group_num-1) * config['aggregate_timeframe']
        time_duration = (len(group)) * config['aggregate_timeframe']
        period = 'off-peak'

        ## Actually, it needs to be revised, beacause it does not include the first/last half of the congested period part.
        sum_prod = (flow_good / speed_good).sum()
        
        traveltime = sum_prod / sum_flow * 60
        speed = 1/traveltime * 60
        density = avg_flow / speed

    return traveltime, speed, demand, avg_flow, avg_occ, density, division_idx, period, time_duration
# -

# #### (code) implementation

# +
### Old-version(2025/10/15)

# Parameters for handling the data
# raw_timeframe: Defines the timeframe unit in minutes for the input raw data 
# (e.g., 30 seconds is represented as 0.5 minutes).
raw_timeframe = 5

# path: The base directory path where the raw data files are stored.
working_f = '01_BPR'
path = '/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/11 Rawdata'

# directory: The subdirectory name under the main path where the data files are located.
directory = '5min'

# VDS_num: The subdirectory name under the main path where the data files are located.
# ['1205541','1212611','1205572','1205583','1214006']
# VDS_num = '1203506'
VDS_num = '1205541'
# VDS_num = '1212611'
# VDS_num = '1205572'
# VDS_num = '1205583'
# VDS_num = '1214006'

c_lane_num = {'1212611':[1,2,3,4,5,6], '1205572':[1,2,3,4,5,6],'1205583':[1,2,3,4,5,6], '1203506':[1,2,3,4],'1214006':[1,2,3,4],'1205541':[1,2,3,4]}
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
            # epsilon=12,3,5(이값이 현재최신),4,10, 4(최신)
            epsilon=3, 
            offpeak_ff_speed_threshold= params['offpeak_ff_speed_threshold'],
            speed_gap_threshold = params['speed_gap_threshold'],
            aggregate_timeframe=config['aggregate_timeframe'],
            date=date, VDS_num=config['VDS_num'],
            min_off_len=params['min_off_len'],
            min_peak_len=params['min_peak_len'],
            method=params['method'],
            congest_method = params['congest_method'],
            occ_threshold = params['occ_threshold']
        )
    elif params['method'] == 'pelt':
        return pelt_speedbased_peak(
            model = "l2",
            df = traffic, column='speed', 
            offpeak_ff_speed_threshold= params['offpeak_ff_speed_threshold'],
            speed_gap_threshold = params['speed_gap_threshold'],
            aggregate_timeframe=config['aggregate_timeframe'],
            date=date, VDS_num=config['VDS_num'],
            # pelt_penalty = 320,2500 # (previous value in TRB), 200z
            pelt_penalty = 100,
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
            pelt_penalty = 1000,
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


def set_peak_period_save(config, set_peak_period,working_f):
    
    if config['spatial_scope'] == 'multi_vds':
        set_peak_period.to_csv(f"./{working_f}/set_peak_period_{config['spatial_scope']}_{config['VDS_list']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config['speedbased_params']['method']}_{config['speedbased_params']['congest_method']}.csv")
    else:
        set_peak_period.to_csv(f"./{working_f}/set_peak_period_{config['spatial_scope']}_{config['VDS_num']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config['speedbased_params']['method']}_{config['speedbased_params']['congest_method']}.csv")


def c_daily_traffic_save(config, results, working_f, criterion): 
    
    c_daily_traffic = pd.DataFrame({'date': results['date'], 'dayofweek': results["dayofweek"],'division': results[criterion], 'period':results['period'], 'duration':results['duration'], 'start_time': results['start'], 'end_time': results['end'],'totaldemand': results["total_demand"], 'avg_flow': results['avg_flow'], 'traveltimes': results["traveltime"], 'avg_speed':results["avg_speed"], 'density':results["density"], 'avg_occ':results["avg_occ"]})
    c_daily_traffic['year'] = c_daily_traffic['date'].astype(int)//10000 + 2000

    if config['spatial_scope'] == 'multi_vds':
        c_daily_traffic.to_csv(f"./{working_f}/c_daily_traffic_{criterion}_{config['spatial_scope']}_{config['VDS_list']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config['speedbased_params']['method']}_{config['speedbased_params']['congest_method']}.csv")
    else:
        c_daily_traffic.to_csv(f"./{working_f}/c_daily_traffic_{criterion}_{config['spatial_scope']}_{config['VDS_num']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config['speedbased_params']['method']}_{config['speedbased_params']['congest_method']}.csv")


# +
import os
import pickle
import numpy as np
import pandas as pd

# =====================
# Configuration Section
# =====================
config = {
    # spatial processing scope
    'spatial_scope': 'single',            # 'single' or 'multi_vds'
    'VDS_list': ['1205541','1212611','1205572','1205583','1214006'],  #,'1205572','1205541'  # used only when spatial_scope == 'multi_vds'
    # 'VDS_list': ['1205583','1214006','1212611'],    # used only when spatial_scope == 'multi_vds'
    'lane_map': c_lane_num,               # {'vds': [lane ids], ...}
    
    # temporal_scope : 'wholeday',  # # 'wholeday', 'peak',
    # Temporal granularity: 'hour', 'peak'(fixedtiime-based), 'entireday', 'speedbasedpeak'
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

    # Peak window definitions (minutes from midnight): start_time basis
    'peak_periods': {
        'morning': (5.5 * 60, 10 * 60),
        'afternoon': (12.5 * 60, 20 * 60)
    },

    # Speed-based peak |detection parameters
    'speedbased_params': {
        ## joon, pelt, RDP_v, derivative, pelt_directpeak
        'method': 'RDP_v',
        'congest_method':'speedgap_neighbor', # 'speedgap_neighbor', 'occ'
        'pelt_min_length': 5,
        'min_off_len': 90,
        'min_peak_len': 0,
        'speed_upper': 60,
        # 'freeflow_speed':70,
        # 'freeflow_speed_epsilon':20,
        'offpeak_ff_speed_threshold':45,
        # 'offpeak_ff_speed_threshold':50
        'speed_gap_threshold':15,
        'occ_threshold':0.16
    }
}


# -

def process_daily_traffic(traffic, config, date, rawdata, Day_list, criterion, result_input):
    """
    Process all divisions within a day's traffic data and return computed metrics.

    Args:
        traffic (pd.DataFrame): Traffic data for one day.
        peaks (list[dict]): List of peak segment information with 'start' and 'end' keys.
        config (dict): Configuration parameters.
        date (datetime): Current date.
        rawdata (pd.DataFrame): Original raw dataset containing 'time' column.
        Day_list (list): List mapping weekday numbers to names.

    Returns:
        dict: Dictionary containing lists of all computed metrics.
    """
    group_num = len(traffic[criterion].unique())
    results = result_input
    
    # Initialize result lists
        

    # Loop through each division
    for division_idx, group in traffic.groupby(criterion):
        if division_idx == 0:
            start_time = '-'
            end_time = '-'
        else:
            start_time = group['time_slot'].iloc[0] - config['aggregate_timeframe']/2
            start_time = f"{int(start_time // 60):02d}:{int(start_time % 60):02d}"
            end_time = group['time_slot'].iloc[-1] + config['aggregate_timeframe']/2
            end_time = f"{int((end_time) // 60):02d}:{int((end_time) % 60):02d}"

        tt, speed, demand, avg_flow, avg_occ, density, div, period, dur = compute_metrics(group, division_idx, config, group_num,criterion)

        results["traveltime"].append(tt)
        results["avg_speed"].append(speed)
        results["total_demand"].append(demand)
        results["avg_flow"].append(avg_flow)
        results["density"].append(density)
        results["avg_occ"].append(avg_occ)
        results["date"].append(date)
        results[criterion].append(division_idx)
        results["period"].append(period)
        results["dayofweek"].append(Day_list[int(rawdata.loc[0, 'time'].weekday())])
        results["duration"].append(dur)
        results["start"].append(start_time)
        results["end"].append(end_time)
        

    return results

# +
# path: The base directory path where the raw data files are stored.
working_f = '01_BPR'
path = '/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/11 Rawdata'

# directory: The subdirectory name under the main path where the data files are located.
directory = '5min'
raw_timeframe = 5

# VDS_num = '1205541'
# VDS_num = '1212611'
# VDS_num = '1205572'
# VDS_num = '1205583'
# VDS_num = '1214006'

c_lane_num = {'1212611':[1,2,3,4,5,6], '1205572':[1,2,3,4,5,6],'1205583':[1,2,3,4,5,6], '1203506':[1,2,3,4],'1214006':[1,2,3,4],'1205541':[1,2,3,4],'1203506':[1,2,3,4],'1203589':[1,2,3,4],'1203615':[1,2,3,4]}
Day_list = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
# '1205572','1205583','1203506','1203589',
# VDS_single_list = ['1203615','1203589','1203506']
#'1203615' has data quality issue: the speed fluctuate a lot.so, I did not use it.
# VDS_single_list = ['1203589','1203506','1212611','1205541','1205572','1205583','1214006']
VDS_single_list = ['1203506']

for VDS_num in VDS_single_list:
    print(VDS_num)
    config['VDS_num'] = VDS_num
    lane_num = c_lane_num[VDS_num]
    config['lane_num'] = lane_num
    
    # Constructs the full path to the directory containing the data files.
    full_path = os.path.join(path, directory, VDS_num)
    
    # Retrieves a list of all files in the specified directory.
    # This list will be used to iterate over or reference the data files for processing.
    file_list = sorted(os.listdir(full_path))
    config['file_list'] = file_list
    
    if '.DS_Store' in file_list:
        file_list.remove('.DS_Store')
        
    # Printing the list of files found in the specified directory.
    # print("Files in the specified directory:", file_list, len(file_list))

    results_div = {"date": [],"division": [],"period": [],"dayofweek": [],"duration": [],"start": [],"end": [],"total_demand": [],"avg_flow": [],"traveltime": [],"avg_speed":[],"density":[],"avg_occ":[]}
    results_seg = {"date": [],"segment": [],"period": [],"dayofweek": [],"duration": [],"start": [],"end": [],"total_demand": [],"avg_flow": [],"traveltime": [],"avg_speed":[],"density":[],"avg_occ":[]}

    set_peak_period = pd.DataFrame(columns=["date", "peak_list"])
    
    
    if (config['spatial_scope'] == 'single'):
        # === your existing main loop (unchanged) ===
        for file_name in config['file_list']:
            print(file_name)
            rawdata, date = load_raw(file_name, config)
            if skip_if_missing(rawdata, config):
                continue
            traffic, plot_date = aggregate_rawdata_5min(rawdata, raw_timeframe, date, lane_num, VDS_num)
            # traffic.to_csv(f"./01_BPR/03 analysis_result/daily_traffic/traffic_{config['VDS_num']}_{date}.csv")
    
            # speed-based peak detection (if chosen)
            if config['temporal_scale'] == 'speedbasedpeak':
                traffic, peaks = detect_speed_peaks(traffic, date, config)
                set_peak_period = pd.concat(
                    [set_peak_period, pd.DataFrame([{'date': date, 'peak_list': peaks}])],
                    ignore_index=True
                )
            elif config['temporal_scale'] == 'entireday':
                traffic['division'] = 0
                traffic['segment'] = 0

            results_div = process_daily_traffic(traffic, config, date, rawdata, Day_list, "division", results_div)
            results_seg = process_daily_traffic(traffic, config, date, rawdata, Day_list, "segment", results_seg)

    
    else:
        # === MULTI-VDS branch ===
        dates_common, date_to_files = _common_dates_and_files(config)
        
        if not dates_common:
            print("No common dates across VDS_list; nothing to process.")
        # A label for plots/outputs
        multi_label = "MULTI_" + "+".join(config['VDS_list'])
    
        for date in dates_common:
            c_coverage_length  = []
            # build per-VDS traffic for this date
            traffic_per_vds = []
            for vds in config['VDS_list']:
                # print(vds)
                ## code update필요!!ㅣ
                cfg_vds  = _make_vds_config(config, vds)
                base_dir = os.path.join(cfg_vds['path'], '11 Rawdata', cfg_vds['dir'], vds)
                fname    = date_to_files[date][vds]
                traffic, coverage_length = _build_traffic_for_vds(date, fname, cfg_vds, vds)
    
                c_coverage_length.append(coverage_length)
                
                if traffic is None:
                    traffic_per_vds = []  # drop this date if any VDS missing
                    break
                traffic_per_vds.append(traffic)
    
            
            if not traffic_per_vds:
                continue        
    
            speedprofile_plot(traffic_per_vds, raw_timeframe, config, date)
            
            # # average across VDS at each time_slot
            traffic_combo = _combine_vds_traffic(traffic_per_vds, config['aggregate_timeframe'], c_coverage_length)
            traffic_combo.to_csv(f"./01_BPR/03 analysis_result/daily_traffic/traffic_multi_{config['VDS_list']}_{date}.csv")
            if traffic_combo is None:
                continue
    
            # run detection on the combined day (reuse your existing function)
            temp_cfg = dict(config)
            temp_cfg['VDS_num'] = multi_label          # for plot filenames
            # lane_num not needed for compute_metrics in multi_vds fallback path
            if config['temporal_scale'] == 'speedbasedpeak':
                traffic_combo, peaks = detect_speed_peaks(traffic_combo, date, temp_cfg)
                set_peak_period = pd.concat(
                    [set_peak_period, pd.DataFrame([{'date': date, 'peak_list': peaks}])],
                    ignore_index=True
                )
            elif config['temporal_scale'] == 'entireday':
                traffic_combo['division'] = 0
                traffic_combo['segment'] = 0


            results_div = process_daily_traffic(traffic_combo, config, date, rawdata, Day_list, "division", results_div)
            results_seg = process_daily_traffic(traffic_combo, config, date, rawdata, Day_list, "segment", results_seg)


    set_peak_period_save(config, set_peak_period, working_f)
    c_daily_traffic_save(config, results_div, working_f, "division")
    c_daily_traffic_save(config, results_seg, working_f, "segment")
    # c_daily_traffic_filter_save(config, working_f)
# -




# ### (Code) Result & Analysis: Congestion-based Peak period result

# +
import pandas as pd
import ast

temporal_scale = 'speedbasedpeak'
# VDS: 1203506, 1205583
# VDS_num = '1203506'
VDS_num = '1205583'
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

# # BPR calibration result

# ## Location

# + [markdown] jp-MarkdownHeadingCollapsed=true
# - VDS1214006: Next to VDS: 1205883 (I-5)
#     - 2011.Jan~2011.June
#     - having days with congested period: 
# - <img src='./01_BPR/02_1_presentation_fig/VDS1205583.png' width=90%>
# -

# <img src='./01_BPR/02_1_presentation_fig/BPR_1214006.png' width=40%>

# |            | SR-91 Morning | SR-91 Afternoon | I-5 Morning (1205583) | I-5 Morning(1214006)|
# |------------|---------------|-----------------|-------------|-------------|
# | alpha_hat  | 1.45          | 1.12            | 3.61        |4.91 |
# | beta_hat   | 0.07          | 0.22            | 0.63        |0.61 |
#
#
#
# - The parameter value shows near known BPR parameter

# ## free-flow speed distribution (off-peak)

# - I-5
#
# | Freeflow Speed (mph)  | 1205541 | 1212611 | 1205572 | 1205583 | 1214006 | all_combined |
# |-----------------------|----------|----------|----------|----------|----------|----------|
# | Edie                 | 61.3     | 65.0     | 66.7     | 65.3     | 64.7 |64.1   |
# | Mean                 | 61.3     | 65.0     | 66.8     | 65.3     | 65.0 |64.1   |
# | Median                 | 61.5     | 65.3     | 67.2     | 65.8     | 65.9 | 64.4     |
#
# - SR-91
#
# | Freeflow Speed (mph)  | 1203506 | 1203589 | 1203615 |
# |-----------------------|----------|----------|----------|
# | Edie                 | 61     | 60     | 56     | 
# | Mean                 | 61     | 65     | 56    | 
# | Median                 | 61     | 60     | 56     |

# +
spatial_scope = 'single'    # 'single' or 'multi_vds'
temporal_scale = 'speedbasedpeak'  # 'speedbasedpeak', 'entireday'

# VDS_num: The subdirectory name under the main path where the data files are located.
# VDS_num = ['1205541', '1212611', '1205572', '1205583', '1214006']
# VDS_num = 1203506
# VDS_num = 1205541
# VDS_num = 1212611
# VDS_num = 1205572
# VDS_num = 1205583
# VDS_num = 1214006

#SR-91
VDS_num = 1203615
# VDS_num = 1203589
# VDS_num = 1203506


method = 'RDP_v'
version= '_filtered'  # "" "_filtered"
# version = 'wholeday'
# 'wholeday', 'peak' 'speedbasedpeak'
temporal_scale = 'speedbasedpeak'

if spatial_scope == 'single':
    file_path = f"./01_BPR/c_daily_traffic_single_{VDS_num}_{temporal_scale}_{config['aggregate_timeframe']}_{method}{version}.csv"
elif spatial_scope == 'multi_vds':
    file_path = f"./01_BPR/c_daily_traffic_multi_vds_{config['VDS_list']}_{temporal_scale}_{config['aggregate_timeframe']}_{method}{version}.csv"

print(file_path)

# + jupyter={"source_hidden": true}
## write down not inclue values
period_include = ['off-peak']
# 'morning-peak', 'afternoon-peak' 'peak-inoffpeak'

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

print(c_daily_traffic.head())

## Step 3-3: remove values of off-peak because of not belonging to the time period
# c_daily_traffic = c_daily_traffic[((1 / c_daily_traffic['traveltimes']) * 60) > 50]


# + jupyter={"source_hidden": true}
c_daily_traffic['avg_density'] = c_daily_traffic['avg_flow'] /  (1/c_daily_traffic['traveltimes'] * 60)

weighted_avg_flow = (c_daily_traffic['avg_flow'] * c_daily_traffic['duration']).sum() / c_daily_traffic['duration'].sum()
weighted_avg_density = (c_daily_traffic['avg_density'] * c_daily_traffic['duration']).sum() / c_daily_traffic['duration'].sum()

Edie_free_tt = weighted_avg_flow / weighted_avg_density

print(Edie_free_tt)

values=(1/c_daily_traffic['traveltimes'] * 60)
print(values.mean())
print(values.median())

# + jupyter={"source_hidden": true}
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

# ## Concept: Flow-rate vs Total volume

# - F.D.
#     - There exists the so-called fundamental diagrams that capture the functional relations between flow/speed and density in equilibrium states
#     - (Qinlong paper에서 equilibrium state가 아닌 상태가 어떤 상태인지 확인해보기!!)
#     - the flow-density relation is unimodal with the maximum flow rate as the capacity.
#     - Empirical studies have shown that the flow-density relations on freeway are triangular.
#     - This relation shows that the flow-speed relation on the freeway shows a backward-bending shape in the congested state.
# - BPR
#     - In contrast, traveltime-demand relation is defined as an increasing pattern, based on the intuition that hihger demand leads to more congestion.
# - Since these two fundamental models show opposite pattern during the congested period, the clarification between the two is needed.
#     - There is much confusion with respect to the names, theoretical definitions, and empirical observations of average traveltime functions 

# ### The theoretical background of Linear Regression

# - The assumption of linear regression
#     - continuous dependent variables Y
#     - Linear-in-parameter relationship between X and Y
#     - Uncertainty Relationship between variables: addition of disturbance term(variables that were omitted from the model, measurement erros, random variation in data-generating process)

# - The OLS (Ordinary Least Squares) Estimation
#     - OLS seeks a solution that minimizes the function Q ($Q=\sum_{i=1}^n (Y_i-\hat{Y}_i)^2$)
#     - $\hat{\beta} = (X^\top X)^{-1}X^\top Y$
#     - OLS Linear Regression Model Assumptions
#         - Funtional form: $Y_i=\beta_0+\beta_1 X_{i1}+e_i$
#         - Zero mean of disturbances: $E[\varepsilon_i]=0$
#         - Homoscedasticity of disturbances: $\text{VAR}[\varepsilon_i]=\sigma^2$
#         - Nonautocorrelation of disturbances: $\text{COV}[\varepsilon_i,\varepsilon_j]=0$ if $i\neq j$
#             - e.g.) $y_t=\beta_0+\beta_1 x_t+\varepsilon_t, \, \varepsilon_t=\rho \varepsilon_{t-1}+\mu_t$ 
#         - Exogeneity: $\text{COV}[X_i,\varepsilon_j]=0$ for all $i$ and $j$
#             - The variables you include in your model are determined independently of the unobserved factors that form the error term.
#             - when this occurs? you omitted a variable from your model that is correlated with explanatory variable in your model
#                 - True model: $y_i=\beta_0+\beta_1 x_i+ \beta_2 z_i+ \varepsilon_i$, but omit z_i, then $\varepsilon'_i=\beta_2 z_i + \varepsilon_i$
#                 - The assumption is essential for the unbiasedness of OLS estimates.
#                     - $y_i = \beta_0 + \beta_1 x_i + \varepsilon_i$
#                     - $\hat{\beta}_1 = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sum (x_i - \bar{x})^2}= \frac{\sum (x_i - \bar{x})[(\beta_0 + \beta_1 x_i + \varepsilon_i) - \bar{y}]}{\sum (x_i - \bar{x})^2}= \frac{\sum (x_i - \bar{x})(\beta_1 x_i - \beta_1 \bar{x} + \varepsilon_i)}{\sum (x_i - \bar{x})^2}=\beta_1 + \frac{\sum (x_i - \bar{x})\varepsilon_i}{\sum (x_i - \bar{x})^2}$
#                     - $E[\varepsilon|X]=0$ and $\text{COV}(X,\varepsilon)=0$ are equivalent, assuming $E[\varepsilon_i|X_i]$ is linear function of $X_i$ 
#         - Normality of disturbances: $\varepsilon_i \approx N(0,\sigma^2)$
#     - why?) MLE estimates with those assumptions are equivalent for the one from OLS.
#         - $L=(2\pi \sigma^2)^{-\frac{n}{2}} \text{EXP}^{-\frac{1}{2\sigma^2}(Y_i-X_i^\top \beta)^2}$
#             - Linearity, Exogeneity: manual inspection
# | Test | Purpose | Statistic | Null Hypothesis ($H_0$) | Decision Rule |
# |------|----------|------------|--------------------------|----------------|
# | **Shapiro–Wilk** | Normality of residuals | $W = \dfrac{(\sum a_i e_{(i)})^2}{\sum (e_i - \bar{e})^2}$ | Residuals are normal | $p < 0.05 \Rightarrow$ non-normal |
# | **Breusch–Pagan** | Homoscedasticity | $F = \frac{(R^2 / k)}{(1 - R^2) / (n - k - 1)}  \sim  F_{k,\, n - k - 1}$ | Constant variance | $p < 0.05 \Rightarrow$ heteroscedasticity |
# | **Durbin–Watson** | Autocorrelation | $DW = \dfrac{\sum (\hat{\varepsilon}_t - \hat{\varepsilon}_{t-1})^2}{\sum \hat{\varepsilon}_t^2}$ | No serial correlation | $DW \approx 2(1-\rho) \text{ where} \rho$ is sample autocorrelation → if $d\approx 2$, then no serial correlation |

# - Inference in Regression Analysis
#     - $\hat{\beta}_1 = \frac{\sum(X_i-\bar{X})(Y_i-\bar{Y})}{\sum(X_i-\bar{X})^2} = \frac{\sum(X_i-\bar{X})(\beta_0+\beta_1 X_i +\varepsilon_i -\bar{Y})}{\sum(X_i-\bar{X})^2}=\beta_1+\frac{\sum(X_i-\bar{X})\varepsilon_i}{\sum(X_i-\bar{X})^2}$
#     - Let's define weights: $w_i=\frac{X_i-\bar{X}}{\sum(X_i-\bar{X})^2}$
#         - $\hat{\beta}_1-\beta_1=\sum w_i\varepsilon_i$
#         - $E[\hat{\beta}_1]=\beta_1$: $\hat{\beta}_1$ is an unbiased estimator of $\beta_1$.
#         - $\text{Var}(\hat{\beta}_1)=\text{Var}(\sum w_i \varepsilon_i)=\sum w_i^2 \text{Var}(\varepsilon_i)=\sigma^2 \sum w_i^2=\frac{\sigma^2}{\sum(X_i-\bar{X})^2}$
#             - $\hat{\beta}_1 \sim N(\beta_1,\frac{\sigma^2}{S_{xx}})$
#         - When $\sigma^2$ is unknown
#             - $s^2=\frac{\sum(Y_i-\beta_0-\beta_1X_i)^2}{n-2}$
#             - $\frac{(n-2)s^2}{\sigma^2} \sim \chi^2_{n-2}$
#         - $\frac{\hat{\beta}_1 - \beta_1}{s/\sqrt{S_{xx}}} \sim t_{n-2}$
#             - $\beta_1$ and $s^2$ are independent when the errors are normal.
#             - $T=\frac{(\hat{\beta}_1-\beta_1)/(\sigma/\sqrt{S_{xx}})}{\sqrt{[(n-2)s^2/\sigma^2]/(n-2)}}=\frac{\hat{\beta}_1-\beta_1}{s/\sqrt{S_{xx}}} \sim t_{n-2}$ 

# + [markdown] jp-MarkdownHeadingCollapsed=true
# __Appendix__
#
# __Common OLS Diagnostic Test Statistics__
#
# 1. Shapiro-Wilk
# - Let $e_{(1)}, e_{(2)}, \ldots, e_{(n)}$ be the \textbf{ordered residuals} (sorted from smallest to largest),
# - and let $\bar{e} = \frac{1}{n}\sum_{i=1}^{n} e_i$ be their mean.
# - The Shapiro--Wilk test statistic: $W = \frac{\left( \sum_{i=1}^{n} a_i e_{(i)} \right)^2}{\sum_{i=1}^{n} (e_i - \bar{e})^2}$.
#
# 2. Breusch-Pagan
# - $\hat{u}_i = \hat{\varepsilon}_i^2
# \quad \text{and} \quad
# \hat{u}_i = \gamma_0 + \gamma_1 z_{1i} + \cdots + \gamma_k z_{ki} + v_i$
#
# **Interpretation:**  
# - Normality ensures valid $t$ and $F$ tests (small samples).  
# - Homoscedasticity ensures efficient OLS estimates.  
# - Nonautocorrelation ensures correct inference in time-series data.
# """)
#
# -

# - Multicollinearity assumption summary
#     - In the multiple regression model: $y_i = \beta_0 + \beta_1 x_{1i} + \beta_2 x_{2i} + \cdots + \beta_k x_{ki} + \varepsilon_i$
#     - The regressors must **not** be perfectly linearly related:
#         - $a_1 x_{1i} + a_2 x_{2i} + \cdots + a_k x_{ki} \neq 0 \quad \text{for any constants } a_j \text{ not all zero.}$
#         - Otherwise, the design matrix \( X \) has linearly dependent columns, making $(X'X)^{-1}$ undefined.
#     - OLS estimator: $\hat{\boldsymbol{\beta}} = (X'X)^{-1} X'y$
#         - If regressors are **perfectly collinear** → \( X'X \) is **singular** → OLS cannot be computed.
#         - If regressors are **highly collinear** → OLS exists but coefficients become **unstable** (large SEs).

# <div class="alert alert-info">
#
# Before estimating the model parameters using the Ordinary Least Squares (OLS) method, several diagnostic tests were performed to verify that the dataset satisfies the fundamental assumptions required for linear regression analysis. The OLS framework assumes that the dependent variable is continuous and that there exists a linear-in-parameter relationship between the explanatory variables and the dependent variable. In addition, the stochastic error term is assumed to have a zero mean, constant variance (homoscedasticity), no serial correlation, and no correlation with the explanatory variables (exogeneity). For valid inference, the residuals are further assumed to follow an approximately normal distribution.
#
# To evaluate whether these assumptions hold, three standard diagnostic tests were conducted. First, the Shapiro–Wilk test was used to examine the normality of residuals. A non-significant result (p>0.05) indicates that the residuals are normally distributed, supporting the normality assumption. Second, the Breusch–Pagan test was applied to detect potential heteroscedasticity by testing whether the variance of the residuals is constant across all observations. A non-significant result confirms homoscedasticity, whereas a significant result (p<0.05) suggests the presence of heteroscedasticity. Third, the Durbin–Watson test was used to identify serial correlation in the residuals, which is particularly important when observations are temporally ordered. The Durbin–Watson statistic ranges from 0 to 4, where a value close to 2 indicates the absence of autocorrelation.
#
# By conducting these diagnostic tests, the study ensures that the linear regression model satisfies the principal OLS assumptions, thereby validating the reliability of the estimated coefficients and the subsequent statistical inference.
#
# </div>

# ### Flow-rate during the congested period

# - It remains unclear which specific variables should be included in the BPR function. Previous studies have defined the BPR function in various ways: 1) for morning or afternoon peak periods, 2) over the course of an entire day, or 3) within stationary periods during peak times, where traffic conditions are considered time-independent.
# - Multiple empirical studies have confirmed the triangular fundamental diagram (FD) using traffic flow rates over short time intervals within peak periods (Case 3).
#     - Ambiguity persists regarding how to properly define the variables in the BPR function.
# - This study investigates how travel times and flow rates (or demand) exhibit different patterns across varying temporal contexts, within a fixed spatial area.
#     - Case1) flowrate inside the congested period
#     - Case2) total demand during the congested period
#     - Case3) total demand during the entire day

# #### Case1) flowrate inside the congested period

# - $\bar{q} = \omega \left( k_j - \bar{k} \right)\;\Rightarrow\;\bar{k} = k_j - \frac{\bar{q}}{\omega}$
# - $\bar{v}= \frac{\bar{q}}{\bar{k}}= \frac{\bar{q}}{\,k_j - \frac{\bar{q}}{\omega}\,}\;\Rightarrow\;\left( \frac{1}{\bar{v}} \right)= \frac{k_j}{\bar{q}} - \frac{1}{\omega}$

# - Introduction to Network Traffic Flow Theory(2021) p46
#     - NGSIM data, the values of parameters are $k_j=\frac{1}{7}veh/m-229vpm$, $u=65\text{mph}$, $\omega \approx 10 \text{mph}$, and $C \approx 1950\text{vph}$
#     - The calibrated parameters are within the realistic range.

# #### Case2) A study period of a day

# - How to do this

# <div class="alert alert-info">
#
# Let the day be partitioned into regimes $s = 1, \dots, S$ with duration $d_s$, mean flow $q_s$, mean speed $v_s$, and travel time per mile $z_s = 1/v_s$.  
# The number of vehicles served in regime $s$ is $N_s = q_s d_s$.  
#
# According to **Edie’s generalized definitions**, the daily space–mean speed and travel time are
#
# $$
# \bar v = \frac{\sum_s q_s d_s}{\sum_s (q_s / v_s) d_s}, \qquad
# \bar z = \frac{1}{\bar v}
#        = \frac{\sum_s (q_s d_s) z_s}{\sum_s q_s d_s}
#        = \sum_s \omega_s z_s,
# $$
#
# where the **weights correspond to vehicle shares**, not time shares:
#
# $$
# \omega_s = \frac{N_s}{\sum_r N_r} = \frac{N_s}{N_{\mathrm{tot}}}, \qquad 
# N_{\mathrm{tot}} := \sum_s N_s .
# $$
#
# Let $\zeta$ denote the free-flow travel time and define the excess over free-flow as $\delta_s := z_s / \zeta - 1 \ge 0$.  
# Then, the daily excess travel time is
#
# $$
# \frac{\bar z}{\zeta} - 1 = \sum_s \omega_s \delta_s .
# \tag{A}
# $$
#
# ---
#
# __Step 1 — Simplify to the two-regime case__
#
# For clarity, consider two regimes: uncongested $(U)$ with $\delta_U \approx 0$, and congested $(C)$ with $\delta_C > 0$ (approximately a plateau level $\delta^\star$).  
# From (A),
#
# $$
# \frac{\bar z}{\zeta} - 1 \approx \omega_C \, \delta^\star, 
# \qquad
# \omega_C := \frac{N_C}{N_{\mathrm{tot}}}.
# \tag{E}
# $$
#
# Taking logs yields the **mixture identity**:
#
# $$
# \ln\!\Big(\frac{\bar z}{\zeta} - 1\Big) = \ln \delta^\star + \ln \omega_C .
# \tag{F}
# $$
#
# This indicates that the entire-day excess travel time depends on the **intensity of congestion** ($\delta^\star$) and the **share of vehicles traveling in congested conditions** ($\omega_C$).
#
# ---
#
# __Step 2 — Link to total demand__
#
# Since $N_C = q_C d_C$ and $N_{\mathrm{tot}} = \sum_s q_s d_s$, any increase in total daily demand that extends the congested duration $d_C$ or increases the through-congestion flow $q_C$ will raise the **congestion vehicle share**:
#
# $$
# \omega_C = \frac{N_C}{N_{\mathrm{tot}}}.
# $$
#
# Hence, $\ln \omega_C$ increases with $\ln N_{\mathrm{tot}}$.  
# Substituting (F) into the estimating equation used for calibration,
#
# $$
# \ln\!\Big(\frac{\bar z}{\zeta} - 1\Big) = \ln(\tilde{\alpha}) + \beta \, \ln N_{\mathrm{tot}},
# $$
#
# shows that the variation in $\ln(\bar z / \zeta - 1)$ primarily arises from changes in $\omega_C$.  
# Because $\omega_C$ co-moves strongly with $N_{\mathrm{tot}}$, the slope $\beta$ estimated for the **entire-day** dataset becomes **larger**.
#
# ---
#
# __Step 3 — Why duration does not affect the congested-only excess__
#
# Within a congested period $C = [t_s, t_e]$, define
#
# $$
# \frac{z_C}{\zeta} - 1 
# = \frac{\int_{t_s}^{t_e} q(t) \, \delta(t) \, dt}{\int_{t_s}^{t_e} q(t) \, dt}, 
# \qquad \delta(t) := \frac{z(t)}{\zeta} - 1.
# \tag{B}
# $$
#
# Empirically, speeds in $C$ drop sharply and then remain near a low plateau for most of the period.  
# Let this plateau level be $\delta^\star = \zeta / v_L - 1$, where $v_L$ is the typical low-speed level.  
# Then, up to small entry and exit transients,
#
# $$
# \frac{z_C}{\zeta} - 1 \approx \delta^\star .
# \tag{C}
# $$
#
# Because both the numerator and denominator in (B) are weighted by $q(t)$, these weights cancel under a stable plateau, so $z_C / \zeta - 1$ depends primarily on the **intensity** $\delta^\star$, not on the **duration** $d_C$.  
# Formally,
#
# $$
# \frac{\partial}{\partial \ln d_C} 
# \ln\!\Big(\frac{z_C}{\zeta} - 1\Big) 
# \approx 0.
# \tag{D}
# $$
#
# Therefore, when we estimate
#
# $$
# \ln\!\Big(\frac{z_C}{\zeta} - 1\Big) 
# = \text{const} + \beta \, \ln N_C, 
# \qquad N_C = q_C d_C,
# $$
#
# most variation in $N_C$ comes from duration $d_C$, while the left-hand side remains roughly constant near $\delta^\star$.  
# This weak co-movement results in a **smaller slope** $\hat{\beta}$ for the **congested-only** sample.
#
# ---
#
# __Step 4 — Why the entire-day slope is steeper__
#
# From the mixture relation (E)–(F), daily excess travel time can be expressed as
#
# $$
# \frac{\bar z}{\zeta} - 1 = \delta^\star \, \omega_C 
# = \delta^\star \frac{N_C}{N_{\mathrm{tot}}}.
# $$
#
# As daily demand rises, both $N_C$ and $\omega_C$ increase because congestion lasts longer or involves more vehicles.  
# Thus, the left-hand side varies more strongly with total demand, and the estimated $\beta$ for the entire-day calibration becomes **larger** than that from the congested-only period.
#
# ---
#
# __Step 5 — Intuitive summary__
#
# Inside a congested period, extending its duration adds vehicles but leaves the plateau intensity $\delta^\star$ nearly unchanged, so $(z_C / \zeta - 1)$ hardly changes.  
# Across the entire day, however, a longer congestion period raises the **share of vehicles in congestion** $\omega_C$, which directly scales the daily excess $(\bar z / \zeta - 1) = \omega_C \delta^\star$.  
# This amplifies variation in daily travel times relative to total demand, leading to a **larger estimated β** for the entire-day regression.
#
# ---
#

# ## (Code) BPR fitting

# |            | 1205541 (Mor) | 1212611 (Mor) | 1205572 (Mor) | 1205583(Mor)|1214006(Mor)|Multi(Mor)|
# |------------|---------------|-----------------|-------------|-------------|------|------|
# | alpha  | 0.35          | 0.90            | 0.90| 0.69        |1.46 |0.64|
# | beta  | 0.53          | 0.55           |1.00| 1.08        |0.91 |0.93|
# | R-squared   | 0.17          | 0.21      |0.41      | 0.34        |0.23 |0.39|
#

# |            | 1205541 (Aft) | 1212611 (Aft) | 1205572 (Aft) | 1205583(Aft)|1214006(Aft)|Multi(Aft)|
# |------------|---------------|-----------------|-------------|-------------|------|------|
# | alpha  | 0.31          | 0.51            | 0.74| 0.40        |0.78 |0.45|
# | beta  | 0.28          | 0.45           |0.56| 0.47       |0.74 |0.48|
# | R-squared   | 0.22          | 0.25      |0.36      | 0.20        |0.25 |0.34|

def c_daily_traffic_filter_save(config, working_f):
    ### eliminate days with more than same periods having more than two.
    if config['spatial_scope'] == 'multi_vds':
        c_daily_traffic=pd.read_csv(f"./{working_f}/c_daily_traffic_{config['spatial_scope']}_{config['VDS_list']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config['method']}.csv")
    else:
        c_daily_traffic = pd.read_csv(f"./{working_f}/c_daily_traffic_{config['spatial_scope']}_{config['VDS_num']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config['method']}.csv")
    
    
    # # Find dates with duplicate periods
    # dup_dates = (
    #     c_daily_traffic.groupby("date")["period"]
    #     .apply(lambda x: x.duplicated().any())
    # )
    
    # # print(dup_dates[dup_dates == True])
    
    # # Keep only dates without duplicate periods
    # valid_dates = dup_dates[~dup_dates].index
    # c_daily_traffic_filtered = c_daily_traffic[c_daily_traffic["date"].isin(valid_dates)]

    # # Find more criterion (the congested period more than 10hours eliminate)
    # largest_hour = 8
    # c_daily_traffic_filtered = c_daily_traffic_filtered[c_daily_traffic_filtered["duration"] < (largest_hour*60)]

    # Eliminate the congested period having average congested period above the 'offpeak_ff_speed_threshold':50,
    c_daily_traffic_filtered = c_daily_traffic
    tt_threshold= config['free_tt_fixed'][VDS_num] / 0.9
    c_daily_traffic_filtered = c_daily_traffic_filtered[(c_daily_traffic_filtered["period"].isin(['afternoon-peak','morning-peak'])) & (c_daily_traffic_filtered["traveltimes"] >= tt_threshold)]
    
    print("Before:", c_daily_traffic.shape)
    print("After :", c_daily_traffic_filtered.shape)
    
    if config['spatial_scope'] == 'multi_vds':
        c_daily_traffic_filtered.to_csv(f"./{working_f}/c_daily_traffic_{config['spatial_scope']}_{config['VDS_list']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config['method']}_filtered.csv")
    else:
        c_daily_traffic_filtered.to_csv(f"./{working_f}/c_daily_traffic_{config['spatial_scope']}_{config['VDS_num']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config['method']}_filtered.csv")


# +
def build_file_path(cfg: dict) -> str:
    if (cfg['spatial_scope'] == "multi_vds"):
        file_path = f"./01_BPR/c_daily_traffic_{cfg['spatial_scope']}_{cfg['VDS_list']}_{cfg['temporal_scale']}_{cfg['aggregate_timeframe']}_{cfg['method']}{cfg['version_tag']}.csv"
        print(file_path)
    else:
        file_path = f"./01_BPR/c_daily_traffic_{cfg['spatial_scope']}_{cfg['VDS_num']}_{cfg['temporal_scale']}_{cfg['aggregate_timeframe']}_{cfg['method']}{cfg['version_tag']}.csv"
    return file_path

# === Shared utilities ===
def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    return 1.0 - ss_res/ss_tot if ss_tot > 0 else np.nan

def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred)**2)))

def to_categorical_day(df: pd.DataFrame) -> pd.DataFrame:
    day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    if "dayofweek" in df.columns:
        df["dayofweek"] = pd.Categorical(df["dayofweek"], categories=day_order, ordered=True)
    return df

# === Load + annotate once ===
# add columns of revise the format of dataframe
def load_and_annotate(cfg: dict) -> pd.DataFrame:
    fp = build_file_path(cfg)
    df = pd.read_csv(fp)
    # basic date fields
    df["date"] = df["date"].astype(str)
    df["month"] = df["date"].str.slice(0, 4)

    # free-flow travel time
    ## Divide the mode depending on how day-dependent freeflow-speed or fixed freeflow
    if cfg["free_tt_mode"] == "by_date_offpeak":
        off = df[df["period"] == "off-peak"]
        free_map = off.set_index("date")["traveltimes"].to_dict()
        df["free_traveltime"] = df["date"].map(free_map)
    else:
        if cfg['spatial_scope'] == 'single':
            df["free_traveltime"] = cfg['free_tt_fixed'][cfg["VDS_num"]]
        elif cfg['spatial_scope'] == 'multi_vds':
            df["free_traveltime"] = cfg['free_tt_fixed']['multi_vds']
        

    lane_num = c_lane_num[cfg['VDS_num']]
    df['totaldemandoverlanes'] = df['totaldemand'] * len(lane_num)
    
    # derived logs
    df["ln_avg_flow"] = np.log(df["avg_flow"])
    df["ln_totaldemand"] = np.log(df["totaldemand"])
    df['ln_totaldemandoverlanes'] = np.log(df["totaldemandoverlanes"])
    

    # ln((z/ζ)-1) using either fixed or date-wise ζ
    df["ln_t_tau"] = np.log(df["traveltimes"]/df["free_traveltime"] - 1.0)

    # Version 5/6 convenience (Ideal waiting time)
    W_hour = cfg["W_minutes"]/60.0
    df["avgdemand"] = np.where(
        df["division"] == 0, df["totaldemand"], df["totaldemand"]/W_hour
    )

    return df

# === One place to filter ===
def apply_filters(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    # common: remove division == -1
    if "division" in df.columns:
        df = df[df["division"] != -1]

    if cfg["dayofweek_exclude"]:
        df = df[~df["dayofweek"].isin(cfg["dayofweek_exclude"])]
    if cfg["month_exclude"]:
        df = df[~df["month"].isin(cfg["month_exclude"])]
    if cfg["year_exclude"] and "year" in df.columns:
        df = df[~df["year"].isin(cfg["year_exclude"])]
    if cfg["period_include"]:
        df = df[df["period"].isin(cfg["period_include"])]

    return to_categorical_day(df.copy())


# +
from typing import Callable, Tuple, Dict


# === Linear version registry (V1–V4) ===
# Each entry returns (x, y, x_label, y_label) for plotting/fit
# 'Collable' means “a function (or any callable object) that takes arguments of given types and returns the given type.”
LinearTransform = Callable[[pd.DataFrame], Tuple[np.ndarray, np.ndarray, str, str]]

def v1_q_vs_tau(g: pd.DataFrame):
    return (
        (1/g["avg_flow"]).to_numpy(),
        (g["traveltimes"]/60).to_numpy(),
        r"$\frac{1}{\bar{q}}$",
        r"$\frac{1}{\bar{v}}$",
    )

def v2_lnN_vs_lnttau(g: pd.DataFrame):
    return (
        g["ln_totaldemand"].to_numpy(),
        g["ln_t_tau"].to_numpy(),
        r"$\ln(Tq)$",
        r"$\ln\!\left(\frac{z(r)}{\zeta}-1\right)$",
    )

def v3_lnN_vs_lnttau(g: pd.DataFrame):
    return (
        g["ln_totaldemandoverlanes"].to_numpy(),
        g["ln_t_tau"].to_numpy(),
        r"$\ln(Tql)$",
        r"$\ln\!\left(\frac{z(r)}{\zeta}-1\right)$",
    )

def v4_speeddep_lnN_vs_lnttau(g: pd.DataFrame):
    # identical axes to v3; differs because ζ is date-wise in ln/columns already
    return v2_lnN_vs_lnttau(g)


def v10_lnq_vs_lnttau(g: pd.DataFrame):
    return (
        g["ln_avg_flow"].to_numpy(),
        g["ln_t_tau"].to_numpy(),
        r"$\ln(q)$",
        r"$\ln\!\left(\frac{z(r)}{\zeta}-1\right)$",
    )

LINEAR_REGISTRY: Dict[str, LinearTransform] = {
    "v1": v1_q_vs_tau,
    "v2": v2_lnN_vs_lnttau,
    "v3": v3_lnN_vs_lnttau,
    "v4": v4_speeddep_lnN_vs_lnttau,
    "v10": v10_lnq_vs_lnttau,
}

# + jupyter={"source_hidden": true}
import math
from typing import Callable, Tuple, Dict, Optional
from scipy.stats import shapiro
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan

# === Shared linear plotter ===
def plot_linear_by_group(
    df: pd.DataFrame,
    cfg: dict,
    version_key: str,
    xlim: Optional[Tuple[float,float]] = None,
    ylim: Optional[Tuple[float,float]] = None,
    title_suffix: str = "",
    save_name: Optional[str] = None,
):
    assert version_key in LINEAR_REGISTRY, "Unknown linear version key."
    ## version_key에 맞는 함수 정의
    trans = LINEAR_REGISTRY[version_key]
    group_key = cfg["label_criterion"]
    
    fig, ax = plt.subplots(1, 1, figsize=(8.5, 6))
    legend_entries = []
    legend_entries_res = []
    

    # Get labels once, before loop
    _, _, xlab, ylab = trans(df)
    ax.set_xlabel(xlab, fontsize=12)
    ax.set_ylabel(ylab, fontsize=12)
    ax.grid(True)
    
    # Then loop only for x,y
    # group_key = "period", "dayofweek", "year", ...
    for name, grp in df.groupby(group_key):
        x, y, _, _ = trans(grp)
        ax.plot(x, y, marker="o", linestyle="", label=str(name))
        # OLS by np.polyfit
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() < 3:
            print(f"Skipping group {name}: insufficient data.")
            continue
            
        # === Fit using statsmodels OLS ===
        X = sm.add_constant(x[mask])  # add intercept
        model = sm.OLS(y[mask], X).fit()
        
        # Extract coefficients
        b0, b1 = model.params
        print(b0,b1)
        yhat = model.fittedvalues
        resid = model.resid

        # === Print coefficient t-tests ===
        print(f"\n=== Group: {name} ===")
        print(model.summary())  # includes t-values and p-values
        p_value_slope = model.pvalues[1]    # index 1 → x coefficient (β)
        # print(f"α = {alpha:.4f}, β = {beta:.4f}")

        # === Homoscedasticity Test (Breusch–Pagan) ===
        bp_test = het_breuschpagan(model.resid, model.model.exog)
        labels = ['LM stat', 'LM p-value', 'F stat', 'F p-value']
        print(dict(zip(labels, bp_test)))

        # === Normality Test (Shapiro–Wilk) ===
        shapiro_test = shapiro(resid)
        print(f"Shapiro–Wilk p-value: {shapiro_test.pvalue:.4f}")
        
        # smooth line
        x_line = np.linspace(x.min(), x.max(), 200)
        y_line = b0 + b1*x_line
        ax.plot(x_line, y_line, linewidth=2)

        if (version_key == 'v1'):
            k_j = b1
            w = -1/b0
            r2 = 1 - np.sum((y[mask] - yhat)**2) / np.sum((y[mask] - np.mean(y[mask]))**2)
            legend_entries.append(
                 f"y={b0:.1f}+{b1:.1f}x (R²={r2:.3f}, b1 p-value: {p_value_slope:.2f})\n"
                 f"$k_j$ = {k_j:.1f}, $w$ = {w:.1f}")
        else:
            beta = b1
            alpha = (cfg['W_minutes']/60*cfg['capacity_fixed'])**beta*math.exp(b0)
            r2 = 1 - np.sum((y[mask] - yhat)**2) / np.sum((y[mask] - np.mean(y[mask]))**2)
            legend_entries.append(
                 f"y={b0:.1f}+{b1:.1f}x (R²={r2:.3f}, b1 p-value: {p_value_slope:.2f})\n"
                 f"$\\alpha$ = {alpha:.2f}, $\\beta$ = {beta:.2f}")

        if cfg["spatial_scope"] == "single":
            if cfg["temporal_scale"] == "speedbasedpeak":
                ax.set_title(f"BPR calibration ({version_key.upper()}) at VDS {cfg['VDS_num']} {name} [{cfg['method']}]")
            elif cfg["temporal_scale"] == "entireday":
                ax.set_title(f"BPR calibration ({version_key.upper()}) at VDS {cfg['VDS_num']} entireday [{cfg['method']}]")
        else:
            if cfg["temporal_scale"] == "speedbasedpeak":
                ax.set_title(f"BPR calibration ({version_key.upper()}) at multiple VDS {name} [{cfg['method']}]")
            elif cfg["temporal_scale"] == "entireday":
                ax.set_title(f"BPR calibration ({version_key.upper()}) at multiple VDS entireday [{cfg['method']}]")
    
        ax.legend(legend_entries, fontsize=14, loc="best")
        
        if xlim: ax.set_xlim(*xlim)
        if ylim: ax.set_ylim(*ylim)

    
    

        if save_name is None:
            if cfg['spatial_scope'] == 'multi_vds':
                save_name = f"{cfg['save_dir']}/{cfg['period_include'][0]}/{version_key}/BPR_calibration_{cfg['spatial_scope']}_{cfg['VDS_list']}_{cfg["temporal_scale"]}_{version_key}_{cfg['method']}{cfg['version_tag']}_{cfg['period_include']}.png"
            elif cfg['spatial_scope'] == 'single':
                save_name = f"{cfg['save_dir']}/{cfg['period_include'][0]}/{version_key}/BPR_calibration_{cfg['spatial_scope']}_{cfg['VDS_num']}_{cfg["temporal_scale"]}_{version_key}_{cfg['method']}{cfg['version_tag']}_{cfg['period_include']}.png"
        
        plt.savefig(save_name, bbox_inches="tight")
        # plt.close(fig)
    
        # --- Plot 1: Residuals vs Fitted ---
        fig1, ax1 = plt.subplots(1, 1, figsize=(6.5, 5))
        ax1.scatter(yhat, resid, alpha=0.7)
        ax1.axhline(0, color="red", linestyle="--", linewidth=1)
        ax1.set_xlabel("Fitted values")
        ax1.set_ylabel("Residuals")
        if cfg["spatial_scope"] == "single":
            ax1.set_title(f"Residuals vs Fitted ({version_key.upper()}) at VDS {cfg['VDS_num']} {name} [{cfg['method']}]")
        else:
            ax1.set_title(f"Residuals vs Fitted ({version_key.upper()}) at multiple VDS {name} [{cfg['method']}]")
            
        ax1.grid(True, alpha=0.3)
        if cfg['spatial_scope'] == 'multi_vds':
            fname1 = f"{cfg['save_dir']}/{cfg['period_include'][0]}/res-vs-fitted/res-vs-fitted_{cfg['spatial_scope']}_{cfg['VDS_list']}_{cfg["temporal_scale"]}_{version_key}_{cfg['method']}{cfg['version_tag']}_{cfg['period_include']}.png"
        elif cfg['spatial_scope'] == 'single':
            fname1 = f"{cfg['save_dir']}/{cfg['period_include'][0]}/res-vs-fitted/res-vs-fitted_{cfg['spatial_scope']}_{cfg['VDS_num']}_{cfg["temporal_scale"]}_{version_key}_{cfg['method']}{cfg['version_tag']}_{cfg['period_include']}.png"
        
        legend_entries_res.append(
                     f"Shaprio-Wilk p-value: {shapiro_test.pvalue:.3f}\n"
                     f"Breusch–Pagan p-value: {bp_test[-1]:.3f}")
        ax1.legend(legend_entries_res, fontsize=14, loc="best")
        
        plt.savefig(fname1, bbox_inches="tight")
        plt.close(fig1)

    # # --- Plot 2: Residuals vs X (predictor) ---
    # fig2, ax2 = plt.subplots(1, 1, figsize=(6.5, 5))
    # ax2.scatter(x[mask], resid, alpha=0.7)
    # ax2.axhline(0, color="red", linestyle="--", linewidth=1)
    # ax2.set_xlabel(xlab)
    # ax2.set_ylabel("Residuals")
    # ax2.set_title(f"Residuals vs {xlab} — {name}")
    # ax2.grid(True, alpha=0.3)
    # fname2 = f"{cfg['save_dir']}/res-vs-x_{cfg['spatial_scope']}_{cfg['VDS_num']}_{cfg["temporal_scale"]}_{version_key}_{cfg['method']}{cfg['version_tag']}_{cfg['period_include']}.png"
    # plt.savefig(fname2, bbox_inches="tight")
    # plt.close(fig2)

        # shapiro_test = shapiro(resid)
        # print(shapiro_test)
    
        print(save_name)
        plt.savefig(save_name, bbox_inches="tight")
        plt.close(fig)


# +
# === Nonlinear: V5 (fixed capacity & W, fit a,b) ===
def model_bpr_avgdemand(x, a, b, free_tt, c_fixed, W_minutes):
    t0 = free_tt
    W = W_minutes/60.0
    return t0 * (1.0 + a * (x/(c_fixed*W))**b)

def run_v5(df: pd.DataFrame, cfg: dict, xlim: Optional[list] = None, ylim: Optional[list] = None, save_name: Optional[str] = None):
    group_key = cfg["label_criterion"]
    c_fixed = cfg["capacity_fixed"]
    Wm = cfg["W_minutes"]
    if cfg['spatial_scope'] == 'single':
        free_tt = cfg['free_tt_fixed'][cfg["VDS_num"]]
    elif cfg['spatial_scope'] == 'multi_vds':
        free_tt = cfg['free_tt_fixed']['multi_vds']

    fig, ax = plt.subplots(1, 1, figsize=(8.5, 6))
    legends = []

    for name, grp in df.groupby(group_key):
        x = grp["totaldemandoverlanes"].to_numpy()
        y = grp["traveltimes"].to_numpy()

        # # Fit a,b with c,W fixed
        # f = lambda xx, a, b: model_bpr_avgdemand(xx, a, b, free_tt, c_fixed, Wm)
        # popt, _ = curve_fit(f, x, y, p0=[1.0, 1.0], maxfev=10000)
        # a_hat, b_hat = popt
        # print(a_hat,b_hat)

        # Lines & metrics
        # x_fit = np.linspace(0, max(float(x.max()), 1.0), 400)
        # y_fit = model_bpr_avgdemand(x_fit, a_hat, b_hat, free_tt, c_fixed, Wm)
        # y_fit_ideal = model_bpr_avgdemand(x_fit, 0.15, 4, cfg['free_tt_fixed'], c_fixed, Wm)
# 
        # y_pred = model_bpr_avgdemand(x, a_hat, b_hat, free_tt, c_fixed, Wm)
        # r2 = r2_score(y, y_pred)
        
        ax.plot(x, y, marker="o", linestyle="", label=str(name))
        # ax.plot(x_fit, y_fit, linewidth=2)
        # ax.plot(x_fit, y_fit_ideal, linewidth=2)

        # legends.append(f"{name}: t=t₀(1+{a_hat:.2f}(x/({c_fixed}·{Wm/60:.2f}))^{b_hat:.2f}), R²={r2:.3f}")
        # legends.append(f"{name}: t=t₀(1+{a_hat:.2f}(x/({c_fixed}·{Wm/60:.2f}))^{b_hat:.2f})")

    
        ax.set_xlim(0,x.max()*1.1)
    
        if xlim: ax.set_xlim(*xlim)
        if ylim: ax.set_ylim(*ylim)
            
        ax.set_xlabel(r"$N$ (veh)", fontsize=12)
        ax.set_ylabel("Average travel time (min/mile)", fontsize=12)
        ax.grid(True)
        ax.set_title(f"BPR calibration (V5) at VDS {cfg['VDS_num']} [{cfg['method']}]", fontsize=12)
        # ax.legend(legends, fontsize=9, loc="best")
    
        if save_name is None:
            if cfg['spatial_scope'] == "multi_vds":
                save_name = f"{cfg['save_dir']}/{cfg['period_include'][0]}/v5/BPR_calibration_{cfg['spatial_scope']}_{cfg['VDS_list']}_{cfg["temporal_scale"]}_v5_{cfg['method']}{cfg['version_tag']}_{cfg['period_include']}.png"
            else:
                save_name = f"{cfg['save_dir']}/{cfg['period_include'][0]}/v5/BPR_calibration_{cfg['spatial_scope']}_{cfg['VDS_num']}_{cfg["temporal_scale"]}_v5_{cfg['method']}{cfg['version_tag']}_{cfg['period_include']}.png"
        
        plt.savefig(save_name, bbox_inches="tight")
        plt.close(fig)


# +
# === Nonlinear: V6 (whole-day weighted ratio) ===
def compute_v6_wratio_and_avgtt(df: pd.DataFrame, cap: float, beta: float = 4.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    For each date, compute:
      w_tilde = [ sum_i epsilon_i^{beta+1} / w_i^{beta} ]^{-1/beta}
      w0      = N_total / cap
      w_ratio = w0 / w_tilde
    and weighted average travel time.
    """
    w_map = {"off-peak": float("inf"), "morning-peak": 1.0, "afternoon-peak": 1.0}
    wratios, avgtts = [], []

    for date, grp in df.groupby("date"):
        periods = grp["period"].tolist()
        w_i = np.array([w_map.get(p, 1.0) for p in periods], dtype=float)
        N_i = grp["totaldemand"].to_numpy(dtype=float)
        eps = N_i / (N_i.sum() if N_i.sum() > 0 else 1.0)
        # Handle inf weights: eps^(b+1)/w^b -> 0 when w=inf
        term = np.where(np.isinf(w_i), 0.0, (eps**(beta+1))/(w_i**beta))
        denom = term.sum()
        if denom <= 0:
            continue
        w_tilde = (1.0/denom)**(1.0/beta)
        w0 = (N_i.sum()/cap) if cap > 0 else np.nan
        if np.isnan(w0):
            continue
        wratios.append(w0/w_tilde)
        avgtts.append(np.sum(grp["traveltimes"]*eps))
    return np.array(wratios, float), np.array(avgtts, float)

def model_bpr_wratio(w_ratio, a, b):
    t0 = 60.0/70.0
    return t0 * (1.0 + a * (w_ratio**b))

def run_v6(df: pd.DataFrame, cfg: dict, save_name: Optional[str] = None):
    cap = cfg["capacity_fixed"]
    w_ratio, avg_tt = compute_v6_wratio_and_avgtt(df, cap=cap, beta=4.0)
    fig, ax = plt.subplots(1, 1, figsize=(8.0, 6.0))

    ax.plot(w_ratio, avg_tt, marker="o", linestyle="", label="daily points")
    f = lambda w, a, b: model_bpr_wratio(w, a, b)
    popt, _ = curve_fit(f, w_ratio, avg_tt, p0=[1.0, 1.0], maxfev=10000)
    a_hat, b_hat = popt

    x_fit = np.linspace(0, max(float(w_ratio.max()), 1.0), 400)
    y_fit = model_bpr_wratio(x_fit, a_hat, b_hat)
    y_pred = model_bpr_wratio(w_ratio, a_hat, b_hat)

    ax.plot(x_fit, y_fit, linewidth=2, label=f"Fit: a={a_hat:.2f}, b={b_hat:.2f}, R²={r2_score(avg_tt, y_pred):.3f}")
    ax.set_xlabel(r"$N/(lC\tilde{W})$", fontsize=12)
    ax.set_ylabel("Average travel time (min/mile)", fontsize=12)
    ax.grid(True)
    ax.set_title(f"BPR calibration (V6) at VDS {cfg['VDS_num']} [{cfg['method']}]", fontsize=12)
    ax.legend()

    if save_name is None:
        if cfg['spatial_scope'] == "multi_vds":
            save_name = f"{cfg['save_dir']}/{cfg['period_include']}/v6/BPR_calibration_{cfg['spatial_scope']}_{cfg['VDS_list']}_{cfg["temporal_scale"]}_v6_{cfg['method']}{cfg['version_tag']}_{cfg['period_include']}.png"
        else:
            save_name = f"{cfg['save_dir']}/{cfg['period_include']}/v6/BPR_calibration_{cfg['spatial_scope']}_{cfg['VDS_num']}_{cfg["temporal_scale"]}_v6_{cfg['method']}{cfg['version_tag']}_{cfg['period_include']}.png"
            
    plt.savefig(save_name, bbox_inches="tight")
    plt.close(fig)


# +
working_f = '01_BPR'
path = '/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/11 Rawdata'

# directory: The subdirectory name under the main path where the data files are located.
directory = '5min'
raw_timeframe = 5

# VDS_num = '1205541'
# VDS_num = '1212611'
# VDS_num = '1205572'
# VDS_num = '1205583'
# VDS_num = '1214006'

c_lane_num = {'1212611':[1,2,3,4,5,6], '1205572':[1,2,3,4,5,6],'1205583':[1,2,3,4,5,6], '1203506':[1,2,3,4],'1214006':[1,2,3,4],'1205541':[1,2,3,4],'1203506':[1,2,3,4],'1203589':[1,2,3,4],'1203615':[1,2,3,4]}
Day_list = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
# '1205572','1205583','1203506','1203589',
# VDS_single_list = ['1203615','1203589','1203506']
VDS_single_list = ['1205541','1212611','1205572','1205583','1214006']

for VDS_num in VDS_single_list:

    CONFIG_BPR['VDS_num'] = VDS_num
    lane_num = c_lane_num[VDS_num]
    
    c_daily_traffic_filter_save(CONFIG_BPR, working_f)

# +
# === Imports ===
import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Callable, Dict, Tuple, Optional
from scipy.optimize import curve_fit

# === Global style (optional) ===
plt.rcParams.update({"figure.dpi": 140})

# === Configuration ===
CONFIG_BPR = {
    "spatial_scope" : "multi_vds" ,      # "multi_vds", "single"
    "VDS_list": ['1205541','1212611','1205572','1205583','1214006'],
    # stations = [1203506,1203589,1203615]
    "VDS_num": '1205541',                # 1203506, 1205583, 1214006, ...
    "temporal_scale": 'speedbasedpeak',    # used in file name "speedbasedpeak", "entireday"
    "period_include": ["morning-peak"],  # subset e.g. ['morning-peak', 'afternoon-peak']
    "method": "RDP_v",
    # "temporal_scope": "entireday",          # "entireday" or "peak"
    "version_tag": "",             # "", "_filtered"
    "aggregate_timeframe": 5,              # used in file name (minutes)
    "label_criterion": "period",           # "period", "dayofweek", "year", ...
    "dayofweek_exclude": [],
    "month_exclude": [],
    "year_exclude": [],
    "free_tt_mode": "fixed",               # "fixed" OR "by_date_offpeak"
    #This is mean free_tt
    "free_tt_fixed": {'1203506': 60*(1/(61)),'1203589': 60*(1/(60)),'1203615': 60*(1/(56)),'1205541': 60*(1/(61)), '1212611': 60*(1/(65)),'1205572': 60*(1/(67)), '1205583': 60*(1/(66)),'1214006': 60*(1/(65)), 'multi_vds': 60*(1/(64))},   # minutes/mile when mode=="fixed" (60*1/freeflow_speed),
    "W_minutes": 90,                      # heart-of-peak window for V5/V6 if needed
    "capacity_fixed": 1800*24,                # for V5/V6 where capacity is fixed
    "save_dir": "./01_BPR/02 fig/12 Daily BPR",               # where to save figures
}

# Ensure save dir exists
os.makedirs(CONFIG_BPR["save_dir"], exist_ok=True)
# -

# === Example driver ===
if __name__ == "__main__":
    cfg = CONFIG_BPR.copy()

    c_lane_num = {'1212611':[1,2,3,4,5,6], '1205572':[1,2,3,4,5,6],'1205583':[1,2,3,4,5,6], '1203506':[1,2,3,4],'1214006':[1,2,3,4],'1205541':[1,2,3,4],
                 '1203506':[1,2,3,4],'1203589':[1,2,3,4],'1203615':[1,2,3,4]}
    
    # 1) Load once, annotate once
    df_all = load_and_annotate(cfg)
    
    # # 1-2) Filter
    # # df_all = df_all[df_all['duration']> 60]
    # df_all = df_all[(df_all['ln_t_tau'] < 0.5) | (df_all['ln_totaldemand'] > 7)]
    # df_all = df_all[(df_all['totaldemand'] > 2000)]
    # df_all = df_all[~((df_all['ln_t_tau'] < 0) & (df_all['ln_totaldemand'] < 8))]
    
    if cfg['spatial_scope'] == 'single' and cfg['VDS_num'] == '1205541':
        df_all = df_all[~df_all['month'].isin(['2401', '2402', '2403', '2404'])]
    if cfg['spatial_scope'] == 'multi_vds' :
        df_all = df_all[~df_all['month'].isin(['2401', '2402', '2403', '2404'])]
    
    # 2) Apply common filters
    df_use = apply_filters(df_all, cfg)

    print(len(df_use))
    
    # version_key = "v1", "v5":[0,6000], "v5": [1,4]
    xlim = {"v1":[6.5,7.25], "v2": [4,9],"v3": [11,12], "v4": [7,15],"v5": [60000,120000]}
    ylim = {"v1": [-1,2], "v2": [-1,2],"v3": [-3,-1], "v4": [-2,2],"v5": [0,2]}

    # 3) Linear variants (choose any of 'v1','v2','v3')
       # Change cfg["free_tt_mode"] to 'by_date_offpeak' for your “speed dependent” ζ
    # plot_linear_by_group(df_use, cfg, version_key=version_key, xlim= xlim[version_key], ylim=ylim[version_key], title_suffix="[linear ln(q) vs ln((z/ζ)-1)]")
    
    plot_linear_by_group(df_use, cfg, version_key="v1")
    plot_linear_by_group(df_use, cfg, version_key="v2")
    plot_linear_by_group(df_use, cfg, version_key="v3")
    # For v3, set cfg["free_tt_mode"] = "by_date_offpeak" before load_and_annotate, then:
    # plot_linear_by_group(df_use, cfg, version_key="v3")

    # 4) Nonlinear versions
    # V5: capacity & W fixed, fit (a,b)
    run_v5(df_use, cfg)
    # run_v5(df_use, cfg,xlim=xlim['v5'],ylim=ylim['v5'])

    # V6: whole-day weighting, fit (a,b)
    # run_v6(df_use, cfg)

# +
df_use.head()
# len(df_use)

# df_use[(df_use['ln_avg_flow'] < 7.2) & (df_use['ln_t_tau'] < -0.5)]
# df_all = df_all[~((df_all['ln_t_tau'] < 0) & (df_all['ln_totaldemand'] < 8))]
# -



# #### (Version1) ln(Avgflow)-ln(traveltimes)

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} q^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC/T)^\beta}$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(q)$
# - $y_n = ln(\tilde{\alpha})+\beta x_n$
#

# #### (Version2) ln(traveldemand)-ln(traveltimes)

# + [markdown] jp-MarkdownHeadingCollapsed=true
# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} (Tq)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tq$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - $y_n = ln(\tilde{\alpha})+\beta x_n$
# - parameter calibration
#     -  $\tilde{\alpha}' = ln(\tilde{\alpha})=ln(\frac{\alpha}{(WC)^\beta})$
#     -  $\alpha = \exp(\tilde{\alpha}')\times (WC)^\beta$
# -

# - $z(r)=\zeta[1+\alpha (\frac{qTl}{WC})^\beta]=\zeta(1+\tilde{\alpha} (Tql)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tql$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - parameter calibration
#     -  $\tilde{\alpha}' = ln(\tilde{\alpha})=ln(\frac{\alpha}{(WC)^\beta})$
#     -  $\alpha = \exp(\tilde{\alpha}')\times (WC)^\beta$

# #### (Version3) Inverse ln(Avgdemand) vs ln(traveltimes)

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} (Tq)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tq$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - $-ln(\frac{z(r)}{\zeta}-1)=-ln(\tilde{\alpha})-\beta ln(N)$
# - $ln((\frac{z(r)}{\zeta}-1)^{-1})=ln(\frac{1}{\tilde{\alpha}})  -\beta ln(N)$

# #### (version4) speed dependent 

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} (Tq)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tq$
# - $ln(\frac{z(r)}{\zeta(r)}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - $-ln(\frac{z(r)}{\zeta(r)}-1)=-ln(\tilde{\alpha})-\beta ln(N)$
# - $ln((\frac{z(r)}{\zeta(r)}-1)^{-1})=ln(\frac{1}{\tilde{\alpha}})  -\beta ln(N)$

# #### (Version5) total demand with time-window size

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $r=\frac{N}{lCW}=\frac{N/l}{CW}$

# - Capacity ($c$): Chosen as the upper limit of the free-flow speed segment
#     - While the congested segment may vary depending on the size of $W$, the free-flow segment remains consistent.
#     - The end of the free-flow segment can be interpreted as the onset of congestion.
#         - VDS_num=1205583: c= 900
#         - VDS_num=1203506: c = 1200    
# - Fitting result (t=t_0 * (1 + a * (x / c) ** b))
#     - VDS_num=1205583: t=t_0 * (1 + 0.86 * (x / 900) ** 1.9), R^2 = 0.832
#     - VDS_num=1205583: t=t_0 * (1 + 0.54 * (x / 1200) ** 1.13), R^2 = 0.573
# - A detailed discussion is needed on how to define capacity and interpret the associated parameters.

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
# ### Previous version

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### Version1: natural log of average flow-rate
# -

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
# #### Version2: natural log of total demand
# -

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} (Tq)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tq$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - $y_n = ln(\tilde{\alpha})+\beta x_n$

#
# - parameter calibration
#     -  $\tilde{\alpha}' = ln(\tilde{\alpha})=ln(\frac{\alpha}{(WC)^\beta})$
#     -  $\alpha = \exp(\tilde{\alpha}')\times (WC)^\beta$

# <img src='./01_BPR/02_1_presentation_fig/BPR_calibration_v2.png' width=70%>

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### Version3: inverse natural log of total demand
# -

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

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### Previous note
# -

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

# <img src='./01_BPR/02_1_presentation_fig/BPR_calibration_v3.png' width=50%>

# <img src='./01_BPR/02_1_presentation_fig/BPR_calibration_v4.png' width=30%>

# + [markdown] jp-MarkdownHeadingCollapsed=true
# ##### Trials for model fitting improvment (e.g., R-squared)
# -

# ##### Measures for model fitting

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

# ##### How to increase model fitting

# ##### 1) Removing days with multiple congested periods within one fixed-time congested window
# - The number of dates before and after filtering
# - |            | SR-91  | I-5 |
# |------------|---------------|-----------------|
# | before_filter |   300       |     230      |
# | after_filter   | 266          | 230           |
# | \|before-after\|  | 34        | 0          |

# - RMSE: small more fit ⟷ R-squared: small less fit
# <img src='./01_BPR/02_1_presentation_fig/BPR_calibration_v3_beforeafter.png' width=30%>

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

# #### daily-basis BPR function estimate

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### daily average flowrate
# -

# <img src='./01_BPR/02_1_presentation_fig/BPR_daily average flow.png' width=80%>

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### Jin (2025): weighted average of ideal arrival time window
# -

# - $z/\zeta = 1+\alpha (\frac{N}{lC\tilde{W}})^\beta$
#     - $\xi_j=\frac{D_j}{D}$, where $D=\sum_{j=1}^J D_j$
#     - $z = \sum_{j=1}^J \xi_j z_j$
#     - $\sum_{j=1}^J \frac{\xi_j^{\beta+1}}{W_j^\beta}=\frac{1}{\tilde{W}^\beta}$
#         - $\tilde{W}=(\frac{1}{\sum_{j=1}^J \frac{\xi_j^{\beta+1}}{W_j^\beta}})^{1/\beta}$ 

# - $W_1=W_2=1\text{hours}$, $W_3=\infty$
# - $\beta = 4$

# + [markdown] jp-MarkdownHeadingCollapsed=true
# - higher R-sqaured
# <img src='./01_BPR/02_1_presentation_fig/BPR_daily_jin_2025.png' width=100%>
# -

# #### BPR calibration based on different temporal scales

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

# +
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

# + [markdown] jp-MarkdownHeadingCollapsed=true
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
# -

# <div class="alert alert-danger">
#
# <6/17/2025>
# - Unlike speed-based peak-period, It did not show the BPR shape.
#     - why?) Because the congestion period alone doesn’t capture distributional information—like the full-day volume—which is critical for explaining travel times.
#     - fixed와 unfixed가 근본적인 차이같어. 이와 관련한 이유를 제시해야할 것 같은데?

# +
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


# + [markdown] jp-MarkdownHeadingCollapsed=true
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
# -

# - <img src='./01_BPR/proj2_Qinlong_2018.png' width=50%>
# - Figure: Yan et al. (2018)

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


# +
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

# +
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

# +
x = [0, 1.6, 1.7, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 5, 5, 6, 7]
# peaks, properties = find_peaks(x, distance=5, plateau_size=2)

peaks, properties = find_peaks(x,height=2,distance=1)
# , width=5
print(peaks)
print(properties)
# -

# # Appendix

# - imputation: 5min (30se)

# + [markdown] jp-MarkdownHeadingCollapsed=true
# ## Pipeline Steps with Manual check

# + [markdown] jp-MarkdownHeadingCollapsed=true
#
# - <img src='./01_BPR/02_1_presentation_fig/2_Data_process_flowchart.png' width=90%>  
# -

# - Discussion about 'capping'
#     - I capped unrealistic 5-min aggregated speed estimates at 80 mph. Such inflated values can bias average speeds across periods. They may arise from measurement errors or from applying g-factors on an hourly basis, which is a relatively coarse interval. I believe it makes more sense to correct these unrealistic values to a realistic level that still reflects free-flow speeds.

# ### 1. `load_or_aggregate(...)`
# **Inputs:** rawdata (30-sec), date, config.  
# **Outputs:** `traffic_within_day` (5-min grid) with per-lane + aggregate metrics.
#
# - Converts 30-sec counts → per-lane flows (vph).  
# - Converts occupancies + gfactor → densities (vpm).  
# - Speed per lane = flow/density.  
# - Aggregated traffic states
#     - Aggregate speed = flow-weighted harmonic mean:  $\bar v = \frac{\sum q_i}{\sum (q_i / v_i)}$
#     - Aggregate travel time = $60/\bar v$.  
#     - Aggregate flow = mean(flow across lanes).  
#     - Aggregate density = $\bar q / \bar v$. 
# - Also compute CVs across lanes.  
# - Cached to disk by VDS/date.
#
# **Manual check:** `1. (load_or_aggregate) Rawdata_110101.xlsx`<br>
# Pick one day(e.g. `rawdata_110101.csv`)
# 1. Compute flow per lane from counts.  
# 2. Compute density from occupancy+gfactor.  
# 3. Speed per lane = flow/density.  
# 4. Verify aggregate speed matches harmonic mean.  
# 5. Check `time_slot` = midpoint (e.g., 8:02:30 → 482.5).
#
# ---
#
# ### 2. `highfreeflowspeed_conversion(...)`
# **Inputs:** aggregated traffic.   `traffic_within_day`<br>
# **Output:** capped aggregate `speed`.  `traffic_within_day`
# - If `speed > threshold` (e.g. 80 mph), replace with threshold.
#
# **Manual check:**  (e.g. `traffic_within_day_110101.csv`) <br>
# Scan daily traffic speed pattern before and after: day → no `speed` should exceed threshold.
#
# ---
#
# ### 3. `interpolate_missing(...)`
# **Inputs:** aggregated traffic (may have missing slots).  `traffic_within_day` <br>
# **Output:** full uniform grid, with interpolated rows inserted. `traffic_within_day`
#
# - Expected slots = `{a_tf/2, a_tf+ a_tf/2, …, 24*60 - a_tf/2}`.  
# - For missing slots: interpolate flows & densities linearly.  
# - Recompute speeds as `flow/density`.  
#
# **Manual check:**  (e.g. `traffic_within_day_110101.csv`) <br>
# - Check for missing time slots.
# - Verify that each lane’s missing flows and densities are properly interpolated.
# - Confirm that missing speeds are recalculated as flow ÷ density.
# - Compute whole-lane average speed using the flow-weighted harmonic mean (Method A).
# - Compute average flow, density, and speed using averaged flow and density values (Method B).
# - Ensure the average speeds from Method A and Method B are consistent.
# ---
#
# ### 4. `assign_fixedtime_peaks(...)`
# **Inputs:** cleaned traffic.  
# **Output:** detect changepoints: `division` column.
#
# - `hour` mode: `division = floor(time_slot/60)`.  
# - `peak` mode: mark fixed morning/afternoon windows.  
# - `entireday`: all zeros.  
# - `speedbasedpeak`: unchanged here (labeling comes later).
#
# **Manual check:**  (e.g. `traffic_within_day_110101.csv`) <br>
# Check a few `time_slot` values vs. config’s windows.
#
# ---
#
# ### 5. `detect_speed_peaks(...)` (speed-based mode)
# **Inputs:** traffic after steps 1–3.  
# **Outputs:**  `traffic['division']` (0 = off-peak, 1,2,... = peaks)/ `peak_list` = list of `{idx, start, end, length}`. <br>
#
# - Apply RDP/PELT to find breakpoints.  
# - For each segment:
#   - Compute mean speed, segment length.  
#   - If free-flow-like (long & near freeflow), mark off-peak.  
#   - Else assign a peak index.  
# - Construct `peak_list`.  
# - Plot breakpoints and peaks.
#
# **Manual check:**  
# 1. Confirm breakpoints in plot align with sharp changes.  
# 2. Compute mean speed per segment manually; check labeling logic.  
# 3. Confirm `peak_list` times match segment boundaries.
#
# ---
#
# ### 6. `compute_metrics(...)`
# **Inputs:** one group (division of traffic).  
# **Outputs:** traveltime, demand, avg_flow, period, duration.
#
# - Flows = group['flow'], Speeds = group['speed'].  
# - If peak (division != 0):
#   - Duration = `(len(group)-1) * a_tf`.  
#   - Demand = $\sum f \cdot (a_{tf}/60)$
#   - Avg flow = mean(flows).  
#   - Travel time = $\frac{\sum f/v}{\sum f} \times 60$.  
#   - Period = morning/afternoon if start slot inside config windows.  
# - Else (off-peak):
#   - Duration = `(len(group)+group_num-1) * a_tf`.  
#   - Same formulas for demand, avg flow, traveltime.
# - Check if the result is same based on the wholelane's average or individual lane's flows.
#
# **Manual check:**  
# Pick one detected peak group:  
# 1. Sum flows, compute demand.  
# 2. Compute flow-weighted travel time.  
# 3. Confirm duration formula.  
# 4. Confirm period naming matches config windows.
#
# --
#

# + [markdown] jp-MarkdownHeadingCollapsed=true
# ### Quick Audit Checklist
# - After Step 1: export CSV, recompute one slot manually.
#     - '1. (load_or_aggregate) Rawdata_110101.xlsx'
# - After Step 2: assert no `speed > threshold` 
# - After Step 3: check full grid present + one interpolation.
#     - '3,6. Interpolate_missing (avg traffic flow, density cal) traffic_1214006_110101.xlsx' 
# - After Step 5: check plot + `peak_list`.:
#     - check the plot 
# - After Step 6: recompute metrics for one group manually and compare.
#     - '3,6. Interpolate_missing (avg traffic flow, density cal) traffic_1214006_110101.xlsx'
#     - when over 80mph cell exists
#         - 6-1. traffic_1214006_peak,off-peak traffic_by individual lane or entire lane based
#         - 6-2. traffic_1214006_110111 (verify when the traveltimes are different)
# -


