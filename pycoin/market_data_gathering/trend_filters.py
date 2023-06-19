import pandas as pd
import datetime as dt

def fill_between_pivots( max_idx:list, min_idx:list , df_:pd.DataFrame, high_col_name:str ,
                                low_col_name:str):
            
            high_df = df_.iloc[max_idx][high_col_name]
            low_df = df_.iloc[min_idx][low_col_name]
            
            # concatnating mins and max and taking isna to check is we have two immediate pivots
            isnan = pd.concat([high_df, low_df], axis = 1, sort = True).isna()
            isnum = isnan == False
            
            min_idx_ = min_idx.copy()
            j = 0
            
            # adding new min between two immediate max
            for i, val in isnan.iterrows(): 
                if i == max_idx[-1]: break
                # if we have two immediate highs and two coresspanding nan in lows
                if isnum[high_col_name].iloc[[j, j+1]].all() and isnan[low_col_name].iloc[[j, j+1]].all(): 
                    ind = max_idx.index(i)
                    new_min = df_.iloc[max_idx[ind]:max_idx[ind+1]][low_col_name].min() # finding new min
                    # selecting the one that is in range of two maxs
                    new_min_ind = [ind_ for ind_ in df_[df_[low_col_name] == new_min].index 
                                   if ind_ in range(max_idx[ind],max_idx[ind+1])][0]
                    
                    min_idx_.append(new_min_ind)
                    min_idx_.sort()
                j+=1
                
            ############ doing the same for lows ######
            max_idx_ = max_idx.copy()
            j = 0
            
            # adding new max between two immediate min
            for i, val in isnan.iterrows():
                
                if i == min_idx[-1]: break
                # if we have two immediate lows and two coresspanding nan in highs
                if isnum[low_col_name].iloc[[j, j+1]].all() and isnan[high_col_name].iloc[[j, j+1]].all():
                    ind = min_idx.index(i)
                    new_max = df_.iloc[min_idx[ind]: min_idx[ind+1]][high_col_name].max() # finding new max
                    # selecting the one that is in range of two mins
                    new_max_ind = [ind_ for ind_ in df_[df_[high_col_name] == new_max].index  
                                   if ind_ in range(min_idx[ind], min_idx[ind+1]) ][0]
                    
                    max_idx_.append(new_max_ind)
                    max_idx_.sort()
                j+=1
                
            return max_idx_, min_idx_
        
        
        
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
                to_remove_ind = highs_df[highs_df.iloc[ind-1:ind+1][high_col].min() == highs_df[high_col]].index[0]
                highs_df.drop(to_remove_ind, axis = 0, inplace = True)
            
            # removing lows closer than specified time 
            while lows_df.diff(1)[datetime_col].min() < min_delta_t: # doing for mins
                try:
                    time_diff = lows_df.diff(1)[datetime_col]
                    to_remove_pair_ind = lows_df[time_diff.min() == time_diff].index[0]
                    ind = min_idx.index(to_remove_pair_ind)
                    if ind == len(lows_df)-1 :break
                    to_remove_ind = lows_df[lows_df.iloc[ind-1:ind+1][low_col].max() == lows_df[low_col]].index[0]
                    lows_df.drop(to_remove_ind, axis = 0, inplace = True)
                
                except IndexError : break
                
            return highs_df.index.to_list(), lows_df.index.to_list()