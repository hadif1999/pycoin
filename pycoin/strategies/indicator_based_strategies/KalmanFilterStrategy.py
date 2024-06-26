from datetime import datetime
from pycoin import Utils
from .._strategy_BASE import _StrategyBASE
from pykalman import KalmanFilter
import pandas as pd
import numpy as np
import ta
from pycoin.data_gathering.trend_filters import remove_less_than_min_time, fill_between_same_exterma
from pycoin.data_gathering.trend_evaluator import eval_trend_with_HighLows



class Kalmanfilter(_StrategyBASE):
    def __init__(self, symbol: str|None = None, timeframe: str|None = None, 
                 data_exchange: str = "binance", 
                 start_time: datetime | None | int = None,
                 dataName_format: str = "{symbol}|{exchange}|{timeframe}",
                 observation_covariance=0.05, transition_covariance=0.01, **kwargs) -> None:
        """
        :param observation_covariance: 
    :param transition_covariance: 

        Args:
            symbol (str | None, optional): Defaults to None.
            timeframe (str | None, optional): Defaults to None.
            data_exchange (str, optional): Defaults to "binance".
            start_time (datetime | None | int, optional): Defaults to None.
            dataName_format (str, optional): df name format. Defaults to "{symbol}|{exchange}|{timeframe}".
            observation_covariance (float, optional): Variance of the observations (larger values allow for more noise). Defaults to 0.05.
            transition_covariance (float, optional): Variance of the state transitions (smaller values make the filter smoother). Defaults to 0.01.
        """        
        
        super().__init__(symbol, timeframe, data_exchange, start_time, dataName_format, **kwargs)
        self.kalman_kwargs = {"n_dim_obs":1, "n_dim_state":1,
                              "observation_covariance":observation_covariance,
                              "transition_covariance":transition_covariance}
        
        
    def filter(self, series, MA_filter:int|None = None, **kwargs):
        kf = KalmanFilter(initial_state_mean=series.iloc[0], **self.kalman_kwargs)
        state_means, state_covariances = kf.filter(series.values)
        self.filtered_data = pd.Series(state_means.flatten(), index=series.index)
        if MA_filter:
            self.filtered_data = self.filtered_data.rolling(MA_filter, center = False).mean()
        return self.filtered_data
    
    
      # main function to get filtered signal
    def generate_signal(self, dataframe:pd.DataFrame,
                        filter_column:str = "Close",
                        fill_between_same_extermas:bool = True,
                        date_col:str = "Date",
                        last_nHighLows_filter:dict = {"enabled":True,
                                                      "n":3, 
                                                      "min_ncandles_between":5,
                                                      "min_price_dist_pct":0.01},
                        **kwargs):
        """generates 'LONG', 'SHORT' signal by finding high and lows and place buy orders
        at lows and and sell orders at highs. 
        adds "Position_side" column which is the main column defines position side
        it can be 1 that means 'LONG' or -1 means 'SHORT' and 0 means do nothing.

        Args:
            dataframe (pd.DataFrame)
            filter_column (str, optional)
            dist_pct (float, optional): distance from column price to find price range. Defaults to 0.01.
            signal_range_column(str): column which runs generate_signal_range func on it.
        Returns:
            pd.Dataframe
        """        
        df = dataframe.copy()
        df.Name = getattr(dataframe, "Name", "")
        # filter given data by Kalman filter
        df["Kalman"] = self.filter(df[filter_column], **kwargs)
        
        # finding high and lows of filtered data
        high_idx, low_idx = Utils.get_signal_HighsLows_ind(df["Kalman"].values, **kwargs)
        lows_df, highs_df = df.iloc[low_idx], df.iloc[high_idx]
        if "HighLow" not in df.columns: df["HighLow"] = 0  
        df.loc[highs_df.index, "HighLow"] = 1
        df.loc[lows_df.index, "HighLow"] = -1
        # filtering last n highlows if by price change and candles count
        if last_nHighLows_filter.get("enabled", True):
            df = self.filter_last_nHighLows(df, last_nHighLows_filter.get('n', 3), 
             last_nHighLows_filter.get("min_ncandles_between", 2),
             last_nHighLows_filter.get("min_price_dist_pct", 0.01),
             filter_column, date_col, "HighLow")
        # filling between to immediate same extermas        
        if fill_between_same_extermas: df = fill_between_same_exterma(df, "HighLow",
                                            low_column="Kalman", high_column="Kalman", 
                                            date_col=date_col)
        # defining 'Position_side' column to define entries and exits
        if "Position_side" not in df.columns: df["Position_side"] = 0
        df.loc[df["HighLow"] == -1, "Position_side"] = 1
        df.loc[df["HighLow"] == 1, "Position_side"] = -1
        if kwargs.get("inplace", True): self.df = df
        return df
    
        
    def filter_last_nHighLows(self, df:pd.DataFrame, n:int = 3,
                            min_candle_dist:int = 25, min_price_dist_pct = 0.05, 
                            price_dist_col:str = "Close", date_col = "Date", 
                            exterma_col:str = "HighLow"):
        df_ = df.copy()
        to_check_df = df_[df_[exterma_col] != 0].iloc[-n:]
        for i, (dt, row) in enumerate(to_check_df.iterrows()):
            if i == len(to_check_df)-1: break
            next_row = to_check_df.iloc[i+1]
            diff_pct = abs(row[price_dist_col]-next_row[price_dist_col])/min(row[price_dist_col], 
                                                                        next_row[price_dist_col])
            between_candles_df = df_.loc[row[date_col]: next_row[date_col]]
            if (diff_pct <= min_price_dist_pct) or (len(between_candles_df) < min_candle_dist):
                df_.loc[next_row[date_col], exterma_col] = 0
        return df_
    
    
    
    def generate_signal_range(self, dataframe: pd.DataFrame, 
                              column:str = "Kalman", dist_pct: float = 0.01, 
                              n_next_candles:int = 2, **kwargs):
        """this method extends found signals to their next candles if they are
        between the main signal 'lower_limit' and 'upper_limit' columns.
        it means it may also turn signals in 'Position_side' column after init signal 
        if they satisfy specific condition. 
        it helps to not lose signals of previous candles.

        Args:
            dataframe (pd.DataFrame)
            column (str, optional): checks conds on this column. Defaults to "Kalman".
            dist_pct (float, optional): upper_limit and lower_limit distance from 'column' values 
            in pct. Defaults to 0.01.
            n_next_candles (int, optional): num of candles after init signal to check. Defaults to 2.

        Returns:
            pd.DataFrame
        """
        upper_limit = np.where(dataframe["Position_side"] != 0, 
                               dataframe[column]+dist_pct*dataframe[column], 0)
        
        lower_limit = np.where(dataframe["Position_side"]!=0,
                               dataframe[column]-dist_pct*dataframe[column], 0)
        
        dataframe["upper_limit"], dataframe["lower_limit"] = upper_limit, lower_limit
        
        for i in range(n_next_candles):
            df_next_candle = pd.concat([ dataframe[column], 
            dataframe.shift(i+1)[["upper_limit", "lower_limit",
                                    "Position_side"]]], axis=1)
            # if these two conditions satisfied next candle will have same position signal
            upper_cond = df_next_candle[column]<=df_next_candle["upper_limit"]
            lower_cond = df_next_candle[column]>=df_next_candle["lower_limit"]
            
            dataframe.loc[upper_cond & lower_cond,
                          "Position_side"] = df_next_candle["Position_side"]
            
        if kwargs.get("inplace", True): self.df = dataframe 
        return dataframe
    
    
    def evaluate_trend(self, dataframe: pd.DataFrame, HighLow_col:str = "HighLow", **kwargs):
        self.df = eval_trend_with_HighLows(dataframe, HighLow_col = HighLow_col, **kwargs)
        return self.df
    
    
    def last_trend(self, dataframe: pd.DataFrame,
                   max_dist:int = 40, trend_column:str = "Trend"):
        nonside_trend = dataframe[dataframe[trend_column] != 0][trend_column]
        if nonside_trend.empty: return dataframe[trend_column].iloc[-1]
        last_trend = nonside_trend.iloc[-1]
        lastTrend_dist = len(dataframe.loc[nonside_trend.index[-1]: ])
        return last_trend if lastTrend_dist <= max_dist else dataframe[trend_column].iloc[-1]
        
    
    
    def add_adx_filter(self, dataframe: pd.DataFrame, remove_below:int = 25, window:int = 14,
                       high_col:str = "High", low_col:str = "Low", close_col:str = "Close"):
        """removes positions with low adx value.

        Args:
            window (int, optional): adx window size. Defaults to 14.
        """        
        dataframe["ADX"] = ta.trend.ADXIndicator(high=dataframe[high_col], 
                            low=dataframe[low_col], close=dataframe[close_col], 
                            window=window, fillna=False).adx()
        
        dataframe.loc[dataframe["ADX"] < remove_below, "Position_side"] = 0
        return dataframe 

    
    def plot(self, **kwargs):
        
        self.df.Name = self.dataName
        fig = super().plot(plot_entries=False ,**kwargs)
        
        fig.add_scatter(x = self.df.index, y = self.df["Kalman"],  
        line_shape='spline', line={"color":kwargs.get("color", "black")},
        name = "Kalman")
        
        self.plotter.plot_HighLows("Position_side", "Kalman",
                                   highs_shape="triangle-up", lows_shape="triangle-down",
                                   high_name="enter_long", low_name="enter_short",
                                   **kwargs
                                   )        
        return fig
    
    
    def plot_trend(self, trend_col:str = "Trend", size = 5,**kwargs):
        self.df.Name = self.dataName
        self.plot(size = size+10, **kwargs)
        return self.plotter.plot_trend(column=trend_col, size=size, **kwargs)    
    
    
    def run_real_backtest(self, dataframe: pd.DataFrame, filter_column:str = "Close", **kwargs):
        
        for i in range(len(dataframe)):
            if i <= 5: continue
            df_temp = dataframe.iloc[:i]
            self.df = self.generate_signal(df_temp, filter_column, **kwargs)
            self.plotter.fig = super().plot(new_plot = False, plot_entries = True, **kwargs)
            
        return dataframe
            
            
        
