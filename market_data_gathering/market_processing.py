import pandas as pd
from market_data_kline_plots.market_plotter import get_market_plots
import plotly.graph_objects as go
import sys
sys.setrecursionlimit(10000)
import numpy as np



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
   
   
    
    def highlight_candle_range()

             
    