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

# <p style="font-size: 25px;"> Detecting Traffic Sensor Malfunctions through Lane-to-Lane Correlation Analysis: A Comparative Study using NGSIM and PeMS Datasets</p>

# In a new code cell, run this:
# !jupytext --set-formats ipynb,py:light Research_BPR_function_Development_JEH.ipynb


import sys
sys.path.append('../src')
from utils import my_function

# !jupyter nbconvert --to pdf --TagRemovePreprocessor.remove_cell_tags="['hide']" your_notebook.ipynb

#
# <div class="alert alert-warning">
#     
# - Blue: notes (info) | White: slides | Green: main(success) | Red: past versions(danger)
# - Generally, the presentation follows <font size = 5> slides -> main text -> personal notes ->  code </font> in each subsection (Outline only appear at the beginning of each section, some subsections may not have personal notes or codes)
#     
# </div>
#     
# <div class="alert alert-info">
#     
# - <font size = 5> Questions / notes </font>:
# 1. The outline of Introduction
#    - Starting from the loop detector based framework and then evaluate its extension to other sources of data
#    - Starting from the different types of data sources available, we aim to develop a general framework that can accommodate all these varied sources of data.
#        - However, it is difficult to justify the framework's applicability to all possible data sources, as our experimentation has been limited to the NGSIM and I-24 data sets. These datasets, while valuable, may not be representative of the full spectrum of traffic data sources that exist in practice.
#
# 2. The issue with the assumption of balanced lane flows underlying the use of CV
#     - The use of the coefficient of variation (CV) as a metric assumes that the distribution of traffic flows across lanes is identical. However, many studies have revealed that the distribution of flows can be unbalanced, which conflicts with this assumption.
#     - To address this limitation, two potential approaches can be considered:
#         - Determine the ground-truth value of CV for situations with unbalanced lane flow distributions, as reported in other published literature.(need to find papers)
#             - need to be very careful
#         - Complement the use of CV with an additional variable that can capture the pattern of time-interval CVs, which may provide more insights into the variability of traffic flows.

# <div class="alert alert-info">
#
#
# <font size = 5> PhD dissertation topics </font>
#
# __Theme__: Understanding demand-supply relationships and using this knowledge to improve system performance
#     
# 1. Filter out the dataset from malfunctioning sensors
#     - Establish a range of CV values for accurately functioning sensors
#     - Evaluate how the time-space domain size matters the CV range
#     
# 2. Analyze the relationship between observed demand and potential demand using the BPR function
#     - How different time periods and traffic conditions affect this relationship by calibrating key parameters
#     - __2.1. Travel demand vs Equilibrium-state demand__
#         - $\bar{t}=\frac{1}{\bar{v}}=t_0[1+\alpha(\frac{N}{C})^\beta]$ ($N=qT$)
#             - N: Traffic volume (vehs)
#             - q: Traffic flow rates (vph)
#             - T: Time period (hours)
#         - $N= \begin{cases} \bar{q} \cdot T \text{ (if T covers off-peak period or all-day) } \\ \bar{q} \cdot T(N) \text{ (if T covers peak period)} \end{cases}$
#             - The gap between potential demand and observed demand during peak periods creates excess demand, which then spills over into other time periods.
#             - but, why potential demand needs to be considered in the BPR function?
#             - <img src='https://github.com/jooneui/fig_collection/blob/main/BPR%20concept.jpg?raw=true' width=30%>
#     - __2.2. Reveal demand & supply relationship__
#         - Determine $\alpha, \beta$ of BPR-function.
# 3. Analyze the interaction in Mixed Traffic Systems:
#     - HOV vs GP / HOV vs HOT / HOT vs GP
#         - Based on individual-purpose lane's potential/observed demands, analyze how they interact until the equilibrium state.
#         - How to avoid compromising the performance of general-purpose lanes in the process
#             - when HOV/HOT lanes are underutilitzed and GP lanes are overburdened.
#     - AV exclusive vs GP lanes
#     - * As transportation shifts towards service instead of infrastructure where competition exists between similaar services, understanding how cost influences travel choices will become more important.
# 4. Extend the relationship to the network level using Bathtub models
#     - HOV/HOT lane is not confined to one segment, but rather covers network level.
#     - The determined BPR parameter determines the shape of F.D., which can be applied to the bathtub models.
# 5. Deep Learning: Dynamic tolling system
#     - Great tool with fundamental principle
#
# - My objective during phd
#     - I want to develop model or framework that depict the macroscopic relationship between demand and supply
#         - Extension of BPR function
#         - Bathtub model
#         - Deep learning (data-based)
# </div>

# + jupyter={"outputs_hidden": true}
from IPython.display import display, Javascript

display(Javascript("""

function hide_cells(tag) {
    var cells = Jupyter.notebook.get_cells();
    for (var i = 0; i < cells.length; i++) {
        var cell = cells[i];
        if (cell.metadata.tags && cell.metadata.tags.indexOf(tag) > -1) {
            cell.element.toggle();
        }
    }
}

function show_cells(tag) {
    var cells = Jupyter.notebook.get_cells();
    for (var i = 0; i < cells.length; i++) {
        var cell = cells[i];
        if (cell.metadata.tags && cell.metadata.tags.indexOf(tag) > -1) {
            cell.element.show();
        }
    }
}

function show_all_cells() {
    var cells = Jupyter.notebook.get_cells();
    for (var i = 0; i < cells.length; i++) {
        var cell = cells[i];
        cell.element.show();
    }
}

// Show only cells with the 'show' tag

show_all_cells()
hide_cells('past')

"""))

#hide_cells('past');
# show_all_cells()
# show_cells('past');
# hide_cells('code')
# hide_cells('past')

# + jupyter={"outputs_hidden": true}
from IPython.display import display, HTML

display(HTML(f"""
<button onclick="hide_cells('past')">Hide Past Cells</button>
<button onclick="hide_cells('notes')">Hide Notes Cells</button>
<button onclick="hide_cells('code')">Hide Code Cells</button>
<button onclick="show_all_cells();">Show All Cells</button>
"""))

# + [markdown] tags=["notes"]
# <font size = 5> Word Use </font>:
# - [__Lane-to-Lane (volumes, speed correlation)__](https://journals.sagepub.com/doi/pdf/10.3141/1856-11)
# - [__A Station(=A location) includes multiple loop detectors__](https://journals.sagepub.com/doi/pdf/10.3141/2593-05)
#     - single/double loop detectors; type of loop detectors
# - The diagnostics algorithm detects bad(malfunctioning) single-loop detectors from their volume and occupancy measurements
# - __traffic volume, traffic flows, total count of vehicles??__
# - detect bad, malfunctioning detectors, evaluate detectors' health
# - use sensors, not (loop) detectors

# + [markdown] tags=["notes"]
# - CV usage in traffic 
#     - [Effect of desired speed variability on highway traffic flow](https://journals.aps.org/pre/pdf/10.1103/PhysRevE.79.066110)
#     - [Estimation of uncertainty and variability of urban traffic volume measurements in Kielce](https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=8373314)
#     - [Change detection based on the coefficient of variation in SAR time-series of urban areas](https://www.mdpi.com/2072-4292/12/13/2089)
#     - [Analytic relationships between travel time reliability measures](https://journals.sagepub.com/doi/pdf/10.3141/2254-13)
# -

# <div class="alert alert-info" role="alert">
#
# __Things to consider when writing down paper__
#     
# - versatility of this framework to sensors other than loop detectors
# - Introduction starts with traffic flow sensors, then how to lead density, and average speeds
#     - main is traffic flow, but add comments in the end of possibility of extending to density and speeds
# - how to distinguish the tense(past/present)
# - non-parametric CV
#

# + [markdown] tags=["slides", "main"]
# # Introduction
# -

# ## The importance of traffic flow sensor data in transportation management

# + [markdown] tags=["main"]
# <div class="alert alert-success" role="alert">
#
# - Traffic flow sensors are essential for modern transportation management, providing data that enhances the efficiency and safety of highways, arterials, and city streets. By analyzing traffic patterns, these sensors enable strategies such as adjusting signal timings, dynamic route guidance, and optimized lane usage to manage congestion effectively. This data-driven approach improves traffic flow, enhances traveler safety by identifying accident-prone areas, and enables rapid incident response. Additionally, traffic sensor data helps minimize environmental impacts by informing strategies to reduce emissions, noise, and energy consumption. This invaluable data gathered from traffic flow sensors is indispensable for modern transportation management systems, enhancing safety, mobility, and environmental sustainability in our cities and communities.
#     
# </div>

# + [markdown] tags=["notes"]
# <div class="alert alert-info" role="alert">
#
# The PeMS algorithms for accurate, real-time estimates of g-factors and speeds from single-loop detectors (Zhangfeng Jia, Chao Chen, Ben Coifman et al., 2001)
# - The algorithm of g-factor in PeMs
# - Checking the definition of 'g-factor'
#     -  $g(t)=g_{traffic}(t)+g_{detector}(t)$
#         - $g_{traffic}(t)$: average value of vehicle length
#         - $g_{detector}(t)$: function of the threshold value and the slope of the detector signal
#     - Zhanfeng Jia's algorithm of calculating g-factor(2001)
#         -  no congestion: $g(t)=\frac{o(t) \times T}{c(t)} \times v_{free}$
#             - $o(t)$: occupancy
#             - $c(t)$: number of vehicles that crossed the detector during period t (vehs)
#             - $v_{free}$: free-flow speed is assumed known.
#             - $T$: duration of reporting period
#         - Make the g-factor to be a continuous, smooth curve over time
#             - If there is no congestion
#                 - $g_{filt}(t)=(1-p)\times g_{filt}(t-1)+p\times g_{inst}(t)$
#                     - $g_{inst}(t)=\frac{o(t)\times T}{c(t)}\times v_{free}$
#                         - $g_{inst}(t)$: instantaneous g-factor calculated from the instantaneous volume and occupancy measurements.
#                         - But, this only applies to the when no congestion(free-flow speed)
#                     - p: $\frac{1}{T+1}$: this weighting refers that it averages out the previous $T$ period.
#                 - $g_{filt}$ averages out previous time.
#                     - Thus, $t$ at $g_{filt}(t)$ is not a current time but 2 hours($\tau$) before the current time.
#                     - $\tau$: delay time 
#             - If congestion,
#                 - $g_{filt}(t)=g_{filt}(t-1)$
#                     - this logic can be understandable if the demand of vehicle types would be not that much changed after congestion occurs.
#         - Corrector to cancel the effect of delay & reflect congested state
#             - $g(t)=g_{filt}(t)+[g_{hist}(t+\tau)-g_{hist}(t)]$
#             - $g_{hist}$ is historic g-factor, and would reflect the effect of congestion
#                 - BUT, I do not know how it can have historic data and how reflect the congestion(speed)
#             - Thus, the speed is $v(t)=\frac{o(t)\times T}{c(t)}\times g(t)$
#
#     
# </div>
# -

# ## The types of traffic flow sensors

# + [markdown] tags=["main"]
# <div class="alert alert-success" role="alert">
#
# - Traffic sensors' definition and types
#     - According to Traffic Detector Handbook (1), a traffic flow sensor is a device for capturing the presence or passage of vehicles in a particular location so as to determine traffic states and parameters. Traffic sensors, which all are considered as point sensors, are categorized into two families: 1) in-roadway sensors that are embedded in pavement or attached to road surfaces, including inductive-loop detectors and magnetometers sensors, 2) over-roadway sensors that are mounted above the surface, including video image processors, microwave radar sensors, laser radar sensors, and ultrasonic/acoustic/passive infrared sensors.
# - In-roadway sensors
#     - One of the primary types of in-roadway sensors is the inductive-loop detector. It comprises loops of wire embedded in sawcuts in the road pavement. When a conductive metal object like a vehicle passes over or stops within the sensor's detection area, it reduces the loop's inductance, generating an electrical signal. This signal travels through a curbside junction box to an electronics unit in a controller cabinet. The electronics unit analyzes the signal to determine vehicle presence or passage and sends corresponding commands to the controller. According to the handbook (1), the inductive-loop detector is the most commonly used sensor in modern traffic control systems. Other in-roadway sensors include magnetic detectors, which detect changes in the Earth's magnetic field caused by vehicles containing ferrous material. Since both sensors are passive devices, they do not emit energy, requiring a portion of the vehicle to pass over them to be detected.
#     - One of the main types of in-roadway sensors is the inductive-loop detector, which consists of loops of wire embedded into sawcuts in the road pavement. A conductive metal object, such as a vehicle passing over or stopped within the sensor's detection area, decreases the loop's inductance (an electrical property), producing an electrical signal that is transmitted through a curbside junction box (a "pull box") to an electronics unit housed in a controller cabinet. The electronics unit analyzes the signal, interpreting it as the presence or passage of a vehicle, and sends an appropriate call to the controller. According to the handbook (1), "Today, the inductive-loop detector is, by far, the most widely used sensor in modern traffic control systems."
#     - Other in-roadway sensors include magnetic detectors and magnetometers, which can be placed underneath a roadway or bridge. A magnetic detector senses changes in the Earth's magnetic field caused by passage of a nearby vehicle that contains ferrous material. A magnetometer measures the difference in the Earth's magnetic field caused by the passage or presence of a vehicle. Its ability to function as a presence sensor enables it to detect stopped vehicles. Because both of these sensors are passive devices, they do not transmit energy. Therefore, a portion of the vehicle must pass over the sensor for it to be detected. A magnetometer can detect two vehicles separated by as little as 0.3 meter (1.0 foot). This potentially makes the magnetometer as accurate as — or even better than — the inductive-loop detector at counting vehicles (1).
#
# - Over-roadway sensors
#     - Examples of over-roadway sensors include video image processors, which use cameras mounted on tall poles adjacent to the roadway or on traffic signal mast arms above the road. There are also microwave radar, laser radar, ultrasonic, and passive infrared sensors, which can be installed either alongside or above the road. Over-roadway sensors offer advantages in monitoring multiple lanes or creating multiple detection zones with a single unit, and they generally do not require road closure and physical modifications for installation and maintenance (1).
#     
# - Selection of sensors
#     - Detection systems can be built up based on one of the traffic flow sensors or a combination of them. Installation and maintenance cost, traffic disruption and safety of installers, coverage area with multiple lanes and detection zones, easiness of working, providing high quality data with respect to weather effects and variable lightening, traffic flow conditions and the number of measured parameters are the criteria that should be taken into account for opting the appropriate detection system (1). Both types of sensor technologies bring strengths and weaknesses. In contrast to over-roadway sensors that are affected by weather-related issues, the in-roadway sensors are insensitive to weather conditions due to their close location to the vehicle (1). However, installation and maintenance of in-roadway sensors require road closure and physical changes on the road surface. The main advantage of over-roadway sensors compared to the in-roadway technologies is their capability to monitor multiple lanes or create multi-detection zones in one lane at the same time with only one unit, whereas multiple loops and magnetometers are required to screen all lanes of an approach.
#     
#     
#
#
#
#
# </div>
# -

# ## The importance of evaluating traffic sensors' performance

# + [markdown] tags=["main"]
# <div class="alert alert-success" role="alert">
#
# - Accurate and reliable traffic data collected from these sensors plays a vital role in transportation decision-making. The decisions for traffic management and transportation planning rely heavily on the quality of traffic data being collected and how well that data reflects the actual situations occurring (2,3). There is no doubt that decisions would be compromised without better and more informative traffic data from these flow sensors (4).
# - However, the data collected from traffic sensors include numerous possibilities for error.
#     - Loop detectors, currently the most plentiful source of traffic data in the most of the cities (5), are prone to have various errors cased by hardware and software problems
#         - pavement/saw-cut failures, intermittent communications, double counting of lane-changing vehicles, and so on (6)
#         - According to PeMS, which is a widely used data source for the freeway sensor system in California, only 67% of the detectors are working properly in May, 2014 (5). Some districts (e.g. district 6 in Los Angeles County) have even lower proportions of working detectors. 
#     - Erik Minge et al. (7) both laser sensors and video processors demonstrated high accuracy, with laser sensors achieving axle-spacing accuracy typically within 5 percent and video processors matching manual counts within 2.2 percent. However, both types faced challenges: laser sensors struggled with occlusion and lens dirt, while video processors were affected by environmental conditions such as fog and rain
# - Sensor errors degrade the quality of detector data, and the impact of these errors will propagate to  subsequent measurements such as ﬂow (the number of vehicles per unit time), occupancy (the percent time the detector is occupied), and speed from the loop detectors. In the end, data incorporating sensor errors could affect the traffic control decisions and traveler information based on the detector’s data.
# - Thus, it is important to determine the health status of traffic sensors, before one can use their data to estimate congestion levels and other trafﬁc characteristics. Moreover, such sensor health information is also critical for priortizing the maintenance of sensors.
#
#     
# </div>
# -

# ## Previous studies

# + [markdown] tags=["main"]
# <div class="alert alert-success" role="alert">
#
# - Extensive studies have been conducted to diagnose and correct traffic flow sensor errors (9,10,11). 
#     - In 1976, FHTVA report (12) identiﬁed ﬁve ways in which detectors can malfunction: sensors stuck on or off, chattering, pulse breakup, hanging, and intermittent malfunctioning. This report presented many methods to detect such malfunctions in different time intervals based on the volume and occupancy parameters. These methods deﬁne some thresholds on minimum and maximum speed, ﬂow, and density, and consider a sample to be invalid if they fail any of the tests.
#     - Later, Jacobson et al. (13) developed the previous algorithm by deﬁning an ‘acceptable region’ in the occupancy-volume plane and declaring the samples to be good only if they fell inside the region. Their algorithm allowed a single detector system to use a surrogate of speed to screen data, adding a dimension to detector error checking. 
#     - Chen et al. (2003) developed an algorithm that extends the time scale of flow and occupancy measurements to cover an entire day. This approach allows for the identification of loops that consistently produce either reasonable or suspect data. While it's challenging to determine if a single 30-second sample is good or bad unless it is blatantly abnormal, examining a full day's worth of data makes it easier to distinguish between good and bad behavior. To detect malfunctioning data, Chen et al. (2003) identifies four types of potential errors: persistent zeros, non-zero occupancy with zero flow, very high occupancy, and constant values. A detector is flagged as bad if the number of error samples over a day exceeds a predefined threshold. 
#     - In the paper "Detection and Classification of Sensor Anomalies for Simulating Urban Traffic Scenarios" (2022), anomalies are detected by first applying a flow-speed correlation filter to identify deviations from expected traffic patterns. Seasonal-Trend Decomposition using Loess is then used to decompose the time series data into trend, seasonal, and residual components. Anomalies are identified in the residual component using the Interquartile Range (IQR) method, with the residual values as input. Thresholds are set at 1.5 times the IQR above the third quartile and below the first quartile, flagging outliers as anomalies.
#     - \citep{bachechi2022detection} implement time-series data of individual loop detector for the detection. The Seasonal-Trend Decomposition using is applied to decompose the time series data into trend, seasonal, and residual components. Anomalies are identified in the residual component using the Interquartile Range (IQR) method, with outliers flagged based on thresholds set at 1.5 times the IQR above the third quartile and below the first quartile.
#         - "Anomaly detection and classification in traffic flow data from fluctuations in the flow–density relationship" 문헌검토
#     - The aforementioned methods are all designed to assess the health of individual sensors by examining whether the data produced by each sensor is statistically correct. However, such methods have a drawback; these local methods focus on each sensor's performance individually and fail to consider the correlations between neighboring sensors.
# -

# ## lane-to-lane correlation application

# + [markdown] tags=["main"]
# <div class="alert alert-success" role="alert">
#
# - The widespread application of lane-to-lane correlations, as demonstrated in the aforementioned studies, highlights the potential use of variations across lanes to detect malfunctioning sensors. Strong lane-to-lane correlations indicate that traffic states in adjacent lanes typically align closely, reflecting similar patterns and trends. This strong correlation helps maintain a consistent level of variation between neighboring lanes, as the traffic states should not deviate significantly from each other under normal conditions. However, when a sensor malfunctions, it generates anomalous measurements, causing the variation between the traffic states in the affected lane and its neighboring lanes to exceed normal levels. Therefore, this abnormal increase in variation can serve as a measure to identify or detect the malfunctioning sensor, as it signals a disruption in the expected correlation between lanes.
# - In fact, some errors that are not noticeable when looking at an individual lane's data can become apparent when considering the lane-to-lane variation. For instance, if neighboring detectors show a large difference in traffic flow, it suggests that at least one of them may be malfunctioning, even if their values fall within the normal range. Therefore, using this measure can help detect malfunctioning sensors by identifying potential errors that previous methods might miss.
#
# </div>
# -

# ## The Poossibility of considering lane-to-lane variation to malfunctioning detection

# <div class="alert alert-success" role="alert">
#
# - The widespread application of lane-to-lane correlations, as demonstrated in the aforementioned studies, highlights the potential use of variations across lanes to detect malfunctioning sensors. Strong lane-to-lane correlations indicate that traffic states in adjacent lanes typically align closely, reflecting similar patterns and trends. This strong correlation helps maintain a consistent level of variation between neighboring lanes, as the traffic states should not deviate significantly from each other under normal conditions. However, when a sensor malfunctions, it generates anomalous measurements, causing the variation between the traffic states in the affected lane and its neighboring lanes to exceed normal levels. Therefore, this abnormal increase in variation can serve as a measure to identify or detect the malfunctioning sensor, as it signals a disruption in the expected correlation between lanes.
# - In fact, some errors that are not noticeable when looking at an individual lane's data can become apparent when considering the lane-to-lane variation. For instance, if neighboring detectors show a large difference in traffic flow, it suggests that at least one of them may be malfunctioning, even if their values fall within the normal range. Therefore, using this measure can help detect malfunctioning sensors by identifying potential errors that previous methods might miss.
#
# </div>

# + [markdown] tags=["main"]
# <div class="alert alert-success" role="alert">
#
# - To the best of my knowledge, no other studies besides Sun et al. (2016) exploit the relationship between neighboring sensors to detect malfunctioning traffic sensors. Sun et al. (2016) focused on the sensor health problem at the network level. They defined a health index for each sensor based on how consistently its data aligned with other data in the network, taking the flow conservation principle of daily flows into account. However, this approach requires detailed information about the flow within the entire network, including data from entering and exiting ramps, which limits its practical implementation. Therefore, using lane-to-lane variation offers a more practical alternative compared to the method proposed by Sun et al. (2016). By focusing on the variations between adjacent lanes, this method can effectively identify malfunctioning sensors without the need for comprehensive network-wide flow data.
#    - cf) The study separates all links in a network into base links and non-base links, allowing the flows on the latter to be calculated from those on the former. The presence of unhealthy sensors would violate the network flow conservation principle, so they define the least inconsistent base set of links as those that minimize the sum of squares of the differences between observed and calculated flows on non-base links. However, such least inconsistent base sets may not be unique in a general road network, so they define the health index of an individual sensor as the frequency it appears in all of the least inconsistent bases.
# </div>

# + [markdown] tags=["notes"]
# <div class="alert alert-info">
# <p style="font-size: 30px"> Literature Review </p>
#
# __1. Estimation of Truck Traffic Volume from Single Loop Detectors with Lane-to-Lane Speed Correlation(Jaimyoung Kwon et al., 2003)__
# -  algorithm for estimating truck traffic volume, applicable to multilane freeways with one truck-free lane and high lane-to-lane speed correlation
# - $ \bar{v}(i,j)\approx \frac{q(i,j)\bar{L}(i,j)}{O(i,j)}= \frac{q(i',j){p(i',j)\bar{l_t}+[1-p(i',j)]\bar{l_c}}}{O(i',j)}$
#     - By assuming there are only two different types of vehicles with the length of two vehicles classes as 18.6ft(5.67m) and 61.2ft(18.65m).
#     - Another assumption is that the inner lane has zero ratio of truck.
# - This papers starts from the phenomenon "strong lane-to-lane correlation of speed", but the degree of correlation varies from the proportion of trucks for each lane.
# - Compared to our study, the difference derives from the truck flow proportion, not from the errors of detectors.
# - The study provides strong evidence that there is a close correlation between speeds in adjacent lanes on multilane freeways. This correlation is a critical component of the proposed algorithm, enabling accurate real-time estimation of truck traffic volumes from single loop detector data. The close lane-to-lane speed correlation allows for effective monitoring and analysis of traffic patterns, making the algorithm a valuable tool for transportation planning and management.
#
# __2. Imputing Errorenous Data of Single-Station Loop Detectors for Nonincident Conditions: Comparison Between Temporal and Spatial Methods__
# - Malfunctioning
#     - correction is equivalent to estimating missimg data points, because all error types are converted to missing-data errors
# - This paper explores 4 different methodologies to estimate the total traffic when several lanes out of all lanes at the same station were revealed as malfunctioning.
#     - Temporal Correction (TC): Calculate averages of the traffic flows on other days when the loop detectors were functioning properly.
#     - Spatial Correction using Linear Regression (LR)
#         - Estimate total traffic flows based only on each lane's flow when the detector is working well: $\hat{q}_t^i=\beta_1^if_t^i+\beta_2^i+e$
#             - $\hat{q}_t^i$ (veh/hr): Estimated traffic flow at the station i aggregated by entire lanes
#             - $f_t^i$ (veh/hr/lane): traffic flow at the station i for each lane(lane number should have been included)
#     - After estimating $\hat{q}_t^i$ from every available flow estimates, compute Arithmetic average: $\hat{q}_t^{LR}=\frac{\sum_i \hat{q}_t^i}{n}$
#         - Chen et al.(2003) only focus on only malfunctioning lane's traffic flow by regression using the adjacent lane's traffic flow
#     - Spatial Correction using Kernel Regression (KR)
#     - Lane Distribution Correction (LD)
#         - Using the data when all detectors were functioning properly, calculate the stable lane distribution  proportions($\bar{p}_t^i=\frac{\sum_{j=1}^d p_t^i(j)}{d}$)
#         - $\hat{q}_t^i=\frac{f_t^i}{\bar{p}_t^i}$ 
#             - where $f_t^i$: flow at time t at lane i when the detector is well-functioning.
#             - $\hat{q}_t^i \text{: estimate of station flow at time t based on }  f_t^i$
# - Randomly generate errors and check the performance of each method.
# - The goal of this paper is to estimate the total traffic flows across all lanes using only the properly functioning loop detectors.
#
#     
# __3. Detecting Errors and Imputing Missing Data for Single-Loop Surveillance Systems(Chao Chen et al., 2003)__
# - discusses methods to detect errors and impute missing data in single-loop traffic surveillance systems. These systems are essential for traffic monitoring but often produce incomplete or incorrect data.
# - Detect bad detectors using time-series data
#     - They define 4 different types of erros, which would be a good reference for possible error types
#         - __Type 1: Occupancy and flow are mostly zero__
#         - __Type 2: Non-zero occupancy and zero flow__
#         - __Type 3: Very high occupancy__
#         - __Type 4: Constant occupancy and flow__
#         - Type 1 applies to Our SR-91 site
#     - Only samples between 5:00 a.m. and 10:00 p.m. were used for diagnostics, as it is more difficult to distinguish between good and bad loops outside this period. This amounts to 2,041 30-second samples per day.
#     - Detects malfunctioning detectors by analyzing the time series of volume and occupancy measurements over an entire day, rather than individual samples. Identifies bad detectors based on specific error types, such as persistent zeros, non-zero occupancy with zero flow, very high occupancy, and constant values.
#     - Use 4 different statistics to distinguish good or bad detectors
#         - $S_1(i,d)$: number of samples that have occupancy=0
#         - $S_2(i,d)$: number of samples that have occupancy >0 and flow=0
#         - $S_3(i,d)$: number of samples that have occupancy > k*
#         - $S_4(i,d)$: entropy of occupnacy samples: well-known measure of the "randomness" of a random variables
#             - if $k_i(d,t)$ is constant in t, its entrpy is zero
#         - The decision whether the loop is bad(0) or good(1) can be used by $\Delta_i(d)$ (_i_th loop and _d_th day)
#         - $\Delta_i(d)= 1 (\text{ if } S_1(i,d) > s_1^* \text{ or } S_2(i,d) > s_2^* \text{ or } S_3(i,d) > s_3^* \text{ or } S_4(i,d) > s_4^* $), otherwise, $\Delta_i(d)= 0$
#             - threshold value($s_1^*, s_2^*, s_3^*, s_4^*$) is meaningless as the distribution is distinctively separated. 
#     - Since the ground truth about which detectors are actually bad is not available, the performance of the algorithm must be verified visually.
#         - Visual verification is possible because the time series patterns of good and bad detectors look distinctly different.
#     - Manual checking of the occupancy plots revealed 14 loops that were declared good by the algorithm but appeared to be bad based on visual inspection.
#         - This suggests a false negative rate of 14/(662 - 142) = 2.7%.
#         - There were no false positives found during the manual verification.
#         - The low false negative rate and absence of false positives suggest that the algorithm performs very well.    
#
# - Impute the missing data
#     - Correlation Analysis
#         - The distribution of correlation coefficients between all neighbors in Los Angeles indicated that most neighbor pairs had high correlations in both flow and occupancy. Figure 6 in the paper illustrates this, showing the cumulative distribution of these correlation coefficients​​.
#         - The high correlation justifies using linear regression models for imputing missing data based on neighboring detectors.
#     - Uses linear regression models to estimate missing or invalid data based on the correlation between neighboring detectors.
#         - Relies on historical data to understand and predict the behavior of neighboring loops, providing more accurate estimates compared to traditional imputation methods like linear interpolation.
#     - $q_i(t)=\alpha_0^*(\delta,l_i,l_j)+\alpha_1^*(\delta,l_i,l_j)q_j(t)+\text{noise}$
#     - $k_i(t)=\beta_0^*(\delta,l_i,l_j)+\beta_1^*(\delta,l_i,l_j)k_j(t)+\text{noise}$
#     - where
#         - $\delta=0$ if _i_ and _j_ are in the same location on the freeway, 1 otherwise;
#         - $l_i$=lane number of loop _i_;
#         - $l_j$=lane number of loop _j_;
#         
# - Conclusion:
#     - The paper provides quantitative evidence of strong correlations between lane-to-lane measurements on multilane freeways. These correlations are leveraged to detect and correct errors in traffic data from single-loop detectors. The imputation algorithm, which uses these correlations, produces accurate and reliable estimates, enhancing the quality of traffic data for analysis and management.
#
# __4. Short-Term_Traffic_State_Prediction_Based_on_TemporalSpatial_Correlation__ <paper re-check>
# - The independent assumption in the original SCTM framework may prevent the model from a broad range of applications, e.g.,
# short-term trafﬁc state prediction. In this paper, the SCTM framework is extended to consider the spatial–temporal correlation of trafﬁc ﬂow and to support short-term trafﬁc state prediction.
# - However, the spatial correlation in this paper refers to one from cell to cell.
# - This paper focuses on predicting short-term traffic states using correlations in traffic data collected over time and space. The study utilizes data from loop detectors on a segment of the I210-W freeway to demonstrate the effectiveness of the proposed prediction method.
#
# __5. Measuring Traffic__
# - The paper "Measuring Traffic" discusses the Freeway Performance Measurement System (PeMS) and its use of statistical methods to process traffic data collected by various sensors, primarily inductive loop detectors. The paper addresses the challenges of detecting sensor malfunctions, imputing missing data, estimating velocity, and predicting travel times.
#
# - Key Elements:
#
# - Data Collection and Traffic Modeling:
#     - PeMS collects traffic data from various sensors, including inductive loops, floating cars, and RFID tags.
# Inductive loop detectors, the primary data source, measure traffic flow and occupancy at regular intervals (every 30 seconds).
# The collected data is used for real-time traffic control and building traffic flow models for planning and analysis.
# Freeway Performance Measurement System (PeMS):
#     - PeMS functions as a statewide repository for traffic data, integrating data collection, processing, and communication infrastructure.
# It provides real-time and historical traffic data to a wide range of users, including traffic engineers, planners, and researchers.
# PeMS supports various visualization and analysis tools to interpret the data and assess freeway performance.
# Detecting Sensor Malfunction:
#     - The paper describes the Daily Statistics Algorithm (DSA) used by PeMS to detect malfunctioning sensors.
# The DSA analyzes daily time series data of volume and occupancy measurements to identify persistent bad behavior in sensors.
# Imputation of Missing Data:
#     - The paper discusses the imputation of missing or erroneous data using measurements from neighboring detectors.
# The imputation algorithm leverages the high correlation between measurements of neighboring loops to predict missing values.
# Linear regression models based on historical data are used for imputation, ensuring accurate and reliable estimates.
# Estimation of Velocity:
#     - Single-loop detectors do not directly measure velocity; instead, velocity is estimated from flow and occupancy data.
# The paper presents methods for estimating mean vehicle length and using it to infer velocity from single-loop detector data.
# Smoothing techniques, such as the exponential filter inspired by the Kalman filter, are applied to improve velocity estimates, especially during light traffic conditions.
# - Travel Time Prediction: PeMS predicts travel times based on real-time and historical data, providing users with estimated travel times for specific routes. The prediction model uses a linear regression approach, incorporating current status and historical mean travel times. The model performs well in predicting travel times, even during rush hours, demonstrating the effectiveness of the statistical methods used.
# - Conclusion:
#     - The paper highlights the importance of statistical methods in processing and analyzing large volumes of traffic data collected by inductive loop detectors. It demonstrates the effectiveness of using correlations between neighboring detectors to detect sensor malfunctions and impute missing data. By leveraging these correlations, the methods presented in the paper significantly improve the quality and completeness of traffic data, enabling more accurate traffic management and analysis. The PeMS system serves as a valuable tool for transportation stakeholders, providing real-time and historical data to enhance freeway performance measurement and traffic control.
#     - By revealing strong lane-to-lane correlations, the paper underscores the critical role of spatial relationships in traffic data analysis, showing how these correlations can be used to improve the accuracy and reliability of traffic surveillance systems.
#
# __6. Yuyan Annie Pan et al., 2023__
# - S3 model(Qixiu Cheng et al. 2021)
# - $q=\frac{k \cdot v_f}{[1+(k/k_c)^m]^{2/m}}$
#     - $q=\frac{k \cdot v_f}{[1+(k/k_c)^m]^l}$
#     - $\frac{dq}{dk}=\frac{v_f}{[1+(k/k_c)^m]^l}-\frac{v_f \cdot l \cdot m \cdot (\frac{k}{k_c})^m}{[1+(k/k_c)^m]^{l+1}}=\frac{v_f}{[1+(k/k_c)^m]^l} \cdot [1-\frac{l\cdot m}{1+(k_c/k)^m}]$
#     - $\frac{dq}{dk}|_{k=k_c}=0 → \frac{v_f}{2^l}-v_f \cdot \frac{l\cdot m}{2^{l+1}}=0 → l=\frac{2}{m}$
# - At the critical density $k_c$: $c=\frac{k_c \cdot v_f}{2^{2/m}}$ → $4 \cdot c^m = k_c^m \cdot v_f^m$
# - $t_0 = \frac{L}{v_f}$, $t = \frac{L}{v}$
# - $tt= \begin{cases} t_0 \cdot [\frac{2}{1+\sqrt{1-(\frac{V}{C})^m}}]^{\frac{2}{m}}, \text{  if  } V/C \lt 1 \\  t_0 \cdot [\frac{2}{1-\sqrt{1-(2-\frac{V}{C})^m}}]^\frac{2}{m}, \text{  if  } V/C > 1 \end{cases}$
#     - pf) $k^m=k_c^m[(\frac{v_f}{v})^{\frac{m}{2}}-1]=4c^m\cdot v_f^{-m}\cdot[(\frac{v_f}{v})^{\frac{m}{2}}-1]=4c^m\cdot v_f^{\frac{-m}{2}}\cdot v^{\frac{-m}{2}}[(\frac{v_f}{v})^{\frac{m}{2}}-1]=4c^m\cdot v_f^{\frac{-m}{2}}\cdot v^{\frac{-m}{2}}[1-(\frac{v}{v_f})^{\frac{m}{2}}]$
#     - $k^m \cdot v^m = q^m = 4c^m \cdot (\frac{v}{v_f})^{\frac{m}{2}}[1-(\frac{v}{v_f})^{\frac{m}{2}}]=4c^m \cdot((\frac{v}{v_f})^{\frac{m}{2}}-(\frac{v}{v_f})^m)=4c^m((\frac{t_0}{t})^{\frac{m}{2}}-(\frac{t_0}{t})^m)$
#     - By solving quadratic equation, $q^m=4c^m(\frac{t_0}{t})^{\frac{m}{2}}-4c^m(\frac{t_0}{t})^m$, the $tt$ can be solved.
#
# </div>
# -

