from typing import Literal
import pandas as pd
from pycoin import KlineData_Fetcher
import datetime as dt


class _StrategyBASE:
    
    def __init__(self, symbol:str|None = None, timeframe:str|None = None,
                 data_exchange:str = "binance",
                 start_time:dt.datetime|None|int = None,
                 dataName_format:str = "{symbol}|{exchange}|{timeframe}",
                 **kwargs) -> None:
        
        #  assigning object parametres such as self.symbol, self.interval
        if timeframe: self.timeframe = self.interval = timeframe
        self.start_time = start_time
        self.kwargs = kwargs
        if symbol: self.symbol:str = symbol.upper().replace("-", '/')
        self.KlineData_gatherer = KlineData_Fetcher
        self.data_exchange = data_exchange.lower()
        self.df = pd.DataFrame() # main dataframe
        self.dataName_format = dataName_format
        self.dataName = dataName_format.format(symbol = self.symbol, 
                                                exchange = data_exchange, 
                                                timeframe = self.interval)
            
        self.SL, self.TP = None, None
        self.side: Literal["LONG", "SHORT"] = None
        self.plotter = None
        
    
    def __getattr__(self, name):
        return None
        

    @property
    def update_data(self):
        print(f"\n\nfetching OHLCV data for {self.dataName}\n")
        self.dataframe = self.KlineData_gatherer(symbol=self.symbol,
                                                 data_exchange=self.data_exchange,
                                                 timeframe=self.timeframe,
                                                 since=self.start_time,
                                                 **self.kwargs)
        print("done\n")
        self.dataframe.Name = self.dataName
        return self.dataframe
    
    
    def plot(self, **kwargs):
        from pycoin.plotting import Market_Plotter
        self.plotter = Market_Plotter(self.df)
        return self.plotter.plot_market(**kwargs)

    
    @property
    def df(self):
        return self.dataframe
    
    @df.setter
    def df(self, new_df):
        assert isinstance(new_df, pd.DataFrame), "input must be dataframe"
        self.dataframe = new_df
        
        
    def add_candleType(self, inplace: bool = True):
        df_ = self.df.copy()
        cond = df_.Close > df_.Open
        df_.loc[cond, "candleType"] = 1
        df_.loc[~cond, "candleType"] = -1
        if inplace: self.df = df_
        return df_["candleType"]
    
    
    @property
    def LastClose(self):
        return self.df.Close.iloc[-2]
    
    @property
    def TickerClose(self):
        return self.df.Close.iloc[-1]
    
    @property
    def remove_SLTP(self):
        self.SL = self.TP = None
        

    def getBulish_CrossedPrice(self, Price:float) -> pd.DataFrame:
        cond = (self.df.Close > Price) & (self.df.Open < Price)
        return self.df.loc[cond, :]
    
    
    def getBearish_CrossedPrice(self, Price: float) -> pd.DataFrame:
        cond = (self.df.Close < Price) & (self.df.Open > Price)
        return self.df.loc[cond, :]
    
    
    def isLastCandle_CrossedPrice(self, Price):
        cond1 = self.getBearish_CrossedPrice(Price).iloc[-1].Close <= self.LastClose
        cond2 = self.getBulish_CrossedPrice(Price).iloc[-1].Close >= self.LastClose
        return cond1 or cond2 
    
    
    def update_SLTP(self, SL: float, TP: float):
        self.SL, self.TP = SL, TP
        
    @property
    def isSHORT(self):
        return self.side.upper() == "SHORT"
    
    @property
    def isLONG(self):
        return self.side.upper() == "LONG" 
    
    @isSHORT.setter
    def isSHORT(self, val):
        assert isinstance(val, bool), "input can be bool type"
        self.side = "SHORT"
    
    @isLONG.setter
    def isLONG(self, val: bool):
        assert isinstance(val, bool), "input can be bool type"
        self.side = "LONG"
    
    def reached_SL(self):
        cond1 = self.isLONG and self.LastClose < self.SL
        cond2 = self.isSHORT and self.LastClose > self.SL
        return cond1 or cond2
    
    def reached_TP(self):
        cond1 = self.isLONG and self.LastClose > self.TP
        cond2 = self.isSHORT and self.LastClose < self.TP
        return cond1 or cond2    
  
    
    