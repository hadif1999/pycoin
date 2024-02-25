import ccxt 
from freqtrade.data.converter import ohlcv_to_dataframe
from .. import utils
import datetime as dt



def KlineData_Fetcher(symbol: str, timeframe: str, data_exchange:str,
                      since: int|dt.datetime|None = None, 
                      limit:int = 1000, fill_missing: bool = True, 
                      drop_incomplete: bool = True, datetime_index: bool = True):
    
    data_exchange = data_exchange.lower()
    assert data_exchange in Data_Exchanges.keys(), f"exchange not found current exchanges: {list(Data_Exchanges.keys())}"
    data_fetcher = Data_Exchanges[data_exchange]
    ohlcv = data_fetcher(symbol=symbol, timeframe=timeframe,
                         since=None, limit=limit)
    all_ohlcv = []
    if since: 
        if isinstance(since, dt.datetime): _since_ = int(since.timestamp()*1000)
        else: _since_ = int(round(since))
        targetTime = ohlcv[-1][0]
        prev_last_fetched_time = None
        while True:
            _ohlcv_ =  data_fetcher(symbol=symbol, timeframe=timeframe,
                                    since=_since_, limit=limit)
            last_fetched_time = _ohlcv_[-1][0]
            if last_fetched_time == prev_last_fetched_time: break
            else: 
                _since_ = last_fetched_time
                all_ohlcv += _ohlcv_
                
            prev_last_fetched_time = last_fetched_time  
            print(f"""\n\n{data_exchange}|{timeframe}|{symbol}  
                  untill {utils.ts2dt(int(all_ohlcv[-1][0]/1000)).__str__()} fetched""")
    else: 
        all_ohlcv = ohlcv
    df = postprocess_Data(ohlcv=all_ohlcv, timeframe = timeframe,
                          fill_missing=fill_missing, drop_incomplete=drop_incomplete,
                          datetime_index=datetime_index, symbol = symbol)
    return df



def postprocess_Data(ohlcv: list[float], fill_missing: bool = True,
                     drop_incomplete: bool = True, datetime_index: bool = True, **kwargs):
    
    df = ohlcv_to_dataframe(ohlcv = ohlcv, timeframe = kwargs.get("timeframe"),
                            fill_missing=fill_missing, drop_incomplete=drop_incomplete,
                            pair = kwargs.get("symbol"))
    df.rename(columns = {"date":"datetime"}, inplace = True)
    df = utils.case_col_names(df, "title")
    if datetime_index: df.set_index("Datetime", inplace = True)
    return df
     


Data_Exchanges = {"binance": ccxt.binance().fetch_ohlcv, "bingx": ccxt.bingx().fetch_ohlcv,
                  "kucoin": ccxt.kucoin().fetch_ohlcv, "htx": ccxt.htx().fetch_ohlcv} 