# ## The speciality of our research

# + [markdown] tags=["main"]
#
#
# <div class="alert alert-success" role="alert">
#
#
# ### Develop a broadly applicable framework to detect malfunctioning traffic flow sensors
# - Therefore, we developed a general framework for detecting malfunctioning traffic sensors by comparing lane-to-lane traffic variation. To measure this variation, we use the ratio of the standard deviation to the mean traffic flow, as it effectively quantifies variability, especially when higher average values are typically associated with higher standard deviations. 
# - The core element of our framework is the establishment of an upper threshold for lane-to-lane variations. This threshold is designed to ensure that normal data values remain below it across the entire temporal-spatial space. To determine this upper threshold, we utilize NGSIM data as the ground truth, calculating lane-to-lane variations over various time and space domains. First, we analyze the NGSIM data to compute the lane-to-lane variations. With these variations in hand, we confirm that our empirically pre-defined upper threshold can reliably identify normal traffic patterns. This involves testing whether normal detectors consistently show lane-to-lane variations below this threshold. Finally, we validate our threshold by testing its ability to distinguish between malfunctioning and normal detectors. This step ensures that the threshold effectively identifies anomalies in detector performance.
# - This method is broadly applicable in most cases, including with any type of traffic sensor that can generate traffic state variables for individual lanes, except for one-lane roads where such comparisons are not possible. For instance, when data is collected from a video image processor that generates trajectory information for all vehicles, this data can be processed to compare the traffic flow in each lane by converting the vehicle trajectories into traffic flow metrics for each lane. By providing a reliable framework, our approach enhances the accuracy of traffic monitoring systems with the detection of sensor malfunctions. This contributes to better traffic management, improved road safety, and more efficient utilization of transportation infrastructure. The following sections will detail our conceptual framework, setting an upper threshold, and case study underscore the effectiveness of our framework.
#     
# </div>

# + [markdown] tags=["past"]
#
# <div class="alert alert-danger" role="alert">
#
# __7/2/2024__
# __1.7. The speciality of our researh__  
# - Evalute its applicability to other source of data
# - Furthermore, we evaluated our framework using various data sources from different types of sensors, such as loop detectors and video data, to assess the extensibility and applicability of our framework across diverse sensing technologies.
# - To the best of our knowledge, this is one of the first attempts to assess the health of different detector types by solely relying on their own data, without making comparisons to concurrent measurements from another detector.
#     - This statement requires more careful check.
#     - Previous studies have compared data from one detector against concurrent measurements from another detector type (e.g., a loop detector versus an emerging detector technology) at the same location.
#         - However, this comparative approach cannot be applied when only a single source of data is available.
# </div>

# + [markdown] tags=["past"]
#
# <div class="alert alert-danger" role="alert">
#
# __4/18/2024__
#
# __1.1. Usefulness of Loop detector__
#     
# - Traditional approaches utilize dedicated hardware
# [49] such as inductive loop detectors, radar detectors, laser detectors
# to detect vehicles, but the main drawbacks of these equipment are
# high maintenance cost and being affected by environmental factors.
# Comparing to traditional sensors, video cameras aremore advantageous
# in terms of cost and ﬂexibility. Video cameras have been deployed for
# trafﬁc surveillance for a long time, because they provide a rich contex-
# tual information for human visualization and understanding. With the
# increasing numbers and coverage of CCTV cameras and consequent ac-
# cessibility of image data, image-based vehicle detection is one of the
# most promising new techniques for large scale trafﬁc information data
# collection and analysis [7]. In recent years, there is even a trend to
# fuse data from different sources [21,71] to detect vehicles.
#    
#
# - They work by detecting the metal in vehicles as they pass over loops of wire embedded in the pavement. A typical loop detector station will have either a single loop detector or two loop detectors per lane, known as single-loop or dual-loop detectors, respectively. 
#     - Since a dual-loop detector is capable of recording the time used for a vehicle to traverse from the first loop to the second loop and the distance between the two loops is predetermined, a dual-loop detector can calculate traffic speed fairly accurately based on such information. 
# - Loop detectors are a widely used vehicle detector for freeway traffic surveillance. The data obtained from these loop detectors is used for various applications, such as ramp metering (1, 2), incident detection (3–5), travel time prediction (6, 7), and vehicle classification (8, 9).
# </div>

# + [markdown] tags=["past"]
#
#
# <div class="alert alert-danger" role="alert">
#
# __1.2.The importance of evaluating Loop detector's performance__
#     
# - The performance of such applications greatly depends on the accuracy of the detector data, but data collected from loop detectors are prone to various errors caused by hardware and software problems
#     - pavement/saw-cut failures, intermittent communications, double counting of lane-changing vehicles, and so on (10)
# - Detector errors degrade the quality of detector data, and the impact of these errors will propagate to  subsequent measurements such as ﬂow (the number of vehicles per unit time), occupancy (the percent time the detector is occupied), and speed from the loop detectors. In the end, data incorporating detector errors could affect the traffic control decisions and traveler information based on the detector’s data.
# - According to PeMS, which is a widely used data source for the freeway sensor system in California, only 67% of the detectors were working properly in May, 2014 (11). Some districts (e.g. district 6 in Los Angeles County) have even lower proportions of working detectors. 
# - Thus, it is important to determine the health status of a detector, before one can use its data to estimate congestion levels and other trafﬁc characteristics. Moreover, such sensor health information is also critical for priortizing the maintenance of detectors.
# - etc) - Loop detectors are primarily employed for collecting traffic
# count data at fixed positions of a road network, and are a
# major source of real-time traffic flow information that has
# been widely used in traffic flow estimation [4], [5], [7], [8].
# However, the collected traffic count data typically suffers
# from low accuracy because loop detectors often lack the
# required maintenance to ensure continuous operation [9].
#
# - etc) asy installation compared to loop detectors [10].
# Bottero et al. [11] employed a magnetometer-based wireless
# sensor network to detect and classify passing vehicles for traffic flow estimation. Dong et al. [12] predicted traffic flow on a
# freeway segment in Beijing, China based on data collected by
# 314 remote microwave traffic sensors. However, the sensitivity
# of wireless sensors must be fine-tuned to ensure the accuracy
#
#     
# </div>

# + [markdown] tags=["past"]
# <div class="alert alert-danger" role="alert">
#
# __1.3. Previous studies__
#
# - In the transportation literature, there are only a few studies on the sensor health problem.
#     - The study by Turochy and Smith (12) proposed a method to assess a detector's health status based on the time series of flow and occupancy measurements. This approach placed thresholds on the maxima of occupancy and volume, the number of samples with non-zero volume but zero speed, and the average effective vehicle lengths. The sensor's health status was then determined by the total number of its faulty records. Similarly, Chen et al. (13) developed a method to evaluate a sensor's health using four statistics: the number of samples with zero occupancy, the number of samples with zero flow and non-zero occupancy, the number of samples with extremely high occupancy, and the variance of flow and occupancy. These statistics were calculated daily for each sensor, and the algorithm made health status decisions by comparing the statistics to predefined thresholds. Additionally, PeMS categorizes a sensor's health status into ten different diagnostic states, such as 'line down', 'controller down', and 'high value', using a classification algorithm (14).
#     - The aforementioned methods are all designed to assess the health of individual sensors by examining whether the data produced by each sensor is statistically correct. However, such methods have two major limitations.
#         - First, the thresholds used in the algorithms can be challenging to determine, as they may vary by location and be subject to exogenous factors such as traffic incidents, construction, and weather conditions.
#         - Second, these local methods focus on each sensor's performance individually and fail to consider the correlations between neighboring sensors.
#     - In contrast, the study by Sun (15) proposed a method that cross-checks the consistency among traffic flow sensors based on the principle of flow conservation. However, this approach requires knowledge of the amount of flow entering or exiting the ramps located between the different detectors. The need for this additional data can limit the practical implementation of this method.
# </div>

# + [markdown] tags=["past"]
#
# <div class="alert alert-danger" role="alert">
#
# __1.4. The speciality of our research__
#     
#     
# __Develop a broadly applicable framework using data from lateral loop detectors__
# - Therefore, we develope a general framework for detecting malfunctioning detector loops by comparing the data from lateral loop detectors. Comparing the consistency of lateral loop detectors can not only take into account the correlations between neighboring sensors, but also be broadly applicable in the most cases unless only one detector is installed at a location.
#
# - The coefficient of variation (CV) of traffic flow is used as a measure to evaluate the consistency of the data, as the CV is an appropriate metric to measure variability when a higher average value tends to be associated with a higher standard deviation.
#
# __Evalute its applicability to other source of data__
# - Furthermore, we also evaluate whether our framework is extensible to various data sources beyond loop detectors.
# - To the best of our knowledge, this is one of the first attempts to assess the health of different detector types by solely relying on their own data, without making comparisons to concurrent measurements from another detector.
#     - This statement requires more careful check.
#     - Previous studies have compared data from one detector against concurrent measurements from another detector type (e.g., a loop detector versus an emerging detector technology) at the same location.
#         - However, this comparative approach cannot be applied when only a single source of data is available.
# </div>

# + [markdown] tags=["past"]
# <div class="alert alert-danger" role="alert">
#
# __Usefulness of Loop detector__
#     
# - Loop detectors are the most commonly used vehicle detection devices for automated surveillance in freeway management. 
# - They work by detecting the metal in vehicles as they pass over loops of wire embedded in the pavement. A typical loop detector station will have either a single loop detector or two loop detectors per lane, known as single-loop or dual-loop detectors, respectively. 
#     - Since a dual-loop detector is capable of recording the time used for a vehicle to traverse from the first loop to the second loop and the distance between the two loops is predetermined, a dual-loop detector can calculate traffic speed fairly accurately based on such information. 
# - Loop detectors are a widely used vehicle detector for freeway traffic surveillance. The data obtained from these loop detectors is used for various applications, such as ramp metering (1, 2), incident detection (3–5), travel time prediction (6, 7), and vehicle classification (8, 9).
# </div>

# + [markdown] hide_input=true tags=["main", "slides"]
# # Conceptual Framework

# + [markdown] tags=["slides", "main"]
# ## The Measure of Lane-to-Lane Variation

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["main"]
# <div class="alert alert-success"> 
#
# In many real-world scenarios, the variance of data are proportional to their mean. As the mean of a dataset increases, the values themselves typically grow larger and have more room to spread out. Taylor (1986) documented this in a study on financial time series, showing that the variability of returns increased with the level of returns. This concept can be also applied to traffic volumes: While lane-to-lane variation would remain constant under stable conditions, but the extent of variability would increase with higher traffic volumes once disruptions occur. This trend of heteroscedasticity, where the variability depends on the mean, was observed through PeMs data on most days. The variance remained stable, but the largest variance at each mean traffic flow was proportional to the mean value. This observation confirms that as traffic volumes increase, so does the extent of variability.
#
# To account for this relationship between mean and variance, we implemented the measure of lane-to-lane variation as the standard deviaion by the mean, providing a dimensionless measure of relative variability. This is particularly useful in our study, as it allows us to compare the variability of traffic flows across different times of the day and different traffic conditions without being affected by the scale of the data. For instance, during peak hours when traffic flow is high, the high absolute variance without taking into account its large mean values can be misleading that the variance is too high to be regarded as malfunctioning. By using the variability relative to the mean, the measure can provide a standardized meteric that accurately reflects the relative variability, making it a more appropriate measure for assessing lane-to-lane variation.
#     
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["past"]
#
# <div class="alert alert-danger"> 
#
# 240705
#     
# In analyzing traffic flow data, it is important to account for the significant variations that occur throughout the day, such as during rush hour compared to off-peak times. During peak hours, the mean traffic flow rate is typically much higher than during off-peak periods, leading to varying levels of variability. Using the coefficient of variation (CV) helps adjust for these differences by allowing us to compare the variability in traffic flow relative to the mean flow rate at different times of the day. Our observations support this approach, as we have found that the standard deviation of traffic flow increases linearly with the mean traffic flow rate. This pattern confirms that variability is dependent on the level of traffic flow, justifying the use of CV as a more appropriate measure for assessing lane-to-lane variation. By normalizing the standard deviation relative to the mean, the CV provides a standardized metric that accurately reflects the relative variability across different traffic conditions, ensuring more reliable and insightful analysis.
#
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["past"]
# <div class="alert alert-danger"> 
#
# 24/07/05
#     
# In our analysis of traffic flow data, we observed that the variance in traffic flow increases with higher traffic volumes. This pattern suggests that variability is linked to the level of traffic flow, which can lead to significant differences in lane-to-lane volumes, especially during peak hours. To accurately capture and compare this variability, we propose using the coefficient of variation (CV). The CV normalizes the standard deviation by the mean, providing a dimensionless measure of relative variability. This is particularly useful in our study, as it allows us to compare the variability of traffic flows across different times of the day and different traffic conditions without being affected by the scale of the data.
#
# Using CV helps adjust for differences in mean traffic flow rates, ensuring that we can compare the degree of variability in a meaningful way. For instance, during peak hours when traffic flow is high, the absolute variance can be misleading due to the larger mean values. By normalizing the variability relative to the mean, the CV provides a standardized metric that accurately reflects the relative variability, making it a more appropriate measure for assessing lane-to-lane variation. This approach is crucial for understanding and managing traffic flow, as it highlights the true extent of variability and aids in developing strategies to optimize traffic distribution across lanes.
#     
# </div>

# + [markdown] tags=["sldies"]
# ### The reason of using the measure
# - The CV is effectively used to measure variability when a higher average value tends to be associated with a higher standard deviation.
# - From the perspective of the detector, it activates whenever a vehicle passes by. Thus, during heavy traffic, the detector triggers more frequently, increasing the likelihood of measurement errors.
# - Plotting the average and std for each time frame during a day showed the expected pattern.
# - The average slope can be regarded as the average CV during a day.
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/scatter_mean_std_110107.png?raw=true" align="left" width = 50%>
# <distribution CV per time 코딩하기!!>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["slies"]
# - 2015 data shows much higher slopes, referring to higher CV.
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/scatter_mean_std_110107.png?raw=true" align="left" width = 40%>
# <img src="https://github.com/jooneui/fig_collection/blob/main/scatter_mean_std_150716.png?raw=true" align="left" width = 40%>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["slides"]
# __Definition of CV__
#
# 그림, 변수 내용 고민해보기!
#
# <div class="alert alert-success"> 
# In our study, we aim to identify the distribution of lane-to-lane variation from normal detectors across various times, days, and locations. This allows us to set an upper threshold to exclude values outside the normal range. While recognizing that each measurement from healthy detectors contains an element of randomness, our focus is on the variation from well-functioning detectors. For example, if two loop detectors are installed in the same lane at the same station, the values they record simultaneously might differ. This indicates that each measurement contains an element of randomness, even at a specific time and location. However, our study does not aim to explain this randomness for individual detectors. Instead, we focus on understanding how the lane-to-lane variations of measurements from well-functioning detectors are distributed across various times, days, and locations. To achieve this, we assume these measurements are deterministic, treating them as true values. This assumption helps us concentrate on our objective without accounting for the inherent randomness in each measurement.
# <br>
#
# To define the lane-to-lane variation, we collect traffic flow rate measurement, denoted as $q^i_{jk,l}$, where 
# i represents the location, j the date, k the time interval, and l the lane, measured in vehicles per hour (vph). We then calculate the average and standard deviation of traffic flow rates across all lanes, denoting them as $\bar{q}^i_{jk}$, $\sigma^i_{jk}$, respectively. Since these observations are assumed to be deterministic and represent all possible data points for a specific day, location, and time, they are not samples from a larger population. Therefore, the standard deviation is denoted by $\sigma$ instead of $s$ and is calculated by dividing the sum of squared deviations by $n$. After then, the lane-to-lane variation is defined as the ratio of the standard deviation ($\sigma^i_{jk}$) to the average flow rate ($\bar{q}^i_{jk}$).
#
# Additionally, the lane-to-lane variation can be also calculated based on average flow rates during an entire day. To calculate this value, the average traffic flow rate across all time intervals on a specific date for a given lane is calculated and denoted as $\bar{q}^i_{j,l}$. After then, the average and standard deviation of $\bar{q}^i_{j,l}$ across lanes are calculated, and they are denoted as $\bar{q}^i_{j}$ and $\sigma^i_{j}$. In the end, the lane-to-lane variation at location $i$ on data $j$, which is denoted as $y^i_{j}$, is calculated by $\sigma^i_{j}$ over $\bar{q}^i_{j}$. 
#     
# Each lane-to-lane variation $y$, such as $y^i_{jk}$ or $y^i_{j}$, is a single observation from a sample, representing the variation at a specific time and location. These individual variations provide a snapshot of the traffic flow differences between lanes at given moments. The random variable $Y$ represents the overall population of these lane-to-lane variations. It encompasses all values of $y^i_{jk}$ and $y^i_{j}$, capturing the full range of variations observed across different times and locations. By analyzing $Y$. we can understand broader patterns and distributions of traffic flow variability from healthy sensors. 
#
# This definition framework also applies to various traffic state measurements, including traffic density and traffic speed. Each measurement is represented by $k^i_{jk,l}$ for density and $u^i_{jk,l}$ for speed. For standard deviation and lane-to-lane variation, values derived from densities are denoted by $\sigma'^i_{jk}$ and $y'^i_{jk}$, while those derived from speeds are indicated by $\sigma''^i_{jk}$ and $y''^i_{jk}$.
#     
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["notes"]
# <div class="alert alert-info">
#
# __The rationale for treating individual lane-to-lane variation as deterministic__
#
# - __Our Study Objective__: 
#     - By identifying the lane-to-lane variation's distribution from normal detectors across all time, days, and locations
#     - we aim to set an upper threshold showing significant difference from the normal detectors to exclude values outside the normal range
# - __Randomness of each observation__: 
#     - For example, if there are two loop detectors in the same lane at the same station, the values they record simultaneously might differ. This indicates that each measurement contains an element of randomness, even at a specific time and location.
#     - Our study does not aim to explain the randomness of individual detectors. Instead, we are interested in understanding how the lane-to-lane variation of measurements from well-functioning detectors are distributed across various times, days, and locations. Therefore, to focus on our objective, we assume that the measurements are deterministic, regarding it as true value. If not, it is necessary to take into account the randomness of each measurement
# - __Reason for Viewing CV as an Observation__: Treating each lane-to-lane variation as a fixed observation simplifies the analysis by eliminating the need to account for measurement randomness, making it easier to directly compare variability across different times and locations.
# - __Standard deviation__: Because these observations are fixed and represent all possible data points for a specific day, location, and time, they are not samples from a larger population. Therefore, the standard deviation is denoted by $\sigma$ instead of $s$ and is calculated by dividing the sum of squared deviations by $n$.
# - __lane-to-lane variation__: Each variation (or CV) is a single observation from a sample of 56 points. Therefore, the standard deviation of the sample CVs should be calculated by dividing by (n-1)    
#     
#     <img src="https://github.com/jooneui/fig_collection/blob/main/CV_definition_v2.jpg?raw=true" align='center' width = 65%> <br>
#     
# </div>
#

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["notes"]
# <div class="alert alert-info">  
#
#    
# <p style="font-size: 30px"> Variable List(Version 1) </p>    
# <br>
# <img src="https://github.com/jooneui/fig_collection/blob/main/CV_definition_v7.jpg?raw=true" align='center' width = 90%> <br>
#     
# - __flow__
#     - $q^i_{jk,l}$: Traffic flow rate measurement at location _i_, on date _j_, during time interval _k_, in lane _l_ (vphpl)
#     - $\bar{q}^i_{jk}$: The average of $q^i_{jk,l}$, across all lanes (vphpl)
#     - $\bar{q}^i_{j,l}$: The average of $q^i_{jk,l}$, across all time intervals on data _j_ (vphpl)
#     - $\bar{q}^i_{j}$: The average of $\bar{q}^i_{j,l}$, across all lanes (vphpl)
#     - $\sigma^i_{jk}$: The standard deviation of $q^i_{jk,l}$, across all lanes (vphpl)
#     - $\sigma^i_{j}$: standard deviation of $\bar{q}^i_{j,l}$, across all lanes (vphpl)
#     - $Y$: Lane-to-lane variation in traffic flow rate measurements ($Y=\{y^i_{jk},y^i_j\}$)
#         - $y^i_{jk}$: Lane-to-lane variation of traffic flow rates measured at location $i$, on date $j$, during time interval $k$
#         - $y^i_{j}$: Lane-to-lane variation of traffic flow rates measured at location $i$, on date $j$
#     
# - __density__
#     - $\rho^i_{jk,l}$: Traffic density measurement at location _i_, on date _j_, during time interval _k_, in lane _l_ (vpmpl)
#     - $\bar{\rho}^i_{jk}$: The average of $\rho^i_{jk,l}$, across all lanes (vpmpl)
#     - $\bar{\rho}^i_{j,l}$: The average of $\rho^i_{jk,l}$, across all time intervals on data _j_ (vpmpl)
#     - $\bar{\rho}^i_{j}$: The average of $\bar{\rho}^i_{j,l}$, across all lanes (vpmpl)
#     - $\sigma'^i_{jk}$: The standard deviation of $\rho^i_{jk,l}$, across all lanes (vpmpl)
#     - $\sigma'^i_{j}$: standard deviation of $\bar{\rho}^i_{j,l}$, across all lanes (vpmpl)
#     - $Y'$: Lane-to-lane variation in traffic density measurements ($Y=\{y^i_{jk},y^i_j\}$)
#         - $y'^i_{jk}$: Lane-to-lane variation of traffic densities measured at location $i$, on date $j$, during time interval $k$
#         - $y'^i_{j}$: Lane-to-lane variation of traffic densities measured at location $i$, on date $j$
#     
# - __speed__
#     - $u^i_{jk,l}$: Traffic speed measurement at location _i_, on date _j_, during time interval _k_, in lane _l_ (mph)
#     - $\bar{u}^i_{jk}$: The average of $u^i_{jk,l}$, across all lanes (mph)
#     - $\bar{u}^i_{j,l}$: The average of $u^i_{jk,l}$, across all time intervals on data _j_ (mph)
#     - $\bar{u}^i_{j}$: The average of $\bar{u}^i_{j,l}$, across all lanes (mph)
#     - $\sigma''^i_{jk}$: The standard deviation of $u^i_{jk,l}$, across all lanes (mph)
#     - $\sigma''^i_{j}$: standard deviation of $\bar{u}^i_{j,l}$, across all lanes (mph)
#     - $Y''$: Lane-to-lane variation in traffic speed measurements ($Y=\{y^i_{jk},y^i_j\}$)
#         - $y''^i_{jk}$: Lane-to-lane variation of traffic speeds measured at location $i$, on date $j$, during time interval $k$
#         - $y''^i_{j}$: Lane-to-lane variation of traffic speeds measured at location $i$, on date $j$
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["notes"]
# <div class="alert alert-info">  
#
# <p style="font-size: 30px"> Variable List(Version 2) </p>    
# <br>
# <img src="https://github.com/jooneui/fig_collection/blob/main/CV_definition_v8.jpg?raw=true" align='center' width = 90%> <br>    
#
# - Update
#     - $k$ → $\rho$
#     - $\bar{q}$ → $\mu_q$ 
#     - $y'$ → $y_{\rho^i_{jk}}$
#     - $y$ → $k, \tau$
#     - I set up "the measurement of (average) traffic flow rates" to align with other variables("density/speeds")
#         - The daily traffic flow rates, density, and speeds refer to the measurement of daily averages, not averages of averages.
#         - "The measurement of the average" is a common term.
#         - However, this interpretation doesn't apply to lane-to-lane means because the unit (vphpl) isn't consistent.
# - $\mu^i_{q,jk}$
#     
# - __flow__
#     - $q^i_{jk,l}$: Traffic flow rate measurement at location _i_, on date _j_, during time interval _k_, in lane _l_ (vphpl)
#     - $q^i_{j,l}$: Traffic flow rate measurement at location _i_, on date _j_, in lane _l_ (vphpl)
#     - $\mu_{q^i_{jk}}$: The average of $q^i_{jk,l}$, across all lanes (vphpl)
#     - $\mu_{q^i_{j,l}}$: The average of $q^i_{jk,l}$, across all time intervals on data _j_ (vphpl)
#     - $\mu_{q^i_{j}}$: The average of $\mu_{q^i_{j,l}}$, across all lanes (vphpl)
#     - $\sigma_{q^i_{jk}}$: The standard deviation of $q^i_{jk,l}$, across all lanes (vphpl)
#     - $\sigma_{\bar{q}^i_{j}}$: standard deviation of $\bar{q}^i_{j,l}$, across all lanes (vphpl)
#     - $Y_q$: Lane-to-lane variation in traffic flow rate measurements ($Y=\{y_{q^i_{jk}},y_{q^i_{j}}\}$)
#         - $y_{q^i_{jk}}$: Lane-to-lane variation of traffic flow rates measured at location $i$, on date $j$, during time interval $k$
#         - $y_{q^i_{j}}$: Lane-to-lane variation of traffic flow rates measured at location $i$, on date $j$
#     
# - __density__
#     - $\rho^i_{jk,l}$: Density measurement at location _i_, on date _j_, during time interval _k_, in lane _l_ (vpmpl)
#     - $\rho^i_{j,l}$: Density measurement at location _i_, on date _j_, in lane _l_ (vpmpl)
#     - $\bar{\rho}^i_{jk}$: The average of $\rho^i_{jk,l}$, across all lanes (vpmpl)
#     - $\bar{\rho}^i_{j,l}$: The average of $\rho^i_{jk,l}$, across all time intervals on data _j_ (vpmpl)
#     - $\bar{\rho}^i_{j}$: The average of $\bar{\rho}^i_{j,l}$, across all lanes (vpmpl)
#     - $\sigma_{\rho^i_{jk}}$: The standard deviation of $\rho^i_{jk,l}$, across all lanes (vpmpl)
#     - $\sigma_{\bar{\rho}^i_{j}}$: standard deviation of $\bar{\rho}^i_{j,l}$, across all lanes (vpmpl)
#     - $Y_\rho$: Lane-to-lane variation in density measurements ($Y=\{y_{\rho^i_{jk}},y_{\rho^i_{j}}\}$)
#         - $y_{\rho^i_{jk}}$: Lane-to-lane variation of densities measured at location $i$, on date $j$, during time interval $k$
#         - $y_{\rho^i_{j}}$: Lane-to-lane variation of densities measured at location $i$, on date $j$
#
# - __speed__
#     - $u^i_{jk,l}$: Speed measurement at location _i_, on date _j_, during time interval _k_, in lane _l_ (mph)
#     - $u^i_{j,l}$: Speed measurement at location _i_, on date _j_, in lane _l_ (mph)
#     - $\bar{u}^i_{jk}$: The average of $u^i_{jk,l}$, across all lanes (mph)
#     - $\bar{u}^i_{j,l}$: The average of $u^i_{jk,l}$, across all time intervals on data _j_ (mph)
#     - $\bar{u}^i_{j}$: The average of $\bar{u}^i_{j,l}$, across all lanes (mph)
#     - $\sigma_{u^i_{jk}}$: The standard deviation of $u^i_{jk,l}$, across all lanes (mph)
#     - $\sigma_{\bar{u}^i_{j}}$: standard deviation of $\bar{u}^i_{j,l}$, across all lanes (mph)
#     - $Y_u$: Lane-to-lane variation in speed measurements ($Y=\{y_{u^i_{jk}},y_{u^i_{j}}\}$)
#         - $y_{u^i_{jk}}$: Lane-to-lane variation of speeds measured at location $i$, on date $j$, during time interval $k$
#         - $y_{u^i_{j}}$: Lane-to-lane variation of speeds measured at location $i$, on date $j$
#
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true
# <div class="alert alert-info">  
#
# <p style="font-size: 30px"> Variable List(Version 3) </p>    
#    
# - __flow__
#     - $q^i_{jk,l}$: Traffic flow rate measurement at location _i_, on date _j_, during time interval _k_, in lane _l_ (vphpl)
#     - $q^i_{j,l}$: Traffic flow rate measurement at location _i_, on date _j_, in lane _l_ (vphpl)
#     - $\mu^i_{q,jk}$: The average of $q^i_{jk,l}$, across all lanes (vphpl)
#     - $\mu^i_{q,j}$: The average of $q^i_{j,l}$, across all lanes (vphpl)
#     - $\sigma^i_{q,jk}$: The standard deviation of $q^i_{jk,l}$ across all lanes (vphpl)
#     - $\sigma^i_{q,j}$: The standard deviation of $q^i_{j,l}$ across all lanes (vphpl)
#     - $Y_q$: Lane-to-lane variation in traffic flow rate measurements ($Y=\{y^i_{q,jk},y^i_{q,j}\}$)
#         - $y^i_{q,jk}$: Lane-to-lane variation of traffic flow rates measured at location $i$, on date $j$, during time interval $k$
#         - $y^i_{q,j}$: Lane-to-lane variation of traffic flow rates measured at location $i$, on date $j$
#     
# - __density__
#     - $\rho^i_{jk,l}$: Density measurement at location _i_, on date _j_, during time interval _k_, in lane _l_ (vpmpl)
#     - $\rho^i_{j,l}$: Density measurement at location _i_, on date _j_, in lane _l_ (vpmpl)
#     - $\mu^i_{\rho,jk}$: The average of $\rho^i_{jk,l}$, across all lanes (vpmpl)
#     - $\mu^i_{\rho,j}$: The average of $\rho^i_{j,l}$, across all time intervals on data _j_ (vpmpl)
#     - $\sigma^i_{\rho,jk}$: The standard deviation of $\rho^i_{jk,l}$, across all lanes (vpmpl)
#     - $\sigma^i_{\rho,j}$: standard deviation of $\rho^i_{j,l}$, across all lanes (vpmpl)
#     - $Y_\rho$: Lane-to-lane variation in density measurements ($Y=\{y^i_{\rho,jk},y^i_{\rho,j}\}$)
#         - $y^i_{\rho,jk}$: Lane-to-lane variation of densities measured at location $i$, on date $j$, during time interval $k$
#         - $y^i_{\rho,j}$: Lane-to-lane variation of densities measured at location $i$, on date $j$
#
# </div>
# -

