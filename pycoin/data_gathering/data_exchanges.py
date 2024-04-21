import ccxt 
from freqtrade.data.converter import ohlcv_to_dataframe
from pycoin import Utils
import datetime as dt
import pandas as pd



def KlineData_Fetcher(symbol: str, timeframe: str, data_exchange:str,
                      since: int|dt.datetime|None = None, 
                      limit:int = 1000, fill_missing: bool = True, 
                      drop_incomplete: bool = True, datetime_index: bool = True,
                      throw_exc: bool = False,
                      dataframe_Name_format:str = "{symbol}|{exchange}|{timeframe}",
                      title_col_names:bool = True, **kwargs):
    
    data_exchange = data_exchange.lower() 
    assert data_exchange in Data_Exchanges.keys(), f"exchange not found, current exchanges: {list(Data_Exchanges.keys())}"
    # get exchange ccxt ohlcv fetcher func
    data_fetcher = Data_Exchanges[data_exchange].fetch_ohlcv
    dataframe_Name = dataframe_Name_format.format(symbol = symbol, exchange = data_exchange,
                                                  timeframe = timeframe) 
    kwargs = dict(symbol=symbol, timeframe=timeframe, limit=limit)
    ohlcv = data_fetcher(**kwargs, since = None)
    all_ohlcv = []
    # fetches historical data if since if provided
    if since: 
        if isinstance(since, dt.datetime): _since_ = int(since.timestamp()*1000)
        else: _since_ = int(round(since))
        targetTime = ohlcv[-1][0]
        prev_last_fetched_time = None
        while True:
            try: _ohlcv_ =  data_fetcher(**kwargs, since=_since_)
            except ccxt.BadRequest as e:
                if throw_exc: raise e
                print(f"\n {e}, fetching available timerange...\n")
                _ohlcv_ = data_fetcher(**kwargs, since = None)
            last_fetched_time = _ohlcv_[-1][0]
            if last_fetched_time == prev_last_fetched_time: break
            else: 
                _since_ = last_fetched_time
                all_ohlcv += _ohlcv_
            prev_last_fetched_time = last_fetched_time  
            print(f"""\n\n{dataframe_Name}  
                  untill {Utils.ts2dt(int(all_ohlcv[-1][0]/1000)).__str__()} fetched""")
    else: 
        all_ohlcv = ohlcv
    # filling nans and missing values
    df = postprocess_Data(ohlcv=all_ohlcv, timeframe = timeframe,
                          fill_missing=fill_missing, drop_incomplete=drop_incomplete,
                          datetime_index=datetime_index, symbol = symbol,
                          title_col_names = title_col_names)
    df.Name = dataframe_Name
    return df



def postprocess_Data(ohlcv: list[float], datetime_index: bool = True, **kwargs):
    
    df = ohlcv_to_dataframe(ohlcv = ohlcv, timeframe = kwargs.get("timeframe"),
                            fill_missing=kwargs.get("fill_missing", True),
                            drop_incomplete=kwargs.get("drop_incomplete", True),
                            pair = kwargs.get("symbol"))
    df["date"] = pd.to_datetime(df["date"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    df['datetime'] = df["date"]
    if kwargs.get("title_col_names", True):
        df = Utils.case_col_names(df, "title")
        if datetime_index: df.set_index("Datetime", inplace = True)
    else: 
        if datetime_index: df.set_index("datetime", inplace = True)
    return df
     

Data_Exchanges = {exchange: getattr(ccxt, exchange)() for exchange in ccxt.exchanges}
