from pycoin import KlineData_Fetcher
from pycoin.order_making import Bingx
from . import _Levels
import datetime as dt
import pandas as pd
from .. import dataTypes
from pycoin import Utils
from typeguard import typechecked

class Fract_Levels(_Levels):
    
    def __init__(self,*, symbol:str, timeframe: str, APIkeys_dir:str|None = None,
                 APIkeys_File:str|None = None, API_key:str|None = None,
                 Secret_key:str|None = None, exchange:str = "bingx",
                 read_APIkeys_fromFile: bool = False, start_time:dt.datetime|int = None,
                 read_APIkeys_fromEnv: bool = True, isdemo:bool = True, 
                 data_exchange:str = "binance", **kwargs) -> None:
        
        super().__init__(symbol = symbol, timeframe = timeframe, start_time = start_time,
                         data_exchange = data_exchange, **kwargs)
        
    
    
    def _find_nearest_FractLevels(self, price:float):
        """find one/two nearest pivots to a price 

        Args:
            price (float): price 

        Returns:
            list[float, float]| None, float | float, None: levels
        """        
        levels = self.fracts
        if levels is None: 
            raise NotImplementedError("first you have to calculate fract levels")
        
        lower_levels = []
        upper_levels = []
        for level in levels:
            if price >= level: lower_levels.append(level)
            elif price < level: upper_levels.append(level)

        upper_level = min(upper_levels) if upper_levels!=[] else None   
        lower_level = max(lower_levels) if lower_levels!=[] else None  
        return [lower_level, upper_level]
    
    
    def eval_fract_levels(self, *, method: str = "both",
                          candle_ranges: range | None = None,
                          accuracy_pct: float = 1e-9, min_occurred: int = 2,
                          inplace: bool = True, min_FractsDist_Pct: float = 0.01, 
                          find_onIntervals: list[str] = ["1d", "1w"], **kwargs):
        
        all_fractsLevels = []
        for _interval in find_onIntervals:
            levels = _Levels(symbol=self.symbol, timeframe= _interval,
                         data_exchange=self.data_exchange, start_time=self.start_time)
            levels.update_data
            if method in ["both", "pivots"]: levels.update_pivots
            fractsLevels = levels.eval_fract_levels(
                         method = method,
                         candle_ranges = candle_ranges, # window size for evaluating high and lows
                         tolerance_percent=accuracy_pct, # a tolerance to specify how much accurate touches must be 
                         min_occurred=min_occurred, 
                         min_FractsDist_Pct=min_FractsDist_Pct, **kwargs
                         ) 
            all_fractsLevels += fractsLevels
        all_fractsLevels = sorted(list(set(all_fractsLevels)))
        all_fractsLevels = self.fracts_distance_filter(all_fractsLevels, 
                                                        min_FractsDist_Pct,
                                                        **kwargs)
        if inplace: self.fracts = all_fractsLevels
        return all_fractsLevels
    
    
    
    def eval_FractsRegion(self, tolerance: float = 0.01, **kwargs):
        if "min_FractsDist_Pct" in kwargs: del kwargs["min_FractsDist_Pct"]
        fracts = self.eval_fract_levels(min_FractsDist_Pct=tolerance, **kwargs)
        fracts_ser = pd.Series(fracts)
        fracts_ser_lower = fracts_ser - (fracts_ser*tolerance)
        fracts_ser_upper = fracts_ser + (fracts_ser*tolerance)
        fracts_ser_lower.name = "fracts_lower"
        fracts_ser.name = "fracts"
        fracts_ser_upper.name = "fracts_upper" 
        fracts_df = pd.concat([fracts_ser_lower, fracts_ser, fracts_ser_upper], axis=1)
        if kwargs.get("inplace", True): 
            fracts = sorted(fracts_df.values.reshape(1, -1)[0].tolist()) 
            self.fracts = fracts
        return fracts_df
    
    
    
    def _GetCrossedFracts_Candles(self, Price: float = None, *,
                                 df:pd.DataFrame = pd.DataFrame(), 
                                 candle_type:dataTypes.CandleType = "bullish", 
                                 ignore_HighLow: bool = True):
        """finds last 'bullish'/'bearish' candle that crossed a pivot. 

        Args:
            dataframe (pd.DataFrame, optional): finds candle on this df. Defaults to None.
            candle_type (str, optional): 'bullish' or 'bearish'. Defaults to "bullish".

        Raises:
            ValueError: _description_

        Returns:
            candle_indice, crossed pivot
        """        
        
        df_ = (self.df if df.empty else df).copy()
        
        nearFracts = self._find_nearest_FractLevels(Price or self.LastClose)
        
        match candle_type.lower():
            case "bullish":
                return {level: Utils.getBulish_CrossedPrice(df_, level, ignore_HighLow) 
                        for level in nearFracts}
            case "bearish":
                return {level: Utils.getBearish_CrossedPrice(df_, level, ignore_HighLow)
                        for level in nearFracts} 
            case _ : 
                raise ValueError("candle_type can be 'bullish' or 'bearish'")
            
            
    
    def _FindAllC1C2_Candles_FromPrice(self, Price: float = None, *,
                                       df: pd.DataFrame = pd.DataFrame(),
                                       C1_Type:dataTypes.CandleType = "bearish",
                                       C2_Type:dataTypes.CandleType = "bullish",
                                       timeout:dt.timedelta = dt.timedelta(days=3),
                                       min_time :dt.timedelta = dt.timedelta(hours=3),
                                       betweenCandles_maxPeakDist:float = 0.015,
                                       minC1_size:float|None = None,
                                       minC2_size:float|None = 100, 
                                       ignore_timeFilter:bool = False,
                                       ignore_C1C2_sizeFilter:bool = False,
                                       ignore_lowestlowDist_filter:bool = False, **kwargs
                                       ):
        
        assert C1_Type != C2_Type, "C1 and C2 candle type must be diffrent"
        cols = ['Open', 'High', 'Low', 'Close', 'Volume', "Datetime"]
        df_ = (self.df if df.empty else df).copy()
        if "Datetime" not in df_.columns: df_["Datetime"] = df_.index
        df_ = df_[cols].copy()
        if "Datetime" not in df_.index.dtype.name.lower(): 
            df_.set_index("Datetime", inplace = True, drop = False) 
        C1_dict = self._GetCrossedFracts_Candles(Price = Price, df = df, 
                                                 candle_type = C1_Type,
                                                 ignore_HighLow = kwargs.get("ignore_HighLow", True))
        C2_dict = self._GetCrossedFracts_Candles(Price = Price, df = df,
                                                 candle_type = C2_Type, 
                                                 ignore_HighLow = True)
        assert C1_dict.keys() == C2_dict.keys(), "fract Levels found must be same!"
        levelNames = C1_dict.keys()
        c1, c2 = "_C1", "_C2"
        C1_colNames, C2_colNames = [col+c1 for col in cols], [col+c2 for col in cols]
        # getting C1,C2 pair
        C1C2_candles = {}
        # levelName is the level that candle C1, C2 may cross it (it's float)
        for levelName in levelNames:
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
            C1C2_candles[levelName] = [{"C1":C1[1].to_dict(),"C2":C2[1].to_dict(),"level":levelName} 
                                       for C1, C2 in zip(_C1_df.iterrows(), _C2_df.iterrows())]
        # putting all levels C1, C2s in a single list
        all_C1C2_candles = []
        for C1C2s in C1C2_candles.values(): all_C1C2_candles += C1C2s
        
        # adding some filters to C1C2s
        if not ignore_timeFilter:
            all_C1C2_candles = self.C1C2_time_filter(all_C1C2_candles, timeout = timeout,
                                                    min_time=min_time)
        if not ignore_C1C2_sizeFilter:
            if minC1_size: all_C1C2_candles = self.C1C2_size_filter(all_C1C2_candles, "C1",
                                                                    minC1_size)
            if minC2_size: all_C1C2_candles = self.C1C2_size_filter(all_C1C2_candles, "C2",
                                                                    minC2_size)
        if not ignore_lowestlowDist_filter:
            all_C1C2_candles = self.C1C2_minDistOFBetweenCandle_filter(all_C1C2_candles,
                                                            betweenCandles_maxPeakDist, df_)
        return all_C1C2_candles
    
    
    
    def FindAllC1C2_Candles_FromPrice(self, *arg, **kwargs):
        
        all_C1C2s = []
        if kwargs["ignore_HighLow"]: 
            C1C2s_noHighLow = self._FindAllC1C2_Candles_FromPrice(*arg, **kwargs)
            all_C1C2s += C1C2s_noHighLow
        else: 
            C1C2s_HighLow = self._FindAllC1C2_Candles_FromPrice(*arg, **kwargs)
            kwargs["ignore_HighLow"] = True
            C1C2s_noHighLow = self._FindAllC1C2_Candles_FromPrice(*arg, **kwargs)
            all_C1C2s += C1C2s_HighLow
            all_C1C2s += C1C2s_noHighLow
            
        all_C1C2s = self.rm_repeated_C1C2_pairs(all_C1C2s)
        all_C1C2s = sorted(all_C1C2s, key = lambda x: x["C2"]["Datetime"])
        return all_C1C2s
    
    
    def rm_repeated_C1C2_pairs(self, C1C2s: list[dict[str]]):
        C1s = [C1C2["C1"] for C1C2 in C1C2s]
        C2s = [C1C2["C2"] for C1C2 in C1C2s]
        for C1, C2, C1C2 in zip(C1s, C2s, C1C2s):
            while C1C2s.count(C1C2)>1: C1C2s.remove(C1C2)
        return C1C2s
    
    
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
    
    
class C1C2s:
    
    @typechecked
    def __init__(self, c1c2s: list[dict[str]]) -> None:
        self._c1c2s = c1c2s
        self.rm_repeated_pairs().rm_repeated_C1s().rm_repeated_C2s()
        self.sort()
        
    @property
    def c1c2s(self):
        return self._c1c2s
    
    @property
    def values(self):
        return self.c1c2s
    
    def rm_repeated_pairs(self):
        for C1C2 in self.c1c2s: 
            while self.c1c2s.count(C1C2) > 1: self.c1c2s.remove(C1C2)        
        return self
    
    
    def rm_repeated_C1s(self):
        C1s = self.C1s 
        for C1, C1C2 in zip(C1s, self.c1c2s):
            while C1s.count(C1) > 1:
                C1s.remove(C1)
                self.c1c2s.remove(C1C2)
        return self
    
    
    def rm_repeated_C2s(self):
        C2s = self.C2s 
        for C2, C1C2 in zip(C2s, self.c1c2s):
            while C2s.count(C2) > 1:
                C2s.remove(C2)
                self.c1c2s.remove(C1C2)
        return self
    
    
    def mixPeakDist_FromC1C2_filter(self, minDist: float = 0.015, 
                                dataframe: pd.DataFrame = pd.DataFrame(), 
                                inplace: bool = True):

        candleType_col = "CandleType"
        df_ = (dataframe).copy()
        df_[candleType_col] = Utils.add_candleType(df_)
        all_C1C2s = []
        for C1C2 in self.c1c2s:
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
        if inplace: self.c1c2s = all_C1C2s
        return all_C1C2s
            
    
    
    @property
    def C1s(self):
        return [C1C2["C1"] for C1C2 in self.c1c2s]
    
    @property
    def C2s(self):
        return [C1C2["C2"] for C1C2 in self.c1c2s]
    
    def sort(self):
        self.c1c2s = sorted(self.c1c2s, key= lambda x: x["C2"]["Datetime"])
        return self
    
    @property
    def last(self):
        return self.c1c2s[-1]
    
    def __repr__(self) -> str:
        return f"{self.c1c2s}"
    
    def __str__(self):
        return f"{self.c1c2s}"
    
    
    
        
        
    