# ### The definition of random variable

# 1. **Define the 1st random variable (flow rate)**:  
# - The random variable $Q_l(x,t;\Omega)$ represents the traffic flow rate at lane $l$.
#     - $q_l(x,t;\Omega)$ represents traffic flow rate value at location $x$ and time $t$, given that the time-space domain size for each sample is $\Omega$.
# - A random variable maps a sample space to a measurable space, but the sample itself may not serve as a function input, as it might not be numerical: ex.) for example, the coin flip {H,T} is not implemented into the function.
#
# - ※ The expression of random variable ($Q_l(x,t;\Omega)$ vs $Q(x,t;\Omega,l)$
#     - Both expression is based on the fixed $\Omega,l$, and $x,t$ as variable.
#     - $Q_l(x,t;\Omega)$;
#         - Lane $l$ is fixed and predetermined for each function. You analyze one lane at a time, meaning each lane requires its own separate function.
#         - This expression is more straightforward to distinguish each lane as different random variable.
#     - $Q(x,t;\Omega,l)$;
#         -  Lane $l$ is treated as a parameter that you can adjust, allowing you to analyze multiple lanes in one function by varying $l$.
#         -  It can be applicable as the function itself does not change depending on the lane.
#
# 2. **Define the 2nd random variable (coefficient of variation)**:  
# - The coefficient of variation (CV) across lanes, considering the different sample spaces for each lane, is:
# - $y(x,t;\Omega) = \frac{\sqrt{\frac{\sum_{l=1}^{L} (Q_l(x,t;\Omega) - \bar{Q}(x,t;\Omega))^2}{(L-1)}}}{\bar{Q}(x,t;\Omega)}$
#     - where $\bar{Q}(x,t;\Omega) = \frac{\sum_{l=1}^{L} Q_l(x,t;\Omega)}{L} $ represents the mean flow rate across lanes.
#
# - $\Omega=(m,n)$, $m \in M, n\in N$
#     - where, $M$ is the set of possible space scales, $N$ is the set of possible time scales
#
# <img src='https://github.com/jooneui/fig_collection/blob/main/Random%20variable_v8.jpg?raw=true' width=100%>
#
# - The source of randomness
#     - $Q_l(x,t;\Omega,l)$: for each lane, the randomness comes from x(space), t(time), and $\Omega$(Edie domain size).
#     - $Y(x,t;\Omega,l)$: The randomness comes from x(space), t(time), and $\Omega$(Edie domain size).
# </div>

# + [markdown] tags=["slides", "main"]
# ### Definition of the Measure
# -

# #### **Variable Definition**
# - __Concept__
#     - Traffic state variable is a r.v. for each lane.
#         - but we do not fully explain how these r.vs are derived.
#     - CV is a function of these r.v.s, and we focus on explaining this process
# - __Flow rates__
#     - $Q_l$: Traffic flow rate at lane $l$, defined as $Q_l=\{q_l(x,t;\Omega)\}$
#         - $q_l(x,t;\Omega)$: Traffic flow rate value at location $x$ and time $t$, given that the Edie domain size for each sample is $\Omega$ (vphpl)
#             - $\Omega=(m,n)$, $m \in M, n\in N$
#                 - where, $M$ is the set of possible space scales, $N$ is the set of possible time scales
#             - If we refer to a daily traffic flow rate, $n$ needs to be a day.
#         - $\bar{q}(x,t;\Omega)$: The average of $q_l(x,t;\Omega)$, across all lanes (vphpl)
#         - $s_q(x,t;\Omega)$: The standard deviation of $q_l(x,t;\Omega)$, across all lanes (vphpl)
#     - $Y_q$: Lane-to-lane variation of traffic flow rate ($Y_q=\{y_q(x,t;\Omega)\}$)
#         - $y_q(x,t;\Omega)$: Lane-to-lane variation of traffic flow rates measured at location $x$, time $t$, given the Edie domain size for each sample as $\Omega$
#
# - __Densities__
#     - $K_l$: Traffic densitiy at lane $l$, defined as $K_l=\{k_l(x,t;\Omega)\}$
#         - $k_l(x,t;\Omega)$: Traffic density value at location $x$ and time $t$, given that the Edie domain size for each sample is $\Omega$ (vphpl)
#             - $\Omega=(m,n)$, $m \in M, n\in N$
#                 - where, $M$ is the set of possible space scales, $N$ is the set of possible time scales
#             - If we refer to a daily traffic density, $n$ needs to be a day.
#         - $\bar{k}(x,t;\Omega)$: The average of $k_l(x,t;\Omega)$, across all lanes (vpmpl)
#         - $s_k(x,t;\Omega)$: The standard deviation of $k_l(x,t;\Omega)$, across all lanes (vphpl)
#     - $Y_k$: Lane-to-lane variation of traffic density ($Y_k=\{y_k(x,t;\Omega)\}$)
#         - $y_k(x,t;\Omega)$: Lane-to-lane variation of traffic density measured at location $x$, time $t$, given the Edie domain size for each sample as $\Omega$
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/Fig2.%20Variable%20Definition_v3.jpg?raw=true" align='center' width = 70%> <br>
#

# + [markdown] tags=["past"]
# <div class="alert alert-danger" role="alert">
#
# - 241018 version
#
# 1. __Definition of random variable__
#     - A random variable $X$ is a real-valued function $X:\Omega → E$ from a sample space $\Omega$ as a set of possible outcomes to a measurable space $E$.
#
# <img src='https://github.com/jooneui/fig_collection/blob/main/Random%20variable_v1.jpg?raw=true' align='center' width=40%>
#
# 2. __CV is a random variable, but the randomness varies on how to define traffic measurement.__
#
# - __The measurement as deterministic__
#     - Define the r.v. CV as Lane-to-lane variation in flow-rates measurements
#         - we have a sample at each location, date, and time, and each sample is a set of measurements of all lanes.
#     - The r.v., CV transforms the sample space into a measurable space.
#     - If the detector functions properly, simply counting vehicles won't cause significant errors.
#     - In this case, the variability in values (nature of noise) is due to different traffic conditions, drivers' lane choices preference, and road geometry.
# <img src='https://github.com/jooneui/fig_collection/blob/main/Random%20variable_case1.jpg?raw=true' align='center' width=40%>
#
# - __The measurement as a random variable__
#     - Measurements at each time, location, and lane contain errors, leading to different potential sample values.
#         - In reality, we have only one sample, but we can imagine many if multiple detectors were installed at the same spot.
#     - Each measurement from each detector is a sample, with a random variable mapping measuring to real-valued outcomes (e.g., flow rates).
#     - Statistics is a measure to represent a sample space, and variance is a statistics if it represents the sample space, but in this structure, it is not a statistics (pf. If it represents the population, it's a parameter.)
#     - Statistics can be seen as random variables. If then, there are two stages of randomness, which is difficult to separate the two levels.
#
# <img src='https://github.com/jooneui/fig_collection/blob/main/Random%20variable_case2_v3.jpg?raw=true' align='center' width=70%>
#
# </div>

# + [markdown] tags=["past"]
# <div class="alert alert-danger" role="alert">
#     
# - Variable Definition
#     - $q^i_{jk,l}$: Traffic rate measurement at location _i_, on date _j_, during time interval _k_, in lane _l_ (vphpl)
#         - data is considered deterministic, so express it as lower case, meaning not r.v.
#     - $\bar{q}^i_{jk}$: The average of $q^i_{jk,l}$, across all lanes (vphpl)
#     - $\bar{q}^i_{j,l}$: The average of $q^i_{jk,l}$, across all time intervals on data _j_ (vphpl)
#     - $\bar{q}^i_{j}$: The average of $\bar{q}^i_{j,l}$, across all lanes (vphpl)
#     - $\sigma^i_{jk}$: The standard deviation of $q^i_{jk,l}$, across all lanes (vphpl)
#         - The fixed nature of these observations implies that it deals with all possible observations(entire datasets) for that specific day, location, and time, even though it is not sampling from a larger population
#     - $\sigma^i_{j}$: standard deviation of $\bar{q}^i_{j,l}$, across all lanes (vphpl)
#     - $Y$: Lane-to-lane variation in traffic rate measurements ($Y=\{y^i_{jk},y^i_j\}$)
#         - $y^i_{jk}$: Lane-to-lane variation of traffic flow rates measured at location $i$, on date $j$, during time interval $k$
#         - $y^i_{j}$: Lane-to-lane variation of traffic flow rates measured at location $i$, on date $j$
#
# - Lane-to-lane variation
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/CV_definition_v3.jpg?raw=true" align='center' width = 100%> <br>
#
# </div>
# -

# #### Definition considering the size of space and time

# - directly start with defining r.v. and go to CV.
# - try to write down. before calculation.
#
# #### Comparison by the lake
#
# 1. __Lake Description:__
# - There is a large lake divided into two sections, each with equal, but very large, areas.
# 2. __Measurement Method:__
# - To measure the depth of specific parts of each section, we use a device that estimates the depth in an area of size $m \times n$ (width by length). This measurement is performed in each part of the lake section at a time.
# 3. __Device Functionality:__
# - The device emits multiple laser beams, each measuring the depth at a specific point. The depth of the area is then determined by averaging the measurements from these lasers.
# 4. __Comparison of Sections:__
# - Each $m \times n$ domain is considered comparable between the two sections. After collecting the depth data, the coefficient of variation is calculated to assess the variability between the sections.
#
# <img src='https://github.com/jooneui/fig_collection/blob/main/Random_variable_lake_fig.png?raw=true' align='center' width=40%>
#
#
# <img src='https://github.com/jooneui/fig_collection/blob/main/Random%20variable_lake.jpg?raw=true' width=100%>

# + [markdown] tags=["past"]
# <div class="alert alert-danger" role="alert">
#
# <img src='https://github.com/jooneui/fig_collection/blob/main/Random%20variable_v7.jpg?raw=true' width=100%>
#
# 1. **Define the sample space**:  
# - $\Omega^{(m,n)}_{l}$ is the set of all travel distance sets for vehicles within a space interval of size ($m$), time interval of size ($n$), and lane ($l$). This definition explicitly distinguishes the sample space by lane, in addition to space and time intervals:
# - $\Omega^{(m,n)}_l = \text{set of all travel distance sets for space interval } m, \text{ time interval } n, \text{ and lane } l$
#     - $\Omega^{(m,n)}_l = \{ (d_1, d_2, \dots, d_n) \mid d_i \in \mathbb{R},\ 0 < d_i < \infty,\ \forall i = 1, 2, \dots, n,\ n \text{ varies for each sample} \}$
#     - $\Omega^{(m,n)}_l \text{ ~ } N(\mu^{(m,n)}_l, \sigma^{(m,n)}_l)$
#
# 2. **Define a sample**:
# - $s^{(m,n)}_{i,j,k,l}$ denotes the set of travel distances for all vehicles within a space interval of size $m$ and a time interval of size $n$, recorded at the $i$-th location, during the $k$-th time interval on the $j$-th date, and within the $l$-th lane. The membership of this set in the sample $\Omega^{(m,n)}_l$ is now explicitly stated as $s^{(m,n)}_{i,j,k,l} \in \Omega^{(m,n)}_l$
# - $s^{(m,n)}_{i,j,k,l} = \{d^{(m,n)}_{i,j,k,l,1},d^{(m,n)}_{i,j,k,l,1},...,,d^{(m,n)}_{i,j,k,l,N}\}$
#     - where $d^{(m,n)}_{i,j,k,l,p} \text{ for } p=1,2,...,N)$ represents the travel distance of the $p$-th vehicle within the specified space, time, location, date, and lane intervals.
#
# 3. **Define the 1st random variable (flow rate)**:  
# - The flow rate for each sample in the sample space is calculated as:$[Q(s^{(m,n)}_{i,j,k,l}) = \frac{\sum_{p=1}^N d^{(m,n)}_{i,j,k,l,p}}{m \cdot n}]$
# - This maintains explicit dependence on space ($m$), time ($n$), and lane ($l$), linking it to the sample space.
#
# 4. **Define flow rates across lanes**:  
# - The flow rates for all four lanes at a particular location and time interval are expressed as: $\{Q(s^{(m,n)}_{i,j,k,1}), Q(s^{(m,n)}_{i,j,k,2}), Q(s^{(m,n)}_{i,j,k,3}), Q(s^{(m,n)}_{i,j,k,4})\}$
# - Each flow rate is now linked to the appropriate sample space ($\Omega^{(m,n)}_l$) for each lane.
#
# 5. **Define the 2nd random variable (coefficient of variation)**:  
# - The coefficient of variation (CV) across lanes, considering the different sample spaces for each lane, is: $y^{(m,n)}_{i,j,k} = \frac{\sqrt{\frac{1}{4} \sum_{l=1}^{4} (Q(s^{(m,n)}_{i,j,k,l}) - \bar{Q}(s^{(m,n)}_{i,j,k}))^2}}{\bar{Q}(s^{(m,n)}_{i,j,k})}$
#     - where $\bar{Q}(s^{(m,n)}_{i,j,k}) = \frac{1}{4} \sum_{l=1}^{4} Q(s^{(m,n)}_{i,j,k,l})$ represents the mean flow rate across lanes.
#
# - Summary:
#     - The sample space $\Omega^m_{n,l}$ now includes the lane $l$, distinguishing different VMT distributions for each lane.
#     - The rest of the structure follows naturally, maintaining the distinction across lanes in both the sample and random variable definitions.
#
# </div>

# + [markdown] tags=["past"]
# <div class="alert alert-danger" role="alert">
#
# - While drawing the figure in 3.2.3., I figured out that the r.v. does not have info about the length of time & space, only covers the order of interval and location.
# - There are two approaches to take into account the size of intervals
#
# 1. Sample space
# - Random variable is the same as $Q^i_{jk,l}$
# - $\Omega^m_n$ is the sample space associated with a location interval of size m and a time interval of size n.
# - $Q^i_{jk,l}(\Omega^m_n)$ is the traffic flow rates at location i, date j, and time interval k, within the sample space defined by $S^m_n$.
# - $Q^i_{jk,l}(\Omega^m_n)$ is the traffic flow rates at location i, date j, and time interval k, within the sample space defined by $S^m_n$.
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/Random variable_v5.jpg?raw=true" align='center' width = 100%> <br>
#
# 1.1. Example:
# - Let’s consider a practical example. Suppose you are measuring traffic flow rates at different times of the day and different sections of a highway. The traffic flow rate is your random variable, but you might define different sample spaces based on the size of the time intervals or the segments of the highway depending on how you're dividing the entire domain.
# - Sample Space 1: Traffic flow for every 10-minute interval and a 500-meter section of the highway.
# - Sample Space 2: Traffic flow for every 1-hour interval and a 2-kilometer section of the highway.
# - In both cases, the random variable (traffic flow) remains the same, but you are looking at it under different partitions of time and space. Each sample space represents a different context or resolution in which you're observing the same phenomenon.
#
# 1.2. Why Use Multiple Sample Spaces?
# - Different Resolutions: You may want to observe the variable at different granularities. For example, if you divide your sample space by time (10-minute intervals vs. 1-hour intervals), you're examining the same random variable at different time resolutions.
# - Different Contexts: Different sample spaces could represent different conditions under which the random variable is measured, such as different geographical locations or different environmental factors
#
# 1.3. Connection to our research
# - Since each sample is composed of 
#
# </div>
# -

# 2. Random variable
# - So, the random variable needs to capture the length of time-space domain.
# - $Q^i_{jk,l}$ may need to be changed to $Q^{m_i}_{jn_k,1},Q^{m_i}_{jn_k,2},...,Q^{m_i}_{jn_k,1} $
#     -  $Q^{m}_{jn,1}$: flow rate from m-size space, n-size time interval, at j-th data, and lane 1 (vphpl)
#         - whether or not including the j-th is controversial  
#     -  $Q^{m}_{jn,1} = \{q^{m_i}_{jn_k,1}\} \text{  } \forall i \in I, k \in K$
#         - $q^{m_i}_{jn_k,1}$: flow rate from m-size i-th space, n-size k-th time interval, at j-th data, and lane 1 (vphpl)
#         - ex.) $Q^{60}_{j200,1}=\{q^{60_1}_{j200_1,1},q^{60_2}_{j200_2,1},..., q^{60_I}_{j200_K,1}\}$
#         - Each $Q^{i}_{jk,1}$ is a measuralbe space and convert contains samples, leading to its own distribution
#             - its own distribution depends on the size of i and k. 

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["past"]
# <div class="alert alert-danger" role="alert">
#
# __Definition of lane-to-lane variation in our study__
#
# - Definition
#     - $Q^i_{jk,l}$: traffic flow at location i, on date j, during time interval k, in lane l(veh)
#         - $q^i_{jk,l}$: the possible value of $Q^i_{jk,l}$
#     - $\bar{Q}^i_{jk}$: average traffic flow at location i, on date j, during time interval k(veh)
#         - $\bar{q}^i_{jk}$: the possible value of $\bar{Q}^i_{jk}$
#     - Assumption: $q^i_{jk,1}, q^i_{jk,2}, q^i_{jk,3}, \text{and }q^i_{jk,4}$ are  I.I.D. samples of $\bar{Q}^i_{jk}$
#         - Referring to the distribution of $Q^i_{jk,1}, Q^i_{jk,2}, Q^i_{jk,3}, Q^i_{jk,4}$ are equal to the one of $\bar{Q}^i_{jk}$.
#     - $Q^i_{j,l}$: Daily traffic at location i, on date j, in lane l (veh)
#         - $q^i_{j,l}$: the possible value of $Q^i_{j,l}$
#     - $\bar{Q}^i_{j}$: average traffic flow at location i, on date j(veh)
#         - $\bar{q}^i_{j}$: the possible value of $\bar{Q}^i_{j}$
#     - $\sigma^i_{jk}$: standard deviation of traffic flows at location i on date j, during time interval k, across all lanes(veh)
#         - $s^i_{jk}$: the possible value of $\sigma^i_{jk}$
#
# - Two methodologies
#     - case1: compute the sample CV from daily volumes
#     - case2: compute the sample CV for each time-period and then calculate their arithmetic mean
#     - case3: compute the sample CV for each time-period and then calculate their average weighted by mean traffic flows.
#         - case3 is the arithmetic mean of std over entire mean traffic flows
#             -  $\sum_{k=1}^5 \frac{\bar{q}_{jk}^i}{\sum_{r=1}^5\bar{q}_{jr}^i} cv_{jk}^i = \sum_{k=1}^5 \frac{\bar{q}_{jk}^i}{\sum_{r=1}^5\bar{q}_{jr}^i} \times \frac{\sqrt{\sum_{l=1}^4(q_{jk,l}^i-\bar{q}_{jk}^i)^2/3}}{\bar{q}_{jk}^i}=\sum_{k=1}^5\frac{\sqrt{\sum_{l=1}^4(q_{jk,l}^i-\bar{q}_{jk}^i)^2/3}}{\sum_{r=1}^5\bar{q}_{jr}^i}=\sum_{k=1}^5\frac{\sqrt{\sum_{l=1}^4(q_{jk,l}^i-\bar{q}_{jk}^i)^2/3}}{5 \times \bar{q}_{j}^i}=\frac{1}{5\bar{q}_{j}^i}\sum_{k=1}^5(\sqrt{\sum_{l=1}^4(q_{jk,l}^i-\bar{q}_{jk}^i)^2/3})$
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/CV_definition__.jpg?raw=true" align='center' width = 70%> <br>
#
# </div>    

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["slides"]
# - Comparison of two different cases
#     - While cv_case2 generally has higher values than cv_case1, cv_case1 and cv_case2 overally show a linear relationship.
#     - cv_case1 is more straightforward than cv_case2, because the process of starting from each interval’s CV ($cv^i_{jk}$​) in case2 requires considering their variation.
# <br>
#     <img src="https://github.com/jooneui/fig_collection/blob/main/cv_plot_.png?raw=true" align="center" width = 80%><br>

# + [markdown] jp-MarkdownHeadingCollapsed=true
# - ※ While the distribution of CV varies throughout the day, I believe that addressing this variation needs to a separate discussion
#     - Morning has higher CV due to a lower mean or independent arrivals between lanes <br>
# <img src ='https://github.com/jooneui/fig_collection/blob/main/CV%20across%20time_110111.png?raw=true' align = 'center' width=90%>
# -

# ## Impact of Time-Space Domain Size on Lane-to-Lane Variation in Traffic State Analysis

# <div class="alert alert-danger" role="alert">
#
# 평균 값에도 샘플개수가 식으로 영향을 미치는 지 확인해보기!!
# variability 논문 확인해보기!!
# 로직 정리!! 수업 끝나고 무조건 정리하기!!
# - daganzo의 책에서 사이즈에 따라 어떻게 variance가 어떻게 달라지는지 확인
# - 취지는 한정된 entire domain에 대해서 샘플수를 늘리는 행위(Normal distribution 만족시키기 위해)가 과연 \bar{X}의 variance를 감소할 것인가?
# - 아니었다. Interval을 작게 해도 interval 간에 dependency가 존재하기 때문에, variance는 줄지 않는다.
# - 그래서 여기서 강조하는 것은 샘플 수를 늘리고 싶으면 전체 entire domaiN의 크기를 늘려야 한다는 것!
# - 실제로, entire domain을 증가시키면 independency가 증가하기 때문에 \bar{X}의 분산은 줄어듬.
# - 본 연구에서도 마찬가지로 전체 도메인 사이즈를 증가시킬수록 값은 계속 감소함.
# 실제로 평균과 전체 도메인을 분리했을 때 계속 감소하는 이유는 cov 파트를 포하하지 않기 때문.
#
# covariance 파트가 포함이 안되는거네?
# 그렇담?? covariance 파트를 어떻게 포함 안시키지??
#
# </div>

# <div class="alert alert-danger" role="alert">
# Daganzo(1997) book, addressed how the interval size/and entire domain size influenced the variance of mean.
# The book wants to address the issue of having not large enough entire domain, but trying to divide it into small intervals so that the averages follow the normal distribution based on the central limit theorem. 
#
# Its example focuses on 1-dimensional space. Time. firstly, the entire time domain is given, and divide it into predefined time intervals, and the sample Xs are collected in each interval, and the aim is to find out the variance of X_bar. 
#
# The mean of variance is usually expressed as sigma^2 over N, assuming the variance(X_i) is equal to sigma, and different X_i are independent. However, these time-series data are not independent, especially between neighboring intervals, so the covariance needs to be considered.
# The book assumed that there is a dependency within L time intervals when the interval size is small, so expression 표시.
#
# Therefore, if you want to use small intervals, it is necessary to include this R portion to determine the \bar{X} distribution, or expand the entire domain size and have large interval, so that each sample is independent.
#
# After reading this part, I have realized that my approach needs to be changed. My previous approach was that we set pretty large entire domain, and see what happens to the average lane-to-lane CV as the Edie domain increases. 
#
# <그림 그리기> For example, if we set this as Edie domain size, it can be expressed, and if we the Edie domain size twice for each dimension, it can be expressed: N2=4*N1, l어떻게 표현하지?. In the pretty large size intervals, dependent tendency occurs and since the N2 is 4N1, the variance keeps decreasing. Therefore, even as we increase the entire domain, it keeps decreasing and never converges.(여기 논리 다시 생각해야 함.,sigma 동일하다는 것 설명해줘야 함.)
#
# However, what we want to focus is when this sigma is different because this edie domain is too small so it is dominated by individual vehicle distinct driving behavior. In this case, the sigma_1 is larger than sima_2, and we assume that both two edie domains are small, so the covariances are both dependent. so, we want to find the point when the points are both small.
# 여기까지 작성!!
# </div>

# ### Estimation of Var($\bar{X}$) when $X$s are correlated**
#
# #### Edie domain: $\Delta{t_1}$ and $\Delta{x_1}$
# - a sample {$X_n$} as multidimensional random variable that takes a numerical value {$X_n$} and that the sample mean is computed componentwise.
#     - In our study, the $\bar{Q}(t,x;\Delta t_1,\Delta x_1)= \{\bar{Q}_1(t,x;\Delta t_1, \Delta x_1),\bar{Q}_2(t,x;\Delta t_1, \Delta x_1), \bar{Q}_3(t,x;\Delta t_1, \Delta x_1),\bar{Q}_4(t,x;\Delta t_1, \Delta x_1)\}$ 
# - The sample mean $\bar{X}=\sum_n \frac{X_n}{N}$  
#     - The aggregated mean over an entire domain is given by: $\bar{Q}(1,1;T,X) = \{\frac{1}{M_1 \cdot N_1}\sum_{t=1}^{M_1}\sum_{x=1}^{N_1}\bar{Q}_1(t,x;\Delta t_1,\Delta x_1),\frac{1}{M_1 \cdot N_1}\sum_{t=1}^{M_1}\sum_{x=1}^{N_1}\bar{Q}_2(t,x;\Delta t_1,\Delta x_1), \frac{1}{M_1 \cdot N_1}\sum_{t=1}^{M_1}\sum_{x=1}^{N_1}\bar{Q}_3(t,x;\Delta t_1,\Delta x_1),\frac{1}{M_1 \cdot N_1}\sum_{t=1}^{M_1}\sum_{x=1}^{N_1}\bar{Q}_4(t,x;\Delta t_1,\Delta x_1) \}$
#         - where $M_1$ and $N_1$ represent the number of spatial and temporal intervals, respectively.
#         - $\Delta t_1 = \frac{T}{M_1}$ and $\Delta x_1 = \frac{X}{N_1}$
# - $\text{Var}(\bar{Q}(1,1;T,X))=\frac{\sigma_1^2 \cdot R_1}{M_1 \cdot N_1}$
#     - with the assumption that every Edie domain cell $(i,j)$, $\text{Var} (\bar{Q}(i,j;\Delta t_1,\Delta x_1) = \sigma_1^2 \text{,  } \forall i \in \{1,...M_1\} \text{ and } j  \in \{1,...,N_1\}$
#     - In this formulation, $\sigma_1^2$ is constant variance across all Edie domain cells.
# #### Edie domain: $\Delta{t_2}$ and $\Delta{x_2}$
# - Let's think about the case when $\bar{Q}(1,1;\Delta t_1,\Delta x_1) = \frac{1}{M_2 \cdot N_2}\sum_{t=1}^{M_2}\sum_{x=1}^{N_2}\bar{Q}(t,x;\Delta t_2,\Delta x_2)$
#     - where, $ M_2 = \frac{\Delta t_1}{\Delta t_2}$ and $N_2 = \frac{\Delta x_1}{\Delta x_2}$ 
# - $\text{Var}(\bar{Q}(1,1;\Delta t_1,\Delta x_1))=\sigma_1^2=\frac{\sigma_2^2 \cdot R_2}{M_2 \cdot N_2}$
#     - with the assumption that every Edie domain cell $(i,j)$, $\text{Var} (\bar{Q}(i,j;\Delta t_2,\Delta x_2) = \sigma_2^2 \text{,  } \forall i \in \{1,...M_2\} \text{ and } j  \in \{1,...,N_2\}$
#     - In this formulation, $\sigma_2^2$ is constant variance across all Edie domain cells
# - $\text{Var}(\bar{Q}(1,1;T,X))=\frac{\sigma_1^2 \cdot R_1}{M_1 \cdot N_1}=\frac{\sigma_2^2 \cdot R_1 \cdot R_2}{(M_1 \cdot N_1) \cdot (M_2 \cdot N_2)}$

# #### The relationship between the different Edie domain size
# - To explain the relationship above, $\frac{\sigma_1^2 \cdot R_1}{M_1 \cdot N_1}=\frac{\sigma_2^2 \cdot R_1 \cdot R_2}{(M_1 \cdot N_1) \cdot (M_2 \cdot N_2)}$ needs to be explained first.
#     - Since the $\sigma_1^2=\frac{\sigma_2^2  \cdot R_2}{(M_2 \cdot N_2)}$, the relationship depends on $\sigma_1^2$ vs $\sigma_2^2$ and the size of $R_2$ (extent of correlation)
#     - This also applies to the case of $\text{Var}(\bar{Q}(1,1;T,X))=\frac{\sigma_1^2 \cdot R_1}{M_1 \cdot N_1}$
# - Explaining the relationship using the above formula is unclear. Instead, the random variable $\bar{Q}$ can be expressed as the law of total variance: the average of “within-group” variance plus “between-group” variance.
#     - $\text{Var}(\bar{Q}(1,1;T,X)) = \frac{\sum_{t=1}^{M_1} \sum_{x=1}^{N_1} [\text{Var}(\bar{Q}(t,x; \Delta t_1,\Delta x_1))+\sum_{t'=1, t\neq t'}^{M_1} \sum_{x'=1, x\neq x'}^{N_1} Cov(\bar{Q}(t,x;\Delta t_1,\Delta x_1),\bar{Q}(t',x';\Delta t_1,\Delta x_1))]}{(M_1 \cdot N_1)^2} = \text{E[Var}(\bar{Q}(t,x;\Delta t_1, \Delta x_1))]+\text{Var(E[}\bar{Q}(t,x;\Delta t_1, \Delta x_1)])$

