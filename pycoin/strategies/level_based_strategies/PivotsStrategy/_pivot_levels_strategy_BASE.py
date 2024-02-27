import os
from typing import Literal

import pandas as pd
from .._Levels_evaluator import _Levels
import datetime as dt
import numpy as np
from backtesting import Backtest
from backtesting.backtesting import Strategy
from bokeh.io import show, save
import shutil as sh
from pycoin import Utils
from pycoin.strategies._strategy_BASE import _StrategyBASE
from pycoin import exchanges
from pycoin.strategies import dataTypes


class Pivot_Strategy_BASE(_Levels):
    """pivot levels strategy based on weekly or monthly pivots (pivots_type arg). 

    Args:
        _Levels (_type_): _description_
    """    
    
    def __init__(self,*, symbol:str, interval: str, APIkeys_dir:str|None = None,
                 APIkeys_File:str|None = None, API_key:str|None = None,
                 Secret_key:str|None = None, pivots_type:dataTypes.PivotType = "weekly", 
                 read_APIkeys_fromFile: bool = False, start_time:dt.datetime|int = None,
                 read_APIkeys_fromEnv: bool = True, isdemo:bool = True, 
                 data_exchange:str = "binance", exchange:str = "bingx", 
                 init_update:bool = False, **kwargs) -> None:
        """_summary_

        Args:
            symbol (str): _description_
            interval (str): _description_
            APIkeys_dir (str | None, optional): _description_. Defaults to None.
            APIkeys_File (str | None, optional): _description_. Defaults to None.
            API_key (str | None, optional): _description_. Defaults to None.
            Secret_key (str | None, optional): _description_. Defaults to None.
            pivots_type (dataTypes.PivotType, optional): _description_. Defaults to "weekly".
            read_APIkeys_fromFile (bool, optional): _description_. Defaults to False.
            start_time (dt.datetime | int, optional): _description_. Defaults to None.
            read_APIkeys_fromEnv (bool, optional): _description_. Defaults to True.
            isdemo (bool, optional): _description_. Defaults to True.
        """
        
        super().__init__(symbol = symbol, interval = interval,  start_time = start_time,
                         freq = interval, data_exchange = data_exchange,
                         PivotsType = pivots_type.lower(), **kwargs)
        
        
        _API_KEY = os.environ.get("API_KEY", API_key) if read_APIkeys_fromEnv else API_key
        _SECRET_KEY = os.environ.get("SECRET_KEY", Secret_key) if read_APIkeys_fromEnv else Secret_key
         
        exchange_cls = exchanges[ exchange ]
        
        self.market = exchange_cls(symbol = symbol, isdemo = isdemo, 
                            APIkeys_File = APIkeys_File, APIkeys_dir = APIkeys_dir,
                            API_key = _API_KEY , Secret_key = _SECRET_KEY , 
                            read_APIkeys_fromFile = read_APIkeys_fromFile)
                
        self.C1_ind = None
        self.C2_ind = None
        self.crossed_pivot = None # the pivot line that C1 and C2 found on
        
        self.PivotsType = pivots_type.lower()
        
        if init_update: 
            self.update_data
            self.update_pivots
        
        
    
    @property
    def update_pivots(self):
        print("\n\nfetching Pivots data...")
        super().update_pivots        
        ## dataframe correspanding to last pivot
        self.df_lastPivots = Utils.get_by_datetimeRange(dataframe = self.df ,
                                                  start = self.Pivots[self.PivotsType].index[-1])
        print("done")
        self.add_PivotDatetime_to_dataframe(self.df, col_name="PivotDatetime", inplace=True)
         
        return self.LastPivots
        


    def add_PivotDatetime_to_dataframe(self, dataframe: pd.DataFrame = pd.DataFrame(), 
                                       col_name:str = "PivotDatetime", inplace = False):
        df_ = (self.df if dataframe.empty else dataframe).copy()
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
        
        
    
    @property
    def clear_data(self):
        self.C1_ind = self.C2_ind = None
        
    
    def _find_nearest_pivots(self, price:float):
        """find one/two nearest pivots to a price 

        Args:
            price (float): price 

        Returns:
            tuple[float, float]| None, float | float, None: pivots
        """        
        pivots_dict = self.LastPivots[self.PivotsType]
        
        lower_pivots = {}
        upper_pivots = {}
        for name, val in pivots_dict.items():
            if price >= val: lower_pivots[name] = val
            elif price < val: upper_pivots[name] = val

        upper_pivot = [min(upper_pivots.items(), key = lambda x:x[1])] if upper_pivots!={} else {}  
        lower_pivot = [max(lower_pivots.items(), key = lambda x:x[1])] if lower_pivots!={} else {} 
        return {**dict(lower_pivot), **dict(upper_pivot)}
        
        
        
    def _GetCrossedPivot_Candles(self, Price: float = None, *,
                                 df:pd.DataFrame = pd.DataFrame(), 
                                 candle_type:dataTypes.CandleType = "bullish"):
        """finds last 'bullish'/'bearish' candle that crossed a pivot. 

        Args:
            dataframe (pd.DataFrame, optional): finds candle on this df. Defaults to None.
            candle_type (str, optional): 'bullish' or 'bearish'. Defaults to "bullish".

        Raises:
            ValueError: _description_

        Returns:
            candle_indice, crossed pivot
        """        
        
        df_ = (self.df_lastPivots if df.empty else df).copy()
        
        pivots_dict = self._find_nearest_pivots(Price or self.LastClose)
        match candle_type.lower():
            case "bullish":
                return {pivot_name: Utils.getBulish_CrossedPrice(df_, pivot) 
                        for pivot_name, pivot in pivots_dict.items()}
                
            case "bearish":
                return {pivot_name: Utils.getBearish_CrossedPrice(df_, pivot)
                        for pivot_name, pivot in pivots_dict.items()} 
                
            case _ : 
                raise ValueError("candle_type can be 'bullish' or 'bearish'")
            
            
            
    def _FindAllC1C2_Candles_FromPrice(self, Price: float = None, *,
                                       df: pd.DataFrame = pd.DataFrame(),
                                       C1_Type:dataTypes.CandleType = "bearish",
                                       C2_Type:dataTypes.CandleType = "bullish",
                                       ignore_mean: bool = True, 
                                       timeout:dt.timedelta = dt.timedelta(days=3),
                                       min_time :dt.timedelta = dt.timedelta(hours=3),
                                       betweenCandles_C1C2_dist:float = 0.015
                                       ):
        
        assert C1_Type != C2_Type, "C1 and C2 candle type must be diffrent"
        cols = ['Open', 'High', 'Low', 'Close', 'Volume', "Datetime"]
        df_ = df.copy()
        if "Datetime" not in df_.columns: df_["Datetime"] = df_.index
        df_ = df_[cols].copy()
        if "datetime" not in df_.index.dtype.name.lower(): 
            df_.set_index("Datetime", inplace = True, drop = False) 
        C1_dict = self._GetCrossedPivot_Candles(Price = Price, df = df, candle_type = C1_Type)
        C2_dict = self._GetCrossedPivot_Candles(Price = Price, df = df, candle_type = C2_Type)
        assert C1_dict.keys() == C2_dict.keys(), "pivotLevels found must be same!"
        pivot_levelNames = C1_dict.keys()
        c1, c2 = "_C1", "_C2"
        C1_colNames, C2_colNames = [col+c1 for col in cols], [col+c2 for col in cols]
        # getting C1,C2 pair
        C1C2_candles = {}
        for levelName in pivot_levelNames:
            if ignore_mean and "mean" in levelName.lower(): continue
            C1_df, C2_df = C1_dict[levelName], C2_dict[levelName]
            C1_df["Datetime"], C2_df["Datetime"] = C1_df.index, C2_df.index
            # adding suffix to C1,C2 col names to identify them easily
            C1_df = Utils.add_to_ColumnNames(C1_df.copy(), suffix = c1)
            C2_df = Utils.add_to_ColumnNames(C2_df.copy(), suffix = c2)
            ## first concat to add indices
            C1C2_df = pd.concat([C1_df, C2_df], axis = 1)
            # shifting C1 part to align indexes and removing empty rows
            shifted_C1_df = C1C2_df[C1_colNames].shift(1)
            C1C2_df = pd.concat([shifted_C1_df, C2_df], axis = 1).dropna().copy()
            ## reverting column names to their initial names
            _C1_df, _C2_df = C1C2_df[C1_colNames], C1C2_df[C2_colNames]
            _C1_df = Utils.remove_from_ColumnNames(_C1_df, suffix = c1)
            _C2_df = Utils.remove_from_ColumnNames(_C2_df, suffix = c2)
            # making a list of dicts with C1 and C2 keys
            C1C2_candles[levelName] = [{"C1":C1[1].to_dict(), "C2":C2[1].to_dict()} 
                                       for C1, C2 in zip(_C1_df.iterrows(), _C2_df.iterrows())]
        # putting all levels C1, C2s in a single list
        all_C1C2_candles = []
        for C1C2s in C1C2_candles.values(): all_C1C2_candles += C1C2s
        all_C1C2_candles = self.C1C2_time_filter(all_C1C2_candles, timeout = timeout,
                                                 min_time=min_time)
        all_C1C2_candles = sorted(all_C1C2_candles, key = lambda x: x["C2"]["Datetime"])
        return all_C1C2_candles
    
    
    
    def __Find_AllC1C2_Candles_const_Pivot(self, *, dataframe: pd.DataFrame,
                                          ignore_mean: bool = True, 
                                          timeout:dt.timedelta = dt.timedelta(days=3),
                                          min_time :dt.timedelta = dt.timedelta(hours=3), 
                                          add_side_filter: bool = False,
                                          C1_type:str = "bullish", C2_type:str = "bearish"):
        pivots = self.LastPivots[self.PivotsType]
        pivots_ser = pd.Series(pivots)
        prices = [pivots_ser["Low"]-0.2, pivots_ser[["Low", "25%"]].mean(),
                  pivots_ser[["25%", "mean"]].mean(), pivots_ser[["mean", "75%"]].mean(),
                  pivots_ser[["75%", "High"]].mean(), pivots_ser["High"]+0.2]
        all_C1C2s = []
        for price in prices:
            if add_side_filter:
                C1Type, C2Type = ( ("bearish","bullish") if self._findSide_fromPivots(price) == "LONG" 
                else ("bullish", "bearish") )
            else: C1Type, C2Type = C1_type, C2_type
            all_C1C2s += self._FindAllC1C2_Candles_FromPrice(price, df=dataframe,
                                                    C1_Type=C1Type, C2_Type=C2Type,
                                                    ignore_mean=ignore_mean, 
                                                    timeout=timeout, min_time=min_time)
        all_C1C2s = sorted(all_C1C2s, key = lambda x: x["C2"]["Datetime"])
        return all_C1C2s
    
    
    
    def _Find_AllC1C2_Candles_const_Pivot(self, *, dataframe: pd.DataFrame,
                                          ignore_mean: bool = True, 
                                          timeout:dt.timedelta = dt.timedelta(days=3),
                                          min_time :dt.timedelta = dt.timedelta(hours=3), 
                                          add_side_filter: bool = False):
        
        main_kwargs = {"dataframe":dataframe, "ignore_mean":ignore_mean,
                  "timeout":timeout, "min_time":min_time}
        
        if add_side_filter:
            C1C2s = self.__Find_AllC1C2_Candles_const_Pivot(**main_kwargs,
                                                            add_side_filter=True)
        else: 
            C1C2s1 = self.__Find_AllC1C2_Candles_const_Pivot(**main_kwargs, 
                                                             add_side_filter=False,
                                                             C1_type="bullish", 
                                                             C2_type="bearish")
            C1C2s2 = self.__Find_AllC1C2_Candles_const_Pivot(**main_kwargs, 
                                                             add_side_filter=False,
                                                             C1_type="bearish", 
                                                             C2_type="bullish")
            C1C2s = C1C2s1+C1C2s2
            [C1C2s.remove(C1C2) for C1C2 in C1C2s if C1C2s.count(C1C2)>1]
            C1C2s = sorted(C1C2s, key = lambda x: x["C2"]["Datetime"] )
            return C1C2s
                
        
    
    
    
    def Find_AllC1C2_Candles(self, dataframe: pd.DataFrame = pd.DataFrame(), *, 
                             ignore_mean: bool = True,
                             PivotDatetime_col: str = "PivotDatetime", 
                             timeout:dt.timedelta = dt.timedelta(days=4),
                             min_time :dt.timedelta = dt.timedelta(hours=2),
                             add_side_filter:bool = False):
        all_C1C2s = []
        dataframe = (self.df if dataframe.empty else dataframe).copy()
        dataframe = self.add_PivotDatetime_to_dataframe(dataframe = dataframe,
                                                        col_name=PivotDatetime_col)
        for pivot_date, df_ in dataframe.groupby(PivotDatetime_col):
            self.LastPivots[self.PivotsType] = self.Pivots[self.PivotsType].loc[pivot_date].to_dict()
            all_C1C2s += self._Find_AllC1C2_Candles_const_Pivot(dataframe = df_,
                                                   ignore_mean = ignore_mean,
                                                   timeout=timeout, min_time=min_time, 
                                                   add_side_filter=add_side_filter)
        
        [all_C1C2s.remove(C1C2) for C1C2 in all_C1C2s if all_C1C2s.count(C1C2)>1]
        all_C1C2s = sorted(all_C1C2s, key = lambda x: x["C2"]["Datetime"] )
        return all_C1C2s

    
    
    def C1C2_time_filter(self, C1C2s:list[dict[str,dict]], 
                        timeout:dt.timedelta = dt.timedelta(days = 1), 
                        min_time:dt.timedelta = dt.timedelta(hours = 3)):
        assert timeout > min_time, "timout must be longer than min_time"
        all_C1C2s = [C1C2 for C1C2 in C1C2s 
                    if C1C2["C2"]["Datetime"] - C1C2["C1"]["Datetime"] <= timeout]
        return [C1C2 for C1C2 in all_C1C2s
                if C1C2["C2"]["Datetime"] - C1C2["C1"]["Datetime"] > min_time]
        
        
        
    def C1C2_size_filter(self, C1C2s: list[dict[str,dict]], 
                         CandleType: dataTypes.C1C2Type = "C2", 
                         minSize:float = 100):
        
        _C1C2s = C1C2s.copy()
        return [C1C2 for C1C2 in _C1C2s 
         if abs(C1C2[CandleType]["Close"] - C1C2[CandleType]["Open"]) >= minSize ]    
        
        
        
    def C1C2_minDistOFBetweenCandle_filter(self, C1C2s: list[dict[str, dict]],
                                           minDist: float = 0.015, 
                                           dataframe: pd.DataFrame = pd.DataFrame()):
        candleType_col = "CandleType"
        df_ = (self.df if dataframe.empty else dataframe).copy()
        df_[candleType_col] = Utils.add_candleType(df_)
        all_C1C2s = []
        for C1C2 in C1C2s:
            C1, C2 = C1C2["C1"], C1C2["C2"]
            between_C1C2_candles = df_.loc[C1["Datetime"]:C2["Datetime"]].iloc[1:-2]
            if between_C1C2_candles.empty: continue
            C1_type = df_.loc[C1["Datetime"], candleType_col]
            C1C2Type = 1 if C1_type == 1 else -1
            candlesByType_grp = between_C1C2_candles.groupby(candleType_col)
            if C1C2Type not in candlesByType_grp.groups: continue
            candlesByType = candlesByType_grp.get_group(C1C2Type)
            if C1C2Type == 1: 
                C1_diff = ( abs(C1["High"] - candlesByType["High"].max()) / C1["High"] )
                C2_diff = ( abs(C2["High"] - candlesByType["High"].max()) / C2["High"] )
                if C1_diff >= minDist and C2_diff >= minDist: 
                    all_C1C2s.append(C1C2)
            else:
                C1_diff = ( abs(C1["Low"] - candlesByType["Low"].min()) / C1["Low"] )
                C2_diff = ( abs(C2["Low"] - candlesByType["Low"].min()) / C2["Low"] )
                if C1_diff >= minDist and C2_diff >= minDist: 
                    all_C1C2s.append(C1C2)
        return all_C1C2s
            
                 
            
    # get the latest pivot crossed      
    def _GetLatestCrossedPivot_candle_from_LastClose(self, *, 
                                                    dataframe: pd.DataFrame = pd.DataFrame(),
                                                    candle_type: dataTypes.CandleType = "bullish"):
        
        """get the latest pivot crossed pivot candle relative to last close

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """        
        crossed_candles_dict = self._GetCrossedPivot_Candles(Price = self.LastClose,
                                                             df = dataframe, 
                                                             candle_type = candle_type)
        lastCrossed_candle = max( [df.iloc[-1] for levelName, df in crossed_candles_dict.items()
                                   if "mean" in levelName and not df.empty], 
                                   key = lambda x: x.name, default = pd.Series()) 
        return lastCrossed_candle
        
                    
    
    
    # check if last pivots are long position pivots or not
    def _findSide_fromPivots(self, close_price:float) -> Literal['SHORT', 'LONG']:
        """find position side from input price according to it's nearest pivots 

        Raises:
            ValueError: _description_

        Returns:
            "LONG" or "SHORT"
        """        
        return "SHORT" if close_price >= self.LastPivots[self.PivotsType]["mean"] else "LONG" 
    
                
                
                
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
        from ....plotting import Market_Plotter
        df_ = (self.df if dataframe.empty else dataframe).copy()
        plots = Market_Plotter(OHLCV_df = df_, symbol = self.symbol,
                               freq = self.interval, exchange=self.data_exchange)
        
        fig = fig or plots.plot_market()
        for C1C2 in C1C2s:
            plots.highlight_single_candle(fig, C1C2["C1"]["Datetime"], color=C1_color)
            plots.highlight_single_candle(fig, C1C2["C2"]["Datetime"], color=C2_color)
        return fig
    
    
    
    def Get_Backtest( self, *, minC1C2_dist:int = 1, max_init_SL_percent:float = 2,
                      init_cash:float = 100000, broker_fee:float = 0.0005, 
                      start_datetime:dt.datetime|int = None, leverage:int = 1,
                      maxDistFromSL_toClose:int = 2,
                      maxDistFromTP_toClose:int = 5,
                      ):
        """get backtest object 

        Args:
            minC1C2_dist (int, optional): minC1C2_dist. Defaults to 2.
            max_init_SL_percent (float, optional): _description_. Defaults to 2.
            init_cash (float, optional): _description_. Defaults to 100000.
            broker_fee (float, optional): _description_. Defaults to 0.0005.
            start_datetime (dt.datetime | int, optional): _description_. Defaults to None.
            leverage (int, optional): _description_. Defaults to 1.
            maxDistFromSL_toClose (int, optional): _description_. Defaults to 2.
            maxDistFromTP_toClose (int, optional): _description_. Defaults to 5.

        Returns:
            _type_: _description_
        """        
        
        pivot_bt = _PivotStrategy_Backtesting(self)
        pivot_bt.Run_Backtest(minC1C2_dist=minC1C2_dist, max_init_SL_percent=max_init_SL_percent,
                              init_cash=init_cash, broker_fee=broker_fee, leverage=leverage,
                              start_datetime=start_datetime,
                              maxDistFromSL_toClose = maxDistFromSL_toClose,
                              maxDistFromTP_toClose = maxDistFromTP_toClose,
                              )
        return pivot_bt
                
                
                
    def LONG(self,*, quantity:float, SL:float = None, TP:float = None, SL_amount:float = None, 
             TP_amount:float = None, leverage:int = 1 ):
            
        return self.market.make_order(positionSide = "LONG", quantity = quantity,
                                      orderType = "market", stopLoss = SL,
                                      profitLevel = TP, stopLoss_quantity = SL_amount,
                                      profitLevel_quantity = TP_amount, leverage = leverage,
                                      verifyByUser=False)

    
    def SHORT(self,*, quantity:float, SL:float = None, TP:float = None, SL_amount:float = None, 
             TP_amount:float = None, leverage:int = 1):        
        
        return self.market.make_order(position_side = "SHORT", quantity = quantity,
                                      order_type = "market",stopLoss = SL,
                                      profitLevel = TP , stopLoss_quantity = SL_amount,
                                      profitLevel_quantity = TP_amount, leverage = leverage)
                
    
    def _findSide_FromC2(self, C2_row):
        """finds side from C2 candle

        Args:
            C2_row (_type_): C2_row as OHLC dataframe.

        Returns:
            "LONG" or "SHORT"
        """        
        return "LONG" if C2_row.close > C2_row.open else "SHORT"
    

    
    
    def define_init_SLTPs(self, C2_row:pd.DataFrame, crossed_pivot:float,
                          max_init_SL_percent:float = 5.0,):
        """define init SL and TP. SL will be shaow price of given C2 candle.
        and TP will be the next pivot line.

        Args:
            C2_row (pd.DataFrame): _description_
            crossed_pivot (float): crossed pivot price.
            max_init_SL_percent (float, optional): this will be the SL if C2 shadow is bigger
            than this percent. Defaults to 5.0.
        """        
                
        if self.side == "LONG":
            C2_change_percent = ((C2_row.close-C2_row.low)/C2_row.close) *100
            max_SL = C2_row.close - (C2_row.close*max_init_SL_percent)/100
            self.SL = max_SL if (C2_change_percent > max_init_SL_percent) else C2_row.low \
                    if C2_row.close > C2_row.open else C2_row.high
                    
            current_ind = np.where(self.last_pivots == crossed_pivot)[0][0]
            self.TP = self.last_pivots[current_ind +1] # TP till next pivot
            assert self.TP > self.SL
            
        elif self.side == "SHORT":
            C2_change_percent = ((C2_row.high - C2_row.close)/C2_row.close)*100
            max_SL = C2_row.close + (C2_row.close * max_init_SL_percent)/100
            self.SL = max_SL if C2_change_percent > max_init_SL_percent else C2_row.high \
                      if C2_row.open > C2_row.close else C2_row.low
            current_ind = np.where(self.last_pivots == crossed_pivot)[0][0]
            self.TP = self.last_pivots[current_ind -1]
            assert self.TP < self.SL
            
            
    
    
    def update_SLTPs(self, last_close:float): 
        """update SL and TP if they're not None. TP will be next pivot line in this method and 
        SL will be previous passed pivot line 

        Args:
            last_close (float): last current market close price
        """        
        
        if None in [self.TP, self.SL]: return 
        
        if self.side == "LONG":
            if last_close >= self.TP: # places SL at arrived TP and new TP at next pivot
                self.SL = self.TP
                if self.TP == self.last_pivots[-1] or self.TP == self.last_pivots[0]: return
                current_ind = np.where(self.last_pivots == self.TP)[0][0]
                self.TP = self.last_pivots[current_ind+1]
                assert self.TP > self.SL
                
        elif self.side == "SHORT":
            if last_close <= self.TP:
                self.SL = self.TP
                if self.TP == self.last_pivots[-1] or self.TP == self.last_pivots[0]: return
                current_ind = np.where(self.last_pivots == self.TP)[0][0]
                self.TP = self.last_pivots[current_ind -1]
                assert self.TP < self.SL
                
    
