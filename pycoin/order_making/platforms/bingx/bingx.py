
from .._base import _BASE
from ._bingx import _Bingx
from asyncer import asyncify, syncify




# this class is a wrapper to deploy perpetual future of bingx
class Bingx(_Bingx, _BASE):
    
    exchange = broker = "bingx"
    
    
    def __init__(self, *, symbol: str, APIkeys_File: str|None = None, APIkeys_dir: str|None = None,
                 read_APIkeys_fromFile: bool = False, API_key:str|None = None,
                 Secret_key:str|None = None, isdemo: bool = True):
        
        super().__init__(symbol = symbol, isdemo = isdemo, API_key = API_key,
                         Secret_key = Secret_key, APIkeys_File = APIkeys_File,
                         APIkeys_dir = APIkeys_dir, read_APIkeys_fromFile = read_APIkeys_fromFile)
        
    
    @asyncify
    def make_order(self,*, 
                    quantity:float, orderType:str,
                    Price:float|None = None, stopLoss:float|None = None, 
                    positionSide:str|None = None, triggerPrice:float|None = None,
                    stopLoss_quantity:float|None = None, profitLevel:float|None = None,
                    profitLevel_quantity:float|None = None, leverage:int = 1,
                    verifyByUser = True):
        
        return super()._make_order(quantity=quantity, orderType=orderType, Price=Price,
                            stopLoss=stopLoss, positionSide=positionSide,triggerPrice=triggerPrice,
                            stopLoss_quantity=stopLoss_quantity, profitLevel=profitLevel,
                            profitLevel_quantity=profitLevel_quantity, leverage=leverage,
                            verifyByUser=verifyByUser, asDemo=False)
    
    @property
    @asyncify
    def available_markets(self):
        return super().available_markets

    @asyncify
    def open_positions(self, AllSymbols: bool = True):
        return super()._active_positions(AllSymbols)
    
    @asyncify
    def pending_orders(self, AllSymbols: bool = True):
        return super()._pending_orders(AllSymbols)
    
    @asyncify
    def closed_positions(self):
        return super()._closed_positions
    
    @asyncify
    def cancel_orders(self, IDs: list):
        return super()._cancel_orders(IDs)
    
    @asyncify
    def cancel_allOrders(self, AllSymbols:bool = True):
        return super()._cancel_all_orders(AllSymbols)
    
    @asyncify
    def close_position(self, positionSide: str, quantity: float, asdemo: bool = True):
        return super()._close_position(positionSide, quantity, asdemo)
    
    @property
    async def get_currentActive_positionSide(self):
        posAmount = await self.CurrentSymbol_TOTAL_PositionsAmt
        if posAmount > 0: return "LONG"
        elif posAmount < 0: return "SHORT"
    
    @asyncify
    def close_allPositions(self, AllSymbols:bool = True):
        return super()._close_all_positions(AllSymbols)
    
    @property
    @asyncify
    def get_ticker(self):
        return super()._get_ticker
    
    @property
    @asyncify
    def assest_details(self):
        return super()._assest_details
    
    @property
    @asyncify
    def total_balance(self):
        return super()._total_balance
    
    @property
    @asyncify
    def available_margin(self):
        return super()._available_margin
    
    @property
    @asyncify
    def freezed_margin(self):
        return super()._freezed_margin
    
    @asyncify
    def __add_SL(self, quantity:float, SL:float, PositionSide:str):
        return super()._add_SL(SL=SL, quantity=quantity, 
                               PositionSide=PositionSide, asdemo=False)
    
    
    async def add_SL(self, at: float, amount:float|None = None):
        posAmount = await self.CurrentSymbol_TOTAL_PositionsAmt
        if posAmount > 0: side = "LONG"
        elif posAmount < 0: side = "SHORT"
        if not amount: amount = abs(posAmount)
        return await self.__add_SL(quantity = amount, SL = at, PositionSide = side)
    
    
    @asyncify
    def __add_TP(self, quantity:float, TP:float, PositionSide:str):
        return super()._add_TP(TP=TP, quantity=quantity,
                               PositionSide=PositionSide, asdemo = False)
    

    async def add_TP(self, at, amount:float|None = None):
        posAmount = await self.CurrentSymbol_TOTAL_PositionsAmt
        if posAmount > 0: side = "LONG"
        elif posAmount < 0: side = "SHORT"
        if not amount: amount = abs(posAmount)
        return await self.__add_TP(quantity = amount, TP = at, PositionSide = side)
    
    
    @property
    @asyncify
    def current_fee(self):
        return super()._current_fee
    
    @asyncify
    def Change_Leverage(self, side:str, n:int):
        return super()._change_leverage(side, n)
    
    @property
    @asyncify
    def LONG_leverage(self):
        return super()._LONG_leverage
    
    @property
    @asyncify
    def SHORT_leverage(self):
        return super()._SHORT_leverage
    
    @property
    @asyncify
    def maxSHORT_leverage(self):
        return super()._maxSHORT_leverage 
    
    @property
    @asyncify
    def maxLONG_leverage(self):
        return super()._maxLONG_leverage
    
    @property
    @asyncify
    def MarginType(self):
        return super()._marginType
    
    @asyncify
    def Change_MarginType(self, newType:str):
        return super()._change_marginType(newType)
    
    @property
    @asyncify
    def get_24HPriceChangePercent(self):
        return super()._get24H_PriceChangePercent    
    
    @property
    @asyncify
    def get_24HLOWPrice(self):
        return super()._get24H_LOWPrice
    
    @property
    @asyncify
    def get_24HHighPrice(self):
        return super()._get24H_HighPrice
    
    @property
    @asyncify
    def last_price(self):
        return super()._last_price
    
    ########################################### get position Amt for current symbol
    @property
    @asyncify
    def CurrentSymbol_LONG_PositionsAmt(self):
        return super()._CurrentSymbol_LONG_posAmt
    
    
    @property
    @asyncify
    def CurrentSymbol_SHORT_PositionsAmt(self):
        return super()._CurrentSymbol_SHORT_posAmt
    
    
    @property
    @asyncify
    def CurrentSymbol_TOTAL_PositionsAmt(self):
        return super()._CurrentSymbol_TOTAL_posAmt
    

