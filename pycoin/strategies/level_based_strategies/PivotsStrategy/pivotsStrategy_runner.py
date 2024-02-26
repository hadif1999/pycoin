from pycoin.strategies import Pivot_Strategy_BASE
from time import time, sleep
from pycoin.risk_management.eval_leverage_amount import Leverage_Amount
from typeguard import typechecked
from asyncer import asyncify, syncify



class Run_PivotStrategy:
    
    @typechecked
    def __init__(self, *, symbol:str, totalCash:float, APIkeys_dir:str|None = None,
                 APIkeys_File:str|None = None, leverage:int = 1, isDemo:bool = True,
                 pivotsType:str = "weekly", interval:str = "30m", min_C1C2_dist:int = 0,
                 API_key:str|None = None, Secret_key:str|None = None,
                 read_APIkeys_fromFile: bool = False,
                 read_APIkeys_fromEnv = True, 
                 UpdateTime_Interval:int = 2*60, max_init_SL_pct:float|int = 2,
                 max_SL_dist:int = 3, max_TP_dist:int = 10) -> None:
        
        self.strategy = Pivot_Strategy(symbol = symbol, interval = interval, isdemo = isDemo,
                                       pivots_type = pivotsType, APIkeys_dir = APIkeys_dir,
                                       APIkeys_File = APIkeys_File, API_key=API_key,
                                       Secret_key=Secret_key, 
                                       read_APIkeys_fromFile = read_APIkeys_fromFile,
                                       read_APIkeys_fromEnv = read_APIkeys_fromEnv)
        
        self.isdemo = isDemo
        self.symbol = symbol
        self.total_cash = totalCash
        self.pivots_type = pivotsType
        self.interval = interval
        self.min_C1C2_dist = min_C1C2_dist
        self.UpdateTime_Interval = UpdateTime_Interval
        self.max_init_pct = max_init_SL_pct
        self.max_SL_dist = max_SL_dist
        self.max_TP_dist = max_TP_dist 
        self.leverage = leverage 
        self.SL_counter = 0
        self.TP_counter = 0
        self.C1 = None
        self.C2 = None
        self.crossed_pivot = None
    
        
    @property
    def zero_counters(self):
        self.SL_counter = self.TP_counter = 0
    
    @property
    def resetParams(self):
        self.C1 = self.C2 = self.crossed_pivot = None
    
    @property
    def reached_SL(self):
        if not self.strategy.SL: return False
        if self.strategy.side == "LONG" and self.strategy.last_close <= self.strategy.SL: return True
        elif self.strategy.side == "SHORT" and self.strategy.last_close >= self.strategy.SL: return True
        return False
    
    @property
    def reached_TP(self):
        if not self.strategy.TP: return False
        if self.strategy.side == "LONG" and self.strategy.last_close >= self.strategy.TP: return True
        elif self.strategy.side == "SHORT" and self.strategy.last_close <= self.strategy.TP: return True
        return False

    
    @property
    def update_position_SLTP(self):
        posAmount = self.strategy.market._CurrentSymbol_TOTAL_posAmt
        if posAmount > 0: side = "LONG"
        elif posAmount < 0: side = "SHORT"
        amount = abs(posAmount)
        self.strategy.market._add_SL(SL = self.strategy.SL, quantity=amount, PositionSide=side)
        self.strategy.market._add_TP(TP = self.strategy.TP, quantity=amount, PositionSide=side)
        
    @property    
    def isHigherClose(self):
        return True if self.strategy.last_close > self.strategy.df_lastPivots.close.iloc[-2] else False


    def thereisLONG(self):
        return self.strategy.market._CurrentSymbol_LONG_posAmt > 0


    def thereisSHORT(self):
        return self.strategy.market._CurrentSymbol_SHORT_posAmt > 0
    
    
    def update_data(self, retries:int = 5, delay_sec:int = 2):
        tries = 1
        while tries != retries:
            try: 
                self.strategy.update_pivots
                return
            except: 
                if tries == retries: 
                    raise SystemError("couldn't download data, check your internet connection or proxy")
                print(f"\n**updating data failed trying again in {delay_sec} seconds")
                sleep(delay_sec)
                tries+=1
                continue
        else: raise SystemError("\n**couldn't download data, check your internet connection or proxy\n\n")
        
        
    @property
    def log(self):
        print(f"{self.symbol}, last close:{self.strategy.last_close}, current {self.pivots_type} pivot:{self.strategy.last_pivots}")
    
    
    @property
    def posLog(self):
        total_positions = self.strategy.market._CurrentSymbol_TOTAL_posAmt 
        # if total_positions != 0 :
        print(f"{self.symbol}, current active amounts: {total_positions}, SL:{self.strategy.SL}, TP:{self.strategy.TP}, last_close:{self.strategy.last_close}")
    
    
    
    def RUN(self):

        res = self.strategy.find_LastC1C2_candles(self.min_C1C2_dist, self.strategy.df_lastPivots)

        if None not in res:
            self.C1, self.C2, self.crossed_pivot = res
            
            if self.strategy.side == "LONG":
                if self.thereisLONG():
                    self.zero_counters
                    self.strategy.clear_SL_TPs
                    self.strategy.define_init_SLTPs( self.strategy.df_lastPivots.iloc[self.C2], 
                                                     self.crossed_pivot, self.max_init_pct)
                    self.update_position_SLTP
                    sleep(self.UpdateTime_Interval)
                    return
                
                elif isThereSHORT:
                    self.strategy.market._close_all_positions
                    self.zero_counters
                    self.strategy.clear_SL_TPs
                risk = Leverage_Amount(self.strategy.last_close, "LONG", self.strategy.SL, 
                                       self.strategy.TP, self.max_init_pct, leverage = self.leverage)
                amount = risk.eval_amount(self.total_cash)
                
                last_order = self.strategy.LONG(quantity = amount, SL = self.strategy.SL, 
                                                  TP = self.strategy.TP, leverage = self.leverage)
                
                
            elif self.strategy.side == "SHORT":
                if isThereSHORT:
                    self.zero_counters
                    self.strategy.clear_SL_TPs
                    self.strategy.define_init_SLTPs(self.strategy.df_lastPivots.iloc[self.C2],
                                                    self.crossed_pivot,
                                                    self.max_init_pct)
                    self.update_position_SLTP
                    sleep(self.UpdateTime_Interval)
                    return
                
                elif isThereLONG:
                    self.strategy.market._close_all_positions
                    self.zero_counters
                    self.strategy.clear_SL_TPs
                risk = Leverage_Amount(self.strategy.last_close, "SHORT", self.strategy.SL,
                                       self.strategy.TP, leverage = self.leverage) 
                amount = risk.eval_amount(self.total_cash)
                last_order = self.strategy.SHORT(quantity = amount, SL = self.strategy.SL,
                                                 TP = self.strategy.TP, leverage = self.leverage)
                
                
        if self.strategy.market._CurrentSymbol_TOTAL_posAmt != 0:
            if None in [self.strategy.SL, self.strategy.TP] and None not in [self.C1, self.C2, 
                                                                             self.crossed_pivot]:
                self.strategy.define_init_SLTPs(self.strategy.df_lastPivots.iloc[self.C2],
                                                self.crossed_pivot, self.max_init_pct)
                self.update_position_SLTP
                self.zero_counters
                
            elif self.reached_TP:
                self.strategy.update_SLTPs(self.strategy.last_close)
                self.update_position_SLTP
                self.zero_counters
                
            if None not in [self.strategy.SL, self.strategy.TP]:
                if self.reached_SL: self.SL_counter += 1
                elif self.reached_TP: self.TP_counter += 1
                else: self.zero_counters
                
                SL_cond = self.SL_counter >= self.max_SL_dist
                TP_cond = self.TP_counter >= self.max_TP_dist
                
                isThereLONG, isThereSHORT = (self.strategy.market._CurrentSymbol_LONG_posAmt !=0, 
                                             self.strategy.market._CurrentSymbol_SHORT_posAmt !=0)
                long_cond = isThereLONG and not self.isHigherClose
                short_cond = isThereSHORT and self.isHigherClose
                
                if (long_cond or short_cond) and (SL_cond or TP_cond):
                    self.strategy.market._close_all_positions(False)
                    self.zero_counters
                    self.strategy.clear_SL_TPs
                    
        else:
            self.zero_counters
            self.strategy.clear_SL_TPs
            self.strategy.clear_data
        
    
