from typing import Any


import numpy as np

class Leverage_Amount:
    def __init__(self, entered_price:float, order_side:str, 
                 stoploss:float = None, profit_level:float = None, 
                 max_loss_percent:float = None, leverage:int = None):
        
        if stoploss is None and profit_level is None:
            raise ValueError("stoploss and profit_level must have value !")
        self.stoploss = stoploss
        self.profit_level = profit_level
        self.order_side = order_side
        self.max_loss_percent = max_loss_percent
        self.entered_price = entered_price
        self.leverage = leverage 
        self.amount = None
        
    def __call__(self, **kwargs):
        self.entered_price = kwargs.get("entered_price", self.entered_price)
        self.order_side = kwargs.get("order_side", self.order_side)
        self.stoploss = kwargs.get("stoploss", self.stoploss)
        self.profit_level = kwargs.get("profit_level", self.profit_level)
        self.max_loss_percent = kwargs.get("max_loss_percent", self.max_loss_percent)
        
    
    @property
    def isLONG(self):
        return True if self.order_side == "LONG" else False
    
    @property
    def isSHORT(self):
        return True if self.order_side == "SHORT" else False
    
    
    def eval_leverage(self, max_loss_percent:float = None):
        if self.max_loss_percent == None and max_loss_percent == None:
            raise ValueError("max loss must defined!")
        
        if max_loss_percent != None: self.max_loss_percent = max_loss_percent
        
        if self.max_loss_percent > 1 or self.max_loss_percent < 0:
            raise ValueError("max_loss_percent must be in 0 and 1")
        
        
        if self.isLONG or self.isSHORT:
            market_change_loss = np.abs((self.entered_price - self.stoploss)/self.entered_price)*100.0
            leverage  =  self.max_loss_percent // market_change_loss
            self.leverage = leverage
        else:
            raise ValueError("entered order_side is not valid.")
        return leverage
    
    
    def eval_risk_to_reward(self):
        return np.abs(self.entered_price-self.stoploss) / np.abs(self.entered_price-self.profit_level)
    
    
    def eval_amount(self, enterance_fund:float):
        if self.leverage == None: raise ValueError("leverage must evaluated first")
        return (enterance_fund * self.leverage)/self.entered_price
            
        
        