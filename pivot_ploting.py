#%% import needed libs
import plotly
import pandas as pd
import kucoin.client as kc
import datetime as dt
import time

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

#%% get data at any interval any period as dataframe

def get_kline_as_df(symbol:str, interval:str ="15min" , reverse_df:bool = False, end_timestamp:int = None , start_timestamp:int = dt.datetime(2017,1,1).timestamp().__int__() ) -> pd.DataFrame :
    """this function gets candlestick data for each symbol,interval output dataframe will be reversed
     if reverse_df is True. also this function will extract data till end_timestamp but if it is None
     will extract data until current time. also data will be extracted from start_timestamp and if it's 
     None will extract data till longest timestamp possible.
     returns timestamp, open, close, high, low, volume, turnover
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

            else:
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



btc_all_df = get_kline_as_df("BTC-USDT", "15min" , False )


#%% saving to excel
btc_all_df.to_excel("BTC-USDT|15min.xlsx")

#%% binance api
def get_klines_iter(symbol, interval, start, end, limit=5000):
    
    df = pd.DataFrame()
    startDate = end
    while startDate>start:
        url = 'https://api.binance.com/api/v3/klines?symbol=' + \
            symbol + '&interval=' + interval + '&limit='  + str(iteration)
        if startDate is not None:
            url += '&endTime=' + str(startDate)
        
        df2 = pd.read_json(url)
        df2.columns = ['Opentime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Closetime', 'Quote asset volume', 'Number of trades','Taker by base', 'Taker buy quote', 'Ignore']
        df = pd.concat([df2, df], axis=0, ignore_index=True, keys=None)
        startDate = df.Opentime[0]   
    df.reset_index(drop=True, inplace=True)    
    return df 

btc_15min = get_klines_iter("BTC-USDT", "15min", dt.datetime(2018, 1, 1 ).timestamp().__int__() ,
                 dt.datetime(2018, 1, 1 ).timestamp().__int__() ,
                 limit=5000)


#%% get data at any interval any period as dataframe

def get_kline_as_df(symbol:str, interval:str ="15min" , reverse_df:bool = False, end_timestamp:int = None , start_timestamp:int = None ):
    """this function gets candlestick data for each symbol,interval output dataframe will be reversed
     if reverse_df is True. also this function will extract data till end_timestamp but if it is None
     will extract data until current time. also data will be extracted from start_timestamp and if it's 
     None will extract data till longest timestamp possible.
     returns timestamp, open, close, high, low, volume, turnover
    """

    cols = ["timestamp",'open','close','high','low','volume','turnover']
    df_temp = pd.DataFrame(columns = cols)
    
    if end_timestamp == None:
        current_timestamp = int(market.get_server_timestamp()*1e-3) # current ts milisec to sec
        ts_temp_end = current_timestamp
    else: ts_temp_end = end_timestamp
    
    
    while 1 :

        # try:
        # returns timestamp(newest date comes first), open, close, high, low, volume, turnover
        ts_temp_last = ts_temp_end # saves last timestamp
        candles_temp = market.get_kline(symbol, interval , startAt = start_timestamp ,endAt = ts_temp_end) # read kline data from kucoin api
        ts_temp_end = int(candles_temp[0][-1]) # get last timestamp of each bunch of data
        print(candles_temp)
        print(len(candles_temp))
    #     if ts_temp_end == ts_temp_last : # check if we got the data of new timestamp else exits loop
        #         print("\n\n****final first datetime is: ",
        #         dt.datetime.fromtimestamp( int(df_temp.iloc[0].timestamp) ),
        #         "\n****final last datetime is: ",
        #         dt.datetime.fromtimestamp( int(df_temp.iloc[-1].timestamp) )
        #              )
        #         print("\n\ndone")
        #         break 

        #     if reverse_df : candles_temp.reverse() # reverses dataframe if specified

        #     candle_df_temp = pd.DataFrame(candles_temp, columns = cols) # convert current data bunch to df
        #     df_temp = pd.concat( [df_temp,candle_df_temp], axis=0, ignore_index = True ) # updating final df

        #     # exits loop if we arrived at start_timestamp (smallest date)
        #     if ts_temp_end != None and ts_temp_end<= start_timestamp : break 

            

        # except Exception: 
        #     print("\n\nfirst datetime till now is: ",
        #             dt.datetime.fromtimestamp( int(df_temp.iloc[0].timestamp) ),
        #             "\nlast datetime till now is: ",
        #             dt.datetime.fromtimestamp( int(df_temp.iloc[-1].timestamp) )
        #          )
            
        #     time.sleep(10)
        #     continue

        return ts_temp_end



ts = get_kline_as_df("BTC-USDT", "15min" , False , start_timestamp = dt.datetime(2018, 1, 1 ).timestamp().__int__() , end_timestamp = None)


# %%
