# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: base
#     language: python
#     name: python3
# ---

# %% [markdown] editable=true slideshow={"slide_type": ""}
#
# <div class="alert alert-warning">
#     
# - Blue: notes (info) | White: slides | Green: main(success) | Red: past versions(danger)
# - Generally, the presentation follows <font size = 5> slides -> main text -> personal notes ->  code </font> in each subsection (Outline only appear at the beginning of each section, some subsections may not have personal notes or codes)
#     
# </div>
#     

# %% [markdown]
# <p style="font-size: 25px;"> Weekly meeting </p>
#
# - [weekley meeting collection](https://github.com/jooneui/BPR/blob/main/.ipynb_checkpoints/Weekly_meeting_BPR_function-checkpoint.ipynb)

# %% [markdown]
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

# %% [markdown]
# __6/24/2025 Agenda__
# - PELT method application
# - Our research contribution
# - Fixed peak-period: non free-flow travel times in the low demand

# %% [markdown]
# # Introduction

# %% [markdown]
# ## The importance of Volume-Delay function(VDF)
# - VDF is a critical component of traffic assignment, quantifying travel time caused by observed volume and road capacity(Kucharski and Drabicki 2017)
# - VDF establishes the relationship between travel time, road traffic volume, and dynamic traffic state (Branston 1976; Nie and Zhang 2005; Patriksson 2015)
# - Accurate estimation and calibration of the current traffic demand and supply are crucial in identifying and addressing congested or oversaturated conditions (Yuyan Pan et al. 2023)

# %% [markdown]
# ## BPR function
# - The Bureau of Public Roads (BPR), Davidson’s, Akcelik’s, and conical delay functions are the most commonly used link cost functions.
# - The BPR function has profound applications in transportation planning primarily as a result of its simple mathematical form, easily observable field inputs, and consistent performance (Mtoi and Ren, 2014; Das and Rama Chilukuri, 2020)
# - BPR function: $t=t_0(1+\alpha(\frac{N}{C})^\beta)$
#     - $\alpha$ is the scale parameter
#         - how the congestion effects change when the capacity is reached(Spiess, 1990)
#     - $\beta$ is a shape parameter

# %% [markdown]
# ## Problem Statement
#
# - ① BPR has not adequately incorporated fundamental diagrams(FD)
#     - BPR function
#         - $\bar{t}=\frac{1}{\bar{v}}=t_0[1+\alpha(\frac{N}{C})^\beta]$ ($N=qT$)
#     - Triangular F.D.
#         - $\bar{t} = \begin{cases} \frac{1}{\mu} \text{  (if  } k < k_c) \\ \frac{Tk_j}{N} - \frac{1}{\omega} \text{  (if  } k > k_c) \end{cases}$ [Appendix 1]
#     - Simply employing $N/C$ in the BPR fails to accurately depict the shape of FD

# %% editable=true slideshow={"slide_type": ""}
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

# %% [markdown]
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

# %% [markdown]
# - __해당 부분 정리 필요!!__

# %% [markdown]
# ## Objective

# %% [markdown]
# 지금은 git을 위한 시간

# %% [markdown]
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

# %% [markdown]
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

# %% [markdown]
# # Contribution

# %% [markdown]
# - Yuyan Pan et al. (2022) reviewed VDFs: and checked various definitions of demand variables for congested conditions.
# - Wu et al. (2022) used the same concept of our research (demand: the total volume during the congested period), and assume this demand is originally intended for the most peak-hour, and showed this pattern using empirical data
#     - Even if assuming $W$ as one peak hour may not be realistic, our current empirical study does not include the determination of $W$. So I'm trying to clarify what the main contribution of this study actually is.
# <img src="./02_1_presentation_fig/VDF_review_demanddef.png" width=70%>
# - [The link to the Wu et al. (2022)](https://www.notion.so/2020-Xin-Burce-Wu-Characterization-and-calibration-of-volume-to-capacity-ratio-in-volume-delay-fun-16618fce4e52801b9e7fd9e9ec7b01b7)

# %% [markdown]
# # Methodology

# %% [markdown]
# ## Pipeline

# %% [markdown]
# - The API(clearhouse) provides rawdata, but g-factor is not provided.
# - The rawdata includes flowrate and speed, so I calculate the density by flowrate/speed

# %% [markdown]
# <center> <img src='./02_1_presentation_fig/1_pipeline.png' width = "70%"> </center>

# %% [markdown]
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

# %% [markdown]
# <div class="alert alert-info">
#
# __Line-based Segmentation__
#
# In this study, we identify uncongested periods by segmenting daily speed (or cumulative speed) profiles into approximately linear intervals. We apply changepoint detection to the speed profile because it provides the most distinct and physically meaningful signal for identifying regime transitions. In contrast, flow and density (or occupancy) each present limitations. Flow is non-unique—the same flow rate can appear in both uncongested and congested states—making it difficult to determine whether a given segment corresponds to free flow or congestion. Density, while unique across regimes, fluctuates even within uncongested periods, which prevents changepoint algorithms from precisely detecting the true transition boundary between regimes. Speed, by comparison, remains nearly constant during free flow and changes sharply at the onset or dissipation of congestion, allowing for more accurate and interpretable segmentation.
#
# To perform the segmentation, we use two widely adopted algorithms in parallel: PELT (Pruned Exact Linear Time) and RDP (Ramer–Douglas–Peucker). The following subsection describes how each method is applied to the daily speed profiles.
#
# - RDP and PELT explanation is in TRB2026 paper

