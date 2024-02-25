from ...data_gathering import Binance_KlineData
import pandas as pd
from ...order_making import Bingx
from ._Levels_evaluator import _Levels
import datetime as dt

class Fract_Levels(_Levels):
    
    def __init__(self,*, symbol:str, interval: str, platform: str = "bingx",
                 start_time:dt.datetime|int = None) -> None:
        
        super().__init__(symbol, interval, platform, start_time = start_time)
        
        self.order_manager = Order_Manager(Bingx(self.symbol) if self.platform == "bingx"
                                           else Kucoin(self.symbol))
        self.SL_long = None
        self.TP_long = None
        self.SL_short = None
        self.TP_short = None
        
    def run_Fract_strategy(self):
        pass
        
    