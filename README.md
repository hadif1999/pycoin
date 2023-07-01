# pykucoin
### a toobox wrriten to simplify some common alghorithmic trading processes.
uses plotly package for visualization, python-kucoin for extracting data, ta to calculate indicators, also pandas and numpy( examples in example file)
### what can this package do:
1. download and extract market historical data for all symbols
2. visualize market data as candlestick in a interactive way.
3. able to add any shapes that are most used in market processing such as lines, circles, etc .
4. can find market highs and lows accurately.
5. can find market trend.
6. you can use it to deploy many strategies such as indicator based, price action, etc (in development). 
also machine learning based strategies will be added in future (in development).
7. backtesting
8. getting position

Note: many of the functions in this package works with standard column names, standard column names are:
"open", "close", "high", "low", "volume", "datetime", "timestamp". 
so it's better to change your market dataframe column names if they are not as the above format.
you can also change your column name using some methods that will be discussed in examples.

Note: row indexes of your input dataframe must be integer not datetime or timestamp format.
instead you must have a column named "datetime" that keeps time index of each row. 

## Examples

after cloning the repo you can use these commands to make a market processing object:

```python 

from pycoin.market_data_gathering.market_processing import Market_Processing
market_obj = Market_Processing(symbol = "BTC-USDT", interval = "4hour")

```
### download "4hour" interval of market dataframe using download_kline_as_df method:
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
### evaluate trend with SMA
```python

market_analysis.eval_trend_with_MAs(drop_MA_cols = True , windows=[50, 200])
plots.draw_trend_highlight(column = "MA_trend")

```




