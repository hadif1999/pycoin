import platform

from attr import dataclass
from tenacity import retry
from pycoin import KlineData_Fetcher

from pycoin.order_making import Bingx
from backtesting import Backtest, backtesting, Strategy
from backtesting._util import _Indicator as next_array
import datetime as dt

class SMA_Strategy(object):
    
    active_positions = []
    
    def __init__(self, short_window:int, long_window:int, symbol:str, interval:str,
                 platform:str = "bingx", start_datatime: dt.datetime|int = None ) -> None:
        """a simple SMA strategy, if short term sma is above long term sma get a long position,
        else get a short position with specified quantity, also TP and SL can be implemented,
        if arrived to a SL order it will close the whole position and wait until a opposite signal to enter.
        this strategy is implemented in market type orders.
        
        Args:
            short_window (int): short term sma size
            long_window (int): long term sma size
            symbol (str): symbol for example 'BTC-USDT'
            interval (str): run strategy on specifed interval (note that diffrent platforms have diffrent interval str)
            platform (str, optional): platform to trade on and data gathering. Defaults to "bingx".
        """        
        
        if short_window >= long_window : raise ValueError("short period SMA can't have larger window than long SMA")

        super().__init__(symbol, interval, platform)
        self.long_sma = long_window
        self.short_sma = short_window
        
        self.start_datetime = start_datatime
        
        platform_obj = Bingx(self.symbol) if self.platform.lower() == "bingx" else Kucoin(self.symbol)
        self.order_manager = Order_Manager(platform_obj = platform_obj) 
        self.update_market_data
        
        self.SL_long = None
        self.TP_long = None
        self.SL_short = None
        self.TP_short = None
        
        
    @property
    def update_market_data(self): 
        self.download_kline_as_df(verbose = True, inplace = True, datetime_as_index = True,
                                  startAt = self.start_datetime)
        
    @property
    def eval_SMA_trend(self):
        trend = Trend_Evaluator(self)
        self.update_market_data
        self.SMA_trend, self.current_trend = trend.eval_trend_with_MAs("close",
                                                                       [self.short_sma, self.long_sma])
        return self.SMA_trend, self.current_trend
        
    @property
    def get_SMA_series(self):
        self.eval_SMA_trend
        return self.df[f"MA{self.short_sma}"], self.df[f"MA{self.long_sma}"]
    

    def current_price(self):
        return self.order_manager.get_ticker["lastPrice"]
    
    def current_open(self):
        return self.order_manager.get_ticker["openPrice"]
    
    def current_high(self):
        return self.order_manager.get_ticker["highPrice"]
    
    def current_low(self):
        return self.order_manager.get_ticker["lowPrice"]
    
    @property
    def current_fee(self):
        self.order_manager.get_current_fee_percent/100
        
    def run_SMA_strategy(self,*, quantity:float, SL:fixed_StopLoss = None, TP:fixed_ProfitLevel = None,
                         TP_SL_ref = current_price, leverage:int = 1 ):
        """run a SMA strategy, it's do the process for one loop and must run in a while True loop.
        SL and TP can be implemented with stoploss classes such as fixed_StopLoss.

        Args:
            quantity (float): quantity of target symbol to trade.
            SL (fixed_StopLoss, optional): StopLoss object. Defaults to None.
            TP (fixed_ProfitLevel, optional): TP object. Defaults to None.
            TP_SL_ref (_type_, optional): refrence of SL and TP orders. Defaults to current_price.
            leverage (int, optional): leverage. Defaults to 1.

        Returns:
            position_detail
        """        
        
        SMA_trend, current_trend = self.eval_SMA_trend

        if current_trend == 1 :
            if self.order_manager.there_is_active_Long_pos: return
            elif self.order_manager.there_is_active_Short_pos: 
                self.order_manager.close_all_positions(confirm_by_user = False)   
                   
            SL_long, SL_short = SL.get_StopLoss( TP_SL_ref() ) if SL != None else (None, None)
            TP_long, TP_short = TP.get_ProfitLevel( TP_SL_ref() ) if TP != None else (None, None)    
            position_detail = self.LONG(quantity = quantity, SL = SL_long, 
                                        TP = TP_long, SL_amount = SL.LONG_SL_amount,
                                        TP_amount = TP.LONG_TP_amount, leverage = leverage)
            
        elif current_trend == -1 :
            if self.order_manager.there_is_active_Short_pos: return
            elif self.order_manager.there_is_active_Long_pos: 
                self.order_manager.close_all_positions(confirm_by_user=False)
                
            SL_long, SL_short = SL.get_StopLoss( TP_SL_ref() ) if SL != None else (None, None)
            TP_long, TP_short = TP.get_ProfitLevel( TP_SL_ref() ) if TP != None else (None, None)    
            position_detail = self.SHORT(quantity = quantity, SL = SL_short,
                                         TP = TP_short, SL_amount = SL.SHORT_SL_amount,
                                         TP_amount = TP.SHORT_TP_amount, leverage = leverage)
            
        else: self.order_manager.close_all_positions(confirm_by_user=False)
        
        self.active_positions.append(position_detail)
        return position_detail
        
    
    def LONG(self,*, quantity:float, SL:float = None, TP:float = None, SL_amount:float = None, 
             TP_amount:float = None, leverage:int = 1 ):
        
        if SL != None:
            if SL >= self.current_price : raise ValueError("in a long position SL < current_price < TP")
            self.SL_long = SL
            
        if TP != None: 
            if TP<= self.current_price: raise ValueError("in a long position SL < current_price < TP")
            self.TP_long = TP
            
        return self.order_manager.place_order(position_side = "LONG", quantity = quantity,
                                              order_type = "market", stopLoss = SL,
                                              profitLevel = TP, stopLoss_quantity = SL_amount,
                                              profitLevel_quantity = TP_amount, leverage = leverage)

    
    def SHORT(self,*, quantity:float, SL:float = None, TP:float = None, SL_amount:float = None, 
             TP_amount:float = None, leverage:int = 1):
        
        if SL != None:
            if SL <= self.current_price: raise ValueError("in a short position TP < current_price < SL")
            self.SL_short = SL
        if TP != None:
            if TP >= self.current_price: raise ValueError("in a short position TP < current_price < SL")
            self.TP_short = TP
        
        return self.order_manager.place_order(position_side = "SHORT", quantity = quantity,
                                              order_type = "market",stopLoss = SL,
                                              profitLevel = TP , stopLoss_quantity = SL_amount,
                                              profitLevel_quantity = TP_amount, leverage = leverage)
    
    

    def close_all_positions(self, just_this_symbol:bool = False, confirm_by_user = True):
        self.active_positions = []
        return self.order_manager.close_all_positions(just_this_symbol, confirm_by_user)
    
    
    def run_backtest(self, *, init_cash:float = 100000, fee:float = 0.0005,
                     start_datetime:dt.datetime|int = None,leverage:int = 1, 
                     SL:fixed_StopLoss = None,  TP:fixed_ProfitLevel = None, 
                     LONG_ref:str = "Close", SHORT_ref:str = "Close", 
                     ncandles_Wait_Before_NewPos:int = 5):
        
        if start_datetime : 
            self.start_datetime = start_datetime
            self.download_kline_as_df(startAt = start_datetime,
                                      verbose = True, inplace = True,
                                      datetime_as_index = True)
        
        backtest = SMA_backtesting(self)
        bt = backtest.make_strategy(init_cash = init_cash, fee = fee, leverage = leverage, 
                                    SL = SL, TP = TP, LONG_ref = LONG_ref, SHORT_ref = SHORT_ref,
                                    ncandles_Wait_Before_NewPos = ncandles_Wait_Before_NewPos )
        result = bt.run()
        bt.plot()
        self.backtest = bt
        return result
    


