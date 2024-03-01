- making KlineData_Fetcher async: currently KlineData_Fetcher in synchronous it must change to async for high performance

- overriding pandas dataframe to make a custom dataframe specialized for OHLCV data 

  - adding needed methods to OHLCV_DataFrame such as symbol, exchange, timeframe, name and       overriding some of them such as copy(), to_csv(), to_feather(), etc.
    
  - adding methods for saving and loading data as csv, feather, etc.

  - changing all dataframe used in project to custom one.

- fixing backtesting bugs 

- defining a way to implement user defined strategies 

- fixing starting strategies in background bugs as celery task

- adding UI/UX to bot

- writing telegram bot core