# %% [markdown]
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

# %% [markdown]
# <center> <img src='./02_1_presentation_fig/2_Period_def.png' width = "50%"> </center>

# %% [markdown]
# <center> <img src='./02_1_presentation_fig/2_uncongested_ambiguous_cases.png' width = "40%"> </center>

# %% [markdown]
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

# %% [markdown]
# <div class="alert alert-info">
# adfa
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

# %% [markdown]
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

# %% [markdown]
# # Data Description

# %% [markdown]
# ## I-5

# %% [markdown]
# - \2024. Jan. 1st ~ Aug.27th
# - <img src='./02_1_presentation_fig/3_VDS_location.png' width=80%>
# - Roughly 1.1mile

# %% [markdown]
# ### Speed patterns

# %% [markdown]
# - From right to left, the VDSs are numbered 1 to 5.
#     - VDS 1 is the least congested.
#     - VDS 2 and 3 experience the heaviest congestion.
#     - When congestion becomes severe, the queue extends into VDS 4 and 5.
#         - VDS 4 and 5 generally have shorter congested periods and smaller speed drops than VDS 2 and 3, forming a triangular pattern.
#         - However, under very severe congestion, VDS 5 shows a larger speed drop despite a shorter congestion duration.
#         - My interpretation is that in a 4-lane section (compared to a 6-lane one), VDS 5 is more prone to collapse once congestion occurs.

# %% [markdown]
# - <img src='./02_1_presentation_fig/I-5_Buenapark.png' width=60%>
# - Period: total __245__
#     - Jan. ~ Oct. 2011

# %% [markdown]
# ## SR-91

# %% [markdown]
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

# %% [markdown]
# # Speed-Based Detection of Peak Periods and Estimation of BPR Functions

# %% [markdown]
# ## Methodology

# %% [markdown]
# ### Ramer–Douglas–Peucker (RDP) Algorithm

# %% [markdown] editable=true slideshow={"slide_type": "subslide"}
# - **Objective:**  
#     - To simplify a curve (a sequence of connected points) by reducing the number of points while preserving the overall shape within a specified tolerance.
#
# - **Concept**
#     - The RDP algorithm identifies and retains **key points (corners or bends)** that are critical to the shape of the curve.
#     - Intermediate points that lie within a user-defined distance (**epsilon, ε**) from a straight-line approximation are discarded.

# %% [markdown] editable=true slideshow={"slide_type": "skip"}
# #### RDP threshold value reference
# - Original RDP studies are was for **image processing (Ramer)** and **geography contour line(Douglas and Peuker)**
#     - Ramer (1972): approximate the curves extracted from images
#     - Douglas and Peuker (1973): digitizing geographic features (coastlines, contours)
#     - so, x-axis and y-axis have the same unit, perpendicular distance has a same unit.
#     - And their purpose was to keep the geometry/visual shape with the minmum number of points to decrease compuatational time/space.

# %% [markdown] editable=true slideshow={"slide_type": "skip"}
# ##### Threshold values
# - Their approach for the threshold was a bit different from our study
#     - Their focus is not on detecting some specific characteristic, but on finding the values that can maintain the general shape with the small number of points. Because of that, most of the studies that they applies is based on the heuristic.
#     - Both studies suggest the limitation that the tolerance must be chosen manually.
#     - Ramar (1972): sensitivity analysis based on the tolerance from 1~5 gridpoints(pixel) in the image
#     - Douglas and Peuker (1973): mention the tolerance should be application-dependent
#         - map scale, positional accuracy of GPS (larger than the accuracy error to eliminate the artifacts)   
# - Many other studies' applications are mostly about the RDP visual image(maps, digitized medical images, object contours), so they used the perpendicular distance. 

# %% [markdown] editable=true slideshow={"slide_type": "skip"}
# - However, in our study, we have a temporal constraint
#     - In our study, we want to segment the curve with the lines that accurate represent the curve, but the accuracy means time-dependent, not just geometric shape.
#     - We want to have an accurate values for each time between the segment and actual pattern.
#     - The vertical deviation directly measures "how wrong" the estimated travel time would be.

# %% [markdown] editable=true slideshow={"slide_type": "skip"}
# - Peque et al. (2019). use the vertical distance.
#     - Travel time curve (travel time vs. time of day) as a polyline
#     - Draw linear interpolation and calculate the vertical distance from each point.
#     - The vertical distance (y-axis difference) is the natural error measure.
#         - It directly means: “how wrong is my predicted travel time at this specific time?”
#         - This matches their application: keeping travel times accurate at every time step.

# %% [markdown]
# #### RDP threshold in this study

# %% [markdown]
# ### PELT method

# %% [markdown]
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

# %% [markdown]
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

# %% [markdown]
# ### Segmentation setting

