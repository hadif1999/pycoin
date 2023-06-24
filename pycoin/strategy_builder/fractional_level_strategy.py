from ..market_data_gathering.market_processing import Market_Processing 
from ..market_data_kline_plots.market_plotter import Market_Plotter

class Fractional_Levels:
    def __init__(self, process_obj: Market_Processing ) -> None:
        self.market_obj = process_obj
        self.update_params_
        self.fracts = None
        
    @property
    def update_params_(self):
        self.symbol = self.market_obj.symbol
        self.df = self.market_obj.market_df
        self.interval = self.market_obj.interval
        self.highs_df = self.market_obj.highs_df
        self.lows_df = self.market_obj.lows_df
        self.pivots = self.market_obj.pivots
    
    
    def eval_Fractional_levels(self, candle_ranges:range = range(30,150,20),
                               tolerance_percent:float = 0.05,
                               min_occurred:int = 1, inplace:bool = True):
        
        self.update_params_
        
        high_col = self.pivots["highs"]["column"]
        low_col = self.pivots["lows"]["column"]
        fracts = []
        
        for range in candle_ranges:
            maxs, mins = self.market_obj.get_market_high_lows(candle_range = range,
                                                              high_col = high_col, low_col=low_col,
                                                              inplace = False)
            all_mins_df = self.df.loc[mins]
            all_maxs_df = self.df.loc[maxs]
            
        # finding fractionals for mins
        
            # finding supports
            for min_ind in mins:
                min_price = self.df.loc[min_ind][low_col]
                upper_side = (min_price + tolerance_percent*0.01*min_price)
                down_side = (min_price - tolerance_percent*0.01*min_price)
                other_pivots = all_mins_df.drop(min_ind, axis = 0)[low_col]
                cond = (other_pivots <= upper_side) & (other_pivots >= upper_side)
                check = all_mins_df.where(cond)
                if check.any().any() and (check.count() >= min_occurred).any():
                    fracts.append(min_price)
                    
            # finding fractionals levels
            for min_ind in mins:
                min_price = self.df.loc[min_ind][low_col]
                upper_side = (min_price + tolerance_percent*0.01*min_price)
                down_side = (min_price - tolerance_percent*0.01*min_price)
                other_pivots = all_maxs_df[high_col]
                cond = (other_pivots <= upper_side) & (other_pivots >= down_side)
                check = all_maxs_df.where(cond)
                if check.any().any() and (check.count() >= min_occurred).any():
                    fracts.append(min_price)
                    
        # finding fractionals for maxs
                            
            # finding resistance
            for max_ind in maxs:
                max_price = self.df.loc[max_ind][high_col]
                upper_side = (max_price + tolerance_percent*0.01*max_price)
                down_side = (max_price - tolerance_percent*0.01*max_price)
                other_pivots = all_maxs_df.drop(max_ind, axis = 0)[high_col]
                cond = (other_pivots <= upper_side) & (other_pivots >= down_side)
                check = all_maxs_df.where(cond)
                if check.any().any() and (check.count() >= min_occurred).any():
                    fracts.append(max_price)
        
            # finding fractionals levels
            for max_ind in maxs:
                max_price = self.df.loc[max_ind][high_col]
                upper_side = (max_price + tolerance_percent*0.01*max_price)
                down_side = (max_price - tolerance_percent*0.01*max_price)
                other_pivots = all_mins_df[low_col]
                cond = (other_pivots <= upper_side) &  (other_pivots >= down_side)
                check = all_mins_df.where(cond)
                if check.any().any() and (check.count() >= min_occurred).any():
                    fracts.append(max_price)
                    
        fracts = list(set(fracts))
        fracts.sort()
        
        if inplace: self.fracts = fracts
        return fracts
    
    
    def plot_fracts(self, **kwargs):
        self.update_params_
        plots = Market_Plotter(self.market_obj)
        fig, _ = plots.plot_market(False)
        for frac in self.fracts:
            plots.draw_static_line(fig, "h",frac, kwargs.get("color","purple"), f"{frac}")
        return fig
        
                

                
         