class _PivotStrategy_Backtesting:
    def __init__(_self_ , pivot_strategy_obj) -> None:
        _self_.pivot_obj = pivot_strategy_obj
        _self_.SL = None
        _self_.TP = None
        _self_.bt = None
        _self_._backtest_objs = []
        _self_._backtest_results = []
        _self_._plots = []
        _self_.C1_ind_all= []
        _self_.C2_ind_all = []
        _self_.all_SLs = []
        _self_.all_TPs = []
        _self_.all_pivots = []
        _self_.all_dfs = []
        _self_.pivot_number = 0

        
    def _make_Backtest(_self_, minC1C2_dist:int = 2, max_init_SL_percent:float = 5,
                      init_cash:float = 100000, broker_fee:float = 0.0005, leverage:int = 1,
                      dataframe:pd.DataFrame = None,
                      maxDistFromSL_toClose:int = 5,
                      maxDistFromTP_toClose:int = 5,
                      start_datetime:dt.datetime|int = None):
        
        df_ = dataframe.copy()
            
        class Pivot_StrategyBacktest(Strategy):                
            
            def init(self):
                self.last_order = None
                self.C2_ind, self.C1_ind, self.crossed_pivot = None, None, None
                self.C1s = []
                self.C2s = []
                self.SLs = []
                self.TPs = []
                _self_.pivot_number += 1
                print(f"current pivot number {_self_.pivot_number}: ", _self_.pivot_obj.last_pivots)
                self.i = 0 # used to count candles passed
                self.TP_counter_activate = 0
                self.SL_counter_activate = 0
                
            @property
            def isHigherClose(self):
                return True if self.data.Close[-1] >= self.data.Close[-2] else False 
            
            @property
            def zero_counters(self):
                self.SL_counter_activate = 0
                self.TP_counter_activate = 0

            @property
            def clear_every_thing(self):
                self.zero_counters
                _self_.pivot_obj.clear_data
                
                
            @property
            def clear_PosData(self):
                self.C1_ind = self.C2_ind = self.crossed_pivot = None
                
                
            @property
            def clear_SLTP(self):
                _self_.pivot_obj.SL = None
                _self_.pivot_obj.TP = None
                
                
            @property
            def SL(self):
                return _self_.pivot_obj.SL
            
            
            @property
            def TP(self):
                return _self_.pivot_obj.TP
        
        
            @property
            def Pending_SL(self):
                assert self.haveActivePos, "no active positions"
                return self.trades[0].sl
            
            @property
            def Pending_TP(self):
                assert self.haveActivePos, "no active positions"
                return self.trades[0].tp
                
                
            @property
            def haveActivePos(self):
                return False if len(self.trades) == 0 else True
            
            
            @property
            def Save_SLTP(self):
                self.SLs.append(self.SL)
                self.TPs.append(self.TP)
            
            
            @property
            def Save_C1C2(self):
                self.C1s.append(self.C1_ind)
                self.C2s.append(self.C2_ind)

            
            @property
            def side(self):
                return _self_.pivot_obj.side
            
            
            def change_SLTP_vals(self, New_SL:float, New_TP:float ):
                assert self.haveActivePos, "no active positions!"
                for pos in self.trades: pos.sl, pos.tp = New_SL, New_TP
                
            
            def reached_anySLTP(self):
                assert self.haveActivePos, "no active positions!"
                for pos in self.trades:
                    if not self.isIn_SLTP_Range(pos.sl, pos.tp): return True
                return False
            
            
            def reached_SL(self, SL):
                assert self.haveActivePos, "no active positions!"
                if self.position.is_long and self.data.Close[-1] <= SL: return True
                elif self.position.is_short and self.data.Close[-1] >= SL: return True
                return False   
                
                
            def reached_TP(self, TP):
                assert self.haveActivePos,"no active positions"
                if self.position.is_long and self.data.Close[-1] >= TP: return True
                elif self.position.is_short and self.data.Close[-1] <= TP: return True
                return False

            
            
            @property
            def thereIsjust_oneActive_Pos(self):
                assert self.haveActivePos, "no active positions !"
                assert self.NumOf_activePos == 1, "num of active positions more than 1"
                 
            
            @property
            def NumOf_activePos(self):
                return len(self.trades)
            
            
            def C2_side(self, C2_row):
                return _self_.pivot_obj._findSide_FromC2(C2_row)
                

            def isIn_SLTP_Range(self, SL:float, TP:float):
                
                if self.position.is_long:
                    if SL <= self.data.Close[-1] <= TP: return True
                
                elif self.position.is_short:
                    if TP <= self.data.Close[-1] <= SL:return True
                                    
                else: return False      
                
                
            def log(self):
                print(f"current SL:{self.SL}, Close:{self.data.Close[-1]}, TP:{self.TP}, size:{self.position.size}, last_crossed_pivot:{self.crossed_pivot}")               
                 
            
            def next(self):
                
                df_data = pd.DataFrame({"open": self.data.Open, "close": self.data.Close,
                                        "high": self.data.High, "low":self.data.Low})
                
                res = _self_.pivot_obj.find_LastC1C2_candles(minC1C2_dist, df_data )
                
                
                if None not in res:
                    self.C1_ind, self.C2_ind, self.crossed_pivot = res
                    self.Save_C1C2
                    
                    if self.side == "LONG":
                        if self.position.is_long: 
                            self.zero_counters
                            self.clear_SLTP
                            _self_.pivot_obj.define_init_SLTPs(df_.iloc[self.C2_ind], self.crossed_pivot,
                                                                max_init_SL_percent)
                            return
                            
                        elif self.position.is_short: 
                            self.position.close()
                            self.zero_counters
                            self.clear_SLTP
                            
                        self.last_order = self.buy()

                        
                    elif self.side == "SHORT":
                        if self.position.is_short: 
                            self.zero_counters
                            self.clear_SLTP
                            _self_.pivot_obj.define_init_SLTPs(df_.iloc[self.C2_ind], self.crossed_pivot,
                                                                max_init_SL_percent)
                            return
                        
                        elif self.position.is_long:
                            self.position.close()
                            self.zero_counters
                            self.clear_SLTP
                            
                        self.last_order = self.sell()                        
                    
                    
                # defining SL TPs for positions  
                if self.haveActivePos:
                    
                    if None in [self.SL, self.TP]:
                        _self_.pivot_obj.define_init_SLTPs(df_.iloc[self.C2_ind], self.crossed_pivot,
                                                           max_init_SL_percent)
                        
                    elif self.reached_TP(self.TP):
                        _self_.pivot_obj.update_SLTPs(self.data.Close[-1]) 
                        self.zero_counters
                        
                    if None not in [self.SL, self.TP]:
                        self.Save_SLTP
                        if self.reached_SL(self.SL): self.SL_counter_activate += 1 
                        elif self.reached_TP(self.TP): self.TP_counter_activate += 1
                        else: self.zero_counters
                        
                        SL_cond = self.SL_counter_activate >= maxDistFromSL_toClose
                        TP_cond = self.TP_counter_activate >= maxDistFromTP_toClose
                        
                        long_cond = self.position.is_long and not self.isHigherClose 
                        short_cond = self.position.is_short and self.isHigherClose
                        
                        # indicator conds
                        
                        if (long_cond or short_cond) and (SL_cond or TP_cond):
                            self.position.close()
                            self.zero_counters
                            self.clear_SLTP
                            
                    else:
                        self.clear_every_thing
                        self.clear_PosData
                        self.clear_SLTP
                        self.zero_counters
                
                self.i +=1
                
                
        bt = Backtest(case_col_names(to_datetime_index(df_)),
                        Pivot_StrategyBacktest,
                        cash = init_cash, 
                        commission = broker_fee,
                        margin = 1/leverage)
        
        return bt

        
            
            
    def Run_Backtest(_self_ , *,minC1C2_dist: int = 2, 
                     max_init_SL_percent: float = 5, 
                     init_cash: float = 100000, broker_fee: float = 0.0005, 
                     leverage: int = 1, start_datetime: dt.datetime|int = None,
                     maxDistFromSL_toClose:int = 5,
                     maxDistFromTP_toClose:int = 5,
                     ):
        
        if start_datetime: _self_.pivot_obj.Download_KlineDataFrame(start_datetime = start_datetime,
                                                                    verbose=False)
        
        
        dfPivots_pair = _self_.pivot_obj._get_dfPivots_pair(_self_.pivot_obj.df)
        init_pivots = _self_.pivot_obj.last_pivots.copy()
        _self_.all_pivots = [pivots for df, pivots in dfPivots_pair]
        _self_.all_dfs = [df for df, pivots in dfPivots_pair]
        
        for df_pivot, pivots in dfPivots_pair:
            pivots.sort()
            _self_.pivot_obj.last_pivots = pivots
            _self_.pivot_obj.clear_data
            _self_.pivot_obj.clear_SL_TPs
            bt  = _self_._make_Backtest(dataframe = df_pivot, minC1C2_dist=minC1C2_dist,
                                        init_cash = init_cash, broker_fee=broker_fee,
                                        leverage = leverage,
                                        max_init_SL_percent=max_init_SL_percent,
                                        maxDistFromSL_toClose = maxDistFromSL_toClose,
                                        maxDistFromTP_toClose = maxDistFromTP_toClose,
                                        )
            _self_._backtest_objs.append(bt)
            res = bt.run()
            _self_._backtest_results.append(res)
            
        _self_.C1_ind_all =  [list(set(res["_strategy"].C1s)) for res in _self_._backtest_results]
        _self_.C2_ind_all = [list(set(res["_strategy"].C2s)) for res in _self_._backtest_results]
        _self_.all_SLs = [list(set(res["_strategy"].SLs)) for res in _self_._backtest_results]
        _self_.all_TPs = [list(set(res["_strategy"].TPs)) for res in _self_._backtest_results]
        
        _self_.pivot_obj.last_pivots = init_pivots
        return pd.DataFrame(_self_._backtest_results)
    
    
    
    
    def plot(_self_, lines_width:int = 2, shapes_size = 20, C1_color = "brown", 
             C2_color = "blue", SL_color = "red", TP_color = "green", pivots_color = "orange" ):
        
        _self_._plots = [bt_obj.plot(open_browser = False, superimpose = False)
                         for bt_obj in _self_._backtest_objs]
        
        # edditing all figures
        for plot, pivots, C1_inds, C2_inds, SLs, TPs, df in zip(_self_._plots, _self_.all_pivots,
                                                                _self_.C1_ind_all, _self_.C2_ind_all,
                                                                _self_.all_SLs, _self_.all_TPs,
                                                                _self_.all_dfs):
            
            fig_tuple = plot.children[2 if len(plot.children) != 2 else 0]
            
            # add any edits or shapes to newfig fig obj
            
            newfig = fig_tuple[0] # adding pivot lines
            newfig.hspan(y = list(pivots), width = lines_width, color = pivots_color,
                         legend_label = f"{_self_.pivot_obj.pivots_type} pivot", name = "pivots")
            # add circle at C1 candles
            newfig.circle(x = C1_inds, y = df.iloc[C1_inds][["high", "low"]].mean(axis = 1), 
                          size = shapes_size, alpha = 0.8, color = C1_color, 
                          legend_label = "C1 candles", name = "C1_candles")
            # add circle at C2 candles
            newfig.circle(x = C2_inds, y = df.iloc[C2_inds][["high", "low"]].mean(axis = 1), 
                          size = shapes_size, alpha = 0.8, color = C2_color,
                          legend_label = "C2 candles", name = "C2_candles")
            # add SL lines
            newfig.hspan(y = list(SLs), width = lines_width, color = SL_color,
                         legend_label = "StopLosses", name = "SLs", line_dash='dashdot')
            # add TP lines
            newfig.hspan(y = list(TPs), width = lines_width, color = TP_color,
                         legend_label = "ProfitLevels", name = "TPs", line_dash='dashed')
            
            # adding titles
            newfig.title.text = f"{_self_.pivot_obj.symbol} {_self_.pivot_obj.interval} {_self_.pivot_obj.pivots_type} pivot strategy from: {df.datetime.iloc[0]}  to: {df.datetime.iloc[-1]} on {_self_.pivot_obj.platform}"
            newfig.title.text_font_size = "14pt"
            newfig.title.text_font_style = "bold"
            
        [show(plot) for plot in _self_._plots]
        from IPython.display import clear_output
        clear_output()
        return _self_._plots
            
            
    @property
    def results(_self_):
        return pd.DataFrame(_self_._backtest_results)
    
    @property ##### needs to edit
    def mean_results(_self_):
        return _self_.results.mean(numeric_only = True)
    
    @property
    def trades(_self_):
        trades_df = pd.DataFrame()
        for i, row in _self_.results.iterrows():
            trades_df = pd.concat( [trades_df, row["_trades"]], axis = 0, ignore_index = True)
        return trades_df
    
    
    def Save_Plots_Html(_self_, folder_name:str = None):
        if folder_name is None: 
            folder_name = f"{_self_.pivot_obj.symbol}_{_self_.pivot_obj.interval}_{_self_.pivot_obj.pivots_type}_PivotStrategyBacktest_{_self_.pivot_obj.platform}"
        cwd = os.getcwd()
        
        if folder_name in os.listdir(): 
            sh.rmtree(folder_name)
            os.mkdir(folder_name)
            os.chdir(folder_name)
        else: 
            os.mkdir(folder_name)
            os.chdir(folder_name)
            
        for plot in _self_._plots:
            fig = plot.children[2 if len(plot.children) != 2 else 0][0]
            file_name = fig.title.text.replace(" ",'_')+".html"
            save(plot, file_name)
        
        sh.make_archive("./"+folder_name, "zip", "./"+folder_name)
        os.chdir(cwd)
        

            
            
                            
                            
                         
    
                
        

        

        
                

                
         