# %% [markdown]
#
# <img src='./02_1_presentation_fig/changepoint_logic.png' width=70%>   

# %% [markdown]
# #### RDP & PELT
# - **Start:** Point where the distance slope changes — congestion start at $\tau_m$.  
# - **End:** The cumulative profile is discrete, adding the next speed value at each step.  
#     - If the point after $\tau_{m+1}$ ($\tau_{m+1} + 1$) is at free-flow speed, the slope from $\tau_{m+1}$ reflects free-flow conditions.
#     - The congestion end changepoint: $\tau_{m+1}+1$

# %% [markdown]
# ## Peak-period detection Result

# %% [markdown]
# - Case1) Speed threshold-based
#     - peak period: A period if the speed stays below the _'speed_upper_bound'_ for at least _'min_minutes'_, allowing up to _'max_outliers'_:
#         -  speed_upper_bound=40mph, min_minutes=90min, max_outliers = 7 
# - Case2) PELT
# - Case3) RDQ
# - Case4) Derivative-based: The concept is similar to PELT, so not deploy it.

# %% [markdown]
# - I explained RDP logic, and we determined to use constant parameters.
# - Compare the how congestion boundaries are similar between PELT vs RDP

# %% [markdown] editable=true slideshow={"slide_type": "subslide"}
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
# <img src="./02_1_presentation_fig/RDP_process.png" width=90%>

# %% [markdown]
# ### Parameter setting
# - RDP: 12miles
# - PELT: 2500 $(mph)^2$

# %% [markdown]
# ### RDP vs PELT

# %% [markdown]
# - SR-91: total __307__ days
#     - Jan. ~ Apr., Aug.~Oct. 2011,
#     - Aug., Sep., . 2012
#     - Sep., Oct., 2023
#     - Jan., 2024
# - I-5: total __245__ days
#     - Jan. ~ Oct. 2011 

# %% [markdown]
# | Case | Description                          | SR-91 (VDS: 1203506)            |          | I-5 (VDS: 1205583)                |          |
# |------|--------------------------------------|---------------------|----------|---------------------|----------|
# |      |                                      | # of periods        | %        | # of periods        | %        |
# | 1    | Start and duration match exactly      | 221                | 55.0%    | 131                   | 58.7%     |
# | 2    | Start and duration differ by ≤ 30 min | 151                 | 37.6%    | 80             | 35.9%    |
# | 3    | All other cases                       | 30                | 7.5%     | 12                   | 5.4%     |
#

# %% [markdown]
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

# %% [markdown]
# ### Manual check based on random sampling

# %% [markdown]
# - Many samples (days) are taken up by uncongested days.
# - Comparing PELT and RDP, RDP tends to cover a slightly wider range.
#     - Personally, I think RDP represents the peak more clearly and captures the start and end of congestion more accurately.
#     - With a smaller m in PELT, the section is captured to some extent.
#     - However, lowering m also makes PELT pick up very small fluctuations, which keeps the detected values high.
#     - Because RDP uses cumulative speed, it’s less sensitive to short fluctuations and produces more stable results overall.

# %% [markdown]
# | Case | Description                          | SR-91 (VDS: 1203506)            |          | I-5 (VDS: 1205583)                |          |
# |------|--------------------------------------|---------------------|----------|---------------------|----------|
# |      |                                      | # of periods        | %        | # of periods        | %        |
# | 1a    | Both as an uncongested day      | 8                | 19.5%    | 18                  | 61.3%     |
# | 1b    | Start and duration match exactly      | 12                | 29.3%    | 3                   | 9.7%     |
# | 2    | Start and duration differ by ≤ 30 min | 15                 | 36.6%    | 7             | 19.4%    |
# | 3    | All other cases                       | 6                | 14.6%     | 2                  | 9.7%     |

# %% [markdown]
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

# %% [markdown]
# #### (Script, 25/11/11)

# %% [markdown]
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
# <img src="./02_1_presentation_fig/1_mid_plateau.png" width=80%>
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

# %% [markdown]
# #### Previous discussion but not valid anymore

# %% [markdown]
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

# %% [markdown]
# #### VDS_num: 1205583 (25/7/22)

# %% [markdown]
# - (25/7/22)
# - Peak-period detection
#     - Divide the peak period well, including the buildup/dissipation process.
#         - Unlike my previous approach, which directly selected the peak period, this method includes the buildup and dissipation phases based on whether speeds fall below a specified upper threshold. 
#     -  <img src='./02_1_presentation_fig/RDP_good.png' width=80%>

# %% [markdown]
# - Disscussion
#     - Speeds have many ups-and-down (8/11/2011)
#     - Temporary uncongested periods between congested states: should we regard it as one peak-peak period or two? (8/8/2011, 7/18/2011)
#         - Our approach first detects off-peak periods as sustained near free-flow speeds over a certain duration. The remaining times are then classified as peak periods. This means that short uncongested intervals between two peak periods are also labeled as peak, since they likely reflect temporary dips in congestion rather than true off-peak conditions. I include these intervals as part of the peak period, considering that queues may build up or dissipate across peak periods, and point sensors might briefly register uncongested conditions even during sustained congestion.
#     - <img src='./02_1_presentation_fig/RDP_discussion.png' width=70%>

