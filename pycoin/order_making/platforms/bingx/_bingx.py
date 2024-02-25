import os, json, hmac, time, requests
from typing import Any
from hashlib import sha256
from ....utils.utils import current_time
from ...API_manager import API_MANAGER
from typeguard import typechecked
from typing import List, Dict
import pandas as pd
import datetime as dt

class _Bingx(API_MANAGER):
    
    INTERVALS = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", 
                 "1d","3d", "1w", "1M"]
    
    @typechecked
    def __init__(self, *, symbol:str, isdemo:bool = True, API_key:str|None = None, 
                 Secret_key:str|None = None, APIkeys_File:str|None = None,
                 APIkeys_dir:str|None = None, read_APIkeys_fromFile:bool=False ):
        super().__init__()
        self.symbol, self.isdemo = symbol.upper().replace('/', '-'), isdemo
        if read_APIkeys_fromFile: self.readAPIs(filename = APIkeys_File, dir = APIkeys_dir)
        else:
            if None in [API_key, Secret_key]: raise ValueError("API keys not given!") 
            self._change_APIkeys(API_key = API_key, secret_key = Secret_key)
        self._request = _request(self._API_key, self._SECRET_key, isdemo = isdemo )

    
    @property
    def _get_leverages(self):
        payload = {}
        path = '/openApi/swap/v2/trade/leverage'
        method = "GET"
        paramsMap = {"symbol": self.symbol}
        return self._request.send_request(payload, path, method, paramsMap)
    
    @property
    def _LONG_leverage(self):
        return int(self._get_leverages['longLeverage'])
    
    @_LONG_leverage.setter
    def _LONG_leverage(self, n):
        self._change_leverage("LONG", n)
        print(f"\n\nLONG leverage changed to {n}\n")
    
    @property
    def _SHORT_leverage(self):
        return int(self._get_leverages['shortLeverage'])
    
    @_SHORT_leverage.setter
    def _SHORT_leverage(self, n):
        self._change_leverage("SHORT", n)
        print(f"\n\nSHORT leverage changed to {n}\n")

    
    @property
    def _maxSHORT_leverage(self):
        return int(self._get_leverages['maxLongLeverage'])
    
    @property
    def _maxLONG_leverage(self):
        return int(self._get_leverages['maxShortLeverage'])
    
    @typechecked
    def _change_leverage(self, side:str, n:int):
        self._checkSide(side)
        payload = {}
        path = '/openApi/swap/v2/trade/leverage'
        method = "POST"
        paramsMap = {
        "symbol": self.symbol,
        "side": side.upper(),
        "leverage": n }
        return self._request.send_request(payload, path, method, paramsMap)
    
    @typechecked
    def _checkSide(self, side:str):
        match side.upper():
            case "LONG": return True
            case "SHORT": return True
            case _: raise ValueError("input side can be 'LONG' or 'SHORT' ")
    
    @typechecked    
    def _change_marginType(self, new_type:str):
        self._checkMarginType(new_type)
        payload = {}
        path = '/openApi/swap/v2/trade/marginType'
        method = "POST"
        paramsMap = {
        "symbol": self.symbol,
        "marginType": new_type.upper()}
        return self._request.send_request(payload, path, method, paramsMap)
        
    @typechecked
    def _checkMarginType(type:str):
        match type.upper():
            case "ISOLATED": return True
            case "CROSSED": return True
            case _: raise ValueError("input side can be 'ISOLATED' or 'CROSSED' ")
    
    @property
    def _marginType(self):
        payload = {}
        path = '/openApi/swap/v2/trade/marginType'
        method = "GET"
        paramsMap = {"symbol": "BTC-USDT"}
        return self._request.send_request(payload, path, method, paramsMap)["marginType"]
    
    @_marginType.setter
    def _marginType(self, newType:str):
        self._change_marginType(newType)
        print(f"\n\nMargin Type changed to {newType}")
        
    
    @property
    def _list_available_markets(self):
        payload = {}
        path = '/openApi/swap/v2/quote/price'
        method = "GET"
        paramsMap = {}
        pairs = self._request.send_request(payload, path, method, paramsMap, False, False)
        return [pair["symbol"] for pair in pairs]
    
    @property
    def _get_ticker(self):
        payload = {}
        path = '/openApi/swap/v2/quote/ticker'
        method = "GET"
        paramsMap = { "symbol": self.symbol }
        return self._request.send_request(payload, path, method, paramsMap, check_APIkeys=False)
    
    @property
    def _get24H_PriceChangePercent(self):
        return float(self._get_ticker["priceChangePercent"])
    
    @property
    def _get24H_LOWPrice(self):
        return float(self._get_ticker["highPrice"])
            
    @property
    def _get24H_HighPrice(self):
        return float(self._get_ticker["lowPrice"])
    
    @property
    def _last_price(self):
        payload = {}
        path = '/openApi/swap/v2/quote/price'
        method = "GET"
        paramsMap = { "symbol":self.symbol}
        return self._request.send_request(payload, path, method, paramsMap,check_APIkeys=False)["price"]
    
    @property
    def _assest_details(self):
        payload = {}
        path = '/openApi/swap/v2/user/balance'
        method = "GET"
        paramsMap = {}
        return self._request.send_request(payload, path, method, paramsMap)["balance"] 
    
    @property
    def _total_balance(self):
        return float(self._assest_details["balance"])
    
    @property
    def _available_margin(self):
        return float(self._assest_details['availableMargin'])
    
    @property
    def _freezed_margin(self):
        return float(self._assest_details['freezedMargin']) 
    
    @property
    def _current_fee(self):
        payload = {}
        path = '/openApi/swap/v2/user/commissionRate'
        method = "GET"
        paramsMap = {}
        return self._request.send_request(payload, path, method, paramsMap)
    
    
    def getAndCheck_side(PositionSide:str):
        PositionSide = PositionSide.upper()
        match PositionSide:
            case "LONG": side = "BUY"
            case "SHORT": side = "SELL"
            case _: raise ValueError("PositionSide can be 'BUY' or 'SELL'.")
        return side, PositionSide
        
        
    @typechecked
    def _make_order(self,*, 
                    quantity:float, orderType:str,
                    Price:float|None = None, stopLoss:float|None = None, 
                    positionSide:str|None = None, triggerPrice:float|None = None,
                    stopLoss_quantity:float|None = None, profitLevel:float|None = None,
                    profitLevel_quantity:float|None = None, leverage:int = 1,
                    verifyByUser = True, asDemo:bool = True):
        
        main_path = "/openApi/swap/v2/trade/order"
        path = main_path + "/test" if asDemo else main_path
        orderType = orderType.upper()       
        
        payload = {}
        method = "POST"
        paramsMap = { "symbol": self.symbol, "type": orderType, 
                     "quantity": quantity, "timeInForce": ""}
        
        if Price: paramsMap["price"] = Price
        
        if positionSide: 
            side, positionSide = _Bingx.getAndCheck_side(positionSide)
            paramsMap["positionSide"] = positionSide
            paramsMap["side"] = side
            self._change_leverage(positionSide, leverage) 
            
        if triggerPrice: paramsMap["stopPrice"] = triggerPrice
        
        if orderType == "MARKET":
            if stopLoss: 
                SL_dict = {"quantity": stopLoss_quantity if stopLoss_quantity 
                           else quantity, "price": stopLoss, "stopPrice":stopLoss,
                           "type": "STOP_MARKET"} 
                paramsMap["stopLoss"] = json.dumps(SL_dict)  
            if profitLevel: 
                TP_dict = {"quantity": profitLevel_quantity if profitLevel_quantity
                           else quantity, "price":profitLevel,"stopPrice":profitLevel,
                           "type": "TAKE_PROFIT_MARKET"}
                paramsMap["takeProfit"] = json.dumps(TP_dict)
        
        if verifyByUser: # verification by user
            ans = input(f"""\n\nare you sure to open a {orderType} of type {positionSide}
                        for {self.symbol} with quantity of {quantity} 
                        with leverage of {leverage} ? (y to continue)""")
            if ans.lower() != 'y': return None
        return self._request.send_request(payload, path, method, paramsMap)
    
    
    @typechecked
    def _add_SL(self, SL:float, quantity:float, PositionSide:str,
                asdemo:bool = True):
        main_path = "/openApi/swap/v2/trade/order"
        payload = {}
        path = main_path + "/test" if asdemo else main_path
        method = "POST"
        side, PositionSide = _Bingx.getAndCheck_side(PositionSide)
        paramsMap = {"symbol":self.symbol,"quantity": quantity,
                     "stopPrice":SL, "type": "STOP_MARKET", 
                     "positionSide":PositionSide, "side": side}
        return self._request.send_request(payload, path, method, paramsMap)
    
    
    @typechecked
    def _add_TP(self, TP:float, quantity:float, PositionSide:str,
                asdemo:bool = True):
        main_path = "/openApi/swap/v2/trade/order"
        payload = {}
        path = main_path + "/test" if asdemo else main_path
        method = "POST"
        side, PositionSide = _Bingx.getAndCheck_side(PositionSide)
        paramsMap = {"symbol":self.symbol, "quantity": quantity, 
                     "stopPrice":TP, "positionSide":PositionSide,
                     "type":"TAKE_PROFIT_MARKET", "side":side}
        return self._request.send_request(payload, path, method, paramsMap)
    
    @typechecked
    def _cancel_orders(self, IDs:List[int]):
        payload = {}
        path = '/openApi/swap/v2/trade/batchOrders'
        method = "DELETE"
        paramsMap = {"symbol":self.symbol, "orderIdList":IDs}
        return self._request.send_request(payload, path, method, paramsMap)

    

    def _cancel_all_orders(self, AllSymbols:bool = True):
        payload = {}
        path = '/openApi/swap/v2/trade/allOpenOrders'
        method = "DELETE"
        paramsMap = { "symbol": "" if AllSymbols else self.symbol }
        return self._request.send_request(payload, path, method, paramsMap)


    @typechecked
    def _close_position(self, positionSide:str, quantity:float, asdemo:bool = True):
        positionSide = positionSide.upper()
        match positionSide:
            case "LONG": side = "SELL"
            case "SHORT": side = "BUY"
            case _: raise ValueError("'positionSide' can be 'BUY' or 'SELL'. ")
        payload = {}
        main_path = "/openApi/swap/v2/trade/order"
        path = main_path + "/test" if asdemo else main_path
        method = "POST"
        paramsMap = {"symbol":self.symbol, "side":side, "quantity":quantity,
                     "positionSide":positionSide, "type": "MARKET"}
        return self._request.send_request(payload, path, method, paramsMap)

        
    def _close_all_positions(self, AllSymbols:bool = True):
        payload = {}
        path = '/openApi/swap/v2/trade/closeAllPositions'
        method = "POST"
        paramsMap = {"symbol": '' if AllSymbols else self.symbol}
        return self._request.send_request(payload, path, method, paramsMap)
    
    
    @property
    def _CurrentSymbol_LONG_posAmt(self):
        df = self._active_positions(False)
        if df.empty: return 0
        long_sum = df[df["positionSide"] == "LONG"]["positionAmt"].sum()
        return abs(long_sum)
    
    @property
    def _CurrentSymbol_SHORT_posAmt(self): 
        df = self._active_positions(False)
        if df.empty: return 0
        short_sum = df[df["positionSide"] == "SHORT"]["positionAmt"].sum()
        return abs(short_sum)
    
    @property
    def _CurrentSymbol_TOTAL_posAmt(self):
        return self._CurrentSymbol_LONG_posAmt - self._CurrentSymbol_SHORT_posAmt
    
    
    @property
    def _AllSymbols_LONG_posAmt(self): # get long Amt as {symbol:Amt} format
        """get long Amts as {symbol:Amt} format

        Returns:
            dict
        """        
        df = self._active_positions(True)
        if df.empty: return {}
        longs_df = df[df["positionSide"] == "LONG"][["symbol", "positionAmt"]]
        return longs_df.to_dict(orient = "index")
    
    
    @property
    def _AllSymbols_SHORT_posAmt(self):
        """get short Amts as {symbol:Amt} format

        Returns:
            dict
        """        
        df = self._active_positions(True)
        if df.empty: return {}
        shorts_df = df[df["positionSide"] == "SHORT"][["symbol", "positionAmt"]]
        return shorts_df.to_dict(orient = "index")
        
    
    
    @property
    def _AllSymbols_SUM_posAmt(self):
        """get total sum of Amts as {symbol:Amt} format

        Returns:
            dict
        """        
        df = self._active_positions(True)
        if df.empty: return {}
        totals_df = df[["symbol", "positionAmt"]].groupby("symbol").sum()
        totals_dict_list = totals_df.to_dict(orient = "records")
        return {d["symbol"]:d['positionAmt'] for d in totals_dict_list}
    
    
    @property
    def _AllSymbols_TOTAL_posAmt(self):
        """get all active pos amounts

        Returns:
            _type_: _description_
        """        
        df = self._active_positions(True)
        if df.empty: return {}
        all_df = df[["symbol", "positionAmt"]]
        return all_df.to_dict(orient = "index")
        
    
    ################## defining orders methods ####################
    
    def _get_pending_TPs_df(self, AllSymbols:bool = True):
        df = self._pending_orders(AllSymbols)
        if df.empty: return df
        df_ = df[(df["type"] == "TAKE_PROFIT_MARKET") | (df["type"] == "TAKE_PROFIT")].copy()
        return df_
    
    @property
    def _CurrentSymbol_PendingTPs(self):
        TPs_df = self._get_pending_TPs_df(False)
        if TPs_df.empty: return {}
        return TPs_df.to_dict(orient="index")
    
    @property
    def _CurrentSymbol_LONG_PendingTPs(self):
        TPs_df = self._get_pending_TPs_df(False)
        if TPs_df.empty: return {}
        TPs_df = TPs_df[TPs_df["positionSide"] == "LONG"]
        return TPs_df.to_dict(orient="index")
    
    @property
    def _CurrentSymbol_SHORT_PendingTPs(self):
        TPs_df = self._get_pending_TPs_df(False)
        if TPs_df.empty: return {}
        TPs_df = TPs_df[TPs_df["positionSide"] == "SHORT"]
        return TPs_df.to_dict(orient="index")
    
    
    @property
    def _AllSymbols_PendingTPs(self):
        df = self._get_pending_TPs_df(True)
        if df.empty: return {}
        return df.to_dict(orient="index")
    
    
    @property
    def _AllSymbols_LONG_PendingTPs(self):
        df = self._get_pending_TPs_df(True)
        if df.empty: return {}
        TPs_df = df[df["positionSide"] == "LONG"]
        return TPs_df.to_dict(orient="index")
    
    
    @property
    def _AllSymbols_SHORT_PendingTPs(self):
        df = self._get_pending_TPs_df(True)
        if df.empty: return {}
        TPs_df = df[df["positionSide"] == "SHORT"]
        return TPs_df.to_dict(orient="index")
    
    
        
    
    def _get_pending_SLs_df(self, AllSymbols:bool = True):
        df = self._pending_orders(AllSymbols)
        if df.empty: return df
        df_ = df[(df["type"] == "STOP_MARKET") | (df["type"] == "STOP")].copy()
        return df_
    
    
    @property
    def _CurrentSymbol_PendingSLs(self):
        df = self._get_pending_SLs_df(False)
        if df.empty: return {}
        return df.to_dict(orient = "index")
    
    
    @property
    def _CurrentSymbol_LONG_PendingSLs(self):
        df = self._get_pending_SLs_df(False)
        if df.empty: return {}
        SLs_df = df[df["positionSide"]=="LONG"]
        return SLs_df.to_dict(orient = "index")
    
    
    @property
    def _CurrentSymbol_SHORT_PendingSLs(self):
        df = self._get_pending_SLs_df(False)
        if df.empty: return {}
        SLs_df = df[df["positionSide"]=="SHORT"]
        return SLs_df.to_dict(orient = "index")
    
    
    @property
    def _AllSymbols_PendingSLs(self):
        df = self._get_pending_SLs_df(True)
        if df.empty: return {}
        return df.to_dict(orient = "index")
    
    @property
    def _AllSymbols_LONG_PendingSLs(self):
        df = self._get_pending_SLs_df(True)
        if df.empty: return {}
        SLs_df = df[df["positionSide"]=="LONG"]
        return SLs_df.to_dict(orient = "index")
    
    
    @property
    def _AllSymbols_SHORT_PendingSLs(self):
        df = self._get_pending_SLs_df(True)
        if df.empty: return {}
        SLs_df = df[df["positionSide"]=="SHORT"]
        return SLs_df.to_dict(orient = "index")
    
    
    def _get_pending_SLTPs_df(self, AllSymbols:bool = True):
        df = self._pending_orders(AllSymbols=AllSymbols)
        if df.empty: return df
        types = df["type"].copy()
        cnd =  ((types == "STOP_MARKET")|
                (types == "TAKE_PROFIT_MARKET")|
                (types == "STOP")|
                (types == "TAKE_PROFIT"))
        return df[cnd]
    
    
    @property
    def _CurrentSymbol_PendingSLTPs(self):
        df = self._get_pending_SLTPs_df(False)
        if df.empty: return {}
        return df.to_dict(orient = "index")
    
    @property
    def _CurrentSymbol_LONG_PendingSLTPs(self):
        df = self._get_pending_SLTPs_df(False)
        if df.empty: return {}
        SLTPs_df = df[df["positionSide"]=="LONG"]
        return SLTPs_df.to_dict(orient = "index")
    
    @property
    def _CurrentSymbol_SHORT_PendingSLTPs(self):
        df = self._get_pending_SLTPs_df(False)
        if df.empty: return {}
        SLTPs_df = df[df["positionSide"]=="SHORT"]
        return SLTPs_df.to_dict(orient = "index")
    
    @property
    def _AllSymbols_PendingSLTPs(self):
        df = self._get_pending_SLTPs_df(True)
        if df.empty: return {}
        return df.to_dict(orient = "index")
    
    @property
    def _AllSymbols_LONG_PendingSLTPs(self):
        df = self._get_pending_SLTPs_df(True)
        if df.empty: return {}
        SLTPs_df = df[df["positionSide"]=="LONG"]
        return SLTPs_df.to_dict(orient = "index")
    
    @property
    def _AllSymbols_SHORT_PendingSLTPs(self):
        df = self._get_pending_SLTPs_df(True)
        if df.empty: return {}
        SLTPs_df = df[df["positionSide"]=="SHORT"]
        return SLTPs_df.to_dict(orient = "index")
    
        
    
    @property
    def _CurrentSymbol_LONG_ordersAmt(self):
        df = self._pending_orders(False)
        if df.empty: return 0
        total_long = df[(df["side"] == "BUY") & (df["positionSide"] == "LONG")]["origQty"].sum()
        return total_long
    
    
    @property
    def _CurrentSymbol_SHORT_ordersAmt(self):
        df = self._pending_orders(False)
        if df.empty: return 0
        total_short = df[(df["side"] == "SELL") & (df["positionSide"] == "SHORT")]["origQty"].sum()
        return total_short
        
    @property
    def _CurrentSymbol_TOTAL_ordersAmt(self):
        return self._CurrentSymbol_LONG_ordersAmt - self._CurrentSymbol_SHORT_ordersAmt
    
    
    def _active_positions(self, AllSymbols:bool = True)-> pd.DataFrame:
        payload = {}
        path = '/openApi/swap/v2/user/positions'
        method = "GET"
        paramsMap = { "symbol": '' if AllSymbols else self.symbol}
        res = self._request.send_request(payload, path, method, paramsMap)
        df = pd.DataFrame(res)
        if df.empty: return df
        df = df.set_index("positionId")
        df = self._format_posColumns(df)
        AmtCols = ["positionAmt", "availableAmt"]
        df[AmtCols] = df[AmtCols].mask(df["positionSide"] == "SHORT", -df[AmtCols].abs())
        return df
    
    
    @typechecked
    def _format_posColumns(self, df:pd.DataFrame, 
                           numeric_cols:list=["positionAmt", "availableAmt", "avgPrice",
                                           "initialMargin", "leverage", "unrealizedProfit",
                                           "realisedProfit", "liquidationPrice"], 
                           bool_cols:list = ['isolated'], 
                           str_cols:list = ["symbol", "currency", "positionSide"]):
        df_ = df.copy()
        df_[numeric_cols] = df_[numeric_cols].astype("Float64")
        df_[bool_cols] = df_[bool_cols].astype("bool")
        df_[str_cols] = df_[str_cols].astype("str")
        return df_
    
        
    
    @property
    def _AllSymbols_SHORT_ordersAmt(self):
        df = self._NonSLTP_orders_df
        if df.empty: return {}
        shorts_df = df[df["positionSide"] == "SHORT"]
        return shorts_df.to_dict(orient = "index")
    
    
    @property
    def _AllSymbols_LONG_ordersAmt(self):
        df = self._NonSLTP_orders_df
        if df.empty: return {}
        longs_df = df[df["positionSide"] == "LONG"] 
        return longs_df.to_dict(orient = "index")
    
    
    @property
    def _AllSymbols_SUM_ordersAmt(self):
        df = self._NonSLTP_orders_df
        if df.empty: return {}
        sums_df = df[["symbol", "origQty"]].groupby("symbol").sum()
        sums_dict_list = sums_df.to_dict(orient="records")
        return {d["symbol"]:d['origQty'] for d in sums_dict_list}
        
    
    @property
    def _AllSymbols_TOTAL_ordersAmt(self):
        df = self._NonSLTP_orders_df
        if df.empty: return {}
        return df.to_dict("index")
        
        
    @property
    def _NonSLTP_orders_df(self)-> pd.DataFrame:
        df = self._pending_orders(True)
        if df.empty: return df
        types = df["type"].copy()
        cnd = ~((types == "STOP_MARKET")|
                (types == "TAKE_PROFIT_MARKET")|
                (types == "STOP")|
                (types == "TAKE_PROFIT"))
        return df[cnd]
        
        
    def _pending_orders(self, AllSymbols:bool = True)-> pd.DataFrame:
        payload = {}
        path = '/openApi/swap/v2/trade/openOrders'
        method = "GET"
        paramsMap = {"symbol": '' if AllSymbols else self.symbol}
        res = self._request.send_request(payload, path, method, paramsMap)["orders"]
        df = pd.DataFrame(res)
        if df.empty: return df
        df = df.set_index("orderId")
        df = self._format_posColumns(df, str_cols = ["symbol", "side", "positionSide", "type"],
                                numeric_cols=["origQty","price","executedQty","avgPrice",
                                              "cumQuote", "profit"], bool_cols=[])
        AmtCols = ["origQty", "executedQty"]
        df[AmtCols] = df[AmtCols].mask(df["side"] == "SELL", -df[AmtCols].abs())
        return df
    
    
    @typechecked
    def _lastCandle(self, interval:str):       
        self._check_interval(interval)
        payload = {}
        path = '/openApi/swap/v3/quote/klines'
        method = "GET"
        paramsMap = { "symbol": self.symbol, "interval": interval, 
                      "startTime": dt.datetime(2023, 1, 1).timestamp().__int__(),
                      "endTime":current_time(False, True), "limit": 1400 }
        return self._request.send_request(payload, path, method, paramsMap, False)[-1]
    
    
    def _lastClose(self, interval:str):
        return float(self._lastCandle(interval)["close"])
        
        
    def _lastOpen(self, interval:str):
        return float(self._lastCandle(interval)["open"])
        
        
    def _lastHigh(self, interval:str):
        return float(self._lastCandle(interval)["high"])
        
        
    def _lastLow(self, interval:str):
        return float(self._lastCandle(interval)["low"])
    
    @type
    def _lastCandleTimestamp(self, interval:str, as_datetime:bool = False):
        time:int = int(self._lastCandle(interval)["time"]) // 1000
        return dt.datetime.fromtimestamp(time) if as_datetime else time 
    
    
    def _lastVolume(self, interval:str):
        return self._lastCandle(interval)["volume"]
    
    
    def _check_interval(self, interval:str):
        res = interval in self.INTERVALS
        if not res: raise ValueError("interval not found")
        return res
        
    
    @property
    def _closed_positions(self):
        pass
        
    
    
