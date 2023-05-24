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


class get_market_plots: 
    
    def __init__(self, symbol) -> None:
        self.symbol = symbol
        self.market = kc.Market(url = 'https://api.kucoin.com')
        
        
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
    
    
    
    def __dt2ts( self, datetime:dt.datetime ) -> int:
        """ converts datetime to timestamp data in int 

        Args:
            datetime (dt.datetime): datetime date 

        Returns:
            int: timestamp
        """        
        return dt.datetime.timestamp(datetime).__int__()
    
    
    
    def __ts2dt(self, ts:int )-> dt.datetime:
        """converts timestamp to datetime format

        Args:
            ts (int): timestamp

        Returns:
            dt.datetime: returns datetime data
        """        
        return dt.datetime.fromtimestamp(ts)
    
    
    
    def get_kline_as_df(self, interval:str ="15min" , reverse_df:bool = False, end_timestamp:int = None , 
                        start_timestamp:int = dt.datetime(2017,1,1).timestamp().__int__() ) -> pd.DataFrame:
    
        
        cols = ["timestamp",'open','close','high','low','volume','turnover']
        df_temp = pd.DataFrame(columns = cols)
        
        if end_timestamp == None:
            current_timestamp = int(self.market.get_server_timestamp()*1e-3) # current ts milisec to sec
            ts_temp_end = current_timestamp
        else: ts_temp_end = end_timestamp
        
        
        while 1 :
            try:
            # returns timestamp(newest date comes first), open, close, high, low, volume, turnover
                ts_temp_last = ts_temp_end # saves last timestamp
                candles_temp = self.market.get_kline(self.symbol, interval , startAt = start_timestamp, endAt = ts_temp_end ) # read kline data from kucoin api
                ts_temp_end = int(candles_temp[-1][0]) # get last timestamp of each bunch of data
                
                if reverse_df : candles_temp.reverse() # reverses dataframe if specified

                candle_df_temp = pd.DataFrame(candles_temp, columns = cols) # convert current data bunch to df
                df_temp = pd.concat( [df_temp,candle_df_temp], axis=0, ignore_index = True ) # updating final df

                # exits loop if we arrived at start_timestamp (smallest date)
                if ts_temp_end <= start_timestamp : break 
                
                print("\n\nfirst datetime till now is: ",
                    self.ts2dt( int(df_temp.iloc[0].timestamp) ) ,
                    "\nlast datetime till now is: ",
                    self.ts2dt( int(df_temp.iloc[-1].timestamp) )
                    )
                

            except : 
            
                if ts_temp_end == ts_temp_last : # check if we got the data of new timestamp else exits loop
                    print("\n\n****final first datetime is: ",
                    self.ts2dt( int(df_temp.iloc[0].timestamp) ),
                    "\n****final last datetime is: ",
                    self.ts2dt( int(df_temp.iloc[-1].timestamp) )
                        )
                    print("\n\ndone")
                    break
                
                time.sleep(10)
                continue
        
        df_temp["timestamp"] = df_temp.timestamp.astype("Int64")
        df_temp[df_temp.columns.to_list()[1:]] = df_temp[df_temp.columns.to_list()[1:]].astype("Float64") 
        df_temp["datetime"] = pd.to_datetime(df_temp["timestamp"],unit = 's')
        df_temp = df_temp[["timestamp","datetime",'open','close','high','low','volume','turnover']]
        return df_temp
    
    
    
    
    def load_kline_data(self , file_name:str, reverse:bool = False) -> pd.DataFrame :
        """reads kline date in .csv or .xlsx format.

        Args:
            file_name (str): name of file in current dir
        return:
            output dataframe
        """        
        
        if "csv" in file_name: df = pd.read_csv(file_name)
        elif "xlsx" in file_name : df = pd.read_excel(file_name)
        else : "file format must be .csv or .xlsx"

        # converting format of data columns
        df["timestamp"] = df.timestamp.astype("Int64")
        df["datetime"] = pd.to_datetime( df["timestamp"], unit = 's')
        df = df[["timestamp","datetime",'open','close','high','low','volume','turnover']]
        df[ df.columns.to_list()[2:] ] = df[ df.columns.to_list()[2:] ].astype("Float64")
        
        if reverse: df = df.reindex(index= df.index[::-1])
        df.reset_index(drop = True, inplace = True)
        
        return df
    

    
    def group_klines(self, df:pd.DataFrame, *grp_bys):
        """groups dataframe by ("year", "month", "day") tuple arg if specified.

        Args:
            df (pd.DataFrame): input df

        Returns:
            _type_: group object
            
        example:
            self.group_klines(df , ("year" , "month" , "day")) --> groups df by year, month, day
        """      
        by = grp_bys[0]
          
        grps = []
        
        
        if "year" in by : grps.append(df["datetime"].dt.year) 
        if "month" in by : grps.append(df["datetime"].dt.month)
        if "day" in by : grps.append(df["datetime"].dt.day)
        
        if grps == []: 
            raise Exception("at least one date parameter(year or month or day must be specified)")
        
        return df.groupby(grps)
    
    
    
    
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
        
        
    
    
    
    def plot_candlestick_plotly(self , dataframe:pd.DataFrame, plot_by_grp:bool = True , **args):
        """plots data as candlestick format. 

        Args:
            dataframe (pd.DataFrame): input dataframe with standard column names
            
            **args : 
                    x,open,high,low,close : same as df2candlestick() name of columns related to these values can be specified
                    slider:bool use slider in x axis or not
                    size: size of figure 
        """        
        if plot_by_grp:
            
            get_grp = [] # this will keep selected group data
            grp_by = ["year","month","day"] # this will keep what we want to grp_by
            
            
            for item in grp_by: # keeps the grp item if entered in fun args else removes from grp_by
                if item in args.keys():
                    if type(args[item]) == int :
                        get_grp.append(args[item])
                    else: raise Exception("year, month or day must be int!")
                else: grp_by.remove(item)
            
            
            grps = self.group_klines(dataframe , grp_by ) # group data by entered dates
            
            if len(get_grp) == 1 : grp = grps.get_group( get_grp[0] ) 
            else: grp = grps.get_group( tuple(get_grp) )      # get specified grp of data 
            grp = grp.reset_index(drop = True)
            
            str_temp = str(grp_by)+" : "+str(get_grp) 
            
            # if the name of df columns are not standard they will be specified here
            if "x" in args.keys() and "open" in args.keys() and "close" in args.keys() and "low" in args.keys() and "high" in args.keys():
                candlestick_data = self.df2candlestick( grp, OPEN = args["open"], CLOSE = args["close"],
                                                        LOW = args["low"], HIGH = args["high"],
                                                        name = self.symbol+" candlestick data"
                                                        ) 
            
            else:
                candlestick_data = self.df2candlestick( grp, name = self.symbol+" candlestick data" )
                
        
        else: 
            # plot full data if plot_by_grp is False
            candlestick_data = self.df2candlestick( dataframe , name = self.symbol+" candlestick data") 
            str_temp = ""
             
        
        
        fig = go.Figure(  data = [candlestick_data] )
        
        # add titles and drag modes
        fig.update_layout(title = self.symbol+'  ' + str_temp,
                          yaxis_title = self.symbol, dragmode = "pan",  
                          margin=dict(l=15, r=10, t=35, b=12) )
        
        
        if "slider" in args.keys(): # add slider in x axis or not
            if type(args["slider"]) == bool:
                fig.update_layout(xaxis_rangeslider_visible = args["slider"] )
            else: raise Exception("slider param can be bool")
        
        
        if "fig_size" in args.keys(): # changes fig size
            if type(args["fig_size"]) == list:
                fig.update_layout( width = args["fig_size"][0], height = args["fig_size"][1] )
            else : raise Exception(" 'fig_size' must be a 2 element list")
                        
        try: return fig, grp
        except: return fig
    
    
    
    
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
        
        if side == "h" or side == "hor":  fig.add_hline( y = c, line = line_ , label = label_, editable = True )
        
        elif side == "v" or side == "ver": fig.add_vline(x = c, line = line_ , label = label_, editable = True )
        
        else: raise Exception("""input side values can be 'h' or 'hor' to draw horizontal line or
                              'v' or 'ver' to draw vertical line.
                              """)
        if "line_dash" in kwargs.keys(): fig.update_shapes(line = dict(dash = kwargs["line_dash"]))
       
        
        
        
    def draw_static_box(self, fig:go.Figure, side:str, c0:str,c1:str ,
                         Color:str = "green", text:str = "", text_position:str = "top right" ):
        
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
        "adds text to plotly figure object"
        
        fig.add_annotation(x=p[0], y=p[1], text = text, showarrow = arrow, yshift = y_shift, 
                           font= dict( size = font_size, color = font_color), textangle = text_angle)
        
    
    
    def remove_all_shapes( self, fig:go.Figure ):
        fig.layout.shapes = []
        
        
        
    def highlight_candle_range(self, fig:go.Figure, from_time:str, to_time:str, 
                            decrease_color:str = "black", increase_color:str = "black" ):
        df_ = self.df.copy()
        df_.set_index("datetime", inplace=True, drop = False)
        df_temp = df_.loc[ from_time : to_time ]
        
        highlight_candle = self.df2candlestick(df_temp, name = "highlight", increase_color = increase_color,
                                                    decrease_color = decrease_color)
        
        fig.add_trace(highlight_candle)
        
    
    
    
    def highlight_single_candle(self, fig:go.Figure, time, color:str = "blue"):
        self.highlight_candle_range(fig, time, time , color , color)  
        
        
    def empty_figure(self, **kwargs):
        fig = go.Figure()
        
        # add titles and drag modes
        fig.update_layout(
                          dragmode = "pan",  
                          margin=dict(l=15, r=10, t=35, b=12)
                         )
        
        if "slider" in kwargs.keys(): # add slider in x axis or not
            if type(kwargs["slider"]) == bool:
                fig.update_layout(xaxis_rangeslider_visible = kwargs["slider"] )
            else: raise Exception("slider param can be bool")
        
        
        if "fig_size" in kwargs.keys(): # changes fig size
            if type(kwargs["fig_size"]) == list:
                fig.update_layout( width = kwargs["fig_size"][0], height = kwargs["fig_size"][1] )
            else : raise Exception(" 'fig_size' must be a 2 element list")
            
        return fig
                   
        
        
    
        
        
        
    
    
        
        
            
            
               
        
        
