### example of plotting a market as candlesticks, groupby of market, get market high and lows, evaluate 
## trend with diffrent methods and visualizing them


#%% import market get data lib
import os
os.chdir("..")
os.getcwd()
from pycoin.market_data_gathering.market_processing import Market_Processing
from pycoin.market_data_kline_plots.market_plotter import Market_Plotter

#%% load data
market_analysis = Market_Processing("BTC-USDT", interval = "4hour")

import datetime as dt

btcusd_h4_df = market_analysis.download_kline_as_df(reverse_df = True, 
               start_timestamp= dt.datetime(2017, 1, 1).timestamp().__int__(), inplace= True,
               verbose=True
               ) 

# market_analysis.save_market()

# btc_4h_df = market_analysis.load_kline_data('BTC-USDT|15min.csv', reverse = True)

# current value of symbol
# val_now = market.tick

#%% plot interactive candlestick data and pivots

# ploting just 1 month for better visualization 
plots = Market_Plotter(market_analysis)
btc_grp_fig,_ = plots.plot_market( plot_by_grp = True, year = 2023,
                                   fig_size = [1100,600],
                                   replace_df_with_grp = True, 
                                   slider = False
                                 )

# define interactive options to use 
config_ = {'modeBarButtonsToAdd':['drawline','drawcircle','drawrect','eraseshape']}
btc_grp_fig.show(config = config_)

#%% plot pivots min and max
import numpy as np
import datetime as dt

maxs, mins = market_analysis.get_market_high_lows( candle_range = 20 , 
                                                  min_time_dist = dt.timedelta(hours=13)) 

# show added min and max pivots
plots.plot_high_lows(R = 5000, y_scale = 0.1)

# market_plot.remove_all_shapes(btc_15m_grp_fig)

#%% eval trend with high lows

df_high_low_trend = market_analysis.eval_trend_with_high_lows()
plots.draw_trend_highlight(column = "high_low_trend")

# %% evaluating market trend with MA

df_trend = market_analysis.eval_trend_with_MAs(drop_MA_cols = True , windows=[50, 200])

# %% plot trend with MAs


plots.draw_trend_highlight(column = "MA_trend")


# %% using MACD to find trend of market

MACD_trend = market_analysis.eval_trend_with_MACD(drop_MACD_col = True )
MACD_trend_fig = plots.empty_figure(fig_size = [1300,600], slider = False)

plots.draw_trend_highlight( column = "MACD_trend")

 # %%                                                       