# %% [markdown]
# #### VDS: 1203506 (25/7/22)

# %% [markdown]
#
# - The trend is more versatile.
# - <img src='./02_1_presentation_fig/RDP_1203506_good.png' width=100%>

# %% [markdown]
# - __(Discussion1)__ By using the cumulative profile, the temporary spark is not regarded as peak-period: I think that is logical.
# - <img src='./02_1_presentation_fig/RDP_123506_temporaryspark.png' width=60%>

# %% [markdown]
# - __(Discussion2: Two-peaks in the afternoon)__ Some days have two peak periods in the afternooon.
# - <img src='./02_1_presentation_fig/RDP_123506_twopeaksinafternoon.png' width=60%>

# %% [markdown]
# - __(Discussion3: Congestion at night)__
# - <img src='./02_1_presentation_fig/RDP_123506_congestionatnight.png' width=60%>

# %% [markdown]
# - __(Discussion3: Congestion at night)__
#     - Controversial to define 16-20 as peak or off-peak: I can include them as off-peak, but their average is about 60mph, I think better to regard them as off-peak
# - <img src='./02_1_presentation_fig/RDP_123506_fluctuation.png' width=60%>

# %% [markdown]
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

# %% [markdown] editable=true slideshow={"slide_type": "subslide"}
# **8/18 discussion**
# - simplify the process of threshold setting
#     - engineering judgement,
#     - function of the average speed 

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ### (Code) Package install

# %%
import importlib
import sys

# Remove all traffic_utils submodules from sys.modules so they're fully reloaded
to_remove = [k for k in sys.modules if k.startswith('traffic_utils')]
for k in to_remove:
    del sys.modules[k]

# Re-import everything fresh
from traffic_utils import *      



# %% [markdown]
# ### Unified MASTER_CONFIG builder
# - Merges the existing `CONFIG_RC`, `CONFIG_BPR`, and `CONFIG_FD` dicts into one `MASTER_CONFIG`.
# - Edit this cell directly if you want to change VDS list, parameters, or toggle stages.
#

# %%
# Unified MASTER_CONFIG (manually merged from CONFIG_RC, CONFIG_BPR, CONFIG_FD)
# Edit this cell directly to change parameters, VDS lists, or paths.
# Old individual config cells are preserved further down for reference.

