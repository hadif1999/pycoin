from dataclasses import dataclass

@dataclass    
class fixed_StopLoss:
    """fixed stoploss can implemented either by delta price from current price or by percent. 
    """    
    value:float
    by_DeltaPrice:bool = True
    LONG_SL_amount:float = None
    SHORT_SL_amount:float = None
    
    def __post_init__(self):
        if not self.by_DeltaPrice and not 0 <= self.value <= 100: 
            raise ValueError("fixed stoploss can be either by distance or percentage")
        self.value = float(self.value)
        assert type(self.value) == float , "value is not float"
        
    def get_StopLoss(self, from_price:float):
        """get stoploss for long and short positions from given price.

        Args:
            from_price (float): refrence price, can be Open, High, Low, etc.

        Returns:
            tuple : long stoploss, short stoploss 
        """        
        if self.by_DeltaPrice: SL_long, SL_short = (from_price - self.value, from_price + self.value)
        else:SL_long, SL_short = (from_price-(self.value/100)*from_price,
                                  from_price+(self.value/100)*from_price)
        return SL_long, SL_short
    
    
@dataclass
class fixed_ProfitLevel:
    """fixed profitLevel can implemented either by delta price from current price or by percent. 
    """ 
    value:float
    by_DeltaPrice:bool = True
    LONG_TP_amount:float = None
    SHORT_TP_amount:float = None

    def __post_init__(self):
        if not self.by_DeltaPrice and not 0 <= self.value <= 100: 
            raise ValueError("fixed profitLevel can be either by distance or percentage")
        self.value = float(self.value)
        assert type(self.value) == float , "value is not float"
        
        
    def get_ProfitLevel(self, from_price:float):
        """get profitLevel for long and short positions from given price.

        Args:
            from_price (float): refrence price, can be Open, High, Low, etc.

        Returns:
            tuple : TP_long, TP_short """
        if self.by_DeltaPrice: TP_long, TP_short = (from_price + self.value, from_price - self.value)
        else:TP_long, TP_short = (from_price+(self.value/100)*from_price, 
                                  from_price-(self.value/100)*from_price)
        return TP_long, TP_short
    
    
@dataclass    
class trailing_StopLoss:
    pass


@dataclass
class trailing_ProfitLevel:
    pass
        