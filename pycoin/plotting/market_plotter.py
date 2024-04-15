import pandas as pd
import datetime as dt
import plotly.graph_objects as go
from typing import List
from typing import Any
from pycoin.data_gathering import get_market_High_Lows
from pycoin import Utils



class Market_Plotter: 
        
    def __init__(self, OHLCV_df:pd.DataFrame) -> None:
        self.df = OHLCV_df
        Utils.check_isStandard_OHLCV_dataframe(OHLCV_df)        
        self.fig = self.empty_figure()
        self.Name = getattr(self.df, "Name", "")

    
    
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
                    show_fig:bool = False, inplace: bool = True, **kwargs):
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
        slider = kwargs.get("slider", False)
        fig_size = kwargs.get("fig_size", [1100,600])
        
        assert isinstance(slider, bool), "slider param must be bool type."
        assert isinstance(fig_size, list), " 'fig_size' must be a 2 element list"
        
        fig.update_layout(
                          title = f"{self.Name}, date ->from: {dataframe.index[0]}  to: {dataframe.index[-1]}",
                          yaxis_title = f"{self.Name}",
                          xaxis_rangeslider_visible = slider,
                          width = fig_size[0], height = fig_size[1],
                          dragmode = "pan", margin=dict(l=15, r=10, t=35, b=12)
                         )
        if show_fig: fig.show()
        if inplace: self.fig = fig
        return fig    
    
    
    
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
        if side in ["h", "hor"]:  fig.add_hline( y = c, line = line_ , 
                                                label = label_,
                                                editable = True,
                                                name = kwargs.get("name","") )
        
        elif side in ["v", "ver"]: fig.add_vline(x = c, line = line_ , label = label_, 
                                                 editable = True, name = kwargs.get("name",""))
        
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
        if side in ["hor", 'h']: fig.add_hrect(y0 = c0, y1 = c1, fillcolor = Color,
                                            layer = "below" , opacity = 0.5, 
                                            annotation_text = text,
                                            annotation_position = text_position, editable = True
                                                       )
        
        if side in ["ver", 'v']: fig.add_vrect(x0 = c0, x1 = c1, fillcolor = Color,
                                            layer = "below" , opacity = 0.5, 
                                            annotation_text = text,
                                            annotation_position = text_position, editable= True
                                                      )
        
        else: raise Exception("""input side values can be 'h' or 'hor' to draw horizontal box or
                        'v' or 'ver' to draw vertical box.
                        """)
        
        
    def draw_circle(self, fig:go.Figure, center:List, R:float, fillcolor:str = "green", 
                    y_scale:float = 0.1, **kwargs):
        
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
        df_.Name = getattr(self.df, "Name", "")
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
        
        assert isinstance(slider, bool),"slider param can be bool"
        assert isinstance(fig_size, list), " 'fig_size' must be a 2 element list"
        
        fig.update_layout(xaxis_rangeslider_visible = slider,
                          width = fig_size[0], height = fig_size[1],
                          dragmode = "pan",  
                          margin=dict(l=15, r=10, t=35, b=12))
            
        return fig
    
    
    
    def draw_trend_highlight(self, column:str = "MA_trend",
                            dataframe:pd.DataFrame = pd.DataFrame(), * ,
                            up_trend_color:str = "blue",
                            down_trend_color:str = "red",
                            side_trend_color:str = "yellow" , 
                            add_high_lows_shapes:bool = False,
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
        
        fig = self.empty_figure(fig_size = kwargs.get("fig_size",[1100,600]),
                                slider = kwargs.get("slider",False))
        
        if dataframe.empty: 
            df_ = self.df.copy()
            df_.Name = getattr(self.df, "Name", "")
        else: 
            df_ = dataframe.copy()
            df_.Name = getattr(self.df, "Name", "")
            
            
            
        if add_high_lows_shapes:
            shapes = self.plot_high_lows(dataframe = df_,
                                        return_only_shapes = True,
                                        R = kwargs.get("R",1000),
                                        y_scale= kwargs.get("y_scale",0.1))
            fig.layout.shapes = shapes        
        
        
        if "Datetime" not in df_.columns: df_["Datetime"] = df_.index
        trend_grps = df_.copy().groupby(column, sort = True)
        
        colors = [down_trend_color , side_trend_color , up_trend_color]
        trend_names = list(trend_grps.groups.keys())
        colors_dict = {key:color for key,color in zip(trend_names,colors)}
          
        for name,grp in trend_grps :
            for i,row in grp.iterrows():
                self.highlight_single_candle(fig, row["Datetime"], color = colors_dict[name] )
        fig.update_layout( title = f"{self.Name}, trend evaluated with: {column}",
                          yaxis_title = self.Name
                         )
        return fig
        
        
        
    
    def plot_high_lows(self, dataframe: pd.DataFrame, HighLows_col = "Pivot" ,
                       min_color:str = "red", max_color:str = "green" ,
                        R:int = 400, y_scale:float = 0.1, *, 
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

        fig = self.plot_market(
                                 plot_by_grp = False,
                                 fig_size = kwargs.get("fig_size",[1100,600]),
                                 slider = kwargs.get("slider",False)
                                )
        
        df_ = dataframe.copy()
        df_.Name = getattr(self.df, "Name", "")
        if "Datetime" not in df_.columns: df_["Datetime"] = df_.index
        highlows_grp = df_.groupby(HighLows_col)
        highs = highlows_grp.get_group(1)[["Datetime","High"]].values.tolist()
        lows = highlows_grp.get_group(-1)[["Datetime","Low"]].values.tolist()
            
        for low_coord in lows:
            self.draw_circle(fig = fig, center = low_coord, R = R , fillcolor = min_color , y_scale = y_scale )
            
        for high_coord in highs:
            self.draw_circle(fig = fig, center = high_coord, R = R , fillcolor = max_color , y_scale = y_scale )

        fig.update_layout(
                          title = f"{self.Name}, date -> from: {self.df.index[0]}   to: {self.df.index[-1]}",
                          yaxis_title = self.Name
                         )
                    
        if return_only_shapes: return fig.layout.shapes
        return fig
        
    
        
    
    
    

                   
        
        
    
        
        
        
    
    
        
        
            
            
               
        
        
