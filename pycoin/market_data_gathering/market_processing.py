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
import time
import kucoin.client as kc


class Market_processing(get_market_plots):
    
    def __init__(self, symbol, interval:str = "4hour") -> None:
        ''' Args:
        interval (str, optional): Type of candlestick patterns: "1min", "3min", "5min", "15min", "30min",
        "1hour", "2hour", "4hour" , "6hour", "8hour", "12hour", "1day", "1week"
        symbol(str): market symbol in format of "BTC-USDT" '''
        
        self.symbol = symbol
        self.market = kc.Market(url = 'https://api.kucoin.com')
        
        if interval in ["1min", "3min", "5min", "15min", "30min","1hour", "2hour",
                    "4hour" , "6hour", "8hour", "12hour", "1day", "1week"]: 
            self.interval = interval
        else: raise ValueError("entered interval value not found !")
        
        self.df = None
        self.highs_df = None
        self.lows_df = None
        self.pivots = {"highs": {}, "lows": {}}
        
        
        
    def get_kline_as_df(self , reverse_df:bool = False, end_timestamp:int = None , 
                        verbose:bool = True, start_timestamp:int = dt.datetime(2017,1,1).timestamp().__int__() ) -> pd.DataFrame:
        """requests kucoin api and gathers kline (candlestick) data. returns output as pd.dataframe .

        Args:
            interval (str, optional): Type of candlestick patterns: "1min", "3min", "5min", "15min", "30min",
            "1hour", "2hour", "4hour" , "6hour", "8hour", "12hour", "1day", "1week".
            Defaults to "15min".
            reverse_df (bool, optional): reverse output dataframe or not. Defaults to False.
            end_timestamp (int, optional): final time data, if not specified gathers data till current time
            . Defaults to None.
            start_timestamp (int, optional): first time data, if not specified it will gather data until 
            first price data at kucoin.

        Returns:
            pd.DataFrame: output candlestick data
        """        
        # Exception for interval

            
        
        cols = ["timestamp",'open','close','high','low','volume','turnover']
        df_temp = pd.DataFrame(columns = cols)
        
        if end_timestamp == None:
            current_timestamp = int(self.market.get_server_timestamp()*1e-3) # current ts milisec to sec
            ts_temp_end = current_timestamp
        else: ts_temp_end = end_timestamp
        
        while 1 :
            try:
            # returns timestamp(newest date comes first), open, close, high, low, volume, turnover
                ts_temp_last = ts_temp_end # saves last timestamp
                candles_temp = self.market.get_kline(self.symbol, self.interval , startAt = start_timestamp, 
                                                     endAt = ts_temp_end ) # read kline data from kucoin api
                
                ts_temp_end = int(candles_temp[-1][0]) # get last timestamp of each bunch of data

                candle_df_temp = pd.DataFrame(candles_temp, columns = cols) # convert current data bunch to df
                df_temp = pd.concat( [df_temp,candle_df_temp], axis=0, ignore_index = True ) # updating final df
            
                if verbose:
                    print("\n\nfirst datetime is: ",
                        self.__ts2dt( int(df_temp.iloc[0].timestamp) ) ,
                        "\nlast datetime till now is: ",
                        self.__ts2dt( int(df_temp.iloc[-1].timestamp) )
                         ) 

            except :      
                 # check if we got the data of new timestamp else exits loop
                if ts_temp_end == ts_temp_last: break
                elif ts_temp_end != ts_temp_last: 
                    ts_temp_end = int(candles_temp[-1][0])
                    time.sleep(10)
                    continue
                
        df_temp["timestamp"] = df_temp.timestamp.astype("Int64")
        df_temp[df_temp.columns.to_list()[1:]] = df_temp[df_temp.columns.to_list()[1:]].astype("Float64") 
        df_temp["datetime"] = pd.to_datetime(df_temp["timestamp"],unit = 's')
        df_temp = df_temp[["timestamp","datetime",'open','close','high','low','volume','turnover']]
        
        # reverses dataframe if specified
        if reverse_df: df_temp = df_temp.reindex(index= df_temp.index[::-1]).reset_index(drop = True)
        self.df = df_temp 
        return df_temp
        


    def load_kline_data(self , file_name:str, reverse:bool = False) -> pd.DataFrame :
            """reads kline date in .csv or .xlsx format.

            Args:
                file_name (str): name of file in current dir
            return:
                output dataframe
            """        
            
            if "csv" in file_name: df = pd.read_csv(file_name)
            elif "xlsx" in file_name : df = pd.read_excel(file_name)
            else : "file format must be .csv or .xlsx"

            # converting format of data columns
            df["timestamp"] = df.timestamp.astype("Int64")
            df["datetime"] = pd.to_datetime( df["timestamp"], unit = 's')
            df = df[["timestamp","datetime",'open','close','high','low','volume','turnover']]
            df[ df.columns.to_list()[2:] ] = df[ df.columns.to_list()[2:] ].astype("Float64")
            
            if reverse: df = df.reindex(index= df.index[::-1])
            df.reset_index(drop = True, inplace = True)
            
            self.df = df
            return df
        
        
    def group_klines(self, df:pd.DataFrame, *grp_bys):
        """groups dataframe by ("year", "month", "day") tuple arg if specified.

        Args:
            df (pd.DataFrame): input df

        Returns:
            _type_: group object
            
        example:
            >>> self.group_klines(df , ("year" , "month" , "day")) --> groups df by year, month, day
        """      
        by = grp_bys[0]
          
        grps = []
        
        
        if "year" in by : grps.append(df["datetime"].dt.year) 
        if "month" in by : grps.append(df["datetime"].dt.month)
        if "day" in by : grps.append(df["datetime"].dt.day)
        
        if grps == []: 
            raise Exception("at least one date parameter(year or month or day must be specified)")
        
        return df.groupby(grps)
        
        
    def get_market_high_lows(self, candle_range:int = 100, mode:str = "clip", 
                             high_col:str = "high", low_col:str = "low", datetime_col:str = "datetime",
                             min_time_dist:list = dt.timedelta(seconds = 24000),fill_between_two_same:bool = True,
                             remove_under_min_time_dist:bool = True):
        """this function evaluates input market highs, lows. and returns their index. 

        Args:
            candle_range (int, optional): looks for highs and lows in every n candles. Defaults to 100.
            mode (str, optional): how to treat with start and end of bound. Defaults to "clip".
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
        
        df_ = self.df.copy()
                
        # evaluating min and max from argrelextrema function which finds high and lows
        max_idx = argrelextrema(data = np.array(df_[high_col].values.tolist()), 
                                comparator= np.greater, order = candle_range, mode = mode )[0]
        min_idx = argrelextrema(data = np.array(df_[low_col].values.tolist()), 
                                comparator= np.less, order = candle_range , mode = mode )[0]
        
        
        max_idx = max_idx.tolist()
        min_idx = min_idx.tolist()
                
        # a helper func that fills between two immediate pivots
        from .trend_filters import fill_between_pivots
                
        # a helper func that removes the pivot that very close in time index to next/previous pivot
        from .trend_filters import remove_less_than_min_time
                
        ### filtering and filling between high and lows with added functions       
        if remove_under_min_time_dist: max_idx, min_idx = remove_less_than_min_time(max_idx, min_idx, df_
                                                                                    ,datetime_col,high_col,
                                                                                    low_col, min_time_dist)
        
        if fill_between_two_same: max_idx, min_idx = fill_between_pivots(max_idx, min_idx, df_, high_col,
                                                                         low_col)
        
        if remove_under_min_time_dist: max_idx, min_idx = remove_less_than_min_time(max_idx, min_idx, df_
                                                                                    ,datetime_col,high_col,
                                                                                    low_col, min_time_dist)
        
        if fill_between_two_same: max_idx, min_idx = fill_between_pivots(max_idx, min_idx, df_, high_col,
                                                                         low_col)
        max_idx.sort()
        min_idx.sort()

        self.highs_df = df_.iloc[max_idx][["datetime", high_col]].drop_duplicates().values.tolist()
        self.lows_df = df_.iloc[min_idx][["datetime",low_col]].drop_duplicates().values.tolist()
        
        self.pivots["highs"]["idx"] = max_idx
        self.pivots["highs"]["column"] = high_col
        self.pivots["highs"]["df_val"] = self.highs_df
        
        self.pivots["lows"]["idx"] = min_idx
        self.pivots["lows"]["column"] = low_col
        self.pivots["lows"]["df_val"] = self.lows_df

        return max_idx , min_idx
    
    
    
    def eval_trend_with_high_lows(self, trend_col_name:str = "high_low_trend", inplace:bool = True,
                                  high_trend_label:int = 1, low_trend_label:int = -1, side_trend_label:int = 0):
        """evaluates trend with high and lows evaluated with remove_less_than_min_time method.

        Args:
            trend_col_name (str, optional): final name of trend col name generate by this method. 
                Defaults to "high_low_trend".
            inplace (bool, optional): add the trend col to self.df or not. Defaults to True.
            high_trend_label (int, optional): label of high trend classes. Defaults to 1.
            low_trend_label (int, optional): label of low trend classes. Defaults to -1.
            side_trend_label (int, optional): label of side trend classes. Defaults to 0.

        Returns:
            df_(pd.Dataframe): updated dataframe with evaluated trend labels.
        """        
        
        try:
            max_idx = self.pivots["highs"]["idx"]
            min_idx = self.pivots["lows"]["idx"]
            high_col = self.pivots["highs"]["column"]
            low_col = self.pivots["lows"]["column"]
        except:
            raise Exception("no high and lows calculated yet! first run obj.get_market_high_lows.")
        
        df_ = self.df.copy()
        df_[trend_col_name] = side_trend_label
        
        for max_ind, min_ind, i  in zip(max_idx, min_idx, range( max( len(max_idx), len(min_idx) ) ) ):

            if i > 0 :
                # compare for uptrend ( if we have higher highs and higher lows we have uptrend)
                is_hh = df_[high_col].iloc[max_ind] > df_[high_col].iloc[last_max_ind]
                is_hl = df_[low_col].iloc[min_ind] > df_[low_col].iloc[last_min_ind] 
                
                # compare for downtrend ( if we have lower highs and lower lows we have downtrend)
                is_lh = df_[high_col].iloc[max_ind] < df_[high_col].iloc[last_max_ind]
                is_ll = df_[low_col].iloc[min_ind] < df_[low_col].iloc[last_min_ind] 
                
                # assign high_trend_ labels to pivots that are hh and hl (same for downtrend)
                if is_hh and is_hl: 
                    df_.loc[ min(last_max_ind, last_min_ind): max(max_ind, min_ind), trend_col_name] = high_trend_label
                elif is_lh and is_ll: 
                    df_.loc[ min(last_max_ind, last_min_ind): max(max_ind, min_ind), trend_col_name] = low_trend_label
                
                # labeling the last pivot                
                if i == min( len(max_idx), len(min_idx) )-1 and len(max_idx) != len(min_idx):
                    
                    if len(min_idx) > len(max_idx) : 
                        if (df_[low_col].iloc[min_idx[-1]] < df_[low_col].iloc[min_ind] and
                            df_[low_col].iloc[min_idx[-1]] < df_[low_col].iloc[last_min_ind]) :
                            
                            df_.loc[min_ind: min_idx[-1], trend_col_name] = low_trend_label
                            
                    if len(max_idx) > len(min_idx):
                        if (df_[high_col].iloc[max_idx[-1]] > df_[high_col].iloc[max_ind] and
                            df_[high_col].iloc[max_idx[-1]] > df_[high_col].iloc[last_max_ind]):
                            
                            df_.loc[max_ind: max_idx[-1], trend_col_name] = high_trend_label
                          
            last_max_ind = max_ind
            last_min_ind = min_ind
            
        if inplace : self.df = df_
        return df_
            
        
    
    def plot_high_lows(self, fig:go.Figure, min_color:str = "red", max_color:str = "green" ,
                                R:int = 400, y_scale:float = 0.1):
        """adds circle shapes for highs and lows for visualizing.

        Args:
            fig (go.Figure): adds shapes to this fig
            min_color (str, optional): color of lows circle. Defaults to "red".
            max_color (str, optional): color of highs circle. Defaults to "green".
            R (int, optional): radius of circle. Defaults to 400.
            y_scale (float, optional): scales the y coord of circle(price) if needed. Defaults to 0.1.

        Raises:
            ValueError: _description_
        """        
        
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
                             up_trends_as = 1, down_trends_as = -1, side_trends_as = 0, inplace:bool = True,
                             trend_col_name:str = 'MACD_trend'):
        
        df_ = self.df.copy()
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
        
        if inplace: self.df = df_
        return df_, overall_trend
    
    
    
    def eval_trend_with_ROC(self, column:str = "close" ,nperiods:int = 14, drop_ROC:bool = False, 
                            up_trends_as = 1, down_trends_as = -1, side_trends_as = 0, 
                            trend_col_name:str = 'ROC_trend'):
        
        df_ = self.df.copy()
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
        self.df = df_
        return df_ , overall_trend
           
           
    
    def draw_trend_highlight(self, fig:go.Figure, column:str = "MA_trend", dataframe:pd.DataFrame = None
                   , up_trend_color:str = "blue", down_trend_color:str = "red"
                   , side_trend_color:str = "yellow"):
        """visualizes the evaluated trend with highlighted candles.

        Args:
            fig (go.Figure): add trend plot to this fig.
            column (str, optional): name of the trend col you want to plot. Defaults to "MA_trend".
            dataframe (pd.DataFrame, optional): you can give a new df else it will use self.df.
            Defaults to None.
            up_trend_color (str, optional): color of up_trend candles. Defaults to "blue".
            down_trend_color (str, optional): color of down_trend candles. Defaults to "red".
            side_trend_color (str, optional): color of side_trend candles. Defaults to "yellow".
        """        
        
        try: df_ = dataframe.copy()
        except: df_ = self.df.copy()
            
        trend_grps = df_.copy().groupby(column, sort = True)
        
        colors = [down_trend_color , side_trend_color , up_trend_color]
        trend_names = list(trend_grps.groups.keys())
        colors_dict = {key:color for key,color in zip(trend_names,colors)}
          
        for name,grp in trend_grps :
            for i,row in grp.iterrows():
                super().highlight_single_candle(fig, row["datetime"], color = colors_dict[name] )
                
        if fig.layout.title.text != None: fig.update_layout(title = fig.layout.title.text +" , "+
                                                            f"trend evaluated with : {column}" )
        
        else : fig.update_layout(title = f"trend evaluated with : {column}" )
        
    
        

             
    