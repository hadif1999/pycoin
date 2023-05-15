#%% import market get data lib
from market_data_kline_plots.get_market_data import get_market_data

#%% load data
market = get_market_data('BTC-USDT')
btc_15min_df = market.load_kline_data('BTC-USDT|15min.csv')
#%% plot interactive candlestick data

btc_15m_fig = market.plot_candlestick_plotly(btc_15min_df, plot_by_grp = True, year = 2022, 
                                      month = 12, fig_size = [1100,600], slider = False)

config_ = {'modeBarButtonsToAdd':['drawline','drawcircle','drawrect','eraseshape']}

btc_15m_fig.show(config = config_)

# %% add shapes to plot

# dynamic line
market.draw_line(btc_15m_fig,["2022-12-01 00:15:00",14000],["2022-12-25 15:15:00",16000]
                 , text_= "test" , text_position= 'top center')
# # rectangle
# market.draw_box(btc_15m_fig, ["2022-12-10 00:15:00",14000], ["2022-12-15 15:15:00",20000] )

# draw static line
# market.draw_static_line(btc_15m_fig, 'h', 16000, text = "test t4t4t4txt", text_position='top center')

# market.draw_static_box(btc_15m_fig, side = 'v',c0 = "2022-12-10 00:15:00",c1 = "2022-12-15 15:15:00",
#                        text ="test text box")

# btc_15m_fig.update_traces(mode="lines+markers+text")

btc_15m_fig.show(config = config_)

# %%
