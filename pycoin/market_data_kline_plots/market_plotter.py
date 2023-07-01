import plotly
import pandas as pd
import kucoin.client as kc
import datetime as dt
import time
import plotly.graph_objects as go
from datetime import datetime
import re
from typing import Dict
from typing import List
import numpy as np
from ..market_data_gathering.market_processing import Market_Processing



class Market_Plotter(): 
    
    def __init__(self, process_obj:Market_Processing) -> None:
        self.market_obj = process_obj
        self.update_params
    
    @property
    def update_params(self):
        self.symbol = self.market_obj.symbol
        self.df = self.market_obj.market_df
        self.interval = self.market_obj.interval
        self.highs_df = self.market_obj.highs_df
        self.lows_df = self.market_obj.lows_df
        
    
    
    def __get_end_time(self , start_time:dt.datetime, delta_days:int = 0, delta_seconds:int = 0, **args) -> dt.datetime:
        """ this method returns new time = start_time + delta_time gets ((delta_days , delta_seconds , 
        delta_mins , delta_hours))

        Args:
            start_time (dt.datetime)
            delta_days (int)
            delta_seconds (int)

        Returns:
            dt.datetime
        """        
        
        start_ts = start_time.timestamp()
        delta_t = float( dt.timedelta(delta_days, delta_seconds, 
                                      minutes = args["delta_mins"], 
                                      hours = args["delta_hours"]).total_seconds() )
        end_ts = delta_t + start_ts
        end_date = dt.datetime.fromtimestamp(end_ts).date()
        return end_date
    
    
    
    def dt2ts( self, datetime:dt.datetime ) -> int:
        """ converts datetime to timestamp data in int 

        Args:
            datetime (dt.datetime): datetime date 

        Returns:
            int: timestamp
        """        
        return dt.datetime.timestamp(datetime).__int__()
    
    
    
    def ts2dt(self, ts:int )-> dt.datetime:
        """converts timestamp to datetime format

        Args:
            ts (int): timestamp

        Returns:
            dt.datetime: returns datetime data
        """        
        return dt.datetime.fromtimestamp(ts)
    

    
    
    def df2candlestick(self , df:pd.DataFrame, X:str = "datetime",OPEN:str = 'open', CLOSE:str = 'close', HIGH:str='high',
                       LOW:str="low", name:str = "candlestick", **kwargs ):
        """converts data frame data to candlestick format. name of needed columns must be specified.

        Args:
            df (pd.DataFrame): _description_
            x (str, optional): name of time column in df (input dataframe) . Defaults to "datetime".
            open (str, optional): name of open column in df. Defaults to 'open'.
            close (str, optional): name of close column in df. Defaults to 'close'.
            high (str, optional): // high //. Defaults to 'high'.
            low (str, optional): // low // . Defaults to "low".
       
        **kwargs:
            increase_color(str): color of increasing candles
            decrease_color(str): color of decreasing candles

        Returns:
            _type_: candlestick data
        """        
        candle_data = go.Candlestick(x = df[X],
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
        
        
        
    def __group_klines(self, df:pd.DataFrame, *grp_bys):
        """groups dataframe by ("year", "month", "day") tuple arg if specified.

        Args:
            df (pd.DataFrame): input df

        Returns:
            _type_: group object
            
        example:
            >>> self.group_klines(df , ("year" , "month" , "day")) --> groups df by year, month, day
        """      
        by = grp_bys[0]
          
        grps = []
        
        
        if "year" in by : grps.append(df["datetime"].dt.year) 
        if "month" in by : grps.append(df["datetime"].dt.month)
        if "day" in by : grps.append(df["datetime"].dt.day)
        
        if grps == []: 
            raise Exception("at least one date parameter(year or month or day must be specified)")
        
        return df.groupby(grps)
    
    
    
    def plot_market(self , plot_by_grp:bool = False, replace_df_with_grp:bool = False ,
                    show_fig:bool = False, **args):
        """plots data as candlestick format. 

        Args:
            dataframe (pd.DataFrame): input dataframe with standard column names
            
            **args : 
                    x,open,high,low,close : same as df2candlestick() name of columns related to these values can be specified
                    slider:bool use slider in x axis or not
                    size: size of figure 
        """        
        self.update_params
        dataframe = self.df.copy()
        
        if plot_by_grp:
            
            
            grp_by = {"year":0, "month":0, "day":0} # this will keep what we want to grp_by
            
            
            for key in grp_by.copy().keys() : # keeps the grp item if entered in fun args else removes from grp_by
                if key in args.keys():
                    if type(args[key]) == int :
                        grp_by[key] = args[key]
                    else: raise Exception("year, month or day must be int!")
                else: del grp_by[key]
                
            
           
            grps = self.__group_klines(dataframe , list(grp_by.keys()) ) # group data by entered dates
            
            if len( list(grp_by.keys()) ) == 1 : grp = grps.get_group( list(grp_by.values())[0] ) 
            else: grp = grps.get_group( tuple(grp_by.values()) )      # get specified grp of data 
            grp = grp.reset_index(drop = True)
                        
            # if the name of df columns are not standard they will be specified here
            if all(True if _ in args.keys() else False for _ in ["x","open","close","low"]):
                candlestick_data = self.df2candlestick( grp, OPEN = args["open"], CLOSE = args["close"],
                                                        LOW = args["low"], HIGH = args["high"],
                                                        name = self.symbol+" candlestick data"
                                                        ) 
            
            else:
                candlestick_data = self.df2candlestick( grp, name = self.symbol+" candlestick data" )
                
        else: 
            # plot full data if plot_by_grp is False
            candlestick_data = self.df2candlestick( dataframe , name = self.symbol+" candlestick data") 
             
        fig = go.Figure(  data = [candlestick_data] )
        
        # add titles and drag modes
        slider = args.get("slider",False)
        fig_size = args.get("fig_size", [1100,600] )
        
        if type(slider) != bool: raise ValueError("slider param must be bool type.")
        if type(fig_size) != list:raise ValueError(" 'fig_size' must be a 2 element list")
        
        fig.update_layout(
                          title = f"{self.symbol}|{self.interval}, date: {dataframe.datetime.iloc[0]} to {dataframe.datetime.iloc[-1]}",
                          yaxis_title = self.symbol,
                          xaxis_rangeslider_visible = slider,
                          width = fig_size[0], height = fig_size[1],
                          dragmode = "pan", margin=dict(l=15, r=10, t=35, b=12)
                         )
        
        if replace_df_with_grp: 
            self.market_obj.market_df = grp.copy()
            self.update_params
            
        if show_fig: fig.show()
        
        try: return fig, grp
        except: return fig, None
    
    
    
    
    def draw_line(self, fig:go.Figure, p0:List[float], p1:List[float], Color:str = "orange",
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
        
        fig.add_shape(type="line", x0 = p0[0], y0 = p0[1], x1 = p1[0], y1 = p1[1], 
                      line = line_ , label = label_ , editable= True) 
        
        if "line_dash" in kwargs.keys(): 
            line_["dash"] = kwargs["line_dash"]
            fig.update_shapes(line = line_ )
        

    
    
    def draw_box(self, fig:go.Figure, p0:List[float], p1:List[float], 
                 fill_color:str = "LightSkyBlue"  ):
        """draw a rectangle with two point as p0 , p1 on input plotly object. each p0,p1 is a list as [x,y]

        Args:
            fig (go.Figure): fig object from plotly
            p0 (list[float,float]): first corner of rectangle x,y
            p1 (list[float,float]): second corner of rectangle x,y
            fill_color (str, optional): inner color of rectangle. Defaults to "LightSkyBlue".
        """        
        
        fig.add_shape( type = "rect", x0 = p0[0], y0 = p0[1], x1 = p1[0], y1 = p1[1],
                      fillcolor = fill_color, layer = "below" , opacity = 0.5, editable = True
                     )
        
        
        
        
    def draw_static_line(self, fig:go.Figure, side:str, c:float, 
                         Color:str = "red", text:str = "", text_position:str = "top right", 
                         width:int=2, font_size = 20, **kwargs ):
        
        """draw static lines with its value as c and a plotly object.

        Args:
                fig = plotly figure object
                side = "h" for horizontal line and 'v' for vertical line.
                Color : line color
                text: a text on line
                text_position : position of text on line
        """        
        line_ = dict(color = Color, width = width)
        label_ = dict(text = text, textposition = text_position, font = dict(color="black",
                                                                             family="Courier New, monospace",
                                                                             size = font_size))
        
        if side == "h" or side == "hor":  fig.add_hline( y = c, line = line_ , label = label_, editable = True,
                                                        name = "helllo")
        
        elif side == "v" or side == "ver": fig.add_vline(x = c, line = line_ , label = label_, editable = True, 
                                                         kwargs = kwargs.get("name","") )
        
        else: raise Exception("""input side values can be 'h' or 'hor' to draw horizontal line or
                              'v' or 'ver' to draw vertical line.
                              """)
        if "line_dash" in kwargs.keys(): fig.update_shapes(line = dict(dash = kwargs["line_dash"]))
       
        
        
        
    def draw_static_box(self, fig:go.Figure, side:str, c0:str,c1:str ,
                         Color:str = "green", text:str = "", text_position:str = "top right" ):
        """draw a static box in a range of x or y coordinates

        Args:
            fig (go.Figure): plotly figure obj
            side (str): make box in x or y coord ('h' or 'hor' for horizontal box, 'v' or 'ver' for vertical box)
            c0 (str): starting coord of box
            c1 (str): final coord of box
            Color (str, optional): color of box. Defaults to "green".
            text (str, optional): add a text to box . Defaults to "".
            text_position (str, optional): position of text for box. Defaults to "top right".
        """        
        if side == "h" or side == "hor": fig.add_hrect(y0 = c0, y1 = c1, fillcolor = Color,
                                                       layer = "below" , opacity = 0.5, 
                                                       annotation_text = text,
                                                       annotation_position = text_position, editable = True
                                                       )
        
        if side == "v" or side == "ver": fig.add_vrect(x0 = c0, x1 = c1, fillcolor = Color,
                                                       layer = "below" , opacity = 0.5, 
                                                       annotation_text = text,
                                                       annotation_position = text_position, editable= True
                                                      )
        
        else: raise Exception("""input side values can be 'h' or 'hor' to draw horizontal box or
                        'v' or 'ver' to draw vertical box.
                        """)
        
        
    def draw_circle(self, fig:go.Figure, center:List, R:float, fillcolor:str = "green", 
                    y_scale:float = 0.1):
        
        """draws a circle at entered center which is a two element list to R radius 

        Args:
            fig (go.Figure): input figure object
            center (List): center of circle
            R (float): radius of circle ( evaluate with test beacuse scales data of y axis)
            fillcolor (str, optional): inside color of circle. Defaults to "green".
        """        
        x_c = center[0]
        if type(x_c) == pd._libs.tslibs.timestamps.Timestamp:
            x_c = str(x_c.to_pydatetime())
        
        x_center = dt.datetime.strptime(x_c , '%Y-%m-%d %H:%M:%S')
        x_0 = x_center - dt.timedelta(minutes = R)
        x_1 = x_center + dt.timedelta(minutes = R)
        
        fig.add_shape(type = "circle", fillcolor = fillcolor, layer = "below", opacity = 0.6,
                      xref="x", yref="y", x0 = x_0  , y0 = center[1]-(float(R) * y_scale), 
                      x1= x_1 , y1 = center[1]+ (float(R) * y_scale), editable = True )
        
        
    
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
        
    
    
    def remove_all_shapes( self, fig:go.Figure ):
        """remove all shapes from figure object

        Args:
            fig (go.Figure): _description_
        """        
        fig.layout.shapes = []
        
        
        
    def highlight_candle_range(self, fig:go.Figure, from_time:str, to_time:str, 
                            decrease_color:str = "lightred", increase_color:str = "lightblue" ):
        """highlight a range of candles from given time to final time

        Args:
            fig (go.Figure): plotly figure object
            from_time (str): start time
            to_time (str): end time 
            decrease_color (str, optional): color of decreasing candles. Defaults to "lightred".
            increase_color (str, optional): color of increasing candles. Defaults to "lightblue".
        """        
        df_ = self.df.copy()
        df_.set_index("datetime", inplace=True, drop = False)
        df_temp = df_.loc[ from_time : to_time ]
        
        highlight_candle = self.df2candlestick(df_temp, name = "highlight", increase_color = increase_color,
                                                    decrease_color = decrease_color)
        
        fig.add_trace(highlight_candle)
        fig.update_layout(showlegend=False)
        
    
    
    
    def highlight_single_candle(self, fig:go.Figure, time:str, color:str = "blue"):
        """highlight a single candle at given time

        Args:
            fig (go.Figure): plotly figure object
            time (str): given time
            color (str, optional): desired color of candle. Defaults to "blue".
        """        
        self.highlight_candle_range(fig, time, time , color , color)  
        fig.update_layout(showlegend=False)        
        
        
        
    def empty_figure(self, **kwargs):
        """make a empty figure

        Returns:
            go.Figure: plotly figure object
        """        
        fig = go.Figure()
        
        # add titles and drag modes
        slider = kwargs.get("slider",False)
        fig_size = kwargs.get("fig_size", [1100,600] )
        
        if type(slider) != bool: raise Exception("slider param can be bool")
        if type(kwargs["fig_size"]) != list:raise Exception(" 'fig_size' must be a 2 element list")
        
        fig.update_layout(xaxis_rangeslider_visible = slider,
                          width = fig_size[0], height = fig_size[1],
                          dragmode = "pan",  
                          margin=dict(l=15, r=10, t=35, b=12))
            
        return fig
    
    
    
    def draw_trend_highlight(self, column:str = "MA_trend",
                            dataframe:pd.DataFrame = None,
                            up_trend_color:str = "blue",
                            down_trend_color:str = "red",
                            side_trend_color:str = "yellow",
                            add_high_lows_shapes:bool = True,
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
        self.update_params
        fig = self.empty_figure(fig_size = kwargs.get("fig_size",[1100,600]),
                                slider = kwargs.get("slider",False))
        
        if add_high_lows_shapes:
            shapes = self.plot_high_lows(return_only_shapes = True, R = kwargs.get("R",1000),
                                         y_scale= kwargs.get("y_scale",0.1))
            fig.layout.shapes = shapes        
        
        try: df_ = dataframe.copy()
        except: df_ = self.df.copy()
            
        trend_grps = df_.copy().groupby(column, sort = True)
        
        colors = [down_trend_color , side_trend_color , up_trend_color]
        trend_names = list(trend_grps.groups.keys())
        colors_dict = {key:color for key,color in zip(trend_names,colors)}
          
        for name,grp in trend_grps :
            for i,row in grp.iterrows():
                self.highlight_single_candle(fig, row["datetime"], color = colors_dict[name] )
                
        fig.update_layout( title = f"{self.symbol} | {self.interval}, trend evaluated with: {column}",
                          yaxis_title = self.symbol
                         )
        
        
        return fig
        
        
        
    
    def plot_high_lows(self, min_color:str = "red", max_color:str = "green" ,
                                R:int = 400, y_scale:float = 0.1, 
                                return_only_shapes:bool = False, **kwargs):
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
        
        self.update_params

        fig,_ = self.plot_market(
                                 plot_by_grp = False,
                                 fig_size = kwargs.get("fig_size",[1100,600]),
                                 slider = kwargs.get("slider",False)
                                )
        
        if self.highs_df == None or self.lows_df == None : 
            raise ValueError("""you didn't calculate highs and lows yet!
                                do this by running obj.get_market_high_lows method.""")
        
        for low_coord in self.lows_df:
            self.draw_circle(fig = fig, center = low_coord, R = R , fillcolor = min_color , y_scale = y_scale )
            
        for high_coord in self.highs_df:
            self.draw_circle(fig = fig, center = high_coord, R = R , fillcolor = max_color , y_scale = y_scale )

        fig.update_layout(
                          title = f"{self.symbol}|{self.interval}, date: {self.df.datetime.iloc[0]} to {self.df.datetime.iloc[-1]}",
                          yaxis_title = self.symbol
                         )
                    
        if return_only_shapes: return fig.layout.shapes
        else: return fig
        
    
        
    
    
    

                   
        
        
    
        
        
        
    
    
        
        
            
            
               
        
        