# #### Implication of the domain size impacts
# - When intervals are very short, local fluctuations in vehicle trajectories raise the within-domain variance. Small or medium entire domain size also increases the between-interval variance because the entire domain itself represents a similar traffic condition.
# - When the entire domain becomes large, but the Edie domain is still small, we need to know the average of the "between-group variance" would decrease because the entire domain covers many different traffic conditions, while the smaller Edie domain would still cause large 'within-domain variance"
# - When Edie domain becomes larger, the individuality gets compensated, leading to smaller & stable variance, leading the entire variance stable.
# - However, in some cases, the variance switches to increase: explain this part!! 
#
# |Entire domain|Edie-domain|Within-group variance|Between-group variance|
# |:---:|:---:|:---:|:---:|
# |medium|small|large|large|
# |large|small|large|small|
# |large|medium|small & stable|small & stable|
#
# - what if we cannot set the large enough entire domain? (like loop detectors)
#     - it is okay. what we want to aim is to exclude the "within-domain variance" from individuality impact.
#     - but how to distinguish them and set the threshold is one of the issues.
# - confusing: calculation vs lane-to-lane variance

# ### Proof of the Law of Total Variance
#
# The Law of Total Variance states that for any random variable \(X\) and any grouping variable \(L\):
#
# $$
# \mathrm{Var}(X) = \mathbb{E}\bigl[\mathrm{Var}(X\mid L)\bigr] + \mathrm{Var}\bigl(\mathbb{E}[X\mid L]\bigr).
# $$
#
# We now prove this step by step.
#
# ---
#
# ##### Start with the Definition of Variance
#
# For any random variable \(X\), the variance is defined as
#
# $$
# \mathrm{Var}(X) = \mathbb{E}[X^2] - \Bigl(\mathbb{E}[X]\Bigr)^2.
# $$
#
# ---
#
# ##### Apply the Law of Total Expectation
#
#
# $$
# \mathbb{E}[X] = \mathbb{E}\bigl[\mathbb{E}[X\mid L]\bigr],
# $$
#
# and
#
# $$
# \mathbb{E}[X^2] = \mathbb{E}\bigl[\mathbb{E}[X^2\mid L]\bigr].
# $$
#
# ---
#
# ##### Express the Conditional Second Moment
#
# For each fixed value \(L = l\), by definition of conditional variance:
#
# $$
# \mathrm{Var}(X\mid L=l) = \mathbb{E}[X^2\mid L=l] - \Bigl(\mathbb{E}[X\mid L=l]\Bigr)^2.
# $$
#
# Rearrange to obtain:
#
# $$
# \mathbb{E}[X^2\mid L=l] = \mathrm{Var}(X\mid L=l) + \Bigl(\mathbb{E}[X\mid L=l]\Bigr)^2.
# $$
#
# Taking the expectation over \(L\):
#
# $$
# \mathbb{E}[X^2] = \mathbb{E}\Bigl[\mathrm{Var}(X\mid L) + \Bigl(\mathbb{E}[X\mid L]\Bigr)^2\Bigr]
# = \mathbb{E}\bigl[\mathrm{Var}(X\mid L)\bigr] + \mathbb{E}\Bigl[\Bigl(\mathbb{E}[X\mid L]\Bigr)^2\Bigr].
# $$
#
# ---
#
# ##### Substitute Back into the Definition of Variance
#
# Recall that
#
# $$
# \mathrm{Var}(X) = \mathbb{E}[X^2] - \Bigl(\mathbb{E}[X]\Bigr)^2.
# $$
#
# Substitute the expression we found for \(\mathbb{E}[X^2]\):
#
# $$
# \mathrm{Var}(X)
# = \mathbb{E}\bigl[\mathrm{Var}(X\mid L)\bigr] + \mathbb{E}\Bigl[\Bigl(\mathbb{E}[X\mid L]\Bigr)^2\Bigr] - \Bigl(\mathbb{E}[X]\Bigr)^2.
# $$
#
# But notice that
#
# $$
# \mathbb{E}\Bigl[\Bigl(\mathbb{E}[X\mid L]\Bigr)^2\Bigr] - \Bigl(\mathbb{E}[X]\Bigr)^2
# = \mathrm{Var}\bigl(\mathbb{E}[X\mid L]\bigr).
# $$
#
# Thus, we have shown that:
#
# $$
# \mathrm{Var}(X) = \mathbb{E}\bigl[\mathrm{Var}(X\mid L)\bigr] + \mathrm{Var}\bigl(\mathbb{E}[X\mid L]\bigr).
# $$
#
# by replacing the random varialbe $X$ with $\bar{X}$,
#
# $$
# \mathrm{Var}(\bar{X}) = \mathbb{E}\bigl[\mathrm{Var}(\bar{X}\mid L)\bigr] + \mathrm{Var}\bigl(\mathbb{E}[\bar{X}\mid L]\bigr).
# $$
#
# ---
#
# ##### Summary
#
# - **Within-Group Variance:** \(\mathbb{E}\bigl[\mathrm{Var}(X\mid L)\bigr]\) is the average of the variances within each subgroup determined by \(L\).  
# - **Between-Group Variance:** \(\mathrm{Var}\bigl(\mathbb{E}[X\mid L]\bigr)\) measures how the subgroup means differ from the overall mean.
#
# This completes the proof of the Law of Total Variance.
#
# ---
#
# *You can copy this cell into your Jupyter Notebook and run it in a Markdown cell to see the formatted explanation.*
#

# ### Appendix: Law of Total Variance for the Averaged Random Variable $\bar{X}$
#
# Suppose we have $N$ observations $X_1, X_2, \dots, X_N$ that are grouped according to some variable $L$. For example, each $X_i$ belongs to a group labeled by $l$, and we denote by $G(l)$ the set of indices that belong to group $l$. The overall average is defined as
#
# $$
# \bar{X} = \frac{1}{N} \sum_{i=1}^N X_i.
# $$
#
# Our goal is to see that the following two decompositions of $\mathrm{Var}(\bar{X})$ are equivalent:
#
# 1. **Covariance Expansion:**
#    $$
#    \mathrm{Var}(\bar{X})
#    = \frac{1}{N^2}\sum_{i=1}^{N} \mathrm{Var}(X_i)
#    + \frac{2}{N^2}\sum_{1\le i<j\le N}\mathrm{Cov}(X_i, X_j).
#    $$
# 2. **Law of Total Variance:**
#    $$
#    \mathrm{Var}(\bar{X})
#    = \mathbb{E}\bigl[\mathrm{Var}(\bar{X}\mid L)\bigr]
#    + \mathrm{Var}\bigl(\mathbb{E}[\bar{X}\mid L]\bigr).
#    $$
#
# Here, the idea is that the conditional mean $\mathbb{E}[\bar{X}\mid L]$ and the conditional variance $\mathrm{Var}(\bar{X}\mid L)$ can be expressed in terms of the individual $X_i$’s that belong to each group.
#
# ##### 1. Writing $\bar{X}$ in Grouped Form
#
# Let the groups be indexed by $l$. Define the contribution of group $l$ to the overall sum as
#
# $$
# S_l = \sum_{i \in G(l)} X_i.
# $$
#
# Then we can write
#
# $$
# \bar{X} = \frac{1}{N} \sum_{l} S_l.
# $$
#
# Now, the overall expectation is
#
# $$
# \mathbb{E}[\bar{X}] = \frac{1}{N}\sum_l \mathbb{E}[S_l] 
# = \frac{1}{N}\sum_l \sum_{i \in G(l)} \mathbb{E}[X_i].
# $$
#
# If we denote by $p_l$ the proportion of observations in group $l$, then (by the law of total expectation) we have
#
# $$
# \mathbb{E}[\bar{X}] = \sum_l p_l \, \mathbb{E}[\bar{X}\mid L=l],
# $$
#
# where
#
# $$
# \mathbb{E}[\bar{X}\mid L=l] = \frac{1}{N}\sum_{i\in G(l)} \mathbb{E}[X_i].
# $$
#
# ##### 2. Within-Group (Conditional) Variance
#
# Within each group $l$, define the conditional variance of the sum:
#
# $$
# \mathrm{Var}(S_l) = \sum_{i\in G(l)} \mathrm{Var}(X_i)
# + 2\sum_{\substack{i,j\in G(l)\\ i<j}} \mathrm{Cov}(X_i,X_j).
# $$
#
# Since $\bar{X}$, when conditioned on being in group $l$, is given by
#
# $$
# \bar{X}\mid (L=l) = \frac{S_l}{N},
# $$
#
# the conditional variance becomes
#
# $$
# \mathrm{Var}(\bar{X}\mid L=l)
# =\; \frac{1}{N^2}\,\mathrm{Var}(S_l)
# =\; \frac{1}{N^2}\left[\sum_{i\in G(l)} \mathrm{Var}(X_i)
# + 2\sum_{\substack{i,j\in G(l)\\ i<j}} \mathrm{Cov}(X_i,X_j)\right].
# $$
#
# Then, taking the weighted average over groups, we have
#
# $$
# \mathbb{E}\bigl[\mathrm{Var}(\bar{X}\mid L)\bigr]
# =\; \sum_{l} p_l\,\mathrm{Var}(\bar{X}\mid L=l)
# =\; \frac{1}{N^2}\sum_{l} p_l \left[\sum_{i\in G(l)} \mathrm{Var}(X_i)
# + 2\sum_{\substack{i,j\in G(l)\\ i<j}} \mathrm{Cov}(X_i,X_j)\right].
# $$
#
# This term collects all the variances and the covariances for pairs within the same group.
#
# ##### 3. Between-Group Variance
#
# Next, consider the variance of the conditional means. For each group $l$, we have
#
# $$
# \mathbb{E}[\bar{X}\mid L=l] = \frac{1}{N}\sum_{i\in G(l)} \mathbb{E}[X_i].
# $$
#
# Then the between-group variance is
#
# $$
# \mathrm{Var}\bigl(\mathbb{E}[\bar{X}\mid L]\bigr)
# =\; \sum_{l} p_l \Bigl(\mathbb{E}[\bar{X}\mid L=l]\Bigr)^2
# -\; \Bigl(\sum_{l} p_l\,\mathbb{E}[\bar{X}\mid L=l]\Bigr)^2.
# $$
#
# This expression captures how the group averages differ from one another. When you expand the square, it essentially includes the contributions from the covariances of the means across different groups. In the full covariance expansion of $\mathrm{Var}(\bar{X})$, these are exactly the cross-group covariance terms
#
# $$
# \frac{2}{N^2}\sum_{l < k} \sum_{\substack{i\in G(l)\\ j\in G(k)}} \mathrm{Cov}(X_i,X_j).
# $$
#
# ##### 4. Adding the Two Parts Together
#
# Now, if you add the **within-group** part (from Step 2) and the **between-group** part (from Step 3), you recover all the terms in the full expansion
#
# $$
# \mathrm{Var}(\bar{X})
# =\; \frac{1}{N^2}\Biggl\{
# \underbrace{\sum_{l} \sum_{i\in G(l)} \mathrm{Var}(X_i)
# + 2\sum_{l}\sum_{\substack{i,j\in G(l)\\ i<j}} \mathrm{Cov}(X_i,X_j)}_{\text{all pairs within the same group}}
# + \underbrace{2\sum_{l<k} \sum_{\substack{i\in G(l)\\ j\in G(k)}} \mathrm{Cov}(X_i,X_j)}_{\text{all pairs in different groups}}
# \Biggr\}.
# $$
#
# This is exactly the same as the covariance expansion
#
# $$
# \mathrm{Var}(\bar{X})
# =\; \frac{1}{N^2}\sum_{i=1}^{N} \mathrm{Var}(X_i)
# +\; \frac{2}{N^2}\sum_{1\le i < j \le N}\mathrm{Cov}(X_i, X_j).
# $$
#
# Thus, by grouping the observations by $L$, the conditional (within-group) variance and the variance of the conditional means (between-group variance) add up to the total variance expressed as the sum of all individual variances and covariances.
#
# ---
#
# ##### 5. Summary
#
# - **Within-Group Component:**  
#   The term $\mathbb{E}\bigl[\mathrm{Var}(\bar{X}\mid L)\bigr]$ collects all contributions from the variances and covariances *inside* each group.
#   
# - **Between-Group Component:**  
#   The term $\mathrm{Var}\bigl(\mathbb{E}[\bar{X}\mid L]\bigr)$ captures the differences between the group averages, which mathematically corresponds to the covariances between observations from different groups.
#
# - **Overall Equivalence:**  
#   When you sum the two, you obtain the full expression for $\mathrm{Var}(\bar{X})$ as given by the covariance expansion. Therefore, the law of total variance is equivalent to writing the overall variance as the sum of individual variances and pairwise covariances (scaled by $\frac{1}{N^2}$).
#
# This completes the mathematical demonstration of the equivalence between the two forms.
#
# **End of Derivation**
#

#
# $$
# Var(\bar{X}) = 
# Var(\bar{X}) = \frac{\sigma^2 \; R_X \; R_Y}{M \; N},
# $$
#
# where the symbols mean the following:
#
# ## Definitions
#
# - **$X = \frac{1}{M} \sum Y_i$:** Each $X$ is an average of $M$ smaller units $Y_i$.
# - **$\bar{X} = \frac{1}{N} \sum X_i$:** $\bar{X}$ is the average of $N$ such $X_i$ values.
# - **$\sigma^2$:** The baseline variance if all measurements were independent.
# - **$R_Y \ge 1$:** A factor that accounts for the correlation among the $Y_i$ values within each $X$. If the $Y_i$ were i.i.d., then $R_Y=1$. Otherwise, $R_Y > 1$.
# - **$R_X \ge 1$:** A factor that accounts for the correlation among the $X_i$ values. If the $X_i$ were independent, then $R_X=1$. Otherwise, $R_X > 1$.
#
# ## Hierarchical Averaging Reduces Variance
#
# 1. **Averaging within each $X$: $M$ values of $Y_i$**
#
#    - If all $Y_i$ are i.i.d. with variance $\\sigma^2$, then averaging them gives:
#      
#      $$
#      Var(X) = \\frac{\\sigma^2}{M}.
#      $$
#      
#    - However, if the $Y_i$ are correlated, the variance reduction is not as large. A correlation factor $R_Y \\ge 1$ is introduced:
#      
#      $$
#      Var(X) = \\frac{\\sigma^2 \\; R_Y}{M}.
#      $$
#
# 2. **Averaging over $N$ of these $X_i$ values to obtain $\\bar{X}$**
#
#    - If the $X_i$ were i.i.d., we would have an additional variance reduction by a factor of $N$:
#      
#      $$
#      Var(\\bar{X}) = \\frac{1}{N} Var(X) = \\frac{\\sigma^2}{M \\; N}.
#      $$ 
#      
#    - With correlation among the $X_i$, we introduce another factor $R_X \\ge 1$, leading to:
#      
#      $$
#      Var(\\bar{X}) = \\frac{\\sigma^2 \\; R_X}{M \\; N}.
#      $$
#
# ## Final Formula and Interpretation
#
# Combining the two effects of correlation from both levels, the overall variance of the hierarchical average is given by:
#
# $$
# Var(\\bar{X}) = \\frac{\\sigma^2 \\; R_X \\; R_Y}{M \\; N}.
# $$
#
# This formula shows that:
#
# - The **total number of measurements** is $M \\times N$, which is in the denominator.
# - The **correlation factors** $R_Y$ and $R_X$ account for the covariance among the $Y_i$ values within each $X$ and among the $X_i$ values, respectively. If all values were independent, then $R_Y = R_X = 1$, and the variance would reduce by the full factor of $1/(M \\; N)$.
#
# In real applications (such as traffic or environmental data), measurements are often correlated, so these factors are essential to accurately reflect the variance of the average.
#



# <div class="alert alert-success" role="alert">
#
# 1. The definition of CVs
#
# </div>

# <div class="alert alert-danger" role="alert">
#     
# 1. **Definition of CVs**: The coefficients of variation (CVs) for flow rates and densities are defined within each Edie’s domain.  
# - **Effect of Domain Size**: The chosen domain size influences their distribution. While the __population mean__ remains consistent, the __variance__ decreases as domain size increases due to the smoothing effect of aggregation.
#
# 2. **Domain Subdivision**:  
# - **Illustration**: The full time-space domain is subdivided into smaller domains of size $m \times n$ and larger domains of size $5m \times 5n$. This figure only shows trajectories in Lane 1.
# - <img src ='https://github.com/jooneui/fig_collection/blob/main/Domain%20example.jpg?raw=true' align = 'center' width=40%>
#
# 3. **Population mean**
# - **Mathematical Expression**: The VMT in the larger domain $\Omega_{5m,5n}$ equals the sum of VMTs from smaller $\Omega_{m,n}$ subdomains:
#     - $VMT(1,1; \Omega_{5m,5n}) = \sum_{x=1}^5 \sum_{t=1}^5 VMT(x,t; \Omega_{m,n}).$
#     - __Accuracy of Traffic Calculations__: The domain size must be significantly larger than the intervals used to record data, as discrete intervals can omit parts of continuous trajectories.
# - **Consistency in Averages**: The average traffic flow rates in a larger domain ($\Omega_{5m,5n}$) match the average across smaller domains ($\Omega_{m,n}$):  
#      $q_l(1,1; \Omega_{5m,5n}) = \frac{\sum_{x=1}^5 \sum_{t=1}^5 q_l(x,t; \Omega_{m,n})}{25}.$  
#     - This relationship holds for densities when VMT is replaced by VHT.
# 4. **Variance**
# - Lane-to-lane variance in $\Omega_{5m,5n}$ can be expressed by using the smaller $\Omega_{m,n}$ subdomains.
# -  $s^2(1,1;\Omega_{5m,5n})=\frac{\sum_{l=1}^4(q_l(1,1;\Omega_{5m,5n})-\bar{q}(1,1;\Omega_{5m,5n}))^2}{4} =\frac{\sum_{l=1}^4(\frac{\sum_{x=1}^5 \sum_{t=1}^5 q_l(x,t;\Omega_{m,n})}{25}-\frac{\sum_{x=1}^5 \sum_{t=1}^5 \bar{q}(x,t;\Omega_{m,n})}{25})^2}{4}=\frac{\sum_{l=1}^4((q_l(1,1;\Omega_{m,n})-\bar{q}(1,1;\Omega_{m,n}))+...+(q_l(5,5;\Omega_{m,n})-\bar{q}(5,5;\Omega_{m,n})))^2}{4\cdot25^2}$ -- __Eq(1)__
# - Eq(1) can have different values depending on the level of dependence between different $x$ and $t$. The two extreme case is as follows.
#     - **Independence Case**: If $q_l(x,t; \Omega_{m,n})$ values are independent, the variance decreases as domain size increases:
#         - $\text{Cov}(q_l(x,t; \Omega_{m,n}), q_l(x',t'; \Omega_{m,n})) = 0\quad \text{for } x \neq x' \text{ and } t \neq t'$.
#         - Under this assumption, the total variance is __reduced by a factor equal to the number of subdomains__ compared to the average variance of the subdomains.
#             - $s^2(1,1; \Omega_{5m,5n}) = \frac{\sum_{x=1}^5 \sum_{t=1}^5 s^2(x,t; \Omega_{m,n})}{(5 \cdot 5)^2}=\frac{\bar{s}^2(\Omega_{m,n})}{25}$
#     - **Dependence Case**: If $q_l(x,t; \Omega_{m,n})$ values are fully dependent, the variance remains __constant__ regardless of domain size:
#         - $\text{Cov}(q_l(x,t; \Omega_{m,n}),q_l(x',t'; \Omega_{m,n})) = \sigma^2 \quad \text{for all} \quad x, x' \in X \quad \text{and} \quad t, t'\in T$
#         - $s^2(1,1;\Omega_{5m,5n})=\frac{25\cdot25\cdot \sigma^2}{25\cdot25}=\sigma^2$
# - In practice, traffic states are neither fully dependent nor independent. As a result, variance typically decreases as the domain size increases.
#     - **Small Domains**: High variance due to individual vehicle differences.  
#     - **Larger Domains**: Individual differences average out, the variance is expected to stabilizes, reflecting intrinsic lane-to-lane differences.  
# - __Identifying the stabilization point is essential for distinguishing malfunctioning sensors from functioning ones.__
#
# </div>

# + [markdown] tags=["main", "slides"]
# ## Hypothesis test

# + [markdown] jp-MarkdownHeadingCollapsed=true
# <div class="alert alert-success"> 
#
# In our study, we use a hypothesis testing approach to determine the threshold for lane-to-lane variation. First, we choose the population mean for lane-to-lane variations from normal sensors, denoted as $\mu$, as the parameter to test. Our alternatvie hypothesis $H_a$ posits that the population mean of lane-to-lane variations from normal sensors is less than a specified value $\mu_0$: $H_a : \mu < \mu_0$. Conversely, the null hypothesis $H_0$ states that the population mean of lane-to-lane variations is equal to $\mu_0$: $H_0 : \mu = \mu_0$.  To ensure the data distribution is approximately normal, we perform a normality check using frequency histrogram and Shapiro-Wilk test. If normality is confirmed, the test statistic $t$ is then calculated using the formula $t=\frac{\bar{y}-\mu}{s/\sqrt{n}} \text{ ~ } t(n-1)$, where $\bar{y}$ is the sample mean of lane-to-lane variations, $s$ is the sample standard deviation, and $n$ is the sample size. We set the significance level $\alpha$ and determine the rejection area for the test statistic: $t\le -t(\alpha,n-1)$. In the experiment step, we collect sample data of lane-to-lane variations $y^i_{jk}$ and calculate the sample mean $\bar{y}$: $\bar{y}=\frac{\sum_i\sum_j\sum_k y^i_{jk}}{n}$. We then compute the test statistic $t$ and compare it with the critical value. If $t\le -t(\alpha,n-1)$, we reject the null hypothesis $H_0$ in favor of the alternatvie hypothesis $H_a$; otherwise, we cannot reject $H_0$. 
# In our study, we compared the distribution of lane-to-lane variations between malfunctioning and healthy sensors to set $\mu_0$ before conducting the hypothesis test. If the null hypothesis is not rejected, we repeat the test with a new $\mu_0$ until it falls into the rejection area. This process allows us to determine a statistically significant threshold for lane-to-lane variations, helping identify significant deviations from normal traffic patterns.
#
# </div>    
# -

# - Normality check
#     - The test relies on the sample mean’s distribution being normal (or approximately normal), which holds true if the population is normal or if the sample size is large. (our case is 56, which is large enough to verify it as normal)

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["slides", "main"]
# - Step2) Determine alternative hypothesis: $H_a$
#     - Our objective of conducting hypothesis test is to identify a threshold value that is significantly different from the population mean of lane-to-lane variations from normal sensors (not the population mean from all types of detectors). 
#     - Therefore, I believe the parameter should be specified as the population mean of normal detectors. 
#         - This approach is not about the data we currently have but about what we want to demonstrate. 
#         - By specifying this, we can clearly define the direction of the alternative hypothesis as "less than." 
#         - Additionally, this specification justifies the use of ground-truth data (NGSIM) for our sample, as it represents the CV of "normal" detectors.
#         
# <img src="https://github.com/jooneui/fig_collection/blob/main/CV_threshold_flow_v2.jpg?raw=true" align='center' width = 60%> <br>

# + [markdown] jp-MarkdownHeadingCollapsed=true
# In our stduy, the $\mu_0$ is predetermined after comparing the lane-to-lane variations with malfunctioning and healthy sensors. If the null hypothesis is not rejected, we can repeat the test with defining another value for the $\mu_0$ until finding out the $\mu_0$ that falls into the rejection area.

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["past"]
# <div class="alert alert-danger">  
#
# - Framework
#     - Step2) Determine alternative hypothesis: $H_a$
#         - The test is based on the groundtruth data from NGSIM. Therefore, our hypothesis needs to address the range of true data, not relating to the malfunctioning data.
#              - If we want to claim such like "$H_a$: CV of malfunctioning detector data is over 0.2", we need to use the sample of the malfunctioning data.
#             - Therefore, left-tailed test (less than) is more supported as the sample mean of the CV is expected to be less than the hypothesized value (upper threshold).
#         - In the meantime, last week, we discussed setting a critical value at a 1% significance level as the upper threshold. 
#             - However, finding a critical value without a hypothesized value is impossible. Instead, set the upper threshold (e.g., 0.2) as the hypothesized value.
#             - And the 1st approcah is clear in that predefined upper threshold, and this is less senstive to variations in CV sample data.
#     - Step4) Normality check
#         - $H_0$:  the population is normally distributed
#     - Step9) Power
#         - This hypothesis is emphasized on filtering normal detector, by minimizing type 1 error.
#             - type 1 error: "$H_0$ rejected but $H_0$ was true"(= minimizing probaility of CV abnormal actually, but judged as normal)
#         - However, our focus is to minimize the case when normal CV being regarded as abnormal CV
#             - type II error: probability of regarded abnormal CV(not reject H0), but actually normal CV(Ha)
#         - power($1-\beta$) needs to be large enough(about 80%)
#             - This explains why we need to set conservative(high) threshold value
#             - Unclear to set the hypothesis value of $H_a$, but I set around sample CV mean(0.09)
#                 - 1% significance level shows 100% power.
#                 - Moreover, high power is necessary because it decrease the possibility of "the CV was not rejected, but it was actually not true"(="the CV was judged as malfunctiong, but it actually was normal)
#                 - Reducing type 1 error refers to "the CV was rejected, but it was actually true"(="the CV was judged as functioning, but it actually was abnormal.") 
#                 - Having the high null hypothesis value resolve(=decrease) the both cases.
#         - ※ Power = $1-\beta = p(H_0 reject|H_0 not true)= p(\frac{\bar{X}-k_0}{\sigma/\sqrt{n}}<-t_{(\alpha,n-2)}|k=k_1)=p(\frac{\bar{X}-k_0}{\sigma/\sqrt{n}}-\frac{k}{\sigma/\sqrt{n}}<-t_{(\alpha,n-1)}-\frac{k}{\sigma/\sqrt{n}}|k=k_1)=p(\frac{\bar{X}-k}{\sigma/\sqrt{n}}<-t_{(\alpha,n-1)}-\frac{k-k_0}{\sigma/\sqrt{n}}|k=k_1)=p(\frac{\bar{X}-k_1}{\sigma/\sqrt{n}}<-t_{(\alpha,n-1)}-\frac{k_1-k_0}{\sigma/\sqrt{n}})$
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/CV_threshold_flow_1.jpg?raw=true" align='center' width = 50%> <br>
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/error type_depiction.jpg?raw=true" align='center' width = 100%> <br>
#
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["past"]
# <div class="alert alert-danger">  
#
# - [A. T. McKay, 1932](https://www.jstor.org/stable/pdf/2342041.pdf)
#     - Step1) Define the distribution of mean and std for __samples of n from a normal population__ defined by the parameters $m$ and $\sigma$
#         - $f_X(\bar{x})$ 
#             - $X$ ~ $N(\mu,\sigma^2)$
#             - $f_X(x_1,x_2,...,x_n)=\Pi_i \frac{1}{\sqrt{2\pi}\sigma}e^{-1/2[(x_i-\mu)/\sigma]^2} \delta x= (\frac{1}{2\pi})^{n/2}\frac{1}{\sigma^n}e^{-1/2\sum[(x_i-\mu)/\sigma]^2}\delta x$
#             - sample mean is a linear combination of $x_i$'s. If $x_1,x_2,...,x_n$ are independent and normally distributed, any linear combination of them is also normally distributed.
#                 - $E[\bar{x}]=\mu$
#                 - $Var(\bar{x})=\frac{\sigma^2}{n}$
#             - $f_{\bar{X}}(\bar{x})=(\frac{n}{2\pi\sigma^2})^{\frac{1}{2}}\cdot e^{-\frac{(\bar{x}-m)^2\cdot n}{2\sigma^2}}\cdot d\bar{x}$
#         - $f_S(s)$ ($s$: sample standard deviation)
#             - $u=\sum_{i=1}^n(\frac{x_i-\bar{x}}{\sigma})^2 \sim \chi_{n-1}$: sum of squared deviations normalized by expected values
#             - $u=\frac{N}{\sigma^2}\cdot\frac{\sum(x_i-\bar{x})^2}{N}=\frac{N}{\sigma^2}\cdot s^2$
#             - pdf: $f(x;k)=\frac{1}{2^{k/2}\Gamma(k/2)}x^{(k/2)-1}e^{-x/2}, x>0. k \text{: degrees of freedom}$
#             - $f_S(s)=(\frac{n}{2\sigma^2})^{\frac{n-1}{2}}\cdot \frac{2 s^{n-2}e^{-ns^2/2\sigma^2}\cdot }{\Gamma(\frac{n-1}{2})}\delta s$
#                 - $u=\frac{n}{\sigma^2}\cdot s^2$
#                 - $\delta u = 2s\cdot \frac{n}{\sigma^2}\delta s$
#     - Step2) Define the joint distribution($h(\bar{x},v)$) of sample mean($\bar{x}$) and sample coefficient of variation($v$) from $k(\bar{x},s)$
#         - Define joint distribution $k(\bar{x},s)=f_{\bar{X}}(\bar{x})\cdot f_{S}(s)$
#             - $f_{\bar{X}}(\bar{x})$ and $f_S(s)$ are independent in that the value of each variable does not impact the other's distribution.
#         - Define $v$ as sample CV: $v=s/\bar{x}$
#         - Transform $k(\bar{x},s)=f_{\bar{X}}(\bar{x})\cdot f_S(s)$ to $h(\bar{x},v)=f_{\bar{X}}(\bar{x})\cdot f_{V}(v)$
#             - by substitute $s$ to $\bar{x}\cdot v$
#             - $\delta s = \delta \bar{v} \cdot \bar{x}$   
#     - Step3) Calculate marginal distribution: $f_V                                    (v) = p_v \delta v = \int_{-\infty}^{\infty}h(\bar{x},v) \delta \bar{x}$
#         - $p_v \delta v = (\frac{n}{\sigma^2})^{n/2}\cdot\frac{v^{n-2}\delta v}{2^{\frac{n-1}{2}}\sqrt{\pi}\Gamma(\frac{n-1}{2})}\cdot\int_{-\infty}^{\infty}\bar{x}^{n-1}e^{-n[v^2\bar{x}^2+(\bar{x}-m)^2]/2\sigma^2}d\bar{x}$
#     - Step4) $ \frac{nv^2(m^2/\sigma^2+1)}{1+v^2}=\frac{nv^2}{1+v^2}\frac{k^2+1}{k^2}$ is approximate to $\chi^2_{n-1}$
#         - $k=\sigma/m$: population CV
#         - $v$: sample CV
#         - $n$: the number of sample
#     - Confidence Interval
#         - lcl = $\frac{v}{\sqrt{(\frac{u_1}{n}-1)v^2+\frac{u_1}{n-1}}}$ (where $u_1=\chi^2_{1-\alpha/2,n-1}$)
#         - ucl = $\frac{v}{\sqrt{(\frac{u_2}{n}-1)v^2+\frac{u_2}{n-1}}}$ (where $u_2=\chi^2_{\alpha/2,n-1}$)
# - Vangel(1996)
#     - Mckay(1932) does not applicable to when sample size is small
#         - $\frac{nv^2}{1+v^2}\frac{k^2+1}{k^2}$
#             - $lim_{v→0}(\frac{nv^2}{1+v^2}\frac{k^2+1}{k^2})=0$
#             - $lim_{v→\infty}(\frac{nv^2}{1+v^2}\frac{k^2+1}{k^2})=\frac{n(k^2+1)}{k^2}=n(1+1/k^2)$
#                 - no applicable when sample size(n) is small or sample CV($k$) is larger than 0.3
#     - Vangel defined r.v. $Q = \frac{v^2(1+k^2)}{(1+\theta v^2)k^2}$ (where $\theta$ is given function)
#         - Mckay(1932): $\theta = \frac{n-1}{n}$, and $Q \sim \chi^2_{n-1}$
#         - Vangel(1996): $\theta = \frac{n-1}{n}[\frac{2}{\chi_{n-1,\alpha}}+1]$, and $Q \sim \chi^2_{n-1}$ 
#     - Confidence Interval
#         - $H_0: v=k$, $H_1: v\neq k$ 
#         - lcl = $\frac{v}{\sqrt{(\frac{u_1+2}{n}-1)v^2+\frac{u_1}{n-1}}}$ (where $u_1=\chi^2_{1-\alpha/2,n-1}$)
#         - ucl = $\frac{v}{\sqrt{(\frac{u_2+2}{n}-1)v^2+\frac{u_2}{n-1}}}$ (where $u_2=\chi^2_{\alpha/2,n-1}$)
# </div>      

