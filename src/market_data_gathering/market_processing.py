import pandas as pd
from ..market_data_kline_plots.market_plotter import get_market_plots
import plotly.graph_objects as go
import sys
sys.setrecursionlimit(10000)
import numpy as np
import datetime as dt
from typing import List
from ta.trend import MACD
from scipy.signal import argrelextrema


class market_processing(get_market_plots):
    
    def __init__(self, dataframe:pd.DataFrame) -> None:
        self.df = dataframe
        self.maxs_series = None
        self.mins_series = None
        
        
    def get_market_high_lows(self, candle_range:int = 100, mode:str = "clip", 
                             high_col:str = "high", low_col:str = "low", 
                             min_dist:list = [dt.timedelta(seconds = 24000), 0.3]  ):
        
        # evaluating min and max from argrelextrema function which finds high and lows
        max_idx = argrelextrema(data = np.array(self.df[high_col].values.tolist()), 
                                comparator= np.greater, order = candle_range, mode = mode )[0]
        min_idx = argrelextrema(data = np.array(self.df[low_col].values.tolist()), 
                                comparator= np.less, order = candle_range , mode = mode )[0]
        
        
        df_ = self.df.copy()
        print(min_dist)

                
        def fill_between_pivots( max_idx:np.ndarray, min_idx:np.ndarray , df_:pd.DataFrame ):
            # adding max between two immediate lows
            for max in max_idx: 
                ind_max = np.where( max == max_idx )[0][0]
                if ind_max > len(min_idx)-1: break
                if min_idx[ind_max] == min_idx[-1]: break
                if max == max_idx[-1]: break
                
                if not max in np.arange( min_idx[ind_max] , min_idx[ind_max+1] ):
                    new_max = df_[df_.iloc[ min_idx[ind_max]:min_idx[ind_max + 1] ][high_col].max() == df_[high_col]].index[0]
                    if new_max == max_idx[-1]: break
                    if new_max == max or new_max == max_idx[ind_max+1] or new_max == max_idx[ind_max-1] : continue
                    max_idx = np.append( max_idx , new_max )
                    max_idx.sort()
            
            # adding min between two immediate highs
            for min in min_idx:
                ind_min = np.where( min == min_idx )[0][0]
                
                if ind_min > len(max_idx)-1: break
                elif min == min_idx[-1] : break
                elif max_idx[ind_min] == max_idx[-1]: break
                
                if not min in np.arange( max_idx[ind_min] , max_idx[ind_min+1] ):
                    new_min = df_[df_.iloc[ max_idx[ind_min]:max_idx[ind_min + 1] ][low_col].min() == df_[low_col]].index[0]
                    if new_min == min_idx[-1]: break
                    if new_min == min or new_min == min_idx[ind_min+1] or new_min == min_idx[ind_min-1] : continue
                    min_idx = np.append( min_idx , new_min )
                    min_idx.sort()
                    
            return max_idx, min_idx
                
        def remove_less_than_min_y(max_idx:np.ndarray|list, min_idx: np.ndarray|list, df_:pd.DataFrame, 
                                   min_y:float = min_dist[1], high_col:str = high_col, low_col:str = low_col):
            
            highs_df = df_.iloc[max_idx][["datetime", high_col]]
            lows_df = df_.iloc[min_idx][["datetime", low_col]]
            
            # finding rows below min change
            less_than_min_y_max = highs_df[ ( highs_df[high_col].diff(1).abs()/ pd.concat([ highs_df[high_col], 
                                      highs_df[high_col].shift(1) ], axis = 1 ).max(axis = 1) ) < min_y ]
            
            # finding the maxs below min y change
            ind_remove_maxs = pd.concat( [df_.iloc[less_than_min_y_max.index][high_col].reset_index(drop=True),
                                          df_.iloc[less_than_min_y_max.index-1][high_col].reset_index(drop=True),
                                          df_.iloc[less_than_min_y_max.index+1][high_col].reset_index(drop=True)],
                                          axis=1 ).min(axis=1)
            
            to_remove_maxs = [ df_[df_[high_col] == max_].index[0]+1 for i,max_ in ind_remove_maxs.items() ]
            
            ####### doing the same for minimum
            less_than_min_y_min = lows_df[ ( lows_df[low_col].diff(1).abs()/ pd.concat([ lows_df[low_col], 
                                    lows_df[low_col].shift(1) ], axis = 1 ).max(axis = 1) ) < min_y]
            
            # getting the max with higher value
            ind_remove_mins = pd.concat([df_.iloc[ less_than_min_y_min.index ][low_col].reset_index(drop = True) ,
                                        df_.iloc[ less_than_min_y_min.index-1 ][low_col].reset_index(drop=True) ,
                                        df_.iloc[ less_than_min_y_min.index+1 ][low_col].reset_index(drop=True)],
                                        axis = 1).max(axis = 1) 
            
            # remove candids
            to_remove_mins = [ df_[df_[low_col] == min_].index[0]+1 for i,min_ in ind_remove_mins.items() ]
    
            return to_remove_maxs, to_remove_mins
        
        
        def remove_less_than_min_time(max_idx, min_idx, df_:pd.DataFrame, datetime_col:str = "datetime", 
                                      min_delta_t:dt.timedelta = min_dist[0] ):
            
            highs_df = df_.iloc[max_idx][datetime_col]
            lows_df = df_.iloc[min_idx][datetime_col]
            
            less_than_delta_ts_max = highs_df[highs_df.diff(1).abs() < min_delta_t]
            remove_candids_max = less_than_delta_ts_max.index.to_list()+(less_than_delta_ts_max.index-1).to_list()
        
            less_than_delta_ts_min = lows_df[lows_df.diff(1).abs() < min_delta_t]
            remove_candids_min = less_than_delta_ts_min.index.to_list()+(less_than_delta_ts_min.index-1).to_list()

            return remove_candids_max, remove_candids_min
        
        
        remove_y_max, remove_y_min = remove_less_than_min_y(max_idx, min_idx, df_)
        remove_t_max, remove_t_min = remove_less_than_min_time(max_idx, min_idx, df_)
        
        final_candids_max = [ rym for rym in remove_y_max if rym in remove_t_max]
        final_candids_min = [ rym for rym in remove_y_min if rym in remove_t_min]
        
        max_idx_ = max_idx.tolist().copy()
        min_idx_ = min_idx.tolist().copy()
        
        for ind in final_candids_max: max_idx_.remove(ind)
        for ind in final_candids_min: min_idx_.remove(ind)
        
        max_idx_ = np.array(max_idx_).copy()
        min_idx_ = np.array(min_idx_).copy()
        
        max_idx_, min_idx_ = fill_between_pivots(max_idx_, min_idx_, df_) 
        
        
        self.highs_df = df_.iloc[max_idx_][["datetime", high_col]].values.tolist()
        self.lows_df = df_.iloc[min_idx_][["datetime",low_col]].values.tolist()

        return max_idx_, min_idx_

    
    
    
    
    def plot_high_lows(self, fig:go.Figure, min_color:str = "red", max_color:str = "green" ,
                                R:int = 400, y_scale:float = 0.1):
        
        if self.highs_df == None or self.lows_df == None : 
            raise ValueError("""you didn't calculate highs and lows yet!
                                do this by running obj.get_market_high_lows method.""")
        
        for low_coord in self.lows_df:
            super().draw_circle(fig = fig, center = low_coord, R = R , fillcolor = min_color , y_scale = y_scale )
            
        for high_coord in self.highs_df:
            super().draw_circle(fig = fig, center = high_coord, R = R , fillcolor = max_color , y_scale = y_scale )
   
        
    @property
    def tick(self):
        """get market current value

        Returns:
            Dict: dictionary of values
        """        
        tick = self.market.get_ticker(symbol = self.symbol )
        tick["datetime"] = dt.datetime.fromtimestamp( tick["time"]*1e-3 )
        return tick
   
   
    def calc_MAs(self, column:str = "close", windows:List = [50,200] ):
        """calculate moving average with list of desired windows

        Args:
            column (str, optional): calculate on which column. Defaults to "close".
            windows (List, optional): list of windows. Defaults to [50,200].

        Returns:
            _type_: _description_
        """        
        
        df_temp = self.df.copy()
        
        for window in windows:
            df_temp[f"MA{str(window)}"] =  df_temp[column].rolling(window).mean()
        return df_temp
    
    
    def eval_trend_with_MAs(self,column:str = "close" ,windows:List = [50,200], drop_MA_cols:bool = False,
                            up_trends_as = 1, down_trends_as = -1, side_trends_as = 0, inplace:bool = True):
        """eval trend with moving averages (list of 2 window values (first lower second higher)must be inserted)
        

        Args:
            column (str, optional): _description_. Defaults to "close".
            windows (List, optional): _description_. Defaults to [50,200].
            drop_MA_cols (bool, optional): drop calculated MA cols after calculation or not. Defaults to False.
            up_trends_as (int, optional): label of uptrend values. Defaults to 1.
            down_trends_as (int, optional): label of down trend values. Defaults to -1.
            side_trends_as (int, optional): label of side trend values. Defaults to 0.
            inplace(bool): add column to dataframe entered at constructor or not. Defaults to True.

        Returns:
            dataframe with a "MA_trend" column : _description_
        """        
        
        if len(windows) > 2 : raise Exception("len of windows must be 2")
        df_with_MA = self.calc_MAs(column = column, windows = windows)
        
        up_trends = df_with_MA.query(f"MA{str(windows[0])} > MA{str(windows[1])}").copy()
        down_trends = df_with_MA.query(f"MA{str(windows[0])} < MA{str(windows[1])}").copy()
        
        up_trends["MA_trend"] = up_trends_as
        down_trends["MA_trend"] = down_trends_as
        
        trends = pd.concat([up_trends, down_trends], axis = 0, ignore_index = False, sort = True)
        labeled_df = pd.merge(self.df, trends, how = "left", sort = True).fillna(side_trends_as)
        
        if drop_MA_cols: labeled_df.drop([f"MA{str(windows[0])}", f"MA{str(windows[1])}"], axis = 1, 
                                     inplace= True)
        
        overall_trend = labeled_df["MA_trend"].iloc[-1]
        
        if inplace: self.df = labeled_df
        return labeled_df, overall_trend
    
    
    
    
    def eval_trend_with_MACD(self, column:str = "close", window_slow:int = 26 , window_fast:int = 12, 
                             window_sign:int = 9 , fill_na:bool = True, drop_MACD_col:bool = False,
                             up_trends_as = 1, down_trends_as = -1, side_trends_as = 0, inplace:bool = True):
        
        df_ = self.df.copy()
        # calculating MACD
        macd = MACD(close = df_[column], window_slow = window_slow , window_fast = window_fast,
                    window_sign = window_sign, fillna = fill_na,)
        
        df_['MACD'] = macd.macd()
        df_['signal_line'] = macd.macd_signal()
        df_['MACD_diff'] = df_['MACD'] - df_['signal_line']
        df_['MACD_trend'] = np.where(df_['MACD_diff'] > 0, up_trends_as, 
                                     np.where(df_['MACD_diff'] < 0, down_trends_as, side_trends_as))
        
        if drop_MACD_col : df_.drop(['signal_line','MACD','MACD_diff'], axis = 1, inplace = True)
        
        overall_trend = df_["MACD_trend"].iloc[-1]
        
        if inplace: self.df = df_
        return df_, overall_trend
    
    
    
    def eval_trend_with_ROC(self, column:str = "close" ,nperiods:int = 14, drop_ROC:bool = False, 
                            up_trends_as = 1, down_trends_as = -1, side_trends_as = 0):
        
        df_ = self.df.copy()
        df_['ROC'] = ((df_[column] - df_[column].shift(nperiods)) / df_[column].shift(nperiods)) * 100

        # Fill missing values with 0
        df_['ROC'].fillna(0, inplace=True)

        # Determine the trend based on the ROC
        threshold = 0  # Threshold for trend determination
        df_['ROC_trend'] = np.where(df_['ROC'] > threshold, up_trends_as, 
                                    np.where(df_['ROC'] < -threshold, down_trends_as, side_trends_as))

        # Get the overall trend based on the last row
        overall_trend = df_['ROC_trend'].iloc[-1]
        
        if drop_ROC : df_.drop("ROC", axis = 1 , inplace = True)
        self.df = df_
        return df_ , overall_trend
           
           
    
    def draw_trend_highlight(self, fig:go.Figure, column:str = "MA_trend", dataframe:pd.DataFrame = None
                   , up_trend_color:str = "blue", down_trend_color:str = "red"
                   , side_trend_color:str = "yellow"):
        
        try: df_ = dataframe.copy()
        except: df_ = self.df.copy()
            
        trend_grps = df_.copy().groupby(column, sort = True)
        
        colors = [down_trend_color , side_trend_color , up_trend_color]
        trend_names = list(trend_grps.groups.keys())
        colors_dict = {key:color for key,color in zip(trend_names,colors)}
          
        for name,grp in trend_grps :
            for i,row in grp.iterrows():
                super().highlight_single_candle(fig, row["datetime"], color = colors_dict[name] )
        
    
        

             
    