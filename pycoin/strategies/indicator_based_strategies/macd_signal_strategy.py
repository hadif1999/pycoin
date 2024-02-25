import sys
from ...data_gathering import Binance_KlineData
from ...order_making import Bingx
from backtesting import Backtest
from backtesting._util import _Indicator as next_array
from backtesting.backtesting import Strategy
import warnings
import datetime as dt

class MACD_Signal_Strategy(Binance_KlineData):
    active_positions = []
    
    def __init__(self, *, window_slow:int = 26, window_fast:int = 12, window_sign:int = 9,  
                 symbol:str, interval:str, platform:str = "bingx"):
        
        super().__init__(symbol = symbol, interval = interval, platform = platform)
        
        assert window_slow > window_fast, "slow window must be greater than fast window."
        if window_sign > 9: warnings.warn("window_sign > 9 may not be very good...")
        
        self.window_slow = window_slow 
        self.window_fast = window_fast
        self.window_sign = window_sign
        
        platform_obj = Bingx(self.symbol) if self.platform.lower() == "bingx" else Kucoin(self.symbol)
        self.order_manager = Order_Manager(platform_obj = platform_obj) 
        self.update_market_data
        
        self.SL_long = None
        self.TP_long = None
        self.SL_short = None
        self.TP_short = None
        
        
    @property
    def update_market_data(self): 
        self.download_kline_as_df(verbose = True, inplace = True, datetime_as_index = False,
                                  fill_missing_dates = False)
        
        
    @property
    def eval_MACD_signal_trend(self):
        trend = Trend_Evaluator(self)
        self.update_market_data
        self.MACD_sig_trend, self.last_trend = trend.eval_trend_with_MACD(column = "close",
                                                         window_slow = self.window_slow,
                                                         window_fast = self.window_fast,
                                                         window_sign = self.window_sign,
                                                         drop_MACD_col = True)
        return self.MACD_sig_trend, self.last_trend
    
    
    def run_backtest(self, *, init_cash:float = 100000, fee:float = 0.0005,
                    start_datetime:dt.datetime|int = None,leverage:int = 1, 
                    SL:fixed_StopLoss = None,  TP:fixed_ProfitLevel = None, 
                    LONG_ref:str = "Close", SHORT_ref:str = "Close",
                    ncandles_Wait_Before_NewPos:int = 5):
        

        self.update_market_data
        
        backtest = MACDSignal_Backtesting(self)
        bt = backtest.Make_backtest(init_cash = init_cash, fee = fee, leverage = leverage, 
                                    SL = SL, TP = TP, LONG_ref = LONG_ref, SHORT_ref = SHORT_ref,
                                    ncandles_Wait_Before_NewPos = ncandles_Wait_Before_NewPos)
        result = bt.run()
        bt.plot()
        self.backtest = bt
        return result
    
    
    
class MACDSignal_Backtesting:
    
    def __init__(_self_, MACDSig_strategy_obj:MACD_Signal_Strategy) -> None:
        
        _self_.macd_obj = MACDSig_strategy_obj
        _self_.slow_window = _self_.macd_obj.window_slow
        _self_.fast_window = _self_.macd_obj.window_fast
        _self_.sig_window = _self_.macd_obj.window_sign
        _self_.df = _self_.macd_obj.df
        
    def Make_backtest(_self_, *, init_cash:int = 10000, fee:float = 0.0005, 
                      leverage:int = 1, SL:fixed_StopLoss = None, TP:fixed_ProfitLevel = None, 
                      LONG_ref:str = "Close", SHORT_ref:str = "Close",
                      ncandles_Wait_Before_NewPos:int = 5, NewPos_JustInOpposite_dir:bool = False):
        
        _self_.trend = Trend_Evaluator(_self_.macd_obj)
        
        class MACDSig_bt(Strategy):
            def init(self):
                self.i = 0
                trend, _ = _self_.macd_obj.eval_MACD_signal_trend
                self.trend = next_array(trend)
                self.SL_long = self.SL_short = self.TP_long = self.TP_short = None
                self.last_pos_type = None
                
            def next(self):
                
                if self.trend == 1:
                    if self.position.is_short: self.position.close()
                    elif self.position.is_long: return
                    self.SL_long, self.SL_short = SL.get_StopLoss( self.data[LONG_ref][-1] ) if SL != None else (None, None)
                    self.TP_long, self.TP_short = TP.get_ProfitLevel( self.data[LONG_ref][-1] ) if TP != None else (None, None) 
                    if self.i >= ncandles_Wait_Before_NewPos+1: 
                        self.buy(sl = self.SL_long, tp = self.TP_long)
                        self.i = 0
                    
                elif self.trend == -1:
                    if self.position.is_long: self.position.close()
                    elif self.position.is_short: return
                    self.SL_long, self.SL_short = SL.get_StopLoss( self.data[SHORT_ref][-1] ) if SL != None else (None, None)
                    self.TP_long, self.TP_short = TP.get_ProfitLevel( self.data[SHORT_ref][-1] ) if TP != None else (None, None) 
                    if self.i >= ncandles_Wait_Before_NewPos+1:
                        self.sell(sl = self.SL_short, tp = self.TP_short)
                        self.i = 0
                    
                else: self.position.close()
                
                self.i += 1
                
        bt = Backtest(_self_.macd_obj.case_col_names(_self_.macd_obj.to_datetime_index(_self_.df)),
                      MACDSig_bt, cash = init_cash,
                      commission = fee, margin = 1/leverage)
        return bt
            
        
    