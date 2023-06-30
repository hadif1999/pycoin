from ..market_data_gathering.market_processing import Market_Processing 
from ..market_data_kline_plots.market_plotter import Market_Plotter
import os
import pandas as pd

class Frac_Levels:
    def __init__(self, process_obj: Market_Processing ) -> None:
        self.market_obj = process_obj
        self.update_params
        self.fracts = None
        self.fig = None
        self.weekly_fracts = None
        
    @property
    def update_params(self):
        self.symbol = self.market_obj.symbol
        self.df = self.market_obj.market_df
        self.interval = self.market_obj.interval
        self.highs_df = self.market_obj.highs_df
        self.lows_df = self.market_obj.lows_df
        self.pivots = self.market_obj.pivots
    
    def eval_fract_levels(self, method:str = "both", candle_ranges:range = range(40,200,20),
                          tolerance_percent:float = 0.01, min_occurred:int = 2, 
                          inplace:bool = True, 
                          high_cols_to_check:list = ["high"],
                          low_cols_to_check:list = ["low"]):
        self.update_params
        fracts = []
        
        match method:
            case "both":
                fracts = self.__eval_fract_levels_last_pivots(candle_ranges,tolerance_percent,
                                                               min_occurred,False, 
                                                               high_cols_to_check,
                                                               low_cols_to_check)
                
                fracts += self.__eval_fract_levels_weekly_pivots(candle_ranges,
                                                                 tolerance_percent,
                                                                 min_occurred, False, 
                                                                 high_cols_to_check,
                                                                 low_cols_to_check)
                fracts = list(set(fracts))
                if inplace: self.fracts = fracts
                
            case "last_pivots":
                fracts = self.__eval_fract_levels_last_pivots(candle_ranges,tolerance_percent,
                                                               min_occurred,False, 
                                                               high_cols_to_check,
                                                               low_cols_to_check)
                fracts = list(set(fracts))
                if inplace: self.fracts = fracts
            case "weekly_pivots":
                fracts = self.__eval_fract_levels_weekly_pivots(candle_ranges,
                                                                 tolerance_percent,
                                                                 min_occurred, False, 
                                                                 high_cols_to_check,
                                                                 low_cols_to_check)
                fracts = list(set(fracts))
                if inplace: self.fracts = fracts
            
        return fracts
    
    
    def __eval_fract_levels_last_pivots(self, candle_ranges:range = range(30,150,20),
                               tolerance_percent:float = 0.05,
                               min_occurred:int = 1, inplace:bool = True,
                               high_cols_to_check:list = ["high"],
                               low_cols_to_check:list = ["low"]):
        
        self.update_params
        
        high_col = self.pivots["highs"]["column"]
        low_col = self.pivots["lows"]["column"]
        fracts = []
        
        for range in candle_ranges:
            maxs, mins = self.market_obj.get_market_high_lows(candle_range = range,
                                                              high_col = high_col, low_col=low_col,
                                                              inplace = False,
                                                              )
            
            all_mins_df = self.df.loc[mins][low_cols_to_check]
            all_maxs_df = self.df.loc[maxs][high_cols_to_check]
            all_maxs_df.columns = ["pivots" for c in all_maxs_df.columns]
            all_mins_df.columns = ["pivots" for c in all_mins_df.columns]
            all_pivots_df = pd.concat([all_maxs_df, all_mins_df], axis=0,
                                      join="outer", ignore_index=True, sort = True)
                               
            for pivot in all_pivots_df.values.reshape(-1,1)[:,0].tolist():
                upper_level = pivot + pivot*(tolerance_percent/100.0)
                lower_level = pivot - pivot*(tolerance_percent/100.0)
                cond  = (all_pivots_df <= upper_level) & (all_pivots_df >= lower_level)
                if cond.sum()[0] >= min_occurred: fracts.append(pivot)
        
        fracts = list(set(fracts))
        fracts.sort()
        if inplace: self.fracts = fracts
        return fracts
    
    def __eval_fract_levels_weekly_pivots(self, candle_ranges:range = range(100,150,20),
                            tolerance_percent:float = 0.01,
                            min_occurred:int = 2, inplace:bool = True,
                            high_cols_to_check:list = ["high"],
                            low_cols_to_check:list = ["low"]):
        
        self.update_params
        weekly_fracts = self.eval_weekly_fracts()
        
        high_col = self.pivots["highs"]["column"]
        low_col = self.pivots["lows"]["column"]
        fracts = []
        
        for range in candle_ranges:
            maxs, mins = self.market_obj.get_market_high_lows(candle_range = range,
                                                              high_col = high_col, low_col=low_col,
                                                              inplace = False)
            all_mins_df = self.df.loc[mins][low_cols_to_check]
            all_maxs_df = self.df.loc[maxs][high_cols_to_check]
            all_maxs_df.columns = ["pivots" for c in all_maxs_df.columns]
            all_mins_df.columns = ["pivots" for c in all_mins_df.columns]
            all_pivots_df = pd.concat([all_maxs_df, all_mins_df], axis=0,
                                      join="outer", ignore_index=True, sort = False)
                        
            for week_pivot in weekly_fracts.tolist():
                upper_level = week_pivot + week_pivot*(tolerance_percent/100.0)
                lower_level = week_pivot - week_pivot*(tolerance_percent/100.0)
                cond  = (all_pivots_df <= upper_level) & (all_pivots_df >= lower_level)
                if cond.sum()[0] >= min_occurred: fracts.append(week_pivot)
        
        fracts = list(set(fracts))
        fracts.sort()
        if inplace: self.fracts = fracts
        return fracts

                
    
    def plot_fracts(self, inplace= True, **kwargs):
        self.update_params
        if self.fracts == None: 
            raise ValueError("fracts levels didn't evaluated, first run eval_Fract_levels func")
        plots = Market_Plotter(self.market_obj)
        fig, _ = plots.plot_market(False)
        for frac in self.fracts:
            plots.draw_static_line(fig, "h",frac, kwargs.get("color","purple"), f"{frac}","top center")
        if inplace: self.fig = fig
        return fig
    
    
    def eval_weekly_fracts(self, mean_high_low_col_name:str = "mean_high_low", inplace:bool = True,
                           just_mean:bool = False, **kwargs):
        week_obj = Market_Processing(self.symbol, "1week")
        weekly_df = week_obj.download_kline_as_df(True, verbose=False)
        weekly_df[mean_high_low_col_name] = weekly_df[["high", "low"]].mean(axis=1)
        if inplace: 
            if just_mean: self.weekly_fracts = weekly_df[mean_high_low_col_name].values.reshape(-1,1)[:,0]
            else: self.weekly_fracts = weekly_df[["high","low",mean_high_low_col_name]].values.reshape(-1,1)[:,0]
        return self.weekly_fracts
    
    
    def plot_weekly_fracts(self, delete_past_shapes:bool = False, inplace = True,
                           n_last_fracts:int = None, **kwargs):
        
        fig = self.fig
        if delete_past_shapes: fig.layout.shapes = []
        
        try:
            if self.weekly_fracts == None: 
                raise ValueError("weekly fracts didn't evaluated, first run eval_weekly_fracts func")
        except: pass
        
        plots = Market_Plotter(self.market_obj)
        
        if n_last_fracts == None: weekly_fracts = self.weekly_fracts
        else: weekly_fracts = self.weekly_fracts[-n_last_fracts:]
        for pivot in weekly_fracts:
            plots.draw_static_line(fig, 'h', pivot, kwargs.get("color","orange"), label = "weekly_pivots" )
        
        fig.update_layout(showlegend=False)
        if inplace: self.fig = fig
        return fig 
        
                

                
         