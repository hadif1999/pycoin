import pandas as pd
from typing import List, Dict


def calc_MAs(df, column:str = "close", windows:List = [50,200] ):
    """calculate moving average with list of desired windows

    Args:
        column (str, optional): calculate on which column. Defaults to "close".
        windows (List, optional): list of windows. Defaults to [50,200].

    Returns:
        _type_: _description_
    """        
    
    df_temp = df.copy()
    
    for window in windows:
        df_temp[f"MA{str(window)}"] =  df_temp[column].rolling(window).mean()
    return df_temp