MASTER_CONFIG = {   
    # 0. VDS and spatial scope settings
    # 'VDS_list': ['1203481','1203506'],  # used only when spatial_scope == 'single'
    'VDS_list': [
                '1203481','1203506','1214006','1205583','1205572','1212611', # original 
                '1212001', '1212115', '1212216', '1205432', #I-5 N
                '1205175','1204924', # I5 NB additional VDSs for sensitivity testing
                '717112','717101', '717249', # I-10W VDSs
                '718496', '774204', # SR-134W
                '761003', '760987',  # SR-134E
                '761851', '717972' # I710S
                 ],
    # 'VDS_list': ['1214006','1205583','1205572','1212611','1203481','1203506'],  #,'1203481','1203506','1205572','1205541'  # used only when spatial_scope == 'multi_vds'
    # 'VDS_list': ['C1'],  
    'spatial_scope': 'single',
    'temporal_scale': 'speedbasedpeak', # entireday, hour, speedbasedpeak, peak
    # C1 or PeMS
    'data_format': 'raw', # 'raw' or 'section_combined'
    'section_combined_params': {
        'filename': 'Detector_276days.csv',
        'speed_unit': 'kmh',   # 'mph' = keep native units; 'kmh' = convert to mph
        'direction_filter': 1,
        'section_filter': list(range(1,6)),
        'volume_to_flow': 12,  # veh/5min -> veh/hr
        'date_format': '%Y%m%d',
    },

    'network_data_path': './01_1_BPR_network/C1data',
    'network_directions': {1: 'C1_D1', 2: 'C1_D2'},
    'network_aggregation': 'bidirectional',

    'period_include': {'speedbasedpeak': ['morning-peak', 'afternoon-peak'], 'hour': ['off-peak'], 'entireday': ['off-peak']},
    'VDS_label_list': {
        # Nested by corridor → {vds_id: label}; _flatten_vds_labels() flattens for downstream use
        'SR91':   {'1203481': 'SR91-WB',  '1203506': 'SR91-EB'},
        'I5-SB': {'1214006': 'I5 SB-1', '1205583': 'I5 SB-2', '1205572': 'I5 SB-3', '1212611': 'I5 SB-4'},
        'I5-NB': {'1212001': 'I5 NB-1', '1212115': 'I5 NB-2', '1212216': 'I5 NB-3', '1205432': 'I5 NB-4','1205175':'I5 NB-5','1204924':'I5 NB-6'},
        'I10-WB':  {'717112': 'I10 WB-1', '717101': 'I10 WB-2', '717249' : 'I10 WB-3'},
        'SR134-WB': {'718496': 'SR-134W-1', '774204': 'SR-134W-2'},
        'SR134-EB': {'761003': 'SR-134E-1', '760987': 'SR-134E-2'},
        'I710-SB': {'761851': 'I710S-1', '717972': 'I710S-2'}
        # Flat dict still works too: {'1203481': 'SR91-WB', ...}
        },
        # 'multi_vds': 'I-5 Network',
        # C1 labels auto-generated as 'C1 S{sec} D{dir}' by pipeline

    'corridor_groups': {
        'SR91':   ['1203481', '1203506'],
        'I5-SB': ['1214006', '1205583', '1205572', '1212611'],
        'I5-NB': ['1212001', '1212115', '1212216', '1205432','1205175','1204924'],
        'I10-WB':  ['717112', '717101', '717249'],
        'SR134-WB': ['718496', '774204'],
        'SR134-EB': ['761003', '760987'],
        'I710-SB': ['761851', '717972']
    },
    'corridor_grid_ncols': 2,   # max columns per corridor sub-grid

    'path': '.',
    'dir': '5min',
    'raw_timeframe': 5,
    'aggregate_timeframe': 5,
    'Day_list': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],    
    'lane_map': {
        '1212611': [1,2,3,4,5,6], '1205572': [1,2,3,4,5,6], '1205583': [1,2,3,4,5,6],
        '1203506': [1,2,3,4], '1214006': [1,2,3,4], '1205541': [1,2,3,4],
        '1203589': [1,2,3,4], '1203615': [1,2,3,4], '1203524': [1,2,3,4], '1203481': [1,2,3,4],
        '1212001': [1,2,3,4], '1205409': [1,2,3,4], '1212115': [1,2,3,4], '1212216': [1,2,3,4,5], '1205432': [1,2,3,4],
        '717112': [1,2,3,4],'717187': [1,2,3,4], '717249': [1,2,3,4], '716088': [1,2,3,4], '717101': [1,2,3,4],
        '1205175':[1,2,3,4,5],'1204924':[1,2,3,4,5], # I5 NB additional VDSs for sensitivity testing
        '718496':[1,2,3,4], '774204':[1,2,3,4], # SR-134W
        '761003':[1,2,3,4], '760987':[1,2,3,4],  # SR-134E
        '761851':[1,2,3,4,5,6], '717972':[1,2,3,4,5,6] # I710S
        # '1212216':[1,2,3,4,5],'1212115':[1,2,3,4],'1212001':[1,2,3,4],'1205432':[1,2,3,4],'1205409':[1,2,3,4]
    },
    
    
    # 1. Data processing
    'missing_ratio': 0.03,
    'interpolate_missing': True,
    ## need to implement "interpoation"

    # 2. Peak detection
    'method': 'RDP_v',
    'congest_method': 'speed-solely',
    
    # 'min_off_len': 90,
    # 'min_peak_len': 0,
    # 'pelt_min_length': 5,
    # 'speed_upper': 70,
    # 'speed_gap_threshold': 10,
    'peak_periods': {'morning': (0, 820), 'afternoon': (720, 1440)}, # when 'temporal_scale' is 'peak' it refers to fixed-window labeling

    # NOTE: free_tt_offpeak_avg is now auto-derived as 60 / offpeak_ff_speed_threshold.
    # Keep speedbased_params.offpeak_ff_speed_threshold as the canonical free-flow speed (mph).
    'speedbased_params': {
        'pelt_min_length': 5,
        'min_off_len': 90,
        'min_peak_len': 0,
        'speed_upper': 60,
        'speed_gap_threshold': 15,
        'offpeak_ff_speed_threshold': {
            '1203481': 54,'1203506': 54, '1203524': 54, 
            '1212611': 57, '1205572': 57, '1205583': 57, '1214006': 57,
            '1212001': 55, '1205409': 55, '1212115': 55, '1212216': 55, '1205432': 55,
            '717112': 54, '717101': 52, '717187': 54, '717249': 52,'716088': 52,
            'multi_vds': 57,
            'C1': 55/1.6,  # <-- fallback for C1
            # Per-section thresholds (compute via compute_bpr_ff_speed_thresholds):
            'C1_S1_D1': 35, 'C1_S2_D1': 31, 'C1_S3_D1': 20, 'C1_S4_D1': 25, 'C1_S5_D1': 34,
        },
        'occ_threshold': {'C1': {'occ_l': 0.1, 'occ_h': 0.3}},
        'FD_phase': 'three_phases',
        # 'freeflow_speed': 70,
        'freeflow_speed_epsilon': 5,
        'pelt_penalty': 100,
    },
    
    # 3. Recurrent analysis
    'drop_nonrecurrent_days': True,
    'recurrent_output_path': None,
    'drop_multiplecongestion_days': False,
    'no_peak_eligibility_threshold': 1.0,  # facets with > 50% no-peak days are skipped in Stage 2 (default: 1.0 = keep all facets): 현재 eligibility 확인이 day of week별로 되어있는 것 같다. 오전, 또는 오후 전체 적용하도록 설정필요
    'save_eligibility_log': True,           # save eligibility_log CSV to 05_recurrent_peak_result/
    'recurrent_method': 'RDP_v',       # 'simpleband', 'shortest_interval', 'PELT', 'RDP_v'
    'segment_min_weeks_by_period': {'morning-peak': 3, 'afternoon-peak': 3},
    'recurrent_method_params': {   'simpleband': {   'selector_by_period': {'morning-peak': 'start_only', 'afternoon-peak': 'end_only'},
                                                     'start_bandwidth_minutes_by_period': {'morning-peak': 60, 'afternoon-peak': 240},
                                                     'end_bandwidth_minutes_by_period': {'morning-peak': 240, 'afternoon-peak': 60}},
                                                    #  'start_bound_mode_by_period': {'morning-peak': 'two_sided', 'afternoon-peak': 'two_sided'},
                                                    #  'end_bound_mode_by_period': {'morning-peak': 'upper_only', 'afternoon-peak': 'two_sided'}},
                                   'shortest_interval': {   'selector_by_period': {'morning-peak': 'start_only', 'afternoon-peak': 'end_only'},
                                                            'start_q_by_period': {'morning-peak': 0.9, 'afternoon-peak': None},
                                                            'end_q_by_period': {'morning-peak': 0.95, 'afternoon-peak': 0.9},
                                                            'coverage_by_period': {'morning-peak': None, 'afternoon-peak': None}},
                                                            # 'start_bound_mode_by_period': {'morning-peak': 'two_sided', 'afternoon-peak': 'two_sided'},
                                                            # 'end_bound_mode_by_period': {'morning-peak': 'two_sided', 'afternoon-peak': 'two_sided'}},
                                   'RDP_v': {
                                                    'epsilon_start_by_period': {'morning-peak': 0.3, 'afternoon-peak': 0.2},
                                                    'epsilon_end_by_period': {'morning-peak': 0.2, 'afternoon-peak': 0.3},
                                                    # 'segment_min_weeks_by_period': {'morning-peak': 2, 'afternoon-peak': 2},
                                                    'selector_by_period': {'morning-peak': 'both', 'afternoon-peak': 'both'},
                                                    'fixed_var_by_period': {'morning-peak': 'start_hour', 'afternoon-peak': 'end_hour'},  # morning: fixed=start_hour; afternoon: fixed=end_hour
                                                    'second_var_by_period': {'morning-peak': 'end_hour', 'afternoon-peak': 'start_hour'}}},
                                                    
                                                    
    # 4. BPR calibration
    'segment_aggregation': True,
    'drop_days_weird_peak_times': False,
    'filer_mode': False,
    'morning_earliest': '00:00',
    'afternoon_latest': '24:00',
    
    'dayofweek_exclude': [],
    'month_exclude': [],
    'year_exclude': [],
    'free_tt_mode': 'fixed',
    'free_tt_method': 'offpeak_avg',

    # BPR-specific free-flow speed threshold (Step 3 only).
    # Compute once with compute_bpr_ff_speed_thresholds() and paste here.
    'bpr_ff_speed_threshold': {
        # Example (auto-computed from 0-3am + 22-24 off-peak flow-weighted harmonic mean):
        '1203481': 68,
        '1203506': 66,
        '1214006': 67,
        '1205583': 70,
        '1205572': 70,
        '1212611': 69,
        '1212001': 67, '1205409': 66, '1212115': 66, '1212216': 70, '1205432': 67,
        '717112': 66,'717187': 65, '717249': 65,'716088': 70,'717101': 68,
        '1205175':69,'1204924':70, # I5 NB additional VDSs for sensitivity testing
        '718496':67, '774204':67, # SR-134W
        '761003':67, '760987':66,  # SR-134E
        '761851':65, '717972':66, # I710S
        # Per-section thresholds for C1 (computed via compute_bpr_ff_speed_thresholds):
        'C1_S1_D1': 40, 'C1_S2_D1': 38, 'C1_S3_D1': 25, 'C1_S4_D1': 28, 'C1_S5_D1': 40,
    },
    
    'save_dir': './02 fig/16 FD',
    'bpr_save_dir': './02 fig/12 Daily BPR',
    'rc_save_dir': './02 fig/17 recurrent_checks',
    'file_path': '/Users/jooneuihong/Library/CloudStorag /OneDrive-UCIrvine/14 Github/01_BPR',
    'W_minutes' : 60,

    'plots': {
        # Stage 1 - peak detection
        'plot_speed_breakpoints':      True,
        'plot_peak_detection':         True,
        'plot_free_flow_speed_dist':   True,
        # Stage 2 - recurrent analysis
        'save_recurrent_checks':       True,
        'plot_fundamental_diagram':     True,
        'plot_recurrent_histogram':    False,
        'plot_fd_phase_boundaries':    False,
        # Stage 3 - BPR calibration
        'plot_bpr_fit':                True,
        'plot_qq_residual':            False,
        'plot_demand_histogram':       False,
        'save_bpr_params_csv':         True,
    },
}



