from typing import Any
import pandas as pd
import datetime as dt
from pycoin.data_gathering import get_market_High_Lows
from pycoin.strategies import dataTypes, _StrategyBASE


class _Levels( _StrategyBASE):
    """this class is a parent for level based strategies, which calculates all market important levels
    """    
    def __init__(self, **kwargs) -> None:
        """this class is a parent for level based strategies, which calculates all market important levels

        Args:
            symbol (str): desired symbol.
            interval (str): interval 
            platform (str, optional): platform to gather data from. Defaults to "bingx".
            start_time (int | dt.datetime, optional): start_time for calculating levels. Defaults to None.
        """        
        
        super().__init__(**kwargs)

        self.fracts = None
        self.fig = None
        
        self.Pivots = {"weekly":{}, "monthly":{}}
        self.LastPivots = {"weekly":{}, "monthly":{}}
        
        
    def __getattr__(self, __name: str) -> Any:
        super().__getattr__(name = __name)
        
            
    @property
    def update_pivots(self):
        weekly_pivots_df = self.KlineData_gatherer(symbol = self.symbol,
                                                   data_exchange=self.data_exchange,
                                                   timeframe = "1w", since = dt.datetime(2017,1,1),
                                                   limit=self.limit or 1000)
        
        monthly_pivots_df = self.KlineData_gatherer(symbol = self.symbol, 
                                                    data_exchange=self.data_exchange,
                                                    timeframe = "1M",
                                                    since = dt.datetime(2017,1,1),
                                                    limit=self.limit or 1000)
            
        weekly_pivots = self._eval_pivots(weekly_pivots_df)
        monthly_pivots = self._eval_pivots(monthly_pivots_df)
        
        weekly_pivots = self._get_numeric_cols(weekly_pivots)
        monthly_pivots = self._get_numeric_cols(monthly_pivots)
        
        self.Pivots["weekly"] = weekly_pivots
        self.Pivots["monthly"] = monthly_pivots
        
        self.LastPivots["weekly"] = weekly_pivots.iloc[-1].to_dict()
        self.LastPivots["monthly"] = monthly_pivots.iloc[-1].to_dict()
        
        
        return self
        
        
            
    @staticmethod
    def _eval_pivots(df:pd.DataFrame):
        """evaluates pivot levels for given dataframe.

        Args:
            df (pd.DataFrame): input dataframe. recommended to be the weekly or monthly dataframe
            to calculate weekly or monthly pivots.

        Returns:
            pd.dataframe: pivot levels for each row of input dataframe (candlesticks)
        """        
        df_ = df.copy()
        df_["mean"] = df_[["High", "Low"]].mean(axis = 1)
        df_["75%"] = df_[["High", "mean"]].mean(axis = 1)
        df_["25%"] = df_[["mean", "Low"]].mean(axis = 1)
        return df_[["Low","25%","mean","75%","High"]]


    def _eval_range_of_high_lows(self, candle_ranges:range = range(100,200,20)):
        """evaluates market high and lows but for a range of candles. it gathers high and lows for
        each candle range and returns their price in a list.

        Args:
            candle_ranges (range, optional): range of candles to evaluate high and lows.
            Defaults to range(100,200,20).

        Returns:
            list: list of prices of evaluated high and lows.
        """        
        
        all_high_lows = []
        
        for range in candle_ranges:
            
            maxs, mins = get_market_High_Lows(self.df,
                                              candle_range = range)
            all_mins = self.df.iloc[mins]["Low"].values.reshape(-1,1)[:,0].tolist()
            all_maxs = self.df.iloc[maxs]["High"].values.reshape(-1,1)[:,0].tolist()
            all_high_lows = all_high_lows + all_mins + all_maxs 
        list(set(all_high_lows))
        all_high_lows.sort()
        return all_high_lows
    
    
    def _get_numeric_cols(self, df):
        numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
        return df.select_dtypes(include=numerics)
    
    
    def _eval_fract_levels_by_past_pivots(self, candle_ranges:range = range(100,200,20),
                                         tolerance_percent:float = 0.01,
                                         min_occurred:int = 2):
        """checks if past weekly and monthly pivots are fract levels too.
        does this by checking if they have enough touch to high and lows.

        Args:
            candle_ranges (range, optional): candle range in range format. Defaults to range(100,200,20).
            tolerance_percent (float, optional): this specifies how accurate can touches be.
            if it is a lower value we have more accurate touches.Defaults to 0.01.
            min_occurred (int, optional): min touches to get that pivot as fract level. Defaults to 2.

        Returns:
            list: list of fract prices
        """        
        
        # converting dataframes to np.ndarray
        all_pivots = []
        for pivots in self.Pivots.values(): 
            all_pivots += pivots.values.reshape(-1,1)[:,0].tolist()
        all_pivots.sort()
        all_high_lows = self._eval_range_of_high_lows(candle_ranges)  
        all_high_lows_ser = pd.Series(all_high_lows)
           
        fracts = []
        
        for pivot in all_pivots:
            upper_level = pivot + pivot*(tolerance_percent/100.0)
            lower_level = pivot - pivot*(tolerance_percent/100.0)
            cond  = (all_high_lows_ser <= upper_level) & (all_high_lows_ser >= lower_level)
            if cond.sum() >= min_occurred: fracts.append(pivot)
        fracts = list(set(fracts))
        fracts.sort()
        return fracts
    
    
    
    def _eval_fract_levels_by_past_high_lows(self, candle_ranges:range = range(30,150,20),
                                      tolerance_percent:float = 0.05,
                                      min_occurred:int = 1 ):
        """checks if past high and lows are fract levels.
        does this by checking if they have enough touch to high and lows.

        Args:
            candle_ranges (range, optional): candle range in range format. Defaults to range(100,200,20).
            tolerance_percent (float, optional): this specifies how accurate can touches be.
            if it is a lower value we have more accurate touches.Defaults to 0.01.
            min_occurred (int, optional): min touches to get that high/low as fract level. Defaults to 2.

        Returns:
            list: list of fract prices
        """        
        
        all_high_lows = self._eval_range_of_high_lows(candle_ranges)
        all_high_lows_ser = pd.Series(all_high_lows)
        fracts = []
        
        for pivot in all_high_lows_ser.values.reshape(-1,1)[:,0].tolist():
            upper_level = pivot + pivot*(tolerance_percent/100.0)
            lower_level = pivot - pivot*(tolerance_percent/100.0)
            cond  = (all_high_lows_ser <= upper_level) & (all_high_lows_ser >= lower_level)
            if cond.sum() >= min_occurred: fracts.append(pivot)
    
        fracts = list(set(fracts))
        fracts.sort()
        return fracts
    
    
    
    def eval_fract_levels(self,*, method:str = "both", candle_ranges:range = range(40,200,20),
                          tolerance_percent:float = 1e-5, min_occurred:int = 3, 
                          inplace:bool = True):
        """finds fract levels by past weekly and monthly pivots and past high and lows.
        does this by checking if they have enough touch.

        Args:
            candle_ranges (range, optional): candle range in range format. Defaults to range(100,200,20).
            tolerance_percent (float, optional): this specifies how accurate can touches be.
            if it is a lower value we have more accurate touches.Defaults to 0.01.
            min_occurred (int, optional): min touches to get that high/low as fract level. Defaults to 2.

        Returns:
            list: list of fract prices
        """        
        fracts = []
        
        match method:
            case "both":
                fracts = self._eval_fract_levels_by_past_high_lows(candle_ranges,tolerance_percent,
                                                                   min_occurred)
                
                fracts += self._eval_fract_levels_by_past_pivots(candle_ranges,
                                                                 tolerance_percent,
                                                                 min_occurred+1)                
            case "last_pivots":
                fracts = self._eval_fract_levels_by_past_high_lows(candle_ranges,tolerance_percent,
                                                                   min_occurred)
            case "weekly_pivots":
                fracts = self._eval_fract_levels_by_past_pivots(candle_ranges,
                                                                 tolerance_percent,
                                                                 min_occurred+1)
        fracts = list(set(fracts))
        fracts.sort()
        if inplace: self.fracts = fracts    
        return fracts
    
    
    def plot_fracts(self, inplace= True, **kwargs):
        if not self.fracts: 
            raise ValueError("fracts levels didn't evaluated, first run eval_Fract_levels func")
        from ...plotting.market_plotter import Market_Plotter
        
        plots = Market_Plotter(self.df, self.symbol, self.interval, 
                               self.data_exchange)
        fig = plots.plot_market(plot_by_grp=False)
        for frac in self.fracts:
            plots.draw_static_line(fig, "h",frac, kwargs.get("color","purple"), 
                                   f"{frac}","top center", font_size = 12)
        if inplace: self.fig = fig
        return fig
    
    
    def plot_Pivots(self, *, fig = None, dataframe:pd.DataFrame = pd.DataFrame(),
                   pivotsDate_col:str = "PivotDatetime",
                   which_pivot: dataTypes.PivotType = "weekly",
                   inplace:bool = False, **kwargs):
        """plot last weekly or monthly pivots

        Args:
            which_pivot (str, optional): "weekly" or "monthly". Defaults to "weekly".
            inplace (bool, optional): will replace current self.fig figure obj. Defaults to False.

        Returns:
            _type_: _description_
        """        
        from ...plotting.market_plotter import Market_Plotter
        which_pivot = which_pivot.lower()
        
        df_ = (self.df if dataframe.empty else dataframe).copy()
        
        if which_pivot.lower() not in ["weekly", "monthly"]:
            raise ValueError("which_pivot arg can be 'monthly' or 'weekly'.")
        
        if self.Pivots[which_pivot.lower()].empty:
            raise ValueError("pivots didn't evaluated yet!")
        else: pivots_df:pd.Series = self.Pivots[which_pivot.lower()]
        assert pivotsDate_col in df_.columns, f"column {pivotsDate_col} not found"
         
        plots = Market_Plotter(df_, self.symbol,
                               self.interval, self.data_exchange)  
              
        if not fig: fig = plots.plot_market(plot_by_grp = False)
        lastPivot_endDate = None
        for pivotDate, df_grp in df_.groupby(pivotsDate_col):
            pivots:dict = pivots_df.loc[pivotDate].to_dict()
            # drawing boundries
            plots.draw_static_line(fig, side = "v", c = pivotDate, Color="black",
                                   text = f"{pivotDate}", text_position='bottom left',
                                   font_size=12)
            
            # drawing boundry of last pivot
            if pivotDate == pivots_df.index[-1]: 
                from freqtrade.strategy import timeframe_to_seconds
                pivotType_dict = {"weekly":'1w', 'monthly':'1M'}
                tf2secs = timeframe_to_seconds(pivotType_dict[which_pivot])
                lastPivot_endDate = pivotDate + dt.timedelta(seconds=tf2secs)
                plots.draw_static_line(fig, side = "v", c = lastPivot_endDate, Color="black",
                                       text = f"{lastPivot_endDate}", text_position='bottom left',
                                       font_size=12)
                
            # drawing pivot lines
            for levelName, value in pivots.items():
                plots.draw_line(fig, [df_grp.index[0], value], 
                                [lastPivot_endDate or df_grp.index[-1], value],
                                kwargs.get("color", "orange"),
                                kwargs.get("width", 2), f"{levelName} pivot:{value}", 
                                'top center')
            
        if inplace: self.fig = fig
        return fig
        
                

                
         
