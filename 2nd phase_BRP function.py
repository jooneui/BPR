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

# + [markdown] editable=true slideshow={"slide_type": ""}
#
# <div class="alert alert-warning">
#     
# - Blue: notes (info) | White: slides | Green: main(success) | Red: past versions(danger)
# - Generally, the presentation follows <font size = 5> slides -> main text -> personal notes ->  code </font> in each subsection (Outline only appear at the beginning of each section, some subsections may not have personal notes or codes)
#     
# </div>
#     
# -

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


# + editable=true slideshow={"slide_type": ""}
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
# In this study, we identify uncongested periods by segmenting daily speed (or cumulative speed) profiles into approximately linear intervals. We apply changepoint detection to the speed profile because it provides the most distinct and physically meaningful signal for identifying regime transitions. In contrast, flow and density (or occupancy) each present limitations. Flow is non-unique—the same flow rate can appear in both uncongested and congested states—making it difficult to determine whether a given segment corresponds to free flow or congestion. Density, while unique across regimes, fluctuates even within uncongested periods, which prevents changepoint algorithms from precisely detecting the true transition boundary between regimes. Speed, by comparison, remains nearly constant during free flow and changes sharply at the onset or dissipation of congestion, allowing for more accurate and interpretable segmentation.
#
# To perform the segmentation, we use two widely adopted algorithms in parallel: PELT (Pruned Exact Linear Time) and RDP (Ramer–Douglas–Peucker). The following subsection describes how each method is applied to the daily speed profiles.
#
# - RDP and PELT explanation is in TRB2026 paper

# <div class="alert alert-info">
#
# __Uncongsted Period Selection__
#
# After applying PELT and RDP-based segmentation to the speed and distance time series, respectively, we proceed to identify and classify traffic periods based on characteristics of uncongested conditions. This process consists of two main phases: segment classification and adjacent-segment merging.
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
# The near–free-flow threshold of 45 mph is chosen to reflect the range of stable speeds observed across different uncongested periods. While early-morning and late-night traffic typically exhibit higher free-flow speeds around 60–70 mph, the uncongested periods between the morning and evening peaks often sustain lower yet stable speeds of approximately 50 mph. Hence, 45 mph serves as a representative lower bound that captures all sustained, near–free-flow conditions throughout the day.
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

# <center> <img src='./01_BPR/02_1_presentation_fig/2_uncongested_ambiguous_cases.png' width = "40%"> </center>

# - __Condition A (Sustained)__: the duration of the segment is at least $T$ ($D_i \ge T=90 \text{minutes}$)
# - __Condition B (Near-free-flow)__: the mean speed of the segment is at least $v_1$ ($ v_i \geq v_1 = 45 \text{mph} $)
#
# - __Case1__: origianl
#     - $\phi(S_i) = 
# \begin{cases}
#   1 & \text{if } B \cap A \\
#   2 & \text{otherwise}
# \end{cases}$
# - __Case2__: ambiguous part using intensity and neighboring state
#     - $\phi(S_i) = 
# \begin{cases}
#   1 & \text{if } B \cap A \\
#   2 & \text{otherwise}
# \end{cases}$
#     - For the $B \cap \neg A$, update it as $\phi(S_i) = 2$, when $I(s) < 15\,\text{mph}$ and neighbors and uncongested.
#
# - __Case3__: ambiguous part using occupancy
#     -  For the $B \cap \neg A$, update it as $\phi(S_i) = 2$, when $\bar{o}_i < o_{\text{c}}$
#     - $\phi(S_i) =
# \begin{cases}
# 1, & \text{if } B \cap
#    (\bar{o}_i < o_{\text{c}} \;\cup \; A ), \\[6pt]
# 2, & \text{otherwise.}
# \end{cases}
# $
#
# where:
# - $B$: mean speed ≥ 45 mph (near-free-flow condition),
# - $A$: sustained duration ≥ 90 minutes (stability condition),
# - $o_{\text{c}} = 0.16$

# <div class="alert alert-info">
#
#
# __Interpreting Ambiguous Segments Using Occupancy-Based Criteria__
#
#
#
# While segmentation algorithms such as RDP and PELT effectively partition the speed profile into homogeneous intervals, their sensitivity parameters are geometric rather than physical. The level of detail in the resulting segmentation depends entirely on the chosen tolerance (for RDP) or penalty (for PELT), which governs how finely the algorithm reacts to fluctuations in the speed series. In theory, a high parameter value could allow each uncongested period to appear as a single continuous segment, but this setting would also smooth over important transitions such as congestion buildup, recovery phases, or mild congested states. To capture these transitional behaviors, the parameters must instead be set to relatively small values, allowing finer segmentation of the speed profile.
#
# However, when parameters are set small, minor speed fluctuations within the free-flow range can cause a single sustained uncongested period to be divided into multiple short segments. Some of these short segments may then fail the duration condition (A) even though they belong to an overall uncongested regime, leading to misclassification as congested. Because segmentation parameters only reflect the shape of the time series and not its traffic state, purely geometric criteria cannot resolve such cases. Therefore, post-segmentation interpretation must incorporate traffic-theoretic indicators—such as occupancy or density—to identify whether these short, high-speed segments ($\neg A \cup B$) represent true transitional dynamics (e.g., congestion buildup or recovery) or simply internal fluctuations within a sustained uncongested period.
#
# To accomplish this, we employ **occupancy** as a physically grounded indicator of traffic density. Occupancy directly reflects the proportion of time a detector is covered by vehicles and, unlike intensity or local variance, corresponds to a measurable physical state on the **fundamental diagram (FD)**. By plotting segment-level average flow ($\bar{q}_i$) against average occupancy ($\bar{o}_i$), we identify a clear **critical occupancy** around $o_c \approx 0.16$ marking the onset of capacity. Segments with occupancies below this threshold correspond to stable free-flow states, whereas those above indicate higher density and potential congestion.
#
# Initially, we implemented $o_c = 0.16$ as a universal cutoff for reclassifying ambiguous segments. However, empirical results showed that it could not adequately distinguish among the three ambiguous cases. Specifically, it tended to classify all short high-speed segments as uncongested, including **Case 1 and 3** (congestion buildup/recovery and short recovery between congested periods) that should remain part of the congested regime.  
#
# To improve interpretability, we refined the occupancy criterion based on the **capacity-drop characteristics** observed in the fundamental diagram (FD). Using data from SR-91 in 2011, we identified a distinct capacity drop occurring between $o_{\text{low}} = 0.12$ and $o_{\text{high}} = 0.30$. Because the capacity drop represents a **post-breakdown phenomenon**—arising from bounded vehicle acceleration and the formation of a queue—states within this range indicate the presence of congestion and are thus classified as congested. In practice, this region includes the buildup and recovery phases, as well as temporary speed recoveries that occur between congested intervals.
#
# By contrast, **Case 2** segments—short bridges between two free-flow periods—typically exhibit occupancies below $o_{\text{low}} = 0.12$, remaining well below the onset of the capacity-drop regime. Hence, the lower bound ($o_{\text{low}}$) effectively separates genuine free-flow bridges from transitional or congested states.
#
# We retain the original duration–speed logic but reinterpret the uncongested regime to encompass both long-term and short-term free-flow behavior. Traffic is considered **uncongested** when it operates within the free-flow or near-capacity range **without signs of breakdown**, either through sustained stability or sufficiently low occupancy. Formally, the final classification function follows directly as:
#
# $$
# \phi(S_i) =
# \begin{cases}
# 1, & \text{if } B \wedge 
#    (\bar{o}_i < o_{\text{low}} \;\vee \; A ), \\[6pt]
# 2, & \text{otherwise.}
# \end{cases}
# $$
#
# where:
# - $B$: mean speed ≥ 45 mph (near-free-flow condition),
# - $A$: sustained duration ≥ 90 minutes (stability condition),
# - $o_{\text{low}} = 0.12$: upper bound of the unambiguous free-flow regime,
#
# This rule distinguishes the ambiguous cases as follows:
#
# - **Case 1 (Queue buildup or recovery):** short-duration segments with moderate or high occupancy ($\bar{o}_i \ge 0.12$) → *congested*.  
# - **Case 2 (Free-flow bridge):** short-duration but low-occupancy segment ($\bar{o}_i < 0.12$) → *uncongested*.  
# - **Case 3 (Temporary recovery within congestion):** short-duration segment with moderate to high occupancy ($\bar{o}_i \ge 0.12$) → *congested*.  
#
# ---
#
# __Discussion__
#
# This occupancy-based refinement extends the duration–speed logic by embedding a traffic-theoretic measure of density into the classification framework.  
# Unlike geometric segmentation parameters, the occupancy thresholds are derived directly from the fundamental diagram, ensuring physical interpretability and transferability.  
# The approach corrects false positives from segmentation (short free-flow bridges mislabeled as congestion) while maintaining realistic detection of queue transitions and recoveries.  
# By incorporating both **duration** and **density regime**, the final definition ensures that the *uncongested period* consistently represents stable operation within or below the free-flow domain, while all transient or high-density states are classified as *congested*.
#
#
# </div>

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

# #### (Script, 25/11/11)

# <div class="alert alert-info">
#
# **Framework for Identifying Congested and Uncongested Periods**
#
# We first segment each day’s speed (or cumulative speed) profile using either the RDP (Ramer–Douglas–Peucker) or PELT (Pruned Exact Linear Time) algorithm to obtain piecewise-homogeneous intervals.
# Speed is selected as the segmentation variable because free-flow operation produces long, flat plateaus, while breakdown and recovery events appear as sharp geometric changes—providing clear visual cues for both algorithms.
# Since the segmentation groups similar patterns, minor fluctuations within the free-flow range are smoothed and treated as a single continuous interval, effectively filtering out noise while preserving physically meaningful transitions such as the onset or clearance of congestion.
#
# Each detected segment $S_i = [\tau_{i-1} + 1, \tau_i]$ represents a period of relatively consistent traffic state. For each segment, we calculate its duration $D_i$, mean speed $\bar{v}_i$, mean occupancy $\bar{o}_i$, and mean flow rate $\bar{q}_i$. These aggregated statistics provide the basis for determining whether the segment reflects congested or uncongested conditions.
#
# To establish this classification, we construct a fundamental diagram (FD) using the segment-level $(\bar{o}i, \bar{q}i)$ pairs. Because the data are averaged over homogeneous intervals, the resulting FD exhibits a clear and stable structure.
# When the FD exhibits a two-phase relationship, a single critical occupancy effectively separates uncongested and congested regimes.
# However, when the FD reveals a three-phase structure, two characteristic occupancy thresholds—$o{\text{low}}$ and $o{\text{high}}$—appear around the capacity point, defining an intermediate range of operation.
# Empirically, such a three-phase pattern often emerges in urban freeways or bottlenecks with recurring congestion, where traffic alternates between free-flow, transitional, and over-saturated states.
#
# This middle occupancy band does not represent a single traffic regime. Instead, it contains two physically distinct behaviors:
# (i) Transitional states, caused by the formation or dissipation of queues, and
# (ii) Stable near-capacity states, where demand approximately equals downstream supply and no queue develops.
# Although both occupy the same range of occupancy, their physical mechanisms differ fundamentally. The critical distinction is the presence of a queue. Transitional states inherently involve the dynamics of queue formation or dissipation—often accompanied by shockwaves or capacity drops—and therefore belong to the congestion regime. In contrast, stable near-capacity states operate without a queue and thus behave as uncongested, despite their higher density.
#
# <img src="./01_BPR/02_1_presentation_fig/1_mid_plateau.png" width=80%>
#
# To distinguish transitional congestion from stable near-capacity operation, we apply a speed–duration gate based on traffic stability.
# Here, an uncongested period is defined as a sustained near–free-flow condition, identifiable by two measurable indicators:
#
# - Sustained duration ($A$): the segment persists for at least $T = 90$ minutes, representing a stable operating state rather than a brief transitional one.
# - Near–free-flow speed ($B$): the mean segment speed exceeds $v_{nf} = 50$ mph, corresponding to the lower bound of observed free-flow speeds (typically between 50–70 mph) that vary throughout the day.
#
# A segment is classified as uncongested if both conditions are satisfied ($A \land B$); otherwise, it is treated as congested.
# This rule ensures that temporary fluctuations or short-lived drifts within the middle occupancy band—typically associated with queue formation, recovery, or mild instability—are correctly regarded as congestion-related, while long-lasting, high-speed intervals are interpreted as stable, uncongested operation near capacity.
#
# Short, near-capacity states can also appear in the mid-plateau. When such states occur between two uncongested plateaus and differ only slightly in speed or occupancy, the segmentation process naturally merges them into a single sustained interval. This behavior is physically consistent, as these mild variations represent continuous free-flow or near-capacity operation rather than genuine transitions.
# Conversely, when short near-capacity states appear between two congested intervals, they are interpreted as temporary recoveries within congestion—brief episodes of partial speed restoration that do not signal a full regime change.
# In this case, the segmentation and classification together treat these adjacent congested periods and the short recovery segment as a single, unified congested episode.
# This contextual interpretation strengthens the robustness of the framework, ensuring that short-term fluctuations are understood in relation to their surrounding traffic conditions.
#

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

# #### VDS_num: 1205583 (25/7/22)

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

# #### VDS: 1203506 (25/7/22)

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

# + [markdown] editable=true slideshow={"slide_type": ""}
# ### (Code) Package install

# + editable=true slideshow={"slide_type": ""}
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


# + [markdown] editable=true slideshow={"slide_type": ""}
# ### (Code) Peak period detection

# + [markdown] editable=true slideshow={"slide_type": ""}
# #### (Code) Data process

# + tags=["code"] editable=true slideshow={"slide_type": ""}
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


# + editable=true slideshow={"slide_type": ""}
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


# + editable=true slideshow={"slide_type": ""}
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


# + editable=true slideshow={"slide_type": ""}
def skip_if_missing(rawdata, config):
    """
    Check if rawdata exceeds missing_ratio threshold; skip if too many missing slots.
    """
    total_expected = (24 * 60) / config['raw_timeframe']

    for lane in config['lane_num']:
        col_name = f'flow_{lane}'
        # Count total zeros in this lane
        zero_count = (rawdata[col_name] == 0).sum()
        
        if zero_count > (total_expected * config['missing_ratio']):
            return True
    
    return False
    

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

# +
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


# +
def _make_vds_config(config, vds: str, c_lane_num: dict):
    """Shallow clone with per-VDS fields."""
    cfg = dict(config)
    cfg['VDS_num']  = vds
    # cfg['lane_num'] = config['lane_map'][vds]
    cfg['lane_num'] = c_lane_num[vds]
    return cfg

