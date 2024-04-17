
from pycoin import Utils
from pykalman import KalmanFilter
import pandas as pd
import numpy as np

    

class KalmanfilterDeploy:
    def __init__(self, observation_covariance=0.05,
                 transition_covariance=0.01, **kwargs) -> None:
    
        self.kalman_kwargs = {"n_dim_obs":1, "n_dim_state":1,
                                "observation_covariance":observation_covariance,
                                "transition_covariance":transition_covariance}
    
    def filter(self, series):
        kf = KalmanFilter(initial_state_mean=series.iloc[0], **self.kalman_kwargs)
        state_means, state_covariances = kf.filter(series.values)
        self.filtered_data = pd.Series(state_means.flatten(), index=series.index)
        return self.filtered_data


    def generate_signal(self, dataframe:pd.DataFrame,
                        filter_column:str = "Close", dist_pct: float = 0.01 ,
                        **kwargs):
        """generates LONG, SHORT signal by finding high and lows and make order in 
        those price. adds "Position_side", "Kalman", "upper_limit", "lower_limit" columns

        Args:
            dataframe (pd.DataFrame)
            filter_column (str, optional)
            dist_pct (float, optional): distance from column price to find price range. Defaults to 0.01.

        Returns:
            pd.Dataframe
        """        
        df = dataframe.copy()
        df["Kalman"] = self.filter(df[filter_column])
        high_idx, low_idx = Utils.get_signal_HighsLows_ind(df["Kalman"].values, **kwargs )
        lows_df, highs_df = df.iloc[low_idx], df.iloc[high_idx]
        df["Position_side"] = 0
        df.loc[highs_df.index, "Position_side"] = -1
        df.loc[lows_df.index, "Position_side"] = 1
        df = self.generate_position_price_range(df, filter_column, dist_pct)
        if kwargs.get("inplace", True): self.df = df
        return df
    
    
    def generate_position_price_range(self, dataframe: pd.DataFrame, 
                                      column:str = "Close", dist_pct: float = 0.01):
        """evaluates range of price than a position can be excuted if 
        there is a signal

        Args:
            dataframe (pd.DataFrame)
            column (str, optional): column to evalute the range from. Defaults to "Close".
            dist_pct (float, optional): acceptable distance from price in pct. Defaults to 0.01.

        Returns:
            pd.DataFrame: df consisting "upper_limit" and "lower_limit" column
        """        
        upper_limit = np.where(dataframe["Position_side"] != 0, 
                               dataframe[column]+dist_pct*dataframe[column], 0)
        
        lower_limit = np.where(dataframe["Position_side"]!=0,
                               dataframe[column]-dist_pct*dataframe[column], 0)
        c1 = ((dataframe[column] <= upper_limit) & (dataframe[column] >= lower_limit))
        c2 = ((upper_limit!=0) & (lower_limit!=0)) 
        dataframe["IsInPriceRange"] = c1 & c2
        return dataframe
