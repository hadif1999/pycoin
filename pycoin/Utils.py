
import datetime as dt
from typeguard import typechecked
import pandas as pd
import asyncer
from typing import Literal

@typechecked
def current_time(as_str:bool = False, as_timestamp:bool = False):
    # if as_str and as_timestamp: raise ValueError("return format can be str or timestamp, not both!")
    dt_now = dt.datetime.now()
    dt_now_ts = dt_now.timestamp().__int__() 
    if as_timestamp: 
        if as_str: return str(dt_now_ts)
        return dt_now_ts
    else: 
        if as_str: return dt.datetime.fromtimestamp(dt_now_ts).__str__()
        return dt_now
     
    
@typechecked
def dt2ts(datetime:dt.datetime ) -> int:
    """ converts datetime to timestamp data in int 

    Args:
        datetime (dt.datetime): datetime date 

    Returns:
        int: timestamp
    """        
    return dt.datetime.timestamp(datetime).__int__()


@typechecked
def ts2dt(ts:int, as_str:bool = False )-> dt.datetime|str:
    """converts timestamp to datetime format

    Args:
        ts (int): timestamp

    Returns:
        dt.datetime: returns datetime data
    """        
    dt_ = dt.datetime.fromtimestamp(ts)
    return dt_.__str__() if as_str else dt_ 


def get_Datetime_fromTimestamp(df:pd.DataFrame, timestamp_col = "Timestamp", unit = 's') -> pd.DataFrame:
    df_ = df.copy()
    df_["Datetime"] = pd.to_datetime(df_[timestamp_col], unit = unit)
    return df_


@typechecked
def change_numeric_cols_type(df:pd.DataFrame, 
                             new_type:str = "float64",  
                             except_cols:list = ["datetime", "timestamp", "time","open_time"]):
    df_ = df.copy()
    numeric_cols = [col for col in df_.columns.to_list() if not col in except_cols]
    df_[numeric_cols] = df_[numeric_cols].astype(new_type)
    return df_


@typechecked
def to_datetime_index(df:pd.DataFrame = None, time_col:str = "Datetime"):
    df_ = df.copy()
    df_.set_index(time_col, drop = True, inplace = True)
    df_.index.name = time_col
    return df_


@typechecked
def reverse_dataframe(df:pd.DataFrame):
    return df.reindex(index= df.index[::-1]).reset_index(drop = True)


Column_NameType = Literal["title", "lower", "upper"]
@typechecked
def case_col_names(dataframe:pd.DataFrame = None, method:Column_NameType = "title") -> pd.DataFrame:
        """change dataframe column names

        Args:
            df (pd.DataFrame, optional): input dataframe, if None the obj dataframe will be used.
            Defaults to None.
            method (str, optional): can be one of 'title' to capitalize first letter,
            'upper' to uppercase or 'lower' to lower case. Defaults to "title".

        Returns:
            pd.DataFrame
        """        
        
        df_ = dataframe.copy() 
        
        match method.lower():
            case "title": df_ = df_.rename(columns = {col:col.title() for col in df_.columns})
            case "lower": df_ = df_.rename(columns = {col:col.lower() for col in df_.columns})
            case "upper": df_ =  df_.rename(columns = {col:col.upper() for col in df_.columns})
            case _: 
                raise ValueError(f"method not found. it can be 'title', 'lower' or 'upper'")
        return df_
    

def add_to_ColumnNames(dataframe: pd.DataFrame, *, prefix:str = '', suffix:str = ''):
    return dataframe.rename(columns={col: prefix+col+suffix for col in dataframe.columns}).copy()


def remove_from_ColumnNames(dataframe: pd.DataFrame, *, prefix:str = '', suffix:str = ''):
    return dataframe.rename(columns={col: col.removeprefix(prefix).removesuffix(suffix) 
                              for col in dataframe.columns}).copy()
    
    