def _build_traffic_for_vds(date: str, filename: str, cfg_vds, vds):
    """Reuses your existing functions to get a per-VDS day traffic frame."""
    # load raw + gfactor
    rawdata, date  = load_raw(filename, cfg_vds)
    if skip_if_missing(rawdata, cfg_vds) :
        print("skip", date)
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
        ['time_slot','speed','time','flow','density','occ']
    computed as simple arithmetic means across VDS for each time_slot.
    """
    # keep only columns we can consistently average
    keep = ['time','time_slot', 'speed', 'flow', 'density','occ']
    stacked = []
    for t in traffic_list:
        if t is not None:
            stacked.append(t[keep].copy())

    if not stacked:
        return None

    # Concatenate with keys and average by time_slot
    # combo = (pd.concat(stacked, keys=range(len(stacked)))
    #            .groupby('time_slot', as_index=False)[['flow','density']].mean())

    combo = (
        pd.concat(stacked, keys=range(len(stacked)))
          .groupby(['time', 'time_slot'], as_index=False)
          .apply(lambda g: pd.Series({
              'flow':    np.average(g['flow'],    weights=c_coverage_length),
              'density': np.average(g['density'], weights=c_coverage_length),
              'occ':     np.average(g['occ'],     weights=c_coverage_length)
          }))
          .reset_index(drop=True))

    # recompute time (min/mile) from averaged speed
    combo['speed'] = combo['flow'] / combo['density']
    combo['traveltime'] = 60.0 / combo['speed']

    # ensure standard ordering like your per-day frames
    combo = combo[['time','time_slot','speed','traveltime','flow','density','occ']].sort_values('time_slot').reset_index(drop=True)
    return combo
# #### (Code) plot codes
# -

# #### (Code) Plot

# +
# def PELT_plot(df, bkpts, date, VDS_num, aggregate_timeframe, peak_list, method, penalty):
    
#     time_slot_hour = df['time_slot'] / 60

#     # joon, pelt, RDP, derivative
#     title_name = {'RDP':'RDP-Based Congested Periods Detection',
#                   'RDP_v':'RDP_v_Based Congested Periods Detection',
#                   'pelt': 'PELT-Based Congested Periods Detection',
#                   'joon': 'Speed Threshold-Based Congested Periods Detection',
#                  'pelt_directpeak': 'PELT-Based Directly Congested Periods Detection',}
    
#     fig, ax1 = plt.subplots(figsize=(12, 5))

#     date_v2 = f'{date[2:4]}/{date[4:6]}/20{date[0:2]}'
#     # Left axis: Changepoints (as vertical lines)
#     ax1.set_xlabel('Time (Hours)',fontsize=16)
#     ax1.set_ylabel('Speed (mph)',fontsize=16, color = 'green')
#     ax1.set_title(f'{title_name[method]}(VDS: {VDS_num}, Date: {date_v2})',fontsize=18)
#     ax1.grid(True)
#     ax1.set_xlim(0, 24+.1)
#     ax1.set_xticks(np.arange(0, 25, 1))

#     # Plot changepoints
#     for bkpt in bkpts:
#         # ax1.axvline(x=(time_slot_hour[bkpt]-(aggregate_timeframe/2)/60), color='black', linestyle='--', linewidth = 1.5,
#         #             label='Changepoints' if bkpt == bkpts[0] else "")
#         ax1.axvline(x=(time_slot_hour[bkpt]), color='black', linestyle='--', linewidth = 1.5,
#             label='Changepoints' if bkpt == bkpts[0] else "")

    
#     # # Plot peak/off-peaks
#     for element in peak_list:
#         if element['idx'] > 0:
#             s_hours, s_minutes = map(int, element['start'].split(':'))
#             s_total_hours = s_hours + s_minutes/60
#             label = 'Congested periods boundary' if element['idx'] == 1 else ''
#             ax1.axvline(x=s_total_hours, color='red', linestyle='--', linewidth=2, label=label)

#             e_hours, e_minutes = map(int, element['end'].split(':'))
#             e_total_hours = e_hours + e_minutes/60
#             # label = 'Peak-Periods' if element['idx'] == 1 else ''
#             ax1.axvline(x=e_total_hours, color='red',linewidth=2, linestyle='--')
            

#     # Right axis: Cumulative speed pattern
#     ax1.plot(time_slot_hour, df['speed'], color='green', linewidth=1, label='Speed')
#     ax1.set_ylim(0,85)
#     ax1.set_yticks(np.arange(0, 85 + 1, 10))  # Ticks at 0, 20, 40, 60, 80
#     # Set y-axis tick label color
#     ax1.tick_params(axis='y', colors='green')
#     # Set y-axis spine (axis line) color
#     ax1.spines['left'].set_color('green')

#     time_slot_hour_re = [0] + time_slot_hour.to_list()
#     cumsum_speed_re = [0] + df['cumsum_speed'].to_list()

#     ax2 = ax1.twinx()
#     ax2.plot(time_slot_hour_re, cumsum_speed_re, color='blue', linewidth=1, label='Cumulative speed')
#     ax2.set_ylabel('Cumulative Speed (miles)',fontsize=16, color='blue')
#     ax2.set_ylim(0, 1600)
#     ax2.set_yticks(np.arange(0, 1600 + 1, 200)) 
#     # Set y-axis tick label color
#     ax2.tick_params(axis='y', colors='blue')
#     # Set y-axis spine (axis line) color
#     ax2.spines['right'].set_color('blue')

#     # Handle legend
#     lines1, labels1 = ax1.get_legend_handles_labels()
#     lines2, labels2 = ax2.get_legend_handles_labels()
#     ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right',fontsize=15)

#     fig.tight_layout()
#     plt.savefig(f'./{working_f}/02 fig/16 PELT/{VDS_num}/{VDS_num}_{date}_{aggregate_timeframe}_{method}_{penalty}.png')
#     # plt.show()  # Uncomment if you want to display the plot

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

# #### (Code) Changepoint algorithme itself

# + jupyter={"source_hidden": true}
# rdp.py: 'rdp_v': rdp itself algorithm: the manual function to recursively find the changepoint by RDP. it is applied in the "rdp_v_segmentation_pea"
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

# #### (Code) Segment -> Division logic

# + jupyter={"source_hidden": true}
import numpy as np
import pandas as pd

def _compute_seg_stats(df, value_col, aggregate_timeframe):
    """
    Returns per-segment stats: mean/min/max/size and length in seconds.
    If value_col == 'speed', seg_mean is computed as sum(flow) / sum(density).
    Expects df['segment'] already assigned.
    """

    g = df.groupby("segment")

    if value_col == "speed":
        # Weighted mean speed = sum(flow) / sum(density)
        seg_mean = (g["flow"].sum() / g["density"].sum()).rename("seg_mean")
        
        # For min/max you probably still want the min/max *speed* values
        seg_minmax = g["speed"].agg(seg_min="min", seg_max="max", seg_size="size")
        seg_stats = pd.concat([seg_mean, seg_minmax], axis=1).reset_index()

    else:
        seg_stats = (
            g[value_col]
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
    # bounds["start_time"] = bounds["min"] - aggregate_timeframe / 2
    # bounds["end_time"]   = bounds["max"] + aggregate_timeframe / 2

    bounds["start_time"] = bounds["min"] 
    bounds["end_time"]   = bounds["max"] 

    
    bounds["length"] = bounds["end_time"] - bounds["start_time"]
    return [
        {
            "idx": int(row["division"]),
            "start": f"{int(row['start_time'] // 60):02d}:{int(row['start_time'] % 60):02d}",
            "end":   f"{int(row['end_time']   // 60):02d}:{int(row['end_time']   % 60):02d}",
            "length": float(row["length"]),
        }
        for _, row in bounds.iterrows()
    ]


# + jupyter={"source_hidden": true}
#congest_method: speed-duration-only

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

    # ✅ If segment is not peak (False), set segment value to 0
    df['seg_con'] = 0
    df.loc[is_peak_rows, "seg_con"] = 1
    
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    df["division"] = div.astype(np.int32)

    return df


# + jupyter={"source_hidden": true}
#congest_method: speedgap-neighbor
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

    # ✅ If segment is not peak (False), set segment value to 0
    df['seg_con'] = 0
    df.loc[is_peak_rows, "seg_con"] = 1
    
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    df["division"] = div.astype(np.int32)

    return df


# + jupyter={"source_hidden": true}
# congest_method: occ
def label_divisions_occupancy(
    df,
    column,
    aggregate_timeframe,
    min_off_len,
    offpeak_ff_speed_threshold,
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
    is_cong_amb = (seg_stats_speed["seg_len_sec"] < min_off_len) & (seg_stats_speed["seg_mean"]    >= offpeak_ff_speed_threshold)

    looks_freeflow = (seg_stats_occ["seg_mean"] < occ_threshold)

    # --- 5) Demote peaks that are NOT isolated-offpeak but look free-flow ---
    # “firstly detected as congested” = is_peak_seg
    # Need to convert to uncongested if (~isolated_offpeak & looks_freeflow)
    demote_mask = is_cong_amb  & looks_freeflow
    is_peak_seg_final = is_peak_seg & (~demote_mask)
    
    # Re-index by segment id for mapping to rows
    # is_peak_seg_final: 각 seg의 con/uncon 상태를 아렬줌 (T/F) 동시에 seg_stats_occ는 inde를 가짐. 이것을 df['segment']로 mapping
    is_peak_seg_final.index = seg_stats_occ["segment"]
    
    # --- 6) Map to rows and collapse to contiguous divisions ---
    is_peak_rows = (
        pd.Series(is_peak_seg_final, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy()
    )

    # ✅ If segment is not peak (False), set segment value to 0
    df['seg_con'] = 0
    df.loc[is_peak_rows, "seg_con"] = 1
    
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    df["division"] = div.astype(np.int32)

    return df


# + jupyter={"source_hidden": true}
# congest_method: occ-soley
def label_solely_occupancy(
    df,
    column,
    aggregate_timeframe,
    min_off_len,
    offpeak_ff_speed_threshold,
    occ_threshold,
    FD_phase):
        
# 1) Compare off-peak and peak segments by speed and duration.
# 2) Merge contiguous peak blocks into 'df['division']'.
# 3) Remove 'islands' (small gaps, high mean values, isolated by off-peak neighbors).
# 4) Renumber based on contiguity.
# Returns: df with 'division' updated (np.int32).

    # Per-segment stats on the speed column
    seg_stats_occ = _compute_seg_stats(df, 'occ', aggregate_timeframe)
    seg_stats_speed = _compute_seg_stats(df, 'speed', aggregate_timeframe)

    is_peak_seg = None  # initialize
    is_peak_seg_final = None  # initialize


    # --- 2) Initial classification (your baseline rule) ---
    if FD_phase == 'three_phases':      
        is_uc_seg = (seg_stats_occ["seg_mean"]   < occ_threshold['occ_l'])
        is_oc_seg = (seg_stats_occ["seg_mean"]  >= occ_threshold['occ_h'])

        mid_band = (seg_stats_occ["seg_mean"]  >= occ_threshold['occ_l']) & (seg_stats_occ["seg_mean"]   < occ_threshold['occ_h'])
        A_long = (seg_stats_occ["seg_len_sec"] >= min_off_len)
        B_fast = (seg_stats_speed["seg_mean"] >= offpeak_ff_speed_threshold)

        # final segment labels
        is_uc_seg = is_uc_seg | (mid_band & A_long & B_fast)
        is_oc_seg = is_oc_seg
        is_c_seg  = mid_band & (~(A_long & B_fast))         # short OR long-but-not-fast
        
        # congested side = C ∪ OC
        is_peak_seg = is_c_seg | is_oc_seg
    
    elif FD_phase == 'two_phases':
        occ_c = occ_threshold['occ_c']
        
        is_uc_seg  = seg["occ_mean"] <  occ_c
        is_oc_seg  = seg["occ_mean"] >= occ_c
        
        is_c_seg   = pd.Series(False, index=seg.index)      # no mid-band in two-phase
        is_peak_seg = is_oc_seg
        
    is_peak_seg_final = is_peak_seg
    
    # Re-index by segment id for mapping to rows
    is_peak_seg_final.index = seg_stats_occ["segment"]
    
    # --- 6) Map to rows and collapse to contiguous divisions ---
    is_peak_rows = (
        pd.Series(is_peak_seg_final, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy())
   
    # uncongested(uc): 0, c: 1
    df['seg_con'] = 0
    df.loc[is_peak_rows, "seg_con"] = 1
    
    if FD_phase == 'three_phases':
        is_c_seg = is_c_seg.rename(index=lambda x: x+1)
        
        is_c_rows = (
        pd.Series(is_c_seg, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy())

        df.loc[(~is_c_rows) & (is_peak_rows), "seg_con"] = 2
    
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0

    # starts_d = np.where((div[:-1] == 0) & (div[1:] != 0))[0]
    # # set the 0 value just before the run to match the upcoming non-zero value
    # for s in starts_d:
    #     div[s] = div[s + 1]
    
    df["division"] = div.astype(np.int32)

    return df


# + jupyter={"source_hidden": true}
# congest_method: occ-soley
def label_solely_speed(
    df,
    aggregate_timeframe,
    offpeak_ff_speed_threshold):
        
# 1) Compare off-peak and peak segments by speed and duration.
# 2) Merge contiguous peak blocks into 'df['division']'.
# 3) Remove 'islands' (small gaps, high mean values, isolated by off-peak neighbors).
# 4) Renumber based on contiguity.
# Returns: df with 'division' updated (np.int32).

    # Per-segment stats on the speed column
    seg_stats_speed = _compute_seg_stats(df, 'speed', aggregate_timeframe)

    is_peak_seg = None  # initialize
    is_peak_seg_final = None  # initialize

    # --- 2) Initial classification (your baseline rule) ---
    is_c_seg = (seg_stats_speed["seg_mean"]   < offpeak_ff_speed_threshold)
    is_uc_seg = ~is_c_seg
    
    # congested side = C ∪ OC
    is_peak_seg_final = is_c_seg
    
    # Re-index by segment id for mapping to rows
    is_peak_seg_final.index = seg_stats_speed["segment"]
    
    # --- 6) Map to rows and collapse to contiguous divisions ---
    is_peak_rows = (
        pd.Series(is_peak_seg_final, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy())
   
    # uncongested(uc): 0, c: 1
    df['seg_con'] = 0
    df.loc[is_peak_rows, "seg_con"] = 1
    
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    
    df["division"] = div.astype(np.int32)
    return df
# -

# #### (Code) Congested/Uncongested decision Algorithm

# +
# Verion0: speedbased_directpeak!!

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
# Version1: pelt based 

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
# Version2: RDP_v based
from rdp import rdp
import numpy as np
import pandas as pd

def rdp_v_segmentation_peak(
    df, column, epsilon, offpeak_ff_speed_threshold, speed_gap_threshold,
    aggregate_timeframe, date, VDS_num, min_off_len, min_peak_len, method, congest_method, occ_threshold, FD_phase):
    
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
    seg_id[0] = 1 # first point (to mirror your original behavior)
    seg = 0
    for s, e in zip(bp[:-1], bp[1:]):
        seg += 1
        seg_id[s+1:e+1] = seg
        
    # seg_id[-1] = seg  # last point (to mirror your original behavior)
    df["segment"] = seg_id

    # speed-duration-only, 'speedgap-neighbor', 'occ', occ-soley
    if congest_method == 'speedgap-neighbor':
        # Strategy A: speed gap + neighbor isolation
        df = label_divisions_speedgap_islands(
            df=df, column="speed", aggregate_timeframe=aggregate_timeframe,min_off_len=min_off_len,
            offpeak_ff_speed_threshold=offpeak_ff_speed_threshold,
            speed_gap_threshold=speed_gap_threshold)
    
    elif congest_method == 'speed-duration-only':
        df = label_divisions_speed(df=df, column="speed",aggregate_timeframe=aggregate_timeframe, min_off_len=min_off_len, offpeak_ff_speed_threshold=offpeak_ff_speed_threshold, speed_gap_threshold=speed_gap_threshold)
    
    elif congest_method == 'occ':
        # Strategy B: occupancy-based (no islands)
        df = label_divisions_occupancy(
            df=df, column="occ",          # e.g., your occupancy column name
            aggregate_timeframe=aggregate_timeframe, min_off_len=min_off_len, offpeak_ff_speed_threshold=offpeak_ff_speed_threshold,occ_threshold=occ_threshold)     # e.g., 0.10 (10%) or whatever scale you use)
    
    elif congest_method == 'occ-solely':
        # Strategy B: occupancy-based (no islands)
        df = label_solely_occupancy(
            df=df, column="occ",          # e.g., your occupancy column name
            aggregate_timeframe=aggregate_timeframe, min_off_len=min_off_len, offpeak_ff_speed_threshold=offpeak_ff_speed_threshold, occ_threshold=occ_threshold[VDS_num], FD_phase=FD_phase)     # e.g., 0.10 (10%) or whatever scale you use)
    
    elif congest_method == 'speed-solely':
        # Strategy B: occupancy-based (no islands)
        df = label_solely_speed(
            df=df, aggregate_timeframe=aggregate_timeframe, offpeak_ff_speed_threshold = offpeak_ff_speed_threshold)     # e.g., 0.10 (10%) or whatever scale you use)

    
    peak_list = _build_peak_list(df, aggregate_timeframe)

    # 9) Plot + return (reuse your existing plotter)
    PELT_plot(df, bp.tolist(), date, VDS_num, aggregate_timeframe, peak_list, method, epsilon)
    return df, peak_list


# + jupyter={"source_hidden": true}
# Version4: RDP based
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
# Version5: def speedbasedpeak(df, column, speed_upper, min_minutes, max_outliers, aggregate_timeframe, method):
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


# +
# Version6: divisions based on fixed temporal_range.

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

# #### (Code) Compute the traffic_metrics for each division

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
    
    
    if (config['temporal_scale'] in ('speedbasedpeak', 'peak')) and (division_idx != 0):
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
        
        t_m = group.time_slot.min()
        t_M = group.time_slot.max()

        sum_prod = (flow_good / speed_good).sum()
        traveltime = sum_prod / sum_flow * 60
        speed = 1/traveltime * 60
        density = avg_flow / speed
        
        m, M = config['peak_periods']['morning']
        a, A = config['peak_periods']['afternoon']
        if criterion == "division":
            # start time
            if (m <= t_m) and (t_M < M):
                period = 'morning-peak'
            elif (a <= t_m) and (t_M < A):
                period = 'afternoon-peak'
            else:
                period = 'peak-in-offpeak'
                # period = 'off-peak'
        elif criterion == "segment":
            val = group['seg_con'].iloc[0]
            if val == 0:
                period = 'uc'
            elif val == 1:
                period = 'c'
            elif val == 2:
                period = 'oc'
            
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

# #### (Code) Save the computed metrics

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


def process_daily_traffic(traffic, config, date, rawdata, criterion, result_input):
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
        results["dayofweek"].append(config['Day_list'][int(group.iloc[0]['time'].weekday())])
        results["duration"].append(dur)
        results["start"].append(start_time)
        results["end"].append(end_time)
        

    return results


# #### (code) implementation

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
        print(config['VDS_num'])
        return rdp_v_segmentation_peak(
            df = traffic, column='speed',
            # epsilon=12,3,5(이값이 현재최신),4,10, 4(최신), 3(ㅚ신)
            epsilon=2.5, 
            offpeak_ff_speed_threshold= params['offpeak_ff_speed_threshold'][config['VDS_num']],
            # offpeak_ff_speed_threshold= params['offpeak_ff_speed_threshold'],
            speed_gap_threshold = params['speed_gap_threshold'],
            aggregate_timeframe=config['aggregate_timeframe'],
            date=date, VDS_num=config['VDS_num'],
            min_off_len=params['min_off_len'],
            min_peak_len=params['min_peak_len'],
            method=params['method'],
            congest_method = params['congest_method'],
            occ_threshold = params['occ_threshold'],
            FD_phase = params['FD_phase'],
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
    # 'VDS_list': ['1212611','1205583','1214006'],  #,'1205572','1205541'  # used only when spatial_scope == 'multi_vds'
    # 'VDS_list': ['1203524','1203481'],  #,'1205572','1205541'  # used only when spatial_scope == 'multi_vds'
    # 'VDS_list': ['1212611','1205572','1205583','1214006'],  #,'1205572','1205541'  # used only when spatial_scope == 'multi_vds'
    # 'VDS_list': ['1205583','1214006','1212611'],    # used only when spatial_scope == 'multi_vds'
    # 'lane_map': c_lane_num,               # {'vds': [lane ids], ...}
    

    
    # Temporal granularity: 'hour', 'peak'(fixedtiime-based), 'entireday', 'speedbasedpeak'
    'temporal_scale': 'speedbasedpeak', # entireday, speedbasedpeak, hour

    # File paths and identifiers
    'path': './01_BPR',           # base data directory
    'dir': '5min',
    # 'VDS_num': VDS_num,         # detector ID
    # 'lane_num': lane_num,       # list of lane indices
    # 'file_list': file_list,     # list of raw data filenames
    'Day_list': ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
    # Data quality thresholds
    'missing_ratio': 0.05,      # max allowed missing fraction

    # Time parameters (minutes)
    'raw_timeframe': 5,
    'aggregate_timeframe': 5,

    # Peak window definitions (minutes from midnight): start_time basis
    'peak_periods': {
        # 'morning': (5.5 * 60, 11 * 60),
        # 'afternoon': (12.5 * 60, 21 * 60)}
        'morning': (0 * 60, 12 * 60),
        'afternoon': (12 * 60, 24 * 60)},
    # Speed-based peak |detection parameters
    'speedbased_params': {
        ## joon, pelt, RDP_v, derivative, pelt_directpeak
        'method': 'RDP_v',
        'congest_method':'speed-solely', # speed-duration-only, 'speedgap-neighbor', 'occ', occ-solely, speed-solely
        'pelt_min_length': 5,
        'min_off_len': 90,
        'min_peak_len': 0,
        'speed_upper': 60,
        # 'freeflow_speed':70,
        # 'freeflow_speed_epsilon':20,
        'offpeak_ff_speed_threshold': {'1203506': 55, '1203524': 55, '1203481': 55, '1205541': 57, '1212611': 57, '1205572': 57, '1205583': 57, '1214006': 57, 'MULTI_1212611+1205583+1214006': 55,'MULTI_1212611+1205572+1205583+1214006': 55},
        'FD_phase': 'three_phases', #two_phases, three_phases,
        # 'offpeak_ff_speed_threshold':50,
        'speed_gap_threshold':15,
            'occ_threshold': {       
        '1203506': {'occ_l': 0.11, 'occ_h': 0.31},
        '1205541': {'occ_l': 0.09, 'occ_h': 0.15},
        '1212611': {'occ_l': 0.11, 'occ_h': 0.24},
        '1205572': {'occ_l': 0.09, 'occ_h': 0.22},   # appears once only
        '1205583': {'occ_l': 0.095, 'occ_h': 0.14},
        '1214006': {'occ_l': 0.07, 'occ_h': 0.29}},
        'FD_phase': 'three_phases' #two_phases, three_phases
    }
}

# +
from pathlib import Path
import os
import pandas as pd


# --- small utilities ---
def cleaned_file_list(folder: Path) -> list[str]:
    files = sorted(p.name for p in folder.iterdir() if p.is_file())
    return [f for f in files if f != '.DS_Store']

def apply_peak_detection(df, date, cfg):
    """Set 'division'/'segment' per cfg['temporal_scale']; return (df, peaks_or_None)."""
    if cfg['temporal_scale'] == 'speedbasedpeak':
        df, peaks = detect_speed_peaks(df, date, cfg)
        # return df, peaks
    # df['division'] = 0
    # df['segment']  = 0
    return df, peaks

def append_daily_results(df, cfg, date, raw, results_div, results_seg):    
    results_div = process_daily_traffic(df, cfg, date, raw, "division", results_div)
    results_seg = process_daily_traffic(df, cfg, date, raw, "segment", results_seg)
    return results_div, results_seg

# --- core runners ---
def run_single_vds(cfg, base_path: Path, vds_num: str, timeframe_min: int, c_lane_num: set):
    lane_num = c_lane_num[vds_num]
    cfg = dict(cfg, VDS_num=vds_num, lane_num=lane_num)

    data_dir = base_path / cfg['dir'] / vds_num
    file_list = cleaned_file_list(data_dir)

    results_div = {"date": [],"division": [],"period": [],"dayofweek": [],"duration": [],"start": [],"end": [],"total_demand": [],"avg_flow": [],"traveltime": [],"avg_speed":[],"density":[],"avg_occ":[]}
    results_seg = {"date": [],"segment": [],"period": [],"dayofweek": [],"duration": [],"start": [],"end": [],"total_demand": [],"avg_flow": [],"traveltime": [],"avg_speed":[],"density":[],"avg_occ":[]}
    set_peak_period = pd.DataFrame(columns=["date", "peak_list"])

    for fname in file_list:
        print(fname)
        raw, date = load_raw(fname, cfg)
        if skip_if_missing(raw, cfg):
            continue
        traffic, _date = aggregate_rawdata_5min(raw, timeframe_min, date, lane_num, vds_num)

        if cfg['temporal_scale'] == 'entireday':
            traffic[['segment','division']]=0
            peaks = []
            
        elif cfg['temporal_scale'] == 'speedbasedpeak':
            traffic, peaks = apply_peak_detection(traffic, date, cfg)

        elif (cfg['temporal_scale'] == 'hour'):
            step = int(cfg['aggregate_timeframe'])
            rows_per_hour = int(60//step)

            idx = np.arange(len(traffic))

            hour_id = (idx // rows_per_hour) + 1

            traffic['segment']=hour_id
            traffic['division']=hour_id
            peaks = []

        # traffic.to_csv(f"./traffic_{vds_num}_{fname}.csv")
        if peaks is not None:
            set_peak_period = pd.concat(
                [set_peak_period, pd.DataFrame([{'date': date, 'peak_list': peaks}])],ignore_index=True)

        results_div, results_seg = append_daily_results(traffic, cfg, date, raw, results_div, results_seg)

    return results_div, results_seg, set_peak_period

def run_multi_vds(cfg, timeframe_min: int, c_lane_num: dict):
    dates_common, date_to_files = _common_dates_and_files(cfg)
    if not dates_common:
        print("No common dates across VDS_list; nothing to process.")
        return None, None, pd.DataFrame(columns=["date", "peak_list"])

    multi_label = "MULTI_" + "+".join(cfg['VDS_list'])
    temp_cfg = dict(cfg, VDS_num=multi_label)

    results_div = {"date": [],"division": [],"period": [],"dayofweek": [],"duration": [],"start": [],"end": [],"total_demand": [],"avg_flow": [],"traveltime": [],"avg_speed":[],"density":[],"avg_occ":[]}
    results_seg = {"date": [],"segment": [],"period": [],"dayofweek": [],"duration": [],"start": [],"end": [],"total_demand": [],"avg_flow": [],"traveltime": [],"avg_speed":[],"density":[],"avg_occ":[]}
    set_peak_period = pd.DataFrame(columns=["date", "peak_list"])

    for date in dates_common:
        coverage_lengths = []
        per_vds = []

        for vds in cfg['VDS_list']:
            cfg_vds  = _make_vds_config(cfg, vds, c_lane_num)
            base_dir = Path(cfg_vds['path']) / '11 Rawdata' / cfg_vds['dir'] / vds
            fname    = date_to_files[date][vds]
            traffic, cov_len = _build_traffic_for_vds(date, fname, cfg_vds, vds)
            if traffic is None:
                per_vds = []
                break
            per_vds.append(traffic)
            coverage_lengths.append(cov_len)

        if not per_vds:
            continue

        speedprofile_plot(per_vds, timeframe_min, cfg, date)

        traffic_combo = _combine_vds_traffic(per_vds, cfg['aggregate_timeframe'], coverage_lengths)
        if traffic_combo is None:
            continue

        # Detect peaks and summarize
        traffic_combo, peaks = apply_peak_detection(traffic_combo, date, temp_cfg)
        traffic_combo.to_csv(f"./traffic_combo_{fname}.csv")
        if peaks is not None:
            set_peak_period = pd.concat(
                [set_peak_period, pd.DataFrame([{'date': date, 'peak_list': peaks}])],
                ignore_index=True
            )

        results_div, results_seg = append_daily_results(traffic_combo, cfg, date, raw=None, results_div=results_div, results_seg=results_seg)

    return results_div, results_seg, set_peak_period


# +
import matplotlib.pyplot as plt
import numpy as np

def PELT_plot(df, bkpts, date, VDS_num, aggregate_timeframe, peak_list, method, penalty):
    # Set global aesthetic parameters for a "clean" look
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
    
    time_slot_hour = df['time_slot'] / 60
    
    title_name = {
        'RDP': 'RDP-Based Congested Periods Detection',
        'RDP_v': 'RDP_v_Based Congested Periods Detection',
        'pelt': 'PELT-Based Congested Periods Detection',
        'joon': 'Speed Threshold-Based Congested Periods Detection',
        'pelt_directpeak': 'PELT-Based Directly Congested Periods Detection',
    }
    
    # Increase DPI for higher quality and set a clean background
    fig, ax1 = plt.subplots(figsize=(9, 4), dpi=100)
    
    date_v2 = f'{date[4:6]}/{date[6:8]}/20{date[2:4]}' # Adjusted for consistent formatting
    
    # Title and Labels
    ax1.set_title(f'{title_name[method]}\n(VDS: {VDS_num}, Date: {date_v2})', 
                  fontsize=18, fontweight='bold', pad=20)
    ax1.set_xlabel('Time (Hours)', fontsize=14, labelpad=10)
    ax1.set_ylabel('Speed (mph)', fontsize=14, color='#2E7D32', fontweight='bold')
    
    # 1. Primary Plot: Speed (Left Axis)
    ax1.plot(time_slot_hour, df['speed'], color='#4CAF50', linewidth=1.8, label='Speed', alpha=0.9)
    ax1.set_ylim(0, 85)
    ax1.set_xlim(0, 24)
    ax1.set_xticks(np.arange(0, 25, 1))
    ax1.tick_params(axis='y', colors='#2E7D32')
    
    # Subtle Speed Threshold (e.g., 60mph) for context
    ax1.axhline(63, color='#D84315', linestyle=':', linewidth=1.5, alpha=0.8)
    
    # # 2. Secondary Plot: Cumulative Speed (Right Axis)
    ax2 = ax1.twinx()
    time_slot_hour_re = [0] + time_slot_hour.to_list()
    cumsum_speed_re = [0] + df['cumsum_speed'].to_list()
    
    # Use a subtle fill for cumulative speed to avoid cluttering lines
    ax2.fill_between(time_slot_hour_re, cumsum_speed_re, color='#1976D2', alpha=0.1)
    ax2.plot(time_slot_hour_re, cumsum_speed_re, color='#1976D2', linewidth=1.5, alpha=0.7, label='Cumulative Speed')
    
    ax2.set_ylabel('Cumulative Speed (miles)', fontsize=14, color='#1565C0', fontweight='bold', labelpad=10)
    ax2.set_ylim(0, 1600)
    ax2.tick_params(axis='y', colors='#1565C0')
    
    # 3. Changepoints and Peak Periods
    # Changepoints (PELT results)
    for i, bkpt in enumerate(bkpts):
        label = 'Changepoints' if i == 0 else ""
        ax1.axvline(x=time_slot_hour[bkpt], color='#424242', linestyle='--', linewidth=1.2, alpha=0.8, label=label)

    # Congested Periods (Boundaries)
    for i, element in enumerate(peak_list):
        if element['idx'] > 0:
            s_hours, s_minutes = map(int, element['start'].split(':'))
            s_total = s_hours + s_minutes/60 - 5/60
            e_hours, e_minutes = map(int, element['end'].split(':'))
            e_total = e_hours + e_minutes/60
            
            # Highlight the congestion zone
            # ax1.axvspan(s_total, e_total, color='#FF5252', alpha=0.15) 
            
            # Boundary lines
            # label = 'Peak periods' if i == 0 else ""
            # ax1.axvline(x=s_total, color='#D32F2F', linestyle='-', linewidth=2, alpha=0.8, label=label)
            # ax1.axvline(x=e_total, color='#D32F2F', linestyle='-', linewidth=2, alpha=0.8)

    # Styling and Legend
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.4)
    ax1.spines['left'].set_color('#2E7D32')
    ax2.spines['right'].set_color('#1565C0')
    
    # Combined Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    # Unique labels only
    by_label = dict(zip(labels1 + labels2, lines1 + lines2))
    # by_label = dict(zip(labels1, lines1))
    ax1.legend(by_label.values(), by_label.keys(), loc='upper left', fontsize=11, frameon=True, shadow=True)

    plt.tight_layout()
    
    # Save with proper metadata
    save_path = f'./{working_f}/02 fig/16 PELT/{VDS_num}/{VDS_num}_{date}_{aggregate_timeframe}_{method}_{penalty}.png'
    plt.savefig(save_path, bbox_inches='tight')
    plt.show()


# +
from pathlib import Path
import os
import pandas as pd

# Note: '1203506' was duplicated in your c_lane_num dict. Keep one entry.
c_lane_num = {
    '1212611':[1,2,3,4,5,6], '1205572':[1,2,3,4,5,6], '1205583':[1,2,3,4,5,6],
    '1203506':[1,2,3,4], '1214006':[1,2,3,4], '1205541':[1,2,3,4],
    '1203589':[1,2,3,4], '1203615':[1,2,3,4], '1203524': [1,2,3,4], '1203481': [1,2,3,4]
}

working_f = '01_BPR'
raw_timeframe = 5

## SR-91
# VDS_single_list = ['1203481','1203506']
##I-5
# VDS_single_list = ['1214006','1205583','1205572','1212611','1205541']
##all '1203481',
# VDS_single_list = ['1203481','1203506','1214006','1205583','1205572','1212611','1205541']
VDS_single_list = ['1214006']

# Base path for raw files
base_path = Path(config['path']) / '11 Rawdata'

all_results_div = None
all_results_seg = None
all_peaks = None

# Single-VDS mode
if config['spatial_scope'] == 'single':
    for vds in VDS_single_list:
        config['VDS_num'] = vds
        # ensure dir exists in config
        if 'dir' not in config:
            config['dir'] = '5min'
        div, seg, peaks = run_single_vds(config, base_path, vds, raw_timeframe, c_lane_num)

        # Save per-VDS outputs
        set_peak_period_save(config, peaks, working_f)
        c_daily_traffic_save(config, div, working_f, "division")
        c_daily_traffic_save(config, seg, working_f, "segment")

# Multi-VDS mode
elif config['spatial_scope'] == 'multi_vds':
    div, seg, peaks = run_multi_vds(config, raw_timeframe, c_lane_num)
    
    set_peak_period_save(config, peaks, working_f)
    c_daily_traffic_save(config, div, working_f, "division")
    c_daily_traffic_save(config, seg, working_f, "segment")
# -


# ### (Code) Different Congest_method merge

# +
from pathlib import Path
import pandas as pd
from functools import reduce

def merge_period_columns_wide(folder, prefix_before_v, ext=".csv",
                              join_keys=None, strict=False):
    """
    Column-wise merge of files like:
      <prefix_before_v>v_speed-duration-only<ext>
      <prefix_before_v>v_speedgap-neighbor<ext>
      <prefix_before_v>v_occ<ext>
      <prefix_before_v>v_occ-solely<ext>

    Keeps shared keys once; adds one column per method: period_<method>.

    Args:
      folder: directory path
      prefix_before_v: shared filename prefix up to "..._RDP_"
      ext: file extension (".csv" or ".parquet")
      join_keys: list of stable keys; if None, defaults below
      strict: if True, verifies that all non-`period` columns match exactly
              across files (useful if you expect identical metrics)
    """
    folder = Path(folder)
    files = sorted(folder.glob(f"{prefix_before_v}v_*{ext}"))
    if not files:
        raise FileNotFoundError(f"No files match {folder}/{prefix_before_v}v_*{ext}")

    # Reader depending on type
    def _read(fp):
        if ext == ".csv":
            return pd.read_csv(fp, sep=None, engine="python")
        elif ext == ".parquet":
            return pd.read_parquet(fp)
        else:
            raise ValueError("Unsupported ext; use .csv or .parquet")

    # Load first to infer keys if needed
    first = _read(files[0])
    if join_keys is None:
        # Use stable identifiers only; avoid float metrics as keys.
        # Adjust as needed for your dataset.
        candidate_keys = ["date", "division", "start_time", "end_time", "duration", "year", "dayofweek", "totaldemand", "avg_flow", "traveltimes", "avg_speed", "density", "avg_occ"]
        join_keys = [k for k in candidate_keys if k in first.columns]
        if not join_keys:
            # fallback: everything except 'period'
            join_keys = [c for c in first.columns if c != "period"]

    # Build per-method skinny frames: keys + renamed period
    skinny = []
    base_nonperiod = None

    for fp in files:
        method = fp.stem.split("v_", 1)[-1]  # e.g., "speedgap-neighbor"
        print(method)
        df = _read(fp)

        # Optional consistency check (non-`period` cols)
        if strict:
            cols_to_check = [c for c in df.columns if c != "period"]
            if base_nonperiod is None:
                base_nonperiod = df[cols_to_check].copy()
            else:
                # Align by join_keys for a fair comparison
                merged_chk = pd.merge(base_nonperiod, df[cols_to_check], on=join_keys, how="outer", indicator=True)
                if (merged_chk["_merge"] != "both").any():
                    raise ValueError(f"Row mismatch vs base in {fp.name}. Check join_keys or data.")

        # Keep only keys + period, rename period with method suffix
        keep = join_keys + ["period"]
        missing = set(keep) - set(df.columns)
        if missing:
            raise ValueError(f"{fp.name} missing columns: {missing}")

        slim = df[keep].drop_duplicates(join_keys, keep="last")
        slim = slim.rename(columns={"period": f"period_{method}"})
        skinny.append(slim)

    # Outer-merge all skinny frames on the keys
    merged = reduce(lambda L, R: pd.merge(L, R, on=join_keys, how="outer"), skinny)

    # Optional: order columns (keys first, then period_* columns)
    period_cols = [c for c in merged.columns if c.startswith("period_")]
    merged = merged[join_keys + period_cols]

    return merged

# --- Example ---


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

# + [markdown] editable=true slideshow={"slide_type": ""}
# # BPR calibration result
# -

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
method = 'RDP_v'
version= '_filtered'  # "" "_filtered"
temporal_scale = 'speedbasedpeak'

VDS_list = ['1203481','1203506','1214006','1205583','1205572','1212611','1205541']

for VDS_num in VDS_list:    
    
    if spatial_scope == 'single':
        file_path = f"./01_BPR/c_daily_traffic_segment_{spatial_scope}_{VDS_num}_{temporal_scale}_5_RDP_v_speed-solely.csv"
    
    # Step 1: data read
    c_daily_traffic = pd.read_csv(file_path)
    
    # Step 1-2: filtering
    c_dt_filter = c_daily_traffic[c_daily_traffic['period'] == 'uc'].copy()
    
    c_dt_filter['avg_density'] = c_dt_filter['avg_flow'] /  (1/c_dt_filter['traveltimes'] * 60)
    
    weighted_avg_flow = (c_dt_filter['avg_flow'] * c_dt_filter['duration']).sum() / c_dt_filter['duration'].sum()
    weighted_avg_density = (c_dt_filter['avg_density'] * c_dt_filter['duration']).sum() / c_dt_filter['duration'].sum()
    
    Edie_free_tt = weighted_avg_flow / weighted_avg_density
    
    print("VDS:",VDS_num, Edie_free_tt)

# +
c_daily_traffic['avg_density'] = c_daily_traffic['avg_flow'] /  (1/c_daily_traffic['traveltimes'] * 60)

weighted_avg_flow = (c_daily_traffic['avg_flow'] * c_daily_traffic['duration']).sum() / c_daily_traffic['duration'].sum()
weighted_avg_density = (c_daily_traffic['avg_density'] * c_daily_traffic['duration']).sum() / c_daily_traffic['duration'].sum()



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

# ## (Code) FD for speed_threshold

# <div class="alert alert-info">
#
# We automatically infer the structure of the fundamental diagram (FD) from segment-level data by scanning for a capacity. 
# First, we bin occupancy by rounding each segment’s average occupancy to a chosen precision (2 decimal point), and compute the median flow within each occupancy bin to suppress outliers and capture the representative trend. Next, we identify the capacity as the bin corresponding to the maximum median flow. Around this peak, we form a plateau band consisting of all bins whose median flow remains within a tolerance 
# of the capacity value, i.e., 
#
# $$
# q \geq q_{\text{cap}} \cdot (1 - \text{plateau\_tol}),
# $$
#
# where $q_{\text{cap}}$ denotes the capacity flow. 
# The leftmost and rightmost bins within this plateau band define the corresponding occupancy span 
# $[o_{\ell},\,o_{h}]$.
#
# We then determine the FD phase type based on the width of the plateau. 
# If the plateau width $(o_{h} - o_{\ell})$ exceeds a minimum threshold ($o_{threshold}=0.5$), the site is classified as exhibiting a three-phase structure. In this case, the band edges are assigned as phase boundaries:
# $o_{\text{low}} = o_{\ell}, \qquad o_{\text{high}} = o_{h}.$
#
# Otherwise, when the plateau region is narrow and the capacity occurs at a distinct peak, the FD is regarded as two-phase, with the critical occupancy
# $o_c$ defined as the occupancy at capacity.  
#
#
# In summary, the process can be described as:
#
# $$
# \text{Bin occupancy} 
# \;\rightarrow\;
# \text{Compute median flow per bin}
# \;\rightarrow\;
# \text{Find capacity and tolerance band}
# \;\rightarrow\;
# \begin{cases}
# \text{Three-phase, } [o_{\text{low}}, o_{\text{high}}], & \text{if plateau wide}, \\
# \text{Two-phase, } o_c, & \text{if plateau narrow.}
# \end{cases}
# $$
#
# This method enables automatic and reproducible detection of FD boundaries, providing the empirical thresholds $(o_{\text{low}}, o_{\text{high}}, o_c$) that are subsequently used in the occupancy-based traffic-state classification.

# + editable=true slideshow={"slide_type": ""}
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

def plot_linear_by_group_FD(
    df_segment,
    df_division,              # kept for compatibility (not used)
    variable: str,
    cfg: dict,
    version_key: str,
    speed_thre: float,
    xlim=None,
    ylim=None,
    title_suffix: str = "",
    save_name=None,
):
    # ----------------------------
    # 1) Transform
    # ----------------------------
    if variable == "qk":
        X = df_segment['density']
        Y = df_segment['avg_flow']
        Z = X/Y*60
        # Z.to_csv(f"{save_name}_{variable}.csv")
        
    elif variable == "uq":
        X = df_segment['avg_flow']
        Y = df_segment['traveltimes']
        Z = 1/Y*X*60
        # Z.to_csv(f"{save_name}_{variable}.csv")
        
    # ----------------------------
    # 2) Figure setup (beautified)
    # ----------------------------
    plt.rcParams.update({
        "font.family": "STIXGeneral",
        "mathtext.fontset": "stix",
        "axes.unicode_minus": False,
    })
    
    fig, ax = plt.subplots(figsize=(8.4, 5.6), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Scatter: smaller, softer, cleaner
    ax.scatter(
        X, Y,
        s=14,                 # a bit smaller
        alpha=0.18,           # softer cloud
        linewidths=0,
        rasterized=True
    )

    # ----------------------------
    # 3) Reference line q = v k
    # ----------------------------
    if variable == "qk":  
        if xlim is not None:
            xmin, xmax = xlim
        else:
            xmin = max(0, float(np.nanmin(X)))
            xmax = float(np.nanmax(X)) * 1.05
    
        xs = np.linspace(xmin, xmax, 300)
        ax.plot(
            xs, speed_thre * xs,
            linestyle="--",
            linewidth=2.6,        # slightly thicker
            color="black",
            label=rf"$q = {speed_thre}k$"
        )
    
        # Legend: slightly rounded, nicer spacing
        leg = ax.legend(
            loc="upper right",
            fontsize=25,
            frameon=True,
            fancybox=True,
            borderpad=0.6,
            handlelength=2.2
        )
        leg.get_frame().set_alpha(0.95)

    # ----------------------------
    # 4) Labels, limits, title
    # ----------------------------
    # ax.set_xlabel(xlab, fontsize=25, labelpad=10)
    # ax.set_ylabel(ylab, fontsize=25, labelpad=10)

    if xlim is not None:
        ax.set_xlim(*xlim)
    if ylim is not None:
        ax.set_ylim(*ylim)

    if cfg.get("spatial_scope") == "single":
        ttl = f"VDS {cfg.get('VDS_label', '')}"
    else:
        ttl = "Multiple VDS"
    if title_suffix:
        ttl += f" {title_suffix}"

    ax.set_title(ttl, fontsize=30, pad=14)

    # ----------------------------
    # 5) Ticks + grid (more “publication”)
    # ----------------------------
    ax.tick_params(axis="both", which="major", labelsize=18, length=6, width=1.2)
    ax.tick_params(axis="both", which="minor", length=3, width=1.0)

    ax.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator(5))

    # Softer grid: minor very light, major light
    ax.grid(True, which="major", alpha=0.22, linewidth=1.0)
    ax.grid(True, which="minor", alpha=0.10, linewidth=0.8)

    # Clean spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.2)
    ax.spines["bottom"].set_linewidth(1.2)



    # ----------------------------
    # 6) Save (PNG + PDF)
    # ----------------------------
    if save_name is None:
        os.makedirs(cfg["save_dir"], exist_ok=True)
        save_name = (
            f"{cfg['save_dir']}/FD_clean_{cfg['spatial_scope']}_"
            f"{cfg.get('VDS_num','multi')}_{variable}_"
            f"{cfg['temporal_scale']}_{cfg['period_filter']}_"
            f"{version_key}_{cfg['method']}"
        )

    fig.savefig(save_name + ".png", bbox_inches="tight")  # best for papers
    plt.close(fig)

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
CONFIG_FD = {
    "spatial_scope" : "single" ,      # "multi_vds", "single"
    "VDS_list": ['1203481','1203506','1214006','1205583','1205572','1212611','1205541'],
    "VDS_label_list": ['SR-91 WB','SR-91 EB','I-5 SB-1','I-5 SB-2','I-5 SB-3','I-5 SB-4','I-5 SB-5'],
    # stations = [1203506,1203589,1203615]
    "VDS_num": '1203481',                # 1203506, 1205583, 1214006, ...1203524, 1203481
    "temporal_scale": 'speedbasedpeak',    # used in file name "speedbasedpeak", "entireday" "hour"
    "period_filter": "",  # "morning", "afternoon", ""(entire day)
    "method": "RDP_v",
    # "temporal_scope": "entireday",          # "entireday" or "peak"
    "aggregate_timeframe": 5,              # used in file name (minutes)
    "save_dir": "./01_BPR/02 fig/16 FD",               # where to save figures
    'congest_method':'speed-solely', # speed-duration-only, 'speedgap-neighbor', 'occ', occ-solely
    'file_path': '/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR',
    #need_to_check if the thresholds are equal to other CONFIG whenever use
    'offpeak_ff_speed_threshold': {'1203506': 55, '1203524': 55, '1203481': 55, '1205541': 57, '1212611': 57, '1205572': 57, '1205583': 57, '1214006': 57, 'MULTI_1212611+1205583+1214006': 55,'MULTI_1212611+1205572+1205583+1214006': 55},
}

# Ensure save dir exists
os.makedirs(CONFIG_FD["save_dir"], exist_ok=True)

# +
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.gridspec import GridSpec

def plot_fd_all_in_one_png(
    cfg, variable, version_key, speed_thre, xlim, ylim,
    title_suffix="", out_name="FD_all_in_one"
):
    """
    Uses your existing plot_linear_by_group_FD() without changing its signature.
    Produces one combined PNG with layout:
      Row1: 2 plots (SR91: 1-①, 1-②)
      Row2: 3 plots (2-①, 2-②, 2-③)
      Row3: 2 plots (2-④, 2-⑤)
    """

    # --- 1) generate individual PNGs using your existing pipeline ---
    vds_ids = cfg["VDS_list"]
    vds_labels = cfg["VDS_label_list"]
    assert len(vds_ids) == len(vds_labels), "VDS_list and VDS_label_list must have same length."
    assert len(vds_ids) == 7, "This layout expects exactly 7 stations."

    os.makedirs(cfg["save_dir"], exist_ok=True)

    cfg_i = cfg.copy()
    
    png_paths = []
    for vds_id, vds_lab in zip(vds_ids, vds_labels):
        cfg_i["VDS_num"] = vds_id  # IMPORTANT: keep your file naming logic intact
        cfg_i["VDS_label"] = vds_lab  # IMPORTANT: keep your file naming logic intact

        print(cfg_i["VDS_num"])
        # --- keep your current file naming conventions ---
        fn_segment = (
            f"{cfg_i['file_path']}/c_daily_traffic_segment_{cfg_i['spatial_scope']}_"
            f"{cfg_i['VDS_num']}_{cfg_i['temporal_scale']}_{cfg_i['aggregate_timeframe']}_"
            f"{cfg_i['method']}_{cfg_i['congest_method']}.csv"
        )
        fn_division = (
            f"{cfg_i['file_path']}/c_daily_traffic_division_{cfg_i['spatial_scope']}_"
            f"{cfg_i['VDS_num']}_{cfg_i['temporal_scale']}_{cfg_i['aggregate_timeframe']}_"
            f"{cfg_i['method']}_{cfg_i['congest_method']}.csv"
        )

        df_segment = pd.read_csv(fn_segment)
        df_division = pd.read_csv(fn_division)

        # period filter (same logic you already use)
        if cfg_i.get("period_filter", "") in ["morning", "afternoon"]:
            df_segment["start_time_int"] = pd.to_datetime(df_segment["start_time"]).dt.time
            if cfg_i["period_filter"] == "afternoon":
                df_segment = df_segment[df_segment["start_time_int"] >= pd.to_datetime("12:00").time()]
            else:
                df_segment = df_segment[df_segment["start_time_int"] < pd.to_datetime("12:00").time()]

        # keep your special filter
        if cfg_i.get("spatial_scope") == "single" and str(cfg_i.get("VDS_num")) == "1205541":
            # Create 'month' column by taking the first 4 characters of 'date'
            df_segment['month'] = df_segment['date'].astype(str).str[:4]
            df_segment = df_segment[~df_segment["month"].isin(["2401", "2402", "2403"])]


        # --- force a safe save_name so we can stitch later ---
        save_base = f"{cfg_i['save_dir']}/FD_{vds_lab}_{vds_id}_{variable}"
        plot_linear_by_group_FD(
            df_segment=df_segment,
            df_division=df_division,
            variable=variable,
            cfg=cfg_i,
            version_key=version_key,
            speed_thre=speed_thre[vds_id],
            xlim=xlim,
            ylim=ylim,
            title_suffix=title_suffix,   # keep as you like
            save_name=save_base
        )
        png_paths.append(save_base + ".png")

    # --- 2) stitch them into one PNG ---
    out_png = f"{cfg['save_dir']}/{out_name}_{variable}_{cfg['temporal_scale']}.png"

    fig = plt.figure(figsize=(18, 12), dpi=300)
    gs = GridSpec(3, 3, figure=fig, wspace=0.04, hspace=0.08)

    positions = [
        (0, 0), (0, 1),          # row 1: 2
        (1, 0), (1, 1), (1, 2),  # row 2: 3
        (2, 0), (2, 1)           # row 3: 2
    ]

    for path, (r, c) in zip(png_paths, positions):
        ax = fig.add_subplot(gs[r, c])
        img = mpimg.imread(path)
        ax.imshow(img)
        ax.axis("off")

    # blank panels
    fig.add_subplot(gs[0, 2]).axis("off")
    fig.add_subplot(gs[2, 2]).axis("off")

    if variable == "qk":
        var_title = r"$k-q$"
        xlab = r"$k \,\text{(vpmpl)}$"
        ylab = r"$q \, \text{(vphpl)}$"
    elif variable == "uq":
        var_title = r"$q-z$"
        xlab = r"$q \,\text{(vphpl)}$"
        ylab = r"$z \, \text{(min}/\text{mile)}$"

    
    fig.supxlabel(xlab,fontsize=22,y=0.07)
    fig.supylabel(ylab,fontsize=22,x=0.11)

    if cfg['temporal_scale'] == 'hour':
        sup_title = f"Traffic State Relationship under Hourly Aggregation: {var_title} Relationship"
    elif cfg['temporal_scale'] == 'speedbasedpeak':
        sup_title = f"Traffic State Relationship under Segment-Level Aggregation: {var_title} Relationship"
    
    fig.suptitle(
    sup_title,
    fontsize=24,
    y=0.93)
    
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)

    print("Saved:", out_png)
    return out_png

# -

cfg = CONFIG_FD.copy()
plot_fd_all_in_one_png(
    cfg=cfg,
    variable="qk", #"qk" or "uq"
    version_key="v3",
    speed_thre=cfg['offpeak_ff_speed_threshold'],
    xlim=[0, 100],
    ylim=[0, 2000],
    title_suffix="",
    out_name="FD_SR91_I5_all"
)

# ## (Code) Recurrent Peak period detection

# +
# === Imports ===
import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Callable, Dict, Tuple, Optional
from scipy.optimize import curve_fit
import copy

# === Global style (optional) ===
plt.rcParams.update({"figure.dpi": 140})

# === Configuration ===
CONFIG_RC = {
    # 1. Options to choose for every analysis
    "VDS_list" : ['1203481','1203506','1214006','1205583','1205572','1212611','1205541'],
    "spatial_scope" : "single" ,      # "multi_vds", "single"
    "working_f": "01_BPR",
    "temporal_scale": 'speedbasedpeak',    # used in file name "speedbasedpeak", "entireday", "hour", "peakhour"
    
    # 2. Data filter option
    "period_include": {'speedbasedpeak':['morning-peak', 'afternoon-peak'], 'hour': ['off-peak'], 'entireday': ['off-peak']},
    "drop_days_weird_peak_times": True,
    "drop_multiplecongestion_days" : False,
    "morning_earliest": "03:00",
    "afternoon_latest": "22:00",
    "dayofweek_exclude": [],
    "month_exclude": [],
    "year_exclude": [],
        ## 2.1. freeflow speed setting 
    "free_tt_mode": "fixed",               # "fixed" OR "by_date_offpeak"
    "free_tt_method": "offpeak_avg", # offpeak_avg or FD

    # 3. data read  & save info
    "aggregate_timeframe": 5,              # used in file name (minutes)
    "save_dir": "./01_BPR/02 fig/12 Daily BPR",               # where to save figures
    "method": "RDP_v",
    'file_path': '/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR',
    
    # 4. Regression_info & plot
    "free_tt_offpeak_avg": {'1203481': 60*(1/64), '1203506': 60*(1/(63)), '1214006': 60*(1/(65)),'1205583': 60*(1/(66)),'1205572': 60*(1/(67)), '1212611': 60*(1/(65)),'1205541': 60*(1/(61)),'multi_vds': 60*(1/(64))},   # minutes/mile when mode=="fixed" (60*1/freeflow_speed),
    # "free_tt_offpeak_avg": {'1203481': 60*(1/61), '1203506': 60*(1/(61)), '1214006': 60*(1/(65)),'1205583': 60*(1/(66)),'1205572': 60*(1/(67)), '1212611': 60*(1/(65)),'1205541': 60*(1/(61)),'multi_vds': 60*(1/(64))},   # minutes/mile when mode=="fixed" (60*1/freeflow_speed),
    "VDS_label_list" : {'1203481': 'SR-91 WB','1203506': 'SR-91 EB','1214006': 'I-5 SB-1','1205583':'I-5 SB-2','1205572':'I-5 SB-3','1212611':'I-5 SB-4','1205541':'I-5 SB-5'},
    'free_tt_FD': {'1203506': 60*(1/55), '1203524': 60*(1/55), '1203481': 60*(1/55), '1205541': 60*(1/57), '1212611': 60*(1/57), '1205572': 60*(1/57), '1205583': 60*(1/57), '1214006': 60*(1/57), 'multi_vds': 60*(1/57)},

    "label_criterion": "period",           # "period", "dayofweek", "year", ...
    "W_minutes": 90,                      # heart-of-peak window for V5/V6 if needed
    "capacity_fixed": 1800*24,                # for V5/V6 where capacity is fixed
    "congest_method":'speed-solely', # speed-duration-only, 'speedgap-neighbor', 'occ', occ-solely,
    
    "occ_threshold": {       
        '1203506': {'occ_l': 0.12, 'occ_h': 0.31}, '1205541': {'occ_l': 0.09, 'occ_h': 0.15}, '1212611': {'occ_l': 0.11, 'occ_h': 0.24}, '1205572': {'occ_l': 0.09, 'occ_h': 0.22}},   # appears once only '1205583': {'occ_l': 0.095, 'occ_h': 0.14}, '1214006': {'occ_l': 0.07, 'occ_h': 0.29}},
    'FD_phase': {'1203506': 'three_phases', '1205541': 'three_phases', '1212611': 'three_phases', '1205572': 'three_phases', '1205583': 'three_phases', '1214006': 'three_phases', 'multi_vds' : 'three_phases'}
    }

# Ensure save dir exists
os.makedirs(CONFIG_BPR["save_dir"], exist_ok=True)

# +
# import pandas as pd
# import numpy as np
# import ruptures as rpt
# import matplotlib.pyplot as plt
# import seaborn as sns
# import matplotlib.ticker as ticker
# import copy

# # ------------------------------------------------------------
# # Helper
# # ------------------------------------------------------------
# def time_to_fractional_hour(t_str, default_val=np.nan):
#     if pd.isna(t_str) or t_str == '-':
#         return default_val
#     try:
#         h, m = map(int, str(t_str).split(':'))
#         return h + m / 60.0
#     except Exception:
#         return default_val


# # ------------------------------------------------------------
# # Build the exact PELT input table for one facet
# # ------------------------------------------------------------
# def build_pelt_input(sub_df):
#     """
#     sub_df must already be filtered to one facet:
#     one dayofweek + one period
#     """

