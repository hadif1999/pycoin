from typing import Any
import pandas as pd
import datetime as dt
from pycoin.data_gathering import get_market_High_Lows
from pycoin.strategies import dataTypes
from pycoin.strategies._strategy_BASE import _StrategyBASE
from pycoin.data_gathering.high_lows_evaluator import SUGGESTED_CANDLE_RANGE


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
                                                   timeframe = "1w", 
                                                   since = self.start_time,
                                                   limit=self.limit or 1000)
        
        monthly_pivots_df = self.KlineData_gatherer(symbol = self.symbol, 
                                                    data_exchange=self.data_exchange,
                                                    timeframe = "1M",
                                                    since = self.start_time,
                                                    limit=self.limit or 1000)
            
        weekly_pivots = self._eval_pivots(weekly_pivots_df)
        monthly_pivots = self._eval_pivots(monthly_pivots_df)
        
        weekly_pivots = self._get_numeric_cols(weekly_pivots)
        monthly_pivots = self._get_numeric_cols(monthly_pivots)
        
        self.Pivots["weekly"] = weekly_pivots
        self.Pivots["monthly"] = monthly_pivots
        
        self.LastPivots["weekly"] = weekly_pivots.iloc[-1].to_dict()
        self.LastPivots["monthly"] = monthly_pivots.iloc[-1].to_dict()
        return self.Pivots
    
    
    def add_PivotDatetime_to_dataframe(self, dataframe: pd.DataFrame = pd.DataFrame(), 
                                       col_name:str = "PivotDatetime", inplace = False):
        df_, df_.Name = ((self.df.copy(), self.df.Name) if dataframe.empty
               else (dataframe.copy(), dataframe.Name))
        pivots = self.Pivots[self.PivotsType]
        dt_ser = pd.Series(pivots.index)
        df_[col_name] = None
        for val, next_val in zip(dt_ser.items(), dt_ser.shift(-1).items()):
            _, datetime = val
            _, next_datetime = next_val
            if isinstance(next_datetime, pd.NaT.__class__): next_datetime = None
            if not df_.loc[datetime: next_datetime].empty:
                df_.loc[datetime: next_datetime, col_name] = datetime
        
        df_[col_name] = pd.to_datetime(df_[col_name])
        if inplace: self.df = df_
        return df_
        
        
        
            
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
        df_.Name = df.Name
        df_["mean"] = df_[["High", "Low"]].mean(axis = 1)
        df_["75%"] = df_[["High", "mean"]].mean(axis = 1)
        df_["25%"] = df_[["mean", "Low"]].mean(axis = 1)
        return df_[["Low","25%","mean","75%","High"]]


    def _eval_range_of_high_lows(self, candle_ranges:range = range(100,200,20), **kwargs):
        """evaluates market high and lows but for a range of candles. it gathers high and lows for
        each candle range and returns their price in a list.

        Args:
            candle_ranges (range, optional): range of candles to evaluate high and lows.
            Defaults to range(100,200,20).

        Returns:
            list: list of prices of evaluated high and lows.
        """        
        
        all_high_lows = []
        colName = kwargs.get("colName", "Pivot")
        
        for _range in candle_ranges:
            
            df = get_market_High_Lows(self.df, candle_range = _range, colName=colName, **kwargs)
            pivots_grp = df.groupby(colName)
            try:
                high_ser = pivots_grp.get_group(1)["High"]
                all_maxs = high_ser.values.reshape(-1,1)[:,0].tolist()
            except: 
                all_maxs = []
            
            try:
                low_ser = pivots_grp.get_group(-1)["Low"]
                all_mins = low_ser.values.reshape(-1,1)[:,0].tolist()
            except: 
                all_mins = []
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
                                      min_occurred:int = 1, **kwargs ):
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
        
        all_high_lows = self._eval_range_of_high_lows(candle_ranges, **kwargs)
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
    
    
    
    def eval_fract_levels(self,*, method:str = "both", 
                          candle_ranges:range|None = None,
                          tolerance_percent:float = 1e-7, min_occurred:int = 3, 
                          inplace:bool = True, 
                          min_FractsDist_Pct: float = 0.01, **kwargs):
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
        if not candle_ranges: 
            candle_ranges = range(SUGGESTED_CANDLE_RANGE.get(self.interval, 10),400,20)
        
        match method:
            case "both":
                fracts = self._eval_fract_levels_by_past_high_lows(candle_ranges,tolerance_percent,
                                                                   min_occurred, **kwargs)
                
                fracts += self._eval_fract_levels_by_past_pivots(candle_ranges,
                                                                 tolerance_percent,
                                                                 min_occurred+1)                
            case "fracts":
                fracts = self._eval_fract_levels_by_past_high_lows(candle_ranges,tolerance_percent,
                                                                   min_occurred, **kwargs)
            case "pivots":
                fracts = self._eval_fract_levels_by_past_pivots(candle_ranges,
                                                                 tolerance_percent,
                                                                 min_occurred+1)
        fracts = list(set(fracts))
        fracts = self.fracts_distance_filter(fracts, min_FractsDist_Pct, **kwargs)
        if inplace: self.fracts = fracts    
        return fracts
    
    
    def fracts_distance_filter(self, fracts:list[float], minDist_pct:float = 0.005,
                               rel_to_LastClose: bool = True):
        fracts_ser = pd.Series(fracts).sort_values().reset_index(drop=True).copy()
        change_pct = (fracts_ser.diff()/self.LastClose 
                      if rel_to_LastClose else fracts_ser.pct_change())
        lowDistFracts = change_pct <= minDist_pct
        while lowDistFracts.any():
            fracts_toMerge = pd.concat([fracts_ser, fracts_ser.shift(1)], axis=1)[lowDistFracts]
            for i, _fracts_ in fracts_toMerge.T.items():
                fracts_ser.loc[[i, i-1]] = _fracts_.mean()
            fracts_ser.drop_duplicates(inplace=True)
            fracts_ser = fracts_ser.sort_values().reset_index(drop = True).copy()
            change_pct = (fracts_ser.diff()/self.LastClose 
                         if rel_to_LastClose else fracts_ser.pct_change())
            lowDistFracts = change_pct <= minDist_pct
        return fracts_ser.sort_values().round(4).tolist()
    
    
    def _plot_C1C2_candles(self, C1C2s:list[dict[str, dict]], 
                            fig = None ,C1_color:str = "orange",
                            dataframe: pd.DataFrame = pd.DataFrame(),
                            C2_color:str = "purple",
                            inplace:bool = False, **kwargs):
            """used in self.pastC1C2candles. iterates over input dataframe, finds and plots C1C2s

            Args:
                fig (plotly.graph_objs, optional): input figure. Defaults to None.
                C1_color (str, optional): _description_. Defaults to "orange".
                C2_color (str, optional): _description_. Defaults to "purple".
                dataframe (pd.DataFrame, optional): _description_. Defaults to None.
                inplace (bool, optional): _description_. Defaults to False.

            Returns:
                _type_: _description_
            """        
            from pycoin.plotting import Market_Plotter
            df_ = (self.df if dataframe.empty else dataframe).copy()
            df_.Name = self.df.Name
            plots = Market_Plotter(OHLCV_df = df_)
            
            fig = fig or plots.plot_market()
            for C1C2 in C1C2s:
                plots.highlight_single_candle(fig, C1C2["C1"]["Datetime"], color=C1_color)
                plots.highlight_single_candle(fig, C1C2["C2"]["Datetime"], color=C2_color)
            return fig
        
    
    def plot_fracts(self, inplace= True, **kwargs):
        if not self.fracts: 
            raise ValueError("fracts levels didn't evaluated, first run eval_Fract_levels func")
        from pycoin.plotting.market_plotter import Market_Plotter
        plots = Market_Plotter(self.df)
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
        
        df_, df_.Name = ((self.df.copy(), self.df.Name) if dataframe.empty 
                         else (dataframe.copy(),dataframe.Name))
        df_.index = df_.index.tz_localize('US/Eastern')
        
        if which_pivot.lower() not in ["weekly", "monthly"]:
            raise ValueError("which_pivot arg can be 'monthly' or 'weekly'.")
        
        if self.Pivots[which_pivot.lower()].empty:
            raise ValueError("pivots didn't evaluated yet!")
        else: pivots_df:pd.Series = self.Pivots[which_pivot.lower()]
        
        if not pivotsDate_col in df_.columns:
            df_ = self.add_PivotDatetime_to_dataframe(df_, pivotsDate_col)
         
        plots = Market_Plotter(df_)  
              
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
        
                

                
         