@typechecked
def isCorrectTimeframe(df:pd.DataFrame, freq_df:str ,
                    INTERVALS:dict, timestamp_col:str , verbose:bool = True):
    
    diffs = (df[timestamp_col]//1000).diff()[1:]
    unique_diffs = diffs.unique()
    
    iscorrect = True if len(unique_diffs) == 1 and unique_diffs[0] == INTERVALS[freq_df] else False
    
    if not iscorrect: 
        missing_datetimes = diffs[diffs != INTERVALS[freq_df]].index
        if verbose: print(f"""interval of your input dataframe is not {freq_df} for some rows.
                            \nmissing datetimes at:\n {missing_datetimes}""")   
    return iscorrect


@typechecked
def fill_missing_dates(df:pd.DataFrame, freq:str, INTERVALS:dict[str, int], 
                       timestamp_col:str, verbose, resetIndex:bool = False):
        df_ = df.copy()
        iscorrect = isCorrectTimeframe(df, freq, INTERVALS, timestamp_col, verbose)
        datetime_col = df["datetime"] if "datetime" in df.columns else df.index
        if not iscorrect:
            df_.set_index(datetime_col, drop = True, inplace = True)
            print("\nfilling missing dates...")
            new_inds = pd.date_range( start = str(df.index[0]),
                                      end = str(df.index[-1]),
                                      freq = freq)
        else: return df_
        
        df_ = df_.reindex(new_inds)
        df_["Datetime"] = df_.index
        cols = df_.columns.to_list().copy()
        cols_ = [col for col in cols if col.lower() not in ["datetime", "time", "timestamp"]].copy()
        df_[cols_] = df_[cols_].astype("float64").interpolate(axis=0, limit_direction = "both")
        if resetIndex: df_.reset_index(drop = True, inplace = True)
        return df_
    
    
def GetByGroup_klines(df:pd.DataFrame, grp: dict[str, int]):
    assert "datetime" in df.index.dtype.name, "index must be datetime type"
    df_grouped = df.copy()
    if "year" in grp: df_grouped = df_grouped.groupby(df_grouped.index.year).get_group(grp.get("year", 2024))
    if "month" in grp: df_grouped = df_grouped.groupby(df_grouped.index.month).get_group(grp.get("month",1))
    if "day" in grp: df_grouped = df_grouped.groupby(df_grouped.index.day).get_group(grp.get("day",1))
    if "hour" in grp: df_grouped = df_grouped.groupby(df_grouped.index.hour).get_group(grp.get("hour",1))
    if "minute" in grp: df_grouped = df_grouped.groupby(df_grouped.index.minute).get_group(grp.get("minute",0))
    return df_grouped


def get_by_datetimeRange(dataframe:pd.DataFrame , start = None, end = None ):
    df_ = dataframe.copy()
    # df_ = to_datetime_index(df_)
    if not start and end: df_ = df_.loc[:end]
    elif not end and start: df_ = df_.loc[start:]
    elif not start and not end : raise ValueError("both start and end can't be None ! ") 
    elif start and end: df_ = df_.loc[start: end]
    return df_


def add_candleType(df:pd.DataFrame):
    df_ = df.copy()
    cond = df_.Close > df_.Open
    df_.loc[cond, "candleType"] = 1
    df_.loc[~cond, "candleType"] = -1
    return df_["candleType"]


@typechecked
def getBulish_CrossedPrice(df: pd.DataFrame, Price:float, 
                           ignore_HighLow: bool = True) -> pd.DataFrame:
    
    isbullish = (df.Close > df.Open)
    betweenCloseOpen_cond = (df.Close > Price) & (df.Open < Price)
    if not ignore_HighLow:
        betweenLowOpen_cond = (Price >= df.Low) & (Price < df.Open)  
        cond = isbullish & (betweenCloseOpen_cond | betweenLowOpen_cond)
    else: cond = isbullish & betweenCloseOpen_cond
    return df.loc[cond, :]


@typechecked
def getBearish_CrossedPrice(df: pd.DataFrame, Price: float, 
                            ignore_HighLow) -> pd.DataFrame:
    isbearish = (df.Close < df.Open)
    betweenCloseOpen_cond = (df.Close < Price) & (df.Open > Price)
    if not ignore_HighLow:
        betweenHighOpen_cond = (Price <= df.High) & (Price > df.Open)
        cond = isbearish & (betweenCloseOpen_cond | betweenHighOpen_cond)
    else: cond = isbearish & betweenCloseOpen_cond
    return df.loc[cond, :]


def check_isStandard_OHLCV_dataframe(dataframe:pd.DataFrame) -> None:
    """standard OHLCV dataframe in this framework consists of 'Open', 'High', 
        'Low', 'Close', 'Volume' and datetime(pd.Timestamp) as index.
    Args:
        dataframe (pd.DataFrame): _description_
    """    
    assert "datetime" in dataframe.index.dtype.name, "dataframe index type must be pd.Timestamp(datetime)"
    cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in cols: assert col in dataframe.columns, f"column {col} not found in dataframe"


@typechecked
async def Run_Tasks_inGroup(Coroutine_Functions:list, Run:bool = True):

    async def task_runner():
        async with asyncer.create_task_group() as task_grp:
            pending_tasks = [task_grp.soonify(task)() for task in Coroutine_Functions]
        values = [task.value for task in pending_tasks]
        return values
    
    if Run:
        values = await task_runner()
        return values
    return await task_runner()

    
        


