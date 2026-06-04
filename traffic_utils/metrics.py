import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def BPR_function(t_0,C,alpha,beta,N):
    t =  t_0 * (1+alpha*(N/C)**beta)
    return t

def Triangular_FD_congested(q,k_j,w):
    t = (k_j/q-1/w)*60
    return t

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