############################ check if there is active pos on current symbol
    @property
    async def IsThere_LONG_posOnCurrentSymbol(self):
        return await self.CurrentSymbol_LONG_PositionsAmt > 0
    
    
    @property
    async def IsThere_SHORT_posOnCurrentSymbol(self):
        return await abs(self.CurrentSymbol_SHORT_PositionsAmt) > 0 
    
######################### All symbols position Amt dict ({symbol:Amt}) #############
    @property
    @asyncify
    def AllSymbols_LONG_PositionsAmt(self):
        return super()._AllSymbols_LONG_posAmt
    
    @property
    @asyncify
    def AllSymbols_SHORT_PositionsAmt(self):
        return super()._AllSymbols_SHORT_posAmt
    
    @property
    @asyncify
    def AllSymbols_SUM_PositionsAmt(self):
        return super()._AllSymbols_SUM_posAmt
    
    
    @property
    @asyncify
    def AllSymbols_PositionsAmt(self):
        return super()._AllSymbols_TOTAL_posAmt
    
############################# orders Amt for current symbol #####
    @property
    @asyncify
    def CurrentSymbol_LONG_OrdersAmt(self):
        return super()._CurrentSymbol_LONG_ordersAmt
    
    @property
    @asyncify
    def CurrentSymbol_SHORT_OrdersAmt(self):
        return super()._CurrentSymbol_SHORT_ordersAmt
    
    @property
    @asyncify
    def CurrentSymbol_TOTAL_OrdersAmt(self):
        return super()._CurrentSymbol_TOTAL_ordersAmt

