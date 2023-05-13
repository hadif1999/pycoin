#%% import needed libs
import plotly
import pandas as pd
import kucoin.client as kc
import datetime as dt
import time
import plotly.graph_objects as go
from datetime import datetime

#%% defining start date and end date of getting data

def get_end_time(start_time:dt.datetime , delta_days:int):
    start_ts = start_time.timestamp()
    delta_t = float( dt.timedelta(delta_days,0).total_seconds() )
    end_ts = delta_t + start_ts
    end_date = dt.datetime.fromtimestamp(end_ts).date()
    return end_date


# start_date  = dt.datetime(2018, 1, 1).timestamp().__int__()
end_date = dt.datetime(2022, 1, 1 ).timestamp().__int__() 
start_data = dt.datetime(2017,1,1).timestamp().__int__()

#%% download data with kucoin api
market = kc.Market(url='https://api.kucoin.com')

# returns timestamp(end date comes first), open, close, high, low, volume, turnover 
btc_data_test = market.get_kline("BTC-USDT", "15min" ,startAt = start_data , endAt = end_date )
# #"""this function gets candlestick data for each symbol,interval output dataframe will be reversed
#      if reverse_df is True. also this function will extract data till end_timestamp but if it is None
#      will extract data until current time. also data will be extracted from start_timestamp and if it's 
#      None will extract data till longest timestamp possible.
#      returns timestamp, open, close, high, low, volume, turnover
#     """
#%% get data at any interval any period as dataframe

def get_kline_as_df(symbol:str, interval:str ="15min" , reverse_df:bool = False, end_timestamp:int = None , start_timestamp:int = dt.datetime(2017,1,1).timestamp().__int__() ) -> pd.DataFrame :
    """ gives candlestick data as dataframe.
    if end timestamp is None data will gathered until current datetime.
    more information at : https://docs.kucoin.com/#get-klines
    

    Args:
        symbol (str): symbol chart pair
        interval (str, optional): frequency of data. Defaults to "15min".
        reverse_df (bool, optional): reverses output dataframe. Defaults to False.
        end_timestamp (int, optional): data gathered until this time (gathers until current time if None). Defaults to None.
        start_timestamp (int, optional): start gathering data from this timestamp. Defaults to dt.datetime(2017,1,1).timestamp().__int__().

    Returns:
        pd.DataFrame: dataframe object
    """   
    

    cols = ["timestamp",'open','close','high','low','volume','turnover']
    df_temp = pd.DataFrame(columns = cols)
    
    if end_timestamp == None:
        current_timestamp = int(market.get_server_timestamp()*1e-3) # current ts milisec to sec
        ts_temp_end = current_timestamp
    else: ts_temp_end = end_timestamp
    
    
    while 1 :
        try:
        # returns timestamp(newest date comes first), open, close, high, low, volume, turnover
            ts_temp_last = ts_temp_end # saves last timestamp
            candles_temp = market.get_kline(symbol, interval , startAt = start_timestamp, endAt = ts_temp_end ) # read kline data from kucoin api
            ts_temp_end = int(candles_temp[-1][0]) # get last timestamp of each bunch of data
            
            if reverse_df : candles_temp.reverse() # reverses dataframe if specified

            candle_df_temp = pd.DataFrame(candles_temp, columns = cols) # convert current data bunch to df
            df_temp = pd.concat( [df_temp,candle_df_temp], axis=0, ignore_index = True ) # updating final df

            # exits loop if we arrived at start_timestamp (smallest date)
            if ts_temp_end <= start_timestamp : break 
            

        except Exception: 
        
            if ts_temp_end == ts_temp_last : # check if we got the data of new timestamp else exits loop
                print("\n\n****final first datetime is: ",
                dt.datetime.fromtimestamp( int(df_temp.iloc[0].timestamp) ),
                "\n****final last datetime is: ",
                dt.datetime.fromtimestamp( int(df_temp.iloc[-1].timestamp) )
                     )
                print("\n\ndone")
                break


            print("\n\nfirst datetime till now is: ",
                dt.datetime.fromtimestamp( int(df_temp.iloc[0].timestamp) ),
                "\nlast datetime till now is: ",
                dt.datetime.fromtimestamp( int(df_temp.iloc[-1].timestamp) )
                    )
            
            time.sleep(10)
            continue
    
    df_temp["timestamp"] = df_temp.timestamp.astype("Int64")
    df_temp[df_temp.columns.to_list()[1:]] = df_temp[df_temp.columns.to_list()[1:]].astype("Float64") 
    return df_temp



btc_15min_df = get_kline_as_df("BTC-USDT", "15min" , False )


#%% saving to excel
btc_15min_df.to_excel("BTC-USDT|15min.xlsx")
#%% plot candlestick

fig = go.Figure(data=[go.Candlestick(x = btc_15min_df['timestamp'],
                open = btc_15min_df['open'],
                high = btc_15min_df['high'],
                low = btc_15min_df['low'],
                close = btc_15min_df['close'])])

fig.show()

# %%