#     sub_df = sub_df.sort_values("week_num").copy()

#     # Manual file uses 1 for peak, -5 for non-peak
#     sub_df["is_peak"] = np.where(sub_df["start_hour"].isna(), -5, 1)

#     # Fill plotting values within the facet only
#     sub_df["start_plot"] = sub_df["start_hour"].ffill().bfill()
#     sub_df["end_plot"]   = sub_df["end_hour"].ffill().bfill()

#     # Keep only exact columns used in manual check
#     return sub_df[["week_num", "is_peak", "start_plot", "end_plot"]].copy()


# # ------------------------------------------------------------
# # Detect changepoints
# # ------------------------------------------------------------
# def detect_multivariate_changepoints(sub_df, pen=20, min_size=1, return_input=False):
#     """
#     sub_df: one facet only (same dayofweek + same period)
#     """

#     pelt_df = build_pelt_input(sub_df)

#     if len(pelt_df) < 10:
#         if return_input:
#             return [], pelt_df
#         return []

#     # Use the exact same variables as the manual input
#     signal = pelt_df[["is_peak", "start_plot", "end_plot"]].to_numpy()

#     algo = rpt.Pelt(model="l2", min_size=min_size).fit(signal)
#     cp_indices = algo.predict(pen=pen)

#     # Remove the final endpoint because ruptures always includes n
#     cp_indices = [i for i in cp_indices if i < len(pelt_df)]