class _request:
    
    APIURL_main = "https://open-api.bingx.com"
    APIURL_vst = "https://open-api-vst.bingx.com"
    
    APIURL = None
    
    
    @typechecked
    def __init__(self, API_KEY:str, SECRET_KEY:str, isdemo:bool = True) -> None:
        self.__API_KEY, self.__SECRET_KEY = API_KEY, SECRET_KEY
        self.APIURL = _request.APIURL_vst if isdemo else _request.APIURL_main
    
    def get_sign(api_secret, payload):
        signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"),
                             digestmod=sha256).hexdigest()
        # print("sign=" + signature)
        return signature
    
    
    def _send_request(self, method, path, urlpa, payload):
        url = "%s%s?%s&signature=%s" % (self.APIURL, path, urlpa,
                                        _request.get_sign(self.__SECRET_KEY, urlpa))
        # print(url)
        headers = {
            'X-BX-APIKEY': self.__API_KEY,
        }
        response = requests.request(method, url, headers=headers, data=payload)
        return response.text
    
    @typechecked
    def send_request(self, payload:dict, path:str, method:str, paramsMap:dict, add_timestamp = True,
                     check_APIkeys:bool = True):
        if check_APIkeys: self.check_APIkeys
        if add_timestamp: paramsMap["recvWindow"] = 25000
        paramsStr = _request.praseParam(paramsMap)
        res = self._send_request(method, path, paramsStr, payload)
        dict_res = _request.check_response(json.loads(res))["data"]
        return dict_res
    
    @property
    def check_APIkeys(self):
        APIs = [self.__API_KEY, self.__SECRET_KEY]
        if '' in APIs or None in APIs: raise KeyError("API keys are not defined yet")
    
    @typechecked
    def check_response(res:dict):
        error_num = res["code"]
        error_msg = res["msg"]
        if error_num != 0: 
            raise ClientError(f"error number {error_num} accured with massage: {error_msg} also check your internet connection or proxy")
        return res
        
    @typechecked
    def praseParam(paramsMap:dict):
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        return paramsStr+"&timestamp="+str(int(time.time() * 1000))
    

    
    
    
class ClientError(Exception):
    def __init__(self, msg:str) -> None:
        super().__init__(msg)
        self.msg = msg
        
        
    
    
        
        