# + [markdown] tags=["slides", "main"]
# # Setting Upper Threshold
#

# + [markdown] jp-MarkdownHeadingCollapsed=true
#
# - The logic
#     - The neccessity of having sample data from healthy sensors to conduct hypothesis test
#     - NGSIM explanation
#     - Calculate the lane-to-lane variation using NGSIM
#     - Setting population parameter
#         - It is essential to determine the population parameters in advance. 
#         - We established threshold values, and these thresholds were derived from an empirical comparison of lane-to-lane variations between normal and malfunctioning detector datasets. 
#         - The empirical data consistently demonstrated a clear separation at these values, providing strong empirical evidence for selecting population parameters.

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["main"]
# <div class="alert alert-success">
# Data from healthy sensors can be regarded as ground truth data because they accurately detect the real traffic conditions. It is crucial to have sample data from these healthy sensors in order to conduct hypothesis tests about the population mean of lane-to-lane variations. For this purpose, we selected the Next Generation SIMulation (NGSIM) I-80 vehicle trajectory dataset, which offers robust evidence to qualify it as ground truth data. The NGSIM dataset comprise of US-101 and I-80 trajectory datasets. In our study, we used I-80 trajectory dataset as it was only datasets manual transcription was conducted after video transcription, which gurantees the accuracy and completeness of the dataset. 
# <br>
#   
# The I-80 trajectory dataset was collected on a segment of I-80 freeway in Emeryville (San Francisco), California. The segment is approximately 500m in length, and contains 6 lanes, including a high occupancy vehicle (HOV) lane. The dataset was originally collected by using cameras, mounted from the top of a 30-story building adjacent to the freeway, and then extracted from the resulting videos with a 0.1 sec frequency. The dataset were collected within two periods, i.e., 15 min ranging from 4:00 p.m. to 4:15 p.m. on April 13, 2005, and 30 min ranging from 5:00 p.m. to 5:30 p.m. on April 13, 2005. These periods represent the buildup of congestion, or the transition between uncongested and congested conditions, and full congestion during the peak period.
# </div>
#

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["past"]
# <div class="alert alert-danger"> 
#
# __6/13/2024__
# - The CV at each time interval is an estimate derived from the sample data,
#     - so it represents a summary statistic rather than a single data point.
# - and each of these CVs has a distinct 100$\alpha$% critical value and a 100(1-$\alpha$)% confidence interval.
# - In the hypothesis testing,
#     - H0: $\text{Population CV} = k$. (or $\text{Population CV} \le k$), (where $k$ is upper threshold of population CV)
#     - H1: $\text{Population CV} > k$
# - This means that $k$ is within the interval for 100(1-$\alpha$)% of the CIs. 
#     - Let's say these are 95% Confidence intervals.
#     - The k, which is the hypothesized value, must fall inside for the 95% of entire CIs.
# - To identify the value that falls inside for the 100(1-$\alpha$)% CIs, 
#     - I calculate the values of upper limits for the entire CIs
#     - and find out 5% value and set it as $k$.
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/Upper%20threshold%20process.jpg?raw=true" align='center' width = 80%> <br>
#
# </div> 

# + [markdown] tags=["main", "slides"]
# ## Define groundtruth data
# - groundtruth data 필요한 이유: 위의 test 진행하려면 groundtruth data 정의 필요
# - The ability to position the camera with sufficient mounting height at an optimized mounting location for a given application impacts the data measurement accuracy. For these reasons, most manufacturers will not provide a confidence interval for their measurement accuracy specifications [60]. Klein [2, Ch. 9] elaborates on the advantage of pairing a confidence interval with an accuracy specification. (Roadside Sensors for Traffic Management, 2024)
#
# - NGSIM
#     - The NG-VIDEO software, a customized application developed for the NGSIM program, was used to transcribe the vehicle trajectory data from the video. This software automatically detected and tracked most vehicles from the video images
#     - __manual transcription__ was also used for any vehicles that were not automatically detected. This dual approach enhances the accuracy and completeness of the data .
# - 해당 논문 참고": Detection of anomalous vehicles using physics of traffic(Groundtruth data 논리 전개 어떻게 했는지)
# - __how to set the true value in different location and time range??__

# + [markdown] hide_input=true tags=["slides"]
# ##### __Issues for hypothesis test__
# - normality test: sample size is too small to see the normality
# - it is based on sample standard deviation

# + [markdown] tags=["slides", "main"]
# ## Upper threshold by NGSIM

# + [markdown] tags=["slides", "main"]
# ### Location
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/NGSIM_location.png?raw=true" align='center' width = 50%> <br>

# + [markdown] tags=["slides"]
# ### Calculation Process
# - Pre-processing the data
#     - Global time: elapsed time in milliseconds since January 1, 1970.
# - Calculate travel times and distance of each vehicle
#     - Distinguish between cases where the same vehicle is in different lanes.
#     - Additionally, if a vehicle switches to another lane and then returns to the original lane, the travel times and distances in the original lane should exclude the periods when the vehicle was in the other lane. 
# -

# ### calculation code

# + tags=["code"]
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


# + tags=["code"]
def NGSIM_preprocessing(data, start_location, end_location):
    # Lane 1: HOV lane
    # Lane 7: On-ramp at Powell Street
    # Set up the space boundary within which all vehicle trajectories are available

    filter_index =  (data['Lane_ID'] != 7) & (data['Lane_ID'] != 1) & (data['Local_Y'] < end_location) & (data['Local_Y'] >= start_location)
    data_filter = data[filter_index]
    
    return data_filter                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  

