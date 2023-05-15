#%% import market get data lib
from market_data_kline_plots.get_market_data import get_market_data

#%% load data
market = get_market_data('BTC-USDT')
btc_15min_df = market.load_kline_data('BTC-USDT|15min.csv')
#%% plot candlestick data
btc_15m_fig = market.plot_candlestick_plotly(btc_15min_df, plot_by_grp = True, year = 2022, 
                                      month = 12, slider = False, size = [1200,600])
btc_15m_fig.show()
# %% add line to plot
market.draw_line(btc_15m_fig,["2022-12-01 00:15:00",8810.592499],["2022-12-25 15:15:00",26792.4]
                 ,line_dash = "dot")


btc_15m_fig.show()
# %%
