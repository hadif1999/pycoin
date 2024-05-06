import pandas as pd
import datetime as dt

def fill_between_same_exterma(df_:pd.DataFrame, exterma_col:str = "HighLows", 
                              low_label:int = -1, high_label = 1, date_col:str = "Date",
                              low_column:str = "Close", high_column:str = "Close", **kwargs):
    
    from pycoin.Utils import check_isStandard_OHLCV_dataframe, get_by_datetimeRange
    df = df_.copy()
    check_isStandard_OHLCV_dataframe(df, True)
    if date_col not in df.columns: df[date_col] = df.index
    pos_grp = df.groupby(exterma_col)
    highs_df, lows_df = pos_grp.get_group(high_label), pos_grp.get_group(low_label)
    
    # filling between lows
    for i, (current_date, row) in enumerate(lows_df.iterrows()):
        if len(lows_df)-1 in [i, i+1]: break
        next_row = lows_df.iloc[i+1]
        highs_between = get_by_datetimeRange(highs_df, current_date, next_row.Date) 
        if highs_between.empty:
            new_high = df.loc[current_date: next_row.Date, high_column].max()
            df.loc[ df[high_column] == new_high, exterma_col] = high_label
            
    # filling between highs
    for i, (current_date, row) in enumerate(highs_df.iterrows()):
        if len(highs_df)-1 in [i, i+1]: break
        next_row = highs_df.iloc[i+1]
        lows_between = get_by_datetimeRange(lows_df, current_date, next_row.Date)
        if lows_between.empty:
            new_low = df.loc[current_date:next_row.Date, low_column].min()
            df.loc[ df[low_column] == new_low, exterma_col] = low_label
            
    return df
        
        
def remove_less_than_min_time(max_idx:list, min_idx:list, df_:pd.DataFrame,
                              datetime_col:str, high_col:str,
                              low_col:str, min_delta_t:dt.timedelta ):
            
            highs_df = df_.iloc[max_idx][[datetime_col,high_col]].drop_duplicates()
            lows_df = df_.iloc[min_idx][[datetime_col,low_col]].drop_duplicates()
                     
            # removing highs closer than specified time  
            while highs_df.diff(1)[datetime_col].min() < min_delta_t: # doing for maxs
                time_diff = highs_df.diff(1)[datetime_col]
                to_remove_pair_ind = highs_df[time_diff.min() == time_diff].index[0]
                ind = max_idx.index(to_remove_pair_ind)
                if ind == len(highs_df)-1 :break
                to_remove_ind = highs_df[highs_df.iloc[ind-1:ind][high_col].min() == highs_df[high_col]].index[0]
                highs_df.drop(to_remove_ind, axis = 0, inplace = True)
            
            # removing lows closer than specified time 
            while lows_df.diff(1)[datetime_col].min() < min_delta_t: # doing for mins
                try:
                    time_diff = lows_df.diff(1)[datetime_col]
                    to_remove_pair_ind = lows_df[time_diff.min() == time_diff].index[0]
                    ind = min_idx.index(to_remove_pair_ind)
                    if ind == len(lows_df)-1 :break
                    to_remove_ind = lows_df[lows_df.iloc[ind-1:ind][low_col].max() == lows_df[low_col]].index[0]
                    lows_df.drop(to_remove_ind, axis = 0, inplace = True)
                
                except IndexError : break
                
            return highs_df.index.to_list(), lows_df.index.to_list()
        
        
def fill_between_trends(df:pd.DataFrame , rm_below_ncandles:int = 10, 
                        trend_col = "high_low_trend", side_trend_label = 0 ,
                        fill_side_between_same = False,
                        fill_other_between_same = False):
        """this function can remove trends found between two same bigger trends. 
        also can remove any side trend between to same trends.

        Args:
            df (pd.DataFrame): input dataframe
            rm_below_ncandles (int, optional): removes small trends if they are
            smaller than this candle size [min size between lowtrends,
            min size between sidetrends, min size between hightrends]. Defaults to [500,500,500].
            trend_col (str, optional): name of column holds the trend labels. Defaults to "high_low_trend".
            side_trend_label (_type_, optional): label of side trend. Defaults to side_trend_label.
            fill_side_between_same (_type_, optional): if True removes all sides between trends.
            Defaults to fill_side_between_same_trends.

        Returns:
            _type_: _description_
        """            
        df_ = df.copy()
        df_.Name = df.Name
        grps = df_.groupby(trend_col, sort = True).groups
        ncandles = rm_below_ncandles
        
        for label in grps.keys():
            ser = pd.Series( grps[label], name = f"{label}")
            inds = ser[ser.diff() > 1].index.to_list()
            for ind in inds:
                small_trend = df_.loc[ ser[ind-1]+1 : ser[ind]-1, trend_col ]
                if (small_trend == side_trend_label).all() and fill_side_between_same: 
                    df_.loc[ ser[ind-1]+1 : ser[ind]-1, trend_col ] = label
                elif len(small_trend) <= ncandles  and fill_other_between_same:
                    df_.loc[ ser[ind-1]+1 : ser[ind]-1, trend_col ] = label
        return df_ 

