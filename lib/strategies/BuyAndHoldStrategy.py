from lib.strategies.BaseStrategy import BaseStrategy
import pandas as pd

class BuyAndHoldStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
    def execute(self, data:pd.DataFrame)->float:
        # Ensure the DataFrame is not empty
        if data.empty:
            return 0.0
        
        # Get the closing prices of the first and last rows
        first_close = data['close'].iloc[0]
        last_close = data['close'].iloc[-1]
        
        # Calculate the percentage change
        self.accumulated_return_percent = ((last_close - first_close) / first_close) * 100
        
        return self.accumulated_return_percent