#     # Convert index -> week number
#     cp_weeks = pelt_df.iloc[np.array(cp_indices) - 1]["week_num"].tolist()

#     if return_input:
#         return cp_weeks, pelt_df

#     return cp_weeks


# # ------------------------------------------------------------
# # Optional: compare automatic PELT input with manual table
# # ------------------------------------------------------------
# def compare_with_manual(auto_df, manual_df, tol=1e-8):
#     """
#     manual_df must contain:
#     is_peak, start_plot, end_plot
#     """

#     cols = ["is_peak", "start_plot", "end_plot"]

#     if len(auto_df) != len(manual_df):
#         print(f"Length mismatch: auto={len(auto_df)}, manual={len(manual_df)}")
#         return False

#     ok = True
#     for c in cols:
#         if c == "is_peak":
#             same = (auto_df[c].to_numpy() == manual_df[c].to_numpy()).all()
#         else:
#             same = np.allclose(auto_df[c].to_numpy(), manual_df[c].to_numpy(), atol=tol, equal_nan=True)

#         print(f"{c}: {'MATCH' if same else 'DIFFERENT'}")
#         if not same:
#             ok = False

#     if not ok:
#         diff = pd.concat(
#             [
#                 auto_df[cols].reset_index(drop=True).add_prefix("auto_"),
#                 manual_df[cols].reset_index(drop=True).add_prefix("manual_"),
#             ],
#             axis=1
#         )
        

#     return ok


# # ------------------------------------------------------------
# # Main loop
# # ------------------------------------------------------------
# for vds_id in cfg_master['VDS_list']:
#     cfg = copy.deepcopy(cfg_master)
#     cfg["VDS_num"] = vds_id
#     path = build_file_path(cfg)
#     df_raw = pd.read_csv(path)

#     # 1. Pre-processing
#     df_raw['date_dt'] = pd.to_datetime(df_raw['date'], format='%y%m%d')
#     df_raw['dayofweek'] = df_raw['date_dt'].dt.strftime('%a')
#     min_date = df_raw['date_dt'].min()
#     df_raw['week_num'] = ((df_raw['date_dt'] - min_date).dt.days // 7) + 1

#     # 2. Numeric hours
#     df_raw['start_hour'] = df_raw['start_time'].apply(time_to_fractional_hour)
#     df_raw['end_hour'] = df_raw['end_time'].apply(time_to_fractional_hour)

#     # 3. Template
#     all_dates = np.sort(df_raw['date_dt'].unique())
#     all_periods = ['morning-peak', 'afternoon-peak']
#     template = pd.MultiIndex.from_product(
#         [all_dates, all_periods],
#         names=['date_dt', 'period']
#     ).to_frame(index=False)

#     df_peaks = pd.merge(template, df_raw, on=['date_dt', 'period'], how='left')
#     df_peaks['dayofweek'] = df_peaks['date_dt'].dt.strftime('%a')
#     df_peaks['week_num'] = ((df_peaks['date_dt'] - min_date).dt.days // 7) + 1

#     # sort once
#     df_peaks = df_peaks.sort_values(['dayofweek', 'period', 'week_num']).copy()

#     # Build columns globally too, for plotting
#     df_peaks['is_peak'] = np.where(df_peaks['start_hour'].isna(), -5, 1)
#     df_peaks['start_plot'] = (
#         df_peaks.groupby(['dayofweek', 'period'])['start_hour']
#         .transform(lambda x: x)
#     )
#     df_peaks['end_plot'] = (
#         df_peaks.groupby(['dayofweek', 'period'])['end_hour']
#         .transform(lambda x: x)
#     )

#     # --------------------------------------------------------
#     # Visualization
#     # --------------------------------------------------------
#     day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

#     g = sns.FacetGrid(
#         df_peaks,
#         row='dayofweek',
#         col='period',
#         row_order=day_order,
#         col_order=['morning-peak', 'afternoon-peak'],
#         height=3,
#         aspect=2.5,
#         sharex=True,
#         sharey=False
#     )

#     g.map_dataframe(
#         sns.lineplot,
#         x='week_num',
#         y='start_plot',
#         errorbar=None,
#         color='blue',
#         alpha=0.3
#     )
#     g.map_dataframe(
#         sns.lineplot,
#         x='week_num',
#         y='end_plot',
#         errorbar=None,
#         color='red',
#         alpha=0.3
#     )

#     for (row_val, col_val), ax in g.axes_dict.items():
#         facet_data = df_peaks[
#             (df_peaks['dayofweek'] == row_val) &
#             (df_peaks['period'] == col_val)
#         ].sort_values('week_num').copy()

#         cp_weeks, pelt_input = detect_multivariate_changepoints(
#             facet_data,
#             pen=20,
#             min_size=1,
#             return_input=True
#         )

#         # print / save the exact PELT input table for checking
#         print(f"\nVDS={vds_id}, day={row_val}, period={col_val}")
#         # print(pelt_input[["is_peak", "start_plot", "end_plot"]].to_string(index=False))

#         # optional save
#         # pelt_input[["is_peak", "start_plot", "end_plot"]].to_csv(
#         #     f"check_input_{vds_id}_{row_val}_{col_val}.csv", index=False
#         # )

#         for cp_week in cp_weeks:
#             ax.axvline(x=cp_week, color='black', linestyle=':', linewidth=2, alpha=0.8)

#         real_peak = facet_data[facet_data['is_peak'] == 1]
#         non_peak = facet_data[facet_data['is_peak'] == -5]

#         ax.scatter(real_peak['week_num'], real_peak['start_hour'], s=30, color='blue', zorder=4)
#         ax.scatter(real_peak['week_num'], real_peak['end_hour'], s=30, color='red', zorder=4)

#         baseline = 0 if col_val == 'morning-peak' else 12
#         ax.scatter(non_peak['week_num'], [baseline] * len(non_peak), color='grey', marker='x', s=40, alpha=0.6)

#         if col_val == 'morning-peak':
#             ax.set_ylim(-1, 12)
#         else:
#             ax.set_ylim(11, 24)

#         ax.yaxis.set_major_locator(ticker.MultipleLocator(3))

#     g.fig.suptitle(f"3D PELT Detection (VDS: {vds_id})", fontsize=16)
#     plt.subplots_adjust(top=0.9, hspace=0.4)
#     plt.show()

# +
import pandas as pd
import numpy as np
import ruptures as rpt
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
import copy

# --- Part 1: Improved Detection Function ---
def detect_multivariate_changepoints(sub_df):
    """
    Returns the raw indices of the segment boundaries.
    """
    if len(sub_df) < 10:
        return []
    
    # We use 'start_plot', 'end_plot' and 'is_peak' (1 or -5)
    signal = sub_df[['start_plot', 'end_plot', 'is_peak']].values

    try:
        # min_size=1 allows the algorithm to catch single-week peaks/outliers
        algo = rpt.Pelt(model="l2", min_size=1, jump=1).fit(signal)
        # pen=20 is a robust threshold for 3D signal jumps
        cp_indices = algo.predict(pen=20)
        return cp_indices
    except:
        return []

# Helper function to convert "HH:MM" to fractional hours
def time_to_fractional_hour(t_str, default_val):
    if pd.isna(t_str) or t_str == '-': 
        return default_val
    try:
        h, m = map(int, str(t_str).split(':'))
        return h + m/60.0
    except: 
        return default_val

# --- Part 2: Main Processing Loop ---
all_recurrent_peaks = []
all_excluded_peaks = []

