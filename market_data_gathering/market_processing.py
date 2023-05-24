import pandas as pd
from market_data_kline_plots.market_plotter import get_market_plots
import plotly.graph_objects as go
import sys
sys.setrecursionlimit(10000)
import numpy as np
import datetime as dt
from typing import List
from ta.trend import MACD


class market_processing(get_market_plots):
    
    def __init__(self, dataframe:pd.DataFrame) -> None:
        self.df = dataframe
        
        
    def get_market_min_max(self, candle_range:int = 10, min_change:float = 0.001):
        
        dataframe = self.df.copy()
        
        index = 0
        min_pivots = []
        max_pivots = []
        
        while index < len(dataframe)-1:
            
            df_temp = dataframe.iloc[ index : index+candle_range ]

            min_temp = df_temp[ df_temp["low"] == df_temp["low"].min() ][["datetime","low"]].values.tolist()[0]
            max_temp = df_temp[ df_temp["high"] == df_temp["high"].max() ][["datetime","high"]].values.tolist()[0]
            
            
            if index > 0 :
                if np.abs((max_temp[1]-max_pivots[-1][1]))/max(max_pivots[-1][1], max_temp[-1]) > min_change :
                    max_pivots.append ( max_temp )
                
                if  np.abs((min_temp[1]-min_pivots[-1][1]))/max(min_pivots[-1][1], min_temp[-1]) > min_change:
                    min_pivots.append( min_temp )
            
            else:
                max_pivots.append ( max_temp )
                min_pivots.append( min_temp )
                
                
            index = df_temp.index[-1]
        
        return min_pivots, max_pivots
    
    
    
    def plot_all_min_max(self, fig:go.Figure, candle_range:int = 10, min_color:str = "red", 
                         max_color:str = "green" , R:int = 500, min_change = 0.001, y_scale:float = 0.1):
        
        
        min_pivots , max_pivots = self.get_market_min_max(candle_range = candle_range, min_change = min_change )

        for min in min_pivots:
            super().draw_circle(fig = fig, center = min, R = R , fillcolor = min_color , y_scale = y_scale )
            
        for max in max_pivots:
            super().draw_circle(fig = fig, center = max, R = R , fillcolor = max_color , y_scale = y_scale )
   
        
    @property
    def tick(self):
        tick = self.market.get_ticker(symbol = self.symbol )
        tick["datetime"] = dt.datetime.fromtimestamp( tick["time"]*1e-3 )
        return tick
   
   
    def calc_MAs(self, column:str = "close", windows:List = [50,200] ):
        
        df_temp = self.df.copy()
        
        for window in windows:
            df_temp[f"MA{str(window)}"] =  df_temp[column].rolling(window).mean()
        return df_temp
    
    
    def eval_trend_with_MAs(self,column:str = "close" ,windows:List = [50,200], drop_MAs:bool = False,
                            up_trends_as = 1, down_trends_as = -1, side_trends_as = 0):
        
        if len(windows) > 2 : raise Exception("len of windows must be 2")
        df_with_MA = self.calc_MAs(column = column, windows = windows)
        
        up_trends = df_with_MA.query(f"MA{str(windows[0])} > MA{str(windows[1])}").copy()
        down_trends = df_with_MA.query(f"MA{str(windows[0])} < MA{str(windows[1])}").copy()
        
        up_trends["MA_trend"] = up_trends_as
        down_trends["MA_trend"] = down_trends_as
        
        trends = pd.concat([up_trends, down_trends], axis = 0, ignore_index = False, sort = True)
        labeled_df = pd.merge(self.df, trends, how = "left", sort = True).fillna(side_trends_as)
        
        if drop_MAs: labeled_df.drop([f"MA{str(windows[0])}", f"MA{str(windows[1])}"], axis = 1, 
                                     inplace= True)
        
        self.df = labeled_df
        return labeled_df
    
    
    
    
    def eval_trend_with_MACD(self, column:str = "close", window_slow:int = 26 , window_fast:int = 12, 
                             window_sign:int = 9 , fill_na:bool = True, drop_MACD:bool = False):
        
        df_ = self.df.copy()
        macd = MACD(close = df_[column], window_slow = window_slow , window_fast = window_fast,
                    window_sign = window_sign, fillna = fill_na,)
        
        df_['MACD'] = macd.macd()
        df_['signal_line'] = macd.macd_signal()
        df_['MACD_diff'] = df_['MACD'] - df_['signal_line']
        df_['MACD_trend'] = np.where(df_['MACD_diff'] > 0, 1, np.where(df_['MACD_diff'] < 0, -1, 0))
        
        if drop_MACD : df_.drop(['signal_line','MACD','MACD_diff'], axis = 1, inplace = True)
        self.df = df_
        return df_
        
           
           
    
    def draw_trend(self, fig:go.Figure, column:str = "MA_trend", dataframe:pd.DataFrame = None
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
        
    
        

             
    