

import pandas as pd 
from pycoin.data_gathering.indicators import calc_MAs
from typing import List, Dict, Any
from ta.trend import MACD
import numpy as np
from .high_lows_evaluator import get_market_High_Lows
from pycoin.Utils import add_to_ColumnNames



def eval_trend_with_HighLows(df:pd.DataFrame,*, HighLow_col:str = "HighLow",
                date_col = "Date", highs_col:str = "Close", 
                lows_col:str = "Close", trend_col:str = "Trend", 
                uptrend_label:int = 1, lowtrend_label:int = -1, 
                sidetrend_label:int = 0, **kwargs):

    highlow_grp = df.groupby(HighLow_col)
    highs_suffix, lows_suffix = "_high", "_low"
    highDateCol, lowDateCol = date_col+highs_suffix, date_col+lows_suffix 
    highCol, lowCol = highs_col+highs_suffix, lows_col+lows_suffix
    # extracting high and low candles
    highs = add_to_ColumnNames(highlow_grp.get_group(1).reset_index()[[date_col, highs_col]], 
                            suffix=highs_suffix)
    lows = add_to_ColumnNames(highlow_grp.get_group(-1).reset_index()[[date_col, lows_col]], 
                            suffix=lows_suffix)
    # concating high and lows into pairs
    hl_pairs = pd.concat([highs, lows], axis=1)
    # checking conditions for uptrend and lowtrend
    isna = hl_pairs[[highCol, lowCol]].isna().any(axis=1)
    hh_hl_df = (hl_pairs > hl_pairs.shift())[[highCol, lowCol]]
    lh_ll_df = (hl_pairs < hl_pairs.shift())[[highCol, lowCol]]

    hh_hl = (hh_hl_df.all(axis=1))|(isna & hh_hl_df.any(axis=1))
    lh_ll = (lh_ll_df.all(axis=1))|(isna & lh_ll_df.any(axis=1))

    # getting end date of each trend
    endDates_uptrend = hl_pairs[hh_hl][[highDateCol,
                                        lowDateCol]].fillna(pd.Timestamp(0)).tz_localize(None).max(axis=1)
    endDates_lowtrend = hl_pairs[lh_ll][[highDateCol,
                                        lowDateCol]].fillna(pd.Timestamp(0)).tz_localize(None).max(axis=1)
    # initializing trend col
    if trend_col not in df.columns: df[trend_col] = sidetrend_label
    for i, row in hl_pairs.iterrows():
        current_Date = row[[highDateCol, lowDateCol]].fillna(pd.Timestamp(0)).tz_localize(None).max()
        if current_Date in endDates_uptrend.values:
            # finding begin date of trend
            begin_Dates = hl_pairs[[highDateCol, lowDateCol]].iloc[i-1].tz_localize(None)
            if begin_Dates.isna().any(): begin_Date = begin_Dates.fillna(pd.Timestamp(0)).max()
            else: begin_Date = begin_Dates.min()
            end_Date = current_Date
            df.loc[begin_Date: end_Date, trend_col] = uptrend_label
            
        elif current_Date in endDates_lowtrend.values:
            begin_Dates = hl_pairs[[highDateCol, lowDateCol]].iloc[i-1].tz_localize(None)
            if begin_Dates.isna().any(): begin_Date = begin_Dates.fillna(pd.Timestamp(0)).max()
            else: begin_Date = begin_Dates.min()
            end_Date = current_Date
            df.loc[begin_Date: end_Date, trend_col] = lowtrend_label
    return df