def NGSIM_timeconvert(file_name, data, unit_time_interval, analysis_time_interval, start_location, end_location):
    """
    Converts global time in the NGSIM dataset to local time and filters data based on local Y coordinates.
    
    Parameters:
        file_name (str): The name of the file containing the data.
        data (pd.DataFrame): The data containing 'Global_Time' and 'Local_Y' columns.
        unit_time_interval (int): The unit time interval in seconds. Default is 30 seconds.
        analysis_time_interval (int): The time interval for analysis in seconds. Default is 300 seconds.
    
    Returns:
        pd.DataFrame: Filtered data with added 'Local_Time(sec)' and 'Time_interval' columns.
        float: The last time interval from the end time.
    """
    
    # Base time in milliseconds from 1/1/1970 to 4/12/2005 : 1113350400000 (4/13/2005 4:00PM start)
    base_time = 1113350400000 
    
    # Extract hour and minute from filename and convert to local time in milliseconds
    hour = int(file_name[-12:-11]) + 19  # Adjusting for 12-hour format and 7-hour GMT to PST gap
    minute = int(file_name[-11:-9])
    file_time_offset = (hour * 3600 + minute * 60) * 1000
    
    # Convert global time to local time in seconds
    local_time_ms = data['Global_Time'] - (base_time + file_time_offset)
    data['Local_Time(sec)'] = local_time_ms / 1000
    
    # Determine min and max local time for vehicles in specific local Y coordinates
    # 5 feet buffer is applied because not all vehicles mark at the exact start- and end-location.
    min_time = data.loc[data['Local_Y'] > (end_location-5), 'Local_Time(sec)'].min()
    max_time = data.loc[data['Local_Y'] < (start_location+5), 'Local_Time(sec)'].max()
    
    # Calculate start and end times rounded to the nearest unit time interval
    # Use "unit_time_interval" instead of min_time to set the starting point as a multiple of unit_time_interval
    ## Example:
    ## min_time: 25.2 sec, unit_time_interval: 30 sec, analysis_time_interval: 300 sec
    #### Without unit_time_interval: 1st subdomain: 25.2 sec, 2nd: 325.2 sec, 3rd: 625.2 sec (not straightforward)
    #### With unit_time_interval: 1st subdomain: 30 sec, 2nd: 330 sec, 3rd: 630 sec (more straightforward)
    start_time = ((min_time // unit_time_interval) + 1) * unit_time_interval
    end_time = (max_time // unit_time_interval) * unit_time_interval
  
    # Filter data to include only the desired time range
    time_filter = (data['Local_Time(sec)'] >= start_time) & (data['Local_Time(sec)'] <= end_time - 0.1)
    data = data[time_filter]
    
    # Define the time sub-domain interval ID
    print(analysis_time_interval, analysis_space_interval)
    data['Time_interval'] = (data['Local_Time(sec)'] - start_time) // analysis_time_interval
    
    
    row_num = [ (idx, len(data[data['Time_interval'] == idx])) for idx in data['Time_interval'].unique()]
    
    
    # Calculate the last time interval from the end time
    last_time_interval = end_time - (data['Time_interval'].max() * analysis_time_interval + start_time)
    
    return data, last_time_interval


# + tags=["code"]
def NGSIM_spacedomain(data, space_interval, start_location, end_location):
    
    # Define the space sub-domain interval ID
    data['Space_interval'] = (data['Local_Y'] - start_location) // space_interval
    
    # Calculate the last space interval from the end point
    last_space_interval = end_location - (data['Space_interval'].max()*space_interval + start_location)
    
    return data, last_space_interval


# + jupyter={"source_hidden": true} tags=["code"]
def segment_by_lane(data):
    """
    VMT: Sum of each vehicle's traveled distance within each sub-domain for each lane
    VHT: Sum of each vehicle's traveled time within each sub-domain for each lane

    Each vehicle's traveled distance in lane i: Location at the last timeframe in lane i - Location at the earliest timeframe in lane i
    Each vehicle's traveled time in lane i: Last timeframe in lane i - Earliest timeframe in lane i

    Note: This method doesn't account for lane changes where a vehicle returns to the original lane. 
    To handle this, assign a different number each time a vehicle changes lanes by defining 'Lane_Change_Group' and separate the dataset for each vehicle when this variable changes.
    """
    
    data = data.sort_values(by=['Vehicle_ID', 'Frame_ID'])
    data['Lane_Change_Group'] = (data['Lane_ID'] != data['Lane_ID'].shift(1)).cumsum()
    
    return data


# + tags=["code"]
"""
Plotting the trajectory of each vehicle
x-axis: lateral position(ft)
y-axis: longitudinal position(ft)
"""

def NGSIM_plot_trajectory(data):
        
        vehicle_data = {}
        veh_id_set = np.unique(data['Vehicle_ID'])
        
        for i, vehicle_id in enumerate(veh_id_set):
            
            vehicle_individual = data[data['Vehicle_ID'] == vehicle_id]
            vehicle_data[i] = vehicle_individual

            fig, ax = plt.subplots(1,1,figsize=(6,6))
            ax.scatter(vehicle_individual['Local_X'], vehicle_individual['Local_Y'], s=10)
            ax.set_title(f'Vehicle (ID: {vehicle_id}) trajectory',fontsize = 12)
            ax.set_xlabel('lateral position(ft)',fontsize = 10)
            ax.set_ylabel('longitudinal position(ft)',fontsize = 10)
            ax.grid(True)
            ax.set_ylim(0,1700)
            ax.set_yticks(range(0,1700,100))
            ax.set_xlim(0,100)
            ax.set_xticks(range(0,100,5))
            plt.savefig(f'./02 fig/05 NGSIM/01 trajectory/vehicle_trajectory_{vehicle_id}.png')

            plt.close()


# + tags=["code"]
"""
Plotting the trajectory of each vehicle
x-axis: Time space interval: 10*Time interval number + Space interval number
y-axis: q,k,u
"""

def plot_lane_aggregates(data, file_name):

    # data['Time_space_interval'] = data['Time_interval'].to_string() + '.' + data['Space_interval'].to_string()
    data['Time_space_interval'] = data['Time_interval']*10 + data['Space_interval']
    

    cmap = plt.cm.viridis
    norm = plt.Normalize(data['Lane_ID'].values.min(), data['Lane_ID'].values.max())
    
    fig, ax = plt.subplots(1,3,figsize=(18,4))
    var_list = ['q','k','u']
    unit_list = ['vph','vpm','mph']
    max_list = [2000,200,50]
    
    for i, data in data.groupby("Lane_ID"):

        for j in range(3):
            ax[j].scatter(data['Time_space_interval'], data[var_list[j]], s=5, c=cmap(norm(data['Lane_ID'].unique())), cmap='viridis', label=f'Lane {data["Lane_ID"].unique()}')
            ax[j].set_title(f'{var_list[j]} over time-space',fontsize = 15)                    
            ax[j].set_xlabel('Time_space interval',fontsize =12)
            ax[j].set_ylabel('Time_space interval',fontsize =12)
            ax[j].set_ylabel(f'{var_list[j]}{unit_list[j]}',fontsize =12)
            ax[j].grid(True)
            ax[j].legend()

            ax[j].set_ylim(0,max_list[j])
            ax[j].set_yticks(np.arange(0,max_list[j],max_list[j]/10))

            ax[j].set_xlim(-1,30)
            ax[j].set_xticks(range(0,31,10))
            
    plt.savefig(f'./02 fig/05 NGSIM/traffic state over time,space domain{file_name}.png')

# + tags=["code"]
"""
This step is to 
1) calculate VMT, VHT
2) calculate u,q,k

"""

def compute_lane_aggregates(veh_aggregates_df, analysis_time_interval, analysis_space_interval, last_time_interval, last_space_interval, file_name):
    
    # Calculate the total VMT and VHT per each lane
    lane_aggregates_df = veh_aggregates_df.groupby(['Time_interval', 'Space_interval', 'Lane_ID']).agg(
        total_travel_time=('travel_time', "sum"),
        total_travel_distance=('travel_distance', "sum"),
        vehicle_count=('Vehicle_ID', "count")
    ).reset_index()

  
    # Calculate flow (q:vpmpl), density (k:vpmpl), and speed (u:mph)
    lane_aggregates_df['q'] = (lane_aggregates_df['total_travel_distance'] / 5280) / ((analysis_time_interval / 3600) * (analysis_space_interval / 5280))
    lane_aggregates_df['k'] = (lane_aggregates_df['total_travel_time'] / 3600) / ((analysis_time_interval / 3600) * (analysis_space_interval / 5280))
    lane_aggregates_df['u'] = lane_aggregates_df['q'] / lane_aggregates_df['k']

    lane_aggregates_df.insert(0, 'file_name', file_name)
    
    # At the last time interval, 'last_time_interval' needs to be applied to the time domain(E)
    conditions = [('Time_interval', last_time_interval, analysis_time_interval, 'time'), 
                  ('Space_interval', last_space_interval, analysis_space_interval, 'space')]
    
    last_indices = {}
    conversion_factors = {}
    
    for interval_type, last_interval, analysis_interval, label in conditions:
        if last_interval != 0:
            last_index = lane_aggregates_df[interval_type] == lane_aggregates_df[interval_type].max()
            last_indices[label] = last_index
            conversion_factor = analysis_interval / last_interval
            conversion_factors[label] = conversion_factor

            lane_aggregates_df.loc[last_index, 'q'] *= conversion_factor
            lane_aggregates_df.loc[last_index, 'k'] *= conversion_factor

    
    # if ('time' in conversion_factors) and ('space' in conversion_factors):
    #     # At the last space & time interval, 'last_time_interval' for the time domain(E)' and last_space_interval' for the space domain(L) & 
    #     last_time_space_index = last_indices['time'] & last_indices['space']
    #     print('last_time_space_index',last_time_space_index)
    #     time_space_conversion = conversion_factors['time'] * conversion_factors['space']
        
    #     lane_aggregates_df.loc[last_time_space_index, 'q'] *= time_space_conversion
    #     lane_aggregates_df.loc[last_time_space_index, 'k'] *= time_space_conversion
    
    return lane_aggregates_df


# + jupyter={"source_hidden": true} tags=["code"]
def compute_cv_metrics(lane_aggregates_df, last_time_interval, last_space_interval):
    
    cv_metrics_df = lane_aggregates_df.groupby(['Time_interval', 'Space_interval']).agg(
        flow_CV=('q', lambda x: x.std(ddof=0) / x.mean()),
        density_CV=('k', lambda x: x.std(ddof=0) / x.mean()),
        speed_CV=('u', lambda x: x.std(ddof=0) / x.mean())
    ).reset_index()
    
    cv_metrics_df['mean'] = cv_metrics_df[['flow_CV', 'density_CV', 'speed_CV']].mean(axis=1)
    cv_metrics_df['var'] = cv_metrics_df[['flow_CV', 'density_CV', 'speed_CV']].var(axis=1,ddof=1)
    
    return cv_metrics_df


# + tags=["code"]
"""
Plotting the trajectory of all vehicles
x-axis: Timeframe
y-axis: longitudinal position(ft)
"""

def NGSIM_plot_total_trajectory(data):
    
    fig, ax = plt.subplots(1,1,figsize=(12,4))
    ax.scatter(data['Frame_ID'], data['Local_Y'], s=5, c=data['Vehicle_ID'], cmap='viridis', alpha=0.7)
    ax.set_title('vehicles\' trajectory over entire time-space domain',fontsize = 20)
    ax.set_xlabel('Timeframe',fontsize = 15)
    ax.set_ylabel('Longitudinal position(ft)',fontsize = 15)
    ax.grid(True)
    ax.set_ylim(0,1700)
    ax.set_yticks(range(0,1700,100))
    ax.set_xlim(int(data['Frame_ID'].min()),int(data['Frame_ID'].max()))
    ax.set_xticks(range(int(data['Frame_ID'].min()),int(data['Frame_ID'].max()),(int(data['Frame_ID'].max())-int(data['Frame_ID'].min()))//20))
    
    ax.text(0.68, 0.1, 'Each color represents a different vehicle\'s trajectory', 
        transform=ax.transAxes, fontsize=15, ha='center', 
        bbox=dict(facecolor='white', alpha=0.8))
    
    plt.savefig(f'./02 fig/05 NGSIM/vehicle_total_trajectory.png')

    plt.close()


# -

os.getcwd()

# +
# Define the path to the dataset
NGSIM_path = '/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/BPR/11 Rawdata/NGSIM'

# Columns to load from each file
columns_to_load = [
    'Vehicle_ID', 'Frame_ID', 'Global_Time', 'Local_X', 'Local_Y', 'Global_X', 'Global_Y',
    'v_Length', 'v_Width', 'v_Vel', 'v_Acc', 'Lane_ID', 'Preceding', 'Following', 'Space_Headway', 'Time_Headway'
]

# Prepare a DataFrame to store Coefficients of Variation (CV) for the traffic metrics
agg_cv_metrics_df = pd.DataFrame(columns=['Time_interval', 'Space_interval', 'flow_CV', 'density_CV', 'speed_CV', 'mean', 'var'])
agg_lane_aggregates_df = pd.DataFrame(columns=['file_name', 'Time_interval', 'Space_interval', 'Lane_ID', 'total_travel_time', 'total_travel_distance', 'vehicle_count', 'q', 'k', 'u'])

# List CSV files in the specified directory
NGSIM_files = [file for file in os.listdir(NGSIM_path) if file.endswith('.csv')]

# Define time and space intervals
## 1. setting the entire time-space domain
#unit_time_interval is to define a starting point from a multiple of unit_time_interval
unit_time_interval = 30  # seconds
start_location = 100
end_location = 1600

## 2. setting analysis point
#analysis_time_interval is related with data analysis
# it should be larger enough than the raw_data time frame (0.1sec)
def find_divisors(n):
    return [i for i in range(3, n+1) if n % i == 0]

agg_time_interval = 600 # seconds
agg_space_interval = 1200 # ft(total segment length: 1600ft)

set_analysis_time_interval = find_divisors(agg_time_interval)
set_analysis_space_interval = find_divisors(agg_space_interval)

print(set_analysis_time_interval)
print(set_analysis_space_interval)

# + tags=["code"]
# Process each file

agg_cv_metrics_df = pd.DataFrame()

for analysis_time_interval in set_analysis_time_interval:
    for analysis_space_interval in set_analysis_space_interval:

        for file_name in NGSIM_files:
            full_path = os.path.join(NGSIM_path, file_name)
            data = pd.read_csv(full_path, usecols=columns_to_load)
            
            # Plotting the trajectory of all vehicles (x-axis: Timeframe, y-axis: longitudinal position(ft))
        #     NGSIM_plot_total_trajectory(data)
            
            # Preprocess data using custom functions
            data_filter = NGSIM_preprocessing(data, start_location, end_location)
            data_filter, last_time_interval = NGSIM_timeconvert(file_name, data_filter,unit_time_interval, analysis_time_interval, start_location, end_location)
            data_filter, last_space_interval = NGSIM_spacedomain(data_filter, analysis_space_interval, start_location, end_location)
            data_filter = segment_by_lane(data_filter)
            
            # Group data by specific intervals and vehicle attributes
            veh_aggregates_df = data_filter.groupby(['Time_interval', 'Space_interval', 'Vehicle_ID', 'Lane_ID', 'Lane_Change_Group']).agg(
                entry_frame=('Local_Time(sec)', "min"),
                exit_frame=('Local_Time(sec)', "max"),
                entry_position=('Local_Y', "min"),
                exit_position=('Local_Y', "max")
            ).reset_index()
        
            # Calculate travel time and distance
            veh_aggregates_df['travel_time'] = veh_aggregates_df['exit_frame'] - veh_aggregates_df['entry_frame']
            ## convert from ft to mile
            veh_aggregates_df['travel_distance'] = veh_aggregates_df['exit_position'] - veh_aggregates_df['entry_position']
        
            # veh_aggregates_df.to_csv(f"./03 analysis_result/veh_aggregates_df_{file_name}_{analysis_time_interval}_{analysis_space_interval}.csv", index=False)
        
            # Aggregate data by lane
            lane_aggregates_df = compute_lane_aggregates(veh_aggregates_df, analysis_time_interval, analysis_space_interval, last_time_interval, last_space_interval,file_name)
            # cv_metrics_df = compute_cv_metrics(lane_aggregates_df, last_time_interval, last_space_interval)
        
            # lane_aggregates_df.to_csv(f"./03 analysis_result/lane_aggregates_df_{file_name}_{analysis_time_interval}_{analysis_space_interval}.csv", index=False)
            # Print the CV metrics DataFrame
            agg_lane_aggregates_df = pd.concat([agg_lane_aggregates_df, lane_aggregates_df], ignore_index=True)
            # agg_cv_metrics_df = pd.concat([agg_cv_metrics_df, cv_metrics_df], ignore_index=True)
            
            # Plot aggregate data
            # plot_lane_aggregates(lane_aggregates_df, file_name)
        
        # Save aggregated CV metrics to CSV aggregating all files
        # agg_cv_metrics_df.to_csv(f"./03 analysis_result/NGSIM_agg_cv_metrics_{analysis_time_interval}_{analysis_space_interval}.csv", index=False)
        agg_lane_aggregates_df.to_csv(f"./03 analysis_result/NGSIM_agg_lane_aggregates_{analysis_time_interval}_{analysis_space_interval}.csv", index=False)    

        # agg_cv_metrics_df = pd.DataFrame()
        agg_lane_aggregates_df = pd.DataFrame()
# -

# ### Phenomenon by Edie domain size 

# #### __Phenomenon__

#
# __1) PeMS__
# - The CV tends to increase as the time-scale decreases, and when during the early morning
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/PeMs_1.%20CV%20pattern%20by%20aggregating%20time-scale.jpg?raw=true" align='center' width=70%>

# __2) NGSIM__

# - __(Manual check)__ I compare the 1 minute vs 5 minute q,k,u.
#     - The average of five std of 1-min flow-rates is larger than the std of 5-min flow-rates
#     - On the other hand, the average of five 1-min flow rates is equal to 5-min flow rates
#         - In fact, it's slightly different because travel time and distance between two time intervals aren't counted.
#             - The 5-minute q is about 0.11% higher than the average of five 1-minute values, which is similar to the time ratio (0.1/60 = 0.16%).
#
# <img src = "https://github.com/jooneui/fig_collection/blob/main/NGSIM%201.%201min%20vs%20%205min%20CV%20comparison.png?raw=true" align="center" width= 60%>

# - __(Plot)__ calculate the average CVs by space and time scales over 600sec (10minutes) and 1200ft
#     - every 15-min period file has empty trajectory space in the first and last few minutes.
#         - By fixing the entire time-space domain, we can see the difference of sub time-space domain size impact
#     - As above, we have observed $\frac{\sum_{i=1}^{I=4}\sum_{k=1}^{K=4} y^i_{jk}}{4*4}$ is larger than $y_j$
#     - The objective is to check how $\frac{\sum_{i=1}^{I}\sum_{k=1}^{K} y^i_{jk}}{I*K}$ is changed by the size of sub time-space domain
#         - For example, if the unit time domain is fixed as 150 sec, see the difference of $\frac{\sum_{i=1}^I\sum_{k=1}^K y^i_{jk}}{I*K}$ depending on the size of unit space domain.
#
# <img src='https://github.com/jooneui/fig_collection/blob/main/NGSIM_Edie_5_v2.jpg?raw=true' align='center' width=80%>

# - __(plot)__ CV across space
#     - The figures was not inconsistent, the misunderstanding comes from the point at 1 & 2sec.
#         - Compare 30sec, 200ft point
#     - Consistent CV value until 200ft, and slightly decline after the point.
#     - 1200 feet may not be long enough to find out the true lane-cross cv. (I-24 needs to be investigated)
#     - __CV from PeMS(30sec vs 20ft): ~0.6, / CV from NGSIM (30sec vs 20ft): 0.15 does__: still not explainable.
#
# <img src='https://github.com/jooneui/fig_collection/blob/main/NGSIM_CV_across_space_v3.jpg?raw=true' align='center' width=70%>
#

# - __(plot)__ CV across time
#     - After 2 sec, it shows decreasing pattern.
#     - Let's see what is the result of 1 or 2 sec. (0.1 sec is out of 20 0.1 sec in 2sec, so it does not too much impact to the values of q)
#
# <img src='https://github.com/jooneui/fig_collection/blob/main/NGSIM_CV_across_time.jpg?raw=true' align='center' width=70%>
#
# - But, why space and time has different starting CV point?

# #### code & result

# variable 'q' or 'k'
variable = 'q'

# +
import pandas as pd

# This function aggregates the data based on time and space intervals, then calculates mean, standard deviation, and coefficient of variation (CV) across lanes.
def pivot(lane_aggregates_df, variable, time_bundle_unit, space_bundle_unit):

    # Step 1: Adjust time and space intervals by aggregating them based on the specified terms
    lane_aggregates_df = lane_aggregates_df.assign(
        Agg_time_interval = lane_aggregates_df['Time_interval'] // time_bundle_unit,
        Agg_space_interval = lane_aggregates_df['Space_interval'] // space_bundle_unit
    )

    # Step 2: Create a pivot table where the lanes are the columns, indexed by time, space, and aggregated intervals
    df_pivot = lane_aggregates_df.pivot_table(
        index=['file_name', 'Time_interval', 'Space_interval', 'Agg_time_interval', 'Agg_space_interval'],
        columns='Lane_ID',
        values=variable
    )

    # Step 3: Calculate the mean, standard deviation, and coefficient of variation (CV) across the lanes for each row
    # The mean, std, cv are based on each disaggregate time and space interval
    df_pivot = df_pivot.assign(
        mean=df_pivot.mean(axis=1),
        lane_std=df_pivot.std(axis=1, ddof=0),
        cv=df_pivot.std(axis=1, ddof=0) / df_pivot.mean(axis=1)
    )

    # Step 4: Group by the file name, aggregated time, and space intervals, and calculate the average statistics for each group
    result = df_pivot.groupby(
        ['file_name', 'Agg_time_interval', 'Agg_space_interval']
    )[['mean', 'lane_std', 'cv']].mean().reset_index()

    # Step 5: Rename the columns for clarity
    # This is to unify the column name with the agg_aggregates_df due to 'join' function
    result = result.rename(
        columns={
            'Agg_time_interval': 'Time_interval',
            'Agg_space_interval': 'Space_interval',
            'mean': 'avg_of_disagg_mean',
            'lane_std': 'avg_of_disagg_std',
            'cv': 'avg_of_disagg_cv'
        }
    )

    return result


# +

# Load pre-aggregated lane data for analysis(CV result)
# agg_aggregates_df = pd.read_csv(f"./03 analysis_result/NGSIM_agg_lane_aggregates_{agg_time_interval}_{agg_space_interval}.csv")

# # Create a pivot table for the aggregated data
# agg_df_pivot = agg_aggregates_df.pivot_table(
#     index=['file_name', 'Time_interval', 'Space_interval'],
#     columns='Lane_ID',
#     values=variable
# )

# # Calculate the mean and standard deviation for the aggregated data
# agg_df_pivot = agg_df_pivot.assign(
#     agg_mean=agg_df_pivot.mean(axis=1),
#     agg_std=agg_df_pivot.std(axis=1, ddof=0)
# )

# Initialize an empty DataFrame to store the final results
final_df = pd.DataFrame(columns=['file_name', 'disagg_time_interval_size', 'disagg_space_interval_size', 'avg_of_disagg_mean', 'avg_of_disagg_std', 'avg_of_disagg_cv'])

# Iterate over all the different analysis intervals
for analysis_time_interval in set_analysis_time_interval:
    for analysis_space_interval in set_analysis_space_interval:
        
        # Load lane data for the current analysis interval(CV result)
        lane_aggregates_df = pd.read_csv(f"./03 analysis_result/NGSIM_agg_lane_aggregates_{analysis_time_interval}_{analysis_space_interval}.csv")
        
        # Adjust vehicle count based on the analysis time interval (scaling to per-hour rates)
        lane_aggregates_df['vehicle_count'] *= 3600 / analysis_time_interval

        # Determine the aggregation terms for time and space intervals
        time_bundle_unit = agg_time_interval // analysis_time_interval
        space_bundle_unit = agg_space_interval // analysis_space_interval

        # Apply the pivot function to convert the format and aggregate data across lanes
        avg_of_disagg_df_pivot = pivot(lane_aggregates_df, variable, time_bundle_unit, space_bundle_unit)
        
        # Merge the pivoted result with the original aggregated data
        # Time interval, space interval refers to aggregate interval.

        # Filter merged data for specific time and space intervals (if needed)
        ## filter out the value within aggregate data
        merged_df_filter = avg_of_disagg_df_pivot[(avg_of_disagg_df_pivot['Time_interval'] == 0) & (avg_of_disagg_df_pivot['Space_interval'] == 0)]
        # This is to notify the basic unit of disaggregate interval
        merged_df_filter = merged_df_filter.assign(
            disagg_time_interval_size=analysis_time_interval,
            disagg_space_interval_size=analysis_space_interval
        )

        # Select relevant columns and concatenate the result to the final DataFrame
        merged_df_filter = merged_df_filter[['file_name', 'disagg_time_interval_size', 'disagg_space_interval_size', 'avg_of_disagg_mean', 'avg_of_disagg_std', 'avg_of_disagg_cv']]
        final_df = pd.concat([final_df, merged_df_filter], ignore_index=True)
# -

final_df

final_df


def plot_final_df(final_df, fixed_variable, fixed_value, variable):
    set_file_name = final_df['file_name'].unique()
    print(final_df.head())

    if (fixed_variable == 'time'):
        fixed_column = 'disagg_time_interval_size'
        x_column = 'disagg_space_interval_size'
        x_column_name = 'space interval'
        x_label = 'space (feet)'
        title_unit = 'sec'
        
    elif (fixed_variable == 'space'):
        fixed_column = 'disagg_space_interval_size'
        x_column = 'disagg_time_interval_size'
        x_column_name = 'time interval'
        x_label = 'time (sec)'
        title_unit = 'ft'

    fig, ax = plt.subplots(1,3,figsize=(18,5))
    fig.suptitle(f"Average CVs by Fixed {fixed_value}-{title_unit}, Varying {x_column_name}s Over {agg_time_interval} sec and {agg_space_interval} ft", fontsize = 15)
    
    for i, file_name in enumerate(set_file_name):
        filter_final_df = final_df[(final_df['file_name'] == file_name) & (final_df[fixed_column] == fixed_value)]

        ax[i].scatter(filter_final_df[x_column], filter_final_df['avg_of_disagg_cv'], s=10)
        ax[i].set_title(f'{file_name[13:22]} PM File',fontsize = 13)
    
        ax[i].set_xlabel(f'{x_label}',fontsize = 10)
        ax[i].set_ylabel('CV (Avg of short-term)',fontsize = 10)
        ax[i].grid(True)
        # ax[i].set_ylim(50,250)
        # ax[i].set_yticks(np.arange(50, 250, 25))
        ax[i].set_ylim(0,0.5)
        ax[i].set_yticks(np.arange(0, 0.6, 0.1))
        # ax.set_xlim(0,2500)
        
    plot_dir = os.path.join('./02 fig/03_3 Std by Edie size')
    os.makedirs(plot_dir, exist_ok=True)
    plt.savefig(os.path.join(plot_dir, f'The std of {variable} depending on {x_column[7:13]} at {fixed_variable} is {fixed_value}.png')) 


def table_final_df(final_df, variable, indicator, threshold_p):
    set_file_name = final_df['file_name'].unique()
    
    for i, file_name in enumerate(set_file_name):
        filter_final_df = final_df[(final_df['file_name'] == file_name)]
        pivot_table = filter_final_df.pivot_table(index='disagg_space_interval_size', columns='disagg_time_interval_size', values=f'avg_of_disagg_{indicator}')
        pivot_table.to_csv(f'./pivot_table_{variable}_{indicator}_{file_name}.csv')

        # Find the value in the bottom-right corner
        bottom_right_value = pivot_table.iloc[-1, -1]
        
        # Define 5% threshold
        threshold_low = bottom_right_value * (1-threshold_p)
        threshold_high = bottom_right_value * (1+threshold_p)
        
        # Define a function to apply the style (color)
        def highlight_within_5pct(val):
            color = 'background-color: yellow' if threshold_low <= val <= threshold_high else ''
            return color
        
        # Apply the style function to the DataFrame
        styled_pivot_table = pivot_table.style.applymap(highlight_within_5pct)
        styled_pivot_table = styled_pivot_table.format("{:.2f}")
        print(file_name)
        display(styled_pivot_table)


# +
# fixed_variable = 'time'
fixed_variable = 'space'
# variable: q,k
variable = 'q'
# indicator: cv, mean, std
indicator = 'mean'
fixed_value = 200
threshold_p = 0.03

# total time-space is agg_time_interval = 600, agg_space_interval = 1200

# plot_final_df(final_df, fixed_variable, fixed_value, variable)
table_final_df(final_df, variable, indicator, threshold_p)
# 나중에 그림 그리기!!
# -

# #### The size of $\bar{q}$
#
# - When the q is less than 500 vphpl, the CV shows higher values
# - This result is due to the discrete nature of flow rates. A one-unit change in low values can cause larger variations.
#     - Slight shift of temporal & spatial range might obtain different values.
#     - ex.) 500 vphpl is about 4 veh/30sec/lane, and if the 1 unit change in the two lanes out of four (3,4,5,4) leads to CV: 0.17
# - But, it needs to further investigated if this pattern is shown in the NGSIM, where Edie's formula is applied.
# <img src='https://github.com/jooneui/fig_collection/blob/main/PeMs_1_2.%20CV%20pattern%20by%20aggregating%20time-scale_across%20flow_rates.jpg?raw=true' align='center' width=70%>

# ### Empirical Reasoning

# #### Traffic state variable (Identifying the point of stabilization)

# - The theoretical basis relies on maintaining consistent average flow rates, regardless of the size of the disaggregated time-space intervals.
# - However, if the time-space intervals are too small, the flow rate (q) becomes unstable.
#     - Travel distance at the boundaries between adjacent intervals is omitted.
#     - For example, with a 2-second time interval, 0.1 sec out of 2 sec (5%) won't be counted as VMT.
#     - Interpolation could help, but how to perform it remains a challenge.
#     - Since we compare the average value, its variation does not come from the individuality of vehicle, but comes from data omitting.
# - Therefore, we need to determine the interval size where the average flow rate stabilizes.
# - This point may be the minimum size of time-space interval
#     - It varies on the frequency of the rawdata 
# - If we allow 3% error, (30sec,100ft), (20sec, 120ft), (10sec, 200ft), (5ft, 400ft) would be minimum interval size.
#     - (2sec, 20ft) is questionable. 

# +
# variable: q,k
variable = 'k'
# indicator: cv, mean, std
indicator = 'cv'
threshold_p = 0.1

table_final_df(final_df, variable, indicator, threshold_p)
# -

# #### CV (Identifying the point of stabilization)

# - Once we identify the minimum time-space interval, we can observe how the CV changes as the interval increases.
# - The CV stabilizes over time, but not across space.
#     - We need to further investigate the CV pattern over larger space intervals.
# - The CV starts at 0.17 ~ 0.23 and eventually converges to 0.05 ~ 0.07.
#     - Declining CV is due to averaging the individual vehicle trajectories.
# - 2025 TRB is based on (300sec, 200ft) 

# +
# variable: q,k
variable = 'q'
# indicator: cv, mean, std
indicator = 'cv'
threshold_p = 0.1

table_final_df(final_df, variable, indicator, threshold_p)
# -

# ### Theoretical Reasoning

#
# __Time-space scale__
# - In PeMS, the rawdata is based on the 30sec data. In order to aggreagate to larger time-scale, it requires averaging the 30sec values.
# - In reality, the assumption (same var, mean for each row) may not be satisfactory, so the ratio is not proportional to the square root (n).
#     - but we can know that the CV using averaging values will be lower than the average of each row's CV.
#
# __Mathematical appoach__
#
# __① Loop detector (Short roadway & Long time observations)__
# - ①-1 Time-extension
# <img src='https://github.com/jooneui/fig_collection/blob/main/NGSIM_Edie_1_1_v3.jpg?raw=true' align='center' width=100%>
#
#     - $q^i_{j1,l}=\frac{\sum x_i}{A}=\frac{n^i_{j1,l} dx}{t_1 \times dx}=\frac{n^i_{j1,l}}{t_1}$
#     - $q^i_{j2,l}=\frac{\sum x_i}{A}=\frac{n^i_{j2,l} dx}{t_2 \times dx}=\frac{n^i_{j2,l}}{t_2}$
#     - Extending the time-scale to the entire-period of a day
#         - $q^i_{j,l}=\frac{\sum_{k=1}^{K} n^i_{jk,l}}{\sum_{k=1}^{K} t_k}=\frac{\sum_{k=1}^{K} t_i q^i_{jk,l}}{\sum_{k=1}^{K} t_k}=\frac{\sum_{k=1}^K q^i_{jk,l}}{K}$
#     - $Var(q^i_{j})=\frac{\sum_{l=1}^4(q^i_{j,l}-\mu^i_{q,j})^2}{4}=\frac{\sum_{l=1}^4(\frac{\sum_{k=1}^K q^i_{jk,l}}{K}-\frac{\sum_{k=1}^K \mu^i_{q,jk}}{K})^2}{4}=\frac{\sum_{l=1}^4(\sum_{k=1}^K(q^i_{jk,l}-\mu^i_{q,jk}))^2}{4K^2}=\frac{\sum_{l=1}^4((q^i_{j1,l}-\mu^i_{q,j1})^2+...+(q^i_{jK,l}-\mu^i_{q,jK})^2+2((q^i_{j1,l}-\mu^i_{q,11})(q^i_{j2,l}-\mu^i_{q,12})+...)}{4K^2}$
#         - Assumption: $q^i_{jk}$s are independent, and $Var(q^i_{jk})$s are equal to $\sigma^2$
#             - $\mu^i_{q,jk}$s do not need to be equal as it satifies $\mu^i_{q,j} = \sum \mu^i_{q,jk}$
#             - $Var(q^i_{j})=\frac{\sum_{l=1}^4((q^i_{j1,l}-\bar{q}^i_{j1})^2+...+(q^i_{jK,l}-\bar{q}^i_{jK})^2}{4K^2}=\frac{K\sigma^2}{K^2}=\frac{\sigma^2}{K}$
#
# - ①-2 Space-extension
# <img src='https://github.com/jooneui/fig_collection/blob/main/NGSIM_Edie_1_2.jpg?raw=true' align='center' width=30%>
#
#     - In $i^{th}$location, there is a loop detector. Let's consider the case when its width increases from $dx_1$ to $dx_1+dx_1$.
#         - $q^i_{jk,l}=\frac{n^i_{jk,l}\times dx_1}{T \times dx_1}=\frac{n^i_{jk,l}}{T}$
#         - $q^i_{jk,l}=\frac{n^i_{jk,l}\times (dx_1+dx_1)}{T \times (dx_1+dx_1)}=\frac{n^i_{jk,l}}{T}$
#     - The $q$ is not a function of the size of the width as long as the number of passing vehicles passing in a given time ($n^i_{jk,l}$) is maintained.
#         - ex) 1500 vphpl * 50mph * 1.414 = 176 feet
#         - Under the 176 feet, the variance should not change.
#     - Likewisee, the lane-to-lane variation at $j^{th}$ location are consistent as long as the number of passing vehicles is maintained.
#         - $Var(q^i_{jk})=(\sigma^i_{jk})^2=\frac{\sum_{l=1}^4(q^i_{jk,l}-\mu^i_{q,jk})^2}{4}=\frac{\sum_{l=1}^4 (n^i_{jk,l}/T-\mu^i_{q,jk})^2}{4}$
#         
#
#
#
#

# __② Camera (Long roadway & Short time observations)__
# - ②-1 Space-extension
# <img src='https://github.com/jooneui/fig_collection/blob/main/NGSIM_Edie_2_1_v3.jpg?raw=true' align='center' width=100%>
#
#     - $q^i_{1k,l}=\frac{\sum_{r=1}^{n^i_{1k,l}} dx_r}{x_1\times dt}=\frac{\sum_{r=1}^{n^i_{1k,l}} u_r}{x_1}$
#     - $q^i_{2k,l}=\frac{\sum_{r=1}^{n^i_{2k,l}} dx_r}{x_2\times dt}=\frac{\sum_{r=1}^{n^i_{2k,l}} u_r}{x_2}$
#     - Extending the space scale to $A (\text{ covering } x_1, x_2, x_3,... \text{ and } x_J$ ($X=x_1+x_2+x_3+...+X_J$).
#         - $q^i_{Ak,l}=\frac{\sum_{i=1}^{I}\sum_{r=1}^{n^i_{jk,l}} dx_r}{X \times dt}=\frac{\sum_{i=1}^I\sum_{r=1}^{n^i_{jk,l}} u_r}{X}=\frac{\sum_{i=1}^I x_iq^i_{jk,l}}{\sum_{i=1}^Ix_i}=\frac{\sum_{i=1}^I q^i_{jk,l}}{I}$
#     - $Var(q^A_{jk})=\frac{\sum_{l=1}^4(q^i_{Ak,l}-\mu^i_{q,Ak})^2}{4}=\frac{\sum_{l=1}^4(\frac{\sum_{i=1}^I q^i_{jk,l}}{I}-\frac{\sum_{i=1}^I \mu^i_{q,jk}}{I})^2}{4}=\frac{\sum_{l=1}^4(\sum_{i=1}^I (q^i_{jk,l}-\mu^i_{q,jk})^2)}{4I^2}=\frac{\sum_{l=1}^4((q^1_{jk,l}-\mu^1_{q,jk})^2+...+(q^I_{jk,l}-\mu^I_{q,jk})^2+2((q^1_{jk,l}-\mu^1_{q,jk})(q^2_{jk,l}-\mu^2_{q,jk})+...)}{4I^2}$
#         - Assumption: $q^i_{jk}$s are independent, and $Var(q^i_{jk})$s are equal to $\sigma^2$
#             - $\mu^i_{q,jk}$s do not need to be equal as it satifies $\mu^A_{q,jk} = \sum_{i=1}^{I} \mu^A_{q,jk}$
#             - $Var(q^A_{jk})=\frac{\sum_{l=1}^4((q^1_{jk,l}-\mu^1_{q,jk})^2+...+(q^I_{jk,l}-\mu^I_{q,jk})^2+2((q^1_{jk,l}-\mu^1_{q,jk})(q^2_{jk,l}-\mu^2_{q,jk})+...)}{4I^2}=\frac{I\sigma^2}{I^2}=\frac{\sigma^2}{I}$
#
#
# - ②-2 Time-extension
# <img src='https://github.com/jooneui/fig_collection/blob/main/NGSIM_Edie_2_2.jpg?raw=true' align='center' width=30%>
#
#     - In $k^{th}$ time interval, there is snapshot. Let's consider the case when its time interval increases from $dt_1$ to $dt_1+dt_1$.
#         - $q^i_{jk,l}=\frac{\sum_{r=1}^{n^i_{jk,l}} u_r \times dt_1}{X \times dt_1}=\frac{\sum_{r=1}^{n^i_{jk,l}} u_r}{X}$
#         - $q^i_{jk,l}=\frac{\sum_{r=1}^{n^i_{jk,l}} u_r \times (dt_1+dt_1)}{X \times (dt_1+dt_1)}=\frac{\sum_{r=1}^{n^i_{jk,l}} u_r}{X}$
#     - The $q$ does not relate with the size of time interval as long as the number of passing vehicles passing in a given segment ($n^i_{jk,l}$) is maintained.
#         - ex) 3600sec / 1500 vphpl = 2.4 sec
#     - Likewisee, the lane-to-lane variation at $k^{th}$ time interval is consistent as long as the number of passing vehicles is maintained.
#         - $Var(q^i_{jk})=\frac{\sum_{l=1}^4(q^i_{jk,l}-\mu^i_{q,jk})^2}{4}=\frac{\sum_{l=1}^4 ((\sum_{r=1}^{n^i_{jk,l}} u_r)/X-\mu^i_{q,jk})^2}{4}$
#
# __③ Long roadway & Long time observations__
#
# <img src='https://github.com/jooneui/fig_collection/blob/main/NGSIM_Edie_3.jpg?raw=true' align='center' width=30%>
#
# - $q^i_{j,l}=\frac{\sum_{k=1}^{K} t_i q^i_{jk,l}}{\sum_{k=1}^{K} t_i}$ & $q^i_{j,l}=\frac{\sum_{i=1}^I x_iq^i_{jk,l}}{\sum_{i=1}^Ix_i}$
# - $q^i_{j,l}=\frac{\sum_{k=1}^{K} t_i q^i_{jk,l}}{\sum_{k=1}^{K} t_i}=\frac{\sum_{k=1}^K t_k \frac{\sum_{i=1}{I} x_iq^i_{jk,l}}{\sum_{i=1}^I x_i}}{\sum_{k=1}{K} t_k}=\frac{\sum_{k=1}^K\sum_{i=1}^{I} t_kx_iq^i{jk,l}}{\sum_{k=1}^Kt_k \times \sum_{i=1}^I x_i}=\frac{\sum_{k=1}^K\sum_{i=1}^I q^i_{jk,l}}{K \times I}$
#
# __Conclusion__
#
# <img src='https://github.com/jooneui/fig_collection/blob/main/NGSIM_Edie_4_v1.jpg?raw=true' align='center' width=30%>
#
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/PeMs_2.%20CV%20difference%20explanation.png?raw=true" align='center' width=10%>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["past"]
#
# <div class="alert alert-danger">
#
# - 2014 and 2015 look unrealistic, but no reference point to check its degree of inaccuracy
# - NGSIM data
#     - cv of I-80(6 lanes) during 15min: 0.08
#         - q(vph): 5280/average time headway(vps)
# |Variable|Lane 1|Lane 2|Lane 3|Lane 4|Lane 5|Lane 6|
# |:------:|:---------------:|:---------------:|:---------------:|:---------------:|:---------------:|:---------------:|
# |avg speed(mph)|40.8|17.1|16.2|13.8|15.6|19.5|
# |density(vpm)|34.5|81.0|69.7|88.0|75.9|66.3|
# |flow(vph)|1408|1381|1130|1218|1187|1293|98 
#
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["past"]
# <div class="alert alert-danger">
#
# __Variable definition__
#
# - $q^i_{jk-n,l}$: The flow rates for the ith day at the jth location, aggregated over the kth timeframe for analysis and the nth timeframe, for lane l
#     - ex) $q^i_{j1-1,1} = \frac{1}{\bar{h}^i_{j1-1,1}}=\frac{n^i_{j1-1,1}}{\sum_{m=1}^{n^i_{j1-1,1}}h^i_{j1-1,1m}}$
# - $h^i_{jk-n,lm}$: The time headway of mth vehicle at the lane l with its preceding vehicle, for the ith day at the jth location, aggregated over the kth timeframe for analysis and the nth timeframe
# - $n^i_{jk-m,l}$: The time headway of the mth vehicle in lane l from the vehicle in front of it, for the ith day at the jth location, aggregated over the kth analysis timeframe and the nth timeframe.
# - $\bar{q}^i_{jk,l}$ = The average flow rates for the ith day at the jth location, aggregated over the kth timeframe for analysis, for lane l
# - $\bar{q}^i_{jk}$ = The average flow rates for the ith day at the jth location, aggregated over the kth timeframe for analysis of all lanes
#
# </div>
# -

# __3. Conclusion__
# - The time-space domain needs to be set when determining CV threshold.
# - The q size matters in the 30sec intervals in PeMs (where small size of q exists), but daily basis won't be.

# - 

# + [markdown] tags=["slides", "main"]
# ### Hypothesis testing

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["slides"]
# - The p-value depending on the different $\mu_0$
#     - sample std: 0.033
#     - our manual threshold(0.2) is shown to be rejected
# | $\mu_0$ | 0.103 | 0.106 | 0.2 |
# |----------|----------|----------|----------|
# | p-value | 0.05   | 0.01   | 0.00   |
#

# + [markdown] jp-MarkdownHeadingCollapsed=true
# <div class="alert alert-success">
#
# In order to conduct the hypothesis test, it is essential to determine the population parameters in advance. We established threshold values of 0.18 for lane-to-lane flow variation, 0.20 for density, and 0.30 for speed. These thresholds were derived from an empirical comparison of lane-to-lane variations between normal and malfunctioning detector datasets. The empirical data consistently demonstrated a clear separation at these values, providing strong statistical evidence for their effectiveness.
#
# Using sample ground truth data from the NGSIM dataset, we conducted hypothesis tests employing the t-statistic ($t = \frac{\bar{y} - \mu}{s/\sqrt{n}} \sim t_{(n-1)}$), where $\bar{y}$ is the sample mean of lane-to-lane variations, $s$ is the sample standard deviation, and $n$ is the sample size. The results of the t-tests consistently rejected the null hypothesis across all tested parameters. Consequently, we concluded that the population means for these parameters are significantly less than the established threshold values, affirming them as upper thresholds.
#
# The p-values obtained were exceptionally low, indicating a minimal likelihood of Type I errors (false positives). This high level of statistical significance ensures that only truly malfunctioning detectors are flagged by minimizing the likelihood of incorrectly identifying well-functioning detectors as malfunctioning.
#
#     
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["past"]
# <div class="alert alert-danger">
# 24/06/13
#     
#     
# |Methodology|Mckay(1932)|Vangel(1996)|
# |:------:|:---------------:|:---------------:|
# |95% Upper threshold|0.105|0.105|
# |99% Upper threshold|0.124|0.123|
#     
# </div>

# +
# from scipy.stats import shapiro


import pandas as pd
import numpy as np
from scipy.stats import shapiro

# Load data
files = {
    "NGSIM": './03 analysis_result/NGSIM_agg_cv_metrics_300_200.csv',
    "I24_flow": './03 analysis_result/flow_disagg_df_pivot_221121_E_14400_10560_[1800]_[1320].csv',
    "I24_density": './03 analysis_result/density_disagg_df_pivot_221121_E_14400_10560_[1800]_[1320].csv'
}

NGSIM_CV = pd.read_csv(files["NGSIM"])
I24_flow_CV = pd.read_csv(files["I24_flow"])
I24_density_CV = pd.read_csv(files["I24_density"])


## I24 excluding between ramp-out and ramp-in
I24_flow_CV = I24_flow_CV.loc[~I24_flow_CV['Space_interval'].isin([0, 1])]
I24_density_CV = I24_density_CV.loc[~I24_density_CV['Space_interval'].isin([0, 1])]

# Extract CVs
flow_CV = pd.concat([NGSIM_CV['flow_CV'], I24_flow_CV['cv']], ignore_index=True)
density_CV = pd.concat([NGSIM_CV['density_CV'], I24_density_CV['cv']], ignore_index=True)

print("flow_CV mean:", flow_CV.mean(),flow_CV.std())
print("flow_density mean:", density_CV.mean(),density_CV.std())


a = np.corrcoef(flow_CV, density_CV)

# + tags=["code"]
"""Normality test: Shapiro–Wilk test
"""

# print(agg_cv_metrics)

stat, p = shapiro(flow_CV)
print(f'Statistic: {stat}, p-value: {p}')

# +
import matplotlib.pyplot as plt
import seaborn as sns

# Set a more modern style
sns.set_theme(style="whitegrid")

# Create the figure and axes
fig, ax = plt.subplots(1, 2, figsize=(10, 3), constrained_layout=True)

# Set the overall title
fig.suptitle('Histogram of CVs from NGSIM', fontsize=16, fontweight='bold')

# Define the conditions
conditions = [(0, flow_CV, 'Flow Rates'), (1, density_CV, 'Densities')]

# Plot each histogram
for i, variable, var_name in conditions:
    sns.histplot(variable, bins=20, kde=False, color='skyblue', edgecolor='black', ax=ax[i])
    ax[i].set_title(f'{var_name}', fontsize=14, fontweight='semibold')
    ax[i].set_xlim(0, 0.3)
    ax[i].set_ylim(0, 10)
    ax[i].set_xlabel('Coefficient of Variation (CV)', fontsize=12)
    ax[i].set_ylabel('Frequency', fontsize=12)

# Display the plot
plt.close()


# +
import matplotlib.pyplot as plt
import seaborn as sns

# Extract just the Series (not DataFrame)
NGSIM_flow_CV = NGSIM_CV['flow_CV'].dropna()
NGSIM_density_CV = NGSIM_CV['density_CV'].dropna()

# Define the conditions
conditions = [
    (0, NGSIM_flow_CV, I24_flow_CV['cv'], 'Flow Rates'),
    (1, NGSIM_density_CV, I24_density_CV['cv'], 'Densities')
]

# Set style
sns.set_theme(style="whitegrid")

# Create the figure
fig, ax = plt.subplots(1, 2, figsize=(10, 3), constrained_layout=True)
fig.suptitle('Density Plot of CVs from NGSIM & Motion', fontsize=20, fontweight='bold')

# Plot density curves
for i, NGSIM, I24, var_name in conditions:
    # sns.kdeplot(NGSIM, bw_adjust=1, color='skyblue', linewidth=2, ax=ax[i], label='NGSIM')
    # sns.kdeplot(I24, bw_adjust=1, color='green', linewidth=2, ax=ax[i], label='I-24')
    sns.histplot(NGSIM, ax=ax[i], kde=True, stat="density", label='NGSIM(I-80)', color='skyblue', linewidth=2)
    sns.histplot(I24, ax=ax[i], kde=True, stat="density", label='Motion(I-24)', color='green', linewidth=2)

    ax[i].set_title(var_name, fontsize=14, fontweight='semibold')
    ax[i].set_xlim(0, 0.5)
    ax[i].set_ylim(0, None)  # auto-scale
    ax[i].set_xlabel('Coefficient of Variation (CV)', fontsize=12)
    ax[i].set_ylabel('Density', fontsize=12)
    ax[i].legend()

# Show plot
plt.show()
plt.close()

# + tags=["code"]
"""
The CV threshold
"""

from scipy import stats
from statsmodels.stats.power import TTestPower 

# variable(flow, density)
variable = 'flow'

if variable == 'density':
    var_CV = flow_CV
elif variable == 'flow':
    var_CV = density_CV

# Hypothesized population mean
alpha = 0.01

# Calculate degrees of freedom
n = len(var_CV)
df = n - 1

# Sample statistics
sample_mean = np.mean(var_CV)
sample_std = np.std(var_CV, ddof=1)

print(f"sample_std: {sample_std}")

SE = sample_std / np.sqrt(n)

mu_0 = 0.20
mu_1 = 0.09

delta = (mu_1 - mu_0) /  SE

# Calculate the critical value for the left-tailed test
critical_value = stats.t.ppf(alpha, df)

# Calculate the actual value of the sample mean that corresponds to the critical value
actual_value = critical_value * SE + mu_0

# Perform the one-sample t-test
t_statistic, p_value = stats.ttest_1samp(var_CV, mu_0)
print("t-statistic",t_statistic)

# Adjust p-value for one-sided test (left-tailed)
p_value /= 2
if t_statistic < 0:
    p_value = p_value
else:
    p_value = 1 - p_value

# Print the results
print(f"Degrees of freedom: {df}")
print(f"p value: {p_value}")
# Conclusion
if t_statistic < critical_value:
    print("Reject the null hypothesis: The sample mean is significantly less than the population mean.")
else:
    print("Fail to reject the null hypothesis: There is no significant evidence that the sample mean is less than the population mean.")

# Calculate the power of the test    

power = stats.nct.cdf(critical_value, df, delta)
# Type II error (beta)
beta = 1 - power

print(f"Power of the test: {power}")
print(f"Type II error probability (beta): {beta}")

# + jupyter={"source_hidden": true} tags=["code"]
import numpy as np
from scipy import stats

# Degrees of freedom
df = 10

# First set of values
t_statistic_1 = 2.5
delta_1 = 1.0
power_1 = stats.nct.cdf(t_statistic_1, df, delta_1)

# Second set of values
t_statistic_2 = 3.0
delta_2 = 1.5
power_2 = stats.nct.cdf(t_statistic_2, df, delta_2)

print(f"Power with first set: {power_1:.5f}")
print(f"Power with second set: {power_2:.5f}")

# + tags=["code"]
"""Type II error"""

import scipy.stats as stats

# Given data
# Hypothesized population mean
k_1 = 0.17

# Calculate degrees of freedom
n = len(flow_CV)
df = n - 1

# Sample statistics
sample_mean = np.mean(flow_CV)
sample_std = np.std(flow_CV, ddof=1)

SE = sample_std / np.sqrt(n)
print(sample_std)

# Calculate the critical value for the left-tailed test
critical_value = stats.t.ppf(alpha, df)
print(critical_value)

# Find the critical t-value for a right-tailed test
# t_critical = stats.t.ppf(1 - alpha, df)
print(t_critical)

# Calculate the power of the test
power = stats.nct.sf(critical_value, df, delta)

# Type II error (beta)
beta = 1 - power

print(f"Power of the test: {power}")
print(f"Type II error probability (beta): {beta}")


# + tags=["code"]
""" Hypothesis test for CV.(Outdated version) 
        H0: The CV is less than the critical value(For the test, H0: The CV is equal to the critical value) 
        H1: The CV is greater than the critical value
    The test is based on McKay A. (1932). 
    Each sample coefficient of variation (CV) has a one-sided critical interval (CI), and we can determine the CIs for all sample CVs. 
    The 95% CI indicates that, if we were to take 100 samples, the population CV would fall within this interval 95 times out of 100. 
    Therefore, to find the critical value with a 5% type I error, we need to identify the 95th percentile value from all the upper thresholds of each CI
 """

from scipy.stats import chi2

# Step1) Input variables

# n: # of samples = # of lanes
agg_lane_aggregates_df = pd.read_csv('./agg_lane_aggregates.csv')
n = len(agg_lane_aggregates_df['Lane_ID'].unique())

# Chi-square values
# Degrees of freedom (df)
df = n-1  # Replace with the actual degrees of freedom for your test
# Significance level (alpha)
alpha = 0.05
# Calculate the critical value
critical_value = chi2.ppf(alpha, df)

# sample CV
agg_cv_metrics_df = pd.read_csv('./agg_cv_metrics.csv')
CV_s =  agg_cv_metrics_df['flow_CV']

# Step2) Calculate critical value for each sample
Mckay_denominator = ((critical_value/n)-1)*CV_s**2+critical_value/(n-1)
Vangel_denominator = ((critical_value+2/n)-1)*CV_s**2+critical_value/(n-1)

ucl_Mckay = CV_s / np.sqrt(Mckay_denominator)
ucl_Vangel = CV_s / np.sqrt(Vangel_denominator)

# Step3) Calculate the population critical value by calculating 95 percentile value
p5_Mckay = np.percentile(ucl_Mckay, alpha*100)
p5_Vangel = np.percentile(ucl_Vangel, alpha*100)

print(np.mean(ucl_Mckay))
print(np.mean(ucl_Vangel))

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["past"]
# <div class="alert alert-danger">
#     
# 1. Procedure
# - Step1) Check NGSIM CV closeness
#     - Normality test
#         - If satisfy normality, calculated 95% or 68% C.I. 
#     - Grubb's Test
#         - Grubbs' test is a statistical test used to identify outliers in a univariate dataset
#         - Steps for Grubbs' Test
#             - Step1-1) Calculate the Test Statistic:
#                 - Compute the sample mean ($\bar{X}$) and sample deviation(s).
#                 - Calculate the test statistic G: $G=\frac{max|X_i-\bar{X}|}{s}$
#             - Step1-2) Determine the Critical Value:
#                 - $G_{crit}=\frac{(n-1)}{\sqrt{n}}\cdot \sqrt{\frac{t^2}{n-2+t^2}}$ 
#                     - $t$: critical value of t-distribution with n-2 degree of freedom
#             - Step1-3) Compare the Test Statistic to the Critical Value:
#                 - If the test statistic G exceeds the critical value, the corresponding data point is considered an outlier.
#     - __※ A confidence interval (C.I.) indicates the range within which we fail to reject $H_O$; however, this does not imply that we accept $H_O$__
# - Step2) choose $CV_{population}$ as the average of NGSIM CV
#     - Not sure the average will be appropriate
# - Step3) hypothesis test to detect malfunctioning detectors(A. T. McKay, 1932)
#     - $H_0: CV_{sample} = CV_{population}(CV_{sample} < CV_{population})$
#     - $H_1: CV_{sample} > CV_{population}$
#     - When identifying a malfunctioning detector, it's better to be strictly certain about one detector's failure than to filter out many potential malfunctioning detectors.
#     - ※ $H_1$ statement needs to be what we want to claim
#         - $\alpha$ and $\beta$ are inverse-proportional, but we priortize $\alpha$ as small enough(less than 5%) when doing a hypothesis test
#         - small $\alpha$ means that small probaility $H_0$ is true but rejected, so if the $H_0$ is rejected, chances are high that it actually rejected, meaning $H_1$ is accepted. 
#         - but, vice versa is not working because of high $\beta$.
#     - $H_0$ needs to have specific point, but $H_1$ does not necessarily need to.
#         - Because significance level is only determined by $\alpha$, so at least $H_0$ needs to have a specific distribution.
#
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["past"]
# <div class="alert alert-danger" role="alert">
#
# __Ratio of speeds exceeding the upper limit__
# - The coefficient of variation (CV) is unable to identify instances where speeds are consistent across lanes but reach unrealistic values.
# - 90mph for the threshold value 
# <center> <img src="https://github.com/jooneui/fig_collection/blob/main/speed_ratio_hist.png?raw=true", width = 80%><br>
#
# - upper bound of the ratio: 1%(from 3 outliered data out of 288 data)
# <center> <img src="https://github.com/jooneui/fig_collection/blob/main/150918.xlsx_%5B1,%202,%203,%204%5D.png?raw=true", width = 80%><br>
# <!-- <center> <img src="https://github.com/jooneui/fig_collection/blob/main/110216.xlsx_%5B1,%202,%203,%204%5D.png?raw=true", width = 100%><br> -->
#
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["past"]
# <div class="alert alert-danger" role="alert">
#     
# __Clustering__
#     
# </div>

# + [markdown] tags=["main", "slides"]
# # Case Study

# + [markdown] tags=["main", "slides"]
# ## PeMs

# + [markdown] jp-MarkdownHeadingCollapsed=true
# 1. why speed calculation requires extra steps?
# - When measurements include zero or NA values of speeds or densities, the average speeds cannot be calculated.
#
# 2. q,k,u calculation
# - $q$
#     - $q^i_{jk,l}=\frac{n^i_{jk,l}\times L}{e\times L}$
#     - $q^i_{j,l}=\frac{n^i_{j,l}\times L}{E\times L}=\frac{\sum_{k=1}^{n_e} n^i_{jk,l}\times L}{n_e\times e \times L}=\frac{1}{n_e} \sum_{k=1}^{n_e}\frac{n^i_{jk,l}\times L}{e\times L}=\frac{1}{n_e}\sum_{k=1}^{n_e}q^i_{jk,l}$
# - $k$
#     - $k^i_{jk,l}=\frac{\sum_{p=1}^{n_k}\frac{L+d}{v^i_{jk_p,l}}}{e \times L}$
#     - $k^i_{j,l}= \frac{\sum_{k=1}^{n_e}\sum_{p=1}^{n_k}\frac{L+d}{v^i_{jk_p,l}}}{n_e \times e \times L}=\frac{1}{n_e} \frac{\sum_{k=1}^{n_e}\sum_{p=1}^{n_k}\frac{L+d}{v^i_{jk_p,l}}}{e \times L}=\frac{1}{n_e}\sum_{k=1}^{n_e}k^i_{jk,l}$
# - $u$
#     - $u^i_{j,l}=\frac{VMT}{VHT}=\frac{\sum_{k=1}^{n_e} n^i_{jk,l} \times L}{\sum_{k=1}^{n_e}\sum_{p=1}^{n_k}\frac{L+d}{v^i_{jk_p,l}}}=\frac{\sum_{k=1}^{n_e} n^i_{jk,l} \times L}{\sum_{k=1}^{n_e}\sum_{p=1}^{n_k}\frac{n^i_{jk,l}}{n^i_{jk,l}}\frac{L+d}{v^i_{jk_p,l}}}=\frac{\sum_{k=1}^{n_e} n^i_{jk,l} \times L}{\sum_{k=1}^{n_e} (L+d)n^i_{jk,l}\sum_{p=1}^{n_k}\frac{1}{n^i_{jk,l}}\frac{1}{v^i_{jk_p,l}}}=\frac{\sum_{k=1}^{n_e} n^i_{jk,l} \times L}{(L+d) \sum_{k=1}^{n_e} \frac{n^i_{jk,l}}{v^i_{jk,l}}}= \frac{(L+d)\sum_{k=1}^{n_e} q^i_{jk,l}}{(L+d) \sum_{k=1}^{n_e} \frac{q^i_{jk,l}}{v^i_{jk,l}}}= \frac{(L+d)\sum_{k=1}^{n_e} q^i_{jk,l}}{(L+d) \sum_{k=1}^{n_e} \frac{q^i_{jk,l}}{v^i_{jk,l}}}=\frac{\sum_{k=1}^{n_e} q^i_{jk,l}}{ \sum_{k=1}^{n_e} \frac{q^i_{jk,l}}{v^i_{jk,l}}}$ 
#
# - extending this formula to the lane-to-lane average does not change the formula, because it only affects to the range of summation.
#
# 3. Issue for calculating the average speed
# - To calculate $u^i_{j,l}$, we need $v^i_{jk,l}$ as the denominator. The value of $v^i_{jk,l}$ is determined by $\frac{q^i_{jk,l}}{k^i_{jk,l}}$. However, if $q^i_{jk,l}$ or $k^i_{jk,l}$ is zero, $v^i_{jk,l}$ becomes 0 or NA, making it impossible to calculate $u^i_{j,l}$.
# - ignoring these part when calculating $u^i_{j,l}$ can be one way because zero flow or density literally means nothing occurs in the traffic situation. 
#     - However, if the zero values come from the malfunctioning, ignoring them at the average would bias the average speeds by only using the values from healthy detectors. In fact, more than 40% of data in the lane 1 are recorded as zero in 2015, and ignoring them lead to no difference with other healthy years such as 2011 and 2024.
#     - Add the figure of the average speeds over all years.
# - In order to properly take these values into the process of average speed calculation, I devised the process as follows
#     - The first step is to aggregate the rawdata into 5-minute interval, because we never know if the single zero value data indicates malfunctioning or not. The 00() addressed that having less than 24 vphpl in 5-minute interval data indicated the data from malfunctioning one. So, if the q is less than 24, and the k is less than 1, I calculated regarded the interval as malfunctioning one with assigning the speed as extreme value as 1mph and the flow as the mean of the rest of lanes at the same time interval. In order to calculate the 5-minute average speed, we assume the flow as zero when the measured speed is zero or NA. 
#
#     

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["slides"]
# <div class="alert alert-success">
#
# Over a number of years, the State of California has invested in developing Transportation Management Centers (TMCs) in urban areas to help manage traffic. The TMCs receive traffic measurements from the field, such as average speed and volume. These data, which are updated every 30 seconds, help the operations staff react to traffic conditions, to minimize congestion and to improve safety. More recently, the California Department of Transportation (Caltrans) recognized that the data collected by the TMCs is valuable beyond real-time operations needs, and a concept of a central data repository and analysis system evolved. Such a system would provide the data to transportation stakeholders at all jurisdictional levels. It was decided to pursue this concept at a research level before investing significant resources. Thus, a collaboration between Caltrans and PATH (Partners for Advanced Transit and Highways) at the University of California at Berkeley was initiated to develop a performance measurement system or PeMS. PeMS currently functions as a statewide repository for traffic data gathered by thousands of automatic sensors. It has integrated existing Caltrans data collection, processing, and communications infrastructure with data storage and analytical tools. Through the Internet (http://pems.eecs.berkeley.edu), PeMS provides immediate access to the data to a wide variety of users. (Measuring Traffic, Peter J. Bickel, Chao Chen, Jaimyoung Kwon, John Rice, Erik van Zwet and Pravin Varaiya, 2007)
#
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true
# <div class="alert alert-danger">
#
# __240722: The logic to calculate speed__
#     
# However, the calculation of the daily average speed, which uses the sum of flow (q) over speed (u) as the denominator, becomes problematic when u has zero or NA values. This occurs when either density or flow is zero, preventing the calculation of the daily average speed. Neglecting these values might be a reasonable approach when the loop detectors function correctly, as it indicates no vehicles passing through the detector during those intervals. However, if the detector is malfunctioning, omitting these values will fail to capture how the malfunctioning affects the average speed. For instance, in the 2015 data analysis, 41\% of intervals in lane 1 exhibited zero flow or occupancy, thus omitting these values does not represent the extent to which the malfunctioning distort the estimate.
#
# Version1: 
#
# Therefore, in our research, we implemented a method to accurately reflect the impact of malfunctioning detectors on the daily average speed, allowing it to serve as an indicator for distinguishing between malfunctioning and healthy detectors. The first step is to aggregate the raw data into 5-minute intervals, as a single zero value does not necessarily indicate malfunctioning. According to 00(), a traffic flow rate of less than 24 vehicles per hour per lane (vphpl) in a 5-minute interval indicates malfunctioning data. Hence, if the flow (q) is less than 24 and the density (k) is less than 1 in 5-minute aggregate data, we consider the interval as malfunctioning. For these intervals, we assign an extreme value of 1 mph for speed and use the average flow of the other lanes at the same time interval. To calculate the 5-minute average speed, we assumed the flow to be zero when the measured speed was zero or NA.
#     
# Similarly, even though most flow and density values in the 2014 data are not zero, the average speeds show little variation. This is because the flow at each time interval, which acts as a weight for the speed, has minimal impact on the daily average speed due to its low values.
#
#     
# </div>

# + [markdown] tags=["slides"]
# ### Measure Distribution
# - Manually checking the datasets leads to conclusion of 2011 and 2024 as normal and consistent, but 2014 and 2015 as abnormal
#     - cv: 2011=2024<<2014<<2015
#     - 2011,2024: 0.1~0.18
#     - 2014: 0.21~0.24
#     - 2015: 0.31~0.53
# - Threshold: 0.20
# <center> <img src="https://github.com/jooneui/fig_collection/blob/main/hist_cv_year.png?raw=true", width = 70%><br>
#

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["notes"] endofcell="--"
# <div class="alert alert-info">
#
# <p style="font-size: 30px"> Memo(Sources for Introduction) </p>
#
# 0. __327 datasets in total__
# - __104 datasets__ in 2011(Jun. ~ Apr.)
# - __16 datasets__ in 2014(Aug., Sep.)
# - __176 datasets__ in 2015 data (Jun. ~ Nov., 176 datasets)
# - __31 datasets__ in 2024(Jun.)
#    
# 1. __PeMs User Guide__
#     - Speed
#         - the speed is either measured directly: possible with radar detectors
#         - calculated: using a g-factor accompanying the flow and occupancy as with single-loop detector
#         - Our location is double-loop and mentioned as "speeds are estimated" 
#         - For the aggregate speed that spans all of the loops, the speed is the flow-weighted mean across the lanes.
#     - g-factor
#         - The g-factor is a conversion factor used to convert the measured quantities of flow and occupancy into speed for detectors that do not measure speed directly. The g-factor is a combination of two quantities: __1)__ the average length of the vehicles traveling over the detector and __2)__ the tuning of the detector. Each detector in the system has its own tuning characteristics. PeMS calculates a g-factor for every single detector over __every 5-minute period__ for an entire week. By doing this, PeMS captures the weekly characteristics of the traffic mix as well as the individual characteristics of each detector.
#         - However, a specific lane or lanes have not been designated on a divided highway having four or more clearly marked lanes for traffic in one direction, ... those vehicles may also be driven in the lane to the immediate left of that right-hand lane [link](https://dot.ca.gov/programs/traffic-operations/legal-truck-access/truck-lane-use#:~:text=those%20vehicles%20shall%20be%20driven,the%20right%20edge%20or%20curb.)
#      
# 2. __Capacity drop__
# - Capacity drop refers to when the q-k curve does not follow the F.D., but rather shows a horizontally dispersed at the certain level of point
# - The commonly well-known case is at the intersection
#     - At the intersection, when the light turns green and cars start moving, even if there's nothing blocking their way, the flow of traffic doesn't reach full capacity because there aren't enough cars to fill up the road.
#     - In this stationary case, data from loop detectors, which monitor both the traffic coming towards the intersection and the traffic leaving it, show that the average density spreads out within the density of upstream and downstream traffic.
#     - This leads to a trapezoid shape on the traffic flow diagram. Instead of reaching a peak, the points on the diagram spread out horizontally at a certain level.
#     - Likewise, the bottleneck shows this pattern as vehicles got stuck at the merging point.
# - If the road is really long, you'd expect the traffic jam to be super dense, but that's not necessarily the case because of physical limits.
#
# 3. __Qiinlong's paper__
# - Theme: Automatic identification of near-stationary traffic states
#     - The major contributwasnto develop method toelop automatically select the candidates for stationary time series.
#     - And then apply Cassidy(1998) method to finally determine near-stationary state__s
# - why SR-9__1 E? can detect stationary equilibrium state(70ft above from the merging point)
#
# 4. __SR-91, EB, (VDS 1203506)__
# - about 70ft upstream from the merge point(Valley-view, bottleneck)
# - EB: But this road is not that much related with commute trip, so it showed one-peak point.
#
# 5. __BPR function__
# - BRP function can only be defined on a congested part(also can verify in the Vickery)
#     - BPR function is the relationship of the supply and demand equilibrium state, and the equilibrium happens only at the congested state
#     - so, based on the defined BPR at the congested period, we can derive fundamental diagram at the congested period.
# - The next step after defining BPR is to define F.D.
#     - By individually defining the F.D. for each side, we can determine the length of flat line in the middle.
# - Only applicable for the two-peak cases
# - If the proportion of volumes is constant, it can be expanded to the whole day.
#
# 6. __Peak-period finding__
# - how to define the peak period
#
# 7. __g-factor__
# - 2011: 24 ~ 26ft for lane 3, 19~22ft for the rest of lanes
# - 2014: varies a lot
# - Reference
#     - compact: 10~14ft
#     - midsize: 14~16ft
#     - large-SUV: 16.7ft
#     - fullsize: 16~18ft
#     - Large pickup: 18.4ft
#
# 8. __how g-factor is calculated__
# - single-loop detector
#     - The PeMS algorithm(Zhanfeng, Coifman, et al.(2001))
#         - Determine the g-factor in an uncongested traffic state using the measured q and occupancy, assuming free-flow speed.
#             - $g_{instant}(t)=\frac{o(t)}{q(t)}\times u_{free}$ ($o(t)$: occupancy, $q(t)$: flow rates(vph), $u_{free}$ : 65mph) 
#         - Then, adjust the g-factor for congested periods using historical data. (historical g-factor data are given)
#             - $g(t) = g_{instant}(t) + [g_{hist}(t+\tau)-g_{hist}(t)]$ ($g_{hist}(t): \text{historical g-factor at time t}, \tau: \text{delay time(hr)}$)
# - dual-loop detector
#     - calculated by u,q,occ:
#         - $g(t)=\frac{o(t)}{q(t)}\times \bar{u}(t)$ (o(t): occupancy, q(t): flow rates(vph), u:velocity(mph))
#  
# 9. NGSIM data
# - I-80 in the San Francisco 
# Bay area in Emeryville, CA
# -  April 13, 2005
# -  The study are:a approximately 500 meters (1,640 feet) i 
# length and consisted of six freeway lanes, including  (HV) la
# - a. Seven synchronized digital video came
# - 
# A total of 45 minute: periods:
# 4:00 p.m. to 4:15 p.m.; 5:00 p.m. to 5:15 p.m.; and 5:15 p.m. to 5:30 p.m. 
#
# 10. __Error screening__
# - Microscopic test: abnormal signal patterns (e.g., splashover, pulse breakup)
#     - splashover: the erroneous detection in one lane of a vehicle from an adjacent lane
#     - pulse breakup: a vehicle should register a single pulse per detector in its lane of travel but instead a detector momentarily drops out in the middle of the vehicle and produces two or more pulses
# - Macroscopic test: aggregated traffic flow relationships (e.g., flow, occupancy, and speed)
#     - Setting thresholds
#         - single-variables: Paynes et al.(1976),
#         - Mathematical relationships between traffic flow variables:
#             - Cleghorn et al.(1991): upper bound of flow-occupancy ratio at the uncongested traffic state
#     - Spatial relationship from direct upstream and downstream detectors: Nihan(1997), Chen et al.(2003), Wall et al. (2003)
#     - Screening for dual loop detectors(after 2000)
#         - __Average effective vehicle length(AEVL), which is equal to g-factor, has been widely used: threshold based__
#             - why?) Can be calculated at the dual loop detector
#             - why?) it is robust to traffic anomalies such as incidents or bad weather, traffic states
#     
#
# 11. __ideas for datasets screening__
# - g-factor: compare g-factor from PeMs with calculated g-factor assuming free-flow speeds(60mph) at the early morning or late night time
# - Adopt PeMS health dataset criteria: 'occ=0', 'Flow=0','High occ', 'High flow', 'Flow=0 & Occ>0', 'Flow>0 & Occ=0', 'Rpt(Repeat) Occ'
# - Conservation laws: conservation between q vs k needs to be guaranteed?
# - Jared Sun: find inconsistent lanes
#     
# </div>
# --

# + [markdown] jp-MarkdownHeadingCollapsed=true
# <div class="alert alert-info">
#
# <p style="font-size: 30px"> NGSIM Summary </p>    
#
# - [Original NGSIM](https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Vehicle-Trajector/8ect-6jqj/about_data)    
#     - Background
#         - FHWA develop a microsimulation system, partnership with simulation developing private companies.
#             - Data was collected for microsimulation behavioral algorithms. The algorithm was then implemented into the simulation.
#         - Dataset
#             - I-80: Emeryville, CA, on April 13, 2005. (500m, 4pm-4:15pm, 5pm-5:15pm, 5:15pm-5:30pm)    
#             - US-101: Hollywood Freeway, in LA, CA, on June 15th, 2005 (640m, 7:50am-8:05am, 8:05am to 8:20am, 8:20am to 8:35am)
#             - Lankershim Boulevard: LA, CA, on June 16, 2005. (3 signalized intersections, 500m, 8:30am-8:45am, 8:45am-9am)
#             - Peachtree Street: Atlanta, GA, on November 8, 2006 (12:45pm-1pm, 4pm- 4:15pm)
#     - [Processed video](https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Program-I-80-Vide/2577-gpny/about_data)
#         - provides raw video and video after superimposing the vehicle_ids
#         - NG-VIDEO was used to automatically detect and track most vehicles from the video images and transcribe the trajectory data to a database. Manual transcription was used to track any vehicles which failed to be automatically detected and tracked.
#             - I-101, I-80 both apply
#
# - Manually re-extracted dataset    
#     - Re-extracted data from [Coifman(2017)](https://www.sciencedirect.com/science/article/pii/S0191261517300838)
#     - all lanes and all of the non-motorcycle vehicles visible in the __I-80 camera 6 for the 0400–0415 time period.__
#     - Background
#         - This research manually re-extracts the vehicle trajectories from a portion of the original NGSIM video to explicitly quantify NGSIM errors, 
#             - e.g., piecewise constant speeds punctuated by brief periods of large acceleration exhibited by the NGSIM data were not evident in the newly extracted trajectories. 
#         - Needless to say, the re-extracted trajectories showed much cleaner speed-spacing relationships than the corresponding raw NGSIM trajectories. 
#         - Finally, this work tracked the original NGSIM vehicles seen in one camera and added another 236 vehicles (11%) visible before/after the period of NGSIM tracking. As of publication, the manually re-extracted data from this paper will be released to the research community
#
#     
#     
# </div>

# + hide_input=false tags=["code"]
# Parameters for handling the data
# raw_timeframe: Defines the timeframe unit in minutes for the input raw data 
# (e.g., 30 seconds is represented as 0.5 minutes).
raw_timeframe = 0.5

# path: The base directory path where the raw data files are stored.
path = '/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github/BPR/11 Rawdata'

# directory: The subdirectory name under the main path where the data files are located.
directory = '30sec'

# VDS_num: The subdirectory name under the main path where the data files are located.
VDS_num = '1203506'

# Constructs the full path to the directory containing the data files.
full_path = os.path.join(path, directory, VDS_num)

# Retrieves a list of all files in the specified directory.
# This list will be used to iterate over or reference the data files for processing.
file_list = os.listdir(full_path)

# total_lane_raw: Total number of lanes at the rawdata
# lane_num: Specifies the range of lane numbers to be analyzed.
# This is used to filter or segment the data based on lane information.

# total_lane_raw = 4
lane_num = [1,2,3,4]

Day_list = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

# Printing the list of files found in the specified directory.
print("Files in the specified directory:", file_list)


# + tags=["code"]
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


# + tags=["code"]
"""
This is the plot of average flow and speed over time for every day.
"""

def plot_within_day(traffic_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num):
    
    # 1st Plot: Time vs Traffic Flow and Avg Speed
    fig, ax = plt.subplots(1,2, figsize=(18,6))
    fig.suptitle(f'Traffic State within a Day using {directory} data(Date: {file_name[8:-5]}({Day}))',fontsize=18)
    ax[0].plot(plot_date, traffic_day['flow'], color='tab:blue')
    
    # Configure x-axis ticks and labels
    x_ticks = range(0, 2400, 100)
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


# + tags=["code"]
""" Sometimes, the rawdata interval is too short to see the stable traffic pattern, so rawdata is aggregated to specific time interval.
This function address calculating traffic state variables in every pre-determined aggregated time interval.
"""

def aggregate_rawdata(rawdata, aggregate_timeframe, raw_timeframe, date, lane_num, gfactor,VDS_num):
    
    # Pre-compute time_slot for all data to avoid doing it in the loop
    rawdata['time_slot'] = np.floor(rawdata['time_filter'] / aggregate_timeframe) * aggregate_timeframe
    
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


# + tags=["code"]
def cv_calculation(agg_data, lane_num, gfactor, date, time, raw_timeframe, plot_whyCV, plot_time, plot_flow):
    
    flow_variable = [f'flow_{lane}' for lane in lane_num]
    density_variable = [f'density_{lane}' for lane in lane_num]
    speed_variable = [f'speed_{lane}' for lane in lane_num]
    
    occ_variable = [f'occ_{lane}' for lane in lane_num]
    gfactor_variable = [f'Lane {lane}' for lane in lane_num]
    
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


def plot_why_CV(traffic_within_day, date, variable, lane_num):
    
    column = [f'{variable}_{lane}' for lane in lane_num]
    data = traffic_within_day[column]
    
    each_mean = np.mean(data, axis=1)
    each_std = np.std(data, axis=1)
    
    fig, ax = plt.subplots(1,1,figsize=(6,6))
    ax.scatter(each_mean, each_std, s=10)
    ax.grid(True)

    # Dictionary to store configuration for each variable type
    config = {
        'flow': {'title': 'Mean Flow Rate vs. Flow Rate Std. Deviation During a Day',
            'xlabel': 'Mean Flow Rate (vph)',
            'ylabel': 'Flow Rate Std. Deviation (vph)',
            'ylim': (0, 600),
            'yticks': range(0, 600, 50),
            'xlim': (0, 2400),
            'xticks': range(0, 2400, 400)},
        'density': {'title': 'Mean Density vs. Density Std. Deviation During a Day',
            'xlabel': 'Mean Density (vpm)',
            'ylabel': 'Density Std. Deviation (vpm)',
            'ylim': (0, 10),
            'yticks': range(0, 10, 2),
            'xlim': (0, 40),
            'xticks': range(0, 40, 5)},
        'speed': {'title': 'Mean Speed vs. Speed Std. Deviation During a Day',
            'xlabel': 'Mean Speed (mph)',
            'ylabel': 'Speed Std. Deviation (mph)',
            'ylim': (0, 20),
            'yticks': range(0, 20, 5),
            'xlim': (0, 80),
            'xticks': range(0, 80, 10)}}

    # Apply configuration based on the variable
    if variable in config:
        ax.set_title(config[variable]['title'], fontsize=15)
        ax.set_xlabel(config[variable]['xlabel'], fontsize=13)
        ax.set_ylabel(config[variable]['ylabel'], fontsize=13)
        ax.set_ylim(*config[variable]['ylim'])
        ax.set_yticks(config[variable]['yticks'])
        ax.set_xlim(*config[variable]['xlim'])
        ax.set_xticks(config[variable]['xticks'])
        
    plt.savefig(f'./02 fig/01 average flow, std scatter/scatter_mean_std_{variable}_{date}.png')


# + solution="hidden" solution_first=true
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
    x_ticks = range(0, 2400, 100)
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


# -

# #### (code) implementation

# + hide_input=false tags=["code"]
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
    # print(file_name)
    
    # Step 0: uploading data and unifying rawdata's format
    cv_threshold = 0.123
    # speed_boundary: 90mph
    speed_bound = 90
    # unit: minute
    # aggregate_timeframe = 5
    aggregate_timeframe = 240
    num_frame = aggregate_timeframe/raw_timeframe
    
    date = file_name[-11:-5]
    gfactor = pd.read_excel(f'{path}/gfactor/{VDS_num}/gfactor_{date}.xlsx') 
    
    rawdata = rawdata_setting(directory,VDS_num,file_name,lane_num)

    if rawdata.shape[0] == 0:
        continue
    else:
        Day = Day_list[int(rawdata.loc[0,'time'].weekday())]
    #     # Step 1: aggregate data to plot or calculate the data
        traffic_within_day, plot_date = aggregate_rawdata(rawdata, aggregate_timeframe, raw_timeframe, date, lane_num, gfactor, VDS_num)

        # Step 1-1: upload saved file
        with open(f'./12 python file/{VDS_num}/traffic_within_day_{date}_{aggregate_timeframe}aggmin_{lane_num}.p', 'rb') as file:
            traffic_within_day = pickle.load(file)

        with open(f'./12 python file/{VDS_num}/plot_date_{date}_{aggregate_timeframe}aggmin.p', 'rb') as file:
            plot_date = pickle.load(file)

        # step 2: calculate daily performance
        over_speed_ratio = len(traffic_within_day[traffic_within_day['speed'] > speed_bound])/len(traffic_within_day)
        detector_health = len(traffic_within_day[traffic_within_day['cv_flow']<=cv_threshold])/len(traffic_within_day['cv_flow']) * 100

        cv_flow_day, cv_density_day, cv_speed_day, cv_flow_day_v2, cv_density_day_v2, daily_flow, daily_density = cv_calculation(traffic_within_day, lane_num, gfactor, date, time = rawdata['time'],raw_timeframe=raw_timeframe, plot_whyCV = False, plot_time = True, plot_flow = True)

        insert = [[date, f'20{date[0:2]}',*daily_flow.tolist(),*daily_density.tolist(), cv_flow_day,cv_density_day, cv_speed_day, cv_flow_day_v2, cv_density_day_v2, over_speed_ratio, detector_health]]

        df_daily_measure = pd.concat([df_daily_measure, pd.DataFrame(insert, columns=df_daily_measure.columns)], ignore_index=True)

        # step 3: plot the graph
        # plot_within_day(traffic_within_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num)
        # plot_within_day_flow(traffic_within_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num)
    #     etc: plot using traffic_within_day to explain why CV is necessary
        # variable = 'speed'
        # plot_why_CV(traffic_within_day, date, variable, lane_num)

        # plot_CV_within_day(traffic_within_day, rawdata, date, aggregate_timeframe, VDS_num)


    with open(f'./12 python file/df_daily_measure_{VDS_num}.p', 'wb') as file:    # james.p 파일을 바이너리 쓰기 모드(wb)로 열기
         pickle.dump(df_daily_measure, file)
# -

df_daily_measure

# +
with open(f'./12 python file/df_daily_measure_{VDS_num}.p', 'rb') as file:
    df_daily_measure = pickle.load(file)

df_daily_measure.to_csv(f'./df_daily_measure_{VDS_num}.csv')
    
    
# df_daily_measure['daily_speed_1'] = df_daily_measure['daily_flow_1'] / df_daily_measure['daily_density_1']

# print(df_daily_measure.loc[df_daily_measure['year']=='2017','daily_flow_1'].mean())
# print(df_daily_measure.loc[df_daily_measure['year']=='2024','daily_flow_1'].mean())

# print(df_daily_measure.loc[df_daily_measure['year']=='2017','daily_flow_1'].mean())
# print(df_daily_measure.loc[df_daily_measure['year']=='2024','daily_flow_1'].mean())

# + [markdown] tags=["slides"]
# ### Detector Health Evaluation
# - Detector health index: the ratio of CV less than upper threshold * 100
#     - 100: all CVs in a specific date are less than upper threshold: perfect functioning.
#     - The upper threshold: 99% critical value(0.123)
# - I expect this this threshold will increase when we implement I-24.

# + tags=["code"]
with open('df_daily_measure.p', 'rb') as file:
    df_daily_measure = pickle.load(file)

print(str(df_daily_measure['date'])[1:4])
df_daily_measure['date'] = df_daily_measure['date'].astype(str)
df_daily_measure['month'] = df_daily_measure['date'].apply(lambda x: x[-6:-2])

df_daily_measure_filter = df_daily_measure[~ (df_daily_measure['month'].isin(['1109','1209','1409','1509','2308']))]

# print(df_daily_measure_filter)

# print(df_daily_measure.head())
bin_size_cv = 0.01
bin_size_grade = 1
variable = 'density'
lane_num = [1, 2, 3, 4]

print(df_daily_measure_filter[['cv_flow_day','cv_density_day']].corr())

# df_daily_measure_filter.to_csv("./03 analysis_result/df_daily_measure_f.csv")

# print(df_daily_measure_filter.head())
# plot_cv_case_comparison(df_daily_measure_filter)
# plot_cv_absgap(df_daily_measure_filter)
# plot_cv_histo_across_years(df_daily_measure_filter, variable, bin_size_cv)
# plot_health_grade_histo_across_years(df_daily_measure_filter, bin_size_grade)
# plot_within_year_flow(df_daily_measure_filter, lane_num)

# + tags=["code"]
## CV distribution depending on the year

def plot_cv_histo_across_years(df_daily_measure,variable, bin_size):
    
    fig, ax = plt.subplots(1,1,figsize=(8,5))
    cv_data = df_daily_measure[['year',f'cv_{variable}_day']]

    for year, group in cv_data.groupby("year"):
        nbins = int((group[f'cv_{variable}_day'].max()-group[f'cv_{variable}_day'].min())/bin_size)
        ax.hist(group[f'cv_{variable}_day'], nbins, histtype='bar',stacked = True, label = year)

    ax.legend(fontsize = 13)
    ax.set_xlabel('Coefficient of variation (CV)', fontsize = 13) 
    ax.set_ylabel('Frequency', fontsize = 13)
    ax.set_title(f'Histogram of {variable} CVs across Years', fontsize = 16)
    ax.set_xticks([i*0.05 for i in range(0,13,1)])

    plt.savefig(f'./02 fig/hist_cv_year_{variable}.png')
    plt.close()


# +
"""
This is the plot of average flow and speed over time for every day.
"""
import seaborn as sns

def plot_within_year_flow(df_daily_measure, lane_num):
    
    # 1st Plot: Time vs Traffic Flow and Avg Speed    
    color_dict = ['red','blue','black','green']
    n_xbin = 15
    df_daily_measure['date_v2'] = df_daily_measure['date'].str[-4:-2] + "/" + df_daily_measure['date'].str[-2:]

    sns.set_theme(style="whitegrid")
    
    fig, ax = plt.subplots(5,2, figsize=(35,45))
    fig.suptitle("Traffic Patterns for Each Lane over a Year", fontsize = 25)
    
    for year_idx, year in enumerate(df_daily_measure['year'].unique()):
        
        sub_data = df_daily_measure[df_daily_measure['year'] == year]
        
        for idx, lane in enumerate(lane_num):
            ax[year_idx,0].plot(sub_data['date_v2'], sub_data[f'daily_flow_{lane}'], label = f'lane {lane}',linewidth=2.5, color=color_dict[idx])
            ax[year_idx,1].plot(sub_data['date_v2'], sub_data[f'daily_density_{lane}'], label = f'lane {lane}',linewidth=2.5, color=color_dict[idx])

        if len(sub_data['date_v2']) > n_xbin:
            multiple = np.round(len(sub_data['date_v2']) / n_xbin,0)
            xlabel = [int(multiple*i) for i in range(int(len(sub_data['date_v2'])//multiple))]
            
            x_ticks = sub_data['date_v2'].iloc[xlabel]
            x_labels = sub_data['date_v2'].iloc[xlabel]

            for j in range(2):
                ax[year_idx,j].set_xticks(ticks=x_ticks, labels=x_labels, fontsize=18, rotation = 45)
                ax[year_idx,j].locator_params(axis='x', nbins=n_xbin)
                
        elif len(sub_data['date_v2']) <= n_xbin:
            x_ticks = range(len(sub_data['date_v2']))
            for j in range(2):
                ax[year_idx,j].set_xticks(x_ticks)
                ax[year_idx,j].set_xticklabels(sub_data['date_v2'], rotation=45, fontsize = 20)

        conditions = [(0, 'Flow rates (vphpl)', 2700), (1, 'Densities (vpmpl)', 60)]
        
        
        for j, ylabel, ylim in conditions:
            
            ax[year_idx,j].grid(True)
            ax[year_idx,j].legend(fontsize = 20)
            # Set plot title and labels
        #     ax.set_title(f'Flow Rate Trends for Each Lane Over a Day',fontsize=13)
            ax[year_idx,j].set_ylabel(ylabel, fontsize=20)
            ax[year_idx,j].tick_params(axis='y')
            ax[year_idx,j].set_xlabel('Date(mm/dd)', fontsize=20)
            ax[year_idx,j].set_yticks(range(0,int(ylim),int(ylim/10)))
            ax[year_idx,j].set_yticklabels(range(0, int(ylim), int(ylim / 10)), fontsize = 20)        

    plt.savefig(f'./02 fig/11 Unit time_flow/year_{lane_num}.png')
    plt.close()

# + tags=["code"]
"""
def plot_cv_case_comparison(df_daily_measure):

    fig, ax = plt.subplots(1,2,figsize=(16,8))

    # Plotting a basic histogram
    ax[0].hist(df_daily_measure['cv_case1'], bins=30, color='skyblue', edgecolor='black', label='case 1', histtype='bar',stacked= True)
    ax[0].hist(df_daily_measure['cv_case2'], bins=30, color='gray', edgecolor='black', label='case 2', histtype='bar',stacked=True)

    # Adding labels and title
    ax[0].set_xlabel('Values')
    ax[0].set_ylabel('Frequency')
    ax[0].set_title(f'Histogram of Coefficient of Variation')

    ax[0].legend()

    ax[1].scatter(df_daily_measure['cv_case1'],df_daily_measure['cv_case2'])

    # Adding labels and title
    ax[1].set_xlabel('daily cv using total flows(case 1)')
    ax[1].set_ylabel('daily cv using individual time-frame cv(case 2)')
    ax[1].set_title('Scatter plot of CVs based on different methodologies')

    ax[1].set_xlim(0,0.7)
    ax[1].set_ylim(0,0.7)

    ax[1].grid()

    plt.savefig(f'./02 fig/cv_plot_.png')

    # Display the plot
    plt.close()
"""

# + tags=["code"]
"""def plot_cv_absgap(df_daily_measure):
    fig, ax = plt.subplots(1,1,figsize=(8,8))

    ax.scatter(df_daily_measure['cv_case1'],df_daily_measure['absolute_gap'])

    # Adding labels and title
    ax.set_xlabel('daily cv using total flows(case 1)')
    ax.set_ylabel('daily absolute gap')
    ax.set_title('Scatter plot of CVs and absolute gaps')

    ax.set_xlim(0,0.7)
    ax.set_ylim(0,1.5)

    ax.grid()

    plt.savefig(f'./02 fig/02 Multiple measures comparison/cv_abs_gap_plot.png')

    # Display the plot
    plt.close()
"""
# -

"""
## CV distribution depending on the year

def plot_cv_histo_across_years(df_daily_measure,variable, bin_size):
    
    fig, ax = plt.subplots(1,1,figsize=(12,6))

    for year, group in df_daily_measure.groupby("year"):
        nbins = int((group[variable].max()-group[variable].min())/bin_size)
        ax.hist(group[variable], nbins, histtype='bar',stacked = True, label = year)

    ax.legend(fontsize = 18)
    ax.set_xlabel('cv', fontsize = 15) 
    ax.set_ylabel('Frequency', fontsize = 15)
    ax.set_title(f'Histogram of {variable} across Years', fontsize = 20)
    ax.set_xticks([i*0.05 for i in range(0,13,1)])

    plt.savefig(f'./02 fig/hist_{variable}_year.png')
    plt.close()
    """


# + tags=["code"]
## health grade distribution depending on the year
def plot_health_grade_histo_across_years(df_daily_measure, bin_size):
    
    fig, ax = plt.subplots(1,1,figsize=(12,6))

    for year, group in df_daily_measure.groupby("year"):
        nbins = int((group['detector health'].max()-group['detector health'].min())/bin_size)
        ax.hist(group['detector health'], nbins, histtype='bar',stacked = True, label = year)

    ax.legend(fontsize = 18)
    ax.set_xlabel('detector health grade', fontsize = 15) 
    ax.set_ylabel('Frequency', fontsize = 15)
    ax.set_title('Histogram of Detector Health Grade across Years', fontsize = 20)
    ax.set_xticks([i*10 for i in range(0,10,1)])

    plt.savefig(f'./02 fig/hist_healthgrade_year.png')
    plt.close()


# + [markdown] tags=["past"]
# <div class="alert alert-danger">
# Clustering
#
#     
# - k-means vs k-nn
#     - k-means: unsupervised learning, refers to the number of clusters
#     - k-nn: supervised learning, the object being assigned to the class most common among its  nearest neighbors
# - k-means implementation
#     - Before normalization
#         - y-axis variable did not divided due to its relatively smaller scale
#         - 그림추가 필요
#
# - After normalization
#     - 그림추가 필요
#     
# </div>
#

# + jupyter={"outputs_hidden": true} tags=["code"]
def kmeans_plot(data_2d,num_clusters,normalization):
    
    if (normalization == True):
        normalized="normalized"
    else:
        normalized="un-normalized"
        
    kmeans = KMeans(num_clusters)
    kmeans.fit(data_2d)

    # Predict the cluster for each data point
    y_kmeans = kmeans.predict(data_2d)
    
    # Plot the clustered data
    fig, ax = plt.subplots(1,2,figsize=(18,6))

    ax[0].scatter(data_2d['cv_case1'], data_2d['over_speed_ratio'], c=y_kmeans, s=20, cmap='viridis')

    # Plot the centroids
    centroids = kmeans.cluster_centers_

#     ax[0].set_ylim(0,0.1)
    ax[0].set_ylabel(f'Ratio of over upper speed({speed_bound}mph)',fontsize = 12)

    ax[0].set_title(f'K-means Clustering(k={num_clusters},{normalized})')
    ax[0].set_xlabel('Coefficient of Variation(CV)')

    df_daily_measure_group = df_daily_measure.groupby('year')

    for name, group in df_daily_measure_group:
        ax[1].plot(group[var[0]], group["over_speed_ratio"], marker="o", linestyle="", label=f"{name}")

    ax[1].set_title('Scatter-plot labeled by year')
    ax[1].set_ylim(0,0.1)
    ax[1].set_xlabel('Coefficient of Variation(CV)')
    ax[1].set_ylabel(f'Ratio of speeds exceeding upper limits',fontsize = 12)

    ax[1].legend()

    plt.savefig(f'./02 fig/04 CV_kmeans/kmeans_{num_clusters}_{normalized}.png')
    plt.close()


# + jupyter={"outputs_hidden": true} tags=["code"]
with open('df_daily_measure.p', 'rb') as file:
    df_daily_measure = pickle.load(file)

# Assuming cv_list[:, 1] is your 1D data that was used for KMeans
var = ['cv_case1','over_speed_ratio']
data_2d = df_daily_measure[var]
data_2d_normalized = (data_2d - data_2d.mean()) / data_2d.std(ddof=1)

# Use KMeans to cluster the data into 3 clusters
num_clusters = 6

## before normalization and after
kmeans_plot(data_2d,num_clusters,normalization=False)
kmeans_plot(data_2d_normalized,num_clusters,normalization=True)

# + tags=["code"]
print(df_daily_measure['year'].unique())

idx__ = (df_daily_measure['year'] == '2011') & (df_daily_measure['over_speed_ratio'] > 0.01)
weird_dates = [item[0] for item in df_daily_measure[idx__][['date']].values.tolist()]
lane_num = [1,2,3,4]

print(weird_dates)
print(df_daily_measure[idx__])

# idx__ = (df_daily_measure['cv_case1'] < 0.25) & (df_daily_measure['over_speed_ratio'] < 0.005)
# filtered_dates = ['Rawdata_' + item[0] for item in df_daily_measure[idx__][['date']].values.tolist()]

# for date in weird_dates:
    
#     # Step 1-1: upload saved file 
#     with open(f'./12 python file/traffic_day_{date}_{lane_num}.p', 'rb') as file:
#         traffic_day = pickle.load(file)

#     with open(f'./12 python file/plot_date_{date}.p', 'rb') as file:
#         plot_date = pickle.load(file)

#     # step 2: calculate daily performance
#      # speed_boundary: 90mph

#     # step 3: plot the graph
#     plot_within_day(traffic_day, plot_date, directory, file_name, Day, aggregate_timeframe, date, lane_num)

# -

# ## I-24

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["slides", "main"]
# # Discussion

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["slides", "main"]
# # Conclusion

# + [markdown] tags=["slides"]
# - HOT, HOV demand-supply side 

# + [markdown] jp-MarkdownHeadingCollapsed=true
# # Reference

# + [markdown] tags=["code"]
# <div class="alert alert-success" role="alert">
#
# - 1) Klein LA, Mills MK, Gibson D, Klein LA. Traffic detector handbook: Volume II. United States. Federal Highway Administration; 2006 Oct 1.
# - 2) Turner S, Carson J, Zimmerman C, Wilkinson LJ, Travis K. Traffic monitoring: A guidebook. United States. Federal Highway Administration. Western Federal Lands Highway Division; 2010 Jul 1.
# - 3) Csiszár C, Sándor Z. Method for analysis and prediction of dwell times at stops in local bus transportation. Transport. 2017 Jul 3;32(3):302-13.
# - 4)  Middleton D, Gopalakrishna D, Raman M. Advances in traffic data collection and management. Intelligent Transportation Systems Report. 2003 Jan(13766).
# - 5) Chen C, Petty K, Skabardonis A, Varaiya P, Jia Z. Freeway performance measurement system: mining loop detector data. Transportation research record. 2001;1748(1):96-102.
# - 6) Coifman B. Vehicle level evaluation of loop detectors and the remote traffic microwave sensor. Journal of transportation engineering. 2006 Mar;132(3):213-26.
# - 7) Minge E, Petersen S, Kotzenmacher J. Evaluation of nonintrusive technologies for traffic detection, phase 3. Transportation research record. 2011;2256(1):95-103.
# - 8) Klein LA, Mills MK, Gibson DR. Traffic detector handbook: Volume I. Turner-Fairbank Highway Research Center; 2006 Oct 1.
# - 9) Chen C, Kwon J, Rice J, Skabardonis A, Varaiya P. Detecting errors and imputing missing data for single-loop surveillance systems. Transportation Research Record. 2003;1855(1):160-7.
# - 10) Cheevarunothai P, Wang Y, Nihan NL. Identification and correction of dual-loop sensitivity problems. Transportation Research Record. 2006 Jan;1945(1):73-81.
# - 11)  Yu R, Zhang G, Wang Y. Loop detector segmentation error and its impacts on traffic speed estimation. Transportation research record. 2009;2099(1):50-7.
# - 12) Payne HJ. Development and testing of incident detection algorithms, Volume 1: summary of results. 1976 Apr.
# - 13)  Jacobson LN, Nihan NL, Bender JD. Detecting erroneous loop detector data in a freeway traffic management system. 1990.
# - 14)  Li J, Van Zuylen HJ, Wei G. Loop detector data error diagnosing and interpolating with probe vehicle data. In93rd Annual Meeting Transportation Research Board, Washington, USA, 12-16 January 2014; Authors version 2014. TRB.
# - 15) Sun Z, Jin WL, Ng M. Network sensor health problem. Transportation Research Part C: Emerging Technologies. 2016 Jul 1;68:300-10.
# - 16) Cassidy MJ, Daganzo CF, Jang K, Chung K. Empirical reassessment of traffic operations: Freeway bottlenecks and the case for HOV lanes.
#
# </div>

# + [markdown] tags=["main"]
# <div class="alert alert-success" role="success">
#
# __7. Reference__
#
# - 1) Papageorgiou, M., H. Hadj-Salem, and F. Middleham. ALINEA Local Ramp Metering Summary of Field Results. In Transportation Research Record 1603, TRB, National Research Council, Washington, D.C., 1997, pp. 90–98.
# - 2) Hourdakis, J., and P. G. Michalopoulos. Evaluation of Ramp Control Effectiveness in Two Twin Cities Freeways. In Transportation Research Record: Journal of the Transportation Research Board, No. 1811, Transportation Research Board of the National Academies, Washington, D.C., 2002, pp. 21–29.
# - 3) Payne, H. J., and S. C. Tignor. c
# - 4) Payne, H. J., and S. M. Thompson. Development and Testing of Operational Incident Detection Algorithms: Technical Report. FHWA, U.S. Department of Transportation, 1997.
# - 5) Williams, B. M., and A. Guin. Traffic Management Center Use of Incintdent Detection Algorithms: Findings of a Nationwide Survey. IEEE Transactions on Intelligent Transportation Systems, Vol. 8, No. 2, s007, pp. 351–358.
# - 6) Kwon, J., B. Coifman, and P. Bickel. Day-to-Day Travel-Time Trends and Travel-Time Prediction from Loop-Detector Data. In Transportation Research Record: Journal of the Transportation Research Board, No. 1717, TRB, National Research Council, Washington, D.C., 2000, pp. 120–129.
# - 7) Coifman, B., and S. Krishnamurthy. Vehicle Reidentiﬁcation and Travel Time Measurement Across Freeway Junctions Using the Existing Detector Infrastructure. Transportation Research Part C, Vol. 15, No. 3, 2007, pp. 135–153.
# - 8) Traffic Monitoring Guide. FHWA, U.S. Department of Transportation, 2001.
# - 9) Coifman, B., and S. Kim. Speed Estimation and Length Based Vehicle Classiﬁcation from Freeway Single Loop Detectors. Transportation Research Part C, Vol. 17, No. 4, 2009, pp. 349–364.
# - 10) Coifman B. Vehicle level evaluation of loop detectors and the remote traffic microwave sensor. Journal of transportation engineering. 2006 Mar;132(3):213-26.
# - 11) Chen C, Petty K, Skabardonis A, Varaiya P, Jia Z. Freeway performance measurement system: mining loop detector data. Transportation research record. 2001;1748(1):96-102.
# - 12) Turochy RE, Smith BL. New procedure for detector data screening in traffic management systems. Transportation Research Record. 2000;1727(1):127-31.
# - 13) Chen C, Kwon J, Rice J, Skabardonis A, Varaiya P. Detecting errors and imputing missing data for single-loop surveillance systems. Transportation Research Record. 2003;1855(1):160-7.
# - 14) Rajagopal R, Varaiya PP. Health of California's loop detector system. 2007 Aug.
# - 15) Sun Z, Jin WL, Ng M. Network sensor health problem. Transportation Research Part C: Emerging Technologies. 2016 Jul 1;68:300-10.
# - 16) Taylor SJ. Modelling financial time series. world scientific; 2008.
#     
# </div>
# -

# # Memo(Sources for Introduction)

# <div class="alert alert-info">
#
# ## __# of datasets: 327 in total__
# - __104 datasets__ in 2011(Jun. ~ Apr.)
# - __16 datasets__ in 2014(Aug., Sep.)
# - __176 datasets__ in 2015 data (Jun. ~ Nov., 176 datasets)
# - __31 datasets__ in 2024(Jun.)
#
# </div>

# <div class="alert alert-info">
#
#    
# ## __PeMs User Guide__
# - Speed
#     - the speed is either measured directly: possible with radar detectors
#     - calculated: using a g-factor accompanying the flow and occupancy as with single-loop detector
#     - Our location is double-loop and mentioned as "speeds are estimated" 
#     - For the aggregate speed that spans all of the loops, the speed is the flow-weighted mean across the lanes.
# - g-factor
#     - The g-factor is a conversion factor used to convert the measured quantities of flow and occupancy into speed for detectors that do not measure speed directly. The g-factor is a combination of two quantities: __1)__ the average length of the vehicles traveling over the detector and __2)__ the tuning of the detector. Each detector in the system has its own tuning characteristics. PeMS calculates a g-factor for every single detector over __every 5-minute period__ for an entire week. By doing this, PeMS captures the weekly characteristics of the traffic mix as well as the individual characteristics of each detector.
#     - However, a specific lane or lanes have not been designated on a divided highway having four or more clearly marked lanes for traffic in one direction, ... those vehicles may also be driven in the lane to the immediate left of that right-hand lane [link](https://dot.ca.gov/programs/traffic-operations/legal-truck-access/truck-lane-use#:~:text=those%20vehicles%20shall%20be%20driven,the%20right%20edge%20or%20curb.)
#      
#
# </div>

# <div class="alert alert-info">
#      
# ## __Capacity drop__
# - Capacity drop refers to when the q-k curve does not follow the F.D., but rather shows a horizontally dispersed at the certain level of point
# - The commonly well-known case is at the intersection
#     - At the intersection, when the light turns green and cars start moving, even if there's nothing blocking their way, the flow of traffic doesn't reach full capacity because there aren't enough cars to fill up the road.
#     - In this stationary case, data from loop detectors, which monitor both the traffic coming towards the intersection and the traffic leaving it, show that the average density spreads out within the density of upstream and downstream traffic.
#     - This leads to a trapezoid shape on the traffic flow diagram. Instead of reaching a peak, the points on the diagram spread out horizontally at a certain level.
#     - Likewise, the bottleneck shows this pattern as vehicles got stuck at the merging point.
# - If the road is really long, you'd expect the traffic jam to be super dense, but that's not necessarily the case because of physical limits.
#     
# </div>

# <div class="alert alert-info">
#
# ## __Qiinlong's paper__
# - Theme: Automatic identification of near-stationary traffic states
#     - The major contributwasnto develop method toelop automatically select the candidates for stationary time series.
#     - And then apply Cassidy(1998) method to finally determine near-stationary state__s
# - why SR-9__1 E? can detect stationary equilibrium state(70ft above from the merging point)
#     
# </div>

# <div class="alert alert-info">
#
# ## __SR-91, EB, (VDS 1203506)__
# - about 70ft upstream from the merge point(Valley-view, bottleneck)
# - EB: But this road is not that much related with commute trip, so it showed one-peak point.
#     
# </div>

# <div class="alert alert-info">
#
#
# ## __BPR function__
# - BRP function can only be defined on a congested part(also can verify in the Vickery)
#     - BPR function is the relationship of the supply and demand equilibrium state, and the equilibrium happens only at the congested state
#     - so, based on the defined BPR at the congested period, we can derive fundamental diagram at the congested period.
# - The next step after defining BPR is to define F.D.
#     - By individually defining the F.D. for each side, we can determine the length of flat line in the middle.
# - Only applicable for the two-peak cases
# - If the proportion of volumes is constant, it can be expanded to the whole day.
#
# 6. __Peak-period finding__
# - how to define the peak period
#     
# </div>

# <div class="alert alert-info">
#
# ## __g-factor__
# - 2011: 24 ~ 26ft for lane 3, 19~22ft for the rest of lanes
# - 2014: varies a lot
# - Reference
#     - compact: 10~14ft
#     - midsize: 14~16ft
#     - large-SUV: 16.7ft
#     - fullsize: 16~18ft
#     - Large pickup: 18.4ft
#
# - __how g-factor is calculated__
#     - single-loop detector
#         - The PeMS algorithm(Zhanfeng, Coifman, et al.(2001))
#             - Determine the g-factor in an uncongested traffic state using the measured q and occupancy, assuming free-flow speed.
#                 - $g_{instant}(t)=\frac{o(t)}{q(t)}\times u_{free}$ ($o(t)$: occupancy, $q(t)$: flow rates(vph), $u_{free}$ : 65mph) 
#             - Then, adjust the g-factor for congested periods using historical data. (historical g-factor data are given)
#                 - $g(t) = g_{instant}(t) + [g_{hist}(t+\tau)-g_{hist}(t)]$ ($g_{hist}(t): \text{historical g-factor at time t}, \tau: \text{delay time(hr)}$)
#     - dual-loop detector
#         - calculated by u,q,occ:
#             - $g(t)=\frac{o(t)}{q(t)}\times \bar{u}(t)$ (o(t): occupancy, q(t): flow rates(vph), u:velocity(mph))
#     
# </div>

# <div class="alert alert-info">
#
# ## __Error screening__
# - Microscopic test: abnormal signal patterns (e.g., splashover, pulse breakup)
#     - splashover: the erroneous detection in one lane of a vehicle from an adjacent lane
#     - pulse breakup: a vehicle should register a single pulse per detector in its lane of travel but instead a detector momentarily drops out in the middle of the vehicle and produces two or more pulses
# - Macroscopic test: aggregated traffic flow relationships (e.g., flow, occupancy, and speed)
#     - Setting thresholds
#         - single-variables: Paynes et al.(1976),
#         - Mathematical relationships between traffic flow variables:
#             - Cleghorn et al.(1991): upper bound of flow-occupancy ratio at the uncongested traffic state
#     - Spatial relationship from direct upstream and downstream detectors: Nihan(1997), Chen et al.(2003), Wall et al. (2003)
#     - Screening for dual loop detectors(after 2000)
#         - __Average effective vehicle length(AEVL), which is equal to g-factor, has been widely used: threshold based__
#             - why?) Can be calculated at the dual loop detector
#             - why?) it is robust to traffic anomalies such as incidents or bad weather, traffic states
#     
#
# ## __ideas for datasets screening__
# - g-factor: compare g-factor from PeMs with calculated g-factor assuming free-flow speeds(60mph) at the early morning or late night time
# - Adopt PeMS health dataset criteria: 'occ=0', 'Flow=0','High occ', 'High flow', 'Flow=0 & Occ>0', 'Flow>0 & Occ=0', 'Rpt(Repeat) Occ'
# - Conservation laws: conservation between q vs k needs to be guaranteed?
# - Jared Sun: find inconsistent lanes
# </div>

# <div class="alert alert-info">
#
# ## NGSIM Summary
#
# ### [Original NGSIM](https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Vehicle-Trajector/8ect-6jqj/about_data)    
# - Background
#     - FHWA develop a microsimulation system, partnership with simulation developing private companies.
#         - Data was collected for microsimulation behavioral algorithms. The algorithm was then implemented into the simulation.
#     - Dataset
#         - __I-80: Emeryville, CA, on April 13, 2005. (500m(1640ft), 4pm-4:15pm, 5pm-5:15pm, 5:15pm-5:30pm)__
#             - A seven synchronized digital video camera
#         - US-101: Hollywood Freeway, in LA, CA, on June 15th, 2005 (640m, 7:50am-8:05am, 8:05am to 8:20am, 8:20am to 8:35am)
#         - Lankershim Boulevard: LA, CA, on June 16, 2005. (3 signalized intersections, 500m, 8:30am-8:45am, 8:45am-9am)
#         - Peachtree Street: Atlanta, GA, on November 8, 2006 (12:45pm-1pm, 4pm- 4:15pm)
# - [Automation Process(Processed video)](https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Program-I-80-Vide/2577-gpny/about_data)
#     - provides raw video and video after superimposing the vehicle_ids
#     - NG-VIDEO was used to automatically detect and track most vehicles from the video images and transcribe the trajectory data to a database. Manual transcription was used to track any vehicles which failed to be automatically detected and tracked.
#         - I-101, I-80 both apply
#
# ### Manually re-extracted dataset    
# - Re-extracted data from [Coifman(2017)](https://www.sciencedirect.com/science/article/pii/S0191261517300838)
# - all lanes and all of the non-motorcycle vehicles visible in the __I-80 camera 6 for the 0400–0415 time period.__
# - Background
#     - This research manually re-extracts the vehicle trajectories from a portion of the original NGSIM video to explicitly quantify NGSIM errors, 
#         - e.g., piecewise constant speeds punctuated by brief periods of large acceleration exhibited by the NGSIM data were not evident in the newly extracted trajectories. 
#     - Needless to say, the re-extracted trajectories showed much cleaner speed-spacing relationships than the corresponding raw NGSIM trajectories. 
#     - Finally, this work tracked the original NGSIM vehicles seen in one camera and added another 236 vehicles (11%) visible before/after the period of NGSIM tracking. As of publication, the manually re-extracted data from this paper will be released to the research community
#     
# ### NGSIM Convergence domain size
# - NGSIM: Length: 1650ft(500m), Time: 45min
# - Convergence: 800ft, 180sec
#     - 60mph=1mile/minute=5280ft/min=88ft/sec : 9sec
#     - 800ft=0.15mile=
#     
# </div>

# # Plan after submitting 2025 TRB paper
#
# 1. Clarification of result: need more time to strengthen the logic of the result
# - Justification of 2014 dataset as malfunction
# - Some CV values in NGSIM exceeded our empirical density threshold of 0.19, as shown in PeMS
#
# 2. Additional dataset
# - I-24
#     - I am curious about the result, as the PeMS sometimes show higher CV during off-peak perioid due to very small mean
#     - What Charlie is doing is to transform the data structure to the NGSIM,
#     - Once it is done, I will analyze the CV patterns from I-24 data, and I expect many pattern scenarios will be discovered as it covers the a wide range of time-spatial domain.
#     - The main reason to use I-24 is to evalute extended time period. So, if the data size matters for calculation, I think lessening the spatial range would be another approach. Now, charlie is dividing the entire dataset into every 1 hour, but I have to use the whole time period in the end.  so, I have asked to Charlie to apply the distance when dividing the dataset, for the case when a portion of space is analyzed.

# <div class="alert alert-info">
#
# <p style="font-size: 30px"> I-24 Summary </p>    
#
# __1. Outline__
# - Location:  I-24 in the Nashville-Davidson County Metropolitan area
#     - 4.2 miles (6.75km) on the 4-5 lanes (each direction)
#     - lane 1: HOV
# - Date
#     - 21-24.Nov.2022 (Mon.-Thu.) (6am-10am)
#     - 25.Nov.2022 (Fri.) (6am-5pm)
#     - 28-30.Nov., 1-2.Dec.2022 (Mon.-Fri.) (6am-10am)
#     - 나중에 5-6 hours 여러 days 통해 daily pattern 확인해볼 수는 있음
# - 294 pole-mounted traffic cameras
# - Lane delination: for trajectories in direction "-1" (westbound)
#     - 12-24, lane 1 (HOV lane)
#     - 24-36, lane 2
#     - 36-48, lane 3
#     - 48-60, lane 4
# - Variable
#     - the primary (x) axis aligned along the interstate roadway median
#     - the secondary (y) axis defined locally perpendicular to the primary axis 
# __2. Accuracy__
# - I-24 MOTION firstly transforms the video to traffic information data through the video processor. and it also proceeds trajectory post-processing. Through the article, they compared the result with manually labeled ground truth data, showing 84% of data are within 1 m error. considering our focus is to analyze macroscopic traffic states, I think it is enough to regard it as groundtruth data.
#     - (p8) I-24 MOTION uses an automatic data post-processing pipeline [98] which will be continuously improved to automate as much of the data cleaning steps as possible. C (p10) 
#
# __3. Lists to discuss__
# - Availability of "internal use only" variable.
#     - "flags": describing the tracking processes (i.e., "Lost", "Overlap")
#       - "Overlap": What is the overlap refers(?) : if it appears twice in the dataset, we need to eliminate
#       - "Lost":
#     - "feasibility" : Feasibility score for some metrics
# - The direction "+1" is possible to delinate based on the y-values
# - If the time & location has same length for each vehicle?
# - veh-to-veh variable은 없는지??
#     
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["main"]
# <div class="alert alert-success">
#
# Each sample of I-80 trajectory data includes information such as instantaneous speed, acceleration, longitudinal and lateral positions, lane number, global time, vehicle length, and vehicle type. To calculate lane-to-lane variation, several steps are necessary. First, the raw data must be preprocessed. The dataset contains vehicle trajectories in the HOV lane and on-ramps, which we excluded because they typically exhibit different traffic behaviors compared to regular lanes. Another task is determining the temporal-spatial domain. The trajectory data starts with the first vehicle entering the observed highway section during the period, so vehicles ahead are not detected. To ensure the dataset includes all vehicle trajectories, we redefined the start time as when the first vehicle reaches the end of the section and the end time as when the last tracked vehicle enters the section.
#     
# Each data point covers a 15-minute period and 500 meters (1600 feet). To gain more precise and localized insights into traffic patterns, we divided the domain into smaller sub-domains, each representing a 5-minute period and 200 feet. This finer subdivision allows us to observe and compare traffic conditions over shorter distances and times more accurately. Such detailed analysis is crucial because traffic flow can vary significantly even over small segments of a highway and brief time intervals. Following this subdivision, we computed the Vehicle Miles Traveled (VMT) and Vehicle Hours Traveled (VHT) based on travel time and distance per lane for each vehicle. Using these computations, we then calculated traffic flow rates, density, and speed with Edie's formula (reference needed). Finally, we obtained lane-to-lane variation by calculating the relative variance of each traffic variable across lanes.
#
# </div>

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["slides"]
# <img src="https://github.com/jooneui/fig_collection/blob/main/NGSIM_CV_Edie__.jpg?raw=true" align='center' width = 60%> <br>
#
# - VMT: the total distance traveled by all vehicles
# - VHT: the total time travelled by all vehicles

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["main"]
# <div class="alert alert-success">
#     
# - m,q,k 결과
# - CV-flow, density, speed 결과 정리
# - normal distribution 따르는지 정리
# </div>

# + [markdown] tags=["slides"]
# #### Result
# - The average variation is 0.096 for flow, 0.129 for density, and 0.144 for speed.
#     - The lower average values of speeds affect the higher CV, despite showing relatively consistent values across the lanes.
# - The inconsistency between flow, density, and speed seen in the last interval seems disappeared after setting the temporal-spatial domain.
# - Lanes 2 and 6 did not show similar patterns to the other lanes.
#     - It is also verified in the video (Camera 5, around 8 minutes within the 4:00 to 4:15 period).
#     - Lane 2 usually showed less congestion, while Lane 6 fluctuated depending on its location (before or after merging).
# - Meanwhile, the values in the middle lanes stayed within a relatively consistent range.
#     - The average variation for flow decreased to 0.054, fot the density to 0.102, and for the speed to 0.09.
#     | lanes | q | k | u |
# |----------|----------|----------|----------|
# | all lanes | 0.096   | 0.129   | 0.144   |
# | middle lanes  | 0.054  | 0.102   | 0.09  |
#
# - How can determine the groundtruth value?
#     - The NGSIM traffic condition was congested
#     - Location-dependent
#     - Time-dependent

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=["notes"]
# <div class="alert alert-info">
#
# __Question__
#     
# 1. What if a certain situation has a different distribution? 
# - The 95% critical value might not be applicable in such cases. To justify using this value universally, we need to demonstrate that all sample CVs are statistically close enough across various situations.
#     - So, I think we need to test if the distribution are different depending on the space and time
#         - In NGSIM, 1500 ft space domian, divide into several sub-domains, and identify if the distribtuions are signficantly different.
#
# <img src="https://github.com/jooneui/fig_collection/blob/main/Comparison%20of%20Distribution(overall,%20specific).jpg?raw=true" align='center' width = 40%> <br>
#
#     
# </div>
#
# -

# ### The sensitivity of CV depending on the Edie size