class SMA_backtesting :
    def __init__(self_, SMA_strategy_obj:SMA_Strategy) -> None:
        self_.trend = Trend_Evaluator(SMA_strategy_obj)
        
        self_.SMA_strategy_obj = SMA_strategy_obj
        self_.short_window = SMA_strategy_obj.short_sma
        self_.long_window = SMA_strategy_obj.long_sma
        self_.df = SMA_strategy_obj.df
        
    # SL and TP in % for now
    def make_strategy(self_, *, init_cash:int = 10000, fee:float = 0.0005, 
                      leverage:int = 1, SL:fixed_StopLoss = None, TP:fixed_ProfitLevel = None, 
                      LONG_ref:str = "Close", SHORT_ref:str = "Close",
                      ncandles_Wait_Before_NewPos:int = 5) -> Backtest:
        
        class SMA_strategy(Strategy):
            
            n1 = self_.short_window
            n2 = self_.long_window
            
            def init(self):
                # evaluating indicators and other params
                
                trend, _ = self_.trend.eval_trend_with_MAs(windows = [self.n1, self.n2]) 
                
                self.trend = next_array(trend, name = "trend")
                self.SL_long = self.SL_short = self.TP_long = self.TP_short = None
                self.i = 0
                
            def next(self):
                # defining when to buy and sell                
                if self.trend[-1] == 1 :
                    if self.position.is_short: self.position.close()
                    elif self.position.is_long: return
                    self.SL_long, self.SL_short = SL.get_StopLoss( self.data[LONG_ref][-1] ) if SL != None else (None, None)
                    self.TP_long, self.TP_short = TP.get_ProfitLevel( self.data[LONG_ref][-1] ) if TP != None else (None, None)  
                    print(f"\nLONG order executed -> close:{self.data.Close[-1]}, SL_long:{self.SL_long}, TP_long:{self.TP_long}")
                   
                    if self.i >= ncandles_Wait_Before_NewPos:
                        self.buy(sl = self.SL_long , tp = self.TP_long)
                        self.i = 0
            
                elif self.trend[-1] == -1:
                    if self.position.is_long: self.position.close()
                    elif self.position.is_short: return
                    self.SL_long, self.SL_short = SL.get_StopLoss( self.data[SHORT_ref][-1] ) if SL != None else (None, None)
                    self.TP_long, self.TP_short = TP.get_ProfitLevel( self.data[SHORT_ref][-1] ) if TP != None else (None, None)
                    print(f"\nSHORT order executed -> close:{self.data.Close[-1]}, SL_short:{self.SL_short}, TP_short:{self.TP_short}")
                    
                    if self.i >= ncandles_Wait_Before_NewPos:
                        self.sell(sl = self.SL_short, tp = self.TP_short)
                        self.i = 0
                    
                else: self.position.close()
                self.i += 1
                    
        self_.backtest = Backtest(self_.SMA_strategy_obj.case_col_names(self_.df, inplace = False),
                                  SMA_strategy,cash = init_cash,
                                  commission = fee, margin = 1/leverage)
        
        return self_.backtest
    
    
    
        
    
        
        
        
            
    