import os
from typing import Literal

import pandas as pd
from pycoin.strategies.level_based_strategies import _Levels
import datetime as dt
import numpy as np
from backtesting import Backtest
from backtesting.backtesting import Strategy
from bokeh.io import show, save
import shutil as sh
from pycoin import utils
from pycoin.strategies import _strategy_BASE
from pycoin.order_making.exchanges import exchanges
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
                 read_APIkeys_fromEnv: bool = False, isdemo:bool = True, **kwargs) -> None:
        """
        pivot levels strategy based on weekly or monthly pivots.

        Args:
            symbol (str): symbol like "BTC-USDT"
            interval (str): interval based on platform API
            platform (str, optional): "bingx" or "kucoin". Defaults to "bingx".
            pivots_type (str, optional): "weekly" or "monthly" pivots. Defaults to "weekly".
            start_time (dt.datetime | int, optional): start_time to use in backtest. Defaults to None.
        """        
        
        super().__init__(symbol, interval,  start_time = start_time)
        
        
        _API_KEY = os.environ.get("API_KEY", API_key) if read_APIkeys_fromEnv else API_key
        _SECRET_KEY = os.environ.get("SECRET_KEY", Secret_key) if read_APIkeys_fromEnv else Secret_key
         
        exchange_cls = exchanges[ kwargs.get("exchange", "bingx") ]
        
        self.market = exchange_cls(symbol = symbol, isdemo = isdemo, 
                            APIkeys_File = APIkeys_File, APIkeys_dir = APIkeys_dir,
                            API_key = _API_KEY , Secret_key = _SECRET_KEY , 
                            read_APIkeys_fromFile = read_APIkeys_fromFile)
        
        self.interval = self.freq
        
        self.C1_ind = None
        self.C2_ind = None
        self.crossed_pivot = None # the pivot line that C1 and C2 found on
        
        self.pivots_type = pivots_type.lower()
        
        if kwargs.get("init_update"): self.update_pivots
        
        
    
    @property
    def update_pivots(self):
        super().update_pivots
        # below var is the main var to use calculated pivots
        self.last_pivots = (self.last_weekly_pivot if self.pivots_type == "weekly" \
        else self.last_monthly_pivot).copy()
        
        self.all_pivots = self.weekly_pivots if self.pivots_type == "weekly" \
        else self.monthly_pivots
        
        self.df_lastPivots = get_by_datetimeRange(dataframe = self.df ,
                                                  start = self.all_pivots.iloc[-1].datetime) 
        
        
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
        
        pivots_arr = self.last_pivots.copy()
        if not isinstance(pivots_arr, np.ndarray): pivots_arr = np.array(pivots_arr)
        pivots_arr.sort()
        pivots_arr = pivots_arr[::-1]

        # check if they are pivots in long position        
        if all(price > pivots_arr) : return None, pivots_arr[0]
        elif all(price < pivots_arr): return pivots_arr[-1], None
        else: 
            lower_pivot_ind = np.where(price > pivots_arr)[0][0]
            lower_pivot = pivots_arr[lower_pivot_ind]
            upper_pivot = pivots_arr[lower_pivot_ind - 1]
            return upper_pivot, lower_pivot
        
        
    def _GetLastCrossedPivot_candle(self, dataframe:pd.DataFrame = None, candle_type:str = "bullish"):
        """finds last 'bullish'/'bearish' candle that crossed a pivot. 

        Args:
            dataframe (pd.DataFrame, optional): finds candle on this df. Defaults to None.
            candle_type (str, optional): 'bullish' or 'bearish'. Defaults to "bullish".

        Raises:
            ValueError: _description_

        Returns:
            candle_indice, crossed pivot
        """        
        
        try: df_ = dataframe.copy()
        except: df_ = self.df_lastPivots.copy()
        
        last_candle = df_.iloc[-1]
        upper_pivot, lower_pivot = self._find_nearest_pivots(last_candle.close)
        last_crossed_candle_ind, crossed_pivot = None, None
        
        inds = []
        crossed_pivots = []
        
        match candle_type.lower():
                    # get the ind of the nearest bullish or bearish cross and it's pivot
            case 'bullish':
                if upper_pivot != None:
                    upper_cond = (df_.open < upper_pivot) & (df_.close > upper_pivot )
                    if upper_cond.any():
                        ind_up = df_[upper_cond].index[-1]
                        inds.append(ind_up)
                        crossed_pivots.append(upper_pivot)
                if lower_pivot != None:
                    lower_cond = (df_.open < lower_pivot) & (df_.close > lower_pivot )
                    if lower_cond.any(): 
                        ind_low = df_[lower_cond].index[-1] # if it was newer than above found candle
                        inds.append(ind_low)
                        crossed_pivots.append(lower_pivot)
            
            case 'bearish':
                if upper_pivot != None:
                    upper_cond = (df_.close < upper_pivot) & (df_.open > upper_pivot) 
                    if upper_cond.any():
                        ind_up = df_[upper_cond].index[-1]
                        inds.append(ind_up)
                        crossed_pivots.append(upper_pivot)

                if lower_pivot != None:
                    lower_cond = (df_.close < lower_pivot) & (df_.open > lower_pivot)
                    if lower_cond.any():
                        ind_low = df_[lower_cond].index[-1]        
                        inds.append(ind_low)
                        crossed_pivots.append(lower_pivot)
            case _ : 
                raise ValueError("candle_type can be 'bullish' or 'bearish'")
        
        last_crossed_candle_ind = max(inds) if inds != [] else None
        crossed_pivot = crossed_pivots[inds.index(last_crossed_candle_ind)] \
        if last_crossed_candle_ind != None else None
        
        return last_crossed_candle_ind, crossed_pivot
    
    
    # check if last pivots are long position pivots or not
    def _find_side_from_lastCrossed_pivot(self, close_price:float) -> Literal['SHORT', 'LONG']:
        """find position side from input price according to it's nearest pivots 

        Raises:
            ValueError: _description_

        Returns:
            "LONG" or "SHORT"
        """        
        pivots = self.last_pivots.copy()
        if len(pivots) != 5: raise ValueError("number of last pivots is not 5 !")
        
        upper_pivot, lower_pivot = self._find_nearest_pivots(close_price)
        
        if upper_pivot == None: return "SHORT"
        if lower_pivot == None: return "LONG"
        
        bullish_pivots = pivots[:3]
        bearish_pivots = pivots[3:]
        
        if upper_pivot in bullish_pivots: upper_pivot_type = "LONG"
        elif upper_pivot in bearish_pivots:  upper_pivot_type = "SHORT"
        
        if lower_pivot in bullish_pivots: lower_pivot_type = "LONG"
        elif lower_pivot in bearish_pivots: lower_pivot_type = "SHORT"
        
        return lower_pivot_type if lower_pivot_type == upper_pivot_type else "SHORT" 
    
    

    def _get_dfPivots_pair(self, dataframe:pd.DataFrame):
        """returns list of dataframe and corresponding pivots(each pivot is valid for 7 days)
        

        Args:
            dataframe (pd.DataFrame): weekly or monthly dataframe

        Returns:
            dataframe, pivots: dataframe for each pivot
        """        
        
        try: df_ = dataframe.copy()
        except: df_ = self.df.copy()
        
        dfPivot_pair = []
        for i, row in self.all_pivots.iterrows():
            
            pivot_df = get_by_datetimeRange(df_, start = row.datetime,
                                            end = None 
                                            if i == self.all_pivots.index[-1] 
                                            else self.all_pivots.iloc[i+1].datetime)
            pivot_cols = ["low","25%weekly","50%weekly","75%weekly","high"]
            pivots = row[pivot_cols].values
            pivots.sort()
            if not pivot_df.empty: dfPivot_pair.append( (pivot_df, pivots))
        return dfPivot_pair 

                
                
                
    def _plot_C1C2_candles(self, fig = None ,C1_color:str = "orange",
                           C2_color:str = "purple", dataframe:pd.DataFrame = None,
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
        
        try: df_ = dataframe.copy()
        except: df_ = self.df_lastPivots.copy()
        

        C1_init, C2_init = self.C1_ind, self.C2_ind
        
        self.clear_data
        plots = Market_Plotter(self)
        if fig == None: fig = self.plot_pivot(which_pivot = self.pivots_type)
        
        C1_list = []
        C2_list = []
        
        for i in range(1, len(df_)):
            df_temp = df_.iloc[0:i]
            C1_ind, C2_ind, crossed_pivot = self.find_LastC1C2_candles(min_C1C2_dist = kwargs.get("min_C1C2_dist", 2),
                                                                       dataframe = df_temp)
            if C1_ind != None and C2_ind != None: 
                C1_list.append(C1_ind)
                C2_list.append(C2_ind)
        
        C1_list = list(set(C1_list))
        C2_list = list(set(C2_list))
        C1_list.sort()
        C2_list.sort()
        C1_df = df_.iloc[C1_list].reset_index(drop = True, inplace = False)
        C2_df = df_.iloc[C2_list].reset_index(drop = True, inplace = False)
        
        for i, row in C1_df.iterrows():
            dt_data = row.datetime.to_pydatetime().__str__()
            y_data = row.high
            plots.highlight_single_candle(fig, dt_data, C1_color)
            plots.add_text(fig, f"C1-{i}", [dt_data, y_data], True, font_size = 8,
                           font_color = C1_color )
            
        for i, row in C2_df.iterrows():
            dt_data = row.datetime.to_pydatetime().__str__()
            y_data = row.high
            plots.highlight_single_candle(fig, dt_data, C2_color)
            plots.add_text(fig, f"C2-{i}", [dt_data, y_data], True, font_size = 8,
                           font_color = C2_color)
        
        self.C1_ind, self.C2_ind = C1_init, C2_init
        if inplace: self.fig = fig
        return fig
    
    
    
    def Plot_Past_C1C2_Candles(self,*, plot_past_pivots:bool = True ,
                               dataframe:pd.DataFrame = None, **kwargs):
        """plot past C1 C2 candles by plotly.

        Args:
            plot_past_pivots (bool, optional): also plot pivots or not. Defaults to True.
            dataframe (pd.DataFrame, optional): input df, if None self.df will be used. Defaults to None.

        Returns:
            _type_: _description_
        """        
        from ....plotting import Market_Plotter

        lastPivots_init = self.last_pivots.copy()
        df_init = self.df
        try: df_ = dataframe.copy()
        except: df_ = self.df.copy()
        
        dfPivot_pairs = self._get_dfPivots_pair(df_)
        plots = Market_Plotter(self)
        # fig = plots.plot_market(False)
        figs = []
        
        i = 0
        for df_pivot, pivot in dfPivot_pairs:
            self.last_pivots = pivot.copy()
            fig = plots.plot_market(False)
            if plot_past_pivots : fig = self.plot_pivot(fig = fig, pivots_arr = pivot)
            fig = self._plot_C1C2_candles(fig, dataframe = df_pivot, **kwargs)
            i+=1
            figs.append(fig)
        
        self.df = df_init
        self.last_pivots = lastPivots_init.copy()
        [fig.show() for fig in figs]
        return figs
    
    
    
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
    
    
    
    def find_LastC1C2_candles(self, min_C1C2_dist:int = 2, dataframe:pd.DataFrame = None,
                              MaxPercentDistFromC2close:float = 0.0001 ):
        """finds last C1 and C2 candles.

        Args:
            min_C1C2_dist (int, optional): min distance between C1 and C2. Defaults to 2.
            dataframe (pd.DataFrame, optional): finds on this dataframe if given else on self.df . Defaults to None.
            MaxPercentDistFromC2close (float, optional): max distance price from C2 candle
            to still evaluate it as last C2 candle. Defaults to 0.0001.

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """        
        
        try: df_ = dataframe.copy()
        except: df_ = self.df_lastPivots.copy()
        
        side_pivot = self._find_side_from_lastCrossed_pivot(df_.close.iloc[-1])
        
        side = side_pivot
        
        match side.upper():
            case "LONG":
                C1_ind, C1_crossed_pivot = self._GetLastCrossedPivot_candle(df_, "bearish")
                if None in [C1_ind, C1_crossed_pivot]: return None, None, None
                C2_candid_ind, C2_crossed_pivot = self._GetLastCrossedPivot_candle(df_, "bullish")
                if None in [C2_candid_ind, C2_crossed_pivot]: return None, None, None
                # if below conditions are confirmed then last candle is a C2 candle
                C2_cond1 = C1_crossed_pivot == C2_crossed_pivot 
                C2_cond2 = (C2_candid_ind - C1_ind)-1 > min_C1C2_dist 
                C2_cond3 = C2_candid_ind == df_.index[-1] or (abs(df_.iloc[-1].close - df_.iloc[C2_candid_ind].close)/df_.iloc[C2_candid_ind].close)*100 < MaxPercentDistFromC2close
                C2_cond4 = (df_.iloc[C1_ind+1: C2_candid_ind][["close", "open"]] <=
                            C2_crossed_pivot).all().all()
                
                if C2_cond1 and C2_cond2 and C2_cond3 and C2_cond4: 
                    self.C1_ind = C1_ind
                    self.C2_ind = C2_candid_ind
                    self.crossed_pivot = C2_crossed_pivot
                else:
                    self.clear_data
                
            case "SHORT":
                C1_ind, C1_crossed_pivot = self._GetLastCrossedPivot_candle(df_, "bullish")
                if None in [C1_ind, C1_crossed_pivot]: return None, None, None
                C2_candid_ind, C2_crossed_pivot = self._GetLastCrossedPivot_candle(df_, "bearish")
                if None in [C2_candid_ind, C2_crossed_pivot]: return None, None, None
                C2_cond1 = C1_crossed_pivot == C2_crossed_pivot 
                C2_cond2 = (C2_candid_ind - C1_ind)-1 > min_C1C2_dist
                C2_cond3 = C2_candid_ind == df_.index[-1] or (abs(df_.iloc[-1].close - df_.iloc[C2_candid_ind].close)/df_.iloc[C2_candid_ind].close)*100 < MaxPercentDistFromC2close
                C2_cond4 = (df_.iloc[C1_ind+1: C2_candid_ind][["close", "open"]] >= 
                            C1_crossed_pivot).all().all()
                if C2_cond1 and C2_cond2 and C2_cond3 and C2_cond4: 
                    self.C1_ind = C1_ind
                    self.C2_ind = C2_candid_ind
                    self.crossed_pivot = C2_crossed_pivot
                else:
                    self.clear_data
            
            case _: raise ValueError("side not found ! ")
        
        self.side = side_pivot
        return self.C1_ind, self.C2_ind, self.crossed_pivot
    
    
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
        

            
            
                            
                            
                         
    
                
        

        

        
                

                
         