# %% [markdown]
# ### Stage 1 - Data Loading & Peak Detection
#

# %%
compute_bpr_ff_speed_thresholds(MASTER_CONFIG)

# %%
count_congested_days(MASTER_CONFIG)

# %%
run_full_pipeline(MASTER_CONFIG, stages=[2,3])


# %% [markdown]
# ### Stage 2 - Recurrent Analysis & Fundamental Diagram

# %%
run_full_pipeline(MASTER_CONFIG, stages=[3])



# %% [markdown]
# ### Stage 3 - BPR Fitting & Export
#

# %%
run_full_pipeline(MASTER_CONFIG, stages=[2,3])

# %% [markdown]
# ### BPR Scenario Comparison

# %%

# ─── Comparison engine — no edits needed below ───────────────────────────────

VAR_FORMATS = {
    'N':        '{:.0f}',
    'R-square': '{:.3f}',
    r'$\beta$': '{:.2f}',
}

def _fmt_table(df, var):
    fmt = VAR_FORMATS.get(var, '{:.4f}')
    return df.style.format(fmt)

def _sel_token(selector):
    return {'start_only': 'start', 'end_only': 'end', 'both': 'both'}.get(selector, selector)

def _param_token(param):
    if param is None:
        return None
    return str(int(param * 100) if isinstance(param, float) else int(param))

