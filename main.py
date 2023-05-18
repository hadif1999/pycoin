#%% import market get data lib
from market_data_kline_plots.market_plotter import get_market_plots

#%% load data
market = get_market_plots('BTC-USDT')
btc_15min_df = market.load_kline_data('BTC-USDT|15min.csv', reverse = True)

# current value of symbol
val_now = market.get_tick()

#%% plot interactive candlestick data and pivots

btc_15m_fig, btc_grp_df = market.plot_candlestick_plotly(btc_15min_df, plot_by_grp = True, year = 2021, 
                                      month = 12, fig_size = [1100,600], slider = False)

# define interactive options to use 
config_ = {'modeBarButtonsToAdd':['drawline','drawcircle','drawrect','eraseshape']}


#%% plot pivots min and max

from market_data_gathering.market_processing import market_processing

process = market_processing(btc_grp_df)

process.remove_all_shapes(btc_15m_fig)

# plot min, max pivots
process.plot_all_min_max(btc_15m_fig, candle_range = 200 , min_change = 0.003 , min_color = "red",
                         max_color = "green", R = 350, y_scale = 0.8 )

# show final plot
btc_15m_fig.show(config = config_)


# %% highlight some candles
process.highlight_candle_range(btc_15m_fig, "2021-12-10 00:15:00","2021-12-17 23:45:00")
    
# %%
