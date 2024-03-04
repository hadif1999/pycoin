from pycoin import KlineData_Fetcher
from pycoin.order_making import Bingx
from . import _Levels
import datetime as dt
import pandas as pd
from .. import dataTypes
from pycoin import Utils

class Fract_Levels(_Levels):
    
    def __init__(self,*, symbol:str, interval: str, APIkeys_dir:str|None = None,
                 find_onIntervals: list[str] = ["1d", "1w"],
                 APIkeys_File:str|None = None, API_key:str|None = None,
                 Secret_key:str|None = None, exchange:str = "bingx",
                 read_APIkeys_fromFile: bool = False, start_time:dt.datetime|int = None,
                 read_APIkeys_fromEnv: bool = True, isdemo:bool = True, 
                 data_exchange:str = "binance", **kwargs) -> None:
        
        super().__init__(symbol = symbol, interval = interval, start_time = start_time,
                         data_exchange = data_exchange, 
                         find_onIntervals = find_onIntervals, **kwargs)
        
    
    
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
    
    
    
    def _GetCrossedFracts_Candles(self, Price: float = None, *,
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
        
        df_ = (self.df if df.empty else df).copy()
        
        nearFracts = self._find_nearest_FractLevels(Price or self.LastClose)
        
        match candle_type.lower():
            case "bullish":
                return {level: Utils.getBulish_CrossedPrice(df_, level) 
                        for level in nearFracts}
            case "bearish":
                return {level: Utils.getBearish_CrossedPrice(df_, level)
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
                                       C1_size:float|None = None,
                                       C2_size:float|None = 100
                                       ):
        
        assert C1_Type != C2_Type, "C1 and C2 candle type must be diffrent"
        cols = ['Open', 'High', 'Low', 'Close', 'Volume', "Datetime"]
        df_ = (self.df if df.empty else df).copy()
        if "Datetime" not in df_.columns: df_["Datetime"] = df_.index
        df_ = df_[cols].copy()
        if "Datetime" not in df_.index.dtype.name.lower(): 
            df_.set_index("Datetime", inplace = True, drop = False) 
        C1_dict = self._GetCrossedFracts_Candles(Price = Price, df = df, candle_type = C1_Type)
        C2_dict = self._GetCrossedFracts_Candles(Price = Price, df = df, candle_type = C2_Type)
        assert C1_dict.keys() == C2_dict.keys(), "fract Levels found must be same!"
        levelNames = C1_dict.keys()
        c1, c2 = "_C1", "_C2"
        C1_colNames, C2_colNames = [col+c1 for col in cols], [col+c2 for col in cols]
        # getting C1,C2 pair
        C1C2_candles = {}
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
            C1C2_candles[levelName] = [{"C1":C1[1].to_dict(), "C2":C2[1].to_dict()} 
                                       for C1, C2 in zip(_C1_df.iterrows(), _C2_df.iterrows())]
        # putting all levels C1, C2s in a single list
        all_C1C2_candles = []
        for C1C2s in C1C2_candles.values(): all_C1C2_candles += C1C2s
        
        # adding some filters to C1C2s
        all_C1C2_candles = self.C1C2_time_filter(all_C1C2_candles, timeout = timeout,
                                                 min_time=min_time)
        if C1_size: all_C1C2_candles = self.C1C2_size_filter(all_C1C2_candles, "C1", C1_size)
        if C2_size: all_C1C2_candles = self.C1C2_size_filter(all_C1C2_candles, "C2", C2_size)
        all_C1C2_candles = self.C1C2_minDistOFBetweenCandle_filter(all_C1C2_candles,
                                                         betweenCandles_maxPeakDist, df_)
        
        all_C1C2_candles = sorted(all_C1C2_candles, key = lambda x: x["C2"]["Datetime"])
        return all_C1C2_candles
    
    
    
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
    
    
    
        
        
    