def _matches(filename, sc):
    fn = filename.lower()
    # Strip extension to check the true end of the filename
    name_no_ext = os.path.splitext(fn)[0]
    
    ts = sc.get('temporal_scale', '')
    if ts and ts.lower() not in fn:
        return False
    if sc.get('recurrent_method', '').lower() not in fn:
        return False

    # Check Morning/Afternoon selectors
    m_sel = _sel_token(sc.get('morning_selector', ''))
    if m_sel and f'morning_{m_sel}' not in fn:
        return False
    a_sel = _sel_token(sc.get('afternoon_selector', ''))
    if a_sel and f'afternoon_{a_sel}' not in fn:
        return False

    # Parameters: Get the tokens
    m_tok = _param_token(sc.get('morning_param'))
    a_tok = _param_token(sc.get('afternoon_param'))

    # Logic: If an afternoon param is provided, it MUST be at the end.
    # This prevents matching 's30_S1-36_D1.csv' when you only want 's30.csv'
    if a_tok:
        # Check if it ends with 's30' or just '30' (per your inconsistent naming)
        if not (name_no_ext.endswith(f's{a_tok}') or name_no_ext.endswith(a_tok)):
            return False
    elif m_tok:
        if not (name_no_ext.endswith(f's{m_tok}') or name_no_ext.endswith(m_tok)):
            return False
            
    return True

def _auto_label(sc):
    if 'label' in sc:
        return sc['label']
    method = sc.get('recurrent_method', '?')
    ts     = sc.get('temporal_scale', '')
    m_sel  = _sel_token(sc.get('morning_selector', ''))
    m_p    = sc.get('morning_param', '')
    lbl = f"{method[:3].upper()}|{m_sel}|{m_p}"
    if ts:
        lbl = f"{ts}|{lbl}"
    return lbl

def _find_col(df, var):
    for c in df.columns:
        if var.strip() == c.strip():
            return c
    for c in df.columns:
        if var.lower() in c.lower():
            return c
    return None

def compare_bpr_scenarios(scenarios, variables):
    search_dirs = list(dict.fromkeys([
        MASTER_CONFIG.get('bpr_save_dir', '.'),
        # MASTER_CONFIG.get('save_dir', '.'),
    ]))
    all_csvs = list(set(
        f for d in search_dirs
        for pattern in ['BPR_params_*.csv', 'BPR_*.csv']
        for f in glob.glob(os.path.join(d, pattern))
    ))
    if not all_csvs:
        print(f'No BPR CSV files found in: {search_dirs}')
        return
    print(f'Searching in: {search_dirs}  ({len(all_csvs)} CSV files found)')

    matched = {}
    for sc in scenarios:
        hits = [f for f in all_csvs if _matches(os.path.basename(f), sc)]
        hits = sorted(hits, key=os.path.getmtime, reverse=True)  # newest first
        lbl  = _auto_label(sc)
        if not hits:
            print(f'[WARNING] No file matched: {sc}')
        else:
            if len(hits) > 1:
                print(f'[WARNING] Multiple files matched [{lbl}] — using newest:')
                for h in hits:
                    import datetime
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(h)).strftime('%Y-%m-%d %H:%M')
                    print(f'   {mtime}  {os.path.basename(h)}')
            matched[lbl] = hits[0]

    if not matched:
        print('No scenarios matched any file.')
        return

    print('\nMatched files (newest used when multiple):')
    for lbl, fp in matched.items():
        import datetime
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%Y-%m-%d %H:%M')
        print(f'  [{lbl}]  {mtime}  {os.path.basename(fp)}')

    frames = {lbl: pd.read_csv(fp) for lbl, fp in matched.items()}

    for var in variables:
        slices = []
        for lbl, df in frames.items():
            col = _find_col(df, var)
            if col is None:
                print(f'[WARNING] "{var}" not found in [{lbl}]. Columns: {list(df.columns)}')
                continue
            tmp = df[['VDS', 'Peak-period', col]].rename(columns={col: lbl})
            slices.append(tmp)
        if not slices:
            continue

        tbl = slices[0]
        for s in slices[1:]:
            tbl = tbl.merge(s, on=['VDS', 'Peak-period'], how='outer')
        tbl = tbl.set_index(['VDS', 'Peak-period'])

        avg_row = tbl.mean(numeric_only=True).rename(('Average', ''))
        tbl_display = pd.concat([tbl, avg_row.to_frame().T.rename(index={0: ('Average', '')})])
        print(f'\n{"━" * 60}')
        print(f'  Variable: {var}')
        print(f'{"━" * 60}')
        display(_fmt_table(tbl_display, var))



