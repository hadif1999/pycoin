import pandas as pd
import datetime as dt
import plotly.graph_objects as go
from typing import List
from typing import Any
from pycoin.data_gathering import get_market_High_Lows
from pycoin import Utils
from freqtrade.exchange import timeframe_to_seconds, timeframe_to_minutes
import math



class Market_Plotter: 
        
    def __init__(self, OHLCV_df:pd.DataFrame, **kwargs) -> None:
        self.df = OHLCV_df
        Utils.check_isStandard_OHLCV_dataframe(OHLCV_df)        
        self.fig = self.empty_figure()
        self.Name = getattr(self.df, "Name", "")
        
        self.fig_config = { "slider" : kwargs.get("slider", False),
                           "fig_size": kwargs.get("fig_size", [1100,600]) }
         
        self.show_config={'modeBarButtonsToAdd': ['drawline',
                                        'drawopenpath',
                                        'drawclosedpath',
                                        'drawcircle',
                                        'drawrect',
                                        'eraseshape'
                                       ]}

    
    
    def df2candlestick(self , df:pd.DataFrame,*, OPEN:str = 'Open',
                       CLOSE:str = 'Close', HIGH:str='High',
                       LOW:str="Low", name:str = "candlestick", **kwargs ):
     
        candle_data = go.Candlestick(x = df.index,
                                     open = df[OPEN],
                                     high = df[HIGH],
                                     low = df[LOW],
                                     close = df[CLOSE],
                                     name = name
                                    )
        
        if "increase_color" in kwargs.keys() : 
            candle_data.increasing.fillcolor = kwargs["increase_color"]
            candle_data.increasing.line.color = kwargs["increase_color"]
            
        if "decrease_color" in kwargs.keys() : 
            candle_data.decreasing.fillcolor = kwargs["decrease_color"]
            candle_data.decreasing.line.color = kwargs["decrease_color"]
            
        return candle_data
    
    
    
    def plot_market(self,*, plot_by_grp:bool = False, 
                    grp:dict[str, int] = {"year":2023, "month":1, "day":1},
                    show_fig:bool = False, **kwargs):
        """plots data as candlestick format. 

        Args:
            dataframe (pd.DataFrame): input dataframe with standard column names
            
            **args : 
                    x,open,high,low,close : same as df2candlestick() name of columns related to these values can be specified
                    slider:bool use slider in x axis or not
                    size: size of figure 
        """        
        dataframe = self.df.copy()
        dataframe.Name = getattr(self.df, "Name", "")
        
        if plot_by_grp:
            dataframe = Utils.GetByGroup_klines(dataframe, grp = grp)
            
        candleStick_data = self.df2candlestick(dataframe, **kwargs)

        fig = go.Figure(  data = [candleStick_data] )
        
        # add titles and drag modes
        slider = self.fig_config.get("slider")
        fig_size = self.fig_config.get("fig_size")
        
        assert isinstance(slider, bool), "slider param must be bool type."
        assert isinstance(fig_size, list), " 'fig_size' must be a 2 element list"
        
        fig.update_layout(
                          title = f"{self.Name}, date ->from: {dataframe.index[0]}  to: {dataframe.index[-1]}",
                          yaxis_title = f"{self.Name}",
                          xaxis_rangeslider_visible = slider,
                          width = fig_size[0], height = fig_size[1],
                          dragmode = "pan", margin=dict(l=15, r=10, t=35, b=12)
                         )
        if show_fig: fig.show(config = self.show_config)
        self.fig = fig
        return fig    
    
    
    def show(self):
        self.fig.show(config = self.show_config)
        
    def reset(self, **kwargs):
        self.fig = self.empty_figure(**kwargs)
    
    
    def add_line(self, p0:List[float], p1:List[float], Color:str = "orange",
                  width_:int = 2, text_:str = "", text_position:str = "top right", **kwargs):
        """draws a line on given plotly figure obj starting with point p0:(x0,y0) to p1: (x1,y1)

        Args:
            fig (go.Figure): figure object
            p0 (List[float]): first point of line
            p1 (List[float]): second point of line
            Color (str, optional): desired color for line. Defaults to "yellow".
            width (int, optional): width of line. Defaults to 2.
            text (str, optional): text on line. Defaults to "".
            text_position (str, optional): position of text. Defaults to "top right".
        kwargs:
            line_dash : dash type ('dot' for example)
        """        
        line_ = dict(color = Color, width = width_)
        label_ = dict(text = text_, textposition = text_position) 
        
        self.fig.add_shape(type="line", x0 = p0[0], y0 = p0[1], x1 = p1[0], y1 = p1[1], 
                           line = line_ , label = label_ , editable= True) 
        
        if "line_dash" in kwargs: 
            line_["dash"] = kwargs["line_dash"]
            self.fig.update_shapes(line = line_ )
        

    def add_box(self, p0:List[float], p1:List[float], 
                 fill_color:str = "LightSkyBlue", **kwargs  ):
        """draw a rectangle with two point as p0 , p1 on input plotly object. each p0,p1 is a list as [x,y]

        Args:
            fig (go.Figure): fig object from plotly
            p0 (list[float,float]): first corner of rectangle x,y
            p1 (list[float,float]): second corner of rectangle x,y
            fill_color (str, optional): inner color of rectangle. Defaults to "LightSkyBlue".
        """        
        
        self.fig.add_shape( type = "rect", x0 = p0[0], y0 = p0[1], x1 = p1[0], y1 = p1[1],
                      fillcolor = fill_color, 
                      layer = kwargs.get("layer", "below") , 
                      opacity = kwargs.get("opacity", 0.5),
                      editable = True
                     )
        
        
    def add_hline(self, price:float, color:str = "red", txt:str = "",
                  txt_position:str = "top right", width:int = 2,
                  font_size:int = 20, **kwargs):
        line_ = dict(color = color, width = width)
        label_ = dict(text = txt, textposition = txt_position,
                      font = dict(color="black", family="Courier New, monospace",
                                  size = font_size))
        self.fig.add_hline(price, line = line_, label = label_, editable = True,
                           name = kwargs.get("name","line"), **kwargs)
        
        
    def add_vline(self, time:str|dt.datetime, color:str = "red", txt:str = '',
                  txt_position:str = "top right", width:int = 2,
                  font_size:int = 20, **kwargs):
        line_ = dict(color = color, width = width)
        label_ = dict(text = txt, textposition = txt_position,
                      font = dict(color="black", family="Courier New, monospace",
                                  size = font_size))
        self.fig.add_hline(time, line = line_, label = label_, editable = True,
                           name = kwargs.get("name","line"), **kwargs)
    
    
    def add_vrect(self, time1:str|dt.datetime, time2:str|dt.datetime, 
                  color = "green", txt:str = "", txt_position:str = "top right", **kwargs):
        self.fig.add_vrect(x0 = time1, x1 = time2, fillcolor = color,
                      layer = "below" , opacity = kwargs.get("opacity", 0.5), 
                      annotation_text = txt,
                      annotation_position = txt_position, editable= True, **kwargs)
        
    def add_hrect(self, price1: float, price2: float, color = "green",
                  txt:str = "", txt_position:str = "top right", **kwargs):
        self.fig.add_hrect(x0 = price1, x1 = price2, fillcolor = color,
                      layer = "below" , opacity = kwargs.get("opacity", 0.5), 
                      annotation_text = txt,
                      annotation_position = txt_position, editable= True, **kwargs)
        
        
    def add_circle(self, center:List, R:float = 1, fillcolor:str = "green", 
                   timeframe = "5m", y_len = 3,  **kwargs):
        
        """draws a circle at entered center which is a two element list to R radius 

        Args:
            fig (go.Figure): input figure object
            center (List): center of circle
            R (float): radius of circle ( evaluate with test beacuse scales data of y axis)
            fillcolor (str, optional): inside color of circle. Defaults to "green".
        """        
        assert len(center) == 2, "center list len must be 2"
        x_c = center[0]
        if type(x_c) == pd._libs.tslibs.timestamps.Timestamp:
            x_c = str(x_c.to_pydatetime())
        
        x_center = dt.datetime.strptime(x_c , '%Y-%m-%d %H:%M:%S')
        dx = timeframe_to_seconds(timeframe)*y_len
        x_0 = dt.datetime.fromtimestamp(int(x_center.timestamp() - dx ))
        x_1 = dt.datetime.fromtimestamp(int(x_center.timestamp() + dx ))        
        
        y_0 = center[1]- math.log(center[1]) * R 
        y_1 = center[1]+ math.log(center[1]) * R 
        
        self.fig.add_shape(type = "circle", fillcolor = fillcolor, 
                           layer = "below",
                           opacity = kwargs.get("opacity", 0.6),
                           xref="x", yref="y", x0 = x_0  , y0 = y_0, 
                           x1= x_1 , y1 = y_1, editable = True )
        
        
    
    def add_text(self, fig:go.Figure, text:str, p:List, arrow:bool= False , y_shift:int = 15, 
                 font_size:int = 14, font_color:str = "black", text_angle:int=0 ,  **kwargs ):
        """add a text annotation at given coordinates

        Args:
            fig (go.Figure): plotly figure object
            text (str): the text to insert
            p (List): coordinates of text
            arrow (bool, optional): put a arrow pointing at coordinates or not. Defaults to False.
            y_shift (int, optional): how much shift the text place from it's y coord. Defaults to 15.
            font_size (int, optional): text font size. Defaults to 14.
            font_color (str, optional): color of text. Defaults to "black".
            text_angle (int, optional): angle of text. Defaults to 0.
        """        
        
        fig.add_annotation(x=p[0], y=p[1], text = text, showarrow = arrow, yshift = y_shift, 
                           font= dict( size = font_size, color = font_color), textangle = text_angle)
        
    
    
    def remove_all_shapes( self ):
        """remove all shapes from figure object

        Args:
            fig (go.Figure): _description_
        """        
        self.fig.layout.shapes = []
        
        
        
    def empty_figure(self, inplace: bool = False, **kwargs):
        """make a empty figure

        Returns:
            go.Figure: plotly figure object
        """        
        fig = go.Figure()
        # add titles and drag modes
        slider = kwargs.get("slider",False)
        fig_size = kwargs.get("fig_size", [1100,600] )
        
        assert isinstance(slider, bool),"slider param can be bool"
        assert isinstance(fig_size, list), " 'fig_size' must be a 2 element list"
        
        fig.update_layout(xaxis_rangeslider_visible = slider,
                          width = fig_size[0], height = fig_size[1],
                          dragmode = "pan",  
                          margin=dict(l=15, r=10, t=35, b=12))
        if inplace: self.fig = fig
        return fig
    
    
    
    def plot_trend(self, column:str = "MA_trend", * ,
                  up_trend_color:str = "blue",
                  down_trend_color:str = "red",
                  side_trend_color:str = "yellow", 
                  size = 1,
                  **kwargs):
        """visualizes the evaluated trend with highlighted candles.

        Args:
            fig (go.Figure): add trend plot to this fig.
            column (str, optional): name of the trend col you want to plot. Defaults to "MA_trend".
            dataframe (pd.DataFrame, optional): you can give a new df else it will use self.df.
            Defaults to None.
            up_trend_color (str, optional): color of up_trend candles. Defaults to "blue".
            down_trend_color (str, optional): color of down_trend candles. Defaults to "red".
            side_trend_color (str, optional): color of side_trend candles. Defaults to "yellow".
        """        
        trend_grp = self.df.groupby(column)
        colors = [down_trend_color , side_trend_color , up_trend_color]
        shapes = ["triangle-down", "triangle-right", "triangle-up"]
        trend_labels = sorted(list(trend_grp.groups.keys()))
        trend_names = ["downtrend", "sideway trend", "uptrend"]
          
        for label, color, shape, name in zip(trend_labels, colors, shapes, trend_names):
            trend_df = trend_grp.get_group(label)
            yaxis = trend_df[["Close", "Open"]].mean(axis=1)
            self.fig.add_trace(go.Scatter(mode="markers",x=yaxis.index, 
            y=yaxis, marker=dict(size=size, color = color, symbol= shape,
            line=dict(width=0.1, color="black", )), name = name, **kwargs ) )
                            
        self.fig.update_layout( title = f"{self.Name}, trend evaluated with: {column}",
                          yaxis_title = self.Name)
        return self.fig
        
        
        
    
    def plot_HighLows(self, HighLows_col = "Pivot", plot_onColumn:str = "Close",
                      low_color:str = "red", high_color:str = "green",
                      low_label = -1, high_label = 1, highs_shape = "circle",
                      lows_shape = "circle", size:int = 1, **kwargs):
        """adds circle shapes for highs and lows for visualizing.

        Args:
            fig (go.Figure): adds shapes to this fig
            min_color (str, optional): color of lows circle. Defaults to "red".
            max_color (str, optional): color of highs circle. Defaults to "green".
            R (int, optional): radius of circle. Defaults to 400.
            y_scale (float, optional): scales the y coord of circle(price) if needed. Defaults to 0.1.

        Raises:
            ValueError: _description_
        """        

        hl_grp = self.df.groupby(HighLows_col)
        highs_df = hl_grp.get_group(high_label) 
        lows_df = hl_grp.get_group(low_label)
        
        self.fig.add_trace(go.Scatter(mode="markers",x=highs_df.index, y=highs_df[plot_onColumn],
        marker=dict(size=size, color = high_color, symbol=highs_shape,
                    line=dict(width=0.1, color="black")), name = "high", **kwargs ) )
        
        self.fig.add_trace(go.Scatter(mode="markers",x=lows_df.index, y=lows_df[plot_onColumn],
        marker=dict(size=size, symbol=lows_shape, color = low_color, 
                    line=dict(width=0.1, color="black")), name = "low", **kwargs) )
        
        self.fig.update_layout(
        title = f"{self.Name}, date->from: {self.df.index[0]}   to: {self.df.index[-1]}",
        yaxis_title = self.Name )
                    
        return self.fig
        
    
        
    
    
    

                   
        
        
    
        
        
        
    
    
        
        
            
            
               
        
        
