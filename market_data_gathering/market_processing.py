import pandas as pd


class market_processing:
    def __init__(self,dataframe) -> None:
        self.df = dataframe
        
    def get_market_min_max(self, dataframe:pd.DataFrame, candle_range:int = 10):
        
        window = 0
        min_pivot = []
        max_pivot = []
        
        while window < len(dataframe-1):
            
            df_temp = dataframe.iloc[ window : window+candle_range ]
            
            min_temp = df_temp[ df_temp["low"] == df_temp["low"].min() ][["datetime","low"]].values.tolist()[0]
            max_temp = df_temp[ df_temp["high"] == df_temp["high"].max() ][["datetime","high"]].values.tolist()[0]
            
            min_pivot.append( min_temp)
            max_pivot.append ( max_temp )
                    
            window = df_temp.index[-1]
        
        return min_pivot, max_pivot
             
        