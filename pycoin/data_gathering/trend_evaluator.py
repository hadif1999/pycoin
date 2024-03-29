

import pandas as pd 
from pycoin.data_gathering.indicators import calc_MAs
from typing import List, Dict, Any
from ta.trend import MACD
import numpy as np
from .high_lows_evaluator import get_market_High_Lows

class Trend_Evaluator():
    
    def eval_trend_with_high_lows(dataframe, trend_col_name:str = "high_low_trend", 
                                  HighLow_range: int = 100,
                                  high_trend_label:int = 1, 
                                  side_trend_label:int = 0,
                                  low_trend_label:int = -1,
                                  fill_between_same_trends:bool = True,
                                  remove_less_than_n_candles = 10,
                                  fill_side_between_same_trends:bool = True, 
                                  high_col = "High",
                                  low_col = "Low",
                                  **kwargs
                                  ):
        """evaluates trend with high and lows evaluated with remove_less_than_min_time method.

        Args:
            trend_col_name (str, optional): name of column to add trend labels. Defaults to "high_low_trend".
            inplace (bool, optional): change the main object dataframe or not. Defaults to True.
            high_trend_label (int, optional): label of hightrend. Defaults to 1.
            low_trend_label (int, optional): label of lowtrend. Defaults to -1.
            side_trend_label (int, optional): label of sidetrend. Defaults to 0.
            fill_between_same_trends (bool, optional): fill small trends between two bigger
            same trends or not. Defaults to True.
            remove_less_than_n_candles (list, optional): removes small trends if they are smaller
            than this candle size[min size between lowtrends, min size between sidetrends,
            min size between hightrends] this arg will be ignored if fill_between_same_trends is False.
            Defaults to [500,500,500].. Defaults to [1000,1000,1000].
            fill_side_between_same_trends (bool, optional): remove all sidetrends between two 
            same trends or not. this arg will be ignored if fill_between_same_trends is False.

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """           
        df_ = dataframe.copy()
        df_.Name = dataframe.Name
        df_ = get_market_High_Lows(df_, candle_range=HighLow_range, **kwargs )
        df_[trend_col_name] = side_trend_label
        if "Datetime" not in df_.columns: df_["Datetime"] = df_.index
        df_.reset_index(drop = True, inplace = True)
        HighLows_grp = df_.groupby( kwargs.get("colName", "Pivot"))
        max_idx, min_idx = HighLows_grp.get_group(1).index, HighLows_grp.get_group(-1).index
        
        if not isinstance(remove_less_than_n_candles, int): 
            raise "remove_less_than_n_candles can be int"
        
        for max_ind, min_ind, i  in zip(max_idx, min_idx,
                                        range( max( len(max_idx), len(min_idx) ))):

            if i > 0 :
                # compare for uptrend ( if we have higher highs and higher lows we have uptrend)
                is_hh = df_[high_col].iloc[max_ind] > df_[high_col].iloc[last_max_ind]
                is_hl = df_[low_col].iloc[min_ind] > df_[low_col].iloc[last_min_ind] 
                # compare for downtrend ( if we have lower highs and lower lows we have downtrend)
                is_lh = df_[high_col].iloc[max_ind] < df_[high_col].iloc[last_max_ind]
                is_ll = df_[low_col].iloc[min_ind] < df_[low_col].iloc[last_min_ind] 
                # assign high_trend_ labels to pivots that are hh and hl (same for downtrend)
                if is_hh and is_hl: 
                    to_fill_highs = df_.loc[ min(last_max_ind, last_min_ind):max(max_ind, min_ind),
                                             trend_col_name]
                    inds_high = to_fill_highs.mask(to_fill_highs == side_trend_label , high_trend_label)
                    df_.loc[inds_high.index, trend_col_name] = inds_high
                    
                elif is_lh and is_ll: 
                    to_fill_lows = df_.loc[ min(last_max_ind, last_min_ind):max(max_ind, min_ind),
                                            trend_col_name]
                    inds_low = to_fill_lows.mask(to_fill_lows == side_trend_label, low_trend_label)
                    df_.loc[inds_low.index, trend_col_name] = inds_low
                # labeling the last pivot                
                if i == min( len(max_idx), len(min_idx) )-1 and len(max_idx) != len(min_idx):
                    
                    if len(min_idx) > len(max_idx) : 
                        if (df_[low_col].iloc[min_idx[-1]] < df_[low_col].iloc[last_min_ind]) :
                            
                            df_.loc[min_ind: min_idx[-1], trend_col_name] = low_trend_label
                            
                    if len(max_idx) > len(min_idx):
                        if (df_[high_col].iloc[max_idx[-1]] > df_[high_col].iloc[last_max_ind]):
                            
                            df_.loc[max_ind: max_idx[-1], trend_col_name] = high_trend_label
            last_max_ind = max_ind
            last_min_ind = min_ind
        # filling between same trend
        from .trend_filters import fill_between_trends
        if fill_between_same_trends :
                df_ = fill_between_trends(df_, remove_less_than_n_candles, trend_col_name ,
                                        side_trend_label = side_trend_label,
                                        fill_side_between_same = False,
                                        fill_other_between_same= fill_between_same_trends) 
        if fill_side_between_same_trends:        
                df_ = fill_between_trends(df_, remove_less_than_n_candles, trend_col_name ,
                                        side_trend_label = side_trend_label,
                                        fill_side_between_same = fill_side_between_same_trends,
                                        fill_other_between_same=False)                  
        df_.set_index("Datetime", inplace=True)
        return df_
    
    
    
    
    def eval_trend_with_MAs(dataframe:pd.DataFrame, column:str = "Close" ,
                            windows:List = [50,200], drop_MA_cols:bool = False,
                            up_trends_as = 1, down_trends_as = -1, side_trends_as = 0,
                            trend_col_name:str = "MA_trend"):
        """eval trend with moving averages (list of 2 window values (first lower second higher)
        must be inserted).
        if short term MA > long term MA -> uptrend
        elif short term MA < long term MA -> downtrend 
        

        Args:
            column (str, optional): _description_. Defaults to "Close".
            windows (List, optional): _description_. Defaults to [50,200].
            drop_MA_cols (bool, optional): drop calculated MA cols after calculation or not. Defaults to False.
            up_trends_as (int, optional): label of up_trend values. Defaults to 1.
            down_trends_as (int, optional): label of down_trend values. Defaults to -1.
            side_trends_as (int, optional): label of side_trend values. Defaults to 0.
            inplace(bool): add column to dataframe entered at constructor or not. Defaults to True.

        Returns:
            dataframe with a "MA_trend" column : _description_
        """        
        if len(windows) > 2 : raise Exception("len of windows must be 2")
        if windows[0] > windows[1]: raise Exception("short term MA window must entered first.")
        elif windows[0] == windows[1]: raise Exception("short and long term windows can't be equal!")
        
        df_ = dataframe.copy()
        df_.Name = dataframe.Name
        df_.index.name = ''
        if not "Datetime" in df_.columns: df_["Datetime"] = df_.index            
        df_with_MA = calc_MAs(df_, column = column, windows = windows)
        df_with_MA.Name = dataframe.Name
        
        up_trends = df_with_MA.query(f"MA{str(windows[0])} > MA{str(windows[1])}").copy()
        down_trends = df_with_MA.query(f"MA{str(windows[0])} < MA{str(windows[1])}").copy()
        
        up_trends[trend_col_name] = up_trends_as
        down_trends[trend_col_name] = down_trends_as
        
        trends = pd.concat([up_trends, down_trends], axis = 0, ignore_index = False, sort = True)
        labeled_df = pd.merge(df_, trends, how = "left", sort = True).fillna(side_trends_as)
        
        if drop_MA_cols: labeled_df.drop([f"MA{str(windows[0])}", f"MA{str(windows[1])}"], axis = 1, 
                                     inplace= True)
        
        overall_trend = labeled_df[trend_col_name].iloc[-1]
        labeled_df.Name = dataframe.Name
        labeled_df.set_index("Datetime", inplace = True)
        return labeled_df
    
    


    def eval_trend_with_MACD(dataframe,* , column:str = "Close", window_slow:int = 26 , 
                             window_fast:int = 12, window_sign:int = 9 , fill_na:bool = False,
                             drop_MACD_col:bool = False, up_trends_as = 1,
                             down_trends_as = -1, side_trends_as = 0,
                             trend_col_name:str = 'MACD_trend'):
        
        df_ = dataframe.copy()
        df_.Name = dataframe.Name
        # calculating MACD
        macd = MACD(close = df_[column], window_slow = window_slow , window_fast = window_fast,
                    window_sign = window_sign, fillna = fill_na,)
        
        df_['MACD'] = macd.macd()
        df_['signal_line'] = macd.macd_signal()
        df_['MACD_diff'] = df_['MACD'] - df_['signal_line']
        df_[trend_col_name] = np.where(df_['MACD_diff'] > 0, up_trends_as, 
                                     np.where(df_['MACD_diff'] < 0, down_trends_as, side_trends_as))
        
        if drop_MACD_col : df_.drop(['signal_line','MACD','MACD_diff'], axis = 1, inplace = True)
        overall_trend = df_[trend_col_name].iloc[-1]
        return df_
    
    
    
    def eval_trend_with_ROC(dataframe,* , column:str = "Close" ,nperiods:int = 14, drop_ROC:bool = False, 
                            up_trends_as = 1, down_trends_as = -1, side_trends_as = 0, 
                            trend_col_name:str = 'ROC_trend'):
        
        df_ = dataframe.copy()
        df_.Name = dataframe.Name
        df_['ROC'] = ((df_[column] - df_[column].shift(nperiods)) / df_[column].shift(nperiods)) * 100
        # Fill missing values with 0
        df_['ROC'].fillna(0, inplace=True)
        # Determine the trend based on the ROC
        threshold = 0  # Threshold for trend determination
        df_[trend_col_name] = np.where(df_['ROC'] > threshold, up_trends_as, 
                            np.where(df_['ROC'] < -threshold, down_trends_as, side_trends_as))
        # Get the overall trend based on the last row
        overall_trend = df_[trend_col_name].iloc[-1]
        if drop_ROC : df_.drop("ROC", axis = 1 , inplace = True)
        return df_
    
    
    
    
    