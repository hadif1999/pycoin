import plotly
import pandas as pd
import kucoin.client as kc
import datetime as dt
import time
import plotly.graph_objects as go
from datetime import datetime
import re
from typing import Dict


class get_market_data: 
    
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
    
    
    def load_kline_data(self , file_name:str) -> pd.DataFrame :
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
                       LOW:str="low"):
        """converts data frame data to candlestick format. name of needed columns must be specified.

        Args:
            df (pd.DataFrame): _description_
            x (str, optional): name of time column in df (input dataframe) . Defaults to "datetime".
            open (str, optional): name of open column in df. Defaults to 'open'.
            close (str, optional): name of close column in df. Defaults to 'close'.
            high (str, optional): // high //. Defaults to 'high'.
            low (str, optional): // low // . Defaults to "low".
            

        Returns:
            _type_: candlestick data
        """        

        return go.Candlestick(x = df[X],
                open = df[OPEN],
                high = df[HIGH],
                low = df[LOW],
                close = df[CLOSE])
    
    
    
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
            
            get_grp = []
            grp_by = []
            
            if "year" in args.keys(): # if there is a year arg uses it in group by later
                if type(args["year"]) == int: 
                    get_grp.append(args["year"])
                    grp_by.append("year")
                else: raise Exception("year arg must be int")
                
            if "month" in args.keys(): # same as year
                if type(args["month"]) == int: 
                    get_grp.append(args["month"])
                    grp_by.append("month")
                else: raise Exception("month arg must be int")
                
            
            if "day" in args.keys():
                if type(args["day"]) == int: 
                    get_grp.append(args["day"])
                    grp_by.append("day")
                else: raise Exception("day arg must be int")
                
                
            
            grps = self.group_klines(dataframe , grp_by ) # group data by entered dates
            
            if len(get_grp) == 1 : grp = grps.get_group( get_grp[0] ) 
            else: grp = grps.get_group( tuple(get_grp) ) # get specified grp of data 
             
            str_temp = str(grp_by)+" : "+str(get_grp)
            
            
            if "x" in args.keys() and "open" in args.keys() and "close" in args.keys() and "low" in args.keys() and "high" in args.keys():
                fig = go.Figure(data=[ self.df2candlestick( grp, OPEN = args["open"], CLOSE = args["close"],
                                                        LOW = args["low"], HIGH = args["high"] ) ])
            
            else:
                fig = go.Figure( data=[self.df2candlestick( grp )] )
                
                
        # plot full data if plot_by_grp is False
        else: 
            fig = go.Figure( data=[self.df2candlestick( dataframe )] )
            str_temp = ""
        
        
        if "slider" in args.keys(): # add slider in x axis or not
            if type(args["slider"]) == bool:
                fig.update_layout(xaxis_rangeslider_visible = args["slider"] )
            else: raise Exception("slider param can be bool")
        
        
        
        
        if "size" in args.keys(): # changes fig size
            if type(args["size"]) == list:
                fig.update_layout( width = args["size"][0], height = args["size"][1],
                                   title = self.symbol+'  ' + str_temp,
                                   yaxis_title = self.symbol
                                 )
            else : raise Exception("fig size must be a 2 element list")
            
        return fig
    
    
    
    def draw_box(self, fig:go.Figure, p0:list[float,float], p1:list[float,float], 
                 fill_color:str = "LightSkyBlue",  ):
        """draw a rectangle with two point as p0 , p1 on input plotly object. each p0,p1 is a list as [x,y]

        Args:
            fig (go.Figure): fig object from plotly
            p0 (list[float,float]): first corner of rectangle x,y
            p1 (list[float,float]): second corner of rectangle x,y
            fill_color (str, optional): inner color of rectangle. Defaults to "LightSkyBlue".
        """        
        
        fig.add_shape( type = "rect", x0 = p0[0], y0 = p0[1], x1 = p1[0], y1 = p1[1],
                      fillcolor = fill_color, layer = "below" , opacity = 0.5
                     )
        
        
        
        
    def draw_static_line(self, fig:go.Figure, side:str, c:float, 
                         Color:str = "red", text:str = "", text_position:str = "top right" ):
        
        """draw static lines with its value as c and a plotly object.

        Args:
                fig = plotly figure object
                side = "h" for horizontal line and 'v' for vertical line.
                Color : line color
                text: a text on line
                text_position : position of text on line
        """        
        
        if side == "h" or side == "hor":  fig.add_hline(y = c, color = Color, line_dash = "dot",
                                                        annotation_text = text, 
                                                        annotation_position = text_position
                                                        )
        
        elif side == "v" or side == "ver": fig.add_vline(x = c, color = Color, line_dash = "dot",
                                                        annotation_text = text, 
                                                        annotation_position = text_position )
        
        else: raise Exception("""input side values can be 'h' or 'hor' to draw horizontal line or
                              'v' or 'ver' to draw vertical line.
                              """)
       
        
    def 
            
            
               
        
        