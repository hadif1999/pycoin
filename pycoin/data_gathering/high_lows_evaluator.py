import pandas as pd
import sys
sys.setrecursionlimit(1000)
import numpy as np
import datetime as dt
from scipy.signal import argrelextrema
from pycoin.data_gathering.trend_filters import fill_between_pivots, remove_less_than_min_time


SUGGESTED_CANDLE_RANGE = {
            "1min":1600*3*2*3, "3min":1600*3*2, "5min":1600*3, "15min":1600, "30min":800,
            "1hour":400, "2hour":200,"4hour":100 ,"6hour":80,
            "8hour":50, "12hour": 100//3 , "1day": 100//6,"1week":(100//6)//7 }

    
def get_market_High_Lows(dataframe:pd.DataFrame, 
                         candle_range:int, mode:str = "clip", *,
                         high_col:str = "High", low_col:str = "Low", datetime_col:str = "Datetime",
                         min_time_dist:list = dt.timedelta(hours= 13),
                         fill_between_two_same:bool = True,
                         remove_under_min_time_dist:bool = True ):
    """this function evaluates input market highs, lows. and returns their index. 

    Args:
        candle_range (int, optional): looks for highs and lows in every n candles. if None it will use
        suggested candle range that evaluated with tests.
        mode (str, optional): how to treat with start and end of bound ("clip" or "wrap"). Defaults to "clip".
        high_col (str, optional): col to look for highs in. Defaults to "high".
        low_col (str, optional): col to look for lows in. Defaults to "low".
        min_time_dist (list, optional): min time distance between two similar pivots to get as a new pivot
            . Defaults to dt.timedelta(seconds = 24000).
        fill_between_two_same (bool, optional): if True finds a low between to immediate highs
            and finds a new max between two immediate lows. Defaults to True.
        remove_under_min_time_dist (bool, optional): min_time_dist will be ignored if this arg is False
        . Defaults to True.

    Returns:
        min_idx (list): indices of lows
        max_idx (list): indices of highs
    """        
    df_ = dataframe.copy()
    if datetime_col not in df_.columns: df_[datetime_col] = df_.index
    df_.reset_index(inplace = True, drop = True)
    if not candle_range: raise ValueError("'candle_range' can't be None")
    # evaluating min and max from argrelextrema function which finds high and lows
    max_idx = argrelextrema(data = np.array(df_[high_col].values.tolist()), 
                            comparator= np.greater, order = candle_range, mode = mode )[0]
    min_idx = argrelextrema(data = np.array(df_[low_col].values.tolist()), 
                            comparator= np.less, order = candle_range , mode = mode )[0]
    max_idx = max_idx.tolist()
    min_idx = min_idx.tolist()
    ### filtering and filling between high and lows with added functions       
    if remove_under_min_time_dist: max_idx, min_idx = remove_less_than_min_time(max_idx, min_idx, df_
                                                                                ,datetime_col,high_col,
                                                                                low_col, min_time_dist)
    if fill_between_two_same: max_idx, min_idx = fill_between_pivots(max_idx, min_idx, df_, high_col,low_col)
    if remove_under_min_time_dist: max_idx, min_idx = remove_less_than_min_time(max_idx, min_idx, df_
                                                                                ,datetime_col,high_col,
                                                                                low_col, min_time_dist)
    if fill_between_two_same: max_idx, min_idx = fill_between_pivots(max_idx, min_idx, df_, high_col,low_col)
    max_idx.sort()
    min_idx.sort()
    return max_idx, min_idx
    

           