# %%
# ═══════════════════════════════════════════════════════════════════════════════
# BPR Scenario Comparison
# ───────────────────────────────────────────────────────────────────────────────
# HOW TO USE
#   Step 1 – Edit COMPARE_SCENARIOS  (one dict per scenario you want to compare)
#   Step 2 – Edit COMPARE_VARIABLES  (column names from the BPR_params CSV)
#   Step 3 – Run this cell
# ═══════════════════════════════════════════════════════════════════════════════
import os, glob
import pandas as pd

# ─── Step 1: Scenarios ────────────────────────────────────────────────────────
# Fill in one dict per scenario. The code finds the matching CSV automatically.
#
# Keys
#   recurrent_method    : 'simpleband'  or  'shortest_interval'
#   morning_selector    : 'both'  |  'start_only'  |  'end_only'
#   afternoon_selector  : 'both'  |  'start_only'  |  'end_only'  (optional)
#   morning_param       : int   → bandwidth in minutes  (simpleband)
#                         float → quantile, e.g. 0.9    (shortest_interval)
#   afternoon_param     : same unit as morning_param     (optional)
#   label               : custom column label            (optional)

temp_scale = 'speedbasedpeak'  # 'entireday', 'hour', 'speedbasedpeak', or 'peak'

COMPARE_SCENARIOS = [
    # {
    #     'recurrent_method':   'simpleband',
    #     'morning_selector':   'start_only',
    #     'afternoon_selector': 'end_only',
    #     'morning_param':      1000,
    #     'temporal_scale':     temp_scale,
    # },
    {
        'recurrent_method':   'simpleband',
        'morning_selector':   'start_only',
        'afternoon_selector': 'end_only',
        'morning_param':      30,
        'temporal_scale':     temp_scale,
    },
    {
        'recurrent_method':   'simpleband',
        'morning_selector':   'start_only',
        'afternoon_selector': 'end_only',
        'morning_param':      60,
        'temporal_scale':     temp_scale,
    },
    {
        'recurrent_method':   'simpleband',
        'morning_selector':   'start_only',
        'afternoon_selector': 'end_only',
        'morning_param':      90,
        'temporal_scale':     temp_scale,
    },
    {
        'recurrent_method':   'simpleband',
        'morning_selector':   'start_only',
        'afternoon_selector': 'end_only',
        'morning_param':      120,
        'temporal_scale':     temp_scale,
    },
    {
        'recurrent_method':   'simpleband',
        'morning_selector':   'start_only',
        'afternoon_selector': 'end_only',
        'morning_param':      150,
        'temporal_scale':     temp_scale,
    },
    {
        'recurrent_method':   'shortest_interval',
        'morning_selector':   'start_only',
        'afternoon_selector': 'end_only',
        'morning_param':      0.9,
        'temporal_scale':     temp_scale,
    },
]

# ─── Step 2: Variables ────────────────────────────────────────────────────────
# Exact or partial column names from the CSV.  Common choices:
#   'N'  'R-square'  r'$\beta$'  r'$log\tilde{\alpha}$'
#   'median'  'mean'  'jb_stat'  'jb_p'
#   't-statistic (beta)'  'p-value (beta)'

COMPARE_VARIABLES = ['N', 'R-square', r'$\beta$']


compare_bpr_scenarios(COMPARE_SCENARIOS, COMPARE_VARIABLES)


# %% [markdown]
# # Appendix

# %% [markdown]
# ## Data Quality check

# %%
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

# %%
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


# %%
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

# %%
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
        # with open(f'./12 python file/{VDS_num}/traffic_within_day_{date}_{aggregate_timeframe}aggmin_{lane_num}.p', 'rb') as file:
        #     traffic_within_day = pickle.load(file)

        # with open(f'./12 python file/{VDS_num}/plot_date_{date}_{aggregate_timeframe}aggmin.p', 'rb') as file:
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

    df_daily_measure.to_csv(f'./14 Dataquality_check_result/Data_quality_check_{VDS_num}.csv')

# %% [markdown]
# - imputation: 5min (30se)

# %% [markdown]
# ## Pipeline Steps with Manual check

# %% [markdown]
#
# - <img src='./02_1_presentation_fig/2_Data_process_flowchart.png' width=90%>  

# %% [markdown]
# - Discussion about 'capping'
#     - I capped unrealistic 5-min aggregated speed estimates at 80 mph. Such inflated values can bias average speeds across periods. They may arise from measurement errors or from applying g-factors on an hourly basis, which is a relatively coarse interval. I believe it makes more sense to correct these unrealistic values to a realistic level that still reflects free-flow speeds.

# %% [markdown]
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

# %% [markdown]
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

# %%

# %%

# %%
