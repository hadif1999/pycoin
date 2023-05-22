#%% import market get data lib
from market_data_kline_plots.market_plotter import get_market_plots
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

#%% load data
market_plot = get_market_plots('BTC-USDT')
btc_15min_df = market_plot.load_kline_data('BTC-USDT|15min.csv', reverse = True)

# current value of symbol
# val_now = market.tick

#%% plot interactive candlestick data and pivots

btc_15m_grp_fig, btc_grp_df = market_plot.plot_candlestick_plotly(btc_15min_df, 
                                                                  plot_by_grp = True, year = 2022, 
                                                                  month = 8 , fig_size = [1100,600],
                                                                  slider = False)

# define interactive options to use 
config_ = {'modeBarButtonsToAdd':['drawline','drawcircle','drawrect','eraseshape']}


#%% market processing lib

from market_data_gathering.market_processing import market_processing

analysis = market_processing(btc_grp_df)

#%% plot pivots min and max

analysis.plot_all_min_max(btc_15m_grp_fig, candle_range = 200 , min_change = 0.002
                         , min_color = "red", max_color = "green", 
                         R = 350, y_scale = 0.1 )

# show added min and max pivots
btc_15m_grp_fig.show(config = config_)

market_plot.remove_all_shapes(btc_15m_grp_fig)


# %% evaluating market trend

df_trend = analysis.eval_trend_with_MAs(drop_MAs = False)

# %% plot trend


analysis.draw_trend(btc_15m_grp_fig)

# btc_15m_grp_fig.add_trace(go.Line(btc_15min_df))

btc_15m_grp_fig.show(config = config_)

# %%

