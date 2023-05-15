#%% import market get data lib
from market_data_kline_plots.get_market_data import get_market_data

#%% load data
market = get_market_data('BTC-USDT')
btc_15min_df = market.load_kline_data('BTC-USDT|15min.csv')
#%% plot data
btc_15m_fig = market.plot_candlestick_plotly(btc_15min_df, plot_by_grp = True, year = 2022, 
                                      month = 12, slider = False, size = [1200,600])
# %%
candles = market.df2candlestick(btc_15min_df)
# %%