######################## orders Amt dict ({symbol:Amt}) for all symbols ########  
    @property
    @asyncify
    def AllSymbols_LONG_OrdersAmt(self):
        return super()._AllSymbols_LONG_ordersAmt
    
    @property
    @asyncify
    def AllSymbols_SHORT_OrdersAmt(self):
        return super()._AllSymbols_SHORT_ordersAmt
    
    @property
    @asyncify
    def AllSymbols_OrdersAmt(self):
        return super()._AllSymbols_TOTAL_ordersAmt
    
    @property
    @asyncify
    def AllSymbols_SUM_OrdersAmt(self):
        return super()._AllSymbols_SUM_ordersAmt
    
    ######################### SLTP checker for current symbol #############
    
    @property
    @asyncify
    def CurrentSymbol_PendingSLTPs(self):
        return super()._CurrentSymbol_PendingSLTPs

    @property
    @asyncify
    def CurrentSymbol_LONG_PendingSLTPs(self):
        return super()._CurrentSymbol_LONG_PendingSLTPs
    
    @property
    @asyncify
    def CurrentSymbol_SHORT_PendingSLTPs(self):
        return super()._CurrentSymbol_SHORT_PendingSLTPs
    
    ######################### check SL for current symbol ##############
    @property
    @asyncify
    def CurrentSymbol_PendingSLs(self):
        return super()._CurrentSymbol_PendingSLs
        
    @property
    @asyncify
    def CurrentSymbol_LONG_PendingSLs(self):
        return super()._CurrentSymbol_LONG_PendingSLs
        
    @property
    @asyncify
    def CurrentSymbol_SHORT_PendingSLs(self):
        return super()._CurrentSymbol_SHORT_PendingSLs
        
    ################################ check TP for current symbol #############
    
    @property
    @asyncify
    def CurrentSymbol_PendingTPs(self):
        return super()._CurrentSymbol_PendingTPs
    
    @property
    @asyncify
    def CurrentSymbol_LONG_PendingTPs(self):
        return super()._CurrentSymbol_LONG_PendingTPs
    
    @property
    @asyncify
    def CurrentSymbol_SHORT_PendingTPs(self):
        return super()._CurrentSymbol_SHORT_PendingTPs
        
    
    #######################################check SL TP for all symbols #########
    @property
    @asyncify
    def AllSymbols_PendingSLTPs(self):
        return super()._AllSymbols_PendingSLTPs
    
    @property
    @asyncify
    def AllSymbols_LONG_PendingSLTPs(self):
        return super()._AllSymbols_LONG_PendingSLTPs
    
    @property
    @asyncify
    def AllSymbols_SHORT_PendingSLTPs(self):
        return super()._AllSymbols_SHORT_PendingSLTPs
    
    ########################### check SLs for all symbols ################
    @property
    @asyncify
    def AllSymbols_PendingSLs(self):
        return super()._AllSymbols_PendingSLs
        
    @property
    @asyncify
    def AllSymbols_LONG_PendingSLs(self): 
        return super()._AllSymbols_LONG_PendingSLs
    
    @property
    @asyncify
    def AllSymbols_SHORT_PendingSLs(self): 
        return super()._AllSymbols_SHORT_PendingSLs
        
    
    ########################### check TPs for all symbols ##########
    @property
    @asyncify
    def AllSymbols_PendingTPs(self):
        return super()._AllSymbols_PendingTPs
    
    
    @property
    @asyncify
    def AllSymbols_LONG_PendingTPs(self):
        return super()._AllSymbols_LONG_PendingTPs
        
    
    @property
    @asyncify
    def AllSymbols_SHORT_PendingTPs(self):
        return super()._AllSymbols_SHORT_PendingTPs
        
    ###################################################    
    @asyncify
    def lastClose(self, interval:str):
        return super()._lastClose(interval)
    
    @asyncify
    def lastOpen(self, interval:str):
        return super()._lastOpen(interval)
    
    @asyncify
    def lastHigh(self, interval:str):
        return super()._lastHigh(interval)
    
    @asyncify
    def lastLow(self, interval:str):
        return super()._lastLow(interval)
    
    @asyncify
    def LastCandleTimestamp(self, interval:str, as_datetime:bool):
        return super()._lastCandleTimestamp(interval, as_datetime)
    
    @asyncify
    def LastVolume(self, interval):
        return super()._lastVolume(interval)
    

    
        
    
        
        
        

    
    
    
        
        
        