#%% import market get data lib
from src.market_data_kline_plots.market_plotter import get_market_plots

#%% load data
market_plot = get_market_plots('BTC-USDT')
btc_15min_df = market_plot.load_kline_data('BTC-USDT|15min.csv', reverse = True)

# current value of symbol
# val_now = market.tick

#%% plot interactive candlestick data and pivots

btc_15m_grp_fig, btc_grp_df = market_plot.plot_candlestick_plotly(btc_15min_df, 
                                                                  plot_by_grp = True, year = 2021, 
                                                                  month = 2  , fig_size = [1100,600],
                                                                  slider = False)

# define interactive options to use 
config_ = {'modeBarButtonsToAdd':['drawline','drawcircle','drawrect','eraseshape']}


#%% market processing lib

from src.market_data_gathering.market_processing import market_processing

analysis = market_processing(btc_grp_df)

#%% plot pivots min and max

analysis.plot_all_min_max(btc_15m_grp_fig, candle_range = 200 , min_change = 0.002
                         , min_color = "red", max_color = "green", 
                         R = 350, y_scale = 0.2 )

# show added min and max pivots
btc_15m_grp_fig.show(config = config_)

market_plot.remove_all_shapes(btc_15m_grp_fig)


# %% evaluating market trend with MA

df_trend = analysis.eval_trend_with_MAs(drop_MAs = False)

# %% plot trend with MAs

analysis.draw_trend(btc_15m_grp_fig, column = "MA_trend")

btc_15m_grp_fig.show(config = config_)

# %% using MACD to find trend of market

MACD_trend = analysis.eval_trend_with_MACD()
MACD_trend_fig = market_plot.empty_figure(fig_size = [1100,600], slider = False)

analysis.draw_trend(MACD_trend_fig , column = "MACD_trend")

MACD_trend_fig.show(config = config_)

#%% plot the trend using price itself

# %%
