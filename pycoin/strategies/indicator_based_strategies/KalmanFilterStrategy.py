from datetime import datetime
from pycoin import Utils
from .._strategy_BASE import _StrategyBASE
from pykalman import KalmanFilter
import pandas as pd
import numpy as np


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
        
    def filter(self, series):
        kf = KalmanFilter(initial_state_mean=series.iloc[0], **self.kalman_kwargs)
        state_means, state_covariances = kf.filter(series.values)
        self.filtered_data = pd.Series(state_means.flatten(), index=series.index)
        return self.filtered_data
    
    
      # main function to get filtered signal
    def generate_signal(self, dataframe:pd.DataFrame,
                        filter_column:str = "Close",
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
        df["Kalman"] = self.filter(df[filter_column])
        # finding high and lows of filtered data
        high_idx, low_idx = Utils.get_signal_HighsLows_ind(df["Kalman"].values, **kwargs )
        lows_df, highs_df = df.iloc[low_idx], df.iloc[high_idx]
        # defining 'Position_side' column
        df["Position_side"] = 0
        df.loc[highs_df.index, "Position_side"] = -1
        df.loc[lows_df.index, "Position_side"] = 1
        if kwargs.get("inplace", True): self.df = df
        return df
    
    
    
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

    
    
    def plot(self, **kwargs):
        fig = super().plot(**kwargs)
        fig.add_scatter(x = self.df.index, y = self.df["Kalman"],  
                        line_shape='spline', line={"color":kwargs.get("color", "black")},
                        name = "Kalman")
    
        for side, grp_df in self.df.groupby("Position_side"):
            if side == 0: continue
            for ind, row in grp_df.iterrows():
                self.plotter.draw_circle(fig, [ind, row["Kalman"]], 
                                        fillcolor = "blue" if side == 1 else "yellow", 
                                        R = kwargs.get('R', 100), 
                                        y_scale=kwargs.get("y_scale", 1))
        return fig