def eval_trend_with_MAs(dataframe:pd.DataFrame, column:str = "Close" ,
                        windows:List = [50,200], drop_MA_cols:bool = False,
                        up_trends_as = 1, down_trends_as = -1, side_trends_as = 0,
                        trend_col_name:str = "MA_trend"):
    """eval trend with moving averages (list of 2 window values (first lower second higher)
    must be inserted).
    if short term MA > long term MA -> uptrend
    elif short term MA < long term MA -> downtrend 
    

    Args:
        column (str, optional): _description_. Defaults to "Close".
        windows (List, optional): _description_. Defaults to [50,200].
        drop_MA_cols (bool, optional): drop calculated MA cols after calculation or not. Defaults to False.
        up_trends_as (int, optional): label of up_trend values. Defaults to 1.
        down_trends_as (int, optional): label of down_trend values. Defaults to -1.
        side_trends_as (int, optional): label of side_trend values. Defaults to 0.
        inplace(bool): add column to dataframe entered at constructor or not. Defaults to True.

    Returns:
        dataframe with a "MA_trend" column : _description_
    """        
    if len(windows) > 2 : raise Exception("len of windows must be 2")
    if windows[0] > windows[1]: raise Exception("short term MA window must entered first.")
    elif windows[0] == windows[1]: raise Exception("short and long term windows can't be equal!")
    
    df_ = dataframe.copy()
    df_.Name = dataframe.Name
    df_.index.name = ''
    if not "Datetime" in df_.columns: df_["Datetime"] = df_.index            
    df_with_MA = calc_MAs(df_, column = column, windows = windows)
    df_with_MA.Name = dataframe.Name
    
    up_trends = df_with_MA.query(f"MA{str(windows[0])} > MA{str(windows[1])}").copy()
    down_trends = df_with_MA.query(f"MA{str(windows[0])} < MA{str(windows[1])}").copy()
    
    up_trends[trend_col_name] = up_trends_as
    down_trends[trend_col_name] = down_trends_as
    
    trends = pd.concat([up_trends, down_trends], axis = 0, ignore_index = False, sort = True)
    labeled_df = pd.merge(df_, trends, how = "left", sort = True).fillna(side_trends_as)
    
    if drop_MA_cols: labeled_df.drop([f"MA{str(windows[0])}", f"MA{str(windows[1])}"], axis = 1, 
                                    inplace= True)
    
    overall_trend = labeled_df[trend_col_name].iloc[-1]
    labeled_df.Name = dataframe.Name
    labeled_df.set_index("Datetime", inplace = True)
    return labeled_df




def eval_trend_with_MACD(dataframe,* , column:str = "Close", window_slow:int = 26 , 
                            window_fast:int = 12, window_sign:int = 9 , fill_na:bool = False,
                            drop_MACD_col:bool = False, up_trends_as = 1,
                            down_trends_as = -1, side_trends_as = 0,
                            trend_col_name:str = 'MACD_trend'):
    
    df_ = dataframe.copy()
    df_.Name = dataframe.Name
    # calculating MACD
    macd = MACD(close = df_[column], window_slow = window_slow , window_fast = window_fast,
                window_sign = window_sign, fillna = fill_na,)
    
    df_['MACD'] = macd.macd()
    df_['signal_line'] = macd.macd_signal()
    df_['MACD_diff'] = df_['MACD'] - df_['signal_line']
    df_[trend_col_name] = np.where(df_['MACD_diff'] > 0, up_trends_as, 
                                    np.where(df_['MACD_diff'] < 0, down_trends_as, side_trends_as))
    
    if drop_MACD_col : df_.drop(['signal_line','MACD','MACD_diff'], axis = 1, inplace = True)
    overall_trend = df_[trend_col_name].iloc[-1]
    return df_



def eval_trend_with_ROC(dataframe,* , column:str = "Close" ,nperiods:int = 14, drop_ROC:bool = False, 
                        up_trends_as = 1, down_trends_as = -1, side_trends_as = 0, 
                        trend_col_name:str = 'ROC_trend'):
    
    df_ = dataframe.copy()
    df_.Name = dataframe.Name
    df_['ROC'] = ((df_[column] - df_[column].shift(nperiods)) / df_[column].shift(nperiods)) * 100
    # Fill missing values with 0
    df_['ROC'].fillna(0, inplace=True)
    # Determine the trend based on the ROC
    threshold = 0  # Threshold for trend determination
    df_[trend_col_name] = np.where(df_['ROC'] > threshold, up_trends_as, 
                        np.where(df_['ROC'] < -threshold, down_trends_as, side_trends_as))
    # Get the overall trend based on the last row
    overall_trend = df_[trend_col_name].iloc[-1]
    if drop_ROC : df_.drop("ROC", axis = 1 , inplace = True)
    return df_

    
    
    
    