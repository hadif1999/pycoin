import pandas as pd
import numpy as np
import ta
from ta.momentum import RSIIndicator
from ta.trend import ADXIndicator
from .._strategy_BASE import _StrategyBASE
from pycoin import Utils
from pycoin.plotting import Market_Plotter
from pycoin.data_gathering import get_market_High_Lows

class LorentzianClassifier_Strategy(_StrategyBASE):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.lorenzclassifier = LorentzianClassifier(**kwargs)
    
        
    def predict(self, to_HeikenAshi: bool = False , MA_filter:None|int = None,**kwargs):
        if kwargs.get("update_data", True): self.update_data
        df_ = self.df.copy()
        df_.Name = self.df.Name
        df_ = self.lorenzclassifier.predict(Utils.to_HeikinAshi(df_) 
                                            if to_HeikenAshi else df_ , **kwargs)
        df_["Signal2"] = np.where(df_["Kernel"] > df_["Close"], 1, 
                         np.where(df_["Kernel"] < df_["Close"], -1, 0))
        if MA_filter: df_["Kernel"] = df_["Kernel"].rolling(MA_filter,center=True).mean()
        if kwargs.get("inplace", True):
            try:
                self.df["Kernel"] = df_["Kernel"]
                self.df["Signal1"] = df_["Signal1"]
                self.df["Signal2"] = df_["Signal2"]
            except: pass
        return self.df
        
        
    def find_position_side(self, **kwargs):
        high_idx, low_idx = Utils.get_signal_HighsLows_ind(self.df["Kernel"].values, **kwargs )
        lows_df, highs_df = self.df.iloc[low_idx], self.df.iloc[high_idx]
        long_cond = ((lows_df["Open"]<lows_df["Kernel"]) & (lows_df["Close"]>lows_df["Kernel"]))
        short_cond = ((highs_df["Open"]>highs_df["Kernel"]) & (highs_df["Close"]<highs_df["Kernel"]))
        self.df["Position_side"] = 0
        high_idx = (self.df.loc[long_cond.index].loc[long_cond]).index
        low_idx = (self.df.loc[short_cond.index].loc[short_cond]).index
        self.df.loc[highs_df.index, "Position_side"] = 1
        self.df.loc[lows_df.index, "Position_side"] = -1
        return self.df["Position_side"]
    
    
    def plot(self, **kwargs):
        fig = super().plot(**kwargs)
        fig.add_scatter(x = self.df.index, y = self.df["Kernel"],  
                        line_shape='spline', line={"color":kwargs.get("color", "black")},
                        name = "Lorentzian classifier")
        for side, grp_df in self.df.groupby("Position_side"):
            if side == 0: continue
            for ind, row in grp_df.iterrows():
                self.plotter.draw_circle(fig, [ind, row["Kernel"]], 
                                         fillcolor = "blue" if side == 1 else "yellow", **kwargs)
        return fig
        



