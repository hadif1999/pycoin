#%% import market get data lib
from src.market_data_kline_plots.market_plotter import get_market_plots

#%% load data
market_plot = get_market_plots('BTC-USDT')
btc_15min_df = market_plot.load_kline_data('BTC-USDT|15min.csv', reverse = True)

# current value of symbol
# val_now = market.tick

#%% plot interactive candlestick data and pivots

btc_15m_grp_fig, btc_grp_df = market_plot.plot_candlestick_plotly(btc_15min_df, 
                                                                  plot_by_grp = True, year = 2022, month = 5,
                                                                  fig_size = [1100,600],
                                                                  slider = False)

# define interactive options to use 
config_ = {'modeBarButtonsToAdd':['drawline','drawcircle','drawrect','eraseshape']}


#%% market processing lib

from src.market_data_gathering.market_processing import market_processing

analysis = market_processing(btc_grp_df)

#%% plot pivots min and max
import numpy as np
import datetime as dt

maxs, mins = analysis.get_market_high_lows( 50 , min_time_dist = dt.timedelta(hours=13)) 

analysis.plot_high_lows(btc_15m_grp_fig, R = 400, y_scale = 0.2)

# show added min and max pivots
btc_15m_grp_fig.show(config = config_)

# market_plot.remove_all_shapes(btc_15m_grp_fig)

#%% eval trend with high lows

df_high_low_trend = analysis.eval_trend_with_high_lows()
analysis.draw_trend_highlight(btc_15m_grp_fig, column = "high_low_trend")

btc_15m_grp_fig.show(config = config_)

# %% evaluating market trend with MA

df_trend = analysis.eval_trend_with_MAs(drop_MA_cols = True , windows=[50, 200])

# %% plot trend with MAs

MA_fig = analysis.empty_figure(fig_size = [1300,600], slider = False)
analysis.draw_trend_highlight(MA_fig, column = "MA_trend")

MA_fig.show(config = config_)

# %% using MACD to find trend of market

MACD_trend = analysis.eval_trend_with_MACD(drop_MACD_col = True )
MACD_trend_fig = market_plot.empty_figure(fig_size = [1300,600], slider = False)

analysis.draw_trend_highlight(MACD_trend_fig , column = "MACD_trend")

MACD_trend_fig.show(config = config_)


 # %%                                                       

