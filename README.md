# pycoin
### a lovable data analysis and algorithmic trading library for cryptocurrencies
including tools for deploying any strategies including pattern based strategies,
price action strategies, indicator based strategies and also Machine learning based strategies. 
able to run multi strategy instances on a single bot as a webapp and a lot more...
### what can this package do:
1. download market historical data for all symbols from almost all exchanges thanks to ccxt.
2. visualizing capabilities to easily analysis market.
3. able to perform some useful analysis such as finding market trend according to market past high and lows, finding market important levels (like support and resistance) and more .
4. able to define your strategy, backtest it, run it in dry run mode and also in real mode.
5. using telegram bot and webapp to control and monitor your bot. (soon)  
6. run multiple strategy instances for each user as a single bot (soon) 

Note: for documentation please refer to examples folder.

## Install
```bash
!pip install pythoncoin
```
## Quick start

after installation you can run below:

```python 

from pycoin.market_data_gathering.market_processing import Market_Processing
market_obj = Market_Processing(symbol = "BTC-USDT", interval = "4hour")

```
### download "4hour" interval of market dataframe:
```python

import datetime as dt

btcusd_h4_df = market_obj.download_kline_as_df(reverse_df = True, 
               start_timestamp= dt.datetime(2017, 1, 1).timestamp().__int__(), inplace= True,
               verbose=True
               ) 

```
the important arguments of download_kline_as_df method is :

start_timestamp: the first data timestamp that will be downloaded, if not defined the start_timestamp will be the first data exists for that symbol.

end_timestamp: the data will be extracted till this timestamp, if not defined it will download data until current timestamp.

reverse_df : whether to reverse the final dataframe or not.

inplace: every Market_Processing object will have its own symbol dataframe. 
with this arg you can define if you want to replace current Market_Processing object dataframe with new one.

### saving the current Market_Processing object dataframe:
```python

market_obj.save_market(path = ".", as_csv = False)

```
as_csv: whether to save dataframe as csv or excel file.
path: where to save the dataframe (default is current dir)

### loading the the market dataframe:
```python

btc_h4_df = market_obj.load_kline_data('BTC-USDT|15min.csv', reverse = True)

# accessing market_obj dataframe
market_obj.df

```
### ploting the candlestick data
```python

from pycoin.market_data_kline_plots.market_plotter import Market_Plotter
plots = Market_Plotter(market_obj)

# if plot_by_grp is False then it will plot the whole candlestick data (market_obj.df)
figure, _ = plots.plot_market( plot_by_grp = False,fig_size = [1100,600], slider = False)


# if plot_by_grp is True you can plot candlestick data by group and plot a specific year, month, day
figure, grp_df = plots.plot_market( plot_by_grp = True, year = 2023,
                                    fig_size = [1100,600],
                                    replace_df_with_grp = True, 
                                    slider = False
                                  )


figure.show()

```

![alt text](https://github.com/hadif1999/pycoin/blob/master/pics/btc_h4_2023_candlestick.png?raw=true)

### evaluating market high & lows
```python
max_indices, min_indices = market_obj.get_market_high_lows( candle_range = 100 , 
                                                            min_time_dist = dt.timedelta(hours=13),
                                                          ) 
                                                          
```
candle_range : range of candles to look for high and lows 
min_time: remove the high or low that is very close to previous one if their time distance is below than min_time.
### ploting market high and lows
```python

plots.plot_high_lows(R = 5000, y_scale = 0.1)

```
![alt text](https://github.com/hadif1999/pycoin/blob/master/pics/btc_h4_2023_high_lows.png?raw=true)

the method above puts a circle for each high and low. 
R is the radius and y_scale can scale the price in y axis for better visualizing.

### evaluate market trend with high and lows
every trend that is found with any method such as high & lows, SMA,etc. adds a new column that holds the trend label for each row of data, and when you want to plot these trend you should give this column name to draw_trend_highlight method.

```python
# finding trend 
process.eval_trend_with_high_lows()

# ploting trend
plots.draw_trend_highlight(column = "high_low_trend", add_high_lows = True, R = 3000, 
                           y_scale = 0.1, add_high_lows_shapes = True
                           )

```
![alt text](https://github.com/hadif1999/pycoin/blob/master/pics/btc_h4_2023_trend.png?raw=true)
### evaluate trend with SMA
```python

market_analysis.eval_trend_with_MAs(drop_MA_cols = True , windows=[50, 200])
plots.draw_trend_highlight(column = "MA_trend")

```
![alt text](https://github.com/hadif1999/pycoin/blob/master/pics/btc_h4_2023_MA_trend.png?raw=true)