# Use your existing VDS list from your config
for vds_id in cfg_master['VDS_list']:
    cfg = copy.deepcopy(cfg_master)
    cfg["VDS_num"] = vds_id
    path = build_file_path(cfg)
    df_raw = pd.read_csv(path)
    
    # 1. Pre-processing raw data
    df_raw['date_dt'] = pd.to_datetime(df_raw['date'], format='%y%m%d')
    df_raw['dayofweek'] = df_raw['date_dt'].dt.strftime('%a')
    min_date = df_raw['date_dt'].min()
    df_raw['week_num'] = ((df_raw['date_dt'] - min_date).dt.days // 7) + 1
    
    # 2. Calculate Numeric Hours
    df_raw['start_hour'] = df_raw['start_time'].apply(lambda x: time_to_fractional_hour(x, np.nan))
    df_raw['end_hour'] = df_raw['end_time'].apply(lambda x: time_to_fractional_hour(x, np.nan))
    
    # 3. Create Template and Merge (ensures all weeks are represented)
    all_dates = df_raw['date_dt'].unique()
    all_periods = ['morning-peak', 'afternoon-peak']
    template = pd.MultiIndex.from_product([all_dates, all_periods], names=['date_dt', 'period']).to_frame(index=False)
    
    df_peaks = pd.merge(template, df_raw, on=['date_dt', 'period'], how='left')
    df_peaks['dayofweek'] = df_peaks['date_dt'].dt.strftime('%a')
    # Duplicate (date_dt, period) keys if df_raw has multiple peaks: keep the row whose
    # start_hour is closest to the median peak start for that day-of-week and period.
    _med = df_raw.groupby(['dayofweek', 'period'])['start_hour'].median()
    _idx = pd.MultiIndex.from_arrays([df_peaks['dayofweek'], df_peaks['period']])
    df_peaks['_dist'] = (df_peaks['start_hour'] - _med.reindex(_idx).values).abs()
    df_peaks = (
        df_peaks.sort_values('_dist', na_position='last')
        .drop_duplicates(subset=['date_dt', 'period'], keep='first')
        .drop(columns=['_dist'])
    )
    df_peaks['week_num'] = ((df_peaks['date_dt'] - min_date).dt.days // 7) + 1
    df_peaks['vds_id'] = vds_id

    # 4. Create the 3rd Dimension (is_peak) and Plotting columns
    df_peaks['is_peak'] = 1
    non_peak_mask = df_peaks['start_hour'].isna()
    df_peaks.loc[non_peak_mask, 'is_peak'] = -5
    
    df_peaks['start_plot'] = df_peaks['start_hour'].copy()
    df_peaks['end_plot'] = df_peaks['end_hour'].copy()

    # Set non-peak baselines (0 for morning, 12 for afternoon)
    df_peaks.loc[non_peak_mask & (df_peaks['period'] == 'morning-peak'), ['start_plot', 'end_plot']] = 0.0
    df_peaks.loc[non_peak_mask & (df_peaks['period'] == 'afternoon-peak'), ['start_plot', 'end_plot']] = 12.0

    # --- Part 3: Visualization & Segmentation Logic ---
    length_threshold = 4  # Minimum segment length (weeks)
    
    day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    g = sns.FacetGrid(
        df_peaks, row='dayofweek', col='period', 
        row_order=day_order, col_order=['morning-peak', 'afternoon-peak'],
        height=3, aspect=2.5, sharey=False, sharex=True
    )

    # Plot the lines (they will "dip" to the baseline now)
    g.map(sns.lineplot, 'week_num', 'start_plot', color='blue', alpha=0.3, errorbar=None, estimator=None)
    g.map(sns.lineplot, 'week_num', 'end_plot', color='red', alpha=0.3, errorbar=None, estimator=None)

    for (row_val, col_val), ax in g.axes_dict.items():
        facet_data = df_peaks[(df_peaks['dayofweek'] == row_val) & 
                              (df_peaks['period'] == col_val)].sort_values('week_num').copy()
        
        # 1. Detect Changepoint Indices
        cp_indices = detect_multivariate_changepoints(facet_data)
        
        # 2. Slice segments and identify Outliers
        start_idx = 0
        for end_idx in cp_indices:
            segment = facet_data.iloc[start_idx:end_idx]
            
            # Calculate Segment Duration (Length)
            segment_length = len(segment)
            
            # Recurrence logic: Is this segment long enough AND dense enough?
            # A segment is "Recurrent" ONLY if it lasts at least 3 weeks
            # AND it isn't a "Non-Peak" block (recurrence_rate > 0.5)
            recurrence_rate = (segment['is_peak'] == 1).mean()
            
            is_valid_regime = (segment_length >= length_threshold) and (recurrence_rate > 0.5)
            
            # Extract actual peak instances
            seg_peaks = segment[segment['is_peak'] == 1].copy()
            
            if is_valid_regime:
                all_recurrent_peaks.append(seg_peaks)
            else:
                # If segment is too short OR is mostly empty, exclude its peaks
                all_excluded_peaks.append(seg_peaks)
            
            # Draw vertical lines for visualization
            if end_idx < len(facet_data):
                cp_week = facet_data.iloc[end_idx-1]['week_num']
                ax.axvline(x=cp_week, color='black', linestyle=':', linewidth=2, alpha=0.8)
            
            start_idx = end_idx

        # Overlay scatter points
        real_peak = facet_data[facet_data['is_peak'] == 1]
        non_peak = facet_data[facet_data['is_peak'] == -5]
        
        ax.scatter(real_peak['week_num'], real_peak['start_hour'], color='blue', s=30, zorder=4)
        ax.scatter(real_peak['week_num'], real_peak['end_hour'], color='red', s=30, zorder=4)

        # Baseline markers
        base = 0 if col_val == 'morning-peak' else 12
        ax.scatter(non_peak['week_num'], [base]*len(non_peak), color='grey', marker='x', s=40, alpha=0.4)

        # Axis Formatting
        ax.set_ylim(-1, 12) if col_val == 'morning-peak' else ax.set_ylim(11, 24)
        ax.yaxis.set_major_locator(ticker.MultipleLocator(3))

    g.fig.suptitle(f"PELT Segmentation & Outlier Extraction (VDS: {vds_id})", fontsize=16)
    plt.subplots_adjust(top=0.9, hspace=0.4)
    plt.show()

# --- Part 4: Final Export ---
if all_excluded_peaks:
    df_excluded = pd.concat(all_excluded_peaks)
    df_excluded[['vds_id', 'date_dt', 'dayofweek', 'period', 'start_hour', 'end_hour']].to_csv("excluded_non_recurrent_peaks_PELT.csv", index=False)
    print(f"Exported {len(df_excluded)} outlier instances.")

# +
from sklearn.cluster import MeanShift, estimate_bandwidth

def identify_top_80_percent_peaks(df, day, period, bandwidth, ind_threshold):
    """
    Identifies major peak regimes using Mean Shift clustering. 
    Includes missing dates as defaults (0 or 12).
    Selects enough clusters to cover at least 80% of total possible days.
    """
    
    sub = df[(df['dayofweek'] == day) & (df['period'] == period)]
    
    sub['start_hour'] = pd.to_numeric(sub['start_hour'], errors='coerce')
    sub['end_hour'] = pd.to_numeric(sub['end_hour'], errors='coerce')
    
    # Ensure missing dates are treated as 0:00 (AM) or 12:00 (PM)
    if period == 'morning-peak':
        sub['start_hour'] = sub['start_hour'].fillna(0.0)
        sub['end_hour'] = sub['end_hour'].fillna(0.0)
    else:
        sub['start_hour'] = sub['start_hour'].fillna(12.0)
        sub['end_hour'] = sub['end_hour'].fillna(12.0)

    total_datapoints = len(sub)
    
    if total_datapoints < 3:
        sub['is_significant'] = False
        sub['cluster'] = -1
        return sub, []

    # Clustering on [start, end] coordinates
    X = sub[['start_hour', 'end_hour']].values
    

    # 2. Apply Mean Shift
    # bin_seeding=True speeds up the algorithm for large datasets
    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
    ms.fit(X)
    
    sub['cluster'] = ms.labels_

    # 3. Analyze Clusters
    cluster_counts = sub['cluster'].value_counts().sort_values(ascending=False)
    
    # Mean Shift doesn't usually produce noise (-1), but we keep the logic compatible
    real_clusters = cluster_counts.drop(-1, errors='ignore')
    
    if real_clusters.empty:
        sub['is_significant'] = False
        return sub, []

    # Selection Logic: Accumulate clusters until we hit 80% of the ENTIRE plot
    significant_clusters = []
    current_sum = 0
    
    for cid, count in real_clusters.items():
        # Keep cluster if it meets individual size threshold
        if count < ind_threshold*total_datapoints:
            break
        significant_clusters.append(cid)
        current_sum += count
        # Stop once we've covered 80% of data
        # if current_sum >= sum_threshold:
        #     break
            
    sub['is_significant'] = sub['cluster'].isin(significant_clusters)
    
    # Calculate Cluster Centers (Centroids)
    summaries = []
    cluster_centers = ms.cluster_centers_
    
    for cid in significant_clusters:
        # Instead of calculating the mean of points manually, 
        # Mean Shift provides the exact final centroid (converged center)
        summaries.append({
            'cluster_id': cid,
            'start': cluster_centers[cid][0],
            'end': cluster_centers[cid][1],
            'share': real_clusters[cid] / total_datapoints 
        })

    return sub, summaries


# -

def process_and_visualize_recurrent_peaks(df_peaks, vds_id, day_order, save_dir:str, 
                                         show_temporal, show_cluster_space):
    """
    Modular function to identify recurrent peaks and visualize them.
    Allows independent activation of Temporal and Cluster Space plots.
    """
    all_outliers_vds = []
    # Define this before your loop
    day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    periods = ['morning-peak', 'afternoon-peak']

    # 1. Initialize Figures if needed
    g = None
    fig_clust = None
    axes_clust = None

    if show_temporal:
        g = sns.FacetGrid(
            df_peaks, row='dayofweek', col='period', 
            row_order=day_order, col_order=periods,
            height=4, aspect=1, sharey=False, sharex=True
        )

    if show_cluster_space:
        fig_clust, axes_clust = plt.subplots(
            nrows=len(day_order), ncols=2, 
            figsize=(12, 4 * len(day_order)), 
            constrained_layout=True
        )

    # 2. Iterate through Categories directly (not through the Grid)
    for d_idx, row_val in enumerate(day_order):
        for p_idx, col_val in enumerate(periods):
            
            # --- Execution Logic (Always Run) ---
            df_res, top_summaries = identify_top_80_percent_peaks(df_peaks, row_val, col_val, bandwidth=0.8,ind_threshold=0.05)
            
            outliers = df_res[df_res['is_significant'] == False].copy()
            outliers['vds_id'] = vds_id
            all_outliers_vds.append(outliers)

            # --- Plot 1: Temporal (Week vs Hour) ---
            if show_temporal and g is not None:
                ax_temp = g.axes_dict[(row_val, col_val)]
                
                # Scatter Significant & Insignificant
                for data, color, size, alpha in [
                    (df_res[df_res['is_significant']], None, 50, 1.0),
                    (df_res[~df_res['is_significant']], 'grey', 20, 0.3)
                ]:
                    if not data.empty:
                        sns.scatterplot(data=data, x='week_num', y='start_hour', ax=ax_temp, 
                                        color=color, hue=('cluster' if color is None else None), 
                                        palette='Set1', s=size, alpha=alpha, zorder=3, legend=False)
                        sns.scatterplot(data=data, x='week_num', y='end_hour', ax=ax_temp, 
                                        color=color, hue=('cluster' if color is None else None), 
                                        palette='Set1', s=size, alpha=alpha, zorder=3, legend=False)

                # Draw Bands
                for i, s in enumerate(top_summaries):
                    band_color = plt.cm.Set1(i % 9)
                    ax_temp.axhspan(s['start'], s['end'], color=band_color, alpha=0.15)
                    ax_temp.text(df_peaks['week_num'].max() + 0.5, (s['start'] + s['end'])/2, 
                                f"{s['share']:.0%}", fontsize=9, weight='bold', color=band_color,
                                transform=ax_temp.get_yaxis_transform())

                # Formatting
                ax_temp.set_xlim(0, df_peaks['week_num'].max() + 2)
                curr_lim = (-0.5, 12) if col_val == 'morning-peak' else (11.5, 22)
                ax_temp.set_ylim(curr_lim)
                ax_temp.yaxis.set_major_locator(ticker.MultipleLocator(2))

            # --- Plot 2: Cluster Space (Start vs End) ---
            if show_cluster_space and axes_clust is not None:
                ax_clust = axes_clust[d_idx, p_idx]
                
                # Plot Noise
                noise = df_res[df_res['cluster'] == -1]
                ax_clust.scatter(noise['start_hour'], noise['end_hour'], c='grey', alpha=0.3, s=30)
                
                # Plot Real Clusters
                real_c = df_res[df_res['cluster'] != -1]
                if not real_c.empty:
                    ax_clust.scatter(real_c['start_hour'], real_c['end_hour'], 
                                     c=real_c['cluster'], cmap='Set1', s=40, edgecolors='w')
                
                # Plot Means
                for s in top_summaries:
                    ax_clust.plot(s['start'], s['end'], 'kx', markersize=12, mew=2)

                ax_clust.set_title(f"{row_val} {col_val}")
                curr_lim = (-0.5, 12) if col_val == 'morning-peak' else (11.5, 23)
                ax_clust.set_xlim(curr_lim); ax_clust.set_ylim(curr_lim)
                ax_clust.grid(True, alpha=0.3)

    # 3. Finalize and Save
    if show_temporal and g:
        g.fig.suptitle(f"Recurrent Peaks (Temporal) - VDS: {vds_id}", fontsize=15)
        g.fig.savefig(os.path.join(save_dir, f"Temporal_{vds_id}.png"), dpi=150, bbox_inches='tight')

    if show_cluster_space and fig_clust:
        fig_clust.suptitle(f"Cluster Space (Start vs End) - VDS: {vds_id}", fontsize=15)
        fig_clust.savefig(os.path.join(save_dir, f"ClusterSpace_{vds_id}.png"), dpi=150)

    plt.show()
    plt.close('all')
    
    return all_outliers_vds


# +

# --- Part 2: Main Processing and Visualization ---
all_outliers = []
cfg = copy.deepcopy(CONFIG_RC)
cfg["VDS_num"] = vds_id

for vds_id in cfg['VDS_list']:
    print(vds_id)
    # Assuming df_peaks is already built with all dates/periods filled
    # If not, ensure the preprocessing code used in previous cells is run first
    cfg['VDS_num'] = vds_id
    path = build_file_path(cfg)
    print(path)
    df_analysis = pd.read_csv(path)
    
    # --- Pre-processing ---
    df_analysis['date_dt'] = pd.to_datetime(df_analysis['date'], format='%y%m%d')
    df_analysis['dayofweek'] = df_analysis['date_dt'].dt.strftime('%a')
    
    # --- NEW: Calculate Week Number Labels (1st, 2nd, ...) ---
    min_date = df_analysis['date_dt'].min()
    # Calculate how many weeks from the start (0-indexed then +1)
    df_analysis['week_num'] = ((df_analysis['date_dt'] - min_date).dt.days // 7) + 1
    
    # Function to add ordinal suffixes
    def ordinal(n):
        return f"{n}{'' if 11 <= n % 100 <= 13 else {1: '', 2: '', 3: ''}.get(n % 10, '')}"
    
    df_analysis['week_label'] = df_analysis['week_num'].apply(ordinal)
    
    # Ensure the plot treats week_label as an ordered categorical variable
    unique_labels = [ordinal(i) for i in range(1, df_analysis['week_num'].max() + 1)]
    df_analysis['week_label'] = pd.Categorical(df_analysis['week_label'], categories=unique_labels, ordered=True)

  # 1. Update the function to handle default values for missing data
    def time_to_fractional_hour(t_str, default_val):
        if pd.isna(t_str) or t_str == '-': 
            return default_val
        try:
            h, m = map(int, str(t_str).split(':'))
            return h + m/60.0
        except: 
            return default_val

    # 2. Process existing records
    df_analysis['start_hour'] = df_analysis['start_time'].apply(lambda x: time_to_fractional_hour(x, 0.0))
    df_analysis['end_hour'] = df_analysis['end_time'].apply(lambda x: time_to_fractional_hour(x, 12.0))

    # 3. Create a complete index of all Dates and Peak Periods
    all_dates = df_analysis['date_dt'].unique()
    all_periods = ['morning-peak', 'afternoon-peak']
    
    # Create a template of all possible combinations
    template = pd.MultiIndex.from_product([all_dates, all_periods], names=['date_dt', 'period']).to_frame(index=False)
    
    # Merge existing data into the template
    df_peaks = pd.merge(template, df_analysis, on=['date_dt', 'period'], how='left')
    df_peaks['dayofweek'] = df_peaks['date_dt'].dt.strftime('%a')
    
    # ... inside the vds_id loop ...
    df_peaks['vds_id'] = vds_id  # Add this line to ensure the column exists

    # 2. Call the deployed function
    vds_outliers = process_and_visualize_recurrent_peaks(
        df_peaks, 
        vds_id, 
        day_order, 
        save_dir="./01_BPR/02 fig/recurrent_checks",
        show_temporal=False, show_cluster_space=True)


    for (row_val, col_val), ax in g.axes_dict.items():
        # Get processed results for this facet
        df_res, top_summaries = identify_top_80_percent_peaks(df_peaks[df_peaks['vds_id']==vds_id], row_val, col_val, bandwidth=1.5, ind_threshold=0.1)
        
        # Collect non-recurrent dates for export
        outliers = df_res[df_res['is_significant'] == False].copy()
        outliers['vds_id'] = vds_id
        all_outliers.append(outliers)

# --- Part 3: Export the Outliers and Clean Dataset ---
df_excluded = pd.concat(all_outliers)[['vds_id', 'date_dt', 'dayofweek', 'period', 'start_hour', 'end_hour']]
df_excluded.to_csv("excluded_non_recurrent_peaks_clustering.csv", index=False)

# This creates your final 'recurrent only' dataset for BPR calibration
df_clean_for_bpr = df_peaks.merge(
    df_excluded[['vds_id', 'date_dt', 'period']], 
    on=['vds_id', 'date_dt', 'period'], 
    how='left', 
    indicator=True
).query('_merge == "left_only"').drop(columns=['_merge'])

print(f"Success. Clean dataset created with {len(df_clean_for_bpr)} recurrent peak periods.")
# -

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

# + editable=true slideshow={"slide_type": ""}
from typing import Callable, Tuple, Dict

# === Linear version registry (V1–V4) ===
# Each entry returns (x, y, x_label, y_label) for plotting/fit
# 'Collable' means “a function (or any callable object) that takes arguments of given types and returns the given type.”
LinearTransform = Callable[[pd.DataFrame], Tuple[np.ndarray, np.ndarray, str, str]]
    
def v2_lnN_vs_lnttau():
    return (
        "ln_totaldemand",
        "ln_t_tau",
        r"$\ln(Tq)$",
        r"$\ln\!\left(\frac{z(r)}{\zeta}-1\right)$",
    )

def v3_lnN_vs_lnttau():
    return (
        "ln_totaldemandoverlanes",
        "ln_t_tau",
        r"$\ln(Q)$",
        r"$\ln\!\left(\frac{z(Q)}{\zeta}-1\right)$",
    )

def v4_speeddep_lnN_vs_lnttau(g: pd.DataFrame):
    # identical axes to v3; differs because ζ is date-wise in ln/columns already
    return v2_lnN_vs_lnttau(g)


def v10_lnq_vs_lnttau():
    return (
        "ln_avg_flow",
        "ln_t_tau",
        r"$\ln(q)$",
        r"$\ln\!\left(\frac{z(q)}{\zeta}-1\right)$",
    )

LINEAR_REGISTRY_BPR: Dict[str, LinearTransform] = {
    "v2": v2_lnN_vs_lnttau,
    "v3": v3_lnN_vs_lnttau,
    "v10": v10_lnq_vs_lnttau,
}


# + jupyter={"source_hidden": true}
# === Nonlinear: V5 (fixed capacity & W, fit a,b) ===
def model_bpr_avgdemand(x, a, b, free_tt, c_fixed, W_minutes):
    t0 = free_tt
    W = W_minutes/60.0
    return t0 * (1.0 + a * (x/(c_fixed*W))**b)

def run_v5(df: pd.DataFrame, cfg: dict, xlim: Optional[list] = None, ylim: Optional[list] = None, save_name: Optional[str] = None):
    group_key = cfg["label_criterion"]
    c_fixed = cfg["capacity_fixed"]
    Wm = cfg["W_minutes"]


    if cfg["free_tt_method"] == "FD":
        if cfg['spatial_scope'] == 'single':
            free_tt = cfg['free_tt_FD'][cfg["VDS_num"]]
        elif cfg['spatial_scope'] == 'multi_vds':
            free_tt = cfg['free_tt_FD']['multi_vds']
    elif cfg["free_tt_method"] == "offpeak_avg":
        if cfg['spatial_scope'] == 'single':
            free_tt = cfg['free_tt_offpeak_avg'][cfg["VDS_num"]]
        elif cfg['spatial_scope'] == 'multi_vds':
            free_tt = cfg['free_tt_offpeak_avg']['multi_vds']

    fig, ax = plt.subplots(1, 1, figsize=(8.5, 6))
    legends = []

    for name, grp in df.groupby(group_key):
        x = grp["totaldemandoverlanes"].to_numpy()
        y = grp["traveltimes"].to_numpy()
        
        ax.plot(x, y, marker="o", linestyle="", label=str(name))
    
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
                save_name = f"{cfg['save_dir']}/{cfg['period_include'][cfg['temporal_scale']]}/v5/BPR_calibration_{cfg['spatial_scope']}_{cfg['VDS_list']}_{cfg["temporal_scale"]}_v5_{cfg['method']}_{cfg['free_tt_method']}_{cfg['period_include']}.png"
            else:
                save_name = f"{cfg['save_dir']}/{cfg['period_include'][cfg['temporal_scale']]}/v5/BPR_calibration_{cfg['spatial_scope']}_{cfg['VDS_num']}_{cfg["temporal_scale"]}_v5_{cfg['method']}_{cfg['free_tt_method']}_{cfg['period_include']}.png"
        
        plt.savefig(save_name, bbox_inches="tight")
        plt.close(fig)

# +
# # === Nonlinear: V6 (whole-day weighted ratio) ===
# def compute_v6_wratio_and_avgtt(df: pd.DataFrame, cap: float, beta: float = 4.0) -> Tuple[np.ndarray, np.ndarray]:
#     """
#     For each date, compute:
#       w_tilde = [ sum_i epsilon_i^{beta+1} / w_i^{beta} ]^{-1/beta}
#       w0      = N_total / cap
#       w_ratio = w0 / w_tilde
#     and weighted average travel time.
#     """
#     w_map = {"off-peak": float("inf"), "morning-peak": 1.0, "afternoon-peak": 1.0}
#     wratios, avgtts = [], []

#     for date, grp in df.groupby("date"):
#         periods = grp["period"].tolist()
#         w_i = np.array([w_map.get(p, 1.0) for p in periods], dtype=float)
#         N_i = grp["totaldemand"].to_numpy(dtype=float)
#         eps = N_i / (N_i.sum() if N_i.sum() > 0 else 1.0)
#         # Handle inf weights: eps^(b+1)/w^b -> 0 when w=inf
#         term = np.where(np.isinf(w_i), 0.0, (eps**(beta+1))/(w_i**beta))
#         denom = term.sum()
#         if denom <= 0:
#             continue
#         w_tilde = (1.0/denom)**(1.0/beta)
#         w0 = (N_i.sum()/cap) if cap > 0 else np.nan
#         if np.isnan(w0):
#             continue
#         wratios.append(w0/w_tilde)
#         avgtts.append(np.sum(grp["traveltimes"]*eps))
#     return np.array(wratios, float), np.array(avgtts, float)

# def model_bpr_wratio(w_ratio, a, b):
#     t0 = 60.0/70.0
#     return t0 * (1.0 + a * (w_ratio**b))

# def run_v6(df: pd.DataFrame, cfg: dict, save_name: Optional[str] = None):
#     cap = cfg["capacity_fixed"]
#     w_ratio, avg_tt = compute_v6_wratio_and_avgtt(df, cap=cap, beta=4.0)
#     fig, ax = plt.subplots(1, 1, figsize=(8.0, 6.0))

#     ax.plot(w_ratio, avg_tt, marker="o", linestyle="", label="daily points")
#     f = lambda w, a, b: model_bpr_wratio(w, a, b)
#     popt, _ = curve_fit(f, w_ratio, avg_tt, p0=[1.0, 1.0], maxfev=10000)
#     a_hat, b_hat = popt

#     x_fit = np.linspace(0, max(float(w_ratio.max()), 1.0)# === Nonlinear: V6 (whole-day weighted ratio) ===
#     def compute_v6_wratio_and_avgtt ( df: pd.DataFrame, cap: int, beta: float):
    
#         # w_ratio = v/c
#         # avg_tt  = ( sum(traveltime_i * volume_i) / sum(volume_i) ) / (free_flow_travel_time)
    
#         tdf = df.loc[df["volume"] > 0].copy()
#         if len(tdf) == 0:
#             return np.array([]), np.array([])
        
#         tdf["w_ratio"] = tdf["volume"] / cap
#         tdf["tt_i_vol_i"] = tdf["avg_tt"] * tdf["volume"]
    
#         out = tdf.groupby("w_ratio", as_index=False)[["tt_i_vol_i", "volume"]].sum()
#         out["avg_tt"] = out["tt_i_vol_i"] / out["volume"]
    
#         return out["w_ratio"].to_numpy(), out["avg_tt"].to_numpy()
    
    
#     def model_bpr_wratio(w_ratio, b, a):
#         return (1.0 + a*(w_ratio**b))
    
    
#     def run_v6(df, PdDataFrame, cfg_dict, save_name: Optional[str] = None):
        
#         cap = cfg_dict["capacity_fixed"]
#         w_ratio, avg_tt = compute_v6_wratio_and_avgtt(df, cap=cap, beta=4.0)
    
#         fig, axes = plt.subplots(1, 3, figsize=(24.0, 6.0)) # Modified for 1x3
#         ax = axes[0] # Original plot on the first axis
    
#         ax.plot(w_ratio, avg_tt, marker="o", linestyle="", label="daily points")
        
#         a = lambda w, a, b: model_bpr_wratio(w, a, b)# === Nonlinear: V6 (whole-day weighted ratio) ===
#     def compute_v6_wratio_and_avgtt ( df: pd.DataFrame, cap: int, beta: float):
    
#         # w_ratio = v/c
#         # avg_tt  = ( sum(traveltime_i * volume_i) / sum(volume_i) ) / (free_flow_travel_time)
    
#         tdf = df.loc[df["volume"] > 0].copy()
#         if len(tdf) == 0:
#             return np.array([]), np.array([])
        
#         tdf["w_ratio"] = tdf["volume"] / cap
#         tdf["tt_i_vol_i"] = tdf["avg_tt"] * tdf["volume"]
    
#         out = tdf.groupby("w_ratio", as_index=False)[["tt_i_vol_i", "volume"]].sum()
#         out["avg_tt"] = out["tt_i_vol_i"] / out["volume"]
    
#         return out["w_ratio"].to_numpy(), out["avg_tt"].to_numpy()
    
    
#     def model_bpr_wratio(w_ratio, b, a):
#         return (1.0 + a*(w_ratio**b))
    
    
#     def plot_bpr_single_panel(df, PdDataFrame, cfg_dict, save_name: Optional[str] = None): # Renamed here
        
#         cap = cfg_dict["capacity_fixed"]
#         w_ratio, avg_tt = compute_v6_wratio_and_avgtt(df, cap=cap, beta=4.0)
    
#         fig, axes = plt.subplots(1, 3, figsize=(24.0, 6.0)) # Modified for 1x3
#         ax = axes[0] # Original plot on the first axis
    
#         ax.plot(w_ratio, avg_tt, marker="o", linestyle="", label="daily points")
        
#         a = lambda w, a, b: model_bpr_wratio(w, a, b)
#         popt, _ = curve_fit(f=a, xdata=w_ratio, ydata=avg_tt, p0=[1.0, 4.0], maxfev=10000)
#         a_hat, b = popt
    
#         x_fit = np.linspace(0, max(1.0, w_ratio.max()), 100)
#         y_fit = model_bpr_wratio(x_fit, a=a_hat, b=b)
#         y_pred = model_bpr_wratio(w_ratio, a=a_hat, b=b)
    
#         ax.plot(x_fit, y_fit, linewidth=2, label=f"Fit: a={a_hat:.2f}, b={b:.2f}, R2={r2_score(avg_tt, y_pred):.3f}")
#         ax.set_xlabel(f"V/C ratio (V/{cfg_dict['V/C']})", fontsize=12)
#         ax.set_ylabel("Normalized average travel time (this rule)", fontsize=12)
#         ax.grid(True)
#         ax.set_title(f"BPR calibration result ({cfg_dict['VDS_num']}) ({cfg_dict['spatial_scope']})", fontsize=12)
#         ax.legend()
        
#         # --- Add diagnostic plots ---
#         if "residuals" in cfg_dict and "fittedvalues" in cfg_dict:
#             residuals = cfg_dict["residuals"]
#             fittedvalues = cfg_dict["fittedvalues"]
            
#             # Q-Q plot
#             sm.qqplot(residuals, line='s', ax=axes[1])
#             axes[1].set_title("Q-Q Plot of Residuals")
            
#             # Residuals vs Fitted
#             axes[2].scatter(fittedvalues, residuals)
#             axes[2].axhline(0, color='red', linestyle='--')
#             axes[2].set_xlabel("Fitted Values")
#             axes[2].set_ylabel("Residuals")
#             axes[2].set_title("Residuals vs. Fitted Values")
#         else:
#             axes[1].set_title("Residuals not provided")
#             axes[2].set_title("Fitted values not provided")
    
#         plt.tight_layout() # Adjust layout
#         # --- ---
    
#         if save_name is None:
#             if cfg_dict['spatial_scope'] == "multi_VDS":
#                 save_name = f"{cfg_dict['save_dir']}/{cfg_dict['period_include']}//v6/BPR_calibration_{cfg_dict['spatial_scope']}_{cfg_dict['VDS_num']}.png"
#             else:
#                 save_name = f"{cfg_dict['save_dir']}/{cfg_dict['period_include']}//v6/BPR_calibration_{cfg_dict['spatial_scope']}.png"
        
#         plt.savefig(save_name, bbox_inches="tight")
#         plt.close(fig) # Close the figure to save memory
    
    
#         popt, _ = curve_fit(f=a, xdata=w_ratio, ydata=avg_tt, p0=[1.0, 4.0], maxfev=10000)
#         a_hat, b = popt
    
#         x_fit = np.linspace(0, max(1.0, w_ratio.max()), 100)
#         y_fit = model_bpr_wratio(x_fit, a=a_hat, b=b)
#         y_pred = model_bpr_wratio(w_ratio, a=a_hat, b=b)
    
#         ax.plot(x_fit, y_fit, linewidth=2, label=f"Fit: a={a_hat:.2f}, b={b:.2f}, R2={r2_score(avg_tt, y_pred):.3f}")
#         ax.set_xlabel(f"V/C ratio (V/{cfg_dict['V/C']})", fontsize=12)
#         ax.set_ylabel("Normalized average travel time (this rule)", fontsize=12)
#         ax.grid(True)
#         ax.set_title(f"BPR calibration result ({cfg_dict['VDS_num']}) ({cfg_dict['spatial_scope']})", fontsize=12)
#         ax.legend()
        
#         # --- Add diagnostic plots ---
#         if "residuals" in cfg_dict and "fittedvalues" in cfg_dict:
#             residuals = cfg_dict["residuals"]
#             fittedvalues = cfg_dict["fittedvalues"]
            
#             # Q-Q plot
#             sm.qqplot(residuals, line='s', ax=axes[1])
#             axes[1].set_title("Q-Q Plot of Residuals")
            
#             # Residuals vs Fitted
#             axes[2].scatter(fittedvalues, residuals)
#             axes[2].axhline(0, color='red', linestyle='--')
#             axes[2].set_xlabel("Fitted Values")
#             axes[2].set_ylabel("Residuals")
#             axes[2].set_title("Residuals vs. Fitted Values")
#         else:
#             axes[1].set_title("Residuals not provided")
#             axes[2].set_title("Fitted values not provided")
    
#         plt.tight_layout() # Adjust layout
#         # --- ---
    
#         if save_name is None:
#             if cfg_dict['spatial_scope'] == "multi_VDS":
#                 save_name = f"{cfg_dict['save_dir']}/{cfg_dict['period_include']}//v6/BPR_calibration_{cfg_dict['spatial_scope']}_{cfg_dict['VDS_num']}.png"
#             else:
#                 save_name = f"{cfg_dict['save_dir']}/{cfg_dict['period_include']}//v6/BPR_calibration_{cfg_dict['spatial_scope']}.png"
        
#         plt.savefig(save_name, bbox_inches="tight")
#         plt.close(fig) # Close the figure to save memory
    
#     , 400)
#     y_fit = model_bpr_wratio(x_fit, a_hat, b_hat)
#     y_pred = model_bpr_wratio(w_ratio, a_hat, b_hat)

#     ax.plot(x_fit, y_fit, linewidth=2, label=f"Fit: a={a_hat:.2f}, b={b_hat:.2f}, R²={r2_score(avg_tt, y_pred):.3f}")
#     ax.set_xlabel(r"$N/(lC\tilde{W})$", fontsize=12)
#     ax.set_ylabel("Average travel time (min/mile)", fontsize=12)
#     ax.grid(True)
#     ax.set_title(f"BPR calibration (V6) at VDS {cfg['VDS_num']} [{cfg['method']}]", fontsize=12)
#     ax.legend()

#     if save_name is None:
#         if cfg['spatial_scope'] == "multi_vds":
#             save_name = f"{cfg['save_dir']}/{cfg['period_include']}/v6/BPR_calibration_{cfg['spatial_scope']}_{cfg['VDS_list']}_{cfg["temporal_scale"]}_v6_{cfg['method']}_{cfg['free_tt_method']}_{cfg['period_include']}.png"
#         else:
#             save_name = f"{cfg['save_dir']}/{cfg['period_include']}/v6/BPR_calibration_{cfg['spatial_scope']}_{cfg['VDS_num']}_{cfg["temporal_scale"]}_v6_{cfg['method']}_{cfg['free_tt_method']}_{cfg['period_include']}.png"
            
#     plt.savefig(save_name, bbox_inches="tight")
#     plt.close(fig)
# -

# ### (Code) Data filter & Regression & plot

# +
def build_file_path(cfg: dict) -> str:
    print(cfg['spatial_scope'])
    if (cfg['spatial_scope'] == "multi_vds"):
        file_path = f"./01_BPR/c_daily_traffic_division_{cfg['spatial_scope']}_{cfg['VDS_list']}_{cfg['temporal_scale']}_{cfg['aggregate_timeframe']}_{cfg['method']}_{cfg['congest_method']}.csv"
        print(file_path)
    else:
        file_path = f"./01_BPR/c_daily_traffic_division_{cfg['spatial_scope']}_{cfg['VDS_num']}_{cfg['temporal_scale']}_{cfg['aggregate_timeframe']}_{cfg['method']}_{cfg['congest_method']}.csv"
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
        if cfg["free_tt_method"] == "FD":
            if cfg['spatial_scope'] == 'single':
                df["free_traveltime"] = cfg['free_tt_FD'][cfg["VDS_num"]]
            elif cfg['spatial_scope'] == 'multi_vds':
                df["free_traveltime"] = cfg['free_tt_FD']['multi_vds']
        elif cfg["free_tt_method"] == "offpeak_avg":
            if cfg['spatial_scope'] == 'single':
                df["free_traveltime"] = cfg['free_tt_offpeak_avg'][cfg["VDS_num"]]
            elif cfg['spatial_scope'] == 'multi_vds':
                df["free_traveltime"] = cfg['free_tt_offpeak_avg']['multi_vds']

    if cfg["spatial_scope"] == 'single':
        lane_num = c_lane_num[cfg['VDS_num']]
        df['totaldemandoverlanes'] = df['totaldemand'] * len(lane_num)
        df['ln_totaldemandoverlanes'] = np.log(df["totaldemandoverlanes"])
    
    # derived logs
    df["ln_avg_flow"] = np.log(df["avg_flow"])
    df["ln_totaldemand"] = np.log(df["totaldemand"])
    

    # ln((z/ζ)-1) using either fixed or date-wise ζ
    df["ln_t_tau"] = np.log(df["traveltimes"]/df["free_traveltime"] - 1.0)

    # Version 5/6 convenience (Ideal waiting time)
    W_hour = cfg["W_minutes"]/60.0
    df["avgdemand"] = np.where(
        df["division"] == 0, df["totaldemand"], df["totaldemand"]/W_hour
    )

    return df

# === Recurrent vs all peaks (CONFIG) ===
def use_recurrent_peak_filter(cfg: dict) -> bool:
    """
    True  -> remove rows that appear in the non-recurrent exclusion CSV (recurrent peaks only).
    False -> keep all peak-period rows (no exclusion merge).

    New key: cfg['peak_subset'] in {'all', 'recurrent'}.
    Legacy: cfg['drop_nonrecurrent_days'] if peak_subset is absent.
    """
    ps = cfg.get("peak_subset")
    if ps == "all":
        return False
    if ps == "recurrent":
        return True
    return bool(cfg.get("drop_nonrecurrent_days", False))


def recurrent_exclusion_csv_path(cfg: dict) -> str:
    """
    Path to excluded_non_recurrent_peaks_*.csv produced by your preprocessing notebook.
    Override with cfg['recurrent_peaks']['exclusion_csv'].
    Method suffix from cfg['recurrent_peaks']['method'] or legacy cfg['nonrecurrent_method'].
    """
    rp = cfg.get("recurrent_peaks") or {}
    if rp.get("exclusion_csv"):
        return rp["exclusion_csv"]
    method = rp.get("method") or cfg.get("nonrecurrent_method") or "PELT"
    return f"./excluded_non_recurrent_peaks_{method}.csv"


# === One place to filter ===
def apply_filters(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    # common: remove division == -1
    if "division" in df.columns:
        df = df[df["division"] != -1]
    
    if cfg.get("dayofweek_exclude", False):
        df = df[~df["dayofweek"].isin(cfg["dayofweek_exclude"])]
    if cfg.get("month_exclude", False):
        df = df[~df["month"].isin(cfg["month_exclude"])]
    if cfg["year_exclude"] and "year" in df.columns:
        df = df[~df["year"].isin(cfg["year_exclude"])]

    df = df[df["period"].isin(cfg["period_include"][cfg['temporal_scale']])]

    # keep your special filter
    if cfg.get("spatial_scope") == "single" and str(cfg.get("VDS_num")) == "1205541":
        df = df[df["month"].isin(["2401", "2402", "2403"])]
    
    # -----------------------
    # 1) drop days with weird peak start_time (optional)
    # -----------------------
    if cfg.get("drop_days_weird_peak_times", False):

        morning_earliest = cfg["morning_earliest"]
        afternoon_latest = cfg["afternoon_latest"]

        # read_csv
        if (cfg['spatial_scope'] == "multi_vds"):
            file_path_sb = f"./01_BPR/c_daily_traffic_division_{cfg['spatial_scope']}_{cfg['VDS_list']}_speedbasedpeak_{cfg['aggregate_timeframe']}_{cfg['method']}_{cfg['congest_method']}.csv"
        else:
            file_path_sb = f"./01_BPR/c_daily_traffic_division_{cfg['spatial_scope']}_{cfg['VDS_num']}_speedbasedpeak_{cfg['aggregate_timeframe']}_{cfg['method']}_{cfg['congest_method']}.csv"
                
        # parse "HH:MM" (handles '-' -> NaT)
        df_sb = pd.read_csv(file_path_sb)
        df_sb = df_sb[df_sb["period"].isin(['morning-peak','afternoon-peak'])]

        # st = df_sb.to_datetime(df_sb["start_time"], format="%H:%M", errors="coerce").dt.time
        st = pd.to_datetime(df_sb["start_time"], format="%H:%M", errors="coerce").dt.time

        bad_mask = (
            ((df_sb["period"] == "morning-peak") &
             (st < pd.to_datetime(morning_earliest).time()))
            |
            ((df_sb["period"] == "afternoon-peak") &
             (st > pd.to_datetime(afternoon_latest).time()))
        )

        bad_dates = df_sb.loc[bad_mask, "date"].unique()
        print(cfg['VDS_list'])

        # apply to the current df
        print("bad_dates", bad_dates,len(bad_dates))
        df["date"] = pd.to_numeric(df["date"], errors="coerce").astype(int)
        bad_dates = bad_dates.astype(int)

        
        # print(len(df))
        df = df[~df["date"].isin(bad_dates)]
        # print(len(df))


    # Optional: Print the new counts to verify
    print(f"Original row count before overlapping peaks: {len(df)}")

    #### count & filter out dates with more than 1 occurenece
    periods_to_check = ['morning-peak', 'afternoon-peak']
    
    if cfg.get("drop_multiplecongestion_days", False):
        for period in periods_to_check:
            # 1. Filter for the specific period
            period_df = df_sb[df_sb['period'] == period]
        
            # 2. Count occurrences per date
            counts_per_date = period_df.groupby('date').size()
        
            # 3. Filter for dates with more than 1 occurrence
            dates_with_multiple = counts_per_date[counts_per_date > 1]
            count_result = len(dates_with_multiple)
        
            if count_result > 0:
                print(f"--- {period.upper()} ---")
                print(f"Number of dates with more than 1 {period}: {count_result}")
                print("Specific dates and their counts:")
                print(dates_with_multiple)
            print("\n")
    
            # 2. Filter the original DataFrame to REMOVE these dates
            if (cfg['temporal_scale'] in ['entireday','hour']):
                df = df[~df['date'].isin(dates_with_multiple)]
            
            elif (cfg['temporal_scale'] == 'speedbasedpeak'):
                print(len(df['date'].isin(dates_with_multiple.index.tolist())))
                df = df[~((df['date'].isin(dates_with_multiple.index.tolist())) & (df['period'] == period))]    
            # Optional: Print the new counts to verify
        print(f"filtered row count: {len(df)}")

    if use_recurrent_peak_filter(cfg):
        # Exclude rows listed in non-recurrent exclusion file (recurrent-peak-only BPR)
        exclusion_file = recurrent_exclusion_csv_path(cfg)
        if os.path.exists(exclusion_file):
            df_excl = pd.read_csv(exclusion_file)
            
            print( cfg['VDS_num'])

            df_excl = df_excl[df_excl['vds_id'].astype(str) == str(cfg['VDS_num'])]
            
            # 1. Convert to numeric first, forcing invalid values to NaN
            # 1. Convert the '2024-02-12' strings into Datetime objects
            df_excl['date_dt'] = pd.to_datetime(df_excl['date_dt'], errors='coerce')
            
            # 2. Format as '240212' string, then convert to numeric/int
            # .dt.strftime('%y%m%d') extracts the last two digits of the year + month + day
            df_excl['date_dt'] = df_excl['date_dt'].dt.strftime('%y%m%d').astype(float).fillna(0).astype(np.int64)
            
            # 3. Standardize the main dataframe 'date' to int64 as well to avoid merge errors
            df['date'] = pd.to_numeric(df['date'], errors='coerce').fillna(0).astype(np.int64)

            print(df_excl.head())

            def to_fractional(t_str):
                if pd.isna(t_str) or t_str == '-': return np.nan
                try:
                    h, m = map(int, str(t_str).split(':'))
                    return h + m/60.0
                except: return np.nan

            df['start_hour_tmp'] = df['start_time'].apply(to_fractional)
            
            
            # Create a mask to identify rows to remove
            # We match on vds_id, date, and period to identify the specific peak occurrences
            # Note: If your exclusion file uses 'date_dt' and 'period', make sure they align with df['date'] and df['period']
            initial_len = len(df)
            
            # Perform an anti-join
            # We merge with an indicator and keep only rows present in 'left' only
            df = df.merge(
                df_excl[['date_dt', 'period', 'start_hour']], 
                left_on=['date', 'period', 'start_hour_tmp'], 
                right_on=['date_dt', 'period', 'start_hour'], 
                how='left', 
                indicator=True
            )
            df = df[df['_merge'] == 'left_only'].drop(columns=['_merge', 'date_dt','start_hour_tmp'])
            
            print(f"Excluded {initial_len - len(df)} rows based on non-recurrent peaks file.")
        else:
            print(
                f"Warning: peak_subset=recurrent but exclusion file not found: {exclusion_file!r} "
                "(generate it with the matching nonrecurrent_method / recurrent_peaks.method)."
            )

    return to_categorical_day(df.copy())

# + editable=true slideshow={"slide_type": ""}
# stat

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.stattools import jarque_bera
from statsmodels.stats.diagnostic import linear_reset

def fit_bpr_ols_stats(dfg, xcol=None, ycol=None):
    """
    Fits: y = a + b x  (a = ln(tilde_alpha), b = beta)
    Returns a dict with tilde_alpha, t-stats, p-values, and R^2.
    """
    
    ## descriptive statistics
    
    mean_val = dfg['duration'].mean()
    median_val = dfg['duration'].median()
    
    
    # dfg = dfg[[xcol, ycol]].dropna()
    # if len(dfg) < 3:
    #     return None  # not enough points

    x = dfg[xcol].to_numpy()
    y = dfg[ycol].to_numpy()

    X = sm.add_constant(x)  # [1, x]
    model = sm.OLS(y, X).fit()

    a = model.params[0]
    b = model.params[1]
    
    # --- Residual normality test (Jarque–Bera) ---
    jb_stat, jb_pvalue, skew, kurt = jarque_bera(model.resid)


    # --- Ramsey RESET (functional form / nonlinearity check) ---
    # H0: model is correctly specified (no omitted nonlinear terms)
    reset_powers = (2,3)
    
    reset_res = linear_reset(model, power=reset_powers, use_f=True)
    reset_stat = float(reset_res.fvalue)
    reset_p = float(reset_res.pvalue)
    
    # =========================
    # 3) LINK TEST
    # =========================
    y_hat = model.fittedvalues
    X_link = sm.add_constant(
        np.column_stack([y_hat, y_hat**2])
    )
    link_model = sm.OLS(y, X_link).fit()

    link_stat = float(link_model.tvalues[2])     # coefficient on y_hat^2
    link_p = float(link_model.pvalues[2])   

    N_0 = (0.15 / math.exp(a)) ** (1 / b)
    
    out = {
        "ln_tilde_alpha": a,                         # intercept
        "alpha_t": float(model.tvalues[0]),
        "alpha_p": float(model.pvalues[0]),
        "N_0": float(N_0),
        "beta": float(b),
        "beta_t": float(model.tvalues[1]),
        "beta_p": float(model.pvalues[1]),
        "r2": float(model.rsquared),
        "n": int(model.nobs),

        # --- Normality diagnostics ---
        "jb_stat": float(jb_stat),
        "jb_p": float(jb_pvalue),

        # RESET diagnostics
        # "reset_power": tuple(reset_powers),
        "reset_stat": reset_stat,   # F-stat if use_f=True
        "reset_p": reset_p,

                # Link Test
        "link_t": link_stat,
        "link_p": link_p,

        "median": median_val,
        "mean": mean_val,
    }
    return out


# + editable=true slideshow={"slide_type": ""}
# 2) 3x3 wrapper (plot_bpr_all_in_one_png_3*3)
# =========================
def plot_bpr_all_in_one_png_3x3(
    cfg,
    version_key: str,
    xlim=None,
    ylim=None,
    var_list=None,               # kept for consistency
    suptitle="Segment-Level Log-",
    out_name="BPR_V3_ALL_3x3",
    show_legend_only_first=False,   # set True if you want only 1 legend total
    font_add=5,
    dpi=200,
):
    """
    Creates a single 3x3 PNG with your requested layout:
      row1: VDS 1-①, VDS 1-②, blank
      row2: VDS 2-①, VDS 2-②, VDS 2-③
      row3: VDS 2-④, VDS 2-⑤, blank
    """

    # --- pull VDS list and label map from cfg ---
    vds_list = cfg.get("VDS_list", [])
    vds_label_map = cfg.get("VDS_label_list", {})

    table_rows = []
    periods_for_table = cfg["period_include"][cfg['temporal_scale']]
    


    assert version_key in LINEAR_REGISTRY_BPR, f"Unknown version_key: {version_key}"
    trans = LINEAR_REGISTRY_BPR[version_key]

    xcol, ycol, xlab, ylab = trans()
    
    # panel order must match your VDS_list mapping
    # Expecting 7 items: [1-①,1-②,2-①,2-②,2-③,2-④,2-⑤]
    if len(vds_list) != 7:
        print(f"[Warning] Expected 7 VDS in cfg['VDS_list'], got {len(vds_list)}. Will plot what is available.")

    # layout indices in a 3x3 grid for 7 panels
    # positions: (r,c)
    positions = [(0,0),(0,1),
                 (1,0),(1,1),(1,2),
                 (2,0),(2,1)]   # (0,2) and (2,2) remain blank

    fig, axs = plt.subplots(
        3, 3,
        figsize=(16, 14),
        constrained_layout=True
    )

    # blank all axes first
    for ax in axs.ravel():
        ax.set_visible(False)

    # loop stations in order
    for i, vds_id in enumerate(vds_list):
        if i >= len(positions):
            break

        r, c = positions[i]
        ax = axs[r, c]
        ax.set_visible(True)

        # build cfg for this station
        cfg_i = copy.deepcopy(cfg)
        cfg_i["VDS_num"] = vds_id
        # cfg_i["VDS_list"] = vds_id  # keep your internal convention

        # --- load + filter using YOUR existing pipeline ---
        df_all = load_and_annotate(cfg_i)
        df_use = apply_filters(df_all, cfg_i)
        
        # ---- collect stats for BOTH periods ----
        for per in periods_for_table:
            dfg = df_use[df_use["period"] == per].copy()
            # dfg.to_csv(f"stas_{vds_id}_{per}.csv")
            
            stats = fit_bpr_ols_stats(dfg,xcol,ycol)
    
            peak_label = ("AM" if per == "morning-peak" else "PM" if per == "afternoon-peak" else "Entireday" if per == "off-peak" else per)
            
            row = {
                "VDS": vds_label_map.get(str(vds_id), str(vds_id)),  # e.g., "1-①"
                "Peak-period": str(peak_label),
                "N": 0 if stats is None else stats["n"],
                r"$log\tilde{\alpha}$": np.nan if stats is None else stats["ln_tilde_alpha"],
                "t-statistic (tilde_alpha)": np.nan if stats is None else stats["alpha_t"],
                "p-value (tilde_alpha)": np.nan if stats is None else stats["alpha_p"],
                r"$N_0$": np.nan if stats is None else stats["N_0"],
                r"$\beta$": np.nan if stats is None else stats["beta"],
                "t-statistic (beta)": np.nan if stats is None else stats["beta_t"],
                "p-value (beta)": np.nan if stats is None else stats["beta_p"],
                "R-square": np.nan if stats is None else stats["r2"],
                "jb_stat": np.nan if stats is None else stats["jb_stat"],
                "jb_p": np.nan if stats is None else stats["jb_p"],
                "reset_stat": np.nan if stats is None else stats["reset_stat"],
                "reset_p": np.nan if stats is None else stats["reset_p"],
                "link_t": np.nan if stats is None else stats["link_t"],
                "link_p": np.nan if stats is None else stats["link_p"],
                 "median": stats["median"],
                 "mean": stats["mean"],
            }
            table_rows.append(row)

            
        df_params = pd.DataFrame(table_rows)
        
        # legend logic
        show_legend = True
        if show_legend_only_first and i != 0:
            show_legend = False

        if len(xlim_list) >1:
            xlim = xlim_list[i]
        else:
            xlim = xlim_list[0]
        
        # plot panel
        plot_bpr_single_panel(
            df_use=df_use,
            cfg=cfg_i,
            version_key=version_key,
            xlim=xlim,
            ylim=ylim,
            ax=ax,
            xcol=xcol,
            ycol=ycol,
            show_legend=show_legend,
            font_add=font_add,
        )

        # FD-style panel title: "VDS 1-①"
        tag = vds_label_map.get(str(vds_id), str(vds_id))
        ax.set_title(f"{tag}", fontsize=16 + font_add, pad=8)

    # ----- shared labels + suptitle (prevents overlap) -----
    fig.suptitle(suptitle, fontsize=20 + font_add, y=1.05)
    fig.supxlabel(xlab, fontsize=16 + font_add)
    fig.supylabel(ylab, fontsize=16 + font_add)

    # save
    save_dir = cfg.get("save_dir", ".")
    os.makedirs(save_dir, exist_ok=True)
    out_path = os.path.join(save_dir, f"{out_name}.png")
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.show()
    
    out_table_filename = f"BPR_params_{cfg_i['temporal_scale']}_{periods_for_table}.csv"
    
    out_table_csv = os.path.join(save_dir, f"BPR_params_{cfg_i['temporal_scale']}_{periods_for_table}.csv")
    df_params.to_csv(out_table_csv, index=False)
    
    print("Saved table:", out_table_csv)
    print(df_params)
    print(f"Saved: {out_path}")
    
    return out_path


# + editable=true slideshow={"slide_type": ""}
# plot_bpr_single_panel

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.stattools import jarque_bera

def plot_bpr_single_panel(
    df_use,
    cfg,
    version_key,
    xlim=None,
    ylim=None,
    ax=None,
    xcol = None,
    ycol = None,
    show_legend=True,
    font_add=None,
):
    """
    Single panel with BOTH morning/afternoon overlaid (scatter + OLS line).
    Expects df_use includes:
      - 'period'
      - x: 'ln_totaldemandoverlanes'
      - y: 'ln_t_tau'
    """
    if ax is None:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 1, figsize=(6, 4))

    # ---- styling ----
    TICK  = 12 + font_add
    LEG   = 8 + font_add

    ax.minorticks_on()
    ax.grid(True, which="major", linestyle="--", linewidth=1.0, alpha=0.35)
    ax.grid(True, which="minor", linestyle="-",  linewidth=0.6, alpha=0.15)
    
    if cfg['temporal_scale'] == 'speedbasedpeak':
        # if period_include missing, default to these two
        periods = ["morning-peak", "afternoon-peak"]
        # in the case when 'period_include' was give as a single string (eg. "off-peak') convert it to ['off-peak']
        if isinstance(periods, str):
            periods = [periods]
    
        # normalize + order (so legend order is consistent)
        wanted_order = ["morning-peak", "afternoon-peak"]
        periods = [p for p in wanted_order if p in periods] + [p for p in periods if p not in wanted_order]
    elif cfg['temporal_scale'] == 'entireday':
        periods = ["off-peak"]
        if isinstance(periods, str):
            periods = [periods]
        use_label = not (len(periods) == 1 and periods[0] == "off-peak")

    elif cfg['temporal_scale'] == 'hour':
        periods = ["off-peak"]
        if isinstance(periods, str):
            periods = [periods]
        use_label = not (len(periods) == 1 and periods[0] == "off-peak")
        
    handles, labels = [], []

    for gname in periods:
        dfg = df_use[df_use["period"] == gname].copy()
        dfg = dfg[[xcol, ycol]].dropna()
        # dfg.to_csv(f"{gname}.csv")

        if dfg.empty:
            continue

        x = dfg[xcol].to_numpy()
        y = dfg[ycol].to_numpy()

        # scatter (label here so legend picks it up)
        sc = ax.scatter(x, y, s=55, alpha=0.55, edgecolors="none", label=gname)

        # OLS fit
        X = sm.add_constant(x)
        model = sm.OLS(y, X).fit()
        a, b = model.params[0], model.params[1]
        r2 = model.rsquared

        # fit line (same color as scatter)
        xx = np.linspace(np.nanmin(x), np.nanmax(x), 100)
        yy = a + b * xx
        ln, = ax.plot(xx, yy, linewidth=3, color=sc.get_facecolor()[0])

        # nicer legend label
        pretty = ("AM" if gname == "morning-peak" else "PM" if gname == "afternoon-peak" else "OLS-fit" if gname == "off-peak" else gname)

        labels.append(rf"{pretty}: $y={a:.2f}+{b:.2f}x$, $R^2$={r2:.3f}")
        handles.append(ln)

    # axis limits
    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    # ticks/spines
    ax.tick_params(axis="both", labelsize=TICK, width=1.8, length=6)
    for s in ax.spines.values():
        s.set_linewidth(1.8)

    # legend (use the LINE handles so legend shows fit equations cleanly)
    if show_legend and handles:
        ax.legend(handles, labels, loc="upper left", fontsize=LEG, frameon=True)

    return ax


# -

# ### (Code) Implementation

# + editable=true slideshow={"slide_type": ""}
# === Imports ===
import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Callable, Dict, Tuple, Optional
from scipy.optimize import curve_fit
import copy

# === Global style (optional) ===
plt.rcParams.update({"figure.dpi": 140})

# === Configuration ===
CONFIG_BPR = {
    # 1. Options to choose for every analysis
    "VDS_list" : ['1203481','1203506','1214006','1205583','1205572','1212611','1205541'],
    "spatial_scope" : "single" ,      # "multi_vds", "single"
    "working_f": "01_BPR",
    "temporal_scale": 'speedbasedpeak',    # used in file name "speedbasedpeak", "entireday", "hour", "peakhour"
    
    # 2. Data filter option
    "period_include": {'speedbasedpeak':['morning-peak', 'afternoon-peak'], 'hour': ['off-peak'], 'entireday': ['off-peak']},
    "drop_days_weird_peak_times": False,
    "drop_multiplecongestion_days" : False,
    # Peak rows for BPR: "all" = every peak day; "recurrent" = drop rows in exclusion CSV
    "peak_subset": "recurrent",
    # Legacy (used only if peak_subset is omitted): same as peak_subset "recurrent" when True
    "drop_nonrecurrent_days": True,
    # Legacy default method suffix; prefer recurrent_peaks["method"]
    "nonrecurrent_method": "PELT",
    # Settings for generating/choosing the exclusion file (apply_filters only uses method / exclusion_csv)
    "recurrent_peaks": {
        "method": "PELT",
        "exclusion_csv": None,
        "PELT": {"pen": 20, "min_size": 1, "jump": 1, "length_threshold_weeks": 4},
        "clustering": {},
        "2DKDE": {
            "band_hours": 0.5,
            "min_mode_count": 4,
            "min_mode_frac": 0.10,
            "include_non_peak_in_kde": True,
        },
        "simpleband": {"bandwidth_method": "se", "bandwidth_minutes": 45},
    },
    "morning_earliest": "03:00",
    "afternoon_latest": "22:00",
    "dayofweek_exclude": [],
    "month_exclude": [],
    "year_exclude": [],
        ## 2.1. freeflow speed setting 
    "free_tt_mode": "fixed",               # "fixed" OR "by_date_offpeak"
    "free_tt_method": "offpeak_avg", # offpeak_avg or FD

    # 3. data read  & save info
    "aggregate_timeframe": 5,              # used in file name (minutes)
    "save_dir": "./01_BPR/02 fig/12 Daily BPR",               # where to save figures
    "method": "RDP_v",
    'file_path': '/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR',
    
    # 4. Regression_info & plot
    "free_tt_offpeak_avg": {'1203481': 60*(1/64), '1203506': 60*(1/(63)), '1214006': 60*(1/(65)),'1205583': 60*(1/(66)),'1205572': 60*(1/(67)), '1212611': 60*(1/(65)),'1205541': 60*(1/(61)),'multi_vds': 60*(1/(64))},   # minutes/mile when mode=="fixed" (60*1/freeflow_speed),
    # "free_tt_offpeak_avg": {'1203481': 60*(1/61), '1203506': 60*(1/(61)), '1214006': 60*(1/(65)),'1205583': 60*(1/(66)),'1205572': 60*(1/(67)), '1212611': 60*(1/(65)),'1205541': 60*(1/(61)),'multi_vds': 60*(1/(64))},   # minutes/mile when mode=="fixed" (60*1/freeflow_speed),
    "VDS_label_list" : {'1203481': 'SR-91 WB','1203506': 'SR-91 EB','1214006': 'I-5 SB-1','1205583':'I-5 SB-2','1205572':'I-5 SB-3','1212611':'I-5 SB-4','1205541':'I-5 SB-5'},
    'free_tt_FD': {'1203506': 60*(1/55), '1203524': 60*(1/55), '1203481': 60*(1/55), '1205541': 60*(1/57), '1212611': 60*(1/57), '1205572': 60*(1/57), '1205583': 60*(1/57), '1214006': 60*(1/57), 'multi_vds': 60*(1/57)},

    "label_criterion": "period",           # "period", "dayofweek", "year", ...
    "W_minutes": 90,                      # heart-of-peak window for V5/V6 if needed
    "capacity_fixed": 1800*24,                # for V5/V6 where capacity is fixed
    "congest_method":'speed-solely', # speed-duration-only, 'speedgap-neighbor', 'occ', occ-solely,
    
    "occ_threshold": {       
        '1203506': {'occ_l': 0.12, 'occ_h': 0.31}, '1205541': {'occ_l': 0.09, 'occ_h': 0.15}, '1212611': {'occ_l': 0.11, 'occ_h': 0.24}, '1205572': {'occ_l': 0.09, 'occ_h': 0.22}},   # appears once only '1205583': {'occ_l': 0.095, 'occ_h': 0.14}, '1214006': {'occ_l': 0.07, 'occ_h': 0.29}},
    'FD_phase': {'1203506': 'three_phases', '1205541': 'three_phases', '1212611': 'three_phases', '1205572': 'three_phases', '1205583': 'three_phases', '1214006': 'three_phases', 'multi_vds' : 'three_phases'}
    }

# Ensure save dir exists
os.makedirs(CONFIG_BPR["save_dir"], exist_ok=True)

# + editable=true slideshow={"slide_type": ""}
# title name
if (CONFIG_BPR["temporal_scale"] == 'speedbasedpeak'):
    suptitle_var = "Log-Transformed BPR Function (Peak-Period Aggregation)"
elif (CONFIG_BPR["temporal_scale"] == "entireday"):
    suptitle_var = "Log-Transformed BPR Function (Entire-Day Aggregation)"
elif (CONFIG_BPR["temporal_scale"] == 'hour'):
    suptitle_var = "Log-Transformed BPR Function (Hourly Aggregation)"
elif (CONFIG_BPR["temporal_scale"] == 'peakhour'):
    suptitle_var = "Log-Transformed BPR Function (Peak-Hour)"

# plot range
if (CONFIG_BPR["temporal_scale"] == 'entireday'):
    xlim_list=[[11.2, 11.6],[11, 11.8],[10.9, 11.4],[11.1, 11.8],[11.4, 11.8],[11.6, 12.1],[11.4, 11.8]]
    ylim=[-6.1, 1.5]
elif (CONFIG_BPR["temporal_scale"] == 'speedbasedpeak'):
    xlim_list=[[6.5, 11]]; ylim=[-3.5, 3]
elif (CONFIG_BPR["temporal_scale"] == 'hour'):
    xlim_list=[[4.5, 8]]; ylim=[-15, 10]
elif (CONFIG_BPR["temporal_scale"] == 'peakhour'):
    xlim_list=[[6, 8]]; ylim=[-8, 5]

# out_file name
_peak_tag = CONFIG_BPR.get("peak_subset") or (
    "recurrent" if CONFIG_BPR.get("drop_nonrecurrent_days") else "all"
)
out_name = (
    f"BPR_V3_ALL_3x3_{CONFIG_BPR['temporal_scale']}_{CONFIG_BPR['period_include']}_"
    f"{CONFIG_BPR['free_tt_method']}_{_peak_tag}"
)

c_lane_num = {
    '1212611':[1,2,3,4,5,6], '1205572':[1,2,3,4,5,6], '1205583':[1,2,3,4,5,6],
    '1203506':[1,2,3,4], '1214006':[1,2,3,4], '1205541':[1,2,3,4],
    '1203589':[1,2,3,4], '1203615':[1,2,3,4], '1203524': [1,2,3,4], '1203481': [1,2,3,4]
}

plot_bpr_all_in_one_png_3x3(
    cfg=CONFIG_BPR,
    version_key="v3",
    xlim=xlim_list,
    ylim=ylim,
    suptitle=suptitle_var,
    out_name=out_name,
    font_add = 5,
    show_legend_only_first=False  # set True if you want ONLY the first legend
)
# -
# ## (Code) QQ-curve and residual curve

# +
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from statsmodels.graphics.gofplots import ProbPlot
import copy
import os

def plot_bpr_multi_scale_diagnostics_normalized(
    cfg_base, 
    version_key, 
    vds_list, 
    vds_label_map,
    diagnostic_type, # 'qq' or 'residual'
    font_add=2,
    out_name="BPR_Diagnostic_Comparison"
):
    """
    Creates a 3x3 grid where each panel represents one VDS.
    'speedbasedpeak' is split into morning-peak and afternoon-peak.
    """
    scales_to_compare = ['hour', 'entireday', 'speedbasedpeak']
    
    # Updated colors and labels to include AM/PM split
    colors = {
        'hour': '#A9C6DA', 
        'entireday': '#2ca02c', 
        'morning-peak': '#FF4500',   # Bright Orange for AM
        'afternoon-peak': '#800000'  # Deep Red/Maroon for PM to distinguish
    }
    label_set = {
        'hour': 'Hour', 
        'entireday': 'Entire-day', 
        'morning-peak': 'Peak (AM)', 
        'afternoon-peak': 'Peak (PM)'
    }
    
    positions = [(0,0),(0,1), (1,0),(1,1),(1,2), (2,0),(2,1)]
    
    fig, axs = plt.subplots(3, 3, figsize=(14, 11), constrained_layout=True)
    for ax in axs.ravel(): ax.set_visible(False)

    trans = LINEAR_REGISTRY_BPR[version_key]
    xcol, ycol, _, _ = trans()

    for i, vds_id in enumerate(vds_list):
        if i >= len(positions): break
        r, c = positions[i]
        ax = axs[r, c]
        ax.set_visible(True)
        
        tag = vds_label_map.get(str(vds_id), str(vds_id))
        ax.set_title(f"VDS {tag}", fontsize=14+font_add, fontweight='bold')

        for scale in scales_to_compare:
            cfg_s = copy.deepcopy(cfg_base)
            cfg_s['temporal_scale'] = scale
            cfg_s['VDS_num'] = vds_id
            cfg_s['VDS_list'] = vds_id

            # Ensure the config includes the correct periods to load
            if scale == 'speedbasedpeak':
                cfg_s['period_include'] = ['morning-peak', 'afternoon-peak']
            else:
                cfg_s['period_include'] = ['off-peak']
            
            try:
                df_all = load_and_annotate(cfg_s)
                if str(vds_id) == "1205541" and "month" in df_all.columns:
                    df_all = df_all[~df_all["month"].isin(["2401", "2402", "2403", "2404"])]
                df_raw = apply_filters(df_all, cfg_s)

                # --- SUB-PERIOD LOGIC ---
                # If speedbasedpeak, we loop through AM and PM peaks separately
                if scale == 'speedbasedpeak':
                    sub_periods = ['morning-peak', 'afternoon-peak']
                else:
                    sub_periods = [scale] # 'hour' or 'entireday'

                for sp in sub_periods:
                    if scale == 'speedbasedpeak':
                        df_use = df_raw[df_raw['period'] == sp].copy()
                    else:
                        df_use = df_raw.copy()

                    df_fit = df_use[[xcol, ycol]].dropna()
                    if df_fit.empty: continue
                    
                    X = sm.add_constant(df_fit[xcol].to_numpy())
                    y = df_fit[ycol].to_numpy()
                    model = sm.OLS(y, X).fit()
                    
                    resids = model.resid
                    y_hat = model.fittedvalues
                    
                    # Normalize y_hat to [0, 1]
                    y_hat_min, y_hat_max = y_hat.min(), y_hat.max()
                    y_hat_norm = (y_hat - y_hat_min) / (y_hat_max - y_hat_min) if y_hat_max != y_hat_min else y_hat

                    current_color = colors.get(sp, '#000000')
                    current_label = label_set.get(sp, sp)

                    if diagnostic_type == 'qq':
                        std_resids = (resids - resids.mean()) / resids.std()
                        pp = ProbPlot(std_resids, fit=True)
                        theoretical = pp.theoretical_quantiles
                        sample = pp.sample_quantiles
                        
                        ax.scatter(theoretical, sample, color=current_color, alpha=0.3, s=12, label=current_label)
                        if scale == scales_to_compare[0] and sp == sub_periods[0]:
                            line_val = [min(theoretical), max(theoretical)]
                            ax.plot(line_val, line_val, color='black', linestyle='--', alpha=0.5)
                        ax.set_xlabel("Theoretical Quantiles", fontsize=10+font_add)
                        ax.set_ylabel("Std. Sample Quantiles", fontsize=10+font_add)

                    elif diagnostic_type == 'residual':
                        ax.scatter(y_hat_norm, resids, color=current_color, alpha=0.3, s=12, label=current_label)
                        ax.axhline(0, color='black', linestyle='--', alpha=0.5)
                        
                        lowess = sm.nonparametric.lowess(resids, y_hat_norm, frac=0.6)
                        # ax.plot(lowess[:, 0], lowess[:, 1], color=current_color, lw=2)
                        
                        ax.set_xlabel("Norm. Fitted [0, 1]", fontsize=10+font_add)
                        ax.set_ylabel("Residuals", fontsize=10+font_add)

            except Exception as e:
                print(f"Skipping {vds_id} for {scale}/{sp}: {e}")

        if i == 0:
            ax.legend(fontsize=10+font_add, loc='best', frameon=True)

    suptitle_text = "Q-Q Plots" if diagnostic_type == 'qq' else "Residuals vs Normalized Fitted"
    fig.suptitle(f"{suptitle_text}", fontsize=18+font_add, y=1.02)
    
    save_dir = cfg_base.get("save_dir", ".")
    out_path = os.path.join(save_dir, f"{out_name}_norm_{diagnostic_type}_split.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.show()
    return out_path


# +
# === Imports ===
import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Callable, Dict, Tuple, Optional
from scipy.optimize import curve_fit
import copy

# === Global style (optional) ===
plt.rcParams.update({"figure.dpi": 140})

# === Configuration ===
CONFIG_linear = {
    "VDS_list" : ['1203481','1203506','1214006','1205583','1205572','1212611','1205541'],
    "spatial_scope" : "single" ,      # "multi_vds", "single"
    "working_f": "01_BPR",
    # stations = [1203506,1203589,1203615]
    # "VDS_num": '1205572',                # 1203506, 1205583, 1214006, ...
    "temporal_scale": 'hour',    # used in file name "speedbasedpeak", "entireday" "hour"
    "period_include": ['off-peak'],  # subset e.g. ['morning-peak', 'afternoon-peak'] or ['off-peak'] for the entireday
    "drop_days_weird_peak_times": True,
    "morning_earliest": "03:00",
    "afternoon_latest": "22:00",
    "method": "RDP_v",
    "free_tt_mode": "fixed",               # "fixed" OR "by_date_offpeak"
    "free_tt_method": "offpeak_avg", # offpeak_avg or FD
    "aggregate_timeframe": 5,              # used in file name (minutes)
    "save_dir": "./01_BPR/02 fig/12 Daily BPR",               # where to save figures
    "max_duration": 420,
    "label_criterion": "period",           # "period", "dayofweek", "year", ...
    "dayofweek_exclude": [],
    "month_exclude": [],
    "year_exclude": [],
    #This is mean free_tt
    "free_tt_offpeak_avg": {'1203481': 60*(1/64), '1203506': 60*(1/(63)), '1214006': 60*(1/(65)),'1205583': 60*(1/(66)),'1205572': 60*(1/(67)), '1212611': 60*(1/(65)),'1205541': 60*(1/(61)),'multi_vds': 60*(1/(64))},   # minutes/mile when mode=="fixed" (60*1/freeflow_speed),
    # "free_tt_offpeak_avg": {'1203481': 60*(1/61), '1203506': 60*(1/(61)), '1214006': 60*(1/(65)),'1205583': 60*(1/(66)),'1205572': 60*(1/(67)), '1212611': 60*(1/(65)),'1205541': 60*(1/(61)),'multi_vds': 60*(1/(64))},   # minutes/mile when mode=="fixed" (60*1/freeflow_speed),
    "VDS_label_list" : {'1203481': 'SR-91 WB','1203506': 'SR-91 EB','1214006': 'I-5 SB-1','1205583':'I-5 SB-2','1205572':'I-5 SB-3','1212611':'I-5 SB-4','1205541':'I-5 SB-5'},
    'free_tt_FD': {'1203506': 60*(1/55), '1203524': 60*(1/55), '1203481': 60*(1/55), '1205541': 60*(1/57), '1212611': 60*(1/57), '1205572': 60*(1/57), '1205583': 60*(1/57), '1214006': 60*(1/57), 'multi_vds': 60*(1/57)},
    "W_minutes": 90,                      # heart-of-peak window for V5/V6 if needed
    "capacity_fixed": 1800*24,                # for V5/V6 where capacity is fixed
    "congest_method":'speed-solely', # speed-duration-only, 'speedgap-neighbor', 'occ', occ-solely,
    'file_path': '/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR',
}

# Ensure save dir exists
os.makedirs(CONFIG_BPR["save_dir"], exist_ok=True)

# +
# Assuming your existing cfg, version_key, and vds_list are defined:

cfg = CONFIG_linear.copy()

vds_list = cfg.get("VDS_list", [])
vds_label_map = cfg.get("VDS_label_list", {})

# 1. Generate the 3x3 QQ-Plot comparison
plot_bpr_multi_scale_diagnostics_normalized(
    cfg_base=cfg,
    version_key="v2", # or your version_key
    vds_list=vds_list,
    vds_label_map=vds_label_map,
    diagnostic_type='qq'
)

# 2. Generate the 3x3 Residual vs Fitted comparison
plot_bpr_multi_scale_diagnostics_normalized(
    cfg_base=cfg,
    version_key="v2", 
    vds_list=vds_list,
    vds_label_map=vds_label_map,
    diagnostic_type='residual'
)

# + [markdown] editable=true slideshow={"slide_type": ""}
# ## (Code) 

# +
import os
import copy
import numpy as np
import matplotlib.pyplot as plt

# ============================================
# A) Single panel: duration vs totaldemand
# ============================================
def plot_duration_vs_demand_single_panel(
    df_use,
    cfg,
    ax=None,
    xcol="totaldemand",
    duration_col="duration",
    period_col="period",
    periods=("morning-peak", "afternoon-peak"),
    dt_min=5,                # if duration is in # of 5-min bins
    duration_unit="auto",    # "auto" | "bins" | "minutes"
    show_legend=True,
    font_add=5,
    xlim=None,
    ylim=None,
):
    """
    Scatter: duration (y) vs totaldemand (x), overlaid by period (Mor/Aft).

    - df_use is your filtered congested-period observation table.
    - duration_unit:
        * "bins": convert duration -> minutes using dt_min
        * "minutes": use as-is
        * "auto": infer; if max(duration) <= 288, treat as bins (typical max # of 5-min bins in a day)
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(6, 4))

    TICK = 12 + font_add
    LEG = 9 + font_add
    ax.minorticks_on()
    ax.grid(True, which="major", linestyle="--", linewidth=1.0, alpha=0.35)
    ax.grid(True, which="minor", linestyle="-", linewidth=0.6, alpha=0.15)

    # basic checks
    needed = {xcol, duration_col, period_col}
    missing = needed - set(df_use.columns)
    if missing:
        ax.text(0.5, 0.5, f"Missing columns: {missing}", ha="center", va="center", transform=ax.transAxes)
        return ax

    # infer duration unit
    dur = df_use[duration_col].dropna()
    if duration_unit == "auto":
        # Heuristic: <= 288 usually means "number of 5-min bins" (24*60/5)
        duration_unit_use = "bins" if (len(dur) and dur.max() <= 288) else "minutes"
    else:
        duration_unit_use = duration_unit

    def _dur_to_minutes(s):
        return s * dt_min if duration_unit_use == "bins" else s

    handles, labels = [], []
    for per in periods:
        dfg = df_use[df_use[period_col] == per].copy()
        dfg = dfg[[xcol, duration_col]].dropna()
        if dfg.empty:
            continue

        x = dfg[xcol].to_numpy()
        y = _dur_to_minutes(dfg[duration_col]).to_numpy()

        sc = ax.scatter(x, y, s=55, alpha=0.55, edgecolors="none")
        pretty = "Mor" if per == "morning-peak" else ("Aft" if per == "afternoon-peak" else per)

        # store one handle for legend (scatter)
        handles.append(sc)
        labels.append(pretty)

    if show_legend and handles:
        ax.legend(handles, labels, loc="upper left", fontsize=LEG, frameon=True)

    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    ax.tick_params(axis="both", labelsize=TICK, width=1.8, length=6)
    for s in ax.spines.values():
        s.set_linewidth(1.8)

    return ax



# +

# ============================================
# B) 3x3 wrapper: duration vs demand (mirrors your BPR layout)
# ============================================
def plot_duration_demand_all_in_one_png_3x3(
    cfg,
    out_name="Duration_vs_Demand_ALL_3x3",
    periods=("morning-peak", "afternoon-peak"),
    dt_min=5,
    duration_unit="auto",
    xlim=None,
    ylim=None,
    font_add=5,
    dpi=200,
):
    """
    Creates a single 3x3 PNG:
      row1: VDS 1-①, VDS 1-②, blank
      row2: VDS 2-①, VDS 2-②, VDS 2-③
      row3: VDS 2-④, VDS 2-⑤, blank
    with Mor/Aft overlaid in each panel.
    """
    vds_list = cfg.get("VDS_list", [])
    vds_label_map = cfg.get("VDS_label_list", {})

    if len(vds_list) != 7:
        print(f"[Warning] Expected 7 VDS in cfg['VDS_list'], got {len(vds_list)}. Will plot what is available.")

    positions = [(0,0),(0,1),
                 (1,0),(1,1),(1,2),
                 (2,0),(2,1)]  # (0,2) and (2,2) blank

    fig, axs = plt.subplots(3, 3, figsize=(16, 14), constrained_layout=True)

    # hide all
    for ax in axs.ravel():
        ax.set_visible(False)

    for i, vds_id in enumerate(vds_list):
        if i >= len(positions):
            break
        r, c = positions[i]
        ax = axs[r, c]
        ax.set_visible(True)

        cfg_i = copy.deepcopy(cfg)
        cfg_i["VDS_num"] = vds_id
        cfg_i["VDS_list"] = vds_id  # keep your convention

        # ---- your pipeline ----
        df_all = load_and_annotate(cfg_i)

        if cfg_i.get("spatial_scope") == "single" and str(cfg_i.get("VDS_num")) == "1205541":
            if "month" in df_all.columns:
                df_all = df_all[~df_all["month"].isin(["2401", "2402", "2403", "2404"])]

        df_use = apply_filters(df_all, cfg_i)

        # panel plot
        show_legend = (i == 0)  # legend only on first to keep it clean
        plot_duration_vs_demand_single_panel(
            df_use=df_use,
            cfg=cfg_i,
            ax=ax,
            periods=periods,
            dt_min=dt_min,
            duration_unit=duration_unit,
            show_legend=show_legend,
            font_add=font_add,
            xlim=xlim,
            ylim=ylim,
        )

        tag = vds_label_map.get(str(vds_id), str(vds_id))
        ax.set_title(f"VDS {tag}", fontsize=16 + font_add, pad=8)

    fig.suptitle("Congested-period Duration vs Total Demand", fontsize=20 + font_add, y=1.05)
    fig.supxlabel(r"Total demand $Q$ (vehicles)", fontsize=16 + font_add)
    fig.supylabel("Congested duration (minutes)", fontsize=16 + font_add)

    save_dir = cfg.get("save_dir", ".")
    os.makedirs(save_dir, exist_ok=True)
    out_path = os.path.join(save_dir, f"{out_name}.png")
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.show()

    print(f"Saved: {out_path}")
    return out_path



# -

plot_duration_demand_all_in_one_png_3x3(CONFIG_BPR, dt_min=5, duration_unit="auto")

# ## (code) Demand Histogram

# +
import os
import copy
import numpy as np
import matplotlib.pyplot as plt

def plot_totaldemand_histogram_single_panel(
    df_use,
    ax,
    xcol="totaldemand",
    period_col="period",
    periods=("morning-peak", "afternoon-peak"),
    bins=30,
    density=True,
    font_add=5,
    show_legend=True,
):
    TICK = 12 + font_add
    LEG = 10 + font_add

    # styling
    ax.minorticks_on()
    ax.grid(True, which="major", linestyle="--", linewidth=1.0, alpha=0.35)
    ax.grid(True, which="minor", linestyle="-", linewidth=0.6, alpha=0.15)
    ax.set_ylim(0, 0.001)
    ax.set_xlim(0, 10000)

    handles, labels = [], []
    for per in periods:
        s = df_use.loc[df_use[period_col] == per, xcol].dropna()
        if s.empty:
            continue

        lab = "Mor" if per == "morning-peak" else ("Aft" if per == "afternoon-peak" else per)

        # use common bin edges per panel (stable overlay)
        # -> compute edges from the pooled data in this panel
    pooled = df_use.loc[df_use[period_col].isin(periods), xcol].dropna()
    if pooled.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return

    edges = np.histogram_bin_edges(pooled.to_numpy(), bins=bins)

   # split data explicitly
    mor = df_use.loc[df_use[period_col] == "morning-peak", xcol].dropna().to_numpy()
    aft = df_use.loc[df_use[period_col] == "afternoon-peak", xcol].dropna().to_numpy()
    
    # Morning: filled histogram
    if mor.size:
        ax.hist(
            mor,
            bins=edges,
            density=density,
            histtype = "step",
            linewidth=2.5,
            label="Mor",
        )
    
    # Afternoon: outline-only histogram
    if aft.size:
        ax.hist(
            aft,
            bins=edges,
            density=density,
            histtype="step",
            linewidth=2.5,
            label="Aft",
        )
    if show_legend:
        ax.legend(loc="upper right", fontsize=LEG, frameon=True)
    

    ax.tick_params(axis="both", labelsize=TICK, width=1.8, length=6)
    for sp in ax.spines.values():
        sp.set_linewidth(1.8)


def plot_totaldemand_histogram_all_in_one_png_3x3(
    cfg,
    out_name="TotalDemand_Hist_ALL_3x3",
    periods=("morning-peak", "afternoon-peak"),
    bins=30,
    density=True,
    font_add=5,
    dpi=200,
):
    """
    Same 3x3 layout as your BPR plots:
      row1: VDS 1-①, VDS 1-②, blank
      row2: VDS 2-①, VDS 2-②, VDS 2-③
      row3: VDS 2-④, VDS 2-⑤, blank
    Each panel overlays Mor/Aft histograms of totaldemand.
    """
    vds_list = cfg.get("VDS_list", [])
    vds_label_map = cfg.get("VDS_label_list", {})

    positions = [(0,0),(0,1),
                 (1,0),(1,1),(1,2),
                 (2,0),(2,1)]  # (0,2), (2,2) blank

    fig, axs = plt.subplots(3, 3, figsize=(16, 14), constrained_layout=True)
    for ax in axs.ravel():
        ax.set_visible(False)

    for i, vds_id in enumerate(vds_list):
        if i >= len(positions):
            break
        r, c = positions[i]
        ax = axs[r, c]
        ax.set_visible(True)

        cfg_i = copy.deepcopy(cfg)
        cfg_i["VDS_num"] = vds_id
        cfg_i["VDS_list"] = vds_id

        df_all = load_and_annotate(cfg_i)

        # your special exclusion
        if cfg_i.get("spatial_scope") == "single" and str(cfg_i.get("VDS_num")) == "1205541":
            if "month" in df_all.columns:
                df_all = df_all[~df_all["month"].isin(["2401","2402","2403","2404"])]

        df_use = apply_filters(df_all, cfg_i)

        # show_legend = (i == 0)  # only first panel
        show_legend = True
        plot_totaldemand_histogram_single_panel(
            df_use=df_use,
            ax=ax,
            xcol="totaldemand",
            period_col="period",
            periods=periods,
            bins=bins,
            density=density,
            font_add=font_add,
            show_legend=show_legend,
        )

        tag = vds_label_map.get(str(vds_id), str(vds_id))
        ax.set_title(f"VDS {tag}", fontsize=16 + font_add, pad=8)

    fig.suptitle("Total Demand Histogram", fontsize=20 + font_add, y=1.05)
    fig.supxlabel("Total demand $Q$ (vehicles)", fontsize=16 + font_add)
    fig.supylabel("Relative frequency" if density else "Count", fontsize=16 + font_add)

    save_dir = cfg.get("save_dir", ".")
    os.makedirs(save_dir, exist_ok=True)
    out_path = os.path.join(save_dir, f"{out_name}.png")
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.show()

    print(f"Saved: {out_path}")
    return out_path



# +

plot_totaldemand_histogram_all_in_one_png_3x3(CONFIG_BPR, bins=25, density=True)


# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### (Version1) ln(Avgflow)-ln(traveltimes)
# -

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} q^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC/T)^\beta}$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(q)$
# - $y_n = ln(\tilde{\alpha})+\beta x_n$
#

# + [markdown] jp-MarkdownHeadingCollapsed=true
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

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### (Version3) Inverse ln(Avgdemand) vs ln(traveltimes)
# -

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} (Tq)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tq$
# - $ln(\frac{z(r)}{\zeta}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - $-ln(\frac{z(r)}{\zeta}-1)=-ln(\tilde{\alpha})-\beta ln(N)$
# - $ln((\frac{z(r)}{\zeta}-1)^{-1})=ln(\frac{1}{\tilde{\alpha}})  -\beta ln(N)$

# + [markdown] jp-MarkdownHeadingCollapsed=true editable=true slideshow={"slide_type": ""}
# #### (version4) speed dependent 
# -

# - $z(r)=\zeta(1+\alpha r^\beta)$
# - $z(r)=\zeta[1+\alpha (\frac{q}{WC/T})^\beta]=\zeta(1+\tilde{\alpha} (Tq)^\beta)=\zeta(1+\tilde{\alpha} N^\beta)$
#     - where $\tilde{\alpha}=\frac{\alpha}{(WC)^\beta}, N = Tq$
# - $ln(\frac{z(r)}{\zeta(r)}-1)=ln(\tilde{\alpha})+\beta ln(N)$
# - $-ln(\frac{z(r)}{\zeta(r)}-1)=-ln(\tilde{\alpha})-\beta ln(N)$
# - $ln((\frac{z(r)}{\zeta(r)}-1)^{-1})=ln(\frac{1}{\tilde{\alpha}})  -\beta ln(N)$

# + [markdown] jp-MarkdownHeadingCollapsed=true
# #### (Version5) total demand with time-window size
# -

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

# ## Data Quality check

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

def rawdata_setting(directory,VDS_num,file_name,lane_num):
    """
    Upload raw-data and standardize the settings
    """
    
    rawdata = pd.read_excel("./01_BPR/11 Rawdata/%s/%s/%s" % (directory,VDS_num,file_name))
    
    rawdata.columns = ['time'] + [f'flow_{i}' for i in lane_num] + [f'speed_{i}' for i in lane_num] + [f'occ_{i}' for i in lane_num] + ['length']                                                                                                                                    

    rawdata['time'] = pd.to_datetime(rawdata['time'])
    # 'time_filter' is to convert the time to minutes.(ex. 02:30:30 -> 150.30min)
    rawdata['time_filter'] = rawdata['time'].dt.hour*60 + rawdata['time'].dt.minute + rawdata['time'].dt.second/60
    # rawdata['time_filter'] = rawdata['time'].dt.hour*100 + rawdata['time'].dt.minute
    rawdata['time_hour'] = rawdata['time'].dt.hour
    
    return rawdata


# +
"""
This is the plot of average flow and speed over time for every day.
"""

def plot_within_day(traffic_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num):
    
    # 1st Plot: Time vs Traffic Flow and Avg Speed
    fig, ax = plt.subplots(1,2, figsize=(18,6))
    fig.suptitle(f'Traffic State within a Day using {directory} data(Date: {file_name[8:-5]}({Day}))',fontsize=18)
    ax[0].plot(plot_date, traffic_day['flow'], color='tab:blue')
    
    # Configure x-axis ticks and labels
    x_ticks = range(0, 1440, 60)
    x_labels = range(0, 24, 1)
    ax[0].set_xticks(ticks=x_ticks, labels=x_labels, fontsize=10)
    ax[0].locator_params(axis='x', nbins=25)
    
    # Set plot title and labels
    ax[0].set_title(f'Average Flow and Speed over time (aggregated by every {aggregate_timeframe} min)',fontsize=13)
    ax[0].set_ylabel('Flow rates (vphpl)', color='tab:blue', fontsize=12)
    ax[0].tick_params(axis='y',labelcolor='tab:blue')
    ax[0].set_xlabel('Time (hr)', fontsize=12)
    ax[0].set_ylim(0,2500)
    ax[0].set_yticks(range(0,2600,200))
    
    # Create a twinx axis for the second line plot on the same subplot
    ax2 = ax[0].twinx()
    ax2.plot(plot_date, traffic_day['speed'], color='tab:red')
    ax2.tick_params(axis='y',labelcolor='tab:red')
    ax2.set_ylim(0,100)
    ax2.set_yticks(range(0,100,10))
    
    # Set y-axis label for the twinx axis
    ax2.set_ylabel('Speed (mph)', color='tab:red', fontsize=12)
    
    # 2nd Plot: z vs q
    ax[1].scatter(traffic_day['flow'], traffic_day['time'])
    
    # Set title and labels for the second subplot
    ax[1].set_title('z over q',fontsize=13)
    ax[1].set_ylabel('z (min/mile)', fontsize=12)
    ax[1].set_xlabel('q (vphpl)', fontsize=12)
    ax[1].set_yticks(range(0,8))

    # Enable grid for both subplots
    ax[0].grid(True)
    ax[1].grid(True)
    
    directory_path = f"./02 fig/11 Unit time/{VDS_num}"
    # Create the directory
    os.makedirs(directory_path, exist_ok=True)

    plt.savefig(f'{directory_path}/{date}_{lane_num}.png')
    plt.close()


# + jupyter={"source_hidden": true}
def avg_traffic_state(rawdata, time_frame, lane_num):
    """
    Calculate traffic state parameters without gfactor.
    Density is computed as flow / speed.
    """

    # Step 0: Select variables
    flow_variable = [f'flow_{lane}' for lane in lane_num]
    speed_variable = [f'speed_{lane}' for lane in lane_num]

    # Step 1: Convert flow to vph
    rawdata_flow_df = rawdata[flow_variable] * (60 / time_frame)
    rawdata_flow = np.array(rawdata_flow_df)

    # Step 2: Read speed (mph)
    rawdata_speed = np.array(rawdata[speed_variable])

    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        rawdata_density = rawdata_flow / rawdata_speed

    # Replace inf and NaN with 0
    rawdata_density[~np.isfinite(rawdata_density)] = 0

    # ---------------------------
    # CV calculation per lane
    # ---------------------------

    agg_flow_per_lane = np.mean(rawdata_flow, axis=0)
    cv_flow = np.std(agg_flow_per_lane, ddof=0) / np.mean(agg_flow_per_lane)

    agg_density_per_lane = np.mean(rawdata_density, axis=0)
    cv_density = np.std(agg_density_per_lane, ddof=0) / np.mean(agg_density_per_lane)

    agg_speed_per_lane = np.mean(rawdata_speed, axis=0)
    cv_speed = np.std(agg_speed_per_lane, ddof=0) / np.mean(agg_speed_per_lane)

    # ---------------------------
    # Aggregate across all lanes
    # ---------------------------

    rawdata_flow_flat = rawdata_flow.flatten()
    rawdata_speed_flat = rawdata_speed.flatten()

    # Weighted average speed
    with np.errstate(divide='ignore', invalid='ignore'):
        multiply = rawdata_flow_flat * (1 / rawdata_speed_flat)

    sum_flow = np.nansum(rawdata_flow_flat)
    sum_product = np.nansum(multiply)

    avg_speed = sum_flow / sum_product if sum_product != 0 else 0
    avg_time = 60 / avg_speed if avg_speed != 0 else 0
    avg_flow = np.mean(rawdata_flow_flat)
    avg_density = avg_flow / avg_speed if avg_speed != 0 else 0

    return (avg_speed, avg_time, avg_flow, avg_density,
            cv_flow, cv_density, cv_speed,
            agg_flow_per_lane, agg_density_per_lane, agg_speed_per_lane)


# + jupyter={"source_hidden": true}
""" Sometimes, the rawdata interval is too short to see the stable traffic pattern, so rawdata is aggregated to specific time interval.
This function address calculating traffic state variables in every pre-determined aggregated time interval.
"""

def aggregate_rawdata(rawdata, aggregate_timeframe, raw_timeframe, date, lane_num, VDS_num):
    
    # Pre-compute time_slot for all data to avoid doing it in the loop
    rawdata['time_slot'] = np.floor(rawdata['time_filter'] / aggregate_timeframe) * aggregate_timeframe
    
    # Initialize list to store each row's data for final DataFrame
    traffic_within_day = pd.DataFrame()
    plot_date = []
     
    # Operate on grouped DataFrame
    for time_slot, group in rawdata.groupby('time_slot'):
        if not group.empty:
            avg_speed, avg_time, avg_flow, avg_density, cv_flow, cv_density, cv_speed, agg_flow_per_lane, agg_density_per_lane, agg_speed_per_lane = avg_traffic_state(group, raw_timeframe, lane_num)
        
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


# -

def cv_calculation(agg_data, lane_num, date, time, raw_timeframe, plot_whyCV, plot_time, plot_flow):
    
    flow_variable = [f'flow_{lane}' for lane in lane_num]
    density_variable = [f'density_{lane}' for lane in lane_num]
    speed_variable = [f'speed_{lane}' for lane in lane_num]
    
    occ_variable = [f'occ_{lane}' for lane in lane_num]
    
    ## step1: flow
    agg_flow_df = agg_data[flow_variable]
    
    agg_flow = np.array(agg_data[flow_variable])
    agg_density = np.array(agg_data[density_variable])
    agg_speed = np.array(agg_data[speed_variable])
       
    daily_flow = agg_flow.mean(axis=0)
    daily_density = agg_density.mean(axis=0)
        
    ## ddof=0: population std, ddof=1: sample
    cv_flow_day = np.std(daily_flow, ddof=0) / np.mean(daily_flow)
    cv_density_day = np.std(daily_density, ddof=0) / np.mean(daily_density)
        
    daily_speed = []

    ## calculate CV every timeframe and average them
    cv_flow_interval = np.std(agg_flow,axis=1,ddof=0)/np.mean(agg_flow,axis=1)
    cv_density_interval = np.std(agg_density,axis=1,ddof=0)/np.mean(agg_density,axis=1)

    cv_flow_day_v2 = np.mean(cv_flow_interval)
    cv_density_day_v2 = np.mean(cv_density_interval)
    
    for lane in lane_num: 
        flow_unit = agg_flow.transpose()[(lane-1)].flatten()
        speed_unit = agg_speed.transpose()[(lane-1)].flatten()
        density_unit = agg_density.transpose()[(lane-1)].flatten()
        
        rest_flow_df = agg_flow_df.drop(columns = [f'flow_{lane}'])
   
        daily_speed_per_lane = average_speed_calculation(flow_unit, speed_unit, density_unit, rest_flow_df, malfunc_inclusion = True)
        daily_speed.append(daily_speed_per_lane)
        
    cv_speed_day = np.std(daily_speed, ddof=0)/np.mean(daily_speed)
    
    return cv_flow_day, cv_density_day, cv_speed_day, cv_flow_day_v2, cv_density_day_v2, daily_flow, daily_density


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


# -

def plot_CV_within_day(traffic_within_day, rawdata, date, aggregate_timeframe, VDS_num):
    
    mean_flow = traffic_within_day['flow']
    cv_flow = traffic_within_day['cv_flow']

    mean_density = traffic_within_day['density']
    cv_density = traffic_within_day['cv_density']

    mean_speed = traffic_within_day['speed']
    cv_speed = traffic_within_day['cv_speed']
    # raw_time_with_rows = [(list(rawdata.loc[rawdata['time_filter'] == idx, 'time']), rawdata.index[rawdata['time_filter'] == idx].tolist()) for idx in traffic_within_day['time_slot']]
    
    raw_time = [list(rawdata.loc[(rawdata['time_filter'] == idx),'time']) for idx in traffic_within_day['time_slot']]
    raw_row = [rawdata.index[rawdata['time_slot'] == idx].tolist() for idx in traffic_within_day['time_slot']]
    time_r = [[str(ts) for ts in sublist] for sublist in raw_time]
    
    for idx, sublist in enumerate(time_r):
        if len(sublist) == 0:
            time_r[idx] = [rawdata.loc[raw_row[idx][0],'time']]
    
    time = [str(sublist[0]) for sublist in time_r if sublist]
    time_s = [pd.Timestamp(ts) for ts in time]
    # # Plot 1: CV across time
    # fig, ax = plt.subplots(1,1,figsize=(8,4))
    # ax.scatter(time_s, cv_flow, s=10)
    # ax.set_title(f'CV across time within {date} (Aggregated by {aggregate_timeframe}min)',fontsize = 15)
    # ax.set_xlabel('time(yy-mm-dd hh:00:00)',fontsize = 10)
    # ax.set_ylabel('CV',fontsize = 10)
    # ax.grid(True)
    # ax.set_ylim(0,2)
    # ax.set_yticks(np.arange(0, 2, 0.1))
    # plt.xticks(rotation=15)  # Rotate x-axis labels for better readability
    # ax.xaxis.set_major_formatter(DateFormatter("%y-%m-%d %H:%M:%S"))
    # ax.xaxis.set_major_locator(dates.HourLocator(byhour=range(0,24,6)))

    # plot1_dir = os.path.join('./02 fig/03_1 CV_across_time',f'{aggregate_timeframe}min')
    # ## exist_ok=True: is it okay if the directory already exists? 'True' means okay, and since the directory is already exists, nothing happens.
    # os.makedirs(plot1_dir, exist_ok=True)
    # plt.savefig(os.path.join(plot1_dir, f'CV across time_{date}.png'))
    
    # Plot 2: CV across flow-rates
    fig, ax = plt.subplots(1,3,figsize=(18,6))
    ax[0].scatter(mean_flow, cv_flow, s=10)
    ax[0].set_title(f'CV across mean flow within {date} (Aggregated by {aggregate_timeframe}min)',fontsize = 15)
    ax[0].set_xlabel('mean flow(vphpl)',fontsize = 20)
    ax[0].set_ylabel('CV',fontsize = 20)
    ax[0].grid(True)
    ax[0].set_ylim(0,2)
    ax[0].set_yticks(np.arange(0, 2, 0.2))
    # ax[0].set_xlim(0,2500)

    # Plot 2: CV across density
    ax[1].scatter(mean_density, cv_density, s=10)
    ax[1].set_title(f'CV across mean density within {date} (Aggregated by {aggregate_timeframe}min)',fontsize = 15)
    ax[1].set_xlabel('mean density(vpmpl)',fontsize = 20)
    ax[1].set_ylabel('CV',fontsize = 20)
    ax[1].grid(True)
    ax[1].set_ylim(0,2)
    ax[1].set_yticks(np.arange(0, 2, 0.2))
    # ax[1].set_xlim(0,40)

    # Plot 3: CV across speed
    ax[2].scatter(mean_speed, cv_speed, s=10)
    ax[2].set_title(f'CV across mean speed within {date} (Aggregated by {aggregate_timeframe}min)',fontsize = 15)
    ax[2].set_xlabel('mean speed(mph)',fontsize = 20)
    ax[2].set_ylabel('CV',fontsize = 20)
    ax[2].grid(True)
    ax[2].set_ylim(0,2)
    ax[2].set_yticks(np.arange(0, 2, 0.2))
    ax[2].set_xlim(0,80)

    plot2_dir = os.path.join('./02 fig/03_2 CV_across_flow',f'{VDS_num}',f'{aggregate_timeframe}min')
    os.makedirs(plot2_dir, exist_ok=True)
    plt.savefig(os.path.join(plot2_dir, f'CV across mean_{date}.png'))


# +
"""
This is the plot of average flow and speed over time for every day.
"""

def plot_within_day_flow(traffic_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num):
    
    # 1st Plot: Time vs Traffic Flow and Avg Speed
    
    fig, ax = plt.subplots(1,1, figsize=(6,6))   
    color_dict = ['red','blue','black','green','yellow','purple']
    
    for idx, lane in enumerate(lane_num):
        ax.plot(plot_date, traffic_day[f'flow_{lane}'], label = f'lane {lane}',linewidth=0.8 , color=color_dict[idx])
    
    # Configure x-axis ticks and labels
    x_ticks = range(0, 1440, 60)
    x_labels = range(0, 24, 1)
    ax.set_xticks(ticks=x_ticks, labels=x_labels, fontsize=9)
    ax.locator_params(axis='x', nbins=25)
    ax.legend(fontsize = 13)
    
    # Set plot title and labels
#     ax.set_title(f'Flow Rate Trends for Each Lane Over a Day',fontsize=13)
    ax.set_ylabel('Flow rates (vphpl)', fontsize=13)
    ax.tick_params(axis='y')
    ax.set_xlabel('Time (hour)', fontsize=13)
    ax.set_ylim(0,3600)
    ax.set_yticks(range(0,3600,200))
    
    ax.grid(True)

    directory_path = os.path.join('./02 fig/11 Unit time_flow',f'{VDS_num}')
    os.makedirs(directory_path, exist_ok=True)
    
    plt.savefig(f'{directory_path}/{date}_flow_{lane_num}.png')
    plt.close()


# +
# Parameters for handling the data
# raw_timeframe: Defines the timeframe unit in minutes for the input raw data 
# (e.g., 30 seconds is represented as 0.5 minutes).
raw_timeframe = 5

# path: The base directory path where the raw data files are stored.
path = '/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/01_BPR/11 Rawdata'

# directory: The subdirectory name under the main path where the data files are located.
directory = '5min'

# VDS_num: The subdirectory name under the main path where the data files are located.
# ['1203481','1203506','1214006','1205583','1205572','1212611','1205541'],
VDS_num = '1203481'

# Constructs the full path to the directory containing the data files.
full_path = os.path.join(path, directory, VDS_num)

# Retrieves a list of all files in the specified directory.
# This list will be used to iterate over or reference the data files for processing.
file_list = [f for f in os.listdir(full_path) if f.endswith('.xlsx')]

# total_lane_raw: Total number of lanes at the rawdata
# lane_num: Specifies the range of lane numbers to be analyzed.
# This is used to filter or segment the data based on lane information.

# total_lane_raw = 4
c_lane_num = {
    '1212611':[1,2,3,4,5,6], '1205572':[1,2,3,4,5,6], '1205583':[1,2,3,4,5,6],
    '1203506':[1,2,3,4], '1214006':[1,2,3,4], '1205541':[1,2,3,4],
    '1203589':[1,2,3,4], '1203615':[1,2,3,4], '1203524': [1,2,3,4], '1203481': [1,2,3,4]
}


lane_num = c_lane_num[VDS_num]

Day_list = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

# Printing the list of files found in the specified directory.
print("Files in the specified directory:", file_list)

# +
# 'cv_case1': calculate the total traffic volume for each lane, and calculate CV
# 'cv_case2': calculate the cv for each time frame and calculate the average value.

# Generate the column names dynamically based on lane_num
columns = ['date', 'year']
columns += [f'daily_flow_{lane}' for lane in lane_num]
columns += [f'daily_density_{lane}' for lane in lane_num]
columns += ['cv_flow_day', 'cv_density_day', 'cv_speed_day', 'cv_flow_day_v2','cv_density_day_v2','over_speed_ratio','detector_health']

# Create the DataFrame with the dynamically generated column names
df_daily_measure = pd.DataFrame(columns=columns)

for i, file_name in enumerate(file_list):
    print(file_name)
    
    # Step 0: uploading data and unifying rawdata's format
    cv_threshold = 0.123
    # speed_boundary: 90mph
    speed_bound = 90
    # unit: minute
    # aggregate_timeframe = 5
    aggregate_timeframe = 5
    num_frame = aggregate_timeframe/raw_timeframe
    
    date = file_name[-11:-5]
    
    rawdata = rawdata_setting(directory,VDS_num,file_name,lane_num)

    if rawdata.shape[0] == 0:
        continue
    else:
        Day = Day_list[int(rawdata.loc[0,'time'].weekday())]
    #     # Step 1: aggregate data to plot or calculate the data
        traffic_within_day, plot_date = aggregate_rawdata(rawdata, aggregate_timeframe, raw_timeframe, date, lane_num, VDS_num)

        # Step 1-1: upload saved file
        # with open(f'./01_BPR/12 python file/{VDS_num}/traffic_within_day_{date}_{aggregate_timeframe}aggmin_{lane_num}.p', 'rb') as file:
        #     traffic_within_day = pickle.load(file)

        # with open(f'./01_BPR/12 python file/{VDS_num}/plot_date_{date}_{aggregate_timeframe}aggmin.p', 'rb') as file:
        #     plot_date = pickle.load(file)

        # step 2: calculate daily performance
        over_speed_ratio = len(traffic_within_day[traffic_within_day['speed'] > speed_bound])/len(traffic_within_day)
        detector_health = len(traffic_within_day[traffic_within_day['cv_flow']<=cv_threshold])/len(traffic_within_day['cv_flow']) * 100

        cv_flow_day, cv_density_day, cv_speed_day, cv_flow_day_v2, cv_density_day_v2, daily_flow, daily_density = cv_calculation(traffic_within_day, lane_num, date, time = rawdata['time'],raw_timeframe=raw_timeframe, plot_whyCV = False, plot_time = True, plot_flow = True)

        insert = [[date, f'20{date[0:2]}',*daily_flow.tolist(),*daily_density.tolist(), cv_flow_day,cv_density_day, cv_speed_day, cv_flow_day_v2, cv_density_day_v2, over_speed_ratio, detector_health]]

        df_daily_measure = pd.concat([df_daily_measure, pd.DataFrame(insert, columns=df_daily_measure.columns)], ignore_index=True)

        # step 3: plot the graph
        plot_within_day(traffic_within_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num)
        plot_within_day_flow(traffic_within_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num)
    #     etc: plot using traffic_within_day to explain why CV is necessary
        variable = 'flow'
        # plot_why_CV(traffic_within_day, date, variable, lane_num)

        plot_CV_within_day(traffic_within_day, rawdata, date, aggregate_timeframe, VDS_num)


    # with open(f'./12 python file/df_daily_measure_{VDS_num}.p', 'wb') as file:    # james.p 파일을 바이너리 쓰기 모드(wb)로 열기
    #      pickle.dump(df_daily_measure, file)

    df_daily_measure.to_csv(f'./01_BPR/14 Dataquality_check_result/Data_quality_check_{VDS_num}.csv')
# -

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






