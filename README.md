# pykucoin
a toobox wrriten to simplify some common alghorithmic trading processes.
uses plotly package for visualization, python-kucoin for extracting data, ta to calculate indicators, also pandas and numpy( examples in example file)
what can this package do:
1. extract market historical data for all symbols
2. visualize market data as candlestick in a interactive way.
3. able to add any shapes that are most used to market figures.
4. can find market highs and lows with high accurate.
5. can find trend of market with diffrent methods 

Note: many of the functions in this package works with standard column names, standard column names are:
"open", "close", "high", "low", "volume", "datetime", timestamp

Note: row indexes of your input dataframe must be integer not datetime or timestamp format.
instead you must have a column named "datetime" that keeps time index of each row. 

example:
```
pip install pycoin
```