class LorentzianClassifier:
    def __init__(self, * ,neighbors_count=6, max_bars_back=900,
                 trade_with_kernel=True, show_kernel_estimate=True, lookback_window=8,
                 relative_weighting=8.0, use_volatility_filter=True, volatility_threshold=1.0,
                 use_regime_filter=True, regime_threshold = -0.1, **kwargs):
        
        self.neighbors_count = neighbors_count
        self.max_bars_back = max_bars_back
        self.trade_with_kernel = trade_with_kernel
        self.show_kernel_estimate = show_kernel_estimate
        self.lookback_window = lookback_window
        self.relative_weighting = relative_weighting
        self.use_volatility_filter = use_volatility_filter
        self.volatility_threshold = volatility_threshold
        self.use_regime_filter = use_regime_filter
        self.regime_threshold = regime_threshold

    def lorentzian_distance(self, series1, series2):
        """ Compute the Lorentzian distance between two series. """
        return np.log(1 + np.abs(series1 - series2))
    
    
    def calculate_atr(self, df):
        """ Calculate Average True Range (ATR) for volatility. """
        df['H-L'] = df['High'] - df['Low']
        df['H-C'] = np.abs(df['High'] - df['Close'].shift())
        df['L-C'] = np.abs(df['Low'] - df['Close'].shift())
        df['TR'] = df[['H-L', 'H-C', 'L-C']].max(axis=1)
        df['ATR'] = df['TR'].rolling(window=14).mean()
        return df
    
    
    def apply_filters(self, df, index):
        """ Apply volatility and regime filters. """
        if self.use_volatility_filter and df.iloc[index]["ATR"] < self.volatility_threshold:
            return False
        if "ADX" in df.columns:
            if self.use_regime_filter and df.iloc[index]["ADX"] < self.regime_threshold:
                return False
        else: False
        return True
    

    def calculate_features(self, df,
                           feature_setting:dict = {"RSI":{"window":14}, "ADX":{"window":20}}, 
                           **kwargs):
        """ Calculate features like RSI and ADX which are inputs to the model. """
        df["ADX"] = ADXIndicator(df.High, df.Low, 
            df.Close, feature_setting["ADX"]["window"]).adx()
        
        df["RSI"] = RSIIndicator(df.Close, feature_setting["RSI"]["window"]).rsi()
            
        df = self.calculate_atr(df)
        return df


    def get_nearest_neighbors(self, df, features, index):
        """ Get nearest neighbors using Lorentzian distance. """
        assert index < len(df), "index must be lower than df.len"
        distances = []
        # Calculate distances for relevant rows
        start_index = max(0, index - self.max_bars_back)
        for i in range(start_index, index):
            distance = sum(self.lorentzian_distance(df[feature].iloc[i], df[feature].iloc[index]) 
                           for feature in features)
            distances.append((distance, df['Close'].iloc[i]))
        # Sort by distance, get closest neighbors count
        distances.sort()
        neighbors = distances[:self.neighbors_count]
        return neighbors


    def apply_kernel_smoothing(self, data, index):
        """ Apply kernel smoothing over the specified lookback window. """
        start = max(0, index - self.lookback_window)
        weights = np.array([1 / (1 + self.relative_weighting * abs(i - index)) 
                            for i in range(start, index)])
        smoothed_value = np.average(data[start:index], weights=weights)
        return smoothed_value
    
    
    def predict(self, df:pd.DataFrame, **kwargs) -> pd.DataFrame:
        """ Classify using the Lorentzian method and predict signals with filters. """
        assert self.max_bars_back < len(df), "max bars must be less than df.len"
        # df = self.calculate_features(df, **kwargs)
        signals = []
        kernel_estimates = []

        for index in range(len(df)):
            if index < max(self.lookback_window, 14):
                signals.append(0)  # Not enough data to predict
                kernel_estimates.append(np.nan)
                continue

            # if not self.apply_filters(df, index):
            #     signals.append(0)  # Filtered out
            #     kernel_estimates.append(np.nan)
            #     continue
            
            # features = list(kwargs.get("feature_setting", {}).keys())
            # neighbors = self.get_nearest_neighbors(df, features, index)
            # avg_close = np.mean([n[1] for n in neighbors])
            # signal_col = kwargs.get("signal_col", "Close")
            # signal = (1 if avg_close > df[signal_col].iloc[index] else -1  
            #          if avg_close < df[signal_col].iloc[index] else 0) 
            # signals.append(signal)

            if self.trade_with_kernel:
                kernel_smoothing_col = kwargs.get("kernel_smoothing_col", "Close")
                kernel_value = self.apply_kernel_smoothing(df[kernel_smoothing_col], index)
                kernel_estimates.append(kernel_value)
            else:
                kernel_estimates.append(np.nan)

        # df['Signal1'] = signals
        if self.show_kernel_estimate:
            df['Kernel'] = kernel_estimates